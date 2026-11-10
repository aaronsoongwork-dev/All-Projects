<?php
declare(strict_types=1);

namespace App;

use PDO;

/**
 * Everything that touches the applications tables. EVERY query is scoped by user_id, so one user can
 * never read or change another user's data, even if they guess an id.
 */
final class Applications
{
    public const PER_PAGE = 10;

    private const SORTS = [
        'updated' => 'updated_at',
        'applied_on' => 'applied_on',
        'company' => 'company COLLATE NOCASE',
        'status' => 'status',
    ];

    public function __construct(private PDO $pdo)
    {
    }

    // ---------- validation ----------

    /**
     * @return array{0:array<string,string>,1:array<string,string>} [clean values, errors by field]
     */
    public static function validate(array $in): array
    {
        $clean = [];
        $errors = [];
        $get = fn(string $k): string => is_string($in[$k] ?? null) ? trim($in[$k]) : '';

        foreach (['company' => 100, 'role' => 100] as $field => $max) {
            $clean[$field] = $get($field);
            if ($clean[$field] === '' || mb_strlen($clean[$field]) > $max) {
                $errors[$field] = ucfirst($field) . " is required (max $max characters).";
            }
        }
        foreach (['location' => 100, 'salary_note' => 100, 'notes' => 5000] as $field => $max) {
            $clean[$field] = $get($field);
            if (mb_strlen($clean[$field]) > $max) {
                $errors[$field] = "Too long (max $max characters).";
            }
        }

        // Only http(s) links: a "javascript:" URL rendered in an href would be an XSS hole.
        $clean['url'] = $get('url');
        if ($clean['url'] !== '') {
            $scheme = strtolower((string) parse_url($clean['url'], PHP_URL_SCHEME));
            if (!in_array($scheme, ['http', 'https'], true) || !filter_var($clean['url'], FILTER_VALIDATE_URL) || strlen($clean['url']) > 500) {
                $errors['url'] = 'Enter a full http(s) link, e.g. https://company.com/jobs/123.';
            }
        }

        $clean['status'] = $get('status');
        if (!Status::valid($clean['status'])) {
            $errors['status'] = 'Choose a status.';
        }

        $clean['applied_on'] = $get('applied_on');
        if ($clean['applied_on'] === '') {
            if (($clean['status'] ?? '') !== 'wishlist' && !isset($errors['status'])) {
                $errors['applied_on'] = 'Add the date you applied (only wishlist items can skip it).';
            }
        } elseif (!self::isDate($clean['applied_on'])) {
            $errors['applied_on'] = 'Use a valid date.';
        } elseif ($clean['applied_on'] > date('Y-m-d', strtotime('+1 day'))) {
            $errors['applied_on'] = 'The application date cannot be in the future.';
        }

        $clean['status_date'] = $get('status_date') ?: date('Y-m-d');
        if (!self::isDate($clean['status_date'])) {
            $errors['status_date'] = 'Use a valid date.';
        }

        return [$clean, $errors];
    }

    public static function isDate(string $value): bool
    {
        $d = \DateTimeImmutable::createFromFormat('!Y-m-d', $value);
        return $d !== false && $d->format('Y-m-d') === $value;
    }

    // ---------- reads ----------

    /** @return array{rows:array<int,array<string,mixed>>, total:int, pages:int, page:int} */
    public function search(int $userId, array $filters, int $page): array
    {
        $where = ['user_id = ?'];
        $params = [$userId];

        $status = (string) ($filters['status'] ?? '');
        if ($status === 'active') {
            $where[] = "status IN ('applied','screening','interview','offer')";
        } elseif (Status::valid($status)) {
            $where[] = 'status = ?';
            $params[] = $status;
        }

        $q = trim((string) ($filters['q'] ?? ''));
        if ($q !== '') {
            $like = '%' . addcslashes($q, '%_\\') . '%';
            $where[] = "(company LIKE ? ESCAPE '\\' OR role LIKE ? ESCAPE '\\' OR location LIKE ? ESCAPE '\\' OR notes LIKE ? ESCAPE '\\')";
            array_push($params, $like, $like, $like, $like);
        }

        $sort = self::SORTS[(string) ($filters['sort'] ?? '')] ?? self::SORTS['updated'];
        $dir = (($filters['dir'] ?? 'desc') === 'asc') ? 'ASC' : 'DESC';
        $clause = ' WHERE ' . implode(' AND ', $where);

        $count = $this->pdo->prepare('SELECT COUNT(*) FROM applications' . $clause);
        $count->execute($params);
        $total = (int) $count->fetchColumn();

        $pages = max(1, (int) ceil($total / self::PER_PAGE));
        $page = max(1, min($page, $pages));
        $offset = ($page - 1) * self::PER_PAGE;

        $stmt = $this->pdo->prepare(
            'SELECT * FROM applications' . $clause . " ORDER BY $sort $dir, id DESC LIMIT " . self::PER_PAGE . " OFFSET $offset"
        );
        $stmt->execute($params);

        return ['rows' => $stmt->fetchAll(), 'total' => $total, 'pages' => $pages, 'page' => $page];
    }

    public function find(int $userId, int $id): ?array
    {
        $stmt = $this->pdo->prepare('SELECT * FROM applications WHERE id = ? AND user_id = ?');
        $stmt->execute([$id, $userId]);
        return $stmt->fetch() ?: null;
    }

    /** @return array<int,array<string,mixed>> */
    public function events(int $appId): array
    {
        $stmt = $this->pdo->prepare('SELECT * FROM status_events WHERE application_id = ? ORDER BY changed_on, id');
        $stmt->execute([$appId]);
        return $stmt->fetchAll();
    }

