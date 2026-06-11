import streamlit as st
import google.generativeai as genai
from PIL import Image

# 網頁版面設定
st.set_page_config(layout="wide")

st.title("💬 AI 萬能聊天與力學助教系統")
st.subheader("版本 3.0：自由對話與全科影像識別版")

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

# --- 🌟【3.0 核心：初始化聊天與記憶體】🌟 ---
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# 如果還沒有啟動大腦聊天室，且 API Key 已經好了，就初始化它
if api_key_ready and st.session_state.chat_session is None:
    model = genai.GenerativeModel('gemini-2.5-flash')
    # 設定 AI 的基本人格：他是個全能的聊天夥伴，但只要看到工程題目就會變身成大師
    system_instruction = (
        "你是一個親切、幽默且知識淵博的 AI 夥伴。你可以和使用者聊任何生活日常話題、開玩笑。\n"
        "但是，如果使用者上傳了工程、物理、靜力學、微積分等學術圖片或題目，\n"
        "請立刻展現你作為『力學頂尖教授』的專業，給出極度詳細、精準的解題步驟和公式列式。"
    )
    st.session_state.chat_session = model.start_chat(history=[])
    # 偷偷塞一條隱藏指令給 AI 奠定人格
    st.session_state.chat_session.send_message(system_instruction)

# --- 【前端介面：左邊上傳、右邊純聊天】 ---
col1, col2 = st.columns([1, 2]) # 調整比例，讓聊天區寬一點

with col1:
    st.header("📸 圖片上傳區")
    st.write("想聊日常直接在右邊打字；想問題目，請把圖片上傳到這裡：")
    uploaded_file = st.file_uploader("選擇題目或生活照片...", type=["png", "jpg", "jpeg"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="📸 已暫存的圖片", width='stretch')
        st.info("💡 圖片已就緒！請在右側對話框輸入你想對這張圖說的話（例如：這題怎麼解？），然後送出。")

with col2:
    st.header("💬 對話聊天室")
    
    # 渲染歷史對話（跳過第一條系統指令）
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        elif msg["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(msg["content"])
                
    # 🌟 使用 Streamlit 內建的標準對話輸入框，極有質感！
    if user_input := st.chat_input("跟 AI 說點什麼吧... (不論是聊生活、問心事、還是問工程題目都可以)"):
        
        # 1. 顯示使用者的對話
        with st.chat_message("user"):
            st.write(user_input)
        
        if api_key_ready:
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    # 2. 判斷這次送出有沒有夾帶左邊上傳的圖片
                    if uploaded_file:
                        # 圖片加上文字一起送過去
                        response = st.session_state.chat_session.send_message([image, user_input])
                    else:
                        # 純文字聊天
                        response = st.session_state.chat_session.send_message(user_input)
                    
                    st.write(response.text)
            
            # 3. 紀錄到歷史對話中，網頁刷新才不會不見
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        else:
            st.error("請先在左側輸入 API Key！")