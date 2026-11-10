<?php
declare(strict_types=1);

// Router for PHP's built-in dev server:  php -S localhost:8000 -t public public/router.php
// (On Apache the included .htaccess does the same job.)

$path = (string) parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);

if (str_starts_with($path, '/api/')) {
    require __DIR__ . '/api.php';
    return true;
}

// Only files under /assets/ are served as static files; everything else is the single-page app.
if (str_starts_with($path, '/assets/') && !str_contains($path, '..') && is_file(__DIR__ . $path)) {
    return false;
}

header('Content-Type: text/html; charset=utf-8');
header("Content-Security-Policy: default-src 'self'; frame-ancestors 'none'");
header('X-Content-Type-Options: nosniff');
readfile(__DIR__ . '/index.html');
return true;
