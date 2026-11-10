<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\Database;
use App\Stats;

try {
    $stats = new Stats(Database::connect(), (int) ($_GET['id'] ?? 0));
} catch (InvalidArgumentException) {
    http_response_code(404);
    exit('Dataset not found. <a href="index.php">Back</a>');
}
$ds = $stats->dataset();
$config = [
    'id' => $ds['id'],
    'columns' => array_values($stats->columns()),
];
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= h($ds['name']) ?> - CSV Analytics Dashboard</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
<header class="top"><a href="index.php" class="brand">CSV Analytics Dashboard</a></header>
<main class="wrap">
    <div class="row between">
        <h1><?= h($ds['name']) ?></h1>
        <a class="btn" id="export" href="export.php?id=<?= (int) $ds['id'] ?>">Download cleaned CSV</a>
    </div>

    <?php if (isset($_GET['imported']) && $ds['report']): ?>
        <p class="alert ok">
            Imported <?= number_format((int) $ds['report']['rows_imported']) ?> of <?= number_format((int) $ds['report']['rows_read']) ?> rows
            (<?= (int) $ds['report']['blank_rows_removed'] ?> blank and <?= (int) $ds['report']['duplicates_removed'] ?> duplicate rows removed).
        </p>
    <?php endif; ?>

    <div id="chips" class="chips"></div>
    <section id="kpis" class="kpis"></section>

    <section class="card">
        <div class="controls">
            <label>Group by <select id="groupBy"></select></label>
            <label id="grainWrap" hidden>Grain
                <select id="grain"><option value="month">Month</option><option value="value">Exact date</option></select>
            </label>
            <label>Metric <select id="metric"></select></label>
            <label>Aggregate
                <select id="agg">
                    <option value="sum">Sum</option><option value="avg">Average</option>
                    <option value="min">Min</option><option value="max">Max</option>
                </select>
            </label>
            <label>Chart
                <select id="chartType"><option value="bar">Bar</option><option value="line">Line</option><option value="doughnut">Doughnut</option></select>
            </label>
        </div>
        <p class="muted small">Tip: click a bar to filter the whole dashboard to that value.</p>
        <div class="chart-box"><canvas id="chart"></canvas></div>
    </section>

    <section class="card">
        <div class="row between">
            <h2>Data preview</h2>
            <input type="search" id="search" placeholder="Search all columns...">
        </div>
        <div class="scroll"><table id="table"></table></div>
        <div class="row between">
            <span id="pageInfo" class="muted small"></span>
            <span><button class="btn small" id="prev">Previous</button> <button class="btn small" id="next">Next</button></span>
        </div>
    </section>
</main>

<script>window.DASHBOARD = <?= json_encode($config, JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT) ?>;</script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<script src="app.js"></script>
</body>
</html>
