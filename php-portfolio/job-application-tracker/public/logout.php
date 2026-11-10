<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\Auth;

// POST + CSRF so another website cannot log you out by embedding an image or link.
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    redirect('index.php');
}
csrf_check();
Auth::signOut();
redirect('login.php');
