import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import json
import time

# ==========================================
# 🛠 管理者設定エリア
# ==========================================
PROJECT_TITLE = "🏆 リンプラリベンジ"  
DEADLINE_STR = "2026-01-14 23:59"

# 左：DB検索用、右：タブ表示用
SONG_MAP = {
    "Pose & Gimmick": "P&G", 
    "絶対的マスターピース！": "絶マス", 
    "GO! GO! RUNNER!": "GGR"
}
# ==========================================

st.set_page_config(page_title=PROJECT_TITLE, page_icon="🦁", layout="centered")

# ---------------------------
# 🎨 CSS
# ---------------------------
hide_streamlit_style = """
<style>
    /* 基本設定 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-bottom: 5rem !important;
        max-width: 100% !important;
    }

    /* タイトル */
    .custom-title {
        font-size: 24px !important;
        font-weight: 800;
        margin-bottom: 5px;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* タイマー */
    .timer-box {
        padding: 8px;
        border-radius: 8px;
        background-color: #f0f2f6;
        color: #000000 !important;
        text-align: center;
        margin-bottom: 5px; 
        font-weight: bold;
        font-size: 16px;
        border: 1px solid #ddd;
    }
    .timer-danger {
        background-color: #fff0f0;
        color: #d32f2f !important;
        border: 2px solid #d32f2f;
    }
    
    /* 日付表示 */
    .deadline-date {
        text-align: center;
        font-size: 12px;
        color: #888;
        margin-bottom: 15px;
    }

    /* スタッツバー */
    .stats-bar {
        display: flex;
        justify-content: space-between;
        background-color: #262730;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid #444;
    }
    .stats-item {
        text-align: center;
        flex: 1;
        color: white;
    }
    .stats-label {
        font-size: 10px;
        color: #aaa;
        display: block;
    }
    .stats-value {
        font-size: 18px;
        font-weight: bold;
        display: block;
    }

    /* 横スクロール対策 */
    body { overflow-x: hidden !important; }
    
    /* チェックボックス */
    .stCheckbox { margin-bottom: 8px !important; }
    
    /* タブの文字サイズ */
    button[data-baseweb="tab"] {
        font-size: 14px !important;
        padding-left: 10px !important;
        padding-right: 10px !important;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------------------------
# 接続 & ロジック
# ---------------------------
@st.cache_resource
def init_connection():
    key_dict = json.loads(st.secrets["gcp_service_account"]["info"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("CoWrite_DB").sheet1

def load_data():
    sheet = init_connection()
    data = sheet.get_all_records() 
    return data, sheet

tz = pytz.timezone('Asia/Tokyo')
deadline_dt = datetime.strptime(DEADLINE_STR, '%Y-%m-%d %H:%M')
deadline_dt = tz.localize(deadline_dt)
now = datetime.now(tz)
diff = deadline_dt - now

# ---------------------------
# メイン画面
# ---------------------------

# タイトル
st.markdown(f'<div class="custom-title">{PROJECT_TITLE}</div>', unsafe_allow_html=True)

# デッドライン表示
if diff.total_seconds() > 0:
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    timer_class = "timer-box timer-danger" if hours < 6 else "timer-box"
    emoji = "😱" if hours < 6 else "🔥"
    
    st.markdown(
        f'<div class="{timer_class}">{emoji} 残り {hours}時間 {minutes}分</div>', 
        unsafe_allow_html=True
    )
    st.markdown(f'<div class="deadline-date">📅 期限: {DEADLINE_STR}</div>', unsafe_allow_html=True)
else:
    st.error("🚨 締め切り過ぎてます！提出急げ！")

# 自動更新スイッチ
auto_refresh = st.toggle("🔄 自動更新", value=False)
if auto_refresh:
    time.sleep(30)
    st.rerun()

st.markdown("---") 

try:
    data, sheet = load_data()
    df = pd.DataFrame(data)
    
    # --- スタッツ表示 ---
    if not df.empty and "完了" in df.columns:
        total_tasks = len(df)
        completed_tasks = len(df[df["完了"].astype(str).str.upper() == "TRUE"])
        rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        
        st.markdown(f"""
        <div class="stats-bar">
            <div class="stats-item">
                <span class="stats-label">全タスク</span>
                <span class="stats-value">{total_tasks}</span>
            </div>
            <div class="stats-item">
                <span class="stats-label" style="color:#4CAF50;">完了</span>
                <span class="stats-value" style="color:#4CAF50;">{completed_tasks}</span>
            </div>
            <div class="stats-item">
                <span class="stats-label" style="color:#2196F3;">進捗率</span>
                <span class="stats-value" style="color:#2196F3;">{rate}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if rate == 100 and total_tasks > 0:
            st.balloons()
            st.success("🎉 全タスク完了！")
    
    # --- タブ ---
    tabs = st.tabs(list(SONG_MAP.values()))

    for i, (song_name, short_name) in enumerate(SONG_MAP.items()):
        with tabs[i]:
            st.markdown(f"**🎵 {song_name}**")
            
            if not df.empty and "曲名" in df.columns:
                song_tasks = df[df["曲名"] == song_name]
                
                # リスト表示
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"【{row['担当']}】" if row['担当'] not in ["-", ""] else ""
                    
                    task_text = row['タスク名']
                    label = f"~~{person}{task_text}~~" if is_done else f"{person}{task_text}"
                    
                    new_status = st.checkbox(label, value=is_done, key=f"t_{index}")
                    
                    if new_status != is_done:
                        sheet.update_cell(index + 2, 4, "TRUE" if new_status else "FALSE")
                        st.rerun()
            else:
                st.info("タスクなし")

            st.write("---")

            # 追加エリア（担当者記憶機能つき）
            with st.expander("➕ タスク追加"):
                with st.form(key=f"add_{i}", clear_on_submit=True):
                    new_task = st.text_input("タスク名")
                    
                    # セッションステートから前回の担当者を取得（デフォルトは一番上）
                    PERSON_OPTIONS = ["-", "三好", "梅澤", "二人"]
                    last_person_key = f"last_person_{i}"
                    default_index = 0
                    
                    if last_person_key in st.session_state:
                        last_p = st.session_state[last_person_key]
                        if last_p in PERSON_OPTIONS:
