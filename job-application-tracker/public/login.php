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
$email = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $email = (string) ($_POST['email'] ?? '');
    try {
        $user = Auth::login($pdo, $email, (string) ($_POST['password'] ?? ''), $_SERVER['REMOTE_ADDR'] ?? 'unknown');
        Auth::signIn($user['id']);
        redirect('index.php');
    } catch (AuthException $e) {
        $error = $e->getMessage();
    }
}

page_header('Sign in');
?>
<form method="post" class="card narrow">
    <h1>Sign in</h1>
    <?php if ($error): ?><p class="alert"><?= h($error) ?></p><?php endif; ?>
    <?= csrf_field() ?>
    <label>Email <input name="email" type="email" value="<?= h($email) ?>" required autocomplete="email"></label>
    <label>Password <input name="password" type="password" required autocomplete="current-password"></label>
    <button class="btn" type="submit">Sign in</button>
    <p class="muted small">New here? <a href="register.php">Create an account</a></p>
</form>
<?php page_footer();
