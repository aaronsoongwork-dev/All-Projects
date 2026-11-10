<?php
declare(strict_types=1);

namespace App;

/** Session + CSRF handling for the HTTP layer. */
final class Auth
{
    public static function start(): void
    {
        if (session_status() === PHP_SESSION_NONE) {
            session_name('taskboard');
            session_set_cookie_params([
                'httponly' => true,
                'samesite' => 'Lax',
                'secure' => !empty($_SERVER['HTTPS']),
            ]);
            session_start();
        }
    }

    public static function userId(): ?int
    {
        self::start();
        return isset($_SESSION['uid']) ? (int) $_SESSION['uid'] : null;
    }

    public static function signIn(int $userId): void
    {
        self::start();
        session_regenerate_id(true); // prevents session fixation
        $_SESSION['uid'] = $userId;
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }

    public static function signOut(): void
    {
        self::start();
        $_SESSION = [];
        if (ini_get('session.use_cookies')) {
            $p = session_get_cookie_params();
            setcookie(session_name(), '', ['expires' => time() - 3600, 'path' => $p['path'], 'httponly' => true, 'samesite' => 'Lax']);
        }
        session_destroy();
    }

    public static function csrfToken(): string
    {
        self::start();
        if (empty($_SESSION['csrf'])) {
            $_SESSION['csrf'] = bin2hex(random_bytes(32));
        }
        return $_SESSION['csrf'];
    }

    public static function verifyCsrf(?string $sent): bool
    {
        self::start();
        $expected = (string) ($_SESSION['csrf'] ?? '');
        return $expected !== '' && $sent !== null && hash_equals($expected, $sent);
    }
}
