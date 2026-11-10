<?php
declare(strict_types=1);

namespace App;

use PDO;
use Throwable;

/**
 * HTTP layer: routing, JSON in/out, auth and CSRF checks.
 *
 *   GET    /api/me              current user + CSRF token (works signed out too)
 *   POST   /api/register        {name, email, password}
 *   POST   /api/login           {email, password}
 *   POST   /api/logout
 *   GET    /api/tasks
 *   POST   /api/tasks           {title, description?, status?, assignee_id?}
 *   PATCH  /api/tasks/{id}      any of title, description, status, position, assignee_id
 *   DELETE /api/tasks/{id}
 *   GET    /api/users           (emails visible to admins only)
 *   PATCH  /api/users/{id}      {role}  admin only
 */
final class Api
{
    private UserService $users;
    private TaskService $tasks;

    public function __construct(PDO $pdo)
    {
        $this->users = new UserService($pdo);
        $this->tasks = new TaskService($pdo);
    }

    public function handle(): void
    {
        header('Content-Type: application/json; charset=utf-8');
        header('Cache-Control: no-store');
        header('X-Content-Type-Options: nosniff');

        try {
            $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
            $path = rtrim((string) parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH), '/');
            $body = [];

            if ($method !== 'GET') {
                $this->guardMutation();
                $body = $this->readJson();
            }

            $this->respond($this->route($method, $path, $body));
        } catch (ApiException $e) {
            $this->respond(['error' => $e->getMessage(), 'fields' => (object) $e->errors], $e->status);
        } catch (Throwable $e) {
            error_log($e);
            $this->respond(['error' => 'Something went wrong on the server.'], 500);
        }
    }

    private function route(string $method, string $path, array $body): array
    {
        if ($method === 'GET' && $path === '/api/me') {
            $id = Auth::userId();
            return ['user' => $id ? $this->users->find($id) : null, 'csrf' => Auth::csrfToken()];
        }
        if ($method === 'POST' && $path === '/api/register') {
            $user = $this->users->register($body);
            Auth::signIn($user['id']);
            return ['user' => $user, 'csrf' => Auth::csrfToken(), '_status' => 201];
        }
        if ($method === 'POST' && $path === '/api/login') {
            $user = $this->users->login(
                (string) ($body['email'] ?? ''),
                (string) ($body['password'] ?? ''),
                $_SERVER['REMOTE_ADDR'] ?? 'unknown'
            );
            Auth::signIn($user['id']);
            return ['user' => $user, 'csrf' => Auth::csrfToken()];
        }
        if ($method === 'POST' && $path === '/api/logout') {
            Auth::signOut();
            return ['ok' => true];
        }

        // Everything below needs a signed-in user.
        $user = $this->requireUser();

        if ($method === 'GET' && $path === '/api/tasks') {
            return ['tasks' => $this->tasks->list($user)];
        }
        if ($method === 'POST' && $path === '/api/tasks') {
            return ['task' => $this->tasks->create($user, $body), '_status' => 201];
        }
        if (preg_match('#^/api/tasks/(\d+)$#', $path, $m)) {
            if ($method === 'PATCH') {
                return ['task' => $this->tasks->update($user, (int) $m[1], $body)];
            }
            if ($method === 'DELETE') {
                $this->tasks->delete($user, (int) $m[1]);
                return ['ok' => true];
            }
        }
        if ($method === 'GET' && $path === '/api/users') {
            return ['users' => $this->users->all($user['role'] === 'admin')];
        }
        if ($method === 'PATCH' && preg_match('#^/api/users/(\d+)$#', $path, $m)) {
            return ['user' => $this->users->setRole($user, (int) $m[1], (string) ($body['role'] ?? ''))];
        }

        throw new ApiException(404, 'Not found.');
    }

    private function requireUser(): array
    {
        $id = Auth::userId();
        $user = $id ? $this->users->find($id) : null;
        if (!$user) {
            throw new ApiException(401, 'Please sign in.');
        }
        return $user;
    }

    /** CSRF defence in depth: JSON content type (cannot be sent by a plain HTML form) + per-session token header. */
    private function guardMutation(): void
    {
        $type = strtolower((string) ($_SERVER['CONTENT_TYPE'] ?? ''));
        if (!str_starts_with($type, 'application/json')) {
            throw new ApiException(415, 'Content-Type must be application/json.');
        }
        if (!Auth::verifyCsrf($_SERVER['HTTP_X_CSRF_TOKEN'] ?? null)) {
            throw new ApiException(403, 'Invalid or missing CSRF token. Reload the page.');
        }
    }

    /** @return array<string,mixed> */
    private function readJson(): array
    {
        $raw = file_get_contents('php://input', false, null, 0, 65537);
        if ($raw === '' || $raw === false) {
            return [];
        }
        if (strlen($raw) > 65536) {
            throw new ApiException(413, 'Request body too large.');
        }
        $data = json_decode($raw, true);
        if (!is_array($data)) {
            throw new ApiException(400, 'Request body must be a JSON object.');
        }
        return $data;
    }

    private function respond(array $payload, int $status = 200): void
    {
        $status = $payload['_status'] ?? $status;
        unset($payload['_status']);
        http_response_code($status);
        echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    }
}
