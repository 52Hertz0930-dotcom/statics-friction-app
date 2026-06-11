import streamlit as st
import google.generativeai as genai
import json
from PIL import Image

# 1. 網頁基本設定
st.set_page_config(page_title="AI 輔助靜力學求解系統 - 摩擦力篇", layout="wide")
st.title("📐 AI 輔助靜力學求解系統")
st.subheader("第四章：摩擦力 (Friction) 專題版")
st.write("本系統由 Gemini 1.5 Flash 驅動，專門解析靜力學中的摩擦力問題。")

# 2. API Key 設定（本地端完全安全版，保證不崩潰）
api_key_ready = False

try:
    # 這段只有在丟上網路（Streamlit Cloud）後才有用，本機執行時會自動跳過
    if "STORED_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["STORED_API_KEY"])
        api_key_ready = True
except:
    # 在自己電腦執行時，如果抓不到 secrets 就安全 pass，絕對不報錯
    pass

# 如果網頁沒偵測到雲端金鑰，就在左邊側邊欄做一個輸入框給使用者填
if not api_key_ready:
    st.sidebar.warning("⚠️ 尚未偵測到雲端密鑰")
    user_key = st.sidebar.text_input("請在此輸入您的 Gemini API Key：", type="password")
    if user_key:
        genai.configure(api_key=user_key)
        api_key_ready = True
    else:
        st.sidebar.info("請輸入從 Google AI Studio 申請到的 API Key 以利本地測試。")

# 3. 畫面佈局：左邊輸入、右邊輸出
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. 使用者輸入區")
    
    # 文字輸入框
    problem_text = st.text_area(
        "請輸入題目文字：", 
        placeholder="例如：一重 500 N 的木塊置於水平地面，靜摩擦係數 0.3，動摩擦係數 0.2。若施加一 100 N 的水平推力，求此時木塊受到的摩擦力為多少？"
    )
    
    # 圖片上傳功能
    uploaded_file = st.file_uploader("上傳題目圖片（支援 PNG / JPG / JPEG）", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="📸 已上傳的題目圖片", use_container_width=True)
        
    # 開始按鈕
    start_solve = st.button("🚀 開始解題")

with col2:
    st.header("2. 系統解析結果")
    
    if start_solve:
        if not problem_text and not uploaded_file:
            st.error("❌ 請輸入題目文字或上傳題目圖片！")
        elif not api_key_ready:
            st.error("❌ 請先在左側邊欄輸入您的 Gemini API Key！")
        else:
            with st.spinner("🧠 AI 正在分析摩擦力狀態並計算中，請稍候..."):
                try:
                    # 設計摩擦力專用的 Prompt 提示詞
                    prompt = f"""
                    你是一個精通大學工程力學、靜力學（Statics）的專業教授。
                    請分析以下關於「摩擦力（Friction）」的問題，並嚴格以 JSON 格式回傳結果。
                    
                    題目文字內容：{problem_text}
                    
                    請遵循以下摩擦力的物理邏輯進行嚴謹分析：
                    1. 題型判斷：說明這是屬於水平面、斜面、還是聯結體的摩擦力問題。
                    2. 受力分析：判斷正向力 N、沿運動方向的外力等。
                    3. 計算最大靜摩擦力：f_max = mu_s * N。
                    4. 狀態判定：比較外力與最大靜摩擦力。若外力 <= f_max，物體靜止，摩擦力等於外力；若外力 > f_max，物體滑動，摩擦力等於動摩擦力 (f_k = mu_k * N)。
                    5. 給出最終答案。

                    請務必使用【繁體中文】回傳，並嚴格遵守以下 JSON 格式，不要包含任何 ```json 的標記：
                    {{
                        "type_judgment": "填寫題型與物體狀態判斷",
                        "formula_used": "列出此題用到的核心公式（例如：f_max = mu_s * N, f = F_push）",
                        "steps": [
                            "步驟 1：計算正向力...",
                            "步驟 2：計算最大靜摩擦力...",
                            "步驟 3：判定運動狀態並得出摩擦力..."
                        ],
                        "calculation_result": "最終答案（包含摩擦力大小與方向）",
                        "notes": "給學生的補充說明或物理觀念提醒"
                    }}
                    """
                    
                    # 呼叫 AI 腦袋
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    inputs = [prompt]
                    if uploaded_file:
                        inputs.append(image)
                        
                    response = model.generate_content(
                        inputs,
                        generation_config={"response_mime_type": "application/json"}
                    )
                    
                    # 解析回傳的 JSON 資料
                    result = json.loads(response.text)
                    
                    # 渲染在網頁畫面上
                    st.success("🎉 解題完成！")
                    
                    st.subheader("📌 題型與狀態判定")
                    st.info(result.get("type_judgment", "無"))
                    
                    st.subheader("📐 使用公式")
                    st.code(result.get("formula_used", "無"))
                    
                    st.subheader("🔢 詳細解題步驟")
                    for i, step in enumerate(result.get("steps", []), 1):
                        st.write(f"**{i}.** {step}")
                        
                    st.subheader("🎯 計算結果（最終答案）")
                    st.metric(label="RESULT", value=result.get("calculation_result", "無"))
                    
                    st.subheader("💡 觀念補充說明")
                    st.warning(result.get("notes", "無"))
                    
                except Exception as e:
                    st.error(f"系統發生非預期錯誤：{str(e)}")
                    st.info("提示：請確認輸入內容是否正常，或檢查 API Key 是否失效。")