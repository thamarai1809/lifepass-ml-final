# ==========================================
# LifePass Privacy Firewall
# ==========================================

def analyze_privacy(fields):
    """
    Analyze extracted document fields and classify
    their privacy sensitivity.
    """

    privacy_info = {}

    # ------------------------------------------
    # Public / Low sensitivity
    # ------------------------------------------

    public_fields = [
        "nationality"
    ]

    # ------------------------------------------
    # Sensitive fields
    # ------------------------------------------

    sensitive_fields = [
        "holder_name",
        "issue_date",
        "expiry_date"
    ]

    # ------------------------------------------
    # Highly sensitive fields
    # ------------------------------------------

    highly_sensitive_fields = [
        "document_number",
        "date_of_birth"
    ]

    # ------------------------------------------
    # Analyze each extracted field
    # ------------------------------------------

    for field, value in fields.items():

        if value is None or str(value).strip() == "":
            continue

        if field in highly_sensitive_fields:
            level = "HIGHLY_SENSITIVE"

        elif field in sensitive_fields:
            level = "SENSITIVE"

        elif field in public_fields:
            level = "PUBLIC"

        else:
            level = "SENSITIVE"

        privacy_info[field] = {
            "value": value,
            "level": level,
            "share_allowed": level == "PUBLIC"
        }

    # ------------------------------------------
    # Summary
    # ------------------------------------------

    highly_sensitive_count = sum(
        1
        for item in privacy_info.values()
        if item["level"] == "HIGHLY_SENSITIVE"
    )

    sensitive_count = sum(
        1
        for item in privacy_info.values()
        if item["level"] == "SENSITIVE"
    )

    public_count = sum(
        1
        for item in privacy_info.values()
        if item["level"] == "PUBLIC"
    )

    return {
        "fields": privacy_info,
        "summary": {
            "public": public_count,
            "sensitive": sensitive_count,
            "highly_sensitive": highly_sensitive_count,
            "total": len(privacy_info)
        }
    }


# ==========================================
# Test
# ==========================================

if __name__ == "__main__":

    sample_fields = {
        "document_number": "DL123456789",
        "holder_name": "Thamarai Selvi",
        "date_of_birth": "01/01/2004",
        "issue_date": "01/01/2024",
        "expiry_date": "01/01/2034",
        "nationality": "Indian"
    }

    result = analyze_privacy(sample_fields)

    print("\n========== PRIVACY FIREWALL ==========")

    for field, information in result["fields"].items():

        print(
            f"{field}: "
            f"{information['level']} | "
            f"Share Allowed: "
            f"{information['share_allowed']}"
        )

    print("\n========== SUMMARY ==========")

    print(
        "Public:",
        result["summary"]["public"]
    )

    print(
        "Sensitive:",
        result["summary"]["sensitive"]
    )

    print(
        "Highly Sensitive:",
        result["summary"]["highly_sensitive"]
    )

    print(
        "Total:",
        result["summary"]["total"]
    )