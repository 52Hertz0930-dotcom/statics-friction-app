import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from PIL import Image

# 讓網頁版面變寬，左邊輸入、右邊看結果
st.set_page_config(layout="wide")

st.title("📐 AI 輔助靜力學解題系統")
st.subheader("第四章：摩擦力 ")
st.write("本系統由 Gemini 2.5 Flash 驅動。若 AI 計算有誤，可在右側對話框直接輸入提示叫它重算！")

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
        
        # 限制圖片最大邊為 1024px（不影響力學圖精準度，且節省傳輸流量）
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
            
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=expert_instruction
            )
            
            st.session_state.chat_session = model.start_chat(history=[])
            st.session_state.messages = [] # 清空舊對話

            prompt_payload = f"題目文字敘述如下：\n{user_text}" if user_text else "請詳細分析這張圖片中的摩擦力題目。"

            with st.spinner("AI 正在召喚力學之魂分析題目中..."):
                try:
                    # 🌟 核心防禦：捕捉 Google 額度耗盡的異常
                    if uploaded_file:
                        response = st.session_state.chat_session.send_message([image, prompt_payload])
                    else:
                        response = st.session_state.chat_session.send_message(prompt_payload)
                    
                    # 成功拿回答案才寫入記憶體
                    st.session_state.messages.append({"role": "ai", "content": response.text})
                    st.rerun()
                    
                except google_exceptions.ResourceExhausted:
                    st.error("⚠️ **Google API 額度已耗盡！**\n\n這代表您目前金鑰的免費請求次數已達上限。請「等待 1 分鐘」後再試（若是觸發每分鐘限制）；若持續出現，則代表今天的總免費額度已用完，需明日重置或更換 API Key。")
                except Exception as e:
                    st.error(f"系統發生預期外的錯誤：{e}")
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
                        # 🌟 修正階段同樣加上防禦
                        response = st.session_state.chat_session.send_message(user_feedback)
                        
                        st.session_state.messages.append({"role": "user", "content": user_feedback})
                        st.session_state.messages.append({"role": "ai", "content": response.text})
                        st.rerun()
                    except google_exceptions.ResourceExhausted:
                        st.error("⚠️ **修正失敗：Google API 額度已耗盡！** 請稍等一分鐘後再試。")
                    except Exception as e:
                        st.error(f"修正時發生錯誤：{e}")
    else:
        st.info("等待您在左側輸入資料並點擊『開始解題』...")