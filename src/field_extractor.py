import re


def extract_fields(text, document_type):
    """
    Extract important fields from OCR text.
    """

    fields = {}

    # -------------------------
    # Policy / Document Number
    # -------------------------
    number_patterns = [
        r"(?:policy\s*(?:no|number)|policy\s*#)\s*[:\-]?\s*([A-Z0-9\/\-]+)",
        r"(?:license|licence)\s*(?:no|number)\s*[:\-]?\s*([A-Z0-9\/\-]+)",
        r"(?:passport)\s*(?:no|number)\s*[:\-]?\s*([A-Z0-9\/\-]+)",
        r"(?:certificate)\s*(?:no|number)\s*[:\-]?\s*([A-Z0-9\/\-]+)"
    ]

    for pattern in number_patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            fields["document_number"] = match.group(1)
            break

    # -------------------------
    # Name
    # -------------------------
    name_patterns = [
        r"(?:holder\s*name|name)\s*[:\-]\s*([A-Za-z][A-Za-z\s]+)",
        r"(?:owner\s*name|owner)\s*[:\-]\s*([A-Za-z][A-Za-z\s]+)"
    ]

    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            fields["holder_name"] = match.group(1).strip()
            break

    # -------------------------
    # Date of Birth
    # -------------------------
    dob_pattern = (
        r"(?:date\s*of\s*birth|dob)"
        r"\s*[:\-]?\s*"
        r"(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{4})"
    )

    match = re.search(dob_pattern, text, re.IGNORECASE)

    if match:
        fields["date_of_birth"] = match.group(1)

    # -------------------------
    # Issue Date
    # -------------------------
    issue_pattern = (
        r"(?:issue\s*date|issued\s*on|date\s*of\s*issue)"
        r"\s*[:\-]?\s*"
        r"(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{4})"
    )

    match = re.search(issue_pattern, text, re.IGNORECASE)

    if match:
        fields["issue_date"] = match.group(1)

    # -------------------------
    # Expiry Date
    # -------------------------
    expiry_pattern = (
        r"(?:expiry\s*date|expiration\s*date|expires|"
        r"valid\s*(?:until|upto|up\s*to|till|through))"
        r"\s*[:\-]?\s*"
        r"(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{4})"
    )

    match = re.search(expiry_pattern, text, re.IGNORECASE)

    if match:
        fields["expiry_date"] = match.group(1)

    # -------------------------
    # Nationality
    # -------------------------
    nationality_pattern = (
        r"(?:nationality)"
        r"\s*[:\-]?\s*"
        r"([A-Za-z]+)"
    )

    match = re.search(
        nationality_pattern,
        text,
        re.IGNORECASE
    )

    if match:
        fields["nationality"] = match.group(1)

    return fields


# Test
if __name__ == "__main__":

    sample_text = """
    VEHICLE INSURANCE POLICY

    Policy Number: INS123456
    Holder Name: Thamarai Selvi
    Issue Date: 10/09/2026
    Policy Expiry Date: 09/09/2027
    """

    document_type = "insurance"

    fields = extract_fields(
        sample_text,
        document_type
    )

    print("\n========== EXTRACTED FIELDS ==========")

    for key, value in fields.items():
        print(f"{key}: {value}")