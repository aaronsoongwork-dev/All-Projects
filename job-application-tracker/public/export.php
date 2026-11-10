<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\Applications;
use App\Database;
use App\Status;

$pdo = Database::connect();
$user = require_login($pdo);

/** Spreadsheet apps execute cells that start with = + - @ as formulas; prefix them so pasted data stays inert. */
function safe_cell(mixed $v): string
{
    $s = (string) $v;
    return ($s !== '' && strpbrk($s[0], "=+-@\t\r") !== false) ? "'" . $s : $s;
}

header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="job-applications-' . date('Y-m-d') . '.csv"');
header('X-Content-Type-Options: nosniff');

$out = fopen('php://output', 'wb');
fwrite($out, "\xEF\xBB\xBF"); // BOM so Excel reads UTF-8
fputcsv($out, ['Company', 'Role', 'Status', 'Applied on', 'Location', 'Pay', 'Link', 'Notes', 'Last updated'], ',', '"', '');

foreach ((new Applications($pdo))->all($user['id']) as $a) {
    fputcsv($out, array_map('safe_cell', [
        $a['company'], $a['role'], Status::label($a['status']), $a['applied_on'] ?? '', $a['location'],
        $a['salary_note'], $a['url'], $a['notes'], $a['updated_at'],
    ]), ',', '"', '');
}
fclose($out);
