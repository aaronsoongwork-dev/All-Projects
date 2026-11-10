<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\Applications;
use App\Database;
use App\Status;

$pdo = Database::connect();
$user = require_login($pdo);

$filters = [
    'status' => (string) ($_GET['status'] ?? ''),
    'q' => (string) ($_GET['q'] ?? ''),
    'sort' => (string) ($_GET['sort'] ?? 'updated'),
    'dir' => (string) ($_GET['dir'] ?? 'desc'),
];
$result = (new Applications($pdo))->search($user['id'], $filters, (int) ($_GET['page'] ?? 1));

/** Link to this page with some query parameters changed. */
function qs(array $override): string
{
    $params = array_filter(array_merge($_GET, $override), fn($v) => $v !== '' && $v !== null);
    return '?' . http_build_query($params);
}

function sort_link(string $key, string $label, array $filters): string
{
    $next = ($filters['sort'] === $key && $filters['dir'] === 'asc') ? 'desc' : 'asc';
    $arrow = $filters['sort'] === $key ? ($filters['dir'] === 'asc' ? ' &uarr;' : ' &darr;') : '';
    return '<a href="' . h(qs(['sort' => $key, 'dir' => $next, 'page' => 1])) . '">' . h($label) . '</a>' . $arrow;
}

page_header('Applications', $user, 'applications.php');
?>
<div class="row between">
    <h1>Applications <span class="muted">(<?= $result['total'] ?>)</span></h1>
    <span>
        <a class="btn ghost" href="export.php">Export CSV</a>
        <a class="btn" href="edit.php">+ Add application</a>
    </span>
</div>

<form method="get" class="card filters">
    <input type="search" name="q" value="<?= h($filters['q']) ?>" placeholder="Search company, role, location, notes...">
    <select name="status">
        <option value="">All statuses</option>
        <option value="active" <?= $filters['status'] === 'active' ? 'selected' : '' ?>>Active only</option>
        <?php foreach (Status::LABELS as $value => $label): ?>
            <option value="<?= h($value) ?>" <?= $filters['status'] === $value ? 'selected' : '' ?>><?= h($label) ?></option>
        <?php endforeach; ?>
    </select>
    <button class="btn" type="submit">Filter</button>
    <?php if ($filters['q'] !== '' || $filters['status'] !== ''): ?><a href="applications.php">Clear</a><?php endif; ?>
</form>

<section class="card">
    <?php if (!$result['rows']): ?>
        <p class="muted">No applications match. <a href="edit.php">Add one</a>.</p>
    <?php else: ?>
        <div class="scroll">
        <table>
            <thead>
            <tr>
                <th><?= sort_link('company', 'Company', $filters) ?></th>
                <th>Role</th>
                <th><?= sort_link('status', 'Status', $filters) ?></th>
                <th><?= sort_link('applied_on', 'Applied', $filters) ?></th>
                <th>Location</th>
                <th><?= sort_link('updated', 'Updated', $filters) ?></th>
            </tr>
            </thead>
            <tbody>
            <?php foreach ($result['rows'] as $a): ?>
                <tr>
                    <td><a href="view.php?id=<?= (int) $a['id'] ?>"><?= h($a['company']) ?></a></td>
                    <td><?= h($a['role']) ?></td>
                    <td><span class="badge s-<?= h($a['status']) ?>"><?= h(Status::label($a['status'])) ?></span></td>
                    <td><?= h($a['applied_on'] ?? '-') ?></td>
                    <td><?= h($a['location']) ?></td>
                    <td class="muted"><?= h(substr($a['updated_at'], 0, 10)) ?></td>
                </tr>
            <?php endforeach; ?>
            </tbody>
        </table>
        </div>

        <?php if ($result['pages'] > 1): ?>
            <p class="pager">
                <?php if ($result['page'] > 1): ?><a class="btn small ghost" href="<?= h(qs(['page' => $result['page'] - 1])) ?>">Previous</a><?php endif; ?>
                <span class="muted">Page <?= $result['page'] ?> of <?= $result['pages'] ?></span>
                <?php if ($result['page'] < $result['pages']): ?><a class="btn small ghost" href="<?= h(qs(['page' => $result['page'] + 1])) ?>">Next</a><?php endif; ?>
            </p>
        <?php endif; ?>
    <?php endif; ?>
</section>
<?php page_footer();
