<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\Database;
use App\Stats;

try {
    $stats = new Stats(Database::connect(), (int) ($_GET['id'] ?? 0));
} catch (InvalidArgumentException) {
    http_response_code(404);
    exit('Dataset not found.');
}

$filters = [];
foreach ((array) ($_GET['filter'] ?? []) as $col => $val) {
    if (is_string($col) && is_string($val) && $val !== '') {
        $filters[$col] = $val;
    }
}

$filename = preg_replace('/[^A-Za-z0-9_-]+/', '_', $stats->dataset()['name']) . '_cleaned.csv';
header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $filename . '"');

$out = fopen('php://output', 'wb');
fwrite($out, "\xEF\xBB\xBF"); // BOM so Excel reads UTF-8 correctly
try {
    $stats->exportCsv($out, $filters);
} catch (InvalidArgumentException) {
    // Unknown filter column: output just the BOM; nothing sensitive leaks.
}
fclose($out);
