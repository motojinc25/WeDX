#!/usr/bin/env python
import argparse
import logging
import operator
import os

import cv2 as cv
import numpy as np
import onnx
import onnxruntime as ort
from PIL import Image

MAX_DETECTIONS = 64  # Max number of boxes to detect
IOU_THRESHOLD = 0.45


class NonMaxSuppression:
    def __init__(self, max_detections, prob_threshold, iou_threshold, logger=logging.getLogger(__name__)):
        self.max_detections = max_detections
        self.prob_threshold = prob_threshold
        self.iou_threshold = iou_threshold
        self.logger = logger

    def __call__(self, boxes, class_probs):
        classes = np.argmax(class_probs, axis=1)
        probs = class_probs[np.arange(len(class_probs)), classes]
        valid_indices = probs > self.prob_threshold
        boxes, classes, probs = (
            boxes[valid_indices, :],
            classes[valid_indices],
            probs[valid_indices],
        )
        areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        selected_boxes = []
        selected_classes = []
        selected_probs = []
        max_detections = min(self.max_detections, len(boxes))
        while len(selected_boxes) < max_detections:
            i = np.argmax(probs)
            if probs[i] < self.prob_threshold:
                break

            # Save the selected prediction
            selected_boxes.append(boxes[i])
            selected_classes.append(classes[i])
            selected_probs.append(probs[i])
            box = boxes[i]
            other_indices = np.concatenate((np.arange(i), np.arange(i + 1, len(boxes))))
            other_boxes = boxes[other_indices]

            # Get overlap between the 'box' and 'other_boxes'
            xy = np.maximum(box[0:2], other_boxes[:, 0:2])
            xy2 = np.minimum(box[2:4], other_boxes[:, 2:4])
            wh = np.maximum(0, xy2 - xy)

            # Calculate Intersection Over Union (IOU)
            overlap_area = wh[:, 0] * wh[:, 1]
            iou = overlap_area / (areas[i] + areas[other_indices] - overlap_area)

            # Find the overlapping predictions
            overlapping_indices = other_indices[np.where(iou > self.iou_threshold)[0]]
            overlapping_indices = np.append(overlapping_indices, i)
            probs[overlapping_indices] = 0
        return (
            np.array(selected_boxes),
            np.array(selected_classes),
            np.array(selected_probs),
        )


