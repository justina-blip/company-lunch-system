import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import datetime
import time
import json

# --- 1. 設定與 API Key ---
st.set_page_config(page_title="SmartCanteen B&W", layout="wide", initial_sidebar_state="expanded")

# 讀取 API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.warning("⚠️ 未檢測到 API Key，請確認 Streamlit Secrets 設定。")

# --- 2. CSS 極致黑白化 (Monochrome Style) ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* 1. 全站強制灰階 (Grayscale) - 這是讓 Emoji 變黑白的關鍵 */
        html {
            filter: grayscale(100%);
        }

        /* 2. 字體設定：微軟正黑體 */
        html, body, .stApp, [class*="css"], button, input, select, textarea {
            font-family: "Microsoft JhengHei", "微軟正黑體", sans-serif !important;
        }

        /* 3. 背景與文字顏色 */
        .stApp {
            background-color: #FFFFFF !important; /* 純白背景 */
            color: #000000 !important; /* 純黑文字 */
        }

        /* 4. 側邊欄：純黑 */
        [data-testid="stSidebar"] {
            background-color: #000000 !important;
            border-right: 1px solid #333;
        }
        [data-testid="stSidebar"] * {
            color: #FFFFFF !important; /* 側邊欄文字全白 */
        }
        
        /* Logo */
        .sidebar-logo {
            font-size: 24px; font-weight: 800; margin-bottom: 20px; 
            color: #FFFFFF !important;
            border: 2px solid #FFFFFF;
            padding: 10px;
            text-align: center;
            border-radius: 4px;
        }

        /* 5. 輸入框：高對比黑白 */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 2px solid #000000 !important; /* 純黑邊框 */
            border-radius: 0px !important; /* 直角設計更像雜誌 */
            font-weight: 600;
        }
        
        /* 下拉選單選項 */
        ul[data-testid="stSelectboxVirtualDropdown"] { background-color: #FFFFFF !important; }
        li[role="option"] { color: #000000 !important; }

        /* 6. 卡片式設計 (雜誌風格) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border: 2px solid #000000; /* 純黑粗框 */
            border-radius: 0px; /* 直角 */
            padding: 20px;
            box-shadow: 4px 4px 0px #000000; /* 復古黑影效果 */
            transition: all 0.2s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            transform: translate(-2px, -2px);
            box-shadow: 6px 6px 0px #000000;
        }

        /* 7. 價格標籤 (黑底白字膠囊) */
        .price-tag {
            background-color: #000000; 
            color: #FFFFFF;
            padding: 6px 16px; 
            border-radius: 50px;
            font-weight: 800; font-size: 20px;
            display: inline-block; margin-bottom: 12px;
        }

        /* 8. 按鈕 (純黑實心) */
        .stButton > button {
            background-color: #000000 !important;
            color: #FFFFFF !important;
            border-radius: 0px !important; /* 直角 */
            border: 2px solid #000000 !important;
            font-weight: 800 !important;
            padding: 10px 20px !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .stButton > button:hover {
            background-color: #FFFFFF !important; /* Hover 時變白底黑字 */
            color: #000000 !important;
        }

        /* 9. 指標數字 (Metric) */
        div[data-testid="stMetricValue"] {
            color: #000000 !important;
            font-weight: 900 !important;
        }

        /* 隱藏 Header */
        header {visibility: hidden;}
        
        /* 標題加粗 */
        h1, h2, h3 { font-weight: 900 !important; letter-spacing: -1px; }
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()
