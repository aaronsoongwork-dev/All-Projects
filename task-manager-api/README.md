# Task Board: secure PHP REST API + Kanban frontend

[![Tests](https://github.com/your-github-username/task-manager-api/actions/workflows/tests.yml/badge.svg)](https://github.com/your-github-username/task-manager-api/actions)

A small team Kanban board (To do / In progress / Done) with sign-up, login, roles, drag-and-drop and a clean JSON REST API. The backend is **framework-free PHP 8.1+ with SQLite (PDO)** so every piece of the architecture is visible; the frontend is **vanilla JavaScript** talking to the API.

<!-- Add a screenshot after you run it: ![Board](docs/board.png) -->

## Features

- Register / login / logout with `password_hash` (bcrypt), session cookies and brute-force lockout
- Roles: the first account is **admin**; everyone else is a **member**
  - members see the whole board but can only edit/delete tasks they created or are assigned to
  - admins can edit anything and promote/demote users (the last admin cannot be demoted)
- Kanban board with drag-and-drop ordering (plus an Edit dialog so keyboard and touch users can move tasks too)
- Clean REST API with proper status codes (201, 401, 403, 404, 409, 415, 422, 429)
- PHPUnit test suite for validation, auth rules, permissions and task ordering

## Run it

Requirements: PHP 8.1+ with `pdo_sqlite` (default in most installs).

```bash
git clone <your-repo-url>
cd task-manager-api
php -S localhost:8000 -t public public/router.php
```

Open <http://localhost:8000>, create an account (it will be the admin), then register a second account in a private window to see permissions in action.

Run the tests (needs [Composer](https://getcomposer.org)):

```bash
composer install
vendor/bin/phpunit
```

## API

All bodies are JSON. Every non-GET request needs `Content-Type: application/json` and an `X-CSRF-Token` header (get the token from `GET /api/me`).

| Method | Path | Notes |
|---|---|---|
| GET | `/api/me` | current user (or `null`) + CSRF token |
| POST | `/api/register` | `{name, email, password}` |
| POST | `/api/login` | `{email, password}` |
| POST | `/api/logout` | |
| GET | `/api/tasks` | every task, each with a `can_edit` flag for you |
| POST | `/api/tasks` | `{title, description?, status?, assignee_id?}` |
| PATCH | `/api/tasks/{id}` | any of `title, description, status, position, assignee_id` |
| DELETE | `/api/tasks/{id}` | |
| GET | `/api/users` | emails are only included for admins |
| PATCH | `/api/users/{id}` | `{role}`, admin only |

Example with curl:

```bash
curl -c jar -s localhost:8000/api/me                       # grab csrf token from the response
curl -b jar -c jar -H 'Content-Type: application/json' -H 'X-CSRF-Token: <token>' \
     -d '{"name":"Ada","email":"ada@example.com","password":"correct horse"}' localhost:8000/api/register
```

## Architecture

```
public/            web root: index.html, assets/, api.php (front controller), router.php (dev server), .htaccess
src/Api.php        HTTP layer: routing, JSON, CSRF + content-type guard, error mapping
src/Auth.php       session and CSRF token handling
src/UserService.php  registration, login throttling, roles
src/TaskService.php  task rules, permissions, ordering (no HTTP code, so it is easy to test)
src/Validator.php  input validation -> 422 with per-field messages
src/Database.php   PDO connection and schema migration
tests/             PHPUnit tests using an in-memory SQLite database
```

Business rules live in the services, not in the HTTP layer, which is why the tests can cover them without a web server.

## Security decisions

- **Passwords**: `password_hash` / `password_verify`; rehash on login when the algorithm cost changes; passwords capped at 72 bytes (bcrypt's real limit) instead of silently truncated.
- **Sessions**: `HttpOnly`, `SameSite=Lax`, `Secure` over HTTPS, and `session_regenerate_id(true)` on login (prevents session fixation).
- **CSRF**: per-session token header **and** a JSON-only content-type requirement.
- **Login throttling**: 5 failures per email per 15 minutes returns `429`; unknown email and wrong password return the same message and do the same hashing work, so accounts cannot be enumerated.
- **SQL injection**: prepared statements everywhere; no user input is concatenated into SQL.
- **XSS**: the API stores data verbatim; the frontend builds the DOM with `textContent`, and a strict Content-Security-Policy (`default-src 'self'`) is sent with the page.
- **Authorization** is enforced on the server (`403`), never just by hiding buttons.
- **Request limits**: 64 KB body cap, length limits on every text field.

## Known limitations / next steps

- Single shared board. A natural extension is `projects` / `boards` tables with membership.
- Login lockout is per email, so an attacker can temporarily lock a victim out. A per-IP limit or CAPTCHA would be the next hardening step.
- No password reset or email verification yet (needs an email service).
- Drag-and-drop uses the HTML5 API (mouse). The Edit dialog is the touch/keyboard path.

