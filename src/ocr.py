import os

import cv2
import numpy as np
import pytesseract
from PIL import Image


# ==========================================
# Tesseract Configuration
# ==========================================

if os.name == "nt":
    # Windows
    windows_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"D:\projects\tesseract.exe",
    ]

    for path in windows_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

# On Linux/Render:
# Tesseract is installed by Dockerfile using:
# apt-get install tesseract-ocr
#
# Therefore pytesseract automatically uses:
# /usr/bin/tesseract


# ==========================================
# OCR Function
# ==========================================

def extract_text_from_image(image_path):

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(
            f"Unable to read image: {image_path}"
        )

    # --------------------------------------
    # Make the image larger
    # --------------------------------------

    image = cv2.resize(
        image,
        None,
        fx=2,
        fy=2,
        interpolation=cv2.INTER_CUBIC
    )

    # --------------------------------------
    # Convert to grayscale
    # --------------------------------------

    gray = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------
    # Improve contrast
    # --------------------------------------

    gray = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    # --------------------------------------
    # OCR
    # --------------------------------------

    text = pytesseract.image_to_string(
        gray,
        lang="tam+eng",
        config="--psm 6"
    )

    return text