#!/usr/bin/env python
import argparse
import copy
import os

import cv2 as cv
import numpy as np
import onnxruntime as ort


class MoveNetMPL:
    def __init__(
        self,
        model_path=os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "movenet_multipose_lightning_1.onnx",
            )
        ),
        input_shape=(256, 256),
        device="CUDA",
    ):
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if device == "CPU":
            providers = ["CPUExecutionProvider"]
        self.session = ort.InferenceSession(
            model_path,
            providers=providers,
        )
        self.input_shape = input_shape
        self.input_name = self.session.get_inputs()[0].name

    def __call__(self, image):
        image_width, image_height = image.shape[1], image.shape[0]
        input_image = cv.resize(image, dsize=(self.input_shape[1], self.input_shape[0]))
        input_image = cv.cvtColor(input_image, cv.COLOR_BGR2RGB)
        input_image = input_image.reshape(
            -1, self.input_shape[0], self.input_shape[1], 3
        )
        input_image = input_image.astype("int32")
        outputs = self.session.run(None, {self.input_name: input_image})
        keypoints_with_scores = outputs[0]
        keypoints_with_scores = np.squeeze(keypoints_with_scores)
        results_list = []
        landmark_dict = {}
        for keypoints_with_score in keypoints_with_scores:
            for id in range(17):
                keypoint_x = int(image_width * keypoints_with_score[(id * 3) + 1])
                keypoint_y = int(image_height * keypoints_with_score[(id * 3) + 0])
                score = keypoints_with_score[(id * 3) + 2]
                landmark_dict[id] = [keypoint_x, keypoint_y, float(score)]

            bbox_ymin = int(image_height * keypoints_with_score[51])
            bbox_xmin = int(image_width * keypoints_with_score[52])
            bbox_ymax = int(image_height * keypoints_with_score[53])
            bbox_xmax = int(image_width * keypoints_with_score[54])
            bbox_score = keypoints_with_score[55]
            landmark_dict["bbox"] = [
                bbox_xmin,
                bbox_ymin,
                bbox_xmax,
                bbox_ymax,
                float(bbox_score),
            ]
            results_list.append(copy.deepcopy(landmark_dict))
        score_th = 0.5
        message = results_list
        for results in results_list:
            for id in range(17):
                landmark_x, landmark_y = results[id][0], results[id][1]
                visibility = results[id][2]
                if score_th > visibility:
                    continue
                cv.circle(image, (landmark_x, landmark_y), 5, (0, 255, 0), -1)
            if results[0][2] > score_th and results[1][2] > score_th:
                cv.line(image, results[0][:2], results[1][:2], (0, 255, 0), 2)
            if results[0][2] > score_th and results[2][2] > score_th:
                cv.line(image, results[0][:2], results[2][:2], (0, 255, 0), 2)
            if results[1][2] > score_th and results[3][2] > score_th:
                cv.line(image, results[1][:2], results[3][:2], (0, 255, 0), 2)
            if results[2][2] > score_th and results[4][2] > score_th:
                cv.line(image, results[2][:2], results[4][:2], (0, 255, 0), 2)
            if results[5][2] > score_th and results[6][2] > score_th:
                cv.line(image, results[5][:2], results[6][:2], (0, 255, 0), 2)
            if results[5][2] > score_th and results[7][2] > score_th:
                cv.line(image, results[5][:2], results[7][:2], (0, 255, 0), 2)
            if results[7][2] > score_th and results[9][2] > score_th:
                cv.line(image, results[7][:2], results[9][:2], (0, 255, 0), 2)
            if results[6][2] > score_th and results[8][2] > score_th:
                cv.line(image, results[6][:2], results[8][:2], (0, 255, 0), 2)
            if results[8][2] > score_th and results[10][2] > score_th:
                cv.line(image, results[8][:2], results[10][:2], (0, 255, 0), 2)
            if results[11][2] > score_th and results[12][2] > score_th:
                cv.line(image, results[11][:2], results[12][:2], (0, 255, 0), 2)
            if results[5][2] > score_th and results[11][2] > score_th:
                cv.line(image, results[5][:2], results[11][:2], (0, 255, 0), 2)
            if results[11][2] > score_th and results[13][2] > score_th:
                cv.line(image, results[11][:2], results[13][:2], (0, 255, 0), 2)
            if results[13][2] > score_th and results[15][2] > score_th:
                cv.line(image, results[13][:2], results[15][:2], (0, 255, 0), 2)
            if results[6][2] > score_th and results[12][2] > score_th:
                cv.line(image, results[6][:2], results[12][:2], (0, 255, 0), 2)
            if results[12][2] > score_th and results[14][2] > score_th:
                cv.line(image, results[12][:2], results[14][:2], (0, 255, 0), 2)
            if results[14][2] > score_th and results[16][2] > score_th:
                cv.line(image, results[14][:2], results[16][:2], (0, 255, 0), 2)
            bbox = results.get("bbox", None)
            if bbox is not None:
                if bbox[4] > score_th:
                    image = cv.rectangle(
                        image,
                        (bbox[0], bbox[1]),
                        (bbox[2], bbox[3]),
                        (0, 255, 0),
                        thickness=2,
                    )
        return image, message

    def set_device(self, device="CUDA"):
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if device == "CPU":
            providers = ["CPUExecutionProvider"]
        self.session.set_providers(providers)


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
    model = MoveNetMPL(device=args.device)

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
