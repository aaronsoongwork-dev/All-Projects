<?php
declare(strict_types=1);

namespace App;

use PDO;
use PDOException;

final class Auth
{
    public const MAX_FAILURES = 5;
    public const LOCKOUT_SECONDS = 900;

    private static ?string $dummyHash = null;

    /** @return array{id:int,email:string,name:string} */
    public static function register(PDO $pdo, string $name, string $email, string $password): array
    {
        $name = trim($name);
        $email = strtolower(trim($email));

        if ($name === '' || mb_strlen($name) > 80) {
            throw new AuthException('Please enter your name (max 80 characters).');
        }
        if (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($email) > 254) {
            throw new AuthException('Please enter a valid email address.');
        }
        if (strlen($password) < 8 || strlen($password) > 72) {
            throw new AuthException('Password must be 8 to 72 characters.');
        }

        try {
            $pdo->prepare('INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)')
                ->execute([$email, $name, password_hash($password, PASSWORD_DEFAULT)]);
        } catch (PDOException $e) {
            if (str_contains($e->getMessage(), 'UNIQUE')) {
                throw new AuthException('That email is already registered. Try signing in.');
            }
            throw $e;
        }
        return ['id' => (int) $pdo->lastInsertId(), 'email' => $email, 'name' => $name];
    }

    /** @return array{id:int,email:string,name:string} */
    public static function login(PDO $pdo, string $email, string $password, string $ip): array
    {
        $email = strtolower(trim($email));

        $stmt = $pdo->prepare('SELECT COUNT(*) FROM login_attempts WHERE email = ? AND attempted_at > ?');
        $stmt->execute([$email, time() - self::LOCKOUT_SECONDS]);
        if ((int) $stmt->fetchColumn() >= self::MAX_FAILURES) {
            throw new AuthException('Too many failed attempts. Please wait a few minutes and try again.');
        }

        $stmt = $pdo->prepare('SELECT * FROM users WHERE email = ?');
        $stmt->execute([$email]);
        $row = $stmt->fetch();

        // Same amount of hashing work whether or not the email exists.
        $hash = $row['password_hash'] ?? (self::$dummyHash ??= password_hash('not-a-real-password', PASSWORD_DEFAULT));
        if (!(password_verify($password, $hash) && $row)) {
            $pdo->prepare('INSERT INTO login_attempts (email, ip, attempted_at) VALUES (?, ?, ?)')->execute([$email, $ip, time()]);
            throw new AuthException('Invalid email or password.');
        }

        $pdo->prepare('DELETE FROM login_attempts WHERE email = ?')->execute([$email]);
        if (password_needs_rehash($row['password_hash'], PASSWORD_DEFAULT)) {
            $pdo->prepare('UPDATE users SET password_hash = ? WHERE id = ?')
                ->execute([password_hash($password, PASSWORD_DEFAULT), $row['id']]);
        }
        return ['id' => (int) $row['id'], 'email' => $row['email'], 'name' => $row['name']];
    }

    public static function signIn(int $userId): void
    {
        start_session();
        session_regenerate_id(true); // prevents session fixation
        $_SESSION['uid'] = $userId;
    }

    public static function signOut(): void
    {
        start_session();
        $_SESSION = [];
        $p = session_get_cookie_params();
        setcookie(session_name(), '', ['expires' => time() - 3600, 'path' => $p['path'], 'httponly' => true, 'samesite' => 'Lax']);
        session_destroy();
    }
}
