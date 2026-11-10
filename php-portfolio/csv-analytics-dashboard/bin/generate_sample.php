<?php
declare(strict_types=1);

// Generates sample-data/sales.csv (deterministic). Run: php bin/generate_sample.php
// The file is intentionally a little messy (blank lines, duplicates, "$" prices) so the cleaning step has work to do.

mt_srand(42);
$regions = ['North', 'South', 'East', 'West', 'Central'];
$catalog = [
    'Electronics' => [['Headphones', 59.9], ['Webcam', 45.0], ['Keyboard', 79.5], ['Monitor', 219.0]],
    'Furniture'   => [['Desk', 249.0], ['Chair', 189.0], ['Lamp', 34.5]],
    'Stationery'  => [['Notebook', 4.5], ['Pen Set', 12.0], ['Planner', 18.0]],
    'Software'    => [['Antivirus', 39.0], ['Office Suite', 99.0]],
];

$fh = fopen(__DIR__ . '/../sample-data/sales.csv', 'wb');
fputcsv($fh, ['Order ID', 'Order Date', 'Region', 'Category', 'Product', 'Units', 'Unit Price', 'Discount', 'Revenue'], ',', '"', '');

$start = strtotime('2025-01-01');
$prev = null;
for ($i = 1; $i <= 1200; $i++) {
    $date = date('Y-m-d', $start + mt_rand(0, 364) * 86400);
    $region = $regions[mt_rand(0, 4)];
    $category = array_keys($catalog)[mt_rand(0, 3)];
    [$product, $price] = $catalog[$category][mt_rand(0, count($catalog[$category]) - 1)];
    $units = mt_rand(1, 8);
    $discount = [0, 0, 0, 0.05, 0.1, 0.15][mt_rand(0, 5)];
    $revenue = round($units * $price * (1 - $discount), 2);

    // Winter/holiday seasonality for a nicer trend line
    if (in_array((int) date('n', strtotime($date)), [11, 12], true)) {
        $units += mt_rand(0, 3);
        $revenue = round($units * $price * (1 - $discount), 2);
    }

    $priceCell = ($i % 25 === 0) ? '$' . number_format($price, 2) : $price; // messy: currency symbols
    $row = [10000 + $i, $date, $region, $category, $product, $units, $priceCell, $discount, $revenue];
    fputcsv($fh, $row, ',', '"', '');

    if ($i % 150 === 0) {
        fputcsv($fh, $row, ',', '"', '');   // exact duplicate row
        fwrite($fh, "\n");                   // blank line
    }
}
fclose($fh);
echo "Wrote sample-data/sales.csv\n";
