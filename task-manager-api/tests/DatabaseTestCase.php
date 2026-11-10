<?php
declare(strict_types=1);

namespace Tests;

use App\Database;
use App\TaskService;
use App\UserService;
use PDO;
use PHPUnit\Framework\TestCase;

/** Gives each test a fresh in-memory database plus an admin, two members and the services. */
abstract class DatabaseTestCase extends TestCase
{
    protected PDO $pdo;
    protected UserService $users;
    protected TaskService $tasks;
    /** @var array<string,mixed> */
    protected array $admin;
    protected array $alice;
    protected array $bob;

    protected function setUp(): void
    {
        $this->pdo = Database::connect(':memory:');
        $this->users = new UserService($this->pdo);
        $this->tasks = new TaskService($this->pdo);

        $this->admin = $this->register('Admin', 'admin@example.com');   // first user => admin
        $this->alice = $this->register('Alice', 'alice@example.com');
        $this->bob = $this->register('Bob', 'bob@example.com');
    }

    protected function register(string $name, string $email, string $password = 'correct-horse-battery'): array
    {
        return $this->users->register(['name' => $name, 'email' => $email, 'password' => $password]);
    }

    /** @return array<int,string> titles of one column, in order */
    protected function column(string $status): array
    {
        $rows = array_filter($this->tasks->list($this->admin), fn($t) => $t['status'] === $status);
        usort($rows, fn($a, $b) => $a['position'] <=> $b['position']);
        return array_values(array_map(fn($t) => $t['title'], $rows));
    }
}
