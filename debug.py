import streamlit as st
import google.generativeai as genai
import sys

st.title("🔧 系統診斷室")

# 1. 檢查 Python 與套件版本
st.subheader("1. 環境檢查")
st.write(f"Python Version: {sys.version}")
try:
    import google.generativeai
    st.success(f"✅ google-generativeai 套件版本: {google.generativeai.__version__}")
    # 關鍵：如果版本低於 0.7.0，那就是 requirements.txt 更新失敗
except ImportError:
    st.error("❌ google-generativeai 套件未安裝！")

# 2. 檢查 API Key
st.subheader("2. 金鑰連線測試")
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("❌ 未讀取到 GEMINI_API_KEY，請檢查 Secrets 設定！")
else:
    # 遮蔽顯示，確認有讀到
    masked_key = api_key[:5] + "*" * 10 + api_key[-5:]
    st.write(f"已讀取金鑰: `{masked_key}`")
    
    # 設定金鑰
    genai.configure(api_key=api_key)

    # 3. 檢查可用模型清單 (這是最關鍵的一步)
    st.subheader("3. 帳號可用模型清單")
    try:
        models = list(genai.list_models())
        found_models = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                found_models.append(m.name)
        
        if found_models:
            st.success(f"✅ 連線成功！您的帳號可以使用以下模型：")
            st.json(found_models)
        else:
            st.warning("⚠️ 連線成功，但沒有找到支援 generateContent 的模型。")
            
    except Exception as e:
        st.error(f"❌ 連線失敗 (List Models Error): {e}")

# 4. 實際發送測試
st.subheader("4. 發送 Hello World 測試")
if st.button("測試 gemini-1.5-flash"):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello, are you alive?")
        st.info(f"回應: {response.text}")
    except Exception as e:
        st.error(f"❌ 測試失敗: {e}")
