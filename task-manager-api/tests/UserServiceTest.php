<?php
declare(strict_types=1);

namespace Tests;

use App\ApiException;
use App\UserService;

final class UserServiceTest extends DatabaseTestCase
{
    public function testFirstUserIsAdminAndLaterUsersAreMembers(): void
    {
        $this->assertSame('admin', $this->admin['role']);
        $this->assertSame('member', $this->alice['role']);
    }

    public function testPublicUserNeverContainsPasswordHash(): void
    {
        $this->assertArrayNotHasKey('password_hash', $this->admin);
        $this->assertArrayNotHasKey('password_hash', $this->users->find($this->admin['id']));
    }

    public function testPasswordIsStoredHashedNotPlain(): void
    {
        $hash = $this->pdo->query("SELECT password_hash FROM users WHERE email = 'alice@example.com'")->fetchColumn();
        $this->assertNotSame('correct-horse-battery', $hash);
        $this->assertTrue(password_verify('correct-horse-battery', $hash));
    }

    public function testDuplicateEmailIsRejectedCaseInsensitively(): void
    {
        try {
            $this->register('Other', 'ALICE@example.com');
            $this->fail('Expected conflict');
        } catch (ApiException $e) {
            $this->assertSame(409, $e->status);
        }
    }

    public function testLoginSucceedsWithCorrectPassword(): void
    {
        $user = $this->users->login('Alice@Example.com', 'correct-horse-battery', '127.0.0.1');
        $this->assertSame($this->alice['id'], $user['id']);
    }

    public function testWrongPasswordAndUnknownEmailGiveTheSameError(): void
    {
        $messages = [];
        foreach ([['alice@example.com', 'wrong-password'], ['nobody@example.com', 'whatever123']] as [$email, $pw]) {
            try {
                $this->users->login($email, $pw, '127.0.0.1');
            } catch (ApiException $e) {
                $this->assertSame(401, $e->status);
                $messages[] = $e->getMessage();
            }
        }
        $this->assertCount(2, $messages);
        $this->assertSame($messages[0], $messages[1], 'Must not reveal whether an email exists.');
    }

    public function testAccountLocksAfterTooManyFailuresEvenWithCorrectPassword(): void
    {
        for ($i = 0; $i < UserService::MAX_FAILED_LOGINS; $i++) {
            try {
                $this->users->login('bob@example.com', 'bad-guess-' . $i, '10.0.0.1');
            } catch (ApiException) {
            }
        }
        try {
            $this->users->login('bob@example.com', 'correct-horse-battery', '10.0.0.1');
            $this->fail('Expected lockout');
        } catch (ApiException $e) {
            $this->assertSame(429, $e->status);
        }
    }

    public function testSuccessfulLoginClearsFailureCounter(): void
    {
        for ($i = 0; $i < UserService::MAX_FAILED_LOGINS - 1; $i++) {
            try {
                $this->users->login('bob@example.com', 'bad' . $i . 'xxxx', '10.0.0.1');
            } catch (ApiException) {
            }
        }
        $this->users->login('bob@example.com', 'correct-horse-battery', '10.0.0.1');
        $count = (int) $this->pdo->query("SELECT COUNT(*) FROM login_attempts WHERE email = 'bob@example.com'")->fetchColumn();
        $this->assertSame(0, $count);
    }

    public function testOnlyAdminsCanChangeRoles(): void
    {
        $this->expectException(ApiException::class);
        $this->expectExceptionCode(0);
        $this->users->setRole($this->alice, $this->bob['id'], 'admin');
    }

    public function testAdminCanPromoteAndTheLastAdminCannotBeDemoted(): void
    {
        $promoted = $this->users->setRole($this->admin, $this->alice['id'], 'admin');
        $this->assertSame('admin', $promoted['role']);

        $this->users->setRole($this->admin, $this->alice['id'], 'member'); // fine: admin still exists

        try {
            $this->users->setRole($this->admin, $this->admin['id'], 'member');
            $this->fail('Expected last-admin protection');
        } catch (ApiException $e) {
            $this->assertSame(409, $e->status);
        }
    }

    public function testUserListHidesEmailsFromNonAdmins(): void
    {
        $this->assertArrayNotHasKey('email', $this->users->all(false)[0]);
        $this->assertArrayHasKey('email', $this->users->all(true)[0]);
    }
}
