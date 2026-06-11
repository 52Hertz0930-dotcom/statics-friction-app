import streamlit as st
import google.generativeai as genai
from PIL import Image

# 讓網頁版面變寬，左邊輸入、右邊看結果
st.set_page_config(layout="wide")

st.title("📐 AI 輔助靜力學求解系統")
st.subheader("第四章：摩擦力 (Friction) 2.0 互動修正優化版")
st.write("本系統由 Gemini 2.5 Flash 驅動。已啟動 Token 流量優化，大幅提升連續修正時的穩定度！")

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
        
        # 🌟【省額度關鍵 1】：如果圖片太大，等比例縮小到最大邊 1024px
        # 手機拍照原圖太大是榨乾 Token 額度的元兇，適度縮小完全不影響 AI 辨識工程圖的精準度
        max_size = 1024
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size))
            
        st.image(image, caption="📸 已上傳的題目圖片（已自動優化尺寸以節省流量）", width='stretch')

    # 按鈕：發起全新題目的解答
    if st.button("🚀 開始解題"):
        if api_key_ready:
            
            # 🌟【省額度關鍵 2】：將不變的教授人格與輸出規範移至 system_instruction
            # 這能讓大腦在對話記憶中對這段規範進行優化處理，避免每一輪對話重複堆疊計費
            expert_instruction = (
                "你是一個專業的靜力學教授。請詳細解析使用者上傳的摩擦力題目。\n"
                "請嚴格包含以下架構輸出：\n"
                "📌 題型與狀態判定：分析是剛體、聯結體，以及屬於靜止或即將滑動狀態。\n"
                "📐 使用公式：列出解題需要的力平衡與力矩平衡公式。\n"
                "🔢 詳細解題步驟：拆解至少 5 個以上的詳細步驟，包含計算過程與代入的數值。"
            )
            
            # 初始化大腦，維持你指定的 gemini-2.5-flash 模型
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=expert_instruction
            )
            
            st.session_state.chat_session = model.start_chat(history=[])
            st.session_state.messages = [] # 清空舊對話

            # 只把變動的題目文字當作首發訊息送出
            prompt_payload = f"題目文字敘述如下：\n{user_text}" if user_text else "請詳細分析這張圖片中的摩擦力題目。"

            with st.spinner("AI 正在召喚力學之魂分析題目中..."):
                if uploaded_file:
                    response = st.session_state.chat_session.send_message([image, prompt_payload])
                else:
                    response = st.session_state.chat_session.send_message(prompt_payload)
                
                # 將第一輪的 AI 答案存入記憶體
                st.session_state.messages.append({"role": "ai", "content": response.text})
                st.rerun()
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
        
        # 🌟【互動式修正輸入框】🌟
        with st.form(key="feedback_form", clear_on_submit=True):
            user_feedback = st.text_input("💬 發現步驟算錯、代錯數字，或有不懂的地方？請在此輸入回覆叫它重算：", 
                                          placeholder="例如：你第三步力矩方程式的正負號列錯了，請重新檢查並修正。")
            submit_feedback = st.form_submit_button("🚀 送出修正提示")
            
            if submit_feedback and user_feedback:
                with st.spinner("AI 正在重新翻閱上面的算式並進行修正..."):
                    # 這裡延續 chat_session，因為先前傳送的圖片已經過輕量化縮放，後續對話累加的 Token 會非常安全
                    response = st.session_state.chat_session.send_message(user_feedback)
                    
                    # 把使用者的質疑和 AI 的全新修正答案一起塞進歷史紀錄
                    st.session_state.messages.append({"role": "user", "content": user_feedback})
                    st.session_state.messages.append({"role": "ai", "content": response.text})
                
                st.rerun()
    else:
        st.info("等待您在左側輸入資料並點擊『開始解題』...")