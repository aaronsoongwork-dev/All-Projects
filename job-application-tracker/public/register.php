<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\Auth;
use App\AuthException;
use App\Database;

start_session();
$pdo = Database::connect();
if (!empty($_SESSION['uid'])) {
    redirect('index.php');
}

$error = null;
$name = $email = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $name = (string) ($_POST['name'] ?? '');
    $email = (string) ($_POST['email'] ?? '');
    try {
        $user = Auth::register($pdo, $name, $email, (string) ($_POST['password'] ?? ''));
        Auth::signIn($user['id']);
        flash('Welcome! Add your first application to get started.');
        redirect('edit.php');
    } catch (AuthException $e) {
        $error = $e->getMessage();
    }
}

page_header('Create account');
?>
<form method="post" class="card narrow" autocomplete="on">
    <h1>Create account</h1>
    <?php if ($error): ?><p class="alert"><?= h($error) ?></p><?php endif; ?>
    <?= csrf_field() ?>
    <label>Name <input name="name" value="<?= h($name) ?>" required maxlength="80" autocomplete="name"></label>
    <label>Email <input name="email" type="email" value="<?= h($email) ?>" required autocomplete="email"></label>
    <label>Password <input name="password" type="password" required minlength="8" maxlength="72" autocomplete="new-password">
        <small class="muted">8 to 72 characters.</small></label>
    <button class="btn" type="submit">Sign up</button>
    <p class="muted small">Already registered? <a href="login.php">Sign in</a></p>
</form>
<?php page_footer();
