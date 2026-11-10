<?php
declare(strict_types=1);

// Tiny PSR-4 style autoloader so the app runs without `composer install`.
// (Composer is only needed for the dev dependency PHPUnit.)
spl_autoload_register(static function (string $class): void {
    $prefix = 'App\\';
    if (strncmp($class, $prefix, strlen($prefix)) !== 0) {
        return;
    }
    $file = __DIR__ . '/' . str_replace('\\', '/', substr($class, strlen($prefix))) . '.php';
    if (is_file($file)) {
        require $file;
    }
});
