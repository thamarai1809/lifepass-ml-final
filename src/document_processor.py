import os
import io
import fitz
import pytesseract

from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"D:\projects\tesseract.exe"


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


def extract_text_from_pdf(pdf_path):
    """
    Extract text from both normal and scanned PDFs.
    """

    document = fitz.open(pdf_path)

    extracted_text = ""

    for page in document:

        # Try extracting existing PDF text first
        text = page.get_text()

        if text.strip():

            extracted_text += text + "\n"

        else:

            # Scanned PDF → render page as image
            pix = page.get_pixmap(
                matrix=fitz.Matrix(2, 2)
            )

            image_bytes = pix.tobytes("png")

            image = Image.open(
                io.BytesIO(image_bytes)
            )

            ocr_text = extract_text_from_image(image)

            extracted_text += ocr_text + "\n"

    document.close()

    return extracted_text


def extract_text_from_file(file_path):
    """
    Automatically process JPG, PNG or PDF.
    """

    extension = os.path.splitext(file_path)[1].lower()

    if extension in [".jpg", ".jpeg", ".png"]:

        image = Image.open(file_path)

        return extract_text_from_image(image)

    elif extension == ".pdf":

        return extract_text_from_pdf(file_path)

    else:

        raise ValueError(
            "Unsupported file type. "
            "Use JPG, JPEG, PNG or PDF."
        )


if __name__ == "__main__":

    file_path = "test_tam_doc.pdf"

    text = extract_text_from_file(file_path)

    print("\n========== EXTRACTED TEXT ==========")
    print(text)