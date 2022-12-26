import os, io

from PIL.Image import Image
from google.cloud import vision
import cv2


class OCR:

    def __init__(self, path_to_token=r"C:\gcloud_service_file.json"):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path_to_token
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


import cv2
import pytesseract

import numpy as np


# def bfs(visited, queue, array, node):
#     # I make BFS itterative instead of recursive
#     def getNeighboor(array, node):
#         neighboors = []
#         if node[0] + 1 < array.shape[0]:
#             if array[node[0] + 1, node[1]] == 0:
#                 neighboors.append((node[0] + 1, node[1]))
#         if node[0] - 1 > 0:
#             if array[node[0] - 1, node[1]] == 0:
#                 neighboors.append((node[0] - 1, node[1]))
#         if node[1] + 1 < array.shape[1]:
#             if array[node[0], node[1] + 1] == 0:
#                 neighboors.append((node[0], node[1] + 1))
#         if node[1] - 1 > 0:
#             if array[node[0], node[1] - 1] == 0:
#                 neighboors.append((node[0], node[1] - 1))
#         return neighboors
#
#     queue.append(node)
#     visited.add(node)
#
#     while queue:
#         current_node = queue.pop(0)
#         for neighboor in getNeighboor(array, current_node):
#             if neighboor not in visited:
#                 #             print(neighboor)
#                 visited.add(neighboor)
#                 queue.append(neighboor)
#
#
# def removeIsland(img_arr, threshold):
#     # !important: the black pixel is 0 and white pixel is 1
#     while 0 in img_arr:
#         x, y = np.where(img_arr == 0)
#         point = (x[0], y[0])
#         visited = set()
#         queue = []
#         bfs(visited, queue, img_arr, point)
#
#         if len(visited) <= threshold:
#             for i in visited:
#                 img_arr[i[0], i[1]] = 1
#         else:
#             # if the cluster is larger than threshold (i.e is the text),
#             # we convert it to a temporary value of 2 to mark that we
#             # have visited it.
#             for i in visited:
#                 img_arr[i[0], i[1]] = 2
#
#     img_arr = np.where(img_arr == 2, 0, img_arr)
#     return img_arr


class OCR1:

    def __init__(self):
        pytesseract.pytesseract.tesseract_cmd = r'C:\Tesseract-OCR\tesseract.exe'
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

    # def detect_digits(self, path):
    #     # https://medium.com/geekculture/bypassing-captcha-with-breadth-first-search-opencv-and-tesseract-8ea374ee1754
    #     img = cv2.imread(path)
    #     # Convert to grayscale
    #     c_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    #     # Median filter
    #     kernel = np.ones((3, 3), np.uint8)
    #     out = cv2.medianBlur(c_gray, 3)
    #     # Image thresholding
    #     a = np.where(out > 195, 1, out)
    #     out = np.where(a != 1, 0, a)
    #     # Islands removing with threshold = 30
    #     # out = removeIsland(out, 30)
    #     # Median filter
    #     out = cv2.medianBlur(out, 3)
    #     # Convert to Image type and pass it to tesseract
    #     from PIL import Image
    #     im = Image.fromarray(out * 255)
    #     return pytesseract.image_to_string(im, config=self.custom_config)

def test_ocr():
    ocr = OCR1()
    res = ocr.detect_text('foo.png')
    print(res)
    # print(ocr.detect_digits('foo.png'))


if __name__ == '__main__':
    test_ocr()

# print(res)
