import array
from abc import ABCMeta, abstractmethod

import cv2
import dearpygui.dearpygui as dpg
import numpy as np


class BaseNode(metaclass=ABCMeta):
    version = "0.0.0"
    name = "Base"
    theme_titlebar = [102, 51, 0]
    theme_titlebar_selected = [153, 76, 0]
    settings = None  # Dear PyGui Window setting
    configs = {}  # Dear PyGui Node config

    # Video and Message position constants
    VIDEO_IN = 0
    VIDEO_OUT = 1
    MESSAGE_IN = 2
    MESSAGE_OUT = 3

    @abstractmethod
    def add_node(self, parent, node_id, pos):
        pass

    @abstractmethod
    def update(self, node_id, node_links, node_frames, node_messages):
        pass

    @abstractmethod
    def close(self, node_id):
        pass

    @abstractmethod
    def delete(self, node_id):
        pass

    @abstractmethod
    def get_export_params(self, node_id):
        pass

    @abstractmethod
    def set_import_params(self, node_id, params):
        pass

    def get_blank_texture(self, width, height):
        # Generate black raw texture
        texture_data = []
        for _ in range(0, width * height):
            texture_data.append(0)
            texture_data.append(0)
            texture_data.append(0)
            texture_data.append(255 / 255)
        raw_texture = array.array("f", texture_data)
        return raw_texture

    def get_image_texture(self, image, width, height):
        # Resize image for Dear PyGui texture
        resize_image = cv2.resize(image, dsize=(width, height))
        resize_image = cv2.cvtColor(resize_image, cv2.COLOR_BGR2RGBA)
        resize_image = resize_image.ravel()  # Flatten camera data to a 1 d stricture
        resize_image = np.asfarray(
            resize_image, dtype="f"
        )  # Change data type to 32bit floats

        # Normalize image data to prepare for GPU
        image_texture = np.true_divide(resize_image, 255.0)
        return image_texture

    def get_tag_list(self, node_tag):
        # Video Input, Video Output, Message Input, Message Output
        tag_list = []
        tag_list.append(
            ":".join(
                [
                    node_tag,
                    str(dpg.mvNode_PinShape_CircleFilled),
                    str(dpg.mvNode_Attr_Input),
                ]
            )
        )
        tag_list.append(
            ":".join(
                [
                    node_tag,
                    str(dpg.mvNode_PinShape_CircleFilled),
                    str(dpg.mvNode_Attr_Output),
                ]
            )
        )
        tag_list.append(
            ":".join(
                [
                    node_tag,
                    str(dpg.mvNode_PinShape_Quad),
                    str(dpg.mvNode_Attr_Input),
                ]
            )
        )
        tag_list.append(
            ":".join(
                [
                    node_tag,
                    str(dpg.mvNode_PinShape_Quad),
                    str(dpg.mvNode_Attr_Output),
                ]
            )
        )
        return tag_list
