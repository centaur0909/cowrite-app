import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import json

# ==========================================
# 🛠 管理者設定エリア（ここを変えるだけでOK）
# ==========================================
PROJECT_TITLE = "🏆 リンプラ"  # コンペ名
DEADLINE_STR = "2026-01-14 23:59"    # 締め切り日時
SONG_LIST = [
    "Pose & Gimmick", 
    "絶対的マスターピース！", 
    "GO! GO! RUNNER!"
]
# ==========================================

# ---------------------------
# 1. ページ設定 & デザイン調整
# ---------------------------
st.set_page_config(page_title=PROJECT_TITLE, page_icon="🔥", layout="centered")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
            /* デッドラインの文字装飾 */
            .deadline-text {
                font-size: 1.2rem;
                font-weight: bold;
                color: #FF4B4B;
                margin-bottom: 0px;
            }
            .deadline-date {
                font-size: 0.9rem;
                color: #888;
                margin-top: -5px;
                margin-bottom: 15px;
            }
            
            /* 【スマホ対策】削除ボタンを極小にして、強制的に横並びにする */
            .stButton button {
                padding: 0rem 0.2rem !important;
                font-size: 0.8rem !important;
                height: 2em !important;
                min-height: 0px !important;
                line-height: 1 !important;
                border: 1px solid #444;
            }
            /* カラムの隙間を詰める */
            [data-testid="column"] {
                padding: 0px !important;
            }
            /* チェックボックスの余白調整 */
            .stCheckbox {
                margin-top: -5px;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------------------------
# 2. スプレッドシート接続
# ---------------------------
@st.cache_resource
def init_connection():
    key_dict = json.loads(st.secrets["gcp_service_account"]["info"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("CoWrite_DB").sheet1

def load_data():
    sheet = init_connection()
    data = sheet.get_all_records() 
    return data, sheet

# ---------------------------
# 3. ロジック（時間計算）
# ---------------------------
# 設定エリアの文字列から日付オブジェクトを作る
tz = pytz.timezone('Asia/Tokyo')
deadline_dt = datetime.strptime(DEADLINE_STR, '%Y-%m-%d %H:%M')
deadline_dt = tz.localize(deadline_dt)
now = datetime.now(tz)
diff = deadline_dt - now

# ---------------------------
# 4. メイン画面構築
# ---------------------------

# タイトル表示
st.title(PROJECT_TITLE)

# デッドライン表示（カウントダウン＋日付）
if diff.total_seconds() > 0:
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    # 残り時間を大きく表示
    st.markdown(f'<p class="deadline-text">🔥 あと {hours}時間 {minutes}分</p>', unsafe_allow_html=True)
    # 正確な日時を小さく表示
    st.markdown(f'<p class="deadline-date">提出期限: {DEADLINE_STR}</p>', unsafe_allow_html=True)
else:
    st.error("🚨 締め切り過ぎてます！！提出急げ！！")

st.write("---") 

# --- アプリ本体 ---

try:
    data, sheet = load_data()
    df = pd.DataFrame(data)

    # 設定エリアの曲リストを使ってタブを作る
    tabs = st.tabs([f"{s.split()[0]}" for s in SONG_LIST])

    for i, song_name in enumerate(SONG_LIST):
        with tabs[i]:
            # 曲タイトル
            st.markdown(f"#### 🎵 {song_name}")
            
            # --- タスク追加フォーム ---
            with st.expander("➕ タスクを追加", expanded=False):
                with st.form(key=f"add_{i}", clear_on_submit=True):
                    col1, col2 = st.columns([3, 1.2])
                    new_task = st.text_input("タスク名")
                    new_person = st.selectbox("担当", ["-", "三好", "梅澤", "二人"])
                    
                    submit = st.form_submit_button("追加")
                    
                    if submit and new_task:
                        person_val = new_person if new_person != "-" else ""
                        sheet.append_row([song_name, new_task, person_val, "FALSE"])
                        st.success("追加！")
                        st.rerun()

            # --- タスクリスト表示 ---
            if not df.empty and "曲名" in df.columns:
                song_tasks = df[df["曲名"] == song_name]
                
                # 進捗バーの計算
                total_tasks = len(song_tasks)
                if total_tasks > 0:
                    done_tasks = len(song_tasks[song_tasks["完了"].astype(str).str.upper() == "TRUE"])
                    progress = done_tasks / total_tasks
                    st.progress(progress)
                    st.caption(f"進捗: {int(progress * 100)}% ({done_tasks}/{total_tasks})")
                else:
                    st.info("タスクがありません")

                # リスト表示
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    
                    # 担当者表示
                    person_label = f"【{row['担当']}】" if row['担当'] else ""
                    label = f"{person_label} {row['タスク名']}"
                    
                    # 【スマホ対策】比率を[6, 1]にして、ボタンエリアを極限まで狭く
                    col_task, col_del = st.columns([6, 1])
                    
                    with col_task:
                        new_status = st.checkbox(label, value=is_done, key=f"task_{index}")
                        if new_status != is_done:
                            sheet_row_num = index + 2
                            sheet.update_cell(sheet_row_num, 4, "TRUE" if new_status else "FALSE")
                            st.rerun()
                    
                    with col_del:
                        # 削除ボタン
                        if st.button("🗑", key=f"del_{index}"):
                            sheet_row_num = index + 2
                            sheet.delete_rows(sheet_row_num)
                            st.rerun()

            else:
                st.info("データなし")

except Exception as e:
    st.error("⚠️ エラー")
    st.code(e)