    /** @return array<int,array<string,mixed>> */
    public function reminders(int $appId): array
    {
        $stmt = $this->pdo->prepare('SELECT * FROM reminders WHERE application_id = ? ORDER BY done, due_on');
        $stmt->execute([$appId]);
        return $stmt->fetchAll();
    }

    /** @return array<int,array<string,mixed>> */
    public function all(int $userId): array
    {
        $stmt = $this->pdo->prepare('SELECT * FROM applications WHERE user_id = ? ORDER BY applied_on DESC, id DESC');
        $stmt->execute([$userId]);
        return $stmt->fetchAll();
    }

    /** Open reminders that are overdue or due within $days days. */
    public function upcomingReminders(int $userId, int $days = 7): array
    {
        $stmt = $this->pdo->prepare(
            'SELECT r.*, a.company, a.role FROM reminders r JOIN applications a ON a.id = r.application_id
             WHERE a.user_id = ? AND r.done = 0 AND r.due_on <= ? ORDER BY r.due_on'
        );
        $stmt->execute([$userId, date('Y-m-d', strtotime("+$days days"))]);
        return $stmt->fetchAll();
    }

    // ---------- writes ----------

    /**
     * @param array<string,string> $data validated values from validate()
     * @param array<int,array{0:string,1:string}>|null $events [status, date] pairs to log; defaults to the initial status
     */
    public function create(int $userId, array $data, ?array $events = null): int
    {
        $this->pdo->beginTransaction();
        try {
            $this->pdo->prepare(
                'INSERT INTO applications (user_id, company, role, url, location, status, applied_on, salary_note, notes)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
            )->execute([
                $userId, $data['company'], $data['role'], $data['url'], $data['location'],
                $data['status'], $data['applied_on'] ?: null, $data['salary_note'], $data['notes'],
            ]);
            $id = (int) $this->pdo->lastInsertId();

            $events ??= [[$data['status'], $data['status'] === 'wishlist' ? date('Y-m-d') : ($data['applied_on'] ?: date('Y-m-d'))]];
            foreach ($events as [$status, $date]) {
                $this->logEvent($id, $status, $date);
            }
            $this->pdo->commit();
            return $id;
        } catch (\Throwable $e) {
            $this->pdo->rollBack();
            throw $e;
        }
    }

    /** @param array<string,string> $data validated values; logs an event when the status changed */
    public function update(int $userId, int $id, array $data): bool
    {
        $current = $this->find($userId, $id);
        if (!$current) {
            return false;
        }
        $this->pdo->beginTransaction();
        try {
            $this->pdo->prepare(
                "UPDATE applications SET company = ?, role = ?, url = ?, location = ?, status = ?, applied_on = ?,
                        salary_note = ?, notes = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?"
            )->execute([
                $data['company'], $data['role'], $data['url'], $data['location'], $data['status'],
                $data['applied_on'] ?: null, $data['salary_note'], $data['notes'], $id, $userId,
            ]);
            if ($current['status'] !== $data['status']) {
                $this->logEvent($id, $data['status'], $data['status_date']);
            }
            $this->pdo->commit();
            return true;
        } catch (\Throwable $e) {
            $this->pdo->rollBack();
            throw $e;
        }
    }

    public function changeStatus(int $userId, int $id, string $status, string $date): bool
    {
        $current = $this->find($userId, $id);
        if (!$current || !Status::valid($status) || !self::isDate($date)) {
            return false;
        }
        if ($current['status'] === $status) {
            return true;
        }
        $this->pdo->beginTransaction();
        try {
            // Moving off the wishlist needs an application date.
            $appliedOn = $current['applied_on'] ?: ($status === 'wishlist' ? null : $date);
            $this->pdo->prepare("UPDATE applications SET status = ?, applied_on = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?")
                ->execute([$status, $appliedOn, $id, $userId]);
            $this->logEvent($id, $status, $date);
            $this->pdo->commit();
            return true;
        } catch (\Throwable $e) {
            $this->pdo->rollBack();
            throw $e;
        }
    }

    public function delete(int $userId, int $id): bool
    {
        $stmt = $this->pdo->prepare('DELETE FROM applications WHERE id = ? AND user_id = ?');
        $stmt->execute([$id, $userId]);
        return $stmt->rowCount() > 0;
    }

    public function addReminder(int $userId, int $appId, string $dueOn, string $note): bool
    {
        $note = trim($note);
        if (!$this->find($userId, $appId) || !self::isDate($dueOn) || $note === '' || mb_strlen($note) > 200) {
            return false;
        }
        $this->pdo->prepare('INSERT INTO reminders (application_id, due_on, note) VALUES (?, ?, ?)')->execute([$appId, $dueOn, $note]);
        return true;
    }

    public function setReminderDone(int $userId, int $reminderId, bool $done): bool
    {
        $stmt = $this->pdo->prepare(
            'UPDATE reminders SET done = ? WHERE id = ? AND application_id IN (SELECT id FROM applications WHERE user_id = ?)'
        );
        $stmt->execute([$done ? 1 : 0, $reminderId, $userId]);
        return $stmt->rowCount() > 0;
    }

    public function deleteReminder(int $userId, int $reminderId): bool
    {
        $stmt = $this->pdo->prepare(
            'DELETE FROM reminders WHERE id = ? AND application_id IN (SELECT id FROM applications WHERE user_id = ?)'
        );
        $stmt->execute([$reminderId, $userId]);
        return $stmt->rowCount() > 0;
    }

    private function logEvent(int $appId, string $status, string $date): void
    {
        $this->pdo->prepare('INSERT INTO status_events (application_id, status, changed_on) VALUES (?, ?, ?)')
            ->execute([$appId, $status, $date]);
    }
}
