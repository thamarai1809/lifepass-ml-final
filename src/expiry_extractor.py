import re
import dateparser


def extract_expiry_date(text):
    """
    Extract a likely expiry date from document text.
    """

    # Words commonly associated with expiry
    expiry_keywords = [
        "expiry",
        "expires",
        "expiration",
        "valid until",
        "valid upto",
        "valid up to",
        "valid till",
        "valid through",
        "expiry date",
        "expiration date",
        "காலாவதி",
        "காலாவதி தேதி"
    ]

    # Date patterns such as:
    # 09/09/2027
    # 09-09-2027
    # 09.09.2027
    date_pattern = r"\b\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{4}\b"

    # First look around expiry-related keywords
    lines = text.splitlines()

    for line in lines:

        line_lower = line.lower()

        if any(keyword in line_lower for keyword in expiry_keywords):

            match = re.search(date_pattern, line)

            if match:
                date_text = match.group()

                parsed_date = dateparser.parse(
                    date_text,
                    settings={
                        "DATE_ORDER": "DMY"
                    }
                )

                if parsed_date:
                    return parsed_date.strftime("%Y-%m-%d")

    # If no keyword match, look for dates anywhere in the document
    matches = re.findall(date_pattern, text)

    for date_text in matches:

        parsed_date = dateparser.parse(
            date_text,
            settings={
                "DATE_ORDER": "DMY"
            }
        )

        if parsed_date:
            return parsed_date.strftime("%Y-%m-%d")

    return None

if __name__ == "__main__":

    sample_text = """
    VEHICLE INSURANCE POLICY

    Policy Number: INS123456
    Policy Start Date: 10/09/2026
    Policy Expiry Date: 09/09/2027
    """

    expiry = extract_expiry_date(sample_text)

    print("Detected expiry date:", expiry)
