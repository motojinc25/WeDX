import logging

from gui.constants import Attribute, PinShape
from nodes.edge_ai_pipeline.base import BaseNode

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    pass


class EdgeAINode(BaseNode):
    def __init__(self, settings, logger=logging.getLogger(__name__)):
        self.version = "0.1.0"
        self.name = "USB Camera"
        self.theme_titlebar = [51, 102, 0]
        self.theme_titlebar_selected = [76, 153, 0]
        self.settings = settings
        self.logger = logger
        self.forms = {}
        self.forms["device"] = {}

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.forms["device"][dpg_node_tag] = ""

        if self.settings["gui"]:
            # Add a dynamic texture and a raw texture
            with dpg.texture_registry(show=False):
                dpg.add_raw_texture(
                    self.settings["node_width"],
                    self.settings["node_height"],
                    self.get_blank_texture(
                        self.settings["node_width"], self.settings["node_height"]
                    ),
                    tag=dpg_node_tag + ":texture",
                    format=dpg.mvFormat_Float_rgba,
                )

            # Add a node to a node editor
            with dpg.node(
                tag=dpg_node_tag, parent=parent, label=self.name, pos=pos
            ) as dpg_node:
                # Set node color
                with dpg.theme() as dpg_theme:
                    with dpg.theme_component(dpg.mvNode):
                        dpg.add_theme_color(
                            dpg.mvNodeCol_TitleBar,
                            self.theme_titlebar,
                            category=dpg.mvThemeCat_Nodes,
                        )
                        dpg.add_theme_color(
                            dpg.mvNodeCol_TitleBarHovered,
                            self.theme_titlebar_selected,
                            category=dpg.mvThemeCat_Nodes,
                        )
                        dpg.add_theme_color(
                            dpg.mvNodeCol_TitleBarSelected,
                            self.theme_titlebar_selected,
                            category=dpg.mvThemeCat_Nodes,
                        )
                        dpg.add_theme_color(
                            dpg.mvNodeCol_NodeOutline,
                            self.theme_titlebar,
                            category=dpg.mvThemeCat_Nodes,
                        )
                        dpg.bind_item_theme(dpg_node, dpg_theme)

                # Add pins that allows linking inputs and outputs
                with dpg.node_attribute(
                    attribute_type=int(Attribute.OUTPUT),
                    tag=dpg_pin_tags[self.VIDEO_OUT],
                ):
                    with dpg.group(horizontal=True):
                        dpg.add_text("VIDEO OUT")
                        dpg.add_spacer(width=self.settings["node_width"] - 100)
                        dpg.add_checkbox(
                            label="",
                            tag=dpg_node_tag + ":video_out",
                            default_value=True,
                        )
                with dpg.node_attribute(
                    attribute_type=int(Attribute.OUTPUT),
                    shape=int(PinShape.QUAD),
                    tag=dpg_pin_tags[self.MESSAGE_OUT],
                ):
                    with dpg.group(horizontal=True):
                        dpg.add_text("MESSAGE OUT")
                        dpg.add_spacer(width=self.settings["node_width"] - 120)
                        dpg.add_checkbox(
                            label="",
                            tag=dpg_node_tag + ":message_out",
                            default_value=True,
                        )

                # Add a combo dropdown that allows selecting usb camera device number
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_spacer(height=5)
                    dpg.add_combo(
                        self.settings["device_no_list"],
                        width=self.settings["node_width"] - 100,
                        default_value=self.forms["device"][dpg_node_tag],
                        label="Device",
                        callback=self.callback_change_device,
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":device",
                    )

                # Add an image from a specified texture
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_image(dpg_node_tag + ":texture")

        # Return Dear PyGui Tag
        return dpg_node_tag

    async def refresh(self, node_id, node_links, node_frames, node_messages):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        frame = None
        message = None

        # Video capturing from USB Camera
        device_no = self.forms["device"][dpg_node_tag]
        if device_no != "" and device_no is not None:
            device_no = int(device_no)
            camera_index = self.settings["device_no_list"].index(device_no)
            camera_capture = self.settings["camera_capture_list"][camera_index]

            # Capture frame-by-frame
            if camera_capture is not None:
                ret, frame = camera_capture.read()
                if ret == True:
                    texture = self.get_image_texture(
                        frame, self.settings["node_width"], self.settings["node_height"]
                    )
                    if self.settings["gui"]:
                        if dpg.does_item_exist(dpg_node_tag + ":texture"):
                            dpg.set_value(dpg_node_tag + ":texture", texture)

            # Generate message
            message = [
                {
                    "type": "source",
                    "subtype": self.name.lower().replace(" ", "_"),
                    "image": {
                        "source": device_no,
                        "width": self.settings["usb_camera_width"],
                        "height": self.settings["usb_camera_height"],
                    },
                }
            ]

        # Control output
        if self.settings["gui"]:
            if not dpg.get_value(dpg_node_tag + ":message_out"):
                message = None
            if not dpg.get_value(dpg_node_tag + ":video_out"):
                frame = None

        # Return frame and message
        return frame, message

    def close(self, node_id):
        pass

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if self.settings["gui"]:
            dpg.delete_item(dpg_node_tag + ":texture")
            dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        if self.settings["gui"]:
            params["version"] = self.version
            params["position"] = dpg.get_item_pos(dpg_node_tag)
            params["device"] = self.forms["device"][dpg_node_tag]
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if (
            "device" in params
            and len(params["device"]) > 0
            and int(params["device"]) in self.settings["device_no_list"]
        ):
            self.forms["device"][dpg_node_tag] = params["device"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":device", params["device"])

    def callback_change_device(self, sender, data, user_data):
        dpg_node_tag = user_data
        self.forms["device"][dpg_node_tag] = data
