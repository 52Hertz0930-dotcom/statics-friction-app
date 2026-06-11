import streamlit as st
import google.generativeai as genai
from PIL import Image

# 讓網頁版面變寬，左邊輸入、右邊看結果
st.set_page_config(layout="wide")

st.title("📐 AI 輔助靜力學求解系統")
st.subheader("第四章：摩擦力 (高配額穩定版)")
st.write("本系統已優化後端模型，嚴格執行靜力學專業解析。若 AI 計算有誤，可在右側輸入框叫它重算。")

# --- 【金鑰安全檢查區】 ---
api_key_ready = False
if "STORED_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["STORED_API_KEY"])
    api_key_ready = True

if not api_key_ready:
    st.sidebar.warning("⚠️ 尚未偵測到雲端密鑰")
    user_key = st.sidebar.text_input("請在此輸入您的 Gemini API Key：", type="password")
    if user_key:
        cleaned_key = user_key.strip().replace('"', '').replace("'", "")
        genai.configure(api_key=cleaned_key)
        api_key_ready = True
    else:
        st.sidebar.info("請輸入從 Google AI Studio 申請到的 API Key 以利測試。")

# --- 🌟【核心：初始化大腦記憶體】🌟 ---
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 【前端介面：左右雙欄配置】 ---
col1, col2 = st.columns(2)

with col1:
    st.header("1. 使用者輸入區")
    user_text = st.text_area("請輸入題目文字敘述：", placeholder="例如：一重 30 kg 桿件 AB 靠在牆面...")
    uploaded_file = st.file_uploader("上傳題目圖片（支援 PNG / JPG / JPEG）", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="📸 已上傳的題目圖片", width='stretch')

    # 按鈕：發起全新題目的解答
    if st.button("🚀 開始解題"):
        if api_key_ready:
            try:
                # 換成 14,400 次/天的大額度模型，拒絕紅字封鎖
                model = genai.GenerativeModel('gemma-3-27b-it')
                st.session_state.chat_session = model.start_chat(history=[])
                st.session_state.messages = [] # 清空舊對話

                # 完全還原你原本的嚴格教授提示詞
                system_prompt = (
                    "你是一個專業的靜力學教授。請詳細解析使用者上傳的摩擦力題目。\n"
                    "請嚴格包含以下架構輸出：\n"
                    "📌 題型與狀態判定：分析是剛體、聯結體，以及屬於靜止或即將滑動狀態。\n"
                    "📐 使用公式：列出解題需要的力平衡與力矩平衡公式。\n"
                    "🔢 詳細解題步驟：拆解至少 5 個以上的詳細步驟，包含計算過程與代入的數值。\n\n"
                    f"題目文字：{user_text}"
                )

                with st.spinner("AI 正在召喚力學之魂分析題目中..."):
                    if uploaded_file:
                        response = st.session_state.chat_session.send_message([image, system_prompt])
                    else:
                        response = st.session_state.chat_session.send_message(system_prompt)
                    
                    # 將第一輪的 AI 答案存入記憶體
                    st.session_state.messages.append({"role": "ai", "content": response.text})
                    st.rerun()
            except Exception as e:
                st.error(f"系統發起失敗，請稍後重試。錯誤原因：{e}")
        else:
            st.error("請先在左側欄位提供 API Key 才能連線到 AI 大腦！")

with col2:
    st.header("2. 系統解析結果")

    # 如果記憶體裡面有對話紀錄，就依序渲染出來
    if st.session_state.messages:
        for msg in st.session_state.messages:
            if msg["role"] == "ai":
                st.markdown(msg["content"])
            elif msg["role"] == "user":
                st.info(f"💡 **您的修正提示：** {msg['content']}")
        
        st.write("---")
        
        # 互動式修正輸入框
        with st.form(key="feedback_form", clear_on_submit=True):
            user_feedback = st.text_input("💬 發現步驟算錯、代錯數字，或有不懂的地方？請在此輸入回覆叫它重算：", 
                                          placeholder="例如：你第三步力矩方程式的正負號列錯了，請重新檢查並修正。")
            submit_feedback = st.form_submit_button("🚀 送出修正提示")
            
            if submit_feedback and user_feedback:
                with st.spinner("AI 正在重新翻閱上面的算式並進行修正..."):
                    try:
                        response = st.session_state.chat_session.send_message(user_feedback)
                        
                        # 把使用者的質疑和 AI 的全新修正答案一起塞進歷史紀錄
                        st.session_state.messages.append({"role": "user", "content": user_feedback})
                        st.session_state.messages.append({"role": "ai", "content": response.text})
                        st.rerun()
                    except Exception as e:
                        st.error(f"修正失敗，伺服器繁忙：{e}")
    else:
        st.info("等待您在左側輸入資料並點擊『開始解題』...")