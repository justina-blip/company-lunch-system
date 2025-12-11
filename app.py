import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import datetime
import time
import json

# --- 1. 設定與 API Key ---
st.set_page_config(page_title="SmartCanteen White", layout="wide", initial_sidebar_state="expanded")

# 讀取 API Key
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    pass 

# --- 2. CSS 全白線框風格 (White Wireframe) ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* ============================
           1. 全域基礎與字體
           ============================ */
        html, body, .stApp, button, input, select, textarea {
            font-family: "Microsoft JhengHei", "微軟正黑體", sans-serif !important;
        }
        
        /* 全站背景純白 */
        .stApp {
            background-color: #FFFFFF !important;
        }
        
        /* 所有文字強制全黑 */
        h1, h2, h3, h4, h5, h6, p, label, span, div, li, small, strong {
            color: #000000 !important;
        }

        /* ============================
           2. 按鈕專區 (白底黑字黑框)
           ============================ */
        
        /* 鎖定所有按鈕 */
        button, 
        [data-testid="baseButton-secondary"],
        [data-testid="baseButton-primary"],
        [data-testid="stFormSubmitButton"] button,
        [data-testid="stFileUploader"] button {
            background-color: #FFFFFF !important; /* 白底 */
            color: #000000 !important; /* 黑字 */
            border: 2px solid #000000 !important; /* 黑框 */
            border-radius: 0px !important; /* 直角 */
            font-weight: 800 !important;
            box-shadow: none !important;
        }

        /* 按鈕滑鼠懸停 (Hover) -> 變黑底白字 */
        button:hover,
        [data-testid="baseButton-secondary"]:hover,
        [data-testid="baseButton-primary"]:hover,
        [data-testid="stFormSubmitButton"] button:hover,
        [data-testid="stFileUploader"] button:hover {
            background-color: #000000 !important; /* 變黑底 */
            color: #FFFFFF !important; /* 變白字 */
        }
        
        /* 修正上傳按鈕內部文字 hover 也要變白 */
        [data-testid="stFileUploader"] button:hover span {
            color: #FFFFFF !important;
        }

        /* ============================
           3. 側邊欄 (全白風格) 
           ============================ */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important; /* 改為白底 */
            border-right: 2px solid #000000; /* 加右側黑框線 */
        }
        /* 側邊欄內的所有文字強制變黑 */
        [data-testid="stSidebar"] * {
            color: #000000 !important;
        }
        
        /* Logo 改為黑字黑框 */
        .sidebar-logo {
            font-size: 24px; font-weight: 800; margin-bottom: 20px; 
            color: #000000 !important;
            border: 2px solid #000000;
            padding: 10px;
            text-align: center;
        }

        /* ============================
           4. 上傳視窗專區 (File Uploader)
           ============================ */
        
        /* 拖放區域背景白 */
        [data-testid="stFileUploader"] section {
            background-color: #FFFFFF !important;
            border: 2px dashed #000000 !important;
        }
        /* 提示文字黑 */
        [data-testid="stFileUploader"] section span, 
        [data-testid="stFileUploader"] section small {
            color: #000000 !important;
        }

        /* ============================
           5. 輸入框與其他元件
           ============================ */
        /* 輸入框：白底黑字黑框 */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            caret-color: #000000 !important;
            border: 2px solid #000000 !important;
            border-radius: 0px !important;
        }

        /* 下拉選單浮動視窗 */
        div[data-baseweb="popover"] li, div[data-baseweb="popover"] div {
            color: #000000 !important;
            background-color: #FFFFFF !important;
        }
        
        /* 警示框文字強制黑 */
        div[data-baseweb="notification"] * {
            color: #000000 !important;
        }
        
        /* 表格文字強制黑 */
        div[data-testid="stDataFrame"] * {
            color: #000000 !important;
        }

        /* 價格標籤 (改為白底黑字黑框) */
        .price-tag {
            background-color: #FFFFFF; 
            color: #000000 !important;
            border: 2px solid #000000;
            padding: 6px 16px; 
            border-radius: 50px;
            font-weight: 800; font-size: 20px;
            display: inline-block; margin-bottom: 12px;
        }
        .price-tag span { color: #000000 !important; }

        /* 卡片設計 */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border: 2px solid #000000;
            border-radius: 0px;
            padding: 20px;
            box-shadow: 4px 4px 0px #000000;
        }
        
        /* Header 白底 */
        header[data-testid="stHeader"] {
            background-color: #FFFFFF !important;
        }
        button[kind="header"] {
            color: #000000 !important;
        }

    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

