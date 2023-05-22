import cv2
import pytesseract
TESSERACT_PATH = r'C:\Tesseract-OCR\tesseract.exe'


class OCR:

    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        # https://ai-facets.org/tesseract-ocr-best-practices/
        self.custom_config = '--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789'

    def detect_text(self, path):
        img = cv2.imread(path)
        img = cv2.fastNlMeansDenoising(img, 120, 120)
        res_digits = pytesseract.image_to_string(img, config=self.custom_config)[:-1]
        print('ocr:', res_digits)
        return res_digits


def test_ocr():
    ocr = OCR()
    res = ocr.detect_text('foo.png')
    print(res)
    # print(ocr.detect_digits('foo.png'))


if __name__ == '__main__':
    test_ocr()

# print(res)
