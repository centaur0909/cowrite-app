import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import json

# ---------------------------
# 1. ページ設定
# ---------------------------
st.set_page_config(page_title="Co-Write Sprinter", page_icon="🦁", layout="centered")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .big-font {
                font-size:20px !important;
                font-weight: bold;
                color: #FF4B4B;
            }
            /* ボタンの余白を極限まで削ってスマホで1行に収める */
            .stButton button {
                padding: 0rem 0.5rem;
                line-height: 1.5;
                height: auto;
            }
            /* チェックボックスの余白調整 */
            .stCheckbox {
                padding-top: 5px;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------------------------
# 2. スプレッドシート接続機能
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
# 3. ロジック
# ---------------------------
DEADLINE = datetime(2026, 1, 14, 23, 59, 0, tzinfo=pytz.timezone('Asia/Tokyo'))
now = datetime.now(pytz.timezone('Asia/Tokyo'))
diff = DEADLINE - now

# ---------------------------
# 4. メイン画面
# ---------------------------
if diff.total_seconds() > 0:
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    progress_val = max(0, min(100, int((1 - diff.total_seconds() / (7*24*60*60)) * 100)))
    st.markdown(f'<p class="big-font">🔥 DEADLINEまで：あと {hours}時間 {minutes}分</p>', unsafe_allow_html=True)
    st.progress(progress_val)
else:
    st.error("🚨 締め切り過ぎてます！！提出急げ！！")

st.write("---") 

try:
    data, sheet = load_data()
    df = pd.DataFrame(data)

    SONG_LIST = ["Pose & Gimmick", "絶対的マスターピース！", "GO! GO! RUNNER!"]
    tabs = st.tabs([f"{i+1}. {s.split()[0]}" for i, s in enumerate(SONG_LIST)])

    for i, song_name in enumerate(SONG_LIST):
        with tabs[i]:
            st.markdown(f"**🎵 {song_name}**")
            
            # --- タスク追加フォーム ---
            with st.expander("➕ タスクを追加する", expanded=False):
                with st.form(key=f"add_{i}", clear_on_submit=True):
                    col1, col2 = st.columns([3, 1.2])
                    new_task = st.text_input("タスク名")
                    # 【修正1】先頭に "-" を入れて、リセット時にここに戻るようにした
                    new_person = st.selectbox("担当", ["-", "三好", "梅澤", "二人"])
                    
                    submit = st.form_submit_button("追加")
                    
                    if submit and new_task:
                        # "-" が選ばれていたら空欄にするか、そのまま登録するか
                        person_val = new_person if new_person != "-" else ""
                        sheet.append_row([song_name, new_task, person_val, "FALSE"])
                        st.success("追加しました！")
                        st.rerun()

            # --- タスクリスト表示 ---
            if not df.empty and "曲名" in df.columns:
                song_tasks = df[df["曲名"] == song_name]
                
                if len(song_tasks) == 0:
                    st.info("まだタスクがありません")
                
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    
                    # 担当者が空欄の場合の表示調整
                    person_label = f"【{row['担当']}】" if row['担当'] else "【未定】"
                    label = f"{person_label} {row['タスク名']}"
                    
                    # 【修正2】比率を調整してスマホで1行に収める
                    # [5, 1] くらいの比率にすると、狭い画面でも横並びを維持しやすい
                    col_task, col_del = st.columns([5, 1])
                    
                    with col_task:
                        new_status = st.checkbox(label, value=is_done, key=f"task_{index}")
                        if new_status != is_done:
                            sheet_row_num = index + 2
                            sheet.update_cell(sheet_row_num, 4, "TRUE" if new_status else "FALSE")
                            st.rerun()
                    
                    with col_del:
                        if st.button("🗑️", key=f"del_{index}"):
                            sheet_row_num = index + 2
                            sheet.delete_rows(sheet_row_num)
                            st.rerun()

            else:
                st.info("データがありません。タスクを追加してください。")

except Exception as e:
    st.error("⚠️ エラーが発生しました！")
    st.code(e)
