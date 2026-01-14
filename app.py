import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import json
import time
# 【重要】これを追加しないと動きません
import streamlit.components.v1 as components

# ==========================================
# 🛠 管理者設定エリア
# ==========================================
PROJECT_TITLE = "🏆 リンプラリベンジ"  
DEADLINE_ISO = "2026-01-14T23:59:00+09:00"
DEADLINE_DISPLAY = "2026-01-14 23:59"

SONG_MAP = {
    "Pose & Gimmick": "P&G", 
    "絶対的マスターピース！": "絶マス", 
    "GO! GO! RUNNER!": "GGR"
}

# 担当者の選択肢（「2人」に変更済み）
PERSON_OPTIONS = ["-", "三好", "梅澤", "2人"]
# ==========================================

st.set_page_config(page_title=PROJECT_TITLE, page_icon="🦁", layout="centered")

# ---------------------------
# 🎨 CSS (全体デザイン用)
# ---------------------------
st.markdown(f"""
<style>
    /* 基本設定 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    .block-container {{
        padding-top: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-bottom: 5rem !important;
        max-width: 100% !important;
    }}

    /* タイトル */
    .custom-title {{
        font-size: 24px !important;
        font-weight: 800;
        margin-bottom: 5px;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    /* スタッツバー */
    .stats-bar {{
        display: flex;
        justify-content: space-between;
        background-color: #262730;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid #444;
    }}
    .stats-item {{
        text-align: center;
        flex: 1;
        color: white;
    }}
    .stats-label {{
        font-size: 10px;
        color: #aaa;
        display: block;
    }}
    .stats-value {{
        font-size: 18px;
        font-weight: bold;
        display: block;
    }}

    /* 横スクロール対策 */
    body {{ overflow-x: hidden !important; }}
    
    /* チェックボックス */
    .stCheckbox {{ margin-bottom: 8px !important; }}
    
    button[data-baseweb="tab"] {{
        font-size: 14px !important;
        padding-left: 10px !important;
        padding-right: 10px !important;
    }}
</style>
""", unsafe_allow_html=True)

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

# ---------------------------
# メイン画面
# ---------------------------

# タイトル
st.markdown(f'<div class="custom-title">{PROJECT_TITLE}</div>', unsafe_allow_html=True)

# ---------------------------
# ⏰ ヌルヌル時計コンポーネント (iframe版)
# ---------------------------
# ここが修正の核心です。Pythonから独立したHTMLとして埋め込みます。
timer_html_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0;
        padding: 0;
        font-family: sans-serif;
        background-color: transparent;
        display: flex;
        flex-direction: column;
        align-items: center;
    }}
    .timer-box {{
        width: 95%;
        padding: 10px;
        border-radius: 8px;
        background-color: #f0f2f6;
        color: #000000;
        text-align: center;
        margin-bottom: 5px; 
        font-weight: bold;
        font-size: 18px;
        border: 1px solid #ddd;
        font-family: monospace;
        box-sizing: border-box;
    }}
    .deadline-date {{
        text-align: center;
        font-size: 12px;
        color: #888;
        margin-top: 0px;
    }}
    .danger-mode {{
        background-color: #fff0f0 !important;
        color: #d32f2f !important;
        border: 2px solid #d32f2f !important;
        animation: pulse 2s infinite;
    }}
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.4); }}
        70% {{ box-shadow: 0 0 0 10px rgba(255, 75, 75, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }}
    }}
</style>
</head>
<body>
    <div id="countdown-box" class="timer-box">⌛ Loading...</div>
    <div class="deadline-date">📅 期限: {DEADLINE_DISPLAY}</div>

    <script>
    (function() {{
        const deadline = new Date("{DEADLINE_ISO}");
        const box = document.getElementById("countdown-box");

        function updateTimer() {{
            const now = new Date();
            const diff = deadline - now;

            if (diff <= 0) {{
                box.innerHTML = "🚨 TIME UP 🚨";
                box.className = "timer-box danger-mode";
                return;
            }}

            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            const hStr = String(hours).padStart(2, '0');
            const mStr = String(minutes).padStart(2, '0');
            const sStr = String(seconds).padStart(2, '0');

            let emoji = "🔥";
            if (hours < 6) {{
                emoji = "😱";
                if (!box.classList.contains("danger-mode")) {{
                    box.classList.add("danger-mode");
                }}
            }} else {{
                box.classList.remove("danger-mode");
            }}
            
            box.innerHTML = emoji + " 残り " + hStr + "時間" + mStr + "分" + sStr + "秒";
        }}
        
        setInterval(updateTimer, 1000);
        updateTimer();
    }})();
    </script>
</body>
</html>
"""

# HTMLをiframeとして埋め込む（高さ85px確保）
components.html(timer_html_code, height=85)


# データ自動更新スイッチ
auto_refresh = st.toggle("🔄 データの自動取得 (30秒)", value=False)
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
                
                # 自動整列
                song_tasks = song_tasks.sort_values(by="完了", ascending=True)
                
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

            # 追加エリア
            with st.expander("➕ タスク追加"):
                with st.form(key=f"add_{i}", clear_on_submit=True):
                    new_task = st.text_input("タスク名")
                    
                    # 担当者の記憶ロジック
                    last_person_key = f"last_person_{i}"
                    default_index = 0
                    
                    if last_person_key in st.session_state:
                        last_p = st.session_state[last_person_key]
                        if last_p in PERSON_OPTIONS:
                            default_index = PERSON_OPTIONS.index(last_p)

                    # ここで「2人」が反映されます
                    new_person = st.selectbox("担当", PERSON_OPTIONS, index=default_index)
                    
                    if st.form_submit_button("追加", use_container_width=True):
                        if new_task:
                            p_val = new_person if new_person != "-" else ""
                            sheet.append_row([song_name, new_task, p_val, "FALSE"])
                            st.session_state[last_person_key] = new_person
                            st.success("追加！")
                            time.sleep(0.5)
                            st.rerun()

            # 削除エリア
            with st.expander("🗑️ タスク整理（削除）"):
                if not df.empty and "曲名" in df.columns and len(song_tasks) > 0:
                    st.caption("削除したいタスクにチェックを入れてください")
                    
                    with st.form(key=f"del_form_{i}"):
                        rows_to_delete = []
                        for idx, row in song_tasks.iterrows():
                            if st.checkbox(f"{row['タスク名']}", key=f"del_chk_{idx}"):
                                rows_to_delete.append(idx + 2)
                        
                        if st.form_submit_button("チェックしたタスクを削除", type="primary", use_container_width=True):
                            if rows_to_delete:
                                rows_to_delete.sort(reverse=True)
                                for r in rows_to_delete:
                                    sheet.delete_rows(r)
                                st.success("削除しました")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning("削除するタスクが選択されていません")
                else:
                    st.info("削除できるタスクがありません")

except Exception as e:
    st.error("エラー")
    st.code(e)
