"""Money rules, kept in one small file so they're easy to test."""


def deposit_for(total_cents: int, deposit_cents: int) -> int:
    """The deposit for a booking: the set amount, but never more than the total."""
    return min(deposit_cents, total_cents)
