import cv2
import base64
import numpy as np
import logging

def compress_screenshot(screenshot_bgr):
    # Input: np.array BGR from BuildABot (720x1280)
    gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)  # Grayscale
    height, width = 224, 128  # Fixed, aspect preserved (720/1280 ~0.5625, 224*0.5625~126, round to 128)
    resized = cv2.resize(gray, (width, height))
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]
    _, buffer = cv2.imencode('.jpg', resized, encode_param)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    return {"data": img_base64, "shape": [height, width]}

def decompress_image(compressed_dict):
    data = compressed_dict['data']
    shape = compressed_dict['shape']
    buffer = base64.b64decode(data)
    nparr = np.frombuffer(buffer, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    return img  # For predict
