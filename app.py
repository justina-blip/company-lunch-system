import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import datetime
import time
import json

# --- 1. 設定與 API Key (後端寫死) ---
# 注意：為了方便測試，我們先寫死。正式上線建議改用 st.secrets
GEMINI_API_KEY = "AIzaSyBXOxRg0KY8RsWoUrj25mZpLDgtk21luW4"

st.set_page_config(page_title="SmartCanteen 內部點餐系統", layout="wide", initial_sidebar_state="expanded")

# 設定 Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"API Key 設定失敗: {e}")

# --- 2. CSS 極致美化 (還原 SmartCanteen 風格) ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* 全域設定 */
        .stApp {
            background-color: #F8F9FA; /* 淺灰背景 */
            font-family: "Microsoft JhengHei", sans-serif;
        }
        
        /* 側邊欄樣式 */
        [data-testid="stSidebar"] {
            background-color: #0E1117; /* 深黑背景 */
        }
        [data-testid="stSidebar"] * {
            color: #E0E0E0 !important;
        }
        .css-17lntkn { /* 側邊欄標題 */
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            color: #4DB6AC !important; /* 品牌色 */
            margin-bottom: 20px;
        }

        /* 頂部資訊卡 (Top Bar) */
        .top-bar {
            background-color: white;
            padding: 15px 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        /* 菜單卡片設計 (Card UI) */
        div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
            gap: 1rem;
        }
        
        .dish-card-container {
            background-color: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            transition: transform 0.2s;
            height: 100%;
            border: 1px solid #eee;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .dish-card-container:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
        }
        
        /* 價格標籤 */
        .price-tag {
            font-size: 1.8rem;
            font-weight: 800;
            color: #2E2E2E;
            margin-bottom: 5px;
        }
        .currency {
            font-size: 1rem;
            color: #888;
            font-weight: normal;
        }
        
        /* 菜名 */
        .dish-name {
            font-size: 1.1rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 15px;
            line-height: 1.4;
        }

        /* 輸入框美化 */
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div {
            border-radius: 8px !important;
            border: 1px solid #E0E0E0;
            background-color: white !important;
            color: #333 !important;
        }
        
        /* 按鈕美化 */
        .stButton > button {
            width: 100%;
            border-radius: 8px !important;
            background-color: #0E1117 !important; /* 黑底 */
            color: white !important;
            border: none;
            font-weight: 600;
            padding: 0.5rem 1rem;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            background-color: #333 !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }

        /* Metric 指標卡優化 */
        div[data-testid="metric-container"] {
            background-color: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
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
st.sidebar.markdown('<div class="css-17lntkn">⚡ SmartCanteen</div>', unsafe_allow_html=True)
st.sidebar.markdown("内部訂餐系統 v2.0")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "MAIN MENU",
    ["👤 員工點餐", "🤖 菜單管理 (AI)", "💰 儲值作業", "📊 每日匯總", "⚙️ 人員管理"]
)

# --- 5. 頁面邏輯 ---

# === 頁面 1: 員工點餐 (Dashboard 風格) ===
if page == "👤 員工點餐":
    
    # 頂部：使用者選擇與餘額
    with get_db_connection() as conn:
        users = pd.read_sql("SELECT user_id, name, current_balance FROM Users", conn)
    
    if users.empty:
        st.warning("⚠️ 系統無員工資料，請至人員管理新增。")
    else:
        # 模擬 Top Bar
        col_u1, col_u2 = st.columns([3, 1])
        with col_u1:
            st.markdown("### 👋 歡迎回來，請點餐")
            user_names = users['name'].tolist()
            selected_user_name = st.selectbox("選擇您的身份", user_names, label_visibility="collapsed")
        
        # 取得資料
        current_user = users[users['name'] == selected_user_name].iloc[0]
        user_id = int(current_user['user_id'])
        balance = int(current_user['current_balance'])

        with col_u2:
            st.metric("目前餘額", f"${balance}")

        st.markdown("---")

        # 歷史紀錄 (縮合式)
        with st.expander("🕒 查看本月消費紀錄", expanded=False):
            with get_db_connection() as conn:
                first_day = datetime.date.today().replace(day=1).strftime('%Y-%m-%d')
                query = """SELECT strftime('%m/%d %H:%M', timestamp) as 時間, dish_name as 品項, amount as 金額, note as 備註 
                           FROM Transactions WHERE user_id = ? AND timestamp >= ? ORDER BY timestamp DESC"""
                history_df = pd.read_sql(query, conn, params=(user_id, first_day))
            st.dataframe(history_df, use_container_width=True, hide_index=True)

        st.markdown("### 🍱 今日精選菜單")
        
        today = datetime.date.today().strftime("%Y-%m-%d")
        with get_db_connection() as conn:
            menu_df = pd.read_sql("SELECT * FROM Menu WHERE date = ?", conn, params=(today,))
            
        if menu_df.empty:
            st.info("🕒 今日菜單尚未發布，請稍後再試。")
        else:
            # 確認視窗函數
            @st.dialog("確認訂單")
            def confirm_order(dish_name, price, note, u_id):
                st.markdown(f"**餐點：** {dish_name}")
                st.markdown(f"**價格：** <span style='color:red;font-weight:bold'>${price}</span>", unsafe_allow_html=True)
                st.markdown(f"**備註：** {note if note else '無'}")
                st.warning("點擊確認後將直接扣款。")
                
                col1, col2 = st.columns(2)
                if col1.button("✅ 確認下單", use_container_width=True):
                    try:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO Transactions (user_id, type, amount, dish_name, note) VALUES (?, 'ORDER', ?, ?, ?)", (u_id, -price, dish_name, note))
                            cursor.execute("UPDATE Users SET current_balance = current_balance - ? WHERE user_id = ?", (price, u_id))
                            conn.commit()
                        st.toast("✅ 訂購成功！已從餘額扣款", icon="🎉")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"錯誤: {e}")
                
                if col2.button("❌ 取消", use_container_width=True):
                    st.rerun()

            # 卡片式排列 (Grid Layout)
            cols = st.columns(3) # 一排 3 個
            for idx, row in menu_df.iterrows():
                with cols[idx % 3]:
                    # 使用 container 模擬卡片
                    with st.container(border=True):
                        # 顯示價格與菜名
                        st.markdown(f"""
                        <div style="text-align: center; margin-bottom: 10px;">
                            <div class="price-tag"><span class="currency">$</span>{row['price']}</div>
                            <div class="dish-name">{row['dish_name']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 備註與按鈕
                        note = st.text_input("備註", placeholder="例: 飯少/不蔥", key=f"note_{row['id']}")
                        if st.button("🛒 下單購買", key=f"btn_{row['id']}"):
                            confirm_order(row['dish_name'], row['price'], note, user_id)

# === 頁面 2: 菜單管理 (AI) ===
elif page == "🤖 菜單管理 (AI)":
    st.title("🤖 智能菜單辨識")
    st.info("上傳菜單圖片，AI 將自動辨識菜名與價格。")
    
    uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg"])
    
    if 'menu_df' not in st.session_state:
        st.session_state['menu_df'] = None

    if uploaded_file:
        if st.session_state['menu_df'] is None:
            with st.spinner("✨ AI 正在分析菜單中..."):
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
            st.success("辨識完成！請確認並發布。")
            edited_df = st.data_editor(st.session_state['menu_df'], num_rows="dynamic", use_container_width=True)
            
            if st.button("🚀 確認發布今日菜單", type="primary"):
                today = datetime.date.today().strftime("%Y-%m-%d")
                with get_db_connection() as conn:
                    conn.execute("DELETE FROM Menu WHERE date = ?", (today,))
                    for _, row in edited_df.iterrows():
                        conn.execute("INSERT INTO Menu (date, dish_name, price) VALUES (?, ?, ?)", (today, row['dish_name'], row['price']))
                    conn.commit()
                st.toast("菜單已更新！", icon="✅")
                st.session_state['menu_df'] = None
                time.sleep(1)
                st.rerun()

# === 頁面 3: 儲值作業 ===
elif page == "💰 儲值作業":
    st.title("💰 員工儲值")
    
    with get_db_connection() as conn:
        users = pd.read_sql("SELECT name, current_balance FROM Users", conn)
    
    with st.container(border=True):
        with st.form("topup"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.selectbox("選擇員工", users['name'].tolist())
            with c2:
                amount = st.number_input("儲值金額 ($)", min_value=0, step=100, value=1000)
            
            if st.form_submit_button("確認儲值", type="primary"):
                with get_db_connection() as conn:
                    uid = conn.execute("SELECT user_id FROM Users WHERE name=?", (name,)).fetchone()[0]
                    conn.execute("INSERT INTO Transactions (user_id, type, amount, note) VALUES (?, 'TOPUP', ?, '管理員儲值')", (uid, amount))
                    conn.execute("UPDATE Users SET current_balance = current_balance + ? WHERE user_id = ?", (amount, uid))
                    conn.commit()
                st.toast(f"成功幫 {name} 儲值 ${amount}", icon="💰")
                time.sleep(1)
                st.rerun()

# === 頁面 4: 每日匯總 ===
elif page == "📊 每日匯總":
    st.title("📊 營運儀表板")
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    with get_db_connection() as conn:
        total_bal = conn.execute("SELECT SUM(current_balance) FROM Users").fetchone()[0] or 0
        today_income = conn.execute("SELECT SUM(amount) FROM Transactions WHERE type='TOPUP' AND date(timestamp)=?", (today,)).fetchone()[0] or 0
        today_sales = abs(conn.execute("SELECT SUM(amount) FROM Transactions WHERE type='ORDER' AND date(timestamp)=?", (today,)).fetchone()[0] or 0)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("總發行儲值金", f"${total_bal}")
        m2.metric("今日營收 (訂單)", f"${today_sales}", delta_color="inverse")
        m3.metric("今日儲值金", f"${today_income}")
        
        st.markdown("### 📋 今日交易明細")
        df = pd.read_sql("""SELECT time(timestamp) as 時間, u.name as 員工, type as 類型, dish_name||coalesce(' ('||note||')','') as 說明, amount as 金額 
                            FROM Transactions t JOIN Users u ON t.user_id=u.user_id WHERE date(timestamp)=? ORDER BY timestamp DESC""", conn, params=(today,))
        
        # 美化表格顯示
        def color_type(val):
            return 'background-color: #ffeba1; color: black' if val == 'ORDER' else 'background-color: #a1ffc3; color: black'
        
        st.dataframe(df.style.applymap(color_type, subset=['類型']), use_container_width=True)

# === 頁面 5: 人員管理 ===
elif page == "⚙️ 人員管理":
    st.title("⚙️ 人員管理")
    
    with st.expander("➕ 新增員工", expanded=True):
        with st.form("add_user"):
            c1, c2 = st.columns(2)
            new_name = c1.text_input("姓名")
            init_bal = c2.number_input("初始餘額", value=0)
            if st.form_submit_button("新增"):
                try:
                    with get_db_connection() as conn:
                        cur = conn.cursor()
                        cur.execute("INSERT INTO Users (name, current_balance) VALUES (?, ?)", (new_name, init_bal))
                        uid = cur.lastrowid
                        cur.execute("INSERT INTO Transactions (user_id, type, amount, note) VALUES (?, 'INIT', ?, '開戶')", (uid, init_bal))
                        conn.commit()
                    st.toast(f"員工 {new_name} 新增成功！", icon="✅")
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error("姓名重複或錯誤")
    
    with get_db_connection() as conn:
        users = pd.read_sql("SELECT * FROM Users", conn)
    st.dataframe(users, use_container_width=True)
    
    to_del = st.selectbox("選擇刪除對象", users['name'].tolist() if not users.empty else [])
    if st.button("🗑️ 刪除員工"):
        with get_db_connection() as conn:
            conn.execute("DELETE FROM Users WHERE name=?", (to_del,))
            conn.commit()
        st.rerun()