class CustomVisionObjectDetection:
    ANCHORS = np.array(
        [[0.573, 0.677], [1.87, 2.06], [3.34, 5.47], [7.88, 3.53], [9.77, 9.17]]
    )
    threshold = 0.55
    is_active = False

    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger

    def connect(
        self,
        model_filepath=os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "object_detection_model.onnx",
            )
        ),
        labels_filepath=os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "object_detection_labels.txt",
            )
        ),
        threshold=0.55,
        device="CUDA",
    ):
        if not os.path.exists(model_filepath) or not os.path.exists(labels_filepath):
            self.is_active = False
        else:
            self.threshold = threshold
            self.nms = NonMaxSuppression(MAX_DETECTIONS, self.threshold, IOU_THRESHOLD)
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if device == "CPU":
                providers = ["CPUExecutionProvider"]
            self.session = ort.InferenceSession(model_filepath, providers=providers)
            self.input_shape = self.session.get_inputs()[0].shape[2:]
            self.input_name = self.session.get_inputs()[0].name
            self.input_type = {"tensor(float)": np.float32, "tensor(float16)": np.float16}[
                self.session.get_inputs()[0].type
            ]
            self.output_names = [o.name for o in self.session.get_outputs()]
            self.is_bgr = False
            self.is_range255 = False
            onnx_model = onnx.load(model_filepath)
            for metadata in onnx_model.metadata_props:
                if metadata.key == "Image.BitmapPixelFormat" and metadata.value == "Bgr8":
                    self.is_bgr = True
                elif (
                    metadata.key == "Image.NominalPixelRange"
                    and metadata.value == "NominalRange_0_255"
                ):
                    self.is_range255 = True
            labels = []
            with open(labels_filepath) as f:
                for readline in f:
                    labels.append(str(readline).strip())
            self.class_names = {k: v for k, v in enumerate(labels)}
            if len(self.session.get_inputs()) == 1:
                self.is_active = True

    def __call__(self, image):
        message = []
        h, w = image.shape[:2]
        image_array = Image.fromarray(image).resize(self.input_shape)
        input_array = np.array(image_array, dtype=np.float32)[np.newaxis, :, :, :]
        input_array = input_array.transpose((0, 3, 1, 2))  # N, C, H, W
        if self.is_bgr:
            input_array = input_array[:, (2, 1, 0), :, :]
        if not self.is_range255:
            input_array = input_array / 255  # Pixel values should be in range [0, 1]
        outputs = self.session.run(
            self.output_names, {self.input_name: input_array.astype(self.input_type)}
        )
        outputs = {name: outputs[i] for i, name in enumerate(self.output_names)}
        if "model_outputs0" in outputs:
            # General (compact) domain for Object Detection requires special postprocessing logic
            outputs = outputs["model_outputs0"][0]
            outputs = self._postprocess(outputs, self.ANCHORS)
        thickness = 3
        if "detected_boxes" in outputs:
            for bbox, class_id, score in zip(
                outputs["detected_boxes"][0],
                outputs["detected_classes"][0],
                outputs["detected_scores"][0],
            ):
                if score > self.threshold:
                    x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
                    color = self._get_color(int(class_id))
                    image = cv.rectangle(
                        image,
                        (int(x1 * w), int(y1 * h)),
                        (int(x2 * w), int(y2 * h)),
                        color,
                        thickness=thickness,
                    )
                    score = "%.2f" % score
                    text = "%s:%s" % (str(self.class_names[int(class_id)]), score)
                    image = cv.putText(
                        image,
                        text,
                        (int(x1 * w), int(y1 * h) - 10),
                        cv.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        thickness=thickness,
                    )
                    message.append([x1, x2, y1, y2, int(class_id)])
        return image, message

    def _get_color(self, index):
        temp_index = abs(int(index + 5)) * 3
        color = (
            (29 * temp_index) % 255,
            (17 * temp_index) % 255,
            (37 * temp_index) % 255,
        )
        return color

    def set_device(self, device="CUDA"):
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if device == "CPU":
            providers = ["CPUExecutionProvider"]
        self.session.set_providers(providers)

    def get_status(self):
        return self.status

    def _postprocess(self, outputs, anchors):
        outputs = outputs.transpose((1, 2, 0))
        num_anchors = anchors.shape[0]
        height, width, channels = outputs.shape
        num_classes = channels // num_anchors - 5
        outputs = outputs.reshape((height, width, num_anchors, -1))
        x = (outputs[..., 0] + np.arange(width)[np.newaxis, :, np.newaxis]) / width
        y = (outputs[..., 1] + np.arange(height)[:, np.newaxis, np.newaxis]) / height
        w = np.exp(outputs[..., 2]) * anchors[:, 0][np.newaxis, np.newaxis, :] / width
        h = np.exp(outputs[..., 3]) * anchors[:, 1][np.newaxis, np.newaxis, :] / height
        x = x - w / 2
        y = y - h / 2
        boxes = np.stack((x, y, x + w, y + h), axis=-1).reshape(-1, 4)
        objectness = self._logistic(outputs[..., 4, np.newaxis])
        class_probs = outputs[..., 5:]
        class_probs = np.exp(
            class_probs - np.amax(class_probs, axis=3)[..., np.newaxis]
        )
        class_probs = (
            class_probs / np.sum(class_probs, axis=3)[..., np.newaxis] * objectness
        ).reshape(-1, num_classes)
        detected_boxes, detected_classes, detected_scores = self.nms(boxes, class_probs)
        return {
            "detected_boxes": detected_boxes.reshape(1, -1, 4),
            "detected_classes": detected_classes.reshape(1, -1),
            "detected_scores": detected_scores.reshape(1, -1),
        }

    def _logistic(self, x):
        return np.where(x > 0, 1 / (1 + np.exp(-x)), np.exp(x) / (1 + np.exp(x)))


