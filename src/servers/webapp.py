import json
import os

import streamlit as st
import streamlit.components.v1 as stc

# Set WeDX settings
settings = None
current_path = os.path.dirname(os.path.abspath(__file__))
with open(os.path.abspath(os.path.join(current_path, "../.wedx/settings.json"))) as fp:
    settings = json.load(fp)

st.set_page_config(layout="wide")

st.title("WeDX Live Streaming")

stc.html(
    "<img width="
    + str(settings["video_streaming_width"])
    + " height="
    + str(settings["video_streaming_height"])
    + ' src="http://localhost:'
    + str(settings["webapi_port"])
    + '/video_feed">',
    width=settings["video_streaming_width"],
    height=settings["video_streaming_height"],
)
