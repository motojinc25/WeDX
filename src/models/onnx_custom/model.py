#!/usr/bin/env python
import argparse
import logging
import os

import cv2 as cv
import numpy as np
import onnxruntime as ort


class CustomClassification:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.state = False

    def connect(
        self,
        model_filepath=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "../onnx_mobilenetv3small/mobilenetv3small.onnx",
        ),
        input_shape=(224, 224),
        input_dtype="float32",
        output_item_count=2,
        device="CUDA",
    ):
        if not os.path.exists(model_filepath):
            self.state = False
            return
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if device == "CPU":
            providers = ["CPUExecutionProvider"]
        self.session = ort.InferenceSession(model_filepath, providers=providers)
        self.input_shape = input_shape
        self.input_dtype = input_dtype
        self.output_item_count = output_item_count
        self.input_name = self.session.get_inputs()[0].name
        self.state = True

    def __call__(self, image):
        message = []
        outputs = self.session.run(
            None,
            {
                self.input_name: np.expand_dims(
                    cv.resize(
                        cv.cvtColor(image, cv.COLOR_BGR2RGB),
                        dsize=(self.input_shape[1], self.input_shape[0]),
                    ),
                    axis=0,
                ).astype(self.input_dtype)
            },
        )
        outputs = np.array(outputs).squeeze()
        class_ids = np.argsort(outputs)[::-1][: self.output_item_count]
        class_scores = outputs[class_ids]
        for index, (class_score, class_id) in enumerate(zip(class_scores, class_ids)):
            score = "%.2f" % class_score
            text = "%s:%s" % (
                str(class_id),
                score,
            )
            image = cv.putText(
                image,
                text,
                (15, 30 + (index * 35)),
                cv.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 255, 0),
                thickness=3,
            )
            message.append(
                {
                    "class": int(class_id),
                    "score": score,
                }
            )
        return image, message

    def is_connect(self):
        return self.state


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", help="Camera No", type=int, default=0)
    parser.add_argument("--width", help="Camera Width", type=int, default=1280)
    parser.add_argument("--height", help="Camera Height", type=int, default=780)
    parser.add_argument("--device", help="Device(CUDA,CPU)", default="CUDA")
    args = parser.parse_args()

    # USB Camera
    cap = cv.VideoCapture(args.camera)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    # Model
    model = CustomClassification()
    model.connect(device=args.device)

    # Inference frame
    while cap.isOpened() and model.is_connect():
        ret, frame = cap.read()
        if not ret:
            break
        frame, message = model(frame)
        cv.imshow("Testing model - Quit:q|Print:p", frame)
        waitkey = cv.waitKey(1)
        if waitkey == ord("q"):
            break
        elif waitkey == ord("p"):
            print(message)
    cap.release()
    cv.destroyAllWindows()
