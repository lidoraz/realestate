import cv2
import os
from google.cloud import vision


class OCR:
    def __init__(self, path_to_token=None):
        unix_path = os.path.expanduser('~') + '/.ssh/gcloud_service_file.json'
        win_path = r"C:\gcloud_service_file.json"
        if os.path.exists(win_path):
            def_path = win_path
        else:
            def_path = unix_path
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path_to_token or def_path
        self.client = vision.ImageAnnotatorClient()

    def detect_text(self, path):
        # with open(path, 'rb') as f:
        #     img = f.read()

        img = cv2.imread(path)
        img = cv2.fastNlMeansDenoising(img, 40, 40)
        success, img = cv2.imencode('.png', img)
        img = img.tobytes()
        img = vision.Image(content=img)
        res = self.client.text_detection(img)
        text = res.full_text_annotation.text
        res_digits = ''.join(c for c in text if c.isdigit())
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
