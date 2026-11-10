<?php
declare(strict_types=1);

namespace App;

use InvalidArgumentException;
use PDO;

/**
 * Read-side queries for an imported dataset. User-supplied column names are NEVER put into SQL
 * directly: they are looked up in the dataset's stored column list first (a whitelist),
 * and values always travel as bound parameters.
 */
final class Stats
{
    private const AGGREGATES = ['sum', 'avg', 'min', 'max', 'count'];

    /** @var array{id:int,name:string,table_name:string,columns:array,row_count:int,report:array,created_at:string} */
    private array $dataset;

    public function __construct(private PDO $pdo, int $datasetId)
    {
        $stmt = $pdo->prepare('SELECT * FROM datasets WHERE id = ?');
        $stmt->execute([$datasetId]);
        $row = $stmt->fetch();
        if (!$row) {
            throw new InvalidArgumentException('Dataset not found.');
        }
        $row['columns'] = json_decode($row['columns_json'], true);
        $row['report'] = json_decode($row['report_json'], true) ?: [];
        $this->dataset = $row;
    }

    public static function quote(string $identifier): string
    {
        return '"' . str_replace('"', '""', $identifier) . '"';
    }

    public function dataset(): array
    {
        return $this->dataset;
    }

    /** @return array<string,array{name:string,label:string,type:string}> keyed by column name */
    public function columns(): array
    {
        $out = [];
        foreach ($this->dataset['columns'] as $c) {
            $out[$c['name']] = $c;
        }
        return $out;
    }

    private function column(string $name): array
    {
        $cols = $this->columns();
        if (!isset($cols[$name])) {
            throw new InvalidArgumentException('Unknown column.');
        }
        return $cols[$name];
    }

    private function table(): string
    {
        return self::quote($this->dataset['table_name']);
    }

    /**
     * @param array<string,string> $filters column => exact value
     * @return array{0:string,1:array<int,string>} WHERE clause and bound values
     */
    private function where(array $filters, string $search = ''): array
    {
        $parts = [];
        $params = [];
        foreach ($filters as $col => $value) {
            $c = $this->column((string) $col);
            if ($c['type'] === 'date' && preg_match('/^\d{4}-\d{2}$/', (string) $value)) {
                $parts[] = 'substr(' . self::quote($c['name']) . ', 1, 7) = ?';
            } else {
                $parts[] = self::quote($c['name']) . ' = ?';
            }
            $params[] = (string) $value;
        }
        if ($search !== '') {
            $like = [];
            foreach ($this->dataset['columns'] as $c) {
                $like[] = 'CAST(' . self::quote($c['name']) . " AS TEXT) LIKE ? ESCAPE '\\'";
                $params[] = '%' . addcslashes($search, '%_\\') . '%';
            }
            $parts[] = '(' . implode(' OR ', $like) . ')';
        }
        return [$parts ? ' WHERE ' . implode(' AND ', $parts) : '', $params];
    }

    /** Totals, plus min/max/avg/sum/missing for every numeric column. */
    public function summary(array $filters = []): array
    {
        [$where, $params] = $this->where($filters);
        $selects = ['COUNT(*) AS total_rows'];
        $numeric = [];
        foreach ($this->dataset['columns'] as $c) {
            if (in_array($c['type'], ['integer', 'real'], true)) {
                $q = self::quote($c['name']);
                $numeric[] = $c;
                $selects[] = "COUNT($q) AS \"{$c['name']}__n\", SUM($q) AS \"{$c['name']}__sum\", AVG($q) AS \"{$c['name']}__avg\", "
                    . "MIN($q) AS \"{$c['name']}__min\", MAX($q) AS \"{$c['name']}__max\"";
            }
        }
        $stmt = $this->pdo->prepare('SELECT ' . implode(', ', $selects) . ' FROM ' . $this->table() . $where);
        $stmt->execute($params);
        $r = $stmt->fetch();

        $out = ['total_rows' => (int) $r['total_rows'], 'columns' => []];
        foreach ($numeric as $c) {
            $n = $c['name'];
            $out['columns'][] = [
                'name' => $n,
                'label' => $c['label'],
                'non_null' => (int) $r["{$n}__n"],
                'missing' => (int) $r['total_rows'] - (int) $r["{$n}__n"],
                'sum' => $this->round($r["{$n}__sum"]),
                'avg' => $this->round($r["{$n}__avg"]),
                'min' => $this->round($r["{$n}__min"]),
                'max' => $this->round($r["{$n}__max"]),
            ];
        }
        return $out;
    }

