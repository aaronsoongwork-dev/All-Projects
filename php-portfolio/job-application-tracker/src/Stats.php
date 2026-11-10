<?php
declare(strict_types=1);

namespace App;

use DateTimeImmutable;
use PDO;

/** Insight calculations. Everything is computed from the status_events log, per user. */
final class Stats
{
    public function __construct(private PDO $pdo)
    {
    }

    /**
     * @return array{
     *   total:int, applied:int, active:int, offers:int, rejected:int,
     *   responded:int, response_rate:?float, avg_days_to_response:?float,
     *   funnel:array<string,int>
     * }
     */
    public function overview(int $userId): array
    {
        $apps = $this->pdo->prepare('SELECT id, status, applied_on FROM applications WHERE user_id = ?');
        $apps->execute([$userId]);
        $apps = $apps->fetchAll();

        $events = $this->eventsByApp($userId);

        $out = [
            'total' => count($apps), 'applied' => 0, 'active' => 0, 'offers' => 0, 'rejected' => 0,
            'responded' => 0, 'response_rate' => null, 'avg_days_to_response' => null,
            'funnel' => ['applied' => 0, 'screening' => 0, 'interview' => 0, 'offer' => 0],
        ];
        $responseDays = [];

        foreach ($apps as $a) {
            if (in_array($a['status'], Status::ACTIVE, true)) {
                $out['active']++;
            }
            if (in_array($a['status'], ['offer', 'accepted'], true)) {
                $out['offers']++;
            }
            if ($a['status'] === 'rejected') {
                $out['rejected']++;
            }
            if ($a['applied_on'] === null) {
                continue; // still on the wishlist
            }
            $out['applied']++;

            $evs = $events[$a['id']] ?? [];

            // Highest happy-path stage ever reached (an offer implies you also had an interview, etc.)
            $best = 1;
            foreach ($evs as $e) {
                $best = max($best, Status::RANK[$e['status']] ?? 0);
            }
            foreach (['applied' => 1, 'screening' => 2, 'interview' => 3, 'offer' => 4] as $stage => $rank) {
                if ($best >= $rank) {
                    $out['funnel'][$stage]++;
                }
            }

            // First response = earliest screening/interview/offer/accepted/rejected event.
            $first = null;
            foreach ($evs as $e) {
                if (in_array($e['status'], Status::RESPONSES, true) && ($first === null || $e['changed_on'] < $first)) {
                    $first = $e['changed_on'];
                }
            }
            if ($first !== null) {
                $out['responded']++;
                $responseDays[] = max(0, $this->daysBetween($a['applied_on'], $first));
            }
        }

        if ($out['applied'] > 0) {
            $out['response_rate'] = round(100 * $out['responded'] / $out['applied'], 1);
        }
        if ($responseDays) {
            $out['avg_days_to_response'] = round(array_sum($responseDays) / count($responseDays), 1);
        }
        return $out;
    }

    /**
     * Average days an application spent in each stage, measured between consecutive status events.
     * @return array<string,array{avg:float,n:int}>
     */
    public function stageDurations(int $userId): array
    {
        $sums = [];
        foreach ($this->eventsByApp($userId) as $evs) {
            for ($i = 0; $i < count($evs) - 1; $i++) {
                $stage = $evs[$i]['status'];
                if (!in_array($stage, Status::ACTIVE, true)) {
                    continue;
                }
                $days = max(0, $this->daysBetween($evs[$i]['changed_on'], $evs[$i + 1]['changed_on']));
                $sums[$stage]['total'] = ($sums[$stage]['total'] ?? 0) + $days;
                $sums[$stage]['n'] = ($sums[$stage]['n'] ?? 0) + 1;
            }
        }
        $out = [];
        foreach (Status::ACTIVE as $stage) {
            if (isset($sums[$stage])) {
                $out[$stage] = ['avg' => round($sums[$stage]['total'] / $sums[$stage]['n'], 1), 'n' => $sums[$stage]['n']];
            }
        }
        return $out;
    }

    /**
     * Applications sent per week for the last $weeks weeks (Monday-based), oldest first, zero-filled.
     * @return array<string,int> 'YYYY-MM-DD' (Monday) => count
     */
    public function weekly(int $userId, int $weeks = 12): array
    {
        // Monday of the week containing applied_on (SQLite: jump to the coming Sunday, then back 6 days).
        $stmt = $this->pdo->prepare(
            "SELECT date(applied_on, 'weekday 0', '-6 days') AS week, COUNT(*) AS n
             FROM applications WHERE user_id = ? AND applied_on IS NOT NULL GROUP BY week"
        );
        $stmt->execute([$userId]);
        $found = $stmt->fetchAll(PDO::FETCH_KEY_PAIR);

        $out = [];
        $monday = new DateTimeImmutable('monday this week');
        for ($i = $weeks - 1; $i >= 0; $i--) {
            $key = $monday->modify("-$i weeks")->format('Y-m-d');
            $out[$key] = (int) ($found[$key] ?? 0);
        }
        return $out;
    }

    /** @return array<int,array<int,array{status:string,changed_on:string}>> */
    private function eventsByApp(int $userId): array
    {
        $stmt = $this->pdo->prepare(
            'SELECT e.application_id, e.status, e.changed_on FROM status_events e
             JOIN applications a ON a.id = e.application_id WHERE a.user_id = ? ORDER BY e.changed_on, e.id'
        );
        $stmt->execute([$userId]);
        $by = [];
        foreach ($stmt->fetchAll() as $row) {
            $by[(int) $row['application_id']][] = ['status' => $row['status'], 'changed_on' => $row['changed_on']];
        }
        return $by;
    }

    private function daysBetween(string $from, string $to): int
    {
        return (int) (new DateTimeImmutable($from))->diff(new DateTimeImmutable($to))->format('%r%a');
    }
}
