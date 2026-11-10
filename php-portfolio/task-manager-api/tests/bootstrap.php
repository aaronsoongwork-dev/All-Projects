<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

$composer = __DIR__ . '/../vendor/autoload.php';
if (is_file($composer)) {
    require $composer;
}
