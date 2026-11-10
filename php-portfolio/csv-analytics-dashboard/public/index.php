<?php
declare(strict_types=1);

require __DIR__ . '/../src/bootstrap.php';

use App\CsvImporter;
use App\Database;

start_session();
$pdo = Database::connect();
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    csrf_check();
    $action = (string) ($_POST['action'] ?? '');

    if ($action === 'upload') {
        $file = $_FILES['csv'] ?? null;
        try {
            if (!$file || $file['error'] !== UPLOAD_ERR_OK) {
                throw new RuntimeException('Please choose a CSV file (max 5 MB).');
            }
            if ($file['size'] > 5 * 1024 * 1024) {
                throw new RuntimeException('File is too large (max 5 MB).');
            }
            if (strtolower(pathinfo($file['name'], PATHINFO_EXTENSION)) !== 'csv') {
                throw new RuntimeException('Only .csv files are accepted.');
            }
            $result = (new CsvImporter($pdo))->import($file['tmp_name'], pathinfo($file['name'], PATHINFO_FILENAME));
            header('Location: dataset.php?id=' . $result['id'] . '&imported=1');
            exit;
        } catch (RuntimeException $e) {
            $error = $e->getMessage();
        }
    } elseif ($action === 'delete') {
        $id = (int) ($_POST['id'] ?? 0);
        $stmt = $pdo->prepare('SELECT table_name FROM datasets WHERE id = ?');
        $stmt->execute([$id]);
        if ($table = $stmt->fetchColumn()) {
            $pdo->exec('DROP TABLE IF EXISTS "' . str_replace('"', '""', $table) . '"');
            $pdo->prepare('DELETE FROM datasets WHERE id = ?')->execute([$id]);
        }
        header('Location: index.php');
        exit;
    }
}

$datasets = $pdo->query('SELECT id, name, row_count, created_at FROM datasets ORDER BY id DESC')->fetchAll();
?>
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>CSV Analytics Dashboard</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
<header class="top"><a href="index.php" class="brand">CSV Analytics Dashboard</a></header>
<main class="wrap">
    <section class="card">
        <h1>Upload a CSV</h1>
        <p class="muted">The file is cleaned (blank rows, duplicates, currency symbols), types are detected, and it is stored in SQLite. Try <code>sample-data/sales.csv</code>.</p>
        <?php if ($error): ?><p class="alert"><?= h($error) ?></p><?php endif; ?>
        <form method="post" enctype="multipart/form-data" class="row">
            <input type="hidden" name="csrf" value="<?= h(csrf_token()) ?>">
            <input type="hidden" name="action" value="upload">
            <input type="file" name="csv" accept=".csv,text/csv" required>
            <button class="btn" type="submit">Upload &amp; analyse</button>
        </form>
    </section>

    <section class="card">
        <h2>Your datasets</h2>
        <?php if (!$datasets): ?>
            <p class="muted">Nothing here yet. Upload your first CSV above.</p>
        <?php else: ?>
            <table>
                <thead><tr><th>Name</th><th class="num">Rows</th><th>Uploaded (UTC)</th><th></th></tr></thead>
                <tbody>
                <?php foreach ($datasets as $d): ?>
                    <tr>
                        <td><a href="dataset.php?id=<?= (int) $d['id'] ?>"><?= h($d['name']) ?></a></td>
                        <td class="num"><?= number_format((int) $d['row_count']) ?></td>
                        <td><?= h($d['created_at']) ?></td>
                        <td class="right">
                            <form method="post" onsubmit="return confirm('Delete this dataset?')">
                                <input type="hidden" name="csrf" value="<?= h(csrf_token()) ?>">
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="id" value="<?= (int) $d['id'] ?>">
                                <button class="btn small danger" type="submit">Delete</button>
                            </form>
                        </td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        <?php endif; ?>
    </section>
</main>
</body>
</html>
