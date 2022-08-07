#!/usr/bin/env python
import argparse
import logging

import cv2 as cv
import mediapipe as mp

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


class MediaPipePose:
    def __init__(
        self,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        logger=logging.getLogger(__name__),
    ):
        self.pose = mp_pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.logger = logger

    def __call__(self, image):
        message = []
        results = self.pose.process(cv.cvtColor(image, cv.COLOR_BGR2RGB))
        if results.pose_landmarks:
            message_landmark = []
            for landmark in results.pose_landmarks.landmark:
                message_landmark.append(
                    {
                        "x": landmark.x,
                        "y": landmark.y,
                        "z": landmark.z,
                        "visibility": landmark.visibility,
                    }
                )
            message = message_landmark
            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
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
    model = MediaPipePose()

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
