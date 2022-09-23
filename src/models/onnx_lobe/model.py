#!/usr/bin/env python
import argparse
import json
import logging
import os

import cv2 as cv
import numpy as np
import onnxruntime as ort

EXPORT_MODEL_VERSION = 1


class LobeClassification:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.model_filepath = None
        self.state = False

    def connect(
        self,
        signature_filepath=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "signature.json",
        ),
        device="CUDA",
    ):
        model_dir = os.path.dirname(signature_filepath)
        if not os.path.exists(signature_filepath):
            self.state = False
            return
        with open(signature_filepath, "r") as f:
            self.signature = json.load(f)
        self.model_filepath = os.path.join(model_dir, self.signature.get("filename"))
        if not os.path.isfile(self.model_filepath):
            self.state = False
            return
        self.signature_inputs = self.signature.get("inputs")
        self.signature_outputs = self.signature.get("outputs")
        self.session = None
        if "Image" not in self.signature_inputs:
            self.state = False
            return
        version = self.signature.get("export_model_version")
        if version is None or version != EXPORT_MODEL_VERSION:
            self.state = False
            return
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if device == "CPU":
            providers = ["CPUExecutionProvider"]
        self.session = ort.InferenceSession(self.model_filepath, providers=providers)
        self.input_shape = self.signature_inputs.get("Image").get("shape")[1:3]
        self.input_dtype = self.signature_inputs.get("Image").get("dtype")
        self.input_name = self.signature_inputs.get("Image").get("name")
        self.state = True

    def __call__(self, image):
        message = []
        img = np.expand_dims(
            cv.resize(
                cv.cvtColor(image, cv.COLOR_BGR2RGB),
                dsize=(self.input_shape[1], self.input_shape[0]),
            ),
            axis=0,
        ).astype(self.input_dtype)
        fetches = [
            (key, value.get("name")) for key, value in self.signature_outputs.items()
        ]
        feed = {self.signature_inputs.get("Image").get("name"): img}
        outputs = self.session.run(
            output_names=[name for (_, name) in fetches], input_feed=feed
        )
        out_keys = ["label", "confidence"]
        results = {}
        for i, (key, _) in enumerate(fetches):
            val = outputs[i].tolist()[0]
            if isinstance(val, bytes):
                val = val.decode()
            results[key] = val
        confs = results["Confidences"]
        labels = self.signature.get("classes").get("Label")
        output = [dict(zip(out_keys, group)) for group in zip(labels, confs)]
        sorted_output = sorted(output, key=lambda k: k["confidence"], reverse=True)
        sorted_output = np.array(sorted_output).squeeze()
        for index, item in enumerate(sorted_output[:5]):
            score = "%.2f" % item["confidence"]
            text = "%s(%s)" % (item["label"], score)
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
                    "class": item["label"],
                    "score": score,
                }
            )
        return image, message

    def is_connect(self):
        return self.state

    def get_model_filepath(self):
        return self.model_filepath


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
    model = LobeClassification()
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
