<?php
declare(strict_types=1);

namespace App;

use PDO;

/**
 * Business rules for tasks, independent of HTTP so they are easy to unit test.
 *
 * Visibility: every signed-in user sees the whole board.
 * Editing:    admins can change/delete any task; members only tasks they created or are assigned to.
 */
final class TaskService
{
    private const SELECT = <<<'SQL'
        SELECT t.id, t.title, t.description, t.status, t.position, t.assignee_id, t.created_by,
               t.created_at, t.updated_at,
               a.name AS assignee_name, c.name AS creator_name
        FROM tasks t
        LEFT JOIN users a ON a.id = t.assignee_id
        LEFT JOIN users c ON c.id = t.created_by
    SQL;

    public function __construct(private PDO $pdo)
    {
    }

    /** @return array<int,array<string,mixed>> */
    public function list(array $user): array
    {
        $rows = $this->pdo->query(self::SELECT . ' ORDER BY t.position, t.id')->fetchAll();
        return array_map(fn($t) => $this->present($t, $user), $rows);
    }

    public function create(array $user, array $input): array
    {
        $data = Validator::task($input, partial: false);
        $status = $data['status'] ?? 'todo';
        $assignee = $data['assignee_id'] ?? null;
        $this->assertAssigneeExists($assignee);

        $stmt = $this->pdo->prepare('SELECT COALESCE(MAX(position), -1) + 1 FROM tasks WHERE status = ?');
        $stmt->execute([$status]);
        $position = (int) $stmt->fetchColumn();

        $this->pdo->prepare(
            'INSERT INTO tasks (title, description, status, position, assignee_id, created_by) VALUES (?, ?, ?, ?, ?, ?)'
        )->execute([$data['title'], $data['description'] ?? '', $status, $position, $assignee, $user['id']]);

        return $this->present($this->findRow((int) $this->pdo->lastInsertId()), $user);
    }

    public function update(array $user, int $id, array $input): array
    {
        $task = $this->findRow($id);
        $this->assertCanEdit($user, $task);
        $data = Validator::task($input, partial: true);

        if (array_key_exists('assignee_id', $data)) {
            $this->assertAssigneeExists($data['assignee_id']);
        }

        $this->pdo->beginTransaction();
        try {
            $sets = [];
            $params = [];
            foreach (['title', 'description', 'assignee_id'] as $field) {
                if (array_key_exists($field, $data)) {
                    $sets[] = "$field = ?";
                    $params[] = $data[$field];
                }
            }
            if ($sets) {
                $sets[] = "updated_at = datetime('now')";
                $params[] = $id;
                $this->pdo->prepare('UPDATE tasks SET ' . implode(', ', $sets) . ' WHERE id = ?')->execute($params);
            }
            if (isset($data['status']) || isset($data['position'])) {
                $this->move($id, $data['status'] ?? $task['status'], $data['position'] ?? null);
            }
            $this->pdo->commit();
        } catch (\Throwable $e) {
            $this->pdo->rollBack();
            throw $e;
        }

        return $this->present($this->findRow($id), $user);
    }

    public function delete(array $user, int $id): void
    {
        $task = $this->findRow($id);
        $this->assertCanEdit($user, $task);
        $this->pdo->prepare('DELETE FROM tasks WHERE id = ?')->execute([$id]);
    }

    /** Moves a task to $status at index $position (end of the column when null) and renumbers the affected columns. */
    private function move(int $id, string $status, ?int $position): void
    {
        $current = $this->pdo->prepare('SELECT status FROM tasks WHERE id = ?');
        $current->execute([$id]);
        $oldStatus = (string) $current->fetchColumn();

        $others = $this->pdo->prepare('SELECT id FROM tasks WHERE status = ? AND id <> ? ORDER BY position, id');
        $others->execute([$status, $id]);
        $ids = array_map('intval', $others->fetchAll(PDO::FETCH_COLUMN));

        $index = $position === null ? count($ids) : min($position, count($ids));
        array_splice($ids, $index, 0, [$id]);

        $this->pdo->prepare('UPDATE tasks SET status = ?, updated_at = datetime(\'now\') WHERE id = ?')->execute([$status, $id]);
        $this->renumber($ids);

        if ($oldStatus !== $status) {
            $rest = $this->pdo->prepare('SELECT id FROM tasks WHERE status = ? ORDER BY position, id');
            $rest->execute([$oldStatus]);
            $this->renumber(array_map('intval', $rest->fetchAll(PDO::FETCH_COLUMN)));
        }
    }

    /** @param int[] $ids */
    private function renumber(array $ids): void
    {
        $stmt = $this->pdo->prepare('UPDATE tasks SET position = ? WHERE id = ?');
        foreach ($ids as $i => $taskId) {
            $stmt->execute([$i, $taskId]);
        }
    }

    private function findRow(int $id): array
    {
        $stmt = $this->pdo->prepare(self::SELECT . ' WHERE t.id = ?');
        $stmt->execute([$id]);
        return $stmt->fetch() ?: throw new ApiException(404, 'Task not found.');
    }

    private function assertCanEdit(array $user, array $task): void
    {
        if (!$this->canEdit($user, $task)) {
            throw new ApiException(403, 'You can only change tasks you created or are assigned to.');
        }
    }

    private function canEdit(array $user, array $task): bool
    {
        return $user['role'] === 'admin'
            || (int) $task['created_by'] === (int) $user['id']
            || (int) ($task['assignee_id'] ?? 0) === (int) $user['id'];
    }

    private function assertAssigneeExists(?int $assigneeId): void
    {
        if ($assigneeId === null) {
            return;
        }
        $stmt = $this->pdo->prepare('SELECT 1 FROM users WHERE id = ?');
        $stmt->execute([$assigneeId]);
        if (!$stmt->fetchColumn()) {
            throw new ApiException(422, 'Please fix the highlighted fields.', ['assignee_id' => 'That user does not exist.']);
        }
    }

    private function present(array $task, array $user): array
    {
        $task['id'] = (int) $task['id'];
        $task['position'] = (int) $task['position'];
        $task['created_by'] = (int) $task['created_by'];
        $task['assignee_id'] = $task['assignee_id'] === null ? null : (int) $task['assignee_id'];
        $task['can_edit'] = $this->canEdit($user, $task);
        return $task;
    }
}
