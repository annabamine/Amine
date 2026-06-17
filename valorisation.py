import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import feedparser
import base64
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import urllib.request
import re

# 1. Toujours en premier
st.set_page_config(page_title="Value Quest", layout="centered")

# 2. Barre de titre (Logique Logo + HTML)
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

logo_base64 = get_base64_image("logo.png")
if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="nav-logo">'
else
