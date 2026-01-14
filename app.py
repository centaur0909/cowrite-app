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
SONG_LIST = [
    "Pose & Gimmick", 
    "絶対的マスターピース！", 
    "GO! GO! RUNNER!"
]
# ==========================================

st.set_page_config(page_title=PROJECT_TITLE, page_icon="🔥", layout="centered")

# ---------------------------
# 🎨 CSS: V4.0 ファイナル・フィックス
# ---------------------------
hide_streamlit_style = """
<style>
    /* 1. 基本設定：ヘッダー隠し・余白最小化 */
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

    /* 2. 【最重要】カラムの強制横並び設定 */
    /* Streamlitはスマホでカラムを縦に積もうとするので、それを阻止する */
    
    [data-testid="stHorizontalBlock"] {
        flex-direction: row !important; /* 絶対に横並び */
        flex-wrap: nowrap !important;   /* 折り返し禁止 */
        align-items: center !important; /* 垂直方向中央揃え */
        gap: 0.5rem !important;
    }

    [data-testid="column"] {
        min-width: 0px !important; /* これがないとスマホで縦になる */
        width: auto !important;
        flex-shrink: 1 !important; /* 必要なら縮むことを許可 */
        padding: 0 !important;
    }

    /* 3. ゴミ箱ボタンのエリア固定 */
    /* 2つ目のカラム（ゴミ箱）をピンポイントで指定 */
    div[data-testid="column"]:nth-of-type(2) {
        flex: 0 0 40px !important; /* 幅40px固定 */
        min-width: 40px !important;
        max-width: 40px !important;
    }

    /* 4. テキスト表示エリアの調整 */
    div[data-testid="column"]:nth-of-type(1) {
        flex-grow: 1 !important; /* 残りのスペースを全部使う */
        overflow: hidden !important; /* はみ出たら隠す */
    }

    /* 5. ゴミ箱ボタンのデザイン */
    div[data-testid="column"]:nth-of-type(2) button {
        border: 1px solid #ccc !important;
        background-color: #f9f9f9 !important;
        color: #333 !important;
        height: 35px !important;
        width: 100% !important;
        padding: 0 !important;
        line-height: 1 !important;
    }

    /* 6. タイトル・文字周り */
    .custom-title {
        font-size: 20px !important;
        font-weight: 700;
        margin-bottom: 0px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .deadline-info {
        font-size: 14px;
        color: #FF4B4B;
        font-weight: bold;
    }
    
    /* 横スクロール対策 */
    body {
        overflow-x: hidden !important;
    }
    
    /* チェックボックス位置微調整 */
    .stCheckbox {
        margin-top: -3px !important;
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

# 自動更新スイッチ
auto_refresh = st.toggle("🔄 自動更新 (入力時はOFF)", value=False)

if auto_refresh:
    time.sleep(10)
    st.rerun()

st.markdown("---") 

try:
    data, sheet = load_data()
    df = pd.DataFrame(data)
    tabs = st.tabs([f"{s.split()[0]}" for s in SONG_LIST])

    for i, song_name in enumerate(SONG_LIST):
        with tabs[i]:
            st.markdown(f"**🎵 {song_name}**")
            
            # --- 入力フォーム（安全第一：縦積み） ---
            with st.expander("➕ タスク追加", expanded=False):
                with st.form(key=f"add_{i}", clear_on_submit=True):
                    # 1. タスク名
                    new_task = st.text_input("タスク名", placeholder="例：ギター録音")
                    
                    # 2. 担当者
                    new_person = st.selectbox("担当", ["-", "三好", "梅澤", "二人"])
                    
                    # 3. 追加ボタン（全幅）
                    submit = st.form_submit_button("リストに追加", use_container_width=True)
                    
                    if submit and new_task:
                        person_val = new_person if new_person != "-" else ""
                        sheet.append_row([song_name, new_task, person_val, "FALSE"])
                        st.success("追加しました")
                        time.sleep(0.5)
                        st.rerun()

            # --- リスト表示 ---
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
                    
                    # ここが修正の肝：カラム比率をPython側でも指定するが、CSSで強制的に上書きされる
                    col_task, col_del = st.columns([0.85, 0.15])
                    
                    with col_task:
                        new_status = st.checkbox(label, value=is_done, key=f"t_{index}")
                        if new_status != is_done:
                            sheet.update_cell(index + 2, 4, "TRUE" if new_status else "FALSE")
                            st.rerun()
                    
                    with col_del:
                        # ゴミ箱ボタン
                        if st.button("🗑", key=f"d_{index}"):
                            sheet.delete_rows(index + 2)
                            st.rerun()
            else:
                st.info("タスクなし")

except Exception as e:
    st.error("エラー")
    st.code(e)