class CustomVisionClassification:
    is_active = False

    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger

    def connect(
        self,
        model_filepath=os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "classification_model.onnx",
            )
        ),
        labels_filepath=os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "classification_labels.txt",
            )
        ),
        device="CUDA",
    ):
        if not os.path.exists(model_filepath) or not os.path.exists(labels_filepath):
            self.is_active = False
        else:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if device == "CPU":
                providers = ["CPUExecutionProvider"]
            self.session = ort.InferenceSession(model_filepath, providers=providers)
            self.input_shape = self.session.get_inputs()[0].shape[2:]
            self.input_name = self.session.get_inputs()[0].name
            self.input_type = {
                "tensor(float)": np.float32,
                "tensor(float16)": np.float16,
            }[self.session.get_inputs()[0].type]
            self.output_names = [o.name for o in self.session.get_outputs()]
            self.is_bgr = False
            self.is_range255 = False
            onnx_model = onnx.load(model_filepath)
            for metadata in onnx_model.metadata_props:
                if (
                    metadata.key == "Image.BitmapPixelFormat"
                    and metadata.value == "Bgr8"
                ):
                    self.is_bgr = True
                elif (
                    metadata.key == "Image.NominalPixelRange"
                    and metadata.value == "NominalRange_0_255"
                ):
                    self.is_range255 = True
            labels = []
            with open(labels_filepath) as f:
                for readline in f:
                    labels.append(str(readline).strip())
            self.class_names = {k: v for k, v in enumerate(labels)}
            if len(self.session.get_inputs()) == 1:
                self.is_active = True

    def __call__(self, image):
        message = []
        image_array = Image.fromarray(image).resize(self.input_shape)
        input_array = np.array(image_array, dtype=np.float32)[np.newaxis, :, :, :]
        input_array = input_array.transpose((0, 3, 1, 2))  # N, C, H, W
        if self.is_bgr:
            input_array = input_array[:, (2, 1, 0), :, :]
        if not self.is_range255:
            input_array = input_array / 255  # Pixel values should be in range [0, 1]
        outputs = self.session.run(
            self.output_names, {self.input_name: input_array.astype(self.input_type)}
        )
        outputs = {name: outputs[i] for i, name in enumerate(self.output_names)}
        if "model_output" in outputs:
            # General (compact) [S1] ONNX Model
            outputs = outputs["model_output"]
            outputs = np.array(outputs).squeeze()
            class_ids = np.argsort(outputs)[::-1][:5]
            class_scores = outputs[class_ids]
            for index, (class_score, class_id) in enumerate(
                zip(class_scores, class_ids)
            ):
                score = "%.2f" % class_score
                text = "%s:%s(%s)" % (
                    str(class_id),
                    str(self.class_names[int(class_id)]),
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
        elif "loss" in outputs:
            # General (compact) ONNX Model
            outputs = outputs["loss"][0]
            outputs = dict(
                sorted(outputs.items(), key=operator.itemgetter(1), reverse=True)
            )
            for index, (class_name, class_score) in enumerate(outputs.items()):
                score = "%.2f" % class_score
                text = "%s(%s)" % (
                    class_name,
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
                        "class": class_name,
                        "score": score,
                    }
                )

        return image, message

    def set_device(self, device="CUDA"):
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if device == "CPU":
            providers = ["CPUExecutionProvider"]
        self.session.set_providers(providers)

    def get_status(self):
        return self.status


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", help="Camera No", type=int, default=0)
    parser.add_argument("--width", help="Camera Width", type=int, default=1280)
    parser.add_argument("--height", help="Camera Height", type=int, default=780)
    parser.add_argument("--device", help="Device(CUDA,CPU)", default="CUDA")
    parser.add_argument("--use_object_detection", action="store_true")
    args = parser.parse_args()

    # USB Camera
    cap = cv.VideoCapture(args.camera)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    # Model
    model = CustomVisionClassification(device=args.device)
    if args.use_object_detection:
        model = CustomVisionObjectDetection(device=args.device)

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
