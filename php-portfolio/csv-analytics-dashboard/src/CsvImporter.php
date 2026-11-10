<?php
declare(strict_types=1);

namespace App;

use PDO;
use RuntimeException;

/**
 * Reads an uploaded CSV, cleans it, infers column types and stores it in its own SQLite table.
 *
 * Cleaning steps: strip BOM, detect delimiter, fix encoding, trim cells, drop blank rows,
 * drop exact duplicate rows, turn "$1,234.50" into 1234.5 when a whole column is numeric.
 */
final class CsvImporter
{
    public const MAX_ROWS = 50000;
    public const MAX_COLUMNS = 40;

    public function __construct(private PDO $pdo)
    {
    }

    /** @return array{id:int, report:array<string,int>} */
    public function import(string $path, string $displayName): array
    {
        $fh = fopen($path, 'rb');
        if ($fh === false) {
            throw new RuntimeException('Could not read the uploaded file.');
        }

        try {
            $delimiter = $this->detectDelimiter($fh);
            $header = fgetcsv($fh, 0, $delimiter, '"', '');
            if ($header === false || $header === [null]) {
                throw new RuntimeException('The CSV file is empty.');
            }
            $header = array_map(fn($v) => trim($this->toUtf8((string) $v)), $header);
            if (count($header) > self::MAX_COLUMNS) {
                throw new RuntimeException('Too many columns (max ' . self::MAX_COLUMNS . ').');
            }

            $n = count($header);
            $rows = [];
            $seen = [];
            $report = ['rows_read' => 0, 'blank_rows_removed' => 0, 'duplicates_removed' => 0, 'rows_imported' => 0];

            while (($r = fgetcsv($fh, 0, $delimiter, '"', '')) !== false) {
                $report['rows_read']++;
                if ($report['rows_read'] > self::MAX_ROWS) {
                    throw new RuntimeException('Too many rows (max ' . self::MAX_ROWS . ').');
                }
                $r = array_map(fn($v) => trim($this->toUtf8((string) $v)), $r);
                if (implode('', $r) === '') {
                    $report['blank_rows_removed']++;
                    continue;
                }
                $r = array_slice(array_pad($r, $n, ''), 0, $n);
                $key = md5(implode("\x1f", $r));
                if (isset($seen[$key])) {
                    $report['duplicates_removed']++;
                    continue;
                }
                $seen[$key] = true;
                $rows[] = $r;
            }
        } finally {
            fclose($fh);
        }

        if ($rows === []) {
            throw new RuntimeException('The CSV has a header but no data rows.');
        }

        $names = $this->uniqueColumnNames($header);
        $columns = [];
        foreach ($names as $i => $name) {
            $values = array_column($rows, $i);
            $type = $this->inferType($values);
            // Identifiers (order_id, zip_code, ...) are labels, not measures: keep them as text.
            if (in_array($type, ['integer', 'real'], true) && preg_match('/(^|_)(id|no|code|zip|phone)$/', $name)) {
                $type = 'text';
            }
            $columns[] = [
                'name' => $name,
                'label' => $header[$i] !== '' ? $header[$i] : 'Column ' . ($i + 1),
                'type' => $type,
                'distinct' => count(array_unique(array_filter($values, fn($v) => $v !== ''))),
            ];
        }

        $report['rows_imported'] = count($rows);

        $this->pdo->beginTransaction();
        try {
            $stmt = $this->pdo->prepare(
                'INSERT INTO datasets (name, table_name, columns_json, row_count, report_json) VALUES (?, ?, ?, ?, ?)'
            );
            $stmt->execute([
                mb_substr($displayName, 0, 120),
                'pending_' . bin2hex(random_bytes(6)),
                json_encode($columns),
                count($rows),
                json_encode($report),
            ]);
            $id = (int) $this->pdo->lastInsertId();
            $table = 'ds_' . $id;
            $this->pdo->prepare('UPDATE datasets SET table_name = ? WHERE id = ?')->execute([$table, $id]);

            $defs = [];
            foreach ($columns as $c) {
                $defs[] = Stats::quote($c['name']) . ' ' . ($c['type'] === 'date' ? 'TEXT' : strtoupper($c['type']));
            }
            $this->pdo->exec('CREATE TABLE ' . Stats::quote($table) . ' (' . implode(', ', $defs) . ')');

            $placeholders = implode(', ', array_fill(0, count($columns), '?'));
            $insert = $this->pdo->prepare('INSERT INTO ' . Stats::quote($table) . ' VALUES (' . $placeholders . ')');
            foreach ($rows as $r) {
                $insert->execute($this->convertRow($r, $columns));
            }
            $this->pdo->commit();
        } catch (\Throwable $e) {
            $this->pdo->rollBack();
            throw $e;
        }

        return ['id' => $id, 'report' => $report];
    }

