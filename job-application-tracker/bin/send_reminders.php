<?php
declare(strict_types=1);

// Emails each user a digest of reminders that are due (or overdue) and not yet sent.
//   php bin/send_reminders.php
// Schedule it daily with cron, e.g.:   0 8 * * *  cd /path/to/job-application-tracker && php bin/send_reminders.php
// In the default MAIL_MODE=log the "emails" are appended to storage/outbox.log instead of being sent.

if (PHP_SAPI !== 'cli') {
    http_response_code(403);
    exit('CLI only.');
}

require __DIR__ . '/../src/bootstrap.php';

use App\Database;
use App\Mailer;

$pdo = Database::connect();
$today = date('Y-m-d');

$stmt = $pdo->prepare(
    'SELECT r.id, r.due_on, r.note, a.id AS app_id, a.company, a.role, u.id AS user_id, u.email, u.name
     FROM reminders r
     JOIN applications a ON a.id = r.application_id
     JOIN users u ON u.id = a.user_id
     WHERE r.done = 0 AND r.sent_at IS NULL AND r.due_on <= ?
     ORDER BY u.id, r.due_on'
);
$stmt->execute([$today]);

$byUser = [];
foreach ($stmt->fetchAll() as $row) {
    $byUser[$row['user_id']][] = $row;
}

$markSent = $pdo->prepare("UPDATE reminders SET sent_at = datetime('now') WHERE id = ?");
$digests = 0;

foreach ($byUser as $rows) {
    $first = $rows[0];
    $lines = array_map(
        fn($r) => sprintf('- %s  %s (%s): %s', $r['due_on'], $r['company'], $r['role'], $r['note']),
        $rows
    );
    $body = "Hi {$first['name']},\n\nThese job-search reminders are due:\n\n" . implode("\n", $lines)
        . "\n\nMark them done in your tracker" . (env('APP_URL') ? ': ' . env('APP_URL') : '.') . "\n";

    if (Mailer::send($first['email'], count($rows) . ' job search reminder' . (count($rows) === 1 ? '' : 's') . ' due', $body)) {
        foreach ($rows as $r) {
            $markSent->execute([$r['id']]);
        }
        $digests++;
    } else {
        fwrite(STDERR, "Could not send to user {$first['user_id']}; will retry on the next run.\n");
    }
}

echo "Sent $digests digest(s) covering " . array_sum(array_map('count', $byUser)) . " reminder(s).\n";
