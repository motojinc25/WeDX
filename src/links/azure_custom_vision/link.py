#!/usr/bin/env python
import argparse
import io
import sys

import cv2 as cv
import numpy as np
import requests
from PIL import Image


class AzureCustomVision:
    client = False
    url = None
    key = None
    threshold = 0.55

    def __init__(self):
        pass

    def connect(self, url=None, key=None, threshold=0.55):
        self.url = url
        self.key = key
        self.threshold = threshold
        image = np.zeros((10, 10, 3), dtype=np.uint8)
        image = Image.fromarray(image)
        image_binary = io.BytesIO()
        image.save(image_binary, format="png")
        headers = {
            "Prediction-Key": self.key,
            "content-type": "application/octet-stream",
        }
        try:
            response = requests.post(
                self.url, data=image_binary.getvalue(), headers=headers
            )
            if response.status_code == 200:
                self.client = True
        except:
            self.client = False

    def __call__(self, image):
        message = []
        if self.client:
            message = self.prediction(image)
            image = self.draw_landmarks(image, message)
        return image, message

    def prediction(self, image):
        message = []
        if self.client:
            image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image_binary = io.BytesIO()
            image.save(image_binary, format="png")
            headers = {
                "Prediction-Key": self.key,
                "content-type": "application/octet-stream",
            }
            response = requests.post(
                self.url, data=image_binary.getvalue(), headers=headers
            )
            message = response.json()
        return message

    def draw_landmarks(self, image, landmarks):
        if "predictions" in landmarks:
            for (index, prediction) in enumerate(landmarks["predictions"]):
                if prediction["probability"] >= self.threshold:
                    height, width, _ = image.shape
                    x1, y1 = 50, 70 + (index * 25)
                    if "boundingBox" in prediction:
                        x1 = prediction["boundingBox"]["left"] * width
                        y1 = prediction["boundingBox"]["top"] * height
                        x2 = x1 + width * prediction["boundingBox"]["width"]
                        y2 = y1 + height * prediction["boundingBox"]["height"]
                        cv.rectangle(
                            image, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0)
                        )
                    cv.putText(
                        image,
                        prediction["tagName"]
                        + " "
                        + "{:.2f}".format(prediction["probability"]),
                        (int(x1), int(y1)),
                        cv.FONT_HERSHEY_SIMPLEX,
                        1.0,
                        (255, 0, 255),
                        thickness=2,
                    )
        return image


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", help="Camera No", type=int, default=0)
    parser.add_argument("--width", help="Camera Width", type=int, default=1280)
    parser.add_argument("--height", help="Camera Height", type=int, default=780)
    parser.add_argument("--url", help="URL")
    parser.add_argument("--key", help="Key")
    args = parser.parse_args()

    # USB Camera
    cap = cv.VideoCapture(args.camera)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    # Link service
    service = AzureCustomVision()
    service.connect(url=args.url, key=args.key)
    if not service.client:
        print("CredentialError")
        sys.exit(1)

    # Inference frame
    message = {}
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        key = cv.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("p"):
            message = service.prediction(frame)
        frame = service.draw_landmarks(frame, message)
        cv.imshow("Testing model - Prediction:p, Quit:q", frame)
    cap.release()
    cv.destroyAllWindows()
