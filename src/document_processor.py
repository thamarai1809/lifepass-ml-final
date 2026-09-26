import os
import io
import fitz
import pytesseract

from PIL import Image


# ==========================================
# Tesseract Configuration
# ==========================================

# Windows:
# Use a locally installed Tesseract executable if available.

if os.name == "nt":

    windows_tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"D:\projects\tesseract.exe",
    ]

    for path in windows_tesseract_paths:

        if os.path.exists(path):

            pytesseract.pytesseract.tesseract_cmd = path
            break


# Linux / Render:
# Tesseract is installed by Dockerfile using:
#
# apt-get install -y --no-install-recommends tesseract-ocr
#
# Therefore Linux will use the tesseract executable
# available in PATH.


# ==========================================
# Extract Text From Image
# ==========================================

def extract_text_from_image(image):
    """
    Extract Tamil + English text from an image.
    """

    text = pytesseract.image_to_string(
        image,
        lang="tam+eng",
        config="--psm 6"
    )

    return text


# ==========================================
# Extract Text From PDF
# ==========================================

def extract_text_from_pdf(pdf_path):
    """
    Extract text from both normal and scanned PDFs.
    """

    document = fitz.open(pdf_path)

    extracted_text = ""

    for page in document:

        # ----------------------------------
        # Try extracting existing PDF text
        # ----------------------------------

        text = page.get_text()

        if text.strip():

            extracted_text += text + "\n"

        else:

            # ------------------------------
            # Scanned PDF → render as image
            # ------------------------------

            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            image_bytes = pix.tobytes("png")

            image = Image.open(
                io.BytesIO(image_bytes)
            )

            ocr_text = extract_text_from_image(
                image
            )

            extracted_text += (
                ocr_text + "\n"
            )

    document.close()

    return extracted_text


# ==========================================
# Extract Text From File
# ==========================================

def extract_text_from_file(file_path):
    """
    Automatically process JPG, PNG or PDF.
    """

    extension = os.path.splitext(
        file_path
    )[1].lower()

    # --------------------------------------
    # Image
    # --------------------------------------

    if extension in [
        ".jpg",
        ".jpeg",
        ".png"
    ]:

        image = Image.open(
            file_path
        )

        return extract_text_from_image(
            image
        )

    # --------------------------------------
    # PDF
    # --------------------------------------

    elif extension == ".pdf":

        return extract_text_from_pdf(
            file_path
        )

    # --------------------------------------
    # Unsupported
    # --------------------------------------

    else:

        raise ValueError(
            "Unsupported file type. "
            "Use JPG, JPEG, PNG or PDF."
        )


# ==========================================
# Local Test
# ==========================================

if __name__ == "__main__":

    file_path = "test_tam_doc.pdf"

    text = extract_text_from_file(
        file_path
    )

    print(
        "\n========== EXTRACTED TEXT =========="
    )

    print(text)