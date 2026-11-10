<?php
declare(strict_types=1);

namespace App;

use PDO;

final class Database
{
    public static function connect(?string $path = null): PDO
    {
        $path ??= getenv('DB_PATH') ?: __DIR__ . '/../storage/app.sqlite';
        if ($path !== ':memory:') {
            $dir = dirname($path);
            if (!is_dir($dir)) {
                mkdir($dir, 0775, true);
            }
        }

        $pdo = new PDO('sqlite:' . $path, null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);

        $pdo->exec(<<<'SQL'
            CREATE TABLE IF NOT EXISTS datasets (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                name         TEXT    NOT NULL,
                table_name   TEXT    NOT NULL UNIQUE,
                columns_json TEXT    NOT NULL,
                row_count    INTEGER NOT NULL,
                report_json  TEXT    NOT NULL DEFAULT '{}',
                created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        SQL);

        return $pdo;
    }
}
