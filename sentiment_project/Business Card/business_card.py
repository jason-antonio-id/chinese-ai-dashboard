import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

img = Image.open('card.png')

text = pytesseract.image_to_string(img, lang='eng+chi_sim')

print ("===== OCR RESULTS =====")
print(text)
print("====================================")