import cv2
import numpy as np
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"D:\projects\tesseract.exe"

image = cv2.imread("test_image.png")

# Make the image larger
image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

# Convert to grayscale
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Improve contrast
gray = cv2.threshold(
    gray,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)[1]

text = pytesseract.image_to_string(
    gray,
    lang="tam+eng",
    config="--psm 6"
)

print(text)