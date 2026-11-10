<?php
declare(strict_types=1);

// Creates a demo account with realistic sample data (deterministic).
//   php bin/seed.php
// Sign in with  demo@example.com / demo-password-123   (local use only: do NOT run this on a public server)

require __DIR__ . '/../src/bootstrap.php';

use App\Applications;
use App\Auth;
use App\Database;

$pdo = Database::connect();
$email = 'demo@example.com';

$exists = $pdo->prepare('SELECT id FROM users WHERE email = ?');
$exists->execute([$email]);
if ($exists->fetchColumn()) {
    echo "Demo user already exists. Delete storage/app.sqlite to start over.\n";
    exit(0);
}

$user = Auth::register($pdo, 'Demo User', $email, 'demo-password-123');
$repo = new Applications($pdo);
mt_srand(7);

$companies = [
    ['Northwind Labs', 'Junior Data Analyst', 'Remote'], ['Brightpath Systems', 'Software Engineer I', 'Hybrid'],
    ['Lumen Analytics', 'Data Scientist (Entry)', 'On-site'], ['Cobalt Cloud', 'Full Stack Developer', 'Remote'],
    ['Harbor Fintech', 'Backend Engineer', 'Hybrid'], ['Orchid Health', 'Data Engineer', 'On-site'],
    ['Pixel Forge', 'Web Developer', 'Remote'], ['Summit Retail Tech', 'Graduate Software Engineer', 'Hybrid'],
    ['Quanta Insights', 'BI Analyst', 'On-site'], ['Maple Logistics', 'PHP Developer', 'Remote'],
    ['Evergreen Labs', 'ML Engineer (Junior)', 'Hybrid'], ['Atlas Payments', 'Full Stack Engineer', 'Remote'],
    ['Skyline Media', 'Junior Developer', 'On-site'], ['Nimbus AI', 'Data Analyst', 'Remote'],
    ['Vertex Gaming', 'Software Developer', 'Hybrid'], ['Coral Education', 'Web Application Developer', 'Remote'],
    ['Ironclad Security', 'Security Analyst (Junior)', 'On-site'], ['Zephyr Travel', 'Full Stack Developer', 'Hybrid'],
    ['Delta Energy Tech', 'Data Scientist', 'On-site'], ['Foxglove Studio', 'Frontend / PHP Developer', 'Remote'],
    ['Granite Insurance', 'Software Engineer', 'Hybrid'], ['Helix Biotech', 'Bioinformatics Analyst', 'On-site'],
];

$today = new DateTimeImmutable('today');
$added = 0;
foreach ($companies as $i => [$company, $role, $location]) {
    $applied = $today->modify('-' . mt_rand(3, 75) . ' days');
    $events = [['applied', $applied->format('Y-m-d')]];
    $status = 'applied';
    $cursor = $applied;

    if (mt_rand(1, 100) <= 60) {                       // got a reply
        $cursor = $cursor->modify('+' . mt_rand(2, 14) . ' days');
        if ($cursor <= $today) {
            $status = 'screening';
            $events[] = [$status, $cursor->format('Y-m-d')];
            if (mt_rand(1, 100) <= 65) {               // moved on to interviews
                $cursor = $cursor->modify('+' . mt_rand(3, 10) . ' days');
                if ($cursor <= $today) {
                    $status = 'interview';
                    $events[] = [$status, $cursor->format('Y-m-d')];
                    $roll = mt_rand(1, 100);
                    $cursor = $cursor->modify('+' . mt_rand(4, 14) . ' days');
                    if ($cursor <= $today && $roll <= 25) {
                        $status = 'offer';
                        $events[] = [$status, $cursor->format('Y-m-d')];
                    } elseif ($cursor <= $today && $roll <= 70) {
                        $status = 'rejected';
                        $events[] = [$status, $cursor->format('Y-m-d')];
                    }
                }
            } elseif (mt_rand(1, 100) <= 55) {
                $cursor = $cursor->modify('+' . mt_rand(2, 9) . ' days');
                if ($cursor <= $today) {
                    $status = 'rejected';
                    $events[] = [$status, $cursor->format('Y-m-d')];
                }
            }
        }
    } elseif (mt_rand(1, 100) <= 30) {                 // ghosted then rejected
        $cursor = $applied->modify('+' . mt_rand(20, 40) . ' days');
        if ($cursor <= $today) {
            $status = 'rejected';
            $events[] = [$status, $cursor->format('Y-m-d')];
        }
    }

    $appId = $repo->create($user['id'], [
        'company' => $company, 'role' => $role, 'url' => 'https://example.com/careers/' . ($i + 100), 'location' => $location,
        'status' => $status, 'applied_on' => $applied->format('Y-m-d'), 'salary_note' => '',
        'notes' => $status === 'interview' ? "Prepare: system design basics, portfolio walkthrough.\nAsk about team structure." : '',
        'status_date' => end($events)[1],
    ], $events);
    $added++;

    // A follow-up reminder for apps that are still waiting.
    if ($status === 'applied' && $i % 2 === 0) {
        $repo->addReminder($user['id'], $appId, $applied->modify('+7 days')->format('Y-m-d'), 'Follow up with ' . $company);
    }
}

foreach ([['Orbit Robotics', 'Software Engineer'], ['Kite Analytics', 'Data Scientist']] as [$company, $role]) {
    $repo->create($user['id'], [
        'company' => $company, 'role' => $role, 'url' => '', 'location' => 'Remote',
        'status' => 'wishlist', 'applied_on' => '', 'salary_note' => '', 'notes' => 'Dream company: apply when portfolio is ready.',
        'status_date' => date('Y-m-d'),
    ]);
    $added++;
}

echo "Seeded $added applications. Sign in as $email / demo-password-123\n";
