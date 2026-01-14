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
# 🎨 CSS: シンプル・イズ・ベスト
# ---------------------------
hide_streamlit_style = """
<style>
    /* 基本設定 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* スマホ余白設定 */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 3rem !important;
        max-width: 100% !important;
    }

    /* タイトル */
    .custom-title {
        font-size: 20px !important;
        font-weight: 700;
        margin-bottom: 0px;
    }
    .deadline-info {
        font-size: 16px;
        color: #FF4B4B;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    /* 横スクロール対策：これでもう絶対にはみ出さない */
    body {
        overflow-x: hidden !important;
    }
    
    /* チェックボックスを見やすく */
    .stCheckbox {
        margin-bottom: 10px !important;
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
    st.markdown(f'<div class="deadline-info">🔥 残り {hours}時間 {minutes}分</div>', unsafe_allow_html=True)
else:
    st.error("🚨 締め切り過ぎてます！")

# 🔄 自動更新ロジック（ここがポイント！）
# 常に画面上部に更新スイッチを置く
# 「入力中」はOFFにしないと入力内容が消えるので注意書きを入れています
auto_refresh = st.toggle("🔄 自動更新 (30秒ごと)", value=False, help="ONにすると30秒ごとに最新情報を取得します")

if auto_refresh:
    time.sleep(30) # 30秒待機
    st.rerun()     # 画面を再読み込み

st.markdown("---") 

try:
    data, sheet = load_data()
    df = pd.DataFrame(data)
    tabs = st.tabs([f"{s.split()[0]}" for s in SONG_LIST])

    for i, song_name in enumerate(SONG_LIST):
        with tabs[i]:
            st.markdown(f"**🎵 {song_name}**")
            
            # --- 1. タスクリスト（シンプル表示） ---
            # ここには削除ボタンを置かない！だから崩れない！
            if not df.empty and "曲名" in df.columns:
                song_tasks = df[df["曲名"] == song_name]
                
                # 進捗バー
                if len(song_tasks) > 0:
                    done = len(song_tasks[song_tasks["完了"].astype(str).str.upper() == "TRUE"])
                    st.progress(done / len(song_tasks))
                
                # リスト表示（チェックボックスのみ）
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"【{row['担当']}】" if row['担当'] not in ["-", ""] else ""
                    label = f"{person}{row['タスク名']}"
                    
                    # カラムを使わずシンプルに配置
                    new_status = st.checkbox(label, value=is_done, key=f"t_{index}")
                    if new_status != is_done:
                        sheet.update_cell(index + 2, 4, "TRUE" if new_status else "FALSE")
                        st.rerun()
            else:
                st.info("タスクがありません")

            st.write("---")

            # --- 2. タスク追加エリア ---
            with st.expander("➕ タスクを追加"):
                with st.form(key=f"add_{i}", clear_on_submit=True):
                    new_task = st.text_input("タスク名")
                    new_person = st.selectbox("担当", ["-", "三好", "梅澤", "二人"])
                    submit_add = st.form_submit_button("追加", use_container_width=True)
                    
                    if submit_add and new_task:
                        person_val = new_person if new_person != "-" else ""
                        sheet.append_row([song_name, new_task, person_val, "FALSE"])
                        st.success("追加しました")
                        time.sleep(0.5)
                        st.rerun()

            # --- 3. タスク削除エリア（別アプローチ！） ---
            # リストを汚さず、ここでまとめて消す
            with st.expander("🗑️ タスクを削除する"):
                if not df.empty and "曲名" in df.columns and len(song_tasks) > 0:
                    # 削除したいタスクを選ばせる
                    delete_options = [f"{row['タスク名']} (行:{index+2})" for index, row in song_tasks.iterrows()]
                    # ※内部処理用にindexを保持
                    selected_to_delete = st.multiselect("削除するタスクを選択", delete_options)
                    
                    if st.button("選択したタスクを削除", key=f"del_btn_{i}", type="primary"):
                        if selected_to_delete:
                            # 行番号が大きい順に消さないとズレるのでソートして逆順にする
                            rows_to_delete = []
                            for item in selected_to_delete:
                                # "(行:X)" から数字を取り出す
                                row_num = int(item.split("(行:")[1].replace(")", ""))
                                rows_to_delete.append(row_num)
                            
                            rows_to_delete.sort(reverse=True)
                            
                            for r in rows_to_delete:
                                sheet.delete_rows(r)
                            
                            st.success("削除しました")
                            time.sleep(1)
                            st.rerun()
                else:
                    st.caption("削除できるタスクがありません")

except Exception as e:
    st.error("エラーが発生しました")
    st.code(e)
