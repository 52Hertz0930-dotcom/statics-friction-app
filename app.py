import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from PIL import Image

# 讓網頁版面變寬
st.set_page_config(layout="wide")

st.title("📐 AI 輔助靜力學求解系統")
st.subheader("第四章：摩擦力 (Friction) 4.0 終極精準備援版")
st.write("本系統優先由頂規的 Gemini 2.5 Pro 驅動。若額度用盡，系統將自動無縫切換至 Flash 或 1.5 Pro 大腦，確保解題精準且不中斷！")

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

# --- 🌟【4.0 核心：手動歷史紀錄記憶體】🌟 ---
if "raw_history" not in st.session_state:
    st.session_state.raw_history = []  # 供 API 讀取的標準結構
if "messages" not in st.session_state:
    st.session_state.messages = []     # 供前端網頁渲染的結構

# 📌 終極精準度優先的備援大腦順序 (Pro先發 -> Flash接手 -> 舊版Pro保底)
MODEL_PIPELINE = ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-1.5-pro']

# --- 【前端介面：左右雙欄配置】 ---
col1, col2 = st.columns(2)

with col1:
    st.header("1. 使用者輸入區")
    user_text = st.text_area("請輸入題目文字敘述：", placeholder="例如：一重 30 kg 桿件 AB 靠在牆面...")
    uploaded_file = st.file_uploader("上傳題目圖片（支援 PNG / JPG / JPEG）", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        max_size = 1024
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size))
        st.image(image, caption="📸 已上傳的題目圖片", width='stretch')

    # 按鈕：發起全新題目的解答
    if st.button("🚀 開始解題"):
        if api_key_ready:
            
            expert_instruction = (
                "你是一個具備極高邏輯嚴謹度的靜力學教授。請詳細且精確地解析使用者上傳的摩擦力題目。\n"
                "為了確保物理觀念與代數計算 100% 正確，請你『絕對不要跳步』，並嚴格依照以下 5 大架構進行推演：\n"
                "📌 1. 系統狀態判定：確認是單一剛體或聯結體，並確立摩擦狀態（靜止、即將滑動/臨界狀態、或已滑動）。\n"
                "🖍️ 2. 自由體圖 (FBD) 參數宣告：在列算式前，請先以文字精確表列出所有已知力、未知力（如正向力 N、摩擦力 f）、幾何尺寸、力臂長度、角度與摩擦係數（μs, μk）。\n"
                "📐 3. 建立方程式與正負號定義：列出 ΣFx=0, ΣFy=0, ΣM=0 的力平衡與力矩平衡原始公式。若有力矩，請務必先宣告「你選擇哪個點作為力矩中心」以及「順時針或逆時針為正」。\n"
                "⚙️ 4. 逐步代數運算：將數值代入方程式中，請像解聯立方程式一樣，一步一步寫出移項與計算過程，不可直接給出最終數字。\n"
                "🔍 5. 邏輯與物理驗證：算完後進行最後檢查：(1) 未知數的數量是否等同方程式數量？(2) 若為靜止狀態，求出的摩擦力 f 是否合理地小於或等於最大靜摩擦力 (μs*N)？"
            )

            prompt_payload = f"題目文字敘述如下：\n{user_text}" if user_text else "請詳細分析這張圖片中的摩擦力題目。"
            parts = [image, prompt_payload] if uploaded_file else [prompt_payload]
            
            st.session_state.raw_history = [{"role": "user", "parts": parts}]
            st.session_state.messages = [] 

            success = False
            error_logs = []

            with st.spinner("AI 教授正在嘗試多重演算法解題中..."):
                for model_name in MODEL_PIPELINE:
                    try:
                        model = genai.GenerativeModel(model_name=model_name, system_instruction=expert_instruction)
                        response = model.generate_content(contents=st.session_state.raw_history)
                        
                        st.session_state.raw_history.append({"role": "model", "parts": [response.text]})
                        st.session_state.messages.append({"role": "ai", "content": response.text, "model": model_name})
                        success = True
                        break 
                    except google_exceptions.ResourceExhausted as e:
                        # 這裡會強制顯示錯誤細節，讓你知道是不是真的額度沒了
                        st.error(f"模型 {model_name} 回報錯誤: {e}") 
                        continue
                    except Exception as e:
                        st.error(f"模型 {model_name} 發生未預期錯誤: {e}")
                        continue
                
                if success:
                    st.rerun()
                else:
                    st.error("😭 抱歉！目前所有可用模型的免費額度皆已耗盡，請稍等一分鐘重試。")
                    for log in error_logs:
                        st.warning(log)
        else:
            st.error("請先在左側欄位提供 API Key 才能連線到 AI 大腦！")

with col2:
    st.header("2. 系統解析結果")

    if st.session_state.messages:
        for msg in st.session_state.messages:
            if msg["role"] == "ai":
                st.markdown(msg["content"])
                # 這裡會顯示是哪一個大腦成功解題的，讓你一目了然！
                st.caption(f"🤖 本段解答由模型大腦：`{msg['model']}` 生成")
            elif msg["role"] == "user":
                st.info(f"💡 **您的修正提示：** {msg['content']}")
        
        st.write("---")
        
        with st.form(key="feedback_form", clear_on_submit=True):
            user_feedback = st.text_input("💬 發現步驟算錯、代錯數字，或有不懂的地方？請在此輸入回覆叫它重算：", 
                                          placeholder="例如：你第三步力矩方程式的正負號列錯了，請重新檢查並修正。")
            submit_feedback = st.form_submit_button("🚀 送出修正提示")
            
            if submit_feedback and user_feedback:
                st.session_state.raw_history.append({"role": "user", "parts": [user_feedback]})
                st.session_state.messages.append({"role": "user", "content": user_feedback})
                
                success = False
                with st.spinner("備援大腦正在重新檢視算式中..."):
                    for model_name in MODEL_PIPELINE:
                        try:
                            expert_instruction = (
                                "你是一個具備極高邏輯嚴謹度的靜力學教授。請詳細且精確地解析使用者上傳的摩擦力題目。\n"
                                "為了確保物理觀念與代數計算 100% 正確，請你『絕對不要跳步』..."
                            )
                            model = genai.GenerativeModel(model_name=model_name, system_instruction=expert_instruction)
                            response = model.generate_content(contents=st.session_state.raw_history)
                            
                            st.session_state.raw_history.append({"role": "model", "parts": [response.text]})
                            st.session_state.messages.append({"role": "ai", "content": response.text, "model": model_name})
                            success = True
                            break
                        except google_exceptions.ResourceExhausted:
                            continue
                        except Exception:
                            continue
                    
                    if success:
                        st.rerun()
                    else:
                        st.error("⚠️ 所有備援大腦皆處於冷卻或額度耗盡狀態，請等候一分鐘再送出。")
    else:
        st.info("等待您在左側輸入資料並點擊『開始解題』...")