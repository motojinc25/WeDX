import os

import dearpygui.dearpygui as dpg


class ToolbarWindow:
    def __init__(self, settings=None, edgeaiwindow=None):
        self.settings = settings
        self.edgeaiwindow = edgeaiwindow

    def create_widgets(self):
        current_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.abspath(os.path.join(current_path, "../assets/icons"))

        # Icon Registry
        with dpg.texture_registry(show=False):
            w, h, _, data = dpg.load_image(os.path.join(icon_path, "new.png"))
            dpg.add_static_texture(w, h, data, tag="texture:new")
            w, h, _, data = dpg.load_image(os.path.join(icon_path, "import.png"))
            dpg.add_static_texture(w, h, data, tag="texture:import")
            w, h, _, data = dpg.load_image(os.path.join(icon_path, "export.png"))
            dpg.add_static_texture(w, h, data, tag="texture:export")
            w, h, _, data = dpg.load_image(os.path.join(icon_path, "active_play.png"))
            dpg.add_static_texture(w, h, data, tag="texture:active_play")
            w, h, _, data = dpg.load_image(os.path.join(icon_path, "active_stop.png"))
            dpg.add_static_texture(w, h, data, tag="texture:active_stop")
            w, h, _, data = dpg.load_image(os.path.join(icon_path, "inactive_play.png"))
            dpg.add_static_texture(w, h, data, tag="texture:inactive_play")
            w, h, _, data = dpg.load_image(os.path.join(icon_path, "inactive_stop.png"))
            dpg.add_static_texture(w, h, data, tag="texture:inactive_stop")

        # Toolbar
        with dpg.group(horizontal=True, horizontal_spacing=3):
            dpg.add_image_button("texture:new", callback=self._callback_new)
            dpg.add_image_button("texture:import", callback=self._callback_import)
            dpg.add_image_button("texture:export", callback=self._callback_export)
            dpg.add_spacer(height=2)
            dpg.add_spacer(height=2)
            dpg.add_image_button(
                "texture:active_play",
                callback=self._callback_start,
                tag="toolbar:play",
            )
            dpg.add_image_button(
                "texture:active_stop",
                callback=self._callback_stop,
                tag="toolbar:stop",
            )
            dpg.add_spacer(height=2)
            dpg.add_spacer(height=2)
            dpg.add_slider_int(
                label="FPS",
                default_value=self.settings["fps"],
                vertical=True,
                min_value=1,
                max_value=30,
                height=40,
                callback=self._callback_fps,
            )

    def _callback_fps(self, sender, app_data, user_data):
        self.settings["fps"] = app_data

    def _callback_new(self, sender, app_data, user_data):
        dpg.configure_item("modal_new_pipeline", show=True)

    def _callback_import(self, sender, app_data, user_data):
        if self.edgeaiwindow.get_node_id() == 0:
            dpg.show_item("file_dialog_import")
        else:
            dpg.configure_item("modal_import_failure", show=True)

    def _callback_export(self, sender, app_data, user_data):
        dpg.show_item("file_dialog_export")

    def _callback_start(self, sender, app_data, user_data):
        self.settings["state"] = "active"
        dpg.configure_item("toolbar:play", texture_tag="texture:active_play")
        dpg.configure_item("toolbar:stop", texture_tag="texture:active_stop")

    def _callback_stop(self, sender, app_data, user_data):
        self.settings["state"] = "inactive"
        dpg.configure_item("toolbar:play", texture_tag="texture:inactive_play")
        dpg.configure_item("toolbar:stop", texture_tag="texture:inactive_stop")
