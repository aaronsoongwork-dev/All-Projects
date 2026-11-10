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
$existing = null;
if ($id) {
    $existing = $repo->find($user['id'], $id);
    if (!$existing) {
        http_response_code(404);
        exit('Application not found. <a href="applications.php">Back</a>');
    }
}

$errors = [];
$values = $existing ?? [
    'company' => '', 'role' => '', 'url' => '', 'location' => '', 'status' => 'applied',
    'applied_on' => date('Y-m-d'), 'salary_note' => '', 'notes' => '',
];
$values['status_date'] = date('Y-m-d');
$values['followup'] = !$existing;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    [$clean, $errors] = Applications::validate($_POST);
    $values = $clean + ['followup' => isset($_POST['followup'])];

    if (!$errors) {
        if ($existing) {
            $repo->update($user['id'], $id, $clean);
            flash('Application updated.');
            redirect('view.php?id=' . $id);
        }
        $newId = $repo->create($user['id'], $clean);
        if (isset($_POST['followup']) && $clean['status'] === 'applied' && $clean['applied_on'] !== '') {
            $due = date('Y-m-d', strtotime($clean['applied_on'] . ' +7 days'));
            $repo->addReminder($user['id'], $newId, $due, 'Follow up with ' . $clean['company']);
        }
        flash('Application added.');
        redirect('view.php?id=' . $newId);
    }
}

function field_error(array $errors, string $name): string
{
    return isset($errors[$name]) ? '<small class="error">' . h($errors[$name]) . '</small>' : '';
}

page_header($existing ? 'Edit application' : 'Add application', $user, $existing ? '' : 'edit.php');
?>
<h1><?= $existing ? 'Edit application' : 'Add application' ?></h1>

<form method="post" class="card form">
    <?= csrf_field() ?>
    <?php if ($existing): ?><input type="hidden" name="id" value="<?= (int) $id ?>"><?php endif; ?>

    <div class="grid2">
        <label>Company * <input name="company" value="<?= h($values['company']) ?>" maxlength="100" required><?= field_error($errors, 'company') ?></label>
        <label>Role * <input name="role" value="<?= h($values['role']) ?>" maxlength="100" required><?= field_error($errors, 'role') ?></label>
        <label>Status
            <select name="status">
                <?php foreach (Status::LABELS as $value => $label): ?>
                    <option value="<?= h($value) ?>" <?= $values['status'] === $value ? 'selected' : '' ?>><?= h($label) ?></option>
                <?php endforeach; ?>
            </select><?= field_error($errors, 'status') ?></label>
        <label>Applied on <input type="date" name="applied_on" value="<?= h($values['applied_on'] ?? '') ?>"><?= field_error($errors, 'applied_on') ?></label>
        <label>Location <input name="location" value="<?= h($values['location']) ?>" maxlength="100"><?= field_error($errors, 'location') ?></label>
        <label>Salary / notes on pay <input name="salary_note" value="<?= h($values['salary_note']) ?>" maxlength="100"><?= field_error($errors, 'salary_note') ?></label>
    </div>
    <label>Job posting link <input type="url" name="url" value="<?= h($values['url']) ?>" placeholder="https://..." maxlength="500"><?= field_error($errors, 'url') ?></label>
    <label>Notes <textarea name="notes" rows="5" maxlength="5000"><?= h($values['notes']) ?></textarea><?= field_error($errors, 'notes') ?></label>

    <?php if ($existing): ?>
        <label>If you changed the status, it happened on
            <input type="date" name="status_date" value="<?= h($values['status_date']) ?>"><?= field_error($errors, 'status_date') ?></label>
    <?php else: ?>
        <label class="check"><input type="checkbox" name="followup" value="1" <?= !empty($values['followup']) ? 'checked' : '' ?>>
            Remind me to follow up 7 days after applying</label>
    <?php endif; ?>

    <div class="row">
        <button class="btn" type="submit">Save</button>
        <a href="<?= $existing ? 'view.php?id=' . (int) $id : 'applications.php' ?>">Cancel</a>
    </div>
</form>
<?php page_footer();
