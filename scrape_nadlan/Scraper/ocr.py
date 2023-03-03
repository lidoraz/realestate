import cv2
import pytesseract

TESSERACT_PATH = r'C:\Tesseract-OCR\tesseract.exe'


class OCR1:

    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        # https://ai-facets.org/tesseract-ocr-best-practices/
        self.custom_config = '--psm 8 --oem 3 -c tessedit_char_whitelist=0123456789'

    def detect_text(self, path):
        img = cv2.imread(path)
        # img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        img = cv2.fastNlMeansDenoising(img, 120, 120)
        # a = np.where(img > 195, 1, img)
        # img = np.where(a != 1, 0, a)
        # cv2.imwrite("foo1.png", img)
        # img = removeIsland(img, 30)
        # cv2.imwrite("foo2.png", img)
        # Adding custom options
        # custom_config = r'--oem 3 --psm 6'
        # custom_config = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        res_digits = pytesseract.image_to_string(img, config=self.custom_config)[:-1]
        print('ocr:', res_digits)
        return res_digits


def test_ocr():
    ocr = OCR1()
    res = ocr.detect_text('foo.png')
    print(res)
    # print(ocr.detect_digits('foo.png'))


if __name__ == '__main__':
    test_ocr()

# print(res)
