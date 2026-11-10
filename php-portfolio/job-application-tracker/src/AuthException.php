<?php
declare(strict_types=1);

namespace App;

use RuntimeException;

/** Messages in these exceptions are safe to show to the user. */
final class AuthException extends RuntimeException
{
}
