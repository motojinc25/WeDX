#!/usr/bin/env python
import argparse
import os

import cv2 as cv
import numpy as np


class YuNet:
    def __init__(
        self,
        model_path=os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "face_detection_yunet_2022mar.onnx",
            )
        ),
        input_size=[320, 320],
        conf_threshold=0.9,
        nms_threshold=0.3,
        top_k=5000,
        backend_id=0,
        target_id=0,
    ):
        self._model_path = model_path
        self._input_size = tuple(input_size)  # [w, h]
        self._conf_threshold = conf_threshold
        self._nms_threshold = nms_threshold
        self._top_k = top_k
        self._backend_id = backend_id
        self._target_id = target_id
        self._model = cv.FaceDetectorYN.create(
            model=self._model_path,
            config="",
            input_size=self._input_size,
            score_threshold=self._conf_threshold,
            nms_threshold=self._nms_threshold,
            top_k=self._top_k,
            backend_id=self._backend_id,
            target_id=self._target_id,
        )

    @property
    def name(self):
        return self.__class__.__name__

    def setBackend(self, backendId):
        self._backend_id = backendId
        self._model = cv.FaceDetectorYN.create(
            model=self._model_path,
            config="",
            input_size=self._input_size,
            score_threshold=self._conf_threshold,
            nms_threshold=self._nms_threshold,
            top_k=self._top_k,
            backend_id=self._backend_id,
            target_id=self._target_id,
        )

    def setTarget(self, targetId):
        self._target_id = targetId
        self._model = cv.FaceDetectorYN.create(
            model=self._model_path,
            config="",
            input_size=self._input_size,
            score_threshold=self._conf_threshold,
            nms_threshold=self._nms_threshold,
            top_k=self._top_k,
            backend_id=self._backend_id,
            target_id=self._target_id,
        )

    def setInputSize(self, input_size):
        self._model.setInputSize(tuple(input_size))

    def infer(self, image):
        faces = self._model.detect(image)
        return faces[1]

    def __call__(self, image):
        h, w, _ = image.shape
        self.setInputSize([w, h])
        landmark_color = [
            (255, 0, 0),  # right eye
            (0, 0, 255),  # left eye
            (0, 255, 0),  # nose tip
            (255, 0, 255),  # right mouth corner
            (0, 255, 255),  # left mouth corner
        ]
        results = self.infer(image)
        message = []
        if results is not None:
            message_squeeze = np.squeeze(results)
            message = message_squeeze.tolist()
        for det in results if results is not None else []:
            bbox = det[0:4].astype(np.int32)
            cv.rectangle(
                image,
                (bbox[0], bbox[1]),
                (bbox[0] + bbox[2], bbox[1] + bbox[3]),
                (0, 255, 0),
                2,
            )
            landmarks = det[4:14].astype(np.int32).reshape((5, 2))
            for idx, landmark in enumerate(landmarks):
                cv.circle(image, landmark, 2, landmark_color[idx], 2)
        return image, message


if __name__ == "__main__":
    current_path = os.path.dirname(os.path.abspath(__file__))
    backends = [cv.dnn.DNN_BACKEND_OPENCV, cv.dnn.DNN_BACKEND_CUDA]
    targets = [
        cv.dnn.DNN_TARGET_CPU,
        cv.dnn.DNN_TARGET_CUDA,
        cv.dnn.DNN_TARGET_CUDA_FP16,
    ]
    help_msg_backends = "Choose one of the computation backends: {:d}: OpenCV implementation (default); {:d}: CUDA"
    help_msg_targets = "Chose one of the target computation devices: {:d}: CPU (default); {:d}: CUDA; {:d}: CUDA fp16"
    try:
        backends += [cv.dnn.DNN_BACKEND_TIMVX]
        targets += [cv.dnn.DNN_TARGET_NPU]
        help_msg_backends += "; {:d}: TIMVX"
        help_msg_targets += "; {:d}: NPU"
    except:
        print(
            "This version of OpenCV does not support TIM-VX and NPU. Visit https://gist.github.com/fengyuentau/5a7a5ba36328f2b763aea026c43fa45f for more information."
        )
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", help="Camera Device No", type=int, default=0)
    parser.add_argument("--width", help="Camera Width", type=int, default=1280)
    parser.add_argument("--height", help="Camera Height", type=int, default=780)
    parser.add_argument("--threshold", help="Score Threshold", type=float, default=0.9)
    parser.add_argument(
        "--model",
        help="Path to the model.",
        type=str,
        default=os.path.abspath(
            os.path.join(current_path, "face_detection_yunet_2022mar.onnx")
        ),
    )
    parser.add_argument(
        "--backend",
        help=help_msg_backends.format(*backends),
        type=int,
        default=backends[0],
    )
    parser.add_argument(
        "--target", help=help_msg_targets.format(*targets), type=int, default=targets[0]
    )
    args = parser.parse_args()

    # USB Camera
    cap = cv.VideoCapture(args.device)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    # Model
    model = YuNet(
        model_path=args.model,
        input_size=[320, 320],
        conf_threshold=args.threshold,
        nms_threshold=0.3,
        top_k=5000,
        backend_id=args.backend,
        target_id=args.target,
    )

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
