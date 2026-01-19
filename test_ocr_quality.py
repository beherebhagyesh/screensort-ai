import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

img_path = "/sdcard/Pictures/Screenshots/Chats/Screenshot_2022-08-21-10-13-28-21_6012fa4d4ddec268fc5c7112cbb265e7.jpg"

def test_process(img, name):
    try:
        text = pytesseract.image_to_string(img)
        print(f"--- {name} Output ---")
        print(text[:200].strip()) # Print first 200 chars
        print("---------------------\n")
    except Exception as e:
        print(e)

# 1. Raw Image
img = Image.open(img_path)
test_process(img, "RAW")

# 2. Grayscale
gray = img.convert('L')
test_process(gray, "GRAYSCALE")

# 3. High Contrast (Thresholding) - This usually fixes it
# Increase contrast
enhancer = ImageEnhance.Contrast(gray)
contrast_img = enhancer.enhance(2.0)
test_process(contrast_img, "HIGH CONTRAST")
