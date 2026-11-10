<?php
declare(strict_types=1);

namespace Tests;

use App\ApiException;

final class TaskServiceTest extends DatabaseTestCase
{
    private function task(array $user, string $title, array $extra = []): array
    {
        return $this->tasks->create($user, ['title' => $title] + $extra);
    }

    private function assertStatus(int $expected, callable $fn): void
    {
        try {
            $fn();
            $this->fail("Expected HTTP $expected");
        } catch (ApiException $e) {
            $this->assertSame($expected, $e->status, $e->getMessage());
        }
    }

    public function testNewTasksAppendToTheEndOfTheirColumn(): void
    {
        $this->task($this->alice, 'A');
        $this->task($this->alice, 'B');
        $this->task($this->alice, 'C', ['status' => 'done']);

        $this->assertSame(['A', 'B'], $this->column('todo'));
        $this->assertSame(['C'], $this->column('done'));
    }

    public function testCreateRecordsCreatorAndOptionalAssignee(): void
    {
        $t = $this->task($this->alice, 'Pair', ['assignee_id' => $this->bob['id']]);
        $this->assertSame($this->alice['id'], $t['created_by']);
        $this->assertSame($this->bob['id'], $t['assignee_id']);
        $this->assertSame('Bob', $t['assignee_name']);
    }

    public function testUnknownAssigneeIsRejected(): void
    {
        $this->assertStatus(422, fn() => $this->task($this->alice, 'X', ['assignee_id' => 9999]));
    }

    public function testMemberCannotEditOrDeleteSomeoneElsesTask(): void
    {
        $t = $this->task($this->alice, 'Alice only');
        $this->assertStatus(403, fn() => $this->tasks->update($this->bob, $t['id'], ['title' => 'Hacked']));
        $this->assertStatus(403, fn() => $this->tasks->delete($this->bob, $t['id']));
        $this->assertSame(['Alice only'], $this->column('todo'));
    }

    public function testAssigneeAndCreatorCanEdit(): void
    {
        $t = $this->task($this->alice, 'Shared', ['assignee_id' => $this->bob['id']]);
        $this->assertSame('By Bob', $this->tasks->update($this->bob, $t['id'], ['title' => 'By Bob'])['title']);
        $this->assertSame('By Alice', $this->tasks->update($this->alice, $t['id'], ['title' => 'By Alice'])['title']);
    }

    public function testAdminCanEditAndDeleteAnyTask(): void
    {
        $t = $this->task($this->alice, 'Anything');
        $this->tasks->update($this->admin, $t['id'], ['status' => 'doing']);
        $this->tasks->delete($this->admin, $t['id']);
        $this->assertSame([], $this->column('doing'));
    }

    public function testCanEditFlagMatchesPermissions(): void
    {
        $this->task($this->alice, 'Mine');
        $forBob = $this->tasks->list($this->bob)[0];
        $forAlice = $this->tasks->list($this->alice)[0];
        $this->assertFalse($forBob['can_edit']);
        $this->assertTrue($forAlice['can_edit']);
    }

    public function testMovingBetweenColumnsInsertsAtPositionAndRenumbers(): void
    {
        $a = $this->task($this->alice, 'A');
        $b = $this->task($this->alice, 'B');
        $c = $this->task($this->alice, 'C');
        $this->task($this->alice, 'X', ['status' => 'doing']);
        $this->task($this->alice, 'Y', ['status' => 'doing']);

        $this->tasks->update($this->alice, $b['id'], ['status' => 'doing', 'position' => 1]);

        $this->assertSame(['A', 'C'], $this->column('todo'));
        $this->assertSame(['X', 'B', 'Y'], $this->column('doing'));

        $positions = array_column(array_filter($this->tasks->list($this->admin), fn($t) => $t['status'] === 'todo'), 'position');
        $this->assertSame([0, 1], $positions, 'Source column must have no gaps after a move.');
    }

    public function testReorderWithinTheSameColumn(): void
    {
        $a = $this->task($this->alice, 'A');
        $this->task($this->alice, 'B');
        $this->task($this->alice, 'C');

        $this->tasks->update($this->alice, $a['id'], ['position' => 2]);
        $this->assertSame(['B', 'C', 'A'], $this->column('todo'));

        $this->tasks->update($this->alice, $a['id'], ['position' => 0]);
        $this->assertSame(['A', 'B', 'C'], $this->column('todo'));
    }

    public function testPositionBeyondTheEndIsClamped(): void
    {
        $a = $this->task($this->alice, 'A');
        $this->task($this->alice, 'B');
        $this->tasks->update($this->alice, $a['id'], ['position' => 500]);
        $this->assertSame(['B', 'A'], $this->column('todo'));
    }

    public function testInvalidUpdatesChangeNothing(): void
    {
        $t = $this->task($this->alice, 'Keep me');
        $this->assertStatus(422, fn() => $this->tasks->update($this->alice, $t['id'], ['status' => 'archived']));
        $this->assertStatus(422, fn() => $this->tasks->update($this->alice, $t['id'], ['title' => '   ']));
        $this->assertSame(['Keep me'], $this->column('todo'));
    }

    public function testMissingTaskIs404(): void
    {
        $this->assertStatus(404, fn() => $this->tasks->update($this->admin, 12345, ['title' => 'x']));
        $this->assertStatus(404, fn() => $this->tasks->delete($this->admin, 12345));
    }

    public function testDeletingAUserUnassignsTheirTasksButKeepsThem(): void
    {
        $this->task($this->alice, 'Handover', ['assignee_id' => $this->bob['id']]);
        $this->pdo->exec('DELETE FROM users WHERE id = ' . (int) $this->bob['id']);
        $t = $this->tasks->list($this->admin)[0];
        $this->assertNull($t['assignee_id']);
    }

    public function testTitleIsStoredVerbatimNotHtmlEscaped(): void
    {
        // Escaping is the job of the output layer (the frontend uses textContent); the API must not mangle data.
        $t = $this->task($this->alice, '<b>bold</b> & "quotes"');
        $this->assertSame('<b>bold</b> & "quotes"', $t['title']);
    }
}
