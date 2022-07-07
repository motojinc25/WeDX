#!/usr/bin/env python
import argparse
import copy
import os

import cv2 as cv
import numpy as np
import onnxruntime

coco_class_names = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorbike",
    4: "aeroplane",
    5: "bus",
    6: "train",
    7: "truck",
    8: "boat",
    9: "traffic light",
    10: "fire hydrant",
    11: "stop sign",
    12: "parking meter",
    13: "bench",
    14: "bird",
    15: "cat",
    16: "dog",
    17: "horse",
    18: "sheep",
    19: "cow",
    20: "elephant",
    21: "bear",
    22: "zebra",
    23: "giraffe",
    24: "backpack",
    25: "umbrella",
    26: "handbag",
    27: "tie",
    28: "suitcase",
    29: "frisbee",
    30: "skis",
    31: "snowboard",
    32: "sports ball",
    33: "kite",
    34: "baseball bat",
    35: "baseball glove",
    36: "skateboard",
    37: "surfboard",
    38: "tennis racket",
    39: "bottle",
    40: "wine glass",
    41: "cup",
    42: "fork",
    43: "knife",
    44: "spoon",
    45: "bowl",
    46: "banana",
    47: "apple",
    48: "sandwich",
    49: "orange",
    50: "broccoli",
    51: "carrot",
    52: "hot dog",
    53: "pizza",
    54: "donut",
    55: "cake",
    56: "chair",
    57: "sofa",
    58: "pottedplant",
    59: "bed",
    60: "diningtable",
    61: "toilet",
    62: "tvmonitor",
    63: "laptop",
    64: "mouse",
    65: "remote",
    66: "keyboard",
    67: "cell phone",
    68: "microwave",
    69: "oven",
    70: "toaster",
    71: "sink",
    72: "refrigerator",
    73: "book",
    74: "clock",
    75: "vase",
    76: "scissors",
    77: "teddy bear",
    78: "hair drier",
    79: "toothbrush",
}


