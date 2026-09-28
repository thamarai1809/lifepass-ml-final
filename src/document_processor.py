import os
import io

import fitz
import pytesseract

from PIL import Image


# ==========================================
# Tesseract Configuration
# ==========================================

def configure_tesseract():
    """
    Configure Tesseract OCR depending on the operating system.

    Windows:
        Look for a locally installed Tesseract executable.

    Linux / Render:
        Use the Tesseract executable installed through
        the Dockerfile and available in PATH.
    """

    # --------------------------------------
    # Windows
    # --------------------------------------

    if os.name == "nt":

        windows_tesseract_paths = [

            r"C:\Program Files\Tesseract-OCR\tesseract.exe",

            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",

            r"D:\projects\tesseract.exe",
        ]

        for path in windows_tesseract_paths:

            if os.path.exists(path):

                pytesseract.pytesseract.tesseract_cmd = path

                print(
                    "Tesseract configured:",
                    path
                )

                return

        # If Tesseract is already available through PATH,
        # don't manually configure a path.

        print(
            "Tesseract executable not found in "
            "standard Windows locations. "
            "Trying system PATH."
        )

    # --------------------------------------
    # Linux / Render
    # --------------------------------------

    else:

        # Render installs Tesseract through Dockerfile:
        #
        # apt-get install -y --no-install-recommends tesseract-ocr
        #
        # Therefore pytesseract should automatically
        # use "tesseract" from PATH.

        print(
            "Linux detected. "
            "Using Tesseract from system PATH."
        )


# Configure Tesseract when this module loads
configure_tesseract()


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

    For normal PDFs:
        PyMuPDF extracts the existing text.

    For scanned PDFs:
        Each page is rendered as an image and
        passed through Tesseract OCR.
    """

    document = fitz.open(pdf_path)

    extracted_text = ""

    try:

        for page in document:

            # ----------------------------------
            # Try extracting existing PDF text
            # ----------------------------------

            text = page.get_text()

            if text.strip():

                extracted_text += (
                    text + "\n"
                )

            else:

                # ------------------------------
                # Scanned PDF → render as image
                # ------------------------------

                pix = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2)
                )

                image_bytes = pix.tobytes(
                    "png"
                )

                image = Image.open(
                    io.BytesIO(image_bytes)
                )

                ocr_text = extract_text_from_image(
                    image
                )

                extracted_text += (
                    ocr_text + "\n"
                )

    finally:

        document.close()

    return extracted_text


# ==========================================
# Extract Text From File
# ==========================================

def extract_text_from_file(file_path):
    """
    Automatically process JPG, JPEG, PNG or PDF.
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

        try:

            return extract_text_from_image(
                image
            )

        finally:

            image.close()

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