<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\Api;
use App\Database;

(new Api(Database::connect()))->handle();