    /**
     * GROUP BY query for charts.
     * @param string $grain 'value' or 'month' (month only applies to date columns)
     * @return array{labels:string[], values:float[]}
     */
    public function group(string $groupBy, ?string $metric, string $agg, string $grain, array $filters = []): array
    {
        $g = $this->column($groupBy);
        $agg = strtolower($agg);
        if (!in_array($agg, self::AGGREGATES, true)) {
            throw new InvalidArgumentException('Unknown aggregate.');
        }

        if ($metric === null || $metric === '' || $agg === 'count') {
            $metricExpr = 'COUNT(*)';
        } else {
            $m = $this->column($metric);
            if (!in_array($m['type'], ['integer', 'real'], true)) {
                throw new InvalidArgumentException('Metric must be a numeric column.');
            }
            $metricExpr = strtoupper($agg) . '(' . self::quote($m['name']) . ')';
        }

        $isMonth = $g['type'] === 'date' && $grain === 'month';
        $groupExpr = $isMonth ? 'substr(' . self::quote($g['name']) . ', 1, 7)' : self::quote($g['name']);
        $chronological = $g['type'] === 'date' || in_array($g['type'], ['integer', 'real'], true);

        [$where, $params] = $this->where($filters);
        $where .= ($where === '' ? ' WHERE ' : ' AND ') . "$groupExpr IS NOT NULL";

        $sql = "SELECT $groupExpr AS label, $metricExpr AS value FROM " . $this->table() . $where
            . ' GROUP BY label ORDER BY ' . ($chronological ? 'label ASC' : 'value DESC') . ' LIMIT 60';
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($params);

        $labels = [];
        $values = [];
        foreach ($stmt->fetchAll() as $row) {
            $labels[] = (string) $row['label'];
            $values[] = $this->round($row['value']);
        }
        return ['labels' => $labels, 'values' => $values];
    }

    /** @return array{rows:array<int,array<string,mixed>>, total:int} */
    public function rows(array $filters, string $search, int $limit, int $offset): array
    {
        [$where, $params] = $this->where($filters, $search);

        $count = $this->pdo->prepare('SELECT COUNT(*) FROM ' . $this->table() . $where);
        $count->execute($params);

        $limit = max(1, min(100, $limit));
        $offset = max(0, $offset);
        $stmt = $this->pdo->prepare('SELECT * FROM ' . $this->table() . $where . " LIMIT $limit OFFSET $offset");
        $stmt->execute($params);

        return ['rows' => $stmt->fetchAll(), 'total' => (int) $count->fetchColumn()];
    }

    /** Streams the cleaned dataset as CSV (with formula-injection protection for spreadsheet apps). */
    public function exportCsv($out, array $filters = []): void
    {
        [$where, $params] = $this->where($filters);
        $stmt = $this->pdo->prepare('SELECT * FROM ' . $this->table() . $where);
        $stmt->execute($params);

        fputcsv($out, array_column($this->dataset['columns'], 'label'), ',', '"', '');
        while ($row = $stmt->fetch(PDO::FETCH_NUM)) {
            $row = array_map(static function ($v) {
                if (is_string($v) && $v !== '' && strpbrk($v[0], "=+-@\t\r") !== false && !is_numeric($v)) {
                    return "'" . $v;
                }
                return $v;
            }, $row);
            fputcsv($out, $row, ',', '"', '');
        }
    }

    private function round(mixed $v): float|int|null
    {
        if ($v === null) {
            return null;
        }
        $f = round((float) $v, 2);
        return floor($f) == $f ? (int) $f : $f;
    }
}
