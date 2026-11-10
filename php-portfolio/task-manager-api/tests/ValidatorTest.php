<?php
declare(strict_types=1);

namespace Tests;

use App\ApiException;
use App\Validator;
use PHPUnit\Framework\TestCase;

final class ValidatorTest extends TestCase
{
    public function testRegistrationNormalisesEmailAndTrimsName(): void
    {
        $out = Validator::registration(['name' => '  Ada  ', 'email' => 'ADA@Example.COM', 'password' => 'longenough1']);
        $this->assertSame('Ada', $out['name']);
        $this->assertSame('ada@example.com', $out['email']);
    }

    public function testRegistrationReportsEveryBadField(): void
    {
        try {
            Validator::registration(['name' => '', 'email' => 'nope', 'password' => 'short']);
            $this->fail('Expected ApiException');
        } catch (ApiException $e) {
            $this->assertSame(422, $e->status);
            $this->assertEqualsCanonicalizing(['name', 'email', 'password'], array_keys($e->errors));
        }
    }

    public function testPasswordLongerThanBcryptLimitIsRejected(): void
    {
        $this->expectException(ApiException::class);
        Validator::registration(['name' => 'A', 'email' => 'a@b.co', 'password' => str_repeat('x', 73)]);
    }

    public function testTaskRequiresTitleWhenCreating(): void
    {
        $this->expectException(ApiException::class);
        Validator::task(['description' => 'no title'], partial: false);
    }

    public function testPartialTaskOnlyValidatesSentKeys(): void
    {
        $this->assertSame(['status' => 'done'], Validator::task(['status' => 'done'], partial: true));
    }

    public function testInvalidStatusPositionAndAssigneeAreRejected(): void
    {
        foreach ([['status' => 'archived'], ['position' => -1], ['position' => '2'], ['assignee_id' => 'x']] as $bad) {
            try {
                Validator::task($bad, partial: true);
                $this->fail('Expected ApiException for ' . json_encode($bad));
            } catch (ApiException $e) {
                $this->assertSame(422, $e->status);
            }
        }
    }

    public function testExplicitNullAssigneeIsAllowedToUnassign(): void
    {
        $this->assertSame(['assignee_id' => null], Validator::task(['assignee_id' => null], partial: true));
    }
}
