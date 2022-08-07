#!/usr/bin/env python
import argparse
import logging

import cv2 as cv
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles


class MediaPipeHands:
    def __init__(
        self,
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        logger=logging.getLogger(__name__),
    ):
        self.hands = mp_hands.Hands(
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.logger = logger

    def __call__(self, image):
        message = []
        results = self.hands.process(cv.cvtColor(image, cv.COLOR_BGR2RGB))
        if results.multi_hand_landmarks:
            message_multi_landmark = []
            for hand_landmarks in results.multi_hand_landmarks:
                message_landmark = []
                for landmark in hand_landmarks.landmark:
                    message_landmark.append(
                        {
                            "x": landmark.x,
                            "y": landmark.y,
                            "z": landmark.z,
                        }
                    )
                message_multi_landmark.append(message_landmark)
                mp_drawing.draw_landmarks(
                    image,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style(),
                )
            message = message_multi_landmark
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
    model = MediaPipeHands()

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
