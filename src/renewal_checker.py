from datetime import datetime


def get_renewal_status(expiry_date):
    """
    Determine renewal status based on expiry date.
    """

    if not expiry_date:
        return {
            "status": "unknown",
            "days_remaining": None
        }

    try:
        expiry = datetime.strptime(
            expiry_date,
            "%Y-%m-%d"
        ).date()

        today = datetime.today().date()

        days_remaining = (
            expiry - today
        ).days

        if days_remaining < 0:
            status = "expired"

        elif days_remaining <= 7:
            status = "critical"

        elif days_remaining <= 30:
            status = "due_soon"

        elif days_remaining <= 90:
            status = "upcoming"

        else:
            status = "valid"

        return {
            "status": status,
            "days_remaining": days_remaining
        }

    except ValueError:

        return {
            "status": "unknown",
            "days_remaining": None
        }


if __name__ == "__main__":

    test_date = "2026-09-09"

    result = get_renewal_status(
        test_date
    )

    print(result)