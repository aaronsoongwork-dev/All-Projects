<?php
declare(strict_types=1);

namespace App;

/** The application pipeline and the rules the statistics are built on. */
final class Status
{
    /** value => label, in pipeline order */
    public const LABELS = [
        'wishlist' => 'Wishlist',
        'applied' => 'Applied',
        'screening' => 'Screening',
        'interview' => 'Interview',
        'offer' => 'Offer',
        'accepted' => 'Accepted',
        'rejected' => 'Rejected',
        'withdrawn' => 'Withdrawn',
    ];

    /** Position in the happy path; rejected/withdrawn are exits and have no rank. */
    public const RANK = ['wishlist' => 0, 'applied' => 1, 'screening' => 2, 'interview' => 3, 'offer' => 4, 'accepted' => 5];

    /** Statuses that mean "the company got back to me". */
    public const RESPONSES = ['screening', 'interview', 'offer', 'accepted', 'rejected'];

    /** Still in play. */
    public const ACTIVE = ['applied', 'screening', 'interview', 'offer'];

    public static function valid(string $status): bool
    {
        return isset(self::LABELS[$status]);
    }

    public static function label(string $status): string
    {
        return self::LABELS[$status] ?? $status;
    }
}
