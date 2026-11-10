<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\Database;
use App\Stats;

try {
    $stats = new Stats(Database::connect(), (int) ($_GET['id'] ?? 0));

    // filter[column]=value  (columns are validated against the dataset's own column list)
    $filters = [];
    foreach ((array) ($_GET['filter'] ?? []) as $col => $val) {
        if (is_string($col) && is_string($val) && $val !== '') {
            $filters[$col] = $val;
        }
    }

    switch ($_GET['action'] ?? '') {
        case 'summary':
            json_response($stats->summary($filters));

        case 'group':
            json_response($stats->group(
                (string) ($_GET['group'] ?? ''),
                isset($_GET['metric']) ? (string) $_GET['metric'] : null,
                (string) ($_GET['agg'] ?? 'count'),
                (string) ($_GET['grain'] ?? 'value'),
                $filters
            ));

        case 'rows':
            json_response($stats->rows(
                $filters,
                trim((string) ($_GET['q'] ?? '')),
                (int) ($_GET['limit'] ?? 15),
                (int) ($_GET['offset'] ?? 0)
            ));

        default:
            json_response(['error' => 'Unknown action.'], 400);
    }
} catch (InvalidArgumentException $e) {
    json_response(['error' => $e->getMessage()], 400);
} catch (Throwable $e) {
    error_log($e->getMessage());
    json_response(['error' => 'Server error.'], 500);
}
