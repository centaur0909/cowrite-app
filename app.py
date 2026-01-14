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
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------------------------
# 2. スプレッドシート接続機能（心臓部）
# ---------------------------
# キャッシュを使って接続を高速化
@st.cache_resource
def init_connection():
    # Secretsから鍵情報を取り出して、JSONに戻す
    key_dict = json.loads(st.secrets["gcp_service_account"]["info"])
    
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    # シートを開く（名前が間違っているとエラーになるので注意！）
    return client.open("CoWrite_DB").sheet1

# データを読み込む関数
def load_data():
    sheet = init_connection()
    # 全データを辞書形式で取得
    data = sheet.get_all_records() 
    return data, sheet

# ---------------------------
# 3. ロジック（時間計算）
# ---------------------------
DEADLINE = datetime(2026, 1, 14, 23, 59, 0, tzinfo=pytz.timezone('Asia/Tokyo'))
now = datetime.now(pytz.timezone('Asia/Tokyo'))
diff = DEADLINE - now

# ---------------------------
# 4. メイン画面
# ---------------------------
# デッドライン表示
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

# --- ここからスプレッドシート連携モード ---

try:
    # データの読み込み
    data, sheet = load_data()
    df = pd.DataFrame(data)

    # タブ表示
    SONG_LIST = ["Pose & Gimmick", "絶対的マスターピース！", "GO! GO! RUNNER!"]
    tabs = st.tabs([f"{i+1}. {s.split()[0]}" for i, s in enumerate(SONG_LIST)])

    for i, song_name in enumerate(SONG_LIST):
        with tabs[i]:
            st.markdown(f"**🎵 {song_name}**")
            
            # --- タスク追加フォーム ---
            with st.expander("➕ タスクを追加する"):
                with st.form(key=f"add_{i}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        new_task = st.text_input("タスク名")
                    with col2:
                        new_person = st.selectbox("担当", ["三好", "梅澤", "二人"])
                    
                    submit = st.form_submit_button("追加")
                    
                    if submit and new_task:
                        # スプレッドシートに追記
                        # A列:曲名, B列:タスク, C列:担当, D列:完了(FALSE)
                        sheet.append_row([song_name, new_task, new_person, "FALSE"])
                        st.success("追加しました！")
                        st.rerun()

            # --- タスクリスト表示 ---
            # この曲のタスクだけを抽出
            if not df.empty and "曲名" in df.columns:
                song_tasks = df[df["曲名"] == song_name]
                
                if len(song_tasks) == 0:
                    st.info("まだタスクがありません")
                
                for index, row in song_tasks.iterrows():
                    # チェックボックスの状態
                    is_done = str(row["完了"]).upper() == "TRUE"
                    
                    label = f"【{row['担当']}】 {row['タスク名']}"
                    
                    # チェックボックス
                    # keyには行番号(index)を使ってユニークにする
                    new_status = st.checkbox(label, value=is_done, key=f"task_{index}")
                    
                    # 状態が変わったらスプレッドシートを更新
                    if new_status != is_done:
                        # スプレッドシートの行番号は「Pythonのindex + 2」（1行目はヘッダー、indexは0始まりのため）
                        sheet_row_num = index + 2
                        # D列（4列目）を更新
                        sheet.update_cell(sheet_row_num, 4, "TRUE" if new_status else "FALSE")
                        st.rerun()
            else:
                st.info("データがありません。タスクを追加してください。")

except Exception as e:
    st.error("⚠️ エラーが発生しました！")
    st.warning("スプレッドシートの名前は「CoWrite_DB」ですか？ シートの1行目に「曲名」「タスク名」「担当」「完了」が入っていますか？")
    st.code(e)
