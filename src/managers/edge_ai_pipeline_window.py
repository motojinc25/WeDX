import copy
import datetime
import json
import os
import platform
from collections import OrderedDict
from glob import glob
from importlib import import_module

import dearpygui.dearpygui as dpg


class EdgeAIPipelineWindow:
    dag_editor_tag = "edge_ai_pipeline_window"
    node_id = 0
    settings = None
    last_pos = None
    menu_instances = {}
    node_tags = []
    node_links = []
    node_refresh_graph = {}
    node_link_graph = {}

    def __init__(self, settings=None):
        self.settings = settings

    def create_widgets(self):
        # Export/Import File Dialog
        with dpg.file_dialog(
            label="Export Pipeline",
            directory_selector=False,
            show=False,
            modal=True,
            height=int(self.settings["viewport_height"] / 2),
            default_filename="PL" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
            default_path=os.path.abspath(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.wedx/")
            ),
            callback=self.callback_file_dialog_export,
            id="file_dialog_export",
        ):
            dpg.add_file_extension(".wedx")
            dpg.add_file_extension("", color=(150, 255, 150, 255))
        with dpg.file_dialog(
            label="Import Pipeline",
            directory_selector=False,
            show=False,
            modal=True,
            height=int(self.settings["viewport_height"] / 2),
            default_path=os.path.abspath(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.wedx/")
            ),
            callback=self.callback_file_dialog_import,
            id="file_dialog_import",
        ):
            dpg.add_file_extension(".wedx")
            dpg.add_file_extension("", color=(150, 255, 150, 255))

        # Popup windows
        with dpg.window(
            label="Import Failure",
            modal=True,
            show=False,
            id="modal_import_failure",
            no_title_bar=True,
            pos=[52, 52],
        ):
            dpg.add_text(
                "Sorry. In the current implementation, \nfile import works only before adding a node.",
            )
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="OK",
                    width=-1,
                    callback=lambda: dpg.configure_item(
                        "modal_import_failure",
                        show=False,
                    ),
                )
        with dpg.window(
            label="New Pipeline",
            modal=True,
            show=False,
            id="modal_new_pipeline",
            no_title_bar=True,
            pos=[52, 52],
        ):
            dpg.add_text(
                "Do you want new pipeline?",
            )
            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Yes", width=75, callback=self.callback_new_pipeline
                )
                dpg.add_button(
                    label="Cancel",
                    width=75,
                    callback=lambda: dpg.configure_item(
                        "modal_new_pipeline", show=False
                    ),
                )

        # Add windows for Edge AI Pipeline
        with dpg.group(horizontal=True):
            with dpg.child_window(width=230, autosize_y=True):
                # Editor group node button theme
                with dpg.theme(tag="theme_editor_group_sources"):
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, [51, 102, 0])
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [76, 153, 0])
                        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)
                with dpg.theme(tag="theme_editor_group_processors"):
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, [102, 51, 0])
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [153, 76, 0])
                        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)
                with dpg.theme(tag="theme_editor_group_sinks"):
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, [102, 0, 102])
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [153, 0, 153])
                        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)
                with dpg.theme(tag="theme_editor_group_debugging"):
                    with dpg.theme_component(dpg.mvButton):
                        dpg.add_theme_color(dpg.mvThemeCol_Button, [0, 51, 102])
                        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [0, 76, 153])
                        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
                        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 3, 3)

                # Create node widgets
                menus = OrderedDict(
                    {
                        "Source nodes": "sources",
                        "Processor nodes": "processors",
                        "Sink nodes": "sinks",
                        "Debugging nodes": "debugging",
                    }
                )
                for menu_info in menus.items():
                    menu_label = menu_info[0]
                    with dpg.collapsing_header(label=menu_label):
                        node_sources_path = os.path.abspath(
                            os.path.join(
                                os.path.dirname(os.path.abspath(__file__)),
                                "../nodes/edge_ai_pipeline",
                                menu_info[1],
                                "*.py",
                            )
                        )
                        node_sources = glob(node_sources_path)
                        for node_source in node_sources:
                            import_path = os.path.splitext(
                                os.path.normpath(node_source)
                            )[0]
                            if platform.system() == "Windows":
                                import_path = import_path.replace("\\", ".")
                            else:
                                import_path = import_path.replace("/", ".")
                            import_path = import_path.split(".")
                            import_path = ".".join(import_path[-4:])
                            if import_path.endswith("__init__"):
                                continue
                            module = import_module(import_path)
                            node = module.EdgeAINode(self.settings)
                            base_node_tag = node.name.lower().replace(" ", "_")
                            dpg.add_button(
                                tag="menu_" + base_node_tag,
                                label=node.name,
                                callback=self.callback_add_node,
                                user_data=base_node_tag,
                                width=-1,
                            )
                            dpg.bind_item_theme(
                                "menu_" + base_node_tag,
                                "theme_editor_group_" + menu_info[1],
                            )
                            self.menu_instances[base_node_tag] = node

            # Add a node editor
            with dpg.node_editor(
                tag=self.dag_editor_tag,
                callback=self.callback_editor_link,
                delink_callback=self.callback_editor_delink,
                minimap=True,
                minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            ):
                pass

        with dpg.handler_registry():
            dpg.add_mouse_click_handler(callback=self.callback_save_last_pos)
            dpg.add_key_press_handler(
                dpg.mvKey_Delete,
                callback=self.callback_mv_key_del,
            )

    def get_node_list(self):
        return self.node_tags

    def get_node_instance(self, node_name):
        return self.menu_instances.get(node_name, None)

    def callback_add_node(self, sender, app_data, user_data):
        self.node_id += 1
        node = self.menu_instances[user_data]
        if self.last_pos is None:
            self.last_pos = [0, 0]
        else:
            self.last_pos = [self.last_pos[0] + 30, self.last_pos[1] + 30]
        dag_node_tag = node.add_node(
            self.dag_editor_tag,
            self.node_id,
            pos=self.last_pos,
        )
        self.node_tags.append(dag_node_tag)
        self.set_node_graph(self.node_tags, self.node_links)

    def callback_editor_link(self, sender, app_data, user_data):
        source_type = app_data[0].split(":")[2]
        destination_type = app_data[1].split(":")[2]
        if source_type == destination_type:
            duplicate_flag = False
            for node_link in self.node_links:
                if app_data[1] == node_link[1]:
                    duplicate_flag = True
            if not duplicate_flag:
                dpg.add_node_link(app_data[0], app_data[1], parent=sender)
                self.node_links.append([app_data[0], app_data[1]])
        self.set_node_graph(self.node_tags, self.node_links)

    def callback_editor_delink(self, sender, app_data, user_data):
        self.node_links.remove(
            [
                dpg.get_item_configuration(app_data)["attr_1"],
                dpg.get_item_configuration(app_data)["attr_2"],
            ]
        )
        self.set_node_graph(self.node_tags, self.node_links)
        dpg.delete_item(app_data)

    def set_node_graph(self, node_tags, node_links):
        node_refresh_graph = {}
        node_link_graph = {}
        for node_link in node_links:
            src_node_link = node_link[0]
            dst_node_link = node_link[1]
            src_dpg_node_tag = ":".join(node_link[0].split(":")[:2])
            dst_dpg_node_tag = ":".join(dst_node_link.split(":")[:2])
            if dst_dpg_node_tag not in node_link_graph:
                node_link_graph[dst_dpg_node_tag] = [[src_node_link, dst_node_link]]
            else:
                node_link_graph[dst_dpg_node_tag].append([src_node_link, dst_node_link])
            if dst_dpg_node_tag not in node_refresh_graph:
                node_refresh_graph[dst_dpg_node_tag] = [src_dpg_node_tag]
            else:
                node_refresh_graph[dst_dpg_node_tag].append(src_dpg_node_tag)
        for node_tag in node_tags:
            if node_tag not in node_refresh_graph:
                node_refresh_graph[node_tag] = []
        self.node_refresh_graph = node_refresh_graph
        self.node_link_graph = node_link_graph

    def callback_new_pipeline(self, sender, app_data, user_data):
        dpg.configure_item("modal_new_pipeline", show=False)
        self.new_pipeline()

    def new_pipeline(self):
        self.node_refresh_graph = {}
        self.node_link_graph = {}
        for dpg_node_tag in self.node_tags:
            node_id, node_name = dpg_node_tag.split(":")
            node = self.menu_instances[node_name]
            try:
                node.delete(node_id)
            except:
                pass
        self.last_pos = None
        self.node_tags = []
        self.node_links = []
        self.node_id = 0

    def callback_file_dialog_export(self, sender, app_data, user_data):
        export_data = self.export_pipeline()
        with open(app_data["file_path_name"], "w") as fp:
            json.dump(export_data, fp, indent=2)

    def export_pipeline(self):
        export_data = {}
        export_data["node_tags"] = self.node_tags
        export_data["node_links"] = self.node_links
        for dpg_node_tag in self.node_tags:
            node_id, node_name = dpg_node_tag.split(":")
            node = self.menu_instances[node_name]
            params = node.get_export_params(node_id)
            export_data[dpg_node_tag] = {
                "id": str(node_id),
                "name": str(node_name),
                "params": params,
            }
        return export_data

    def callback_file_dialog_import(self, sender, app_data, user_data):
        if os.path.exists(app_data["file_path_name"]):
            import_data = None
            with open(app_data["file_path_name"]) as fp:
                import_data = json.load(fp)
                self.import_pipeline(import_data)

    def import_pipeline(self, import_data):
        if "node_tags" in import_data and "node_links" in import_data:
            for dpg_node_tag in import_data["node_tags"]:
                node_id, node_name = dpg_node_tag.split(":")
                node_id = int(node_id)
                if node_id > self.node_id:
                    self.node_id = node_id
                node = self.menu_instances[node_name]
                version = import_data[dpg_node_tag]["params"]["version"]
                if version != node.version:
                    pass
                position = import_data[dpg_node_tag]["params"]["position"]
                node.add_node(self.dag_editor_tag, node_id, pos=position)
                node.set_import_params(node_id, import_data[dpg_node_tag]["params"])
            self.node_tags = import_data["node_tags"]
            self.node_links = import_data["node_links"]
            for node_link in self.node_links:
                dpg.add_node_link(
                    node_link[0], node_link[1], parent=self.dag_editor_tag
                )
            self.set_node_graph(self.node_tags, self.node_links)

    def callback_save_last_pos(self, sender, app_data, user_data):
        if len(dpg.get_selected_nodes(self.dag_editor_tag)) > 0:
            self.last_pos = dpg.get_item_pos(
                dpg.get_selected_nodes(self.dag_editor_tag)[0]
            )

    def callback_mv_key_del(self, sender, app_data, user_data):
        if len(dpg.get_selected_nodes(self.dag_editor_tag)) > 0:
            item_id = dpg.get_selected_nodes(self.dag_editor_tag)[0]
            dpg_node_tag = dpg.get_item_alias(item_id)
            node_id, node_name = dpg_node_tag.split(":")
            node_instance = self.get_node_instance(node_name)
            node_instance.close(node_id)
            self.node_tags.remove(dpg_node_tag)
            copy_node_links = copy.deepcopy(self.node_links)
            for link_info in copy_node_links:
                source_node = link_info[0].split(":")[:2]
                source_node = ":".join(source_node)
                destination_node = link_info[1].split(":")[:2]
                destination_node = ":".join(destination_node)
                if source_node == dpg_node_tag or destination_node == dpg_node_tag:
                    self.node_links.remove(link_info)
            self.set_node_graph(self.node_tags, self.node_links)
            dpg.delete_item(item_id)

    def get_node_id(self):
        return self.node_id
