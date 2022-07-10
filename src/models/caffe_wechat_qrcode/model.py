#!/usr/bin/env python
import argparse
import os

import cv2 as cv


class WeChatQRCode:
    def __init__(self):
        current_path = os.path.dirname(os.path.abspath(__file__))
        self.detector = cv.wechat_qrcode_WeChatQRCode(
            os.path.abspath(os.path.join(current_path, "detect.prototxt")),
            os.path.abspath(os.path.join(current_path, "detect.caffemodel")),
            os.path.abspath(os.path.join(current_path, "sr.prototxt")),
            os.path.abspath(os.path.join(current_path, "sr.caffemodel")),
        )

    def __call__(self, image):
        results = self.detector.detectAndDecode(image)
        texts = []
        bboxes = []
        message = []
        for text, corner in zip(results[0], results[1]):
            texts.append(text)
            corner_01 = [int(corner[0][0]), int(corner[0][1])]
            corner_02 = [int(corner[1][0]), int(corner[1][1])]
            corner_03 = [int(corner[2][0]), int(corner[2][1])]
            corner_04 = [int(corner[3][0]), int(corner[3][1])]
            bboxes.append([corner_01, corner_02, corner_03, corner_04])
            message.append(
                {
                    "text": text,
                    "bbox": [corner_01, corner_02, corner_03, corner_04],
                }
            )
        for text, bbox in zip(texts, bboxes):
            cv.line(
                image,
                (bbox[0][0], bbox[0][1]),
                (bbox[1][0], bbox[1][1]),
                (255, 0, 0),
                2,
            )
            cv.line(
                image,
                (bbox[1][0], bbox[1][1]),
                (bbox[2][0], bbox[2][1]),
                (255, 0, 0),
                2,
            )
            cv.line(
                image,
                (bbox[2][0], bbox[2][1]),
                (bbox[3][0], bbox[3][1]),
                (0, 255, 0),
                2,
            )
            cv.line(
                image,
                (bbox[3][0], bbox[3][1]),
                (bbox[0][0], bbox[0][1]),
                (0, 255, 0),
                2,
            )
            cv.putText(
                image,
                str(text),
                (bbox[0][0], bbox[0][1] - 12),
                cv.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                thickness=3,
            )
        return image, message


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", help="Camera No", type=int, default=0)
    parser.add_argument("--width", help="Camera Width", type=int, default=1280)
    parser.add_argument("--height", help="Camera Height", type=int, default=780)
    args = parser.parse_args()

    # USB Camera
    cap = cv.VideoCapture(args.camera)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    # Model
    model = WeChatQRCode()

    # Inference frame
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame, _ = model(frame)
        cv.imshow("Testing model - Quit:q", frame)
        if cv.waitKey(1) == ord("q"):
            break
    cap.release()
    cv.destroyAllWindows()
