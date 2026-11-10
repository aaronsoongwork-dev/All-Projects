<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\Applications;
use App\Database;
use App\Stats;
use App\Status;

$pdo = Database::connect();
$user = require_login($pdo);

$stats = new Stats($pdo);
$o = $stats->overview($user['id']);
$weekly = $stats->weekly($user['id']);
$stages = $stats->stageDurations($user['id']);
$reminders = (new Applications($pdo))->upcomingReminders($user['id'], 7);

$maxWeek = max(1, ...array_values($weekly));
$funnelMax = max(1, $o['funnel']['applied']);

page_header('Dashboard', $user, 'index.php');
?>
<h1>Dashboard</h1>

<?php if ($o['total'] === 0): ?>
    <section class="card">
        <p>No applications yet. <a href="edit.php">Add your first one</a> to see your stats here.</p>
        <p class="muted small">Want demo data? Run <code>php bin/seed.php</code> and sign in as <code>demo@example.com</code>.</p>
    </section>
<?php else: ?>
    <section class="kpis">
        <div class="kpi"><div class="kpi-title">Applications sent</div><div class="kpi-value"><?= $o['applied'] ?></div>
            <div class="kpi-sub"><?= $o['total'] - $o['applied'] ?> on wishlist</div></div>
        <div class="kpi"><div class="kpi-title">Still active</div><div class="kpi-value"><?= $o['active'] ?></div>
            <div class="kpi-sub"><?= $o['offers'] ?> offer<?= $o['offers'] === 1 ? '' : 's' ?> &middot; <?= $o['rejected'] ?> rejected</div></div>
        <div class="kpi"><div class="kpi-title">Response rate</div>
            <div class="kpi-value"><?= $o['response_rate'] === null ? '-' : h((string) $o['response_rate']) . '%' ?></div>
            <div class="kpi-sub"><?= $o['responded'] ?> of <?= $o['applied'] ?> replied</div></div>
        <div class="kpi"><div class="kpi-title">Avg. days to first reply</div>
            <div class="kpi-value"><?= $o['avg_days_to_response'] === null ? '-' : h((string) $o['avg_days_to_response']) ?></div>
            <div class="kpi-sub">from applying to any response</div></div>
    </section>

    <div class="grid2">
        <section class="card">
            <h2>Funnel</h2>
            <p class="muted small">Applications that ever reached each stage.</p>
            <?php foreach ($o['funnel'] as $stage => $n): ?>
                <div class="funnel-row">
                    <span class="funnel-label"><?= h(Status::label($stage)) ?></span>
                    <span class="bar"><span style="width: <?= round(100 * $n / $funnelMax) ?>%"></span></span>
                    <span class="funnel-n"><?= $n ?></span>
                </div>
            <?php endforeach; ?>
        </section>

        <section class="card">
            <h2>Applications per week</h2>
            <div class="weeks">
                <?php foreach ($weekly as $monday => $n): ?>
                    <div class="week" title="Week of <?= h($monday) ?>: <?= $n ?>">
                        <span class="week-n"><?= $n ?: '' ?></span>
                        <span class="week-bar" style="height: <?= round(100 * $n / $maxWeek) ?>%"></span>
                        <span class="week-label"><?= h(date('j M', strtotime($monday))) ?></span>
                    </div>
                <?php endforeach; ?>
            </div>
        </section>
    </div>

    <div class="grid2">
        <section class="card">
            <h2>Time spent per stage</h2>
            <?php if (!$stages): ?>
                <p class="muted">Update an application's status over time to see how long each stage takes.</p>
            <?php else: ?>
                <table>
                    <thead><tr><th>Stage</th><th class="num">Avg. days</th><th class="num">Samples</th></tr></thead>
                    <tbody>
                    <?php foreach ($stages as $stage => $s): ?>
                        <tr><td><?= h(Status::label($stage)) ?></td><td class="num"><?= h((string) $s['avg']) ?></td><td class="num"><?= $s['n'] ?></td></tr>
                    <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </section>

        <section class="card">
            <h2>Reminders</h2>
            <?php if (!$reminders): ?>
                <p class="muted">Nothing due in the next 7 days.</p>
            <?php else: ?>
                <ul class="plain">
                    <?php foreach ($reminders as $r): ?>
                        <li class="<?= $r['due_on'] < date('Y-m-d') ? 'overdue' : '' ?>">
                            <strong><?= h($r['due_on']) ?></strong> &middot;
                            <a href="view.php?id=<?= (int) $r['application_id'] ?>"><?= h($r['company']) ?></a>: <?= h($r['note']) ?>
                            <?= $r['due_on'] < date('Y-m-d') ? '<span class="tag-overdue">overdue</span>' : '' ?>
                        </li>
                    <?php endforeach; ?>
                </ul>
            <?php endif; ?>
        </section>
    </div>
<?php endif; ?>
<?php page_footer();
