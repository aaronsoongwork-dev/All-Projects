<?php
declare(strict_types=1);

namespace App;

/** Input validation. Every method returns clean values or throws a 422 ApiException with per-field messages. */
final class Validator
{
    public const STATUSES = ['todo', 'doing', 'done'];

    /** @return array{name:string,email:string,password:string} */
    public static function registration(array $in): array
    {
        $errors = [];
        $name = self::string($in['name'] ?? null);
        $email = strtolower(self::string($in['email'] ?? null));
        $password = is_string($in['password'] ?? null) ? $in['password'] : '';

        if ($name === '' || mb_strlen($name) > 80) {
            $errors['name'] = 'Name is required (max 80 characters).';
        }
        if (!filter_var($email, FILTER_VALIDATE_EMAIL) || strlen($email) > 254) {
            $errors['email'] = 'Enter a valid email address.';
        }
        // bcrypt only uses the first 72 bytes, so refuse longer passwords instead of silently truncating.
        if (strlen($password) < 8 || strlen($password) > 72) {
            $errors['password'] = 'Password must be 8 to 72 characters.';
        }
        if ($errors) {
            throw new ApiException(422, 'Please fix the highlighted fields.', $errors);
        }
        return ['name' => $name, 'email' => $email, 'password' => $password];
    }

    /**
     * @param bool $partial true for PATCH: only validate the keys that were sent
     * @return array<string,mixed> only the validated keys
     */
    public static function task(array $in, bool $partial): array
    {
        $errors = [];
        $out = [];

        if (!$partial || array_key_exists('title', $in)) {
            $title = self::string($in['title'] ?? null);
            if ($title === '' || mb_strlen($title) > 120) {
                $errors['title'] = 'Title is required (max 120 characters).';
            }
            $out['title'] = $title;
        }
        if (array_key_exists('description', $in)) {
            $desc = self::string($in['description']);
            if (mb_strlen($desc) > 2000) {
                $errors['description'] = 'Description is too long (max 2000 characters).';
            }
            $out['description'] = $desc;
        }
        if (array_key_exists('status', $in)) {
            if (!is_string($in['status']) || !in_array($in['status'], self::STATUSES, true)) {
                $errors['status'] = 'Status must be one of: ' . implode(', ', self::STATUSES) . '.';
            }
            $out['status'] = $in['status'];
        }
        if (array_key_exists('position', $in)) {
            if (!is_int($in['position']) || $in['position'] < 0 || $in['position'] > 10000) {
                $errors['position'] = 'Position must be a non-negative integer.';
            }
            $out['position'] = $in['position'];
        }
        if (array_key_exists('assignee_id', $in)) {
            if ($in['assignee_id'] !== null && !is_int($in['assignee_id'])) {
                $errors['assignee_id'] = 'Assignee must be a user id or null.';
            }
            $out['assignee_id'] = $in['assignee_id'];
        }

        if ($errors) {
            throw new ApiException(422, 'Please fix the highlighted fields.', $errors);
        }
        return $out;
    }

    private static function string(mixed $v): string
    {
        return is_string($v) ? trim($v) : '';
    }
}