    /** @param resource $fh */
    private function detectDelimiter($fh): string
    {
        $bom = fread($fh, 3);
        if ($bom !== "\xEF\xBB\xBF") {
            rewind($fh);
        }
        $pos = ftell($fh);
        $line = (string) fgets($fh);
        fseek($fh, $pos);

        $best = ',';
        $bestCount = 0;
        foreach ([',', ';', "\t", '|'] as $d) {
            $c = substr_count($line, $d);
            if ($c > $bestCount) {
                $best = $d;
                $bestCount = $c;
            }
        }
        return $best;
    }

    private function toUtf8(string $v): string
    {
        if ($v === '' || mb_check_encoding($v, 'UTF-8')) {
            return $v;
        }
        return (string) iconv('Windows-1252', 'UTF-8//IGNORE', $v);
    }

    /** @param string[] $header @return string[] */
    private function uniqueColumnNames(array $header): array
    {
        $used = [];
        $out = [];
        foreach ($header as $i => $label) {
            $name = strtolower(trim((string) preg_replace('/[^A-Za-z0-9]+/', '_', $label), '_'));
            if ($name === '') {
                $name = 'col_' . ($i + 1);
            }
            if (ctype_digit($name[0])) {
                $name = 'c_' . $name;
            }
            $base = $name;
            $k = 2;
            while (isset($used[$name])) {
                $name = $base . '_' . $k++;
            }
            $used[$name] = true;
            $out[] = $name;
        }
        return $out;
    }

    /** @param string[] $values */
    private function inferType(array $values): string
    {
        $filled = array_values(array_filter($values, fn($v) => $v !== ''));
        if ($filled === []) {
            return 'text';
        }

        $allInt = $allNum = $allDate = true;
        foreach ($filled as $v) {
            $num = self::normalizeNumber($v);
            if ($num === null) {
                $allInt = $allNum = false;
            } elseif (!preg_match('/^-?\d+$/', $num) || (strlen($num) > 1 && ltrim($num, '-')[0] === '0')) {
                $allInt = false; // decimals, or IDs/zip codes with leading zeros
            }
            if (!preg_match('/^\d{4}-\d{2}-\d{2}/', $v) || strtotime(substr($v, 0, 10)) === false) {
                $allDate = false;
            }
            if (!$allInt && !$allNum && !$allDate) {
                return 'text';
            }
        }
        // Leading zeros mean "identifier", not a number.
        if ($allNum) {
            foreach ($filled as $v) {
                if (preg_match('/^0\d+$/', $v)) {
                    return 'text';
                }
            }
        }
        return $allInt ? 'integer' : ($allNum ? 'real' : ($allDate ? 'date' : 'text'));
    }

    /** Returns a clean numeric string, or null when the value is not a number. */
    private static function normalizeNumber(string $v): ?string
    {
        if (preg_match('/^-?\$?\d{1,3}(,\d{3})+(\.\d+)?$/', $v)) {
            $v = str_replace([',', '$'], '', $v);
        } elseif (preg_match('/^-?\$\d+(\.\d+)?$/', $v)) {
            $v = str_replace('$', '', $v);
        }
        return preg_match('/^-?(\d+\.?\d*|\.\d+)$/', $v) ? $v : null;
    }

    /** @param string[] $row @param array<int,array{name:string,label:string,type:string}> $columns @return array<int,mixed> */
    private function convertRow(array $row, array $columns): array
    {
        $out = [];
        foreach ($columns as $i => $c) {
            $v = $row[$i];
            if ($v === '') {
                $out[] = null;
            } elseif ($c['type'] === 'integer') {
                $out[] = (int) self::normalizeNumber($v);
            } elseif ($c['type'] === 'real') {
                $out[] = (float) self::normalizeNumber($v);
            } else {
                $out[] = $v;
            }
        }
        return $out;
    }
}
