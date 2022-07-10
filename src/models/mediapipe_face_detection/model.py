#!/usr/bin/env python
import argparse

import cv2 as cv
import mediapipe as mp

mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils


class MediaPipeFaceDetection:
    def __init__(self, model_selection=0, min_detection_confidence=0.5):
        self.face_detection = mp_face_detection.FaceDetection(
            model_selection=model_selection,
            min_detection_confidence=min_detection_confidence,
        )

    def __call__(self, image):
        message = []
        results = self.face_detection.process(cv.cvtColor(image, cv.COLOR_BGR2RGB))
        if results.detections:
            for detection in results.detections:
                message_landmark = {}
                message_landmark["score"] = detection.score[0]
                bbox = detection.location_data.relative_bounding_box
                message_landmark["bounding_box"] = {
                    "xmin": bbox.xmin,
                    "ymin": bbox.ymin,
                    "width": bbox.width,
                    "height": bbox.height,
                }
                for id, keypoint in enumerate(
                    detection.location_data.relative_keypoints
                ):
                    message_landmark[id] = {
                        "x": keypoint.x,
                        "y": keypoint.y,
                        "score": detection.score[0],
                    }
                for id, keypoint in enumerate(
                    detection.location_data.relative_keypoints
                ):
                    message_landmark[id] = {
                        "x": keypoint.x,
                        "y": keypoint.y,
                        "score": detection.score[0],
                    }
                mp_drawing.draw_detection(image, detection)
            message = message_landmark
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
    model = MediaPipeFaceDetection()

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
