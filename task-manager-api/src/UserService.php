<?php
declare(strict_types=1);

namespace App;

use PDO;
use PDOException;

final class UserService
{
    public const MAX_FAILED_LOGINS = 5;
    public const LOCKOUT_SECONDS = 900;

    private static ?string $dummyHash = null;

    public function __construct(private PDO $pdo)
    {
    }

    /** The very first account becomes the admin; everyone after that is a member. */
    public function register(array $input): array
    {
        $data = Validator::registration($input);
        $hash = password_hash($data['password'], PASSWORD_DEFAULT);

        $this->pdo->beginTransaction();
        try {
            $role = ((int) $this->pdo->query('SELECT COUNT(*) FROM users')->fetchColumn()) === 0 ? 'admin' : 'member';
            $stmt = $this->pdo->prepare('INSERT INTO users (email, name, password_hash, role) VALUES (?, ?, ?, ?)');
            $stmt->execute([$data['email'], $data['name'], $hash, $role]);
            $id = (int) $this->pdo->lastInsertId();
            $this->pdo->commit();
        } catch (PDOException $e) {
            $this->pdo->rollBack();
            if (str_contains($e->getMessage(), 'UNIQUE')) {
                throw new ApiException(409, 'That email is already registered.', ['email' => 'Already registered.']);
            }
            throw $e;
        }
        return $this->find($id);
    }

    public function login(string $email, string $password, string $ip): array
    {
        $email = strtolower(trim($email));

        if ($this->recentFailures($email) >= self::MAX_FAILED_LOGINS) {
            throw new ApiException(429, 'Too many failed attempts. Try again in a few minutes.');
        }

        $stmt = $this->pdo->prepare('SELECT * FROM users WHERE email = ?');
        $stmt->execute([$email]);
        $row = $stmt->fetch();

        // Always run a hash verification so unknown emails and wrong passwords take similar time.
        $hash = $row['password_hash'] ?? (self::$dummyHash ??= password_hash('not-a-real-password', PASSWORD_DEFAULT));
        $ok = password_verify($password, $hash) && $row;

        if (!$ok) {
            $this->pdo->prepare('INSERT INTO login_attempts (email, ip, attempted_at) VALUES (?, ?, ?)')
                ->execute([$email, $ip, time()]);
            throw new ApiException(401, 'Invalid email or password.');
        }

        $this->pdo->prepare('DELETE FROM login_attempts WHERE email = ?')->execute([$email]);
        if (password_needs_rehash($row['password_hash'], PASSWORD_DEFAULT)) {
            $this->pdo->prepare('UPDATE users SET password_hash = ? WHERE id = ?')
                ->execute([password_hash($password, PASSWORD_DEFAULT), $row['id']]);
        }
        return $this->find((int) $row['id']);
    }

    /** Public user fields only: never expose the password hash. */
    public function find(int $id): ?array
    {
        $stmt = $this->pdo->prepare('SELECT id, email, name, role, created_at FROM users WHERE id = ?');
        $stmt->execute([$id]);
        return $stmt->fetch() ?: null;
    }

    /** @return array<int,array<string,mixed>> */
    public function all(bool $includeEmail): array
    {
        $cols = $includeEmail ? 'id, name, email, role' : 'id, name, role';
        return $this->pdo->query("SELECT $cols FROM users ORDER BY name COLLATE NOCASE")->fetchAll();
    }

    public function setRole(array $actor, int $userId, string $role): array
    {
        if ($actor['role'] !== 'admin') {
            throw new ApiException(403, 'Only admins can change roles.');
        }
        if (!in_array($role, ['admin', 'member'], true)) {
            throw new ApiException(422, 'Role must be admin or member.', ['role' => 'Invalid role.']);
        }
        $target = $this->find($userId) ?? throw new ApiException(404, 'User not found.');

        if ($target['role'] === 'admin' && $role === 'member') {
            $admins = (int) $this->pdo->query("SELECT COUNT(*) FROM users WHERE role = 'admin'")->fetchColumn();
            if ($admins <= 1) {
                throw new ApiException(409, 'There must be at least one admin.');
            }
        }
        $this->pdo->prepare('UPDATE users SET role = ? WHERE id = ?')->execute([$role, $userId]);
        return $this->find($userId);
    }

    private function recentFailures(string $email): int
    {
        $stmt = $this->pdo->prepare('SELECT COUNT(*) FROM login_attempts WHERE email = ? AND attempted_at > ?');
        $stmt->execute([$email, time() - self::LOCKOUT_SECONDS]);
        return (int) $stmt->fetchColumn();
    }
}
