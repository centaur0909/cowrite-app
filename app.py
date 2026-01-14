import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import json
import time # 時間管理用

# ==========================================
# 🛠 管理者設定エリア
# ==========================================
PROJECT_TITLE = "🏆 リンプラリベンジ"  
DEADLINE_STR = "2026-01-14 23:59"
SONG_LIST = [
    "Pose & Gimmick", 
    "絶対的マスターピース！", 
    "GO! GO! RUNNER!"
]
# ==========================================

st.set_page_config(page_title=PROJECT_TITLE, page_icon="🔥", layout="centered")

# ---------------------------
# 🎨 CSS: 横スクロール禁止 & スマホ最適化
# ---------------------------
hide_streamlit_style = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 横スクロールを親要素から抹殺する */
    body {
        overflow-x: hidden !important;
    }
    .stApp {
        overflow-x: hidden !important;
    }
    
    /* スマホの余白を限界まで削る */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }

    /* タイトル */
    .custom-title {
        font-size: 20px !important;
        font-weight: 700;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* デッドライン */
    .deadline-info {
        font-size: 14px;
        color: #FF4B4B;
        font-weight: bold;
    }

    /* スマホレイアウト強制（折り返し禁止） */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        width: 100% !important;
    }
    
    /* 左カラム（テキスト）：縮小許可 */
    [data-testid="column"]:nth-of-type(1) {
        flex: 1 1 auto !important;
        width: auto !important;
        min-width: 0 !important;
        overflow: hidden !important;
    }
    
    /* 右カラム（ゴミ箱）：サイズ固定 */
    [data-testid="column"]:nth-of-type(2) {
        flex: 0 0 35px !important;
        width: 35px !important;
        min-width: 35px !important;
    }

    /* ボタン微調整 */
    .stButton button {
        padding: 0px !important;
        width: 30px !important;
        height: 30px !important;
        font-size: 12px !important;
    }
    .stCheckbox {
        margin-top: -4px;
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

# デッドライン
if diff.total_seconds() > 0:
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    st.markdown(f'<div class="deadline-info">🔥 残り {hours}時間 {minutes}分</div>', unsafe_allow_html=True)
else:
    st.error("🚨 締め切り過ぎてます！")

# --- 自動更新モード（トグル） ---
# ここをONにすると、スクリプトがループして最新情報を取ってくる
auto_refresh = st.toggle("🔄 自動更新モード (閲覧用)")

if auto_refresh:
    time.sleep(10) # 10秒待つ
    st.rerun()     # 画面を更新！

st.markdown("---") 

try:
    data, sheet = load_data()
    df = pd.DataFrame(data)
    tabs = st.tabs([f"{s.split()[0]}" for s in SONG_LIST])

    for i, song_name in enumerate(SONG_LIST):
        with tabs[i]:
            st.markdown(f"**🎵 {song_name}**")
            
            # 入力フォーム
            with st.expander("➕ タスク追加", expanded=False):
                with st.form(key=f"add_{i}", clear_on_submit=True):
                    c1, c2 = st.columns([4, 1]) 
                    with c1:
                        new_task = st.text_input("タスク名", label_visibility="collapsed", placeholder="タスク名")
                    with c2:
                        submit = st.form_submit_button("追加")
                    
                    if submit and new_task:
                        sheet.append_row([song_name, new_task, "二人", "FALSE"])
                        st.success("追加")
                        st.rerun()

            # リスト表示
            if not df.empty and "曲名" in df.columns:
                song_tasks = df[df["曲名"] == song_name]
                
                # 進捗バー
                if len(song_tasks) > 0:
                    done = len(song_tasks[song_tasks["完了"].astype(str).str.upper() == "TRUE"])
                    st.progress(done / len(song_tasks))

                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"【{row['担当']}】" if row['担当'] not in ["-", ""] else ""
                    label = f"{person}{row['タスク名']}"
                    
                    # カラム作成（比率調整済み）
                    col_task, col_del = st.columns([6, 1])
                    
                    with col_task:
                        new_status = st.checkbox(label, value=is_done, key=f"t_{index}")
                        if new_status != is_done:
                            sheet.update_cell(index + 2, 4, "TRUE" if new_status else "FALSE")
                            st.rerun()
                    
                    with col_del:
                        if st.button("🗑", key=f"d_{index}"):
                            sheet.delete_rows(index + 2)
                            st.rerun()
            else:
                st.info("タスクなし")

except Exception as e:
    st.error("エラー")
    st.code(e)
