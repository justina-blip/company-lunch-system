import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import datetime
import time
import json
import re # 新增：用於強力清洗資料

# --- 1. 設定與 API Key ---
st.set_page_config(page_title="SmartCanteen White", layout="wide", initial_sidebar_state="expanded")

# 讀取 API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    pass 

# --- 2. CSS 強制全白線框風格 (White Wireframe) ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* 強制覆蓋系統變數 */
        :root {
            --primary-color: #000000;
            --background-color: #FFFFFF;
            --secondary-background-color: #FFFFFF;
            --text-color: #000000;
            --font: "Microsoft JhengHei", sans-serif;
        }

        /* 1. 全域設定 */
        html, body, .stApp {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            font-family: "Microsoft JhengHei", "微軟正黑體", sans-serif !important;
        }
        
        /* 強制所有文字全黑 */
        h1, h2, h3, h4, h5, h6, p, label, span, div, li, small, strong, td, th {
            color: #000000 !important;
        }

        /* ============================
           2. 按鈕專區 (白底、黑字、黑框)
           ============================ */
        
        button, 
        [data-testid="baseButton-secondary"],
        [data-testid="baseButton-primary"],
        [data-testid="stFormSubmitButton"] button,
        [data-testid="stFileUploader"] button {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #000000 !important;
            border-radius: 0px !important;
            font-weight: 800 !important;
            box-shadow: none !important;
        }

        /* Hover 反轉 */
        button:hover,
        [data-testid="baseButton-secondary"]:hover,
        [data-testid="baseButton-primary"]:hover,
        [data-testid="stFormSubmitButton"] button:hover,
        [data-testid="stFileUploader"] button:hover {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            border: 2px solid #000000 !important;
        }
        
        [data-testid="stFileUploader"] button:hover span {
            color: #FFFFFF !important;
        }

        /* ============================
           3. 上傳視窗專區
           ============================ */
        [data-testid="stFileUploader"] section {
            background-color: #FFFFFF !important;
            border: 2px dashed #000000 !important;
        }
        [data-testid="stFileUploader"] section span, 
        [data-testid="stFileUploader"] section small,
        [data-testid="stFileUploader"] section div {
            color: #000000 !important;
        }

        /* ============================
           4. 側邊欄 (Sidebar) 
           ============================ */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 2px solid #000000;
        }
        [data-testid="stSidebar"] * {
            color: #000000 !important;
        }
        
        /* Logo */
        .sidebar-logo {
            font-size: 24px; font-weight: 800; margin-bottom: 20px; 
            color: #000000 !important;
            border: 2px solid #000000;
            padding: 10px;
            text-align: center;
        }

        /* ============================
           5. 其他元件
           ============================ */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            caret-color: #000000 !important;
            border: 2px solid #000000 !important;
            border-radius: 0px !important;
        }

        div[data-baseweb="popover"] li, div[data-baseweb="popover"] div {
            background-color: #FFFFFF !important;
            color: #000000 !important;
        }

        div[data-testid="stDataFrame"] { background-color: #FFFFFF !important; }
        div[data-testid="stDataFrame"] div, div
