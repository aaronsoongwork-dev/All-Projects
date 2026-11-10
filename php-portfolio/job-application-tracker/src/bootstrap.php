<?php
declare(strict_types=1);

// ---- Autoloader (App\Foo -> src/Foo.php) ----
spl_autoload_register(static function (string $class): void {
    if (strncmp($class, 'App\\', 4) !== 0) {
        return;
    }
    $file = __DIR__ . '/' . str_replace('\\', '/', substr($class, 4)) . '.php';
    if (is_file($file)) {
        require $file;
    }
});

// ---- Minimal .env loader: KEY=VALUE lines, real environment variables win ----
(static function (): void {
    $file = __DIR__ . '/../.env';
    if (!is_file($file)) {
        return;
    }
    foreach (file($file, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#' || !str_contains($line, '=')) {
            continue;
        }
        [$k, $v] = array_map('trim', explode('=', $line, 2));
        if (getenv($k) === false) {
            putenv($k . '=' . trim($v, "\"'"));
        }
    }
})();

function env(string $key, string $default = ''): string
{
    $v = getenv($key);
    return $v === false || $v === '' ? $default : $v;
}

date_default_timezone_set(env('APP_TIMEZONE', 'UTC'));

// ---- Output + request helpers ----
function h(?string $value): string
{
    return htmlspecialchars((string) $value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

function start_session(): void
{
    if (session_status() === PHP_SESSION_NONE) {
        session_name('jobtracker');
        session_set_cookie_params([
            'httponly' => true,
            'samesite' => 'Lax',
            'secure' => !empty($_SERVER['HTTPS']),
        ]);
        session_start();
    }
}

function send_security_headers(): void
{
    header('X-Content-Type-Options: nosniff');
    header('X-Frame-Options: DENY');
    header('Referrer-Policy: same-origin');
}

function redirect(string $to): never
{
    header('Location: ' . $to);
    exit;
}

function csrf_token(): string
{
    start_session();
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf'];
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf" value="' . h(csrf_token()) . '">';
}

/** Call at the top of every POST handler. */
function csrf_check(): void
{
    start_session();
    $expected = (string) ($_SESSION['csrf'] ?? '');
    $sent = (string) ($_POST['csrf'] ?? '');
    if ($expected === '' || !hash_equals($expected, $sent)) {
        http_response_code(419);
        exit('Your session expired or the form was invalid. Go back, refresh and try again.');
    }
}

/** One-time messages shown after a redirect. */
function flash(?string $message = null, string $type = 'ok'): ?array
{
    start_session();
    if ($message !== null) {
        $_SESSION['flash'] = ['message' => $message, 'type' => $type];
        return null;
    }
    $f = $_SESSION['flash'] ?? null;
    unset($_SESSION['flash']);
    return $f;
}

/** Signed-in user row, or redirects to the login page. */
function require_login(PDO $pdo): array
{
    start_session();
    $user = null;
    if (!empty($_SESSION['uid'])) {
        $stmt = $pdo->prepare('SELECT id, email, name FROM users WHERE id = ?');
        $stmt->execute([(int) $_SESSION['uid']]);
        $user = $stmt->fetch() ?: null;
    }
    if (!$user) {
        redirect('login.php');
    }
    return $user;
}

function page_header(string $title, ?array $user = null, string $active = ''): void
{
    send_security_headers();
    $nav = [
        'index.php' => 'Dashboard',
        'applications.php' => 'Applications',
        'edit.php' => '+ Add',
    ];
    ?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= h($title) ?> - Job Tracker</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
<header class="top">
    <a class="brand" href="index.php">Job Tracker</a>
    <?php if ($user): ?>
        <nav>
            <?php foreach ($nav as $href => $label): ?>
                <a href="<?= h($href) ?>" class="<?= $active === $href ? 'active' : '' ?>"><?= h($label) ?></a>
            <?php endforeach; ?>
        </nav>
        <form method="post" action="logout.php" class="inline">
            <?= csrf_field() ?>
            <span class="muted"><?= h($user['name']) ?></span>
            <button class="btn small ghost" type="submit">Sign out</button>
        </form>
    <?php endif; ?>
</header>
<main class="wrap">
    <?php if ($f = flash()): ?>
        <p class="alert <?= $f['type'] === 'error' ? '' : 'ok' ?>"><?= h($f['message']) ?></p>
    <?php endif; ?>
<?php
}

function page_footer(): void
{
    echo "</main>\n</body>\n</html>\n";
}
