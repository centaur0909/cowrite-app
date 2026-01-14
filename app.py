import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import json

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
# 🎨 CSSによる強制レイアウト調整
# ---------------------------
hide_streamlit_style = """
<style>
    /* 不要な要素を消す */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 1. タイトルの文字サイズを強制的に小さくする */
    .custom-title {
        font-size: 22px !important; /* スマホで2行にならない絶妙なサイズ */
        font-weight: 700;
        margin-bottom: 5px;
        white-space: nowrap; /* 強制的に1行にする */
        overflow: hidden;
        text-overflow: ellipsis; /* はみ出たら...にする */
    }

    /* 2. デッドライン情報のデザイン */
    .deadline-info {
        font-size: 14px;
        color: #FF4B4B;
        font-weight: bold;
        margin-bottom: 0px;
    }
    .deadline-sub {
        font-size: 11px;
        color: #666;
        margin-bottom: 15px;
    }

    /* 3. 【最重要】スマホでの「縦並び（折り返し）」を禁止する呪文 */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        align-items: center;
    }
    
    /* 4. カラムごとの設定 */
    /* 左側のテキストエリア（幅は自動調整） */
    [data-testid="column"]:nth-of-type(1) {
        flex: 1 1 auto !important;
        min-width: 0 !important; /* これがないとテキストが縮まない */
    }
    
    /* 右側のゴミ箱エリア（幅をガチガチに固定） */
    [data-testid="column"]:nth-of-type(2) {
        flex: 0 0 40px !important; /* 40pxで固定 */
        min-width: 40px !important;
        max-width: 40px !important;
    }

    /* 5. ボタンとチェックボックスの余白微調整 */
    .stButton button {
        padding: 0px !important;
        width: 30px !important;
        height: 30px !important;
        font-size: 14px !important;
        line-height: 1 !important;
    }
    .stCheckbox {
        margin-top: -2px; /* 垂直位置合わせ */
    }
    
    /* 全体の余白を詰める */
    .block-container {
        padding-top: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
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

# タイトル（st.titleではなくHTMLで描画）
st.markdown(f'<div class="custom-title">{PROJECT_TITLE}</div>', unsafe_allow_html=True)

# デッドライン
if diff.total_seconds() > 0:
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    st.markdown(f'<div class="deadline-info">🔥 あと {hours}時間 {minutes}分</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="deadline-sub">期限: {DEADLINE_STR}</div>', unsafe_allow_html=True)
else:
    st.error("🚨 締め切り過ぎてます！")

st.markdown("---") 

try:
    data, sheet = load_data()
    df = pd.DataFrame(data)
    tabs = st.tabs([f"{s.split()[0]}" for s in SONG_LIST])

    for i, song_name in enumerate(SONG_LIST):
        with tabs[i]:
            st.markdown(f"**🎵 {song_name}**")
            
            # 入力フォーム（ここも横並びが維持されます）
            with st.expander("➕ タスク追加", expanded=False):
                with st.form(key=f"add_{i}", clear_on_submit=True):
                    # 入力欄とボタンの比率
                    c1, c2 = st.columns([4, 1]) 
                    with c1:
                        new_task = st.text_input("タスク名", label_visibility="collapsed", placeholder="タスク名")
                    with c2:
                        # 担当選択は場所取るので、あえて「追加」ボタンだけにする（担当はデフォで二人とかにするか、シンプル化）
                        # もしくは、ここだけはCSSの影響受けるので、シンプルに入力→追加ボタンだけにします
                        submit = st.form_submit_button("追加")
                    
                    # 担当は裏で一旦「未定」か「三好」にしておく（シンプル化のため）
                    # 必要なら復活させますが、スマホ入力の快適さ優先なら項目減らすのが吉
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
                    
                    # カラム作成（比率はCSSで上書きされるのでダミーに近いですが指定しておく）
                    col_task, col_del = st.columns([5, 1])
                    
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
