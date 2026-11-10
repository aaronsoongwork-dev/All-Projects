<?php
declare(strict_types=1);

namespace App;

use RuntimeException;

/** An error that is safe to show to the API client. */
final class ApiException extends RuntimeException
{
    /** @param array<string,string> $errors field => message */
    public function __construct(
        public readonly int $status,
        string $message,
        public readonly array $errors = []
    ) {
        parent::__construct($message);
    }
}