# --- 3. SQLite 資料庫設定 ---
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
st.sidebar.markdown('<div class="sidebar-logo">NX ENERGY</div>', unsafe_allow_html=True)
st.sidebar.caption("v12.0 White Flash")
st.sidebar.markdown("---")
page = st.sidebar.radio("MENU", ["👤 員工點餐", "🤖 菜單管理 (AI)", "💰 儲值作業", "📊 每日匯總", "⚙️ 人員管理"], label_visibility="collapsed")

# --- 5. 頁面邏輯 ---

# === 頁面 1: 員工點餐 ===
if page == "👤 員工點餐":
    st.title("員工點餐")
    
    with get_db_connection() as conn:
        users = pd.read_sql("SELECT user_id, name, current_balance FROM Users", conn)
    
    if users.empty:
        st.warning("⚠️ 無員工資料，請先至「人員管理」新增。")
    else:
        c1, c2 = st.columns([2, 1])
        with c1:
            user_names = users['name'].tolist()
            selected_user_name = st.selectbox("選擇身份", user_names)
        
        current_user = users[users['name'] == selected_user_name].iloc[0]
        user_id = int(current_user['user_id'])
        balance = int(current_user['current_balance'])

        with c2:
            st.metric("目前餘額", f"${balance}")
        
        st.divider()

        with st.expander("🧾 查看本月消費紀錄"):
            with get_db_connection() as conn:
                first_day = datetime.date.today().replace(day=1).strftime('%Y-%m-%d')
                history_df = pd.read_sql("""
                    SELECT strftime('%m/%d', timestamp) as 日期, dish_name as 品項, amount as 金額, note as 備註 
                    FROM Transactions 
                    WHERE user_id = ? AND timestamp >= ? 
                    ORDER BY timestamp DESC
                """, conn, params=(user_id, first_day))
            st.dataframe(history_df, use_container_width=True, hide_index=True)

        st.subheader("今日菜單")
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        with get_db_connection() as conn:
            menu_df = pd.read_sql("SELECT * FROM Menu WHERE date = ?", conn, params=(today,))
            
        if menu_df.empty:
            st.info("🕒 今日菜單尚未發布")
        else:
            @st.dialog("確認訂單")
            def confirm_order(dish, price, note, uid):
                st.markdown(f"### {dish}")
                st.markdown(f"**價格: ${price}**")
                st.caption(f"備註: {note if note else '無'}")
                st.divider()
                st.markdown("**確認後將直接扣款**")
                
                if st.button("✅ 確認下單", use_container_width=True):
                    try:
                        with get_db_connection() as conn:
                            cur = conn.cursor()
                            cur.execute("INSERT INTO Transactions (user_id, type, amount, dish_name, note) VALUES (?, 'ORDER', ?, ?, ?)", (uid, -price, dish, note))
                            cur.execute("UPDATE Users SET current_balance = current_balance - ? WHERE user_id = ?", (price, uid))
                            conn.commit()
                        st.success("訂購成功！")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"錯誤: {e}")

            cols = st.columns(3)
            for idx, row in menu_df.iterrows():
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.markdown(f"<div style='text-align:center'><span class='price-tag'>${row['price']}</span></div>", unsafe_allow_html=True)
                        st.markdown(f"<h4 style='text-align:center; color:#000000; margin:0;'>{row['dish_name']}</h4>", unsafe_allow_html=True)
                        st.markdown("<div style='margin-bottom:15px'></div>", unsafe_allow_html=True)
                        
                        note = st.text_input("備註", placeholder="例: 飯少", key=f"n_{row['id']}")
                        
                        if st.button("選購", key=f"b_{row['id']}"):
                            confirm_order(row['dish_name'], row['price'], note, user_id)

# === 頁面 2: 菜單管理 (AI) ===
elif page == "🤖 菜單管理 (AI)":
    st.header("智能菜單辨識")
    uploaded_file = st.file_uploader("上傳菜單圖片 (JPG/PNG)", type=["jpg", "png", "jpeg"])
    
    if 'menu_df' not in st.session_state:
        st.session_state['menu_df'] = None

    if uploaded_file:
        if st.session_state['menu_df'] is None:
            if st.button("開始 AI 辨識"):
                if "GEMINI_API_KEY" not in st.secrets:
                     st.error("⚠️ 請先設定 API Key")
                else:
                    with st.spinner("AI 分析中..."):
                        try:
                            img_parts = [{"mime_type": uploaded_file.type, "data": uploaded_file.getvalue()}]
                            
                            # [關鍵修正] 改回 flash，並依賴 requirements.txt 的升級
                            model = genai.GenerativeModel('gemini-1.5-flash')
                            
                            response = model.generate_content(["Extract menu items to JSON list [{'dish_name':'', 'price':0}]. No markdown.", img_parts[0]])
                            
                            try:
                                text = response.text.strip().replace("```json", "").replace("```", "")
                                data = json.loads(text)
                                st.session_state['menu_df'] = pd.DataFrame(data)
                            except json.JSONDecodeError:
                                st.error("AI 回傳格式錯誤，請重試或檢查圖片。")
                                
                        except Exception as e:
                            st.error(f"AI 連線失敗: {e}")

        if st.session_state['menu_df'] is not None:
            st.success("辨識成功")
            edited_df = st.data_editor(st.session_state['menu_df'], num_rows="dynamic", use_container_width=True)
            
            if st.button("🚀 發布今日菜單"):
                today = datetime.date.today().strftime("%Y-%m-%d")
                with get_db_connection() as conn:
                    conn.execute("DELETE FROM Menu WHERE date = ?", (today,))
                    for _, row in edited_df.iterrows():
                        conn.execute("INSERT INTO Menu (date, dish_name, price) VALUES (?, ?, ?)", (today, row['dish_name'], row['price']))
                    conn.commit()
                st.success("菜單已發布！")
                st.session_state['menu_df'] = None
                time.sleep(1)
                st.rerun()

