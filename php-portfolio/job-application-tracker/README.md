# Job Application Tracker

A full-stack PHP app for running a job search like a project: track every application, log each stage change, set follow-up reminders, and see **data-driven insights** about your own search (response rate, time to first reply, funnel, time spent per stage).

Built with **PHP 8.1+, SQLite (PDO), server-rendered HTML and plain CSS**. No framework, no JavaScript required, no Composer install.

<!-- Add screenshots after you run it: ![Dashboard](docs/dashboard.png) -->

## Features

- Accounts with secure sign-up/login (bcrypt, session cookies, login lockout); every user only ever sees their own data
- Full CRUD for applications: company, role, link, location, pay, notes, status, application date
- **Status history**: every change is logged with a date, which powers the analytics
- **Dashboard**
  - applications sent, still active, offers, rejections
  - **response rate** and **average days to first reply**
  - **funnel** (applied -> screening -> interview -> offer)
  - applications per week (last 12 weeks)
  - average days spent in each stage
- Search, filter by status, sortable columns, pagination
- Follow-up **reminders** (auto-suggested 7 days after applying) and a cron-friendly **email digest script**
- **CSV export** of all your applications

## Run it

Requirements: PHP 8.1+ with `pdo_sqlite` (enabled by default in most installs).

```bash
git clone <your-repo-url>
cd job-application-tracker
cp .env.example .env            # optional: set your timezone
php bin/seed.php                # optional: demo account + 24 sample applications
php -S localhost:8000 -t public
```

Open <http://localhost:8000>. With the seed data, sign in as `demo@example.com` / `demo-password-123` (local use only); otherwise create your own account.

### Email reminders

```bash
php bin/send_reminders.php
```

By default (`MAIL_MODE=log`) emails are written to `storage/outbox.log` so nothing leaves your machine. Set `MAIL_MODE=mail` in `.env` to use PHP's `mail()` on a server with sendmail/SMTP configured. Run it daily with cron:

```
0 8 * * *  cd /path/to/job-application-tracker && php bin/send_reminders.php
```

## How the analytics work

Every status change is stored in `status_events` with a date. From that log:

- **Response rate** = applications that ever reached screening, interview, offer, accepted *or rejected* / applications sent (wishlist items excluded).
- **Days to first reply** = earliest "response" event minus the application date, averaged.
- **Funnel** counts an application at every stage up to the furthest one it reached (an offer implies an interview happened).
- **Time per stage** = days between consecutive events, averaged per stage.

I cross-checked these numbers against separate raw-SQL queries on the seeded data.

## Project structure

```
public/        pages: index (dashboard), applications (list), edit, view, login, register, logout, export, style.css
src/           bootstrap.php (helpers, CSRF, flash), Auth, Applications (all queries), Stats, Status, Mailer, Database
sql/schema.sql database schema (applied automatically on first run)
bin/           seed.php and send_reminders.php (CLI only)
```

## Security notes

- **Authorization**: every query includes `user_id`; asking for someone else's application returns 404.
- **SQL injection**: prepared statements only; sort columns come from a whitelist.
- **XSS**: all output is escaped with `htmlspecialchars`; job links are only rendered if they are `http(s)` (blocks `javascript:` URLs) and open with `rel="noopener noreferrer"`.
- **CSRF**: a token on every POST form, including logout.
- **Sessions**: `HttpOnly`, `SameSite=Lax`, `Secure` over HTTPS, session id regenerated at login.
- **Login**: lockout after 5 failures per email for 15 minutes; identical error and hashing work for unknown emails.
- **CSV export** neutralises spreadsheet formulas (`=`, `+`, `-`, `@` prefixes).
- **Email**: header-injection guard on subject and address.

## Known limitations / next steps

- Email uses PHP's `mail()`; real deployments should use SMTP (for example PHPMailer).
- No password reset or email verification yet.
- Add an automated test suite (the logic in `Applications` and `Stats` is already separated from HTML, so it is easy to test).
- Ideas: interview-prep notes per application, tags, calendar (.ics) export, charts of salary ranges.

## Resume bullet

> Built a multi-user PHP/SQLite job-search tracker with secure authentication, per-user data isolation, a status-history log and an analytics dashboard (response rate, funnel, time-in-stage), plus CSV export and a cron-driven email reminder script.
