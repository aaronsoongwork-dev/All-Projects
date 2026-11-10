<?php
declare(strict_types=1);

namespace App;

/**
 * Sends plain-text email. MAIL_MODE (see .env.example):
 *   log  (default) append to storage/outbox.log: safe for local development, nothing leaves your machine
 *   mail           use PHP's mail(), which needs a working sendmail/SMTP setup on the server
 */
final class Mailer
{
    public static function send(string $to, string $subject, string $body): bool
    {
        // Header-injection guard: CR/LF in the subject or address would let someone add headers.
        $subject = trim(str_replace(["\r", "\n"], ' ', $subject));
        if (!filter_var($to, FILTER_VALIDATE_EMAIL)) {
            return false;
        }

        if (env('MAIL_MODE', 'log') === 'mail') {
            $from = env('MAIL_FROM', 'no-reply@localhost');
            if (!filter_var($from, FILTER_VALIDATE_EMAIL)) {
                return false;
            }
            return mail($to, $subject, $body, "From: $from\r\nContent-Type: text/plain; charset=UTF-8");
        }

        $dir = __DIR__ . '/../storage';
        if (!is_dir($dir)) {
            mkdir($dir, 0775, true);
        }
        $entry = sprintf("[%s] To: %s\nSubject: %s\n\n%s\n%s\n", date('c'), $to, $subject, $body, str_repeat('-', 60));
        return file_put_contents($dir . '/outbox.log', $entry, FILE_APPEND | LOCK_EX) !== false;
    }
}
