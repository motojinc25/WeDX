import logging
import os
import signal
import webbrowser

import requests

from gui.constants import tag
from version import __version__

try:
    import dearpygui.dearpygui as dpg
    import dearpygui.demo as demo
except ImportError:
    pass


class WeDXStudio:
    settings = None
    logger = None
    is_running = True

    def __init__(self, settings, logger=logging.getLogger(__name__)):
        self.settings = settings
        self.logger = logger
        self.latestVersion = ""

        # Set termination handler
        signal.signal(signal.SIGINT, self.termination_handler)
        signal.signal(signal.SIGTERM, self.termination_handler)

    def create_context(self):
        if self.settings["gui"]:
            dpg.create_context()

    def set_default_font(self):
        if self.settings["gui"]:
            current_path = os.path.dirname(os.path.abspath(__file__))
            with dpg.font_registry():
                font_file = os.path.abspath(
                    os.path.join(
                        current_path, "../assets/fonts/NotoSansCJKjp-Regular.otf"
                    )
                )
                with dpg.font(font_file, 16) as regular_font:
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Japanese)
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Korean)
                    dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
                    dpg.add_font_range_hint(
                        dpg.mvFontRangeHint_Chinese_Simplified_Common
                    )
                dpg.bind_font(regular_font)

    def create_viewport(self):
        if self.settings["gui"]:
            dpg.create_viewport(
                title="WeDX",
                width=self.settings["viewport_width"],
                height=self.settings["viewport_height"],
                x_pos=self.settings["viewport_pos"][0],
                y_pos=self.settings["viewport_pos"][1],
            )

            # About WeDX window
            with dpg.window(
                tag=tag["window"]["about_wedx"],
                label="About WeDX",
                min_size=(480, 350),
                show=False,
                pos=(100, 100),
            ):
                dpg.add_text(f"WeDX: {__version__}")
                dpg.add_spacer()
                dpg.add_separator()
                dpg.add_text("Authors", color=(0, 255, 255))
                dpg.add_text("Jingun Jung @ motojin.com, Inc.", bullet=True)
                dpg.add_text(
                    "".join(
                        (
                            "WeDX is licensed under the GNU AGPL-3.0 License, see LiCENSE for more information.\n",
                            "Repository: https://github.com/motojinc25/WeDX",
                        )
                    )
                )
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Open repository",
                        callback=self.callback_open_website,
                        user_data="https://github.com/motojinc25/WeDX",
                    )
                    dpg.add_button(
                        label="About Jingun Jung",
                        callback=self.callback_open_website,
                        user_data="https://www.linkedin.com/in/jingun-jung",
                    )
                    dpg.add_button(
                        label="About motojin.com, Inc.",
                        callback=self.callback_open_website,
                        user_data="https://motojin.com",
                    )
                dpg.add_spacer()
                dpg.add_separator()
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_text("Created with Dear PyGui")
                    dpg.add_button(
                        label="Show About",
                        callback=lambda: dpg.show_tool(dpg.mvTool_About),
                    )
                    dpg.add_button(
                        label="Open Demo source code",
                        callback=self.callback_open_website,
                        user_data="https://github.com/hoffstadt/DearPyGui/blob/master/dearpygui/demo.py",
                    )
                dpg.add_spacer()
                dpg.add_separator()
                dpg.add_text("Special thanks", color=(0, 255, 255))
                dpg.add_text(
                    "Kazuhito Takahashi - Image-Processing-Node-Editor", bullet=True
                )
                dpg.add_text(
                    "Repository: https://github.com/Kazuhito00/Image-Processing-Node-Editor"
                )
                dpg.add_button(
                    label="Open repository",
                    callback=self.callback_open_website,
                    user_data="https://github.com/Kazuhito00/Image-Processing-Node-Editor",
                )
                dpg.add_spacer()
                dpg.add_separator()
                dpg.add_spacer(height=5)
                dpg.add_button(
                    label="Close",
                    callback=lambda: dpg.hide_item(tag["window"]["about_wedx"]),
                )

            # get latest version
            self.getLatestVersion()

            # Check Updates windows
            with dpg.window(
                tag=tag["window"]["check_for_updates"],
                label="Check for updates",
                min_size=(300, 100),
                show=False,
                pos=(100, 100),
            ):
                if self.latestVersion is None:
                    dpg.add_text("Cannot get the latest version.")
                elif self.latestVersion == __version__:
                    dpg.add_text(
                        f"Current version ( {__version__} ) is the latest version."
                    )
                else:
                    with dpg.group(horizontal=True):
                        dpg.add_text("Get the latest version here:")
                        dpg.add_button(
                            label="WeDX Repository",
                            callback=lambda: webbrowser.open(
                                "https://github.com/motojinc25/WeDX"
                            ),
                        )
                    dpg.add_text(f"Cureent Version: {__version__}")
                    dpg.add_text(f"Latest Version: {self.latestVersion}")
                dpg.add_spacer()
                dpg.add_separator()
                dpg.add_spacer()
                dpg.add_button(
                    label="Close",
                    callback=lambda: dpg.hide_item(tag["window"]["check_for_updates"]),
                )

    def viewport_menu_bar(self):
        if self.settings["gui"]:
            with dpg.viewport_menu_bar(label="Primary Menu Bar", tag="viewport-bar"):
                with dpg.menu(label="File"):
                    dpg.add_menu_item(
                        label="Exit", callback=lambda: dpg.stop_dearpygui()
                    )

                with dpg.menu(label="Settings"):
                    dpg.add_menu_item(
                        label="IoT Device",
                        callback=lambda: dpg.configure_item(
                            tag["window"]["iot_device_setting"], show=True
                        ),
                    )
                    dpg.add_menu_item(
                        label="Logging Level",
                        callback=lambda: dpg.configure_item(
                            tag["window"]["logging_level_setting"], show=True
                        ),
                    )

                with dpg.menu(label="Help"):
                    dpg.add_menu_item(
                        label="About WeDX",
                        callback=lambda: dpg.show_item(tag["window"]["about_wedx"]),
                        shortcut="Ctrl + H",
                    )
                    dpg.add_menu_item(
                        label="View License",
                        callback=self.callback_open_website,
                        user_data="https://github.com/motojinc25/WeDX/blob/main/LICENSE",
                    )
                    dpg.add_menu_item(
                        label="Check for updates",
                        callback=lambda: dpg.show_item(
                            tag["window"]["check_for_updates"]
                        ),
                    )
                    dpg.add_spacer()
                    dpg.add_separator()
                    dpg.add_spacer()
                    dpg.add_menu_item(
                        label="Show Metrics",
                        callback=lambda: dpg.show_tool(dpg.mvTool_Metrics),
                    )
                    dpg.add_menu_item(
                        label="Show Documentation",
                        callback=lambda: dpg.show_tool(dpg.mvTool_Doc),
                    )
                    dpg.add_menu_item(
                        label="Show Debug",
                        callback=lambda: dpg.show_tool(dpg.mvTool_Debug),
                    )
                    dpg.add_menu_item(
                        label="Show Style Editor",
                        callback=lambda: dpg.show_tool(dpg.mvTool_Style),
                    )
                    dpg.add_menu_item(
                        label="Show Font Manager",
                        callback=lambda: dpg.show_tool(dpg.mvTool_Font),
                    )
                    dpg.add_menu_item(
                        label="Show Item Registry",
                        callback=lambda: dpg.show_tool(dpg.mvTool_ItemRegistry),
                    )
                    dpg.add_menu_item(
                        label="Show Dear ImGui Demo",
                        callback=lambda: dpg.show_imgui_demo(),
                    )
                    dpg.add_menu_item(
                        label="Show Dear PyGui Demo",
                        callback=lambda: demo.show_demo(),
                    )

    def create_primary_window(self):
        if self.settings["gui"]:
            with dpg.window(tag=tag["window"]["primary"]) as primary_window:
                # Spacing guide: tool bar
                dpg.add_spacer(width=10, height=15)

                # Primary tab bar
                with dpg.tab_bar(tag=tag["tab_bar"]["primary"]):
                    # Edge AI Pipeline tab
                    dpg.add_tab(
                        label="Edge AI Pipeline", tag=tag["tab"]["edge_ai_pipeline"]
                    )

                # Set the primary window
                dpg.set_primary_window(primary_window, True)

    def setup_dearpygui(self):
        if self.settings["gui"]:
            dpg.setup_dearpygui()

    def show_viewport(self):
        if self.settings["gui"]:
            dpg.show_viewport()

    def is_dearpygui_running(self):
        if self.settings["gui"]:
            return dpg.is_dearpygui_running()
        else:
            return self.is_running

    def render_dearpygui_frame(self):
        if self.settings["gui"]:
            dpg.render_dearpygui_frame()

    def destroy_context(self):
        if self.settings["gui"]:
            dpg.destroy_context()

    def termination_handler(self, signal, frame):
        if self.settings["gui"]:
            dpg.stop_dearpygui()
        else:
            self.is_running = False
        if self.settings["webapp"]:
            self.settings["webapp"] = False

    def callback_open_website(self, sender, app_data, user_data):
        webbrowser.open(user_data)

    def getLatestVersion(self):
        headers = {
            "Accept": "application/json",
        }
        try:
            response = requests.get(
                "https://api.github.com/repos/motojinc25/WeDX/releases/latest",
                headers=headers,
            )
            if response.status_code == 200:
                data = response.json()
                self.latestVersion = data["name"].replace("WeDX", "").strip()
        except:
            self.latestVersion = None
