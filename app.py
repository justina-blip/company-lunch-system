import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import datetime
import time
import json

# --- 1. 設定與 API Key ---
# 為了方便您測試，這裡先寫死。正式上線建議改用 st.secrets
GEMINI_API_KEY = "AIzaSyBXOxRg0KY8RsWoUrj25mZpLDgtk21luW4"

st.set_page_config(page_title="SmartCanteen", layout="wide", initial_sidebar_state="expanded")

# 設定 Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"API Key 設定失敗: {e}")

# --- 2. CSS 極致美化 (還原 SmartCanteen React 風格) ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* 引入現代字體 Inter */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', "Microsoft JhengHei", sans-serif;
            background-color: #F3F4F6; /* 整體淺灰背景 */
        }
        
        .stApp {
            background-color: #F3F4F6;
        }

        /* --- 側邊欄優化 --- */
        [data-testid="stSidebar"] {
            background-color: #0F172A; /* 深海軍藍 */
            border-right: 1px solid #1E293B;
        }
        [data-testid="stSidebar"] * {
            color: #94A3B8 !important; /* 淺灰文字 */
        }
        /* Logo 區域 */
        .sidebar-logo {
            color: #FFFFFF !important;
            font-size: 26px;
            font-weight: 800;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            letter-spacing: -0.5px;
        }
        .sidebar-logo span {
            color: #10B981 !important; /* 翠綠色 Logo */
            margin-right: 10px;
        }
        
        /* 側邊欄選單項目 */
        .stRadio > div[role="radiogroup"] > label {
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 6px;
            transition: all 0.2s;
            border: 1px solid transparent;
        }
        .stRadio > div[role="radiogroup"] > label:hover {
            background-color: #1E293B !important;
            color: #FFFFFF !important;
            cursor: pointer;
        }
        /* 選中狀態 */
        .stRadio > div[role="radiogroup"] > label[data-testid="stMarkdownContainer"] > p {
             font-weight: 600;
             font-size: 15px;
        }

        /* --- 主畫面元件優化 --- */
        
        /* 頂部資訊列 (Top Bar) */
        div[data-testid="stMetricValue"] {
            font-size: 36px !important;
            font-weight: 800 !important;
            color: #10B981 !important; /* 翠綠色數字 */
            text-shadow: 0 2px 4px rgba(16, 185, 129, 0.1);
        }
        div[data-testid="stMetricLabel"] {
            color: #6B7280 !important;
            font-weight: 600;
            font-size: 14px !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* 卡片式設計 (Cards) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        /* Hover 效果 */
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            border-color: #10B981;
        }

        /* 價格標籤 */
        .price-tag {
            background-color: #ECFDF5;
            color: #059669;
            padding: 6px 16px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 20px;
            display: inline-block;
            margin-bottom: 16px;
        }

        /* 菜名標題 */
        .dish-title {
            font-size: 18px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 8px;
            text-align: center;
        }

        /* 按鈕優化 */
        .stButton > button {
            background-color: #0F172A !important; /* 深藍底 */
            color: white !important;
            border-radius: 10px !important;
            border: none !important;
            padding: 12px 24px !important;
            font-weight: 600 !important;
            width: 100%;
            transition: background-color 0.2s;
        }
        .stButton > button:hover {
            background-color: #1E293B !important; /* hover 變亮一點 */
        }
        
        /* 輸入框優化 */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 8px !important;
            border: 1px solid #D1D5DB !important;
            background-color: #F9FAFB !important;
            color: #1F2937 !important;
        }
        .stTextInput input:focus {
            border-color: #10B981 !important;
            box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2) !important;
        }
        
        /* 隱藏預設 Header */
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 3. 資料庫連線 ---
DB_NAME = "ordering_system.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            current_balance INTEGER DEFAULT 0
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            dish_name TEXT NOT NULL,
            price INTEGER NOT NULL
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            dish_name TEXT,
            note TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES Users (user_id)
        )''')
        conn.commit()

init_db()

# --- 4. 側邊欄導航 ---
st.sidebar.markdown('<div class="sidebar-logo"><span>⚡</span> SmartCanteen</div>', unsafe_allow_html=True)
st.sidebar.markdown("内部訂餐系統 v2.0")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "MAIN MENU",
    ["👤 員工點餐", "🤖 菜單管理 (AI)", "💰 儲值作業", "📊 每日匯總", "⚙️ 人員管理"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.caption("Designed for Nexcellent Energy")

# --- 5. 頁面邏輯 ---

# === 頁面 1: 員工點餐 ===
if page == "👤 員工點餐":
    
    with get_db_connection() as conn:
        users = pd.read_sql("SELECT user_id, name, current_balance FROM Users", conn)
    
    if users.empty:
        st.warning("⚠️ 暫無員工資料，請至人員管理新增。")
    else:
        # 頂部 Dashboard 佈局
        st.markdown("### 👋 歡迎回來")
        
        col_header_1, col_header_2 = st.columns([2, 1])
        with col_header_1:
            st.markdown("請選擇您的身份以開始點餐")
            user_names = users['name'].tolist()
            selected_user_name = st.selectbox("選擇身份", user_names, label_visibility="collapsed")
        
        current_user = users[users['name'] == selected_user_name].iloc[0]
        user_id = int(current_user['user_id'])
        balance = int(current_user['current_balance'])

        with col_header_2:
            st.metric("目前可用餘額", f"${balance}")

        st.markdown("---")

        # 歷史紀錄
        with st.expander("🧾 查看本月消費紀錄", expanded=False):
            with get_db_connection() as conn:
                first_day = datetime.date.today().replace(day=1).strftime('%Y-%m-%d')
                query = """SELECT strftime('%m/%d', timestamp) as 日期, dish_name as 品項, amount as 金額, note as 備註 
                           FROM Transactions WHERE user_id = ? AND timestamp >= ? ORDER BY timestamp DESC"""
                history_df = pd.read_sql(query, conn, params=(user_id, first_day))
            st.dataframe(history_df, use_container_width=True, hide_index=True)

        st.markdown("### 🍱 今日菜單")
        
        today = datetime.date.today().strftime("%Y-%m-%d")
        with get_db_connection() as conn:
            menu_df = pd.read_sql("SELECT * FROM Menu WHERE date = ?", conn, params=(today,))
            
        if menu_df.empty:
            st.info("🕒 今日菜單尚未發布，請稍後再試。")
        else:
            # 二次確認視窗 (Dialog)
            @st.dialog("確認訂單詳情")
            def confirm_order(dish_name, price, note, u_id):
                st.markdown(f"### {dish_name}")
                st.markdown(f"價格：<span style='color:#10B981;font-weight:bold;font-size:24px'>${price}</span>", unsafe_allow_html=True)
                st.markdown(f"備註：{note if note else '無'}")
                st.divider()
                st.caption("⚠️ 點擊確認後將直接從餘額扣款")
                
                c1, c2 = st.columns(2)
                if c1.button("✅ 確認下單", use_container_width=True):
                    try:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO Transactions (user_id, type, amount, dish_name, note) VALUES (?, 'ORDER', ?, ?, ?)", (u_id, -price, dish_name, note))
                            cursor.execute("UPDATE Users SET current_balance = current_balance - ? WHERE user_id = ?", (price, u_id))
                            conn.commit()
                        st.toast("✅ 訂購成功！已扣款", icon="🎉")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"錯誤: {e}")
                
                if c2.button("❌ 取消", use_container_width=True):
                    st.rerun()

            # 卡片式排列 (Grid Layout)
            cols = st.columns(3) # 3欄佈局，卡片較大
            for idx, row in menu_df.iterrows():
                with cols[idx % 3]:
                    with st.container(border=True):
                        # 綠色價格標籤
                        st.markdown(f"""
                        <div style="text-align: center;">
                            <span class="price-tag">${row['price']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 菜名
                        st.markdown(f"<div class='dish-title'>{row['dish_name']}</div>", unsafe_allow_html=True)
                        
                        # 備註輸入
                        note = st.text_input("備註", placeholder="例: 飯少/不蔥", key=f"note_{row['id']}")
                        
                        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                        
                        # 下單按鈕
                        if st.button("🛒 下單購買", key=f"btn_{row['id']}"):
                            confirm_order(row['dish_name'], row['price'], note, user_id)

# === 頁面 2: 菜單管理 (AI) ===
elif page == "🤖 菜單管理 (AI)":
    st.markdown("## 🤖 智能菜單辨識")
    st.info("請上傳菜單圖片，Gemini AI 將自動解析內容。")
    
    uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"])
    
    if 'menu_df' not in st.session_state:
        st.session_state['menu_df'] = None

    if uploaded_file:
        if st.session_state['menu_df'] is None:
            with st.spinner("AI 正在分析圖片中..."):
                try:
                    img_data = [{"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}]
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    prompt = "Analyze menu image. Return JSON list: [{'dish_name': 'name', 'price': 100}]. No markdown."
                    response = model.generate_content([prompt, img_data[0]])
                    text = response.text.strip().replace("```json", "").replace("```", "")
                    data = json.loads(text)
                    st.session_state['menu_df'] = pd.DataFrame(data)
                except Exception as e:
                    st.error(f"辨識失敗: {e}")
        
        if st.session_state['menu_df'] is not None:
            st.success("辨識成功！請確認表格內容是否正確。")
            edited_df = st.data_editor(st.session_state['menu_df'], num_rows="dynamic", use_container_width=True)
            
            st.warning("⚠️ 按下發布後，將會覆蓋今日原有的菜單。")
            if st.button("🚀 發布今日菜單", type="primary"):
                today = datetime.date.today().strftime("%Y-%m-%d")
                with get_db_connection() as conn:
                    conn.execute("DELETE FROM Menu WHERE date = ?", (today,))
                    for _, row in edited_df.iterrows():
                        conn.execute("INSERT INTO Menu (date, dish_name, price) VALUES (?, ?, ?)", (today, row['dish_name'], row['price']))
                    conn.commit()
                st.toast("菜單已成功更新！", icon="✅")
                st.session_state['menu_df'] = None
                time.sleep(1)
                st.rerun()

# === 頁面 3: 儲