class YOLOXNano:
    def __init__(
        self,
        model_path=os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "yolox_nano.onnx",
            )
        ),
        class_score_th=0.0,
        nms_th=0.45,
        nms_score_th=0.1,
        with_p6=False,
        providers=["CPUExecutionProvider"],
    ):
        self.class_score_th = class_score_th
        self.nms_th = nms_th
        self.nms_score_th = nms_score_th
        self.with_p6 = with_p6
        self.onnx_session = onnxruntime.InferenceSession(
            model_path,
            providers=providers,
        )
        self.input_detail = self.onnx_session.get_inputs()[0]
        self.input_name = self.input_detail.name
        self.output_name = self.onnx_session.get_outputs()[0].name
        self.input_shape = self.input_detail.shape[2:]

    def __call__(self, image):
        temp_image = copy.deepcopy(image)
        image_height, image_width = image.shape[0], image.shape[1]
        temp_image, ratio = self._preprocess(temp_image, self.input_shape)
        message = []
        results = self.onnx_session.run(
            None,
            {self.input_name: temp_image[None, :, :, :]},
        )
        bboxes, scores, class_ids = self._postprocess(
            results[0],
            self.input_shape,
            ratio,
            self.nms_th,
            self.nms_score_th,
            image_width,
            image_height,
            p6=self.with_p6,
        )
        score_th=0.4
        thickness=3
        for bbox, score, class_id in zip(bboxes, scores, class_ids):
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            if score_th > score:
                continue
            color = self._get_color(class_id)
            image = cv.rectangle(
                image,
                (x1, y1),
                (x2, y2),
                color,
                thickness=thickness,
            )
            score = "%.2f" % score
            text = "%s:%s" % (str(coco_class_names[int(class_id)]), score)
            image = cv.putText(
                image,
                text,
                (x1, y1 - 10),
                cv.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                thickness=thickness,
            )
            message.append([x1, x2, y1, y2, int(class_id)])
        return image, message

    def _preprocess(self, image, input_size, swap=(2, 0, 1)):
        if len(image.shape) == 3:
            padded_image = (
                np.ones((input_size[0], input_size[1], 3), dtype=np.uint8) * 114
            )
        else:
            padded_image = np.ones(input_size, dtype=np.uint8) * 114
        ratio = min(input_size[0] / image.shape[0], input_size[1] / image.shape[1])
        resized_image = cv.resize(
            image,
            (int(image.shape[1] * ratio), int(image.shape[0] * ratio)),
            interpolation=cv.INTER_LINEAR,
        )
        resized_image = resized_image.astype(np.uint8)
        padded_image[
            : int(image.shape[0] * ratio), : int(image.shape[1] * ratio)
        ] = resized_image
        padded_image = padded_image.transpose(swap)
        padded_image = np.ascontiguousarray(padded_image, dtype=np.float32)
        return padded_image, ratio

    def _postprocess(
        self,
        outputs,
        img_size,
        ratio,
        nms_th,
        nms_score_th,
        max_width,
        max_height,
        p6=False,
    ):
        grids = []
        expanded_strides = []
        if not p6:
            strides = [8, 16, 32]
        else:
            strides = [8, 16, 32, 64]
        hsizes = [img_size[0] // stride for stride in strides]
        wsizes = [img_size[1] // stride for stride in strides]
        for hsize, wsize, stride in zip(hsizes, wsizes, strides):
            xv, yv = np.meshgrid(np.arange(wsize), np.arange(hsize))
            grid = np.stack((xv, yv), 2).reshape(1, -1, 2)
            grids.append(grid)
            shape = grid.shape[:2]
            expanded_strides.append(np.full((*shape, 1), stride))
        grids = np.concatenate(grids, 1)
        expanded_strides = np.concatenate(expanded_strides, 1)
        outputs[..., :2] = (outputs[..., :2] + grids) * expanded_strides
        outputs[..., 2:4] = np.exp(outputs[..., 2:4]) * expanded_strides
        predictions = outputs[0]
        boxes = predictions[:, :4]
        scores = predictions[:, 4:5] * predictions[:, 5:]
        boxes_xyxy = np.ones_like(boxes)
        boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2.0
        boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2.0
        boxes_xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2.0
        boxes_xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2.0
        boxes_xyxy /= ratio
        dets = self._multiclass_nms(
            boxes_xyxy,
            scores,
            nms_thr=nms_th,
            score_thr=nms_score_th,
        )
        bboxes, scores, class_ids = [], [], []
        if dets is not None:
            bboxes, scores, class_ids = dets[:, :4], dets[:, 4], dets[:, 5]
            for bbox in bboxes:
                bbox[0] = max(0, bbox[0])
                bbox[1] = max(0, bbox[1])
                bbox[2] = min(bbox[2], max_width)
                bbox[3] = min(bbox[3], max_height)
        return bboxes, scores, class_ids

    def _nms(self, boxes, scores, nms_thr):
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = scores.argsort()[::-1]
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            w = np.maximum(0.0, xx2 - xx1 + 1)
            h = np.maximum(0.0, yy2 - yy1 + 1)
            inter = w * h
            ovr = inter / (areas[i] + areas[order[1:]] - inter)
            inds = np.where(ovr <= nms_thr)[0]
            order = order[inds + 1]
        return keep

    def _multiclass_nms(
        self,
        boxes,
        scores,
        nms_thr,
        score_thr,
        class_agnostic=True,
    ):
        if class_agnostic:
            nms_method = self._multiclass_nms_class_agnostic
        else:
            nms_method = self._multiclass_nms_class_aware
        return nms_method(boxes, scores, nms_thr, score_thr)

    def _multiclass_nms_class_aware(self, boxes, scores, nms_thr, score_thr):
        final_dets = []
        num_classes = scores.shape[1]
        for cls_ind in range(num_classes):
            cls_scores = scores[:, cls_ind]
            valid_score_mask = cls_scores > score_thr
            if valid_score_mask.sum() == 0:
                continue
            else:
                valid_scores = cls_scores[valid_score_mask]
                valid_boxes = boxes[valid_score_mask]
                keep = self._nms(valid_boxes, valid_scores, nms_thr)
                if len(keep) > 0:
                    cls_inds = np.ones((len(keep), 1)) * cls_ind
                    dets = np.concatenate(
                        [valid_boxes[keep], valid_scores[keep, None], cls_inds],
                        1,
                    )
                    final_dets.append(dets)
        if len(final_dets) == 0:
            return None
        return np.concatenate(final_dets, 0)

    def _multiclass_nms_class_agnostic(self, boxes, scores, nms_thr, score_thr):
        cls_inds = scores.argmax(1)
        cls_scores = scores[np.arange(len(cls_inds)), cls_inds]
        valid_score_mask = cls_scores > score_thr
        if valid_score_mask.sum() == 0:
            return None
        valid_scores = cls_scores[valid_score_mask]
        valid_boxes = boxes[valid_score_mask]
        valid_cls_inds = cls_inds[valid_score_mask]
        keep = self._nms(valid_boxes, valid_scores, nms_thr)
        dets = None
        if keep:
            dets = np.concatenate(
                [
                    valid_boxes[keep],
                    valid_scores[keep, None],
                    valid_cls_inds[keep, None],
                ],
                1,
            )
        return dets

    def _get_color(self, index):
        temp_index = abs(int(index + 5)) * 3
        color = (
            (29 * temp_index) % 255,
            (17 * temp_index) % 255,
            (37 * temp_index) % 255,
        )
        return color


if __name__ == "__main__":
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", help="Camera Device No", type=int, default=0)
    parser.add_argument("--width", help="Camera Width", type=int, default=1280)
    parser.add_argument("--height", help="Camera Height", type=int, default=780)
    parser.add_argument("--threshold", help="Score Threshold", type=float, default=0.5)
    args = parser.parse_args()

    # USB Camera
    cap = cv.VideoCapture(args.device)
    cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    # Model
    model = YOLOXNano()

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
