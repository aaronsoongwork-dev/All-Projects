<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\Applications;
use App\Database;
use App\Status;

$pdo = Database::connect();
$user = require_login($pdo);
$repo = new Applications($pdo);

$id = (int) ($_GET['id'] ?? $_POST['id'] ?? 0);
$app = $repo->find($user['id'], $id);
if (!$app) {
    http_response_code(404);
    exit('Application not found. <a href="applications.php">Back to the list</a>');
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $back = 'view.php?id=' . $id;

    switch ((string) ($_POST['action'] ?? '')) {
        case 'status':
            $ok = $repo->changeStatus($user['id'], $id, (string) ($_POST['status'] ?? ''), (string) ($_POST['date'] ?? date('Y-m-d')));
            flash($ok ? 'Status updated.' : 'Could not update the status.', $ok ? 'ok' : 'error');
            break;
        case 'add_reminder':
            $ok = $repo->addReminder($user['id'], $id, (string) ($_POST['due_on'] ?? ''), (string) ($_POST['note'] ?? ''));
            flash($ok ? 'Reminder added.' : 'Enter a valid date and a note (max 200 characters).', $ok ? 'ok' : 'error');
            break;
        case 'toggle_reminder':
            $repo->setReminderDone($user['id'], (int) ($_POST['reminder_id'] ?? 0), ($_POST['done'] ?? '') === '1');
            break;
        case 'delete_reminder':
            $repo->deleteReminder($user['id'], (int) ($_POST['reminder_id'] ?? 0));
            break;
        case 'delete':
            $repo->delete($user['id'], $id);
            flash('Application deleted.');
            $back = 'applications.php';
            break;
    }
    redirect($back);
}

$events = $repo->events($id);
$reminders = $repo->reminders($id);

page_header($app['company'], $user);
?>
<div class="row between">
    <div>
        <h1><?= h($app['company']) ?></h1>
        <p class="lead"><?= h($app['role']) ?> <span class="badge s-<?= h($app['status']) ?>"><?= h(Status::label($app['status'])) ?></span></p>
    </div>
    <span>
        <a class="btn ghost" href="edit.php?id=<?= (int) $id ?>">Edit</a>
        <form method="post" class="inline" onsubmit="return confirm('Delete this application and its history?')">
            <?= csrf_field() ?><input type="hidden" name="id" value="<?= (int) $id ?>"><input type="hidden" name="action" value="delete">
            <button class="btn danger" type="submit">Delete</button>
        </form>
    </span>
</div>

<div class="grid2">
    <section class="card">
        <h2>Details</h2>
        <dl>
            <dt>Applied on</dt><dd><?= h($app['applied_on'] ?? 'not yet') ?></dd>
            <dt>Location</dt><dd><?= h($app['location'] ?: '-') ?></dd>
            <dt>Pay</dt><dd><?= h($app['salary_note'] ?: '-') ?></dd>
            <dt>Posting</dt>
            <dd><?php
                // Validated as http(s) on save; re-checked here so a bad row in the database can never become a javascript: link.
                $scheme = strtolower((string) parse_url($app['url'], PHP_URL_SCHEME));
                if ($app['url'] !== '' && in_array($scheme, ['http', 'https'], true)): ?>
                    <a href="<?= h($app['url']) ?>" target="_blank" rel="noopener noreferrer"><?= h($app['url']) ?></a>
                <?php else: ?>-<?php endif; ?></dd>
        </dl>
        <?php if ($app['notes'] !== ''): ?>
            <h3>Notes</h3>
            <p class="notes"><?= h($app['notes']) ?></p>
        <?php endif; ?>
    </section>

    <section class="card">
        <h2>Update status</h2>
        <form method="post" class="row wrap-row">
            <?= csrf_field() ?><input type="hidden" name="id" value="<?= (int) $id ?>"><input type="hidden" name="action" value="status">
            <select name="status">
                <?php foreach (Status::LABELS as $value => $label): ?>
                    <option value="<?= h($value) ?>" <?= $app['status'] === $value ? 'selected' : '' ?>><?= h($label) ?></option>
                <?php endforeach; ?>
            </select>
            <input type="date" name="date" value="<?= h(date('Y-m-d')) ?>" aria-label="Date it happened">
            <button class="btn" type="submit">Save</button>
        </form>

        <h3>Timeline</h3>
        <ol class="timeline">
            <?php foreach ($events as $e): ?>
                <li><span class="muted"><?= h($e['changed_on']) ?></span> <span class="badge s-<?= h($e['status']) ?>"><?= h(Status::label($e['status'])) ?></span></li>
            <?php endforeach; ?>
        </ol>
    </section>
</div>

<section class="card">
    <h2>Reminders</h2>
    <?php if ($reminders): ?>
        <ul class="plain">
            <?php foreach ($reminders as $r): ?>
                <li class="reminder <?= $r['done'] ? 'done' : '' ?>">
                    <form method="post" class="inline">
                        <?= csrf_field() ?><input type="hidden" name="id" value="<?= (int) $id ?>">
                        <input type="hidden" name="action" value="toggle_reminder">
                        <input type="hidden" name="reminder_id" value="<?= (int) $r['id'] ?>">
                        <input type="hidden" name="done" value="<?= $r['done'] ? '0' : '1' ?>">
                        <button class="btn small ghost" type="submit"><?= $r['done'] ? 'Reopen' : 'Done' ?></button>
                    </form>
                    <strong><?= h($r['due_on']) ?></strong> &middot; <?= h($r['note']) ?>
                    <?= (!$r['done'] && $r['due_on'] < date('Y-m-d')) ? '<span class="tag-overdue">overdue</span>' : '' ?>
                    <form method="post" class="inline right-auto">
                        <?= csrf_field() ?><input type="hidden" name="id" value="<?= (int) $id ?>">
                        <input type="hidden" name="action" value="delete_reminder">
                        <input type="hidden" name="reminder_id" value="<?= (int) $r['id'] ?>">
                        <button class="btn small ghost" type="submit" aria-label="Delete reminder">&times;</button>
                    </form>
                </li>
            <?php endforeach; ?>
        </ul>
    <?php endif; ?>

    <form method="post" class="row wrap-row">
        <?= csrf_field() ?><input type="hidden" name="id" value="<?= (int) $id ?>"><input type="hidden" name="action" value="add_reminder">
        <input type="date" name="due_on" value="<?= h(date('Y-m-d', strtotime('+3 days'))) ?>" required aria-label="Due date">
        <input name="note" placeholder="e.g. Send thank-you email" maxlength="200" required class="grow">
        <button class="btn" type="submit">Add reminder</button>
    </form>
</section>
<?php page_footer();
