<?php
declare(strict_types=1);

namespace App;

use PDO;

final class Database
{
    public static function connect(?string $path = null): PDO
    {
        $path ??= env('DB_PATH', __DIR__ . '/../storage/app.sqlite');
        if ($path !== ':memory:' && !is_dir(dirname($path))) {
            mkdir(dirname($path), 0775, true);
        }

        $pdo = new PDO('sqlite:' . $path, null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
        $pdo->exec('PRAGMA foreign_keys = ON');
        $pdo->exec((string) file_get_contents(__DIR__ . '/../sql/schema.sql'));
        return $pdo;
    }
}