# === 頁面 3: 儲值作業 ===
elif page == "💰 儲值作業":
    st.header("員工儲值")
    
    with get_db_connection() as conn:
        users = pd.read_sql("SELECT name FROM Users", conn)
    
    if users.empty:
        st.warning("無員工資料")
    else:
        with st.container(border=True):
            st.markdown("#### 新增儲值")
            with st.form("topup_form"):
                c1, c2 = st.columns(2)
                name = c1.selectbox("員工", users['name'].tolist())
                amount = c2.number_input("金額", step=100, value=1000)
                
                if st.form_submit_button("確認儲值"):
                    with get_db_connection() as conn:
                        uid = conn.execute("SELECT user_id FROM Users WHERE name=?", (name,)).fetchone()[0]
                        conn.execute("INSERT INTO Transactions (user_id, type, amount, note) VALUES (?, 'TOPUP', ?, '管理員儲值')", (uid, amount))
                        conn.execute("UPDATE Users SET current_balance = current_balance + ? WHERE user_id = ?", (amount, uid))
                        conn.commit()
                    st.success(f"已儲值 ${amount}")
                    time.sleep(1)
                    st.rerun()

# === 頁面 4: 每日匯總 ===
elif page == "📊 每日匯總":
    st.header("營運儀表板")
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    with get_db_connection() as conn:
        total_bal = conn.execute("SELECT SUM(current_balance) FROM Users").fetchone()[0] or 0
        today_income = conn.execute("SELECT SUM(amount) FROM Transactions WHERE type='TOPUP' AND date(timestamp)=?", (today,)).fetchone()[0] or 0
        today_sales = abs(conn.execute("SELECT SUM(amount) FROM Transactions WHERE type='ORDER' AND date(timestamp)=?", (today,)).fetchone()[0] or 0)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("總發行儲值金", f"${total_bal}")
        m2.metric("今日營收", f"${today_sales}")
        m3.metric("今日儲值", f"${today_income}")
        
        st.subheader("今日交易明細")
        df = pd.read_sql("""SELECT time(timestamp) as 時間, u.name as 員工, type as 類型, dish_name as 品項, amount as 金額 
                            FROM Transactions t JOIN Users u ON t.user_id=u.user_id WHERE date(timestamp)=? ORDER BY timestamp DESC""", conn, params=(today,))
        st.dataframe(df, use_container_width=True)

# === 頁面 5: 人員管理 ===
elif page == "⚙️ 人員管理":
    st.header("人員管理")
    
    # [維持] 直接展開表單
    st.subheader("➕ 新增員工")
    with st.form("add_user"):
        n = st.text_input("姓名")
        b = st.number_input("初始金", value=0)
        
        if st.form_submit_button("新增"):
            try:
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute("INSERT INTO Users (name, current_balance) VALUES (?, ?)", (n, b))
                    uid = cur.lastrowid
                    cur.execute("INSERT INTO Transactions (user_id, type, amount, note) VALUES (?, 'INIT', ?, '開戶')", (uid, b))
                    conn.commit()
                st.success("新增成功")
                time.sleep(1)
                st.rerun()
            except:
                st.error("姓名重複")

    st.markdown("---")
    
    with get_db_connection() as conn:
        users = pd.read_sql("SELECT * FROM Users", conn)
    st.dataframe(users, use_container_width=True)
    
    # [維持] 垃圾桶圖示
    st.subheader("🗑️ 刪除員工")
    with st.form("del_user"):
        to_del = st.selectbox("選擇刪除對象", users['name'].tolist() if not users.empty else [])
        
        if st.form_submit_button("確認刪除"):
            with get_db_connection() as conn:
                conn.execute("DELETE FROM Users WHERE name=?", (to_del,))
                conn.commit()
            st.warning(f"已刪除 {to_del}")
            time.sleep(1)
            st.rerun()
