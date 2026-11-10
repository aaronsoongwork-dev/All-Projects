# CSV Analytics Dashboard

Upload any CSV and get an interactive dashboard: automatic cleaning, type detection, summary statistics, charts you can drill into, a searchable data table, and a cleaned-CSV download.

Built with **PHP 8.1+, SQLite (PDO) and vanilla JavaScript + Chart.js**. No framework, no database server, no Composer install needed.

<!-- Add a screenshot after you run it: ![Dashboard](docs/dashboard.png) -->

## Features

- **Smart import**: strips the BOM, detects the delimiter (`,` `;` tab `|`), fixes Windows-1252 encoding, trims cells, removes blank and duplicate rows, and reports exactly what it removed.
- **Type inference**: integer, decimal, date or text per column. `"$1,234.50"` becomes `1234.5`; IDs and zip codes with leading zeros stay text.
- **Each dataset gets its own SQL table**, so all analysis is real SQL (`SUM / AVG / MIN / MAX / COUNT ... GROUP BY`) rather than loops in PHP.
- **Dashboard**: KPI tiles, group-by chart (bar / line / doughnut), monthly grain for date columns, click a bar to filter everything, full-text search, pagination.
- **JSON API** (`public/api.php`) that the frontend consumes.
- **Cleaned CSV export** that respects your active filters.

## Run it

Requirements: PHP 8.1+ with the `pdo_sqlite` extension (enabled by default in most installs).

```bash
git clone <your-repo-url>
cd csv-analytics-dashboard
php -S localhost:8000 -t public
```

Open <http://localhost:8000> and upload `sample-data/sales.csv` (1,200 orders with deliberately messy rows). Regenerate it with `php bin/generate_sample.php`.

The charts load Chart.js from a CDN, so you need an internet connection the first time.

## Project structure

```
public/            web root (index.php upload page, dataset.php dashboard, api.php, export.php, app.js, style.css)
src/Database.php   PDO + SQLite connection and schema
src/CsvImporter.php  parsing, cleaning, type inference, import in a transaction
src/Stats.php      all read queries (summary, group-by, search, export)
src/bootstrap.php  autoloader, escaping and CSRF helpers
sample-data/       demo CSV
bin/               sample data generator
```

## Security notes (what I deliberately handled)

- **SQL injection**: user-supplied column names are checked against the dataset's stored column list before they touch SQL; values are always bound parameters. Verified with injection attempts in the column and filter parameters.
- **CSRF** tokens on every state-changing form (upload, delete).
- **XSS**: server output is escaped with `htmlspecialchars`; the frontend renders cell data with `textContent`, and the config JSON uses `JSON_HEX_*` flags.
- **CSV formula injection**: exported cells starting with `=`, `+`, `-` or `@` are prefixed so Excel will not execute them.
- **Upload limits**: `.csv` only, 5 MB, 50,000 rows, 40 columns. Uploaded files are parsed from the temp path and never stored.

## Known limitations / ideas for next steps

- No user accounts: all datasets are visible to anyone who can reach the app. Add login (see my *Task Manager* project) before deploying publicly.
- Single-column group-by; could add multi-series charts and date-range filters.
- Streamed import for files larger than 50k rows; outlier detection and a simple correlation view would suit a data-science angle.

## Resume bullet

> Built a PHP/SQLite analytics dashboard that ingests, cleans and type-infers arbitrary CSV files (delimiter/encoding detection, deduplication) and serves SQL-aggregated insights through a JSON API to an interactive Chart.js frontend; hardened against SQL injection, CSRF, XSS and CSV formula injection.
