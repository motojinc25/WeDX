import dearpygui.dearpygui as dpg

from nodes.edge_ai_pipeline.base import BaseNode


class EdgeAINode(BaseNode):
    def __init__(self, settings):
        self.version = "0.1.0"
        self.name = "Builtin IoT Message"
        self.theme_titlebar = [102, 0, 102]
        self.theme_titlebar_selected = [153, 0, 153]
        self.settings = settings
        self.configs = {}
        self.configs["instances"] = {}
        self.configs["label_connect"] = "Connect"
        self.configs["label_connected"] = "Connected"

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)

        # Add a Popup window
        with dpg.window(
            label="Connection Failure",
            modal=True,
            show=False,
            width=200,
            height=120,
            pos=[200, 200],
            tag=dpg_node_tag + ":modal",
        ):
            dpg.add_text("Sending IoT Message,\nplease set in Settings - IoT Device")
            dpg.add_spacer(height=5)
            dpg.add_button(
                label="OK",
                width=-1,
                callback=lambda: dpg.configure_item(
                    dpg_node_tag + ":modal", show=False
                ),
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
                attribute_type=dpg.mvNode_Attr_Input,
                shape=dpg.mvNode_PinShape_Quad,
                tag=dpg_pin_tags[self.MESSAGE_IN],
            ):
                dpg.add_text("MESSAGE IN")

            # Add a button for publishing
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(
                    label=self.configs["label_connect"],
                    width=self.settings["node_width"],
                    callback=self.callback_button_connect,
                    user_data=dpg_node_tag,
                    tag=dpg_node_tag + ":connect",
                )

        # Update connect status
        self.update_connect_status(node_id)

        # Return Dear PyGui Tag
        return dpg_node_tag

    async def refresh(self, node_id, node_links, node_frames, node_messages):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        message = None

        # Get linked node tag
        for link in node_links:
            link_pin_shape = link[0].split(":")[2]
            if link_pin_shape == str(dpg.mvNode_PinShape_Quad):
                linked_node_tag_message = ":".join(link[0].split(":")[:2])
                message = node_messages.get(linked_node_tag_message, None)

        # Publish message
        if message is not None:
            if (
                dpg.get_item_label(dpg_node_tag + ":connect")
                == self.configs["label_connected"]
            ):
                if "iot_device_instance" in self.settings:
                    self.settings["iot_device_instance"].send_message(message)

        # Update connect status
        self.update_connect_status(node_id)

        # Return frame and message
        return None, None

    def close(self, node_id):
        pass

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg.delete_item(dpg_node_tag + ":modal")
        dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
        params["position"] = dpg.get_item_pos(dpg_node_tag)
        return params

    def set_import_params(self, node_id, params):
        pass

    def update_connect_status(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if "iot_device_instance" in self.settings:
            dpg.set_item_label(
                dpg_node_tag + ":connect", self.configs["label_connected"]
            )
        else:
            dpg.set_item_label(dpg_node_tag + ":connect", self.configs["label_connect"])

    def callback_button_connect(self, sender, data, user_data):
        dpg_node_tag = user_data
        if (
            dpg.get_item_label(dpg_node_tag + ":connect")
            == self.configs["label_connect"]
        ):
            dpg.show_item(dpg_node_tag + ":modal")
