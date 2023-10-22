import easyocr

class OCR:

    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=False)

    def detect_text(self, img_path):
        result = self.reader.readtext(img_path, allowlist='0123456789')
        if len(result):
            return result[0][1]
        return ""


def test_ocr():
    ocr = OCR()
    res = ocr.detect_text('foo.png')
    print(res)


if __name__ == '__main__':
    test_ocr()

