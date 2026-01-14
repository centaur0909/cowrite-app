import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import json
import time
import streamlit.components.v1 as components

# ==========================================
# 🛠 管理者設定エリア
# ==========================================
PROJECT_TITLE = "🏆 リンプラリベンジ"
DEADLINE_ISO = "2026-01-14T23:59:00+09:00"
DEADLINE_DISPLAY = "2026-01-14 23:59"

# 左：DB検索用、右：タブ表示用（DBを書き換えたので、ここも合わせると綺麗です）
SONG_MAP = {
    "ポーズ＆ギミック": "P&G", 
    "絶対的マスターピース！": "絶マス", 
    "GO！GO！ランナー！": "GGR"
}

PERSON_OPTIONS = ["-", "三好", "梅澤", "2人"]
# ==========================================

st.set_page_config(page_title=PROJECT_TITLE, page_icon="🦁", layout="centered")

# ---------------------------
# 🎨 CSS (ここがデザインの命！)
# ---------------------------
st.markdown(f"""
<style>
    /* 1. ベースの配色（DAWのようなダークグレー） */
    .stApp {{
        background-color: #0E1117;
    }}
    
    /* 2. 余白調整 */
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        max-width: 700px !important;
    }}

    /* 3. タイトル（グラデーションで高級感） */
    .custom-title {{
        font-size: 28px !important;
        font-weight: 900;
        margin-bottom: 10px;
        background: linear-gradient(90deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 0.05em;
    }}

    /* 4. スタッツバー（カード化） */
    .stats-bar {{
        display: flex;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.05); /* 半透明 */
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }}
    .stats-item {{
        text-align: center;
        flex: 1;
        color: #E0E0E0;
    }}
    .stats-label {{
        font-size: 11px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: block;
        margin-bottom: 4px;
    }}
    .stats-value {{
        font-size: 20px;
        font-weight: 700;
        display: block;
    }}

    /* 5. タスクリスト（重要：ここをカードっぽくする） */
    /* チェックボックスの周りに枠をつける */
    div[data-testid="stCheckbox"] {{
        background-color: #1A1C24;
        padding: 12px 15px;
        border-radius: 8px;
        border-left: 4px solid #333; /* 左にアクセント線 */
        margin-bottom: 8px;
        transition: all 0.2s ease;
    }}
    /* ホバー時に少し明るく */
    div[data-testid="stCheckbox"]:hover {{
        background-color: #262830;
        border-left: 4px solid #FF4B4B;
    }}

    /* 完了済み（TRUE）のデザインを変える */
    /* ※StreamlitのCSSハックは限界がありますが、雰囲気は出せます */

    /* 6. タブのデザイン */
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        color: #888 !important;
        font-weight: bold !important;
        border-radius: 4px !important;
        margin-right: 4px !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        background-color: #262830 !important;
        color: #fff !important;
        border-bottom: 2px solid #FF4B4B !important;
    }}

    /* 7. エキスパンダー（追加・削除エリア）をスタイリッシュに */
    .streamlit-expanderHeader {{
        background-color: #1A1C24 !important;
        border-radius: 8px !important;
        color: #ddd !important;
        font-size: 14px !important;
    }}
    
    /* フッターなどの非表示 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}

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
# ⏰ 時計（デザイン調整版）
# ---------------------------
tz = pytz.timezone('Asia/Tokyo')
server_now_ms = int(datetime.now(tz).timestamp() * 1000)

timer_html_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0; padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: transparent;
        display: flex; flex-direction: column; align-items: center;
    }}
    .timer-container {{
        width: 100%;
        display: flex; flex-direction: column; align-items: center;
    }}
    .timer-box {{
        width: 100%;
        padding: 12px;
        border-radius: 12px;
        background: linear-gradient(135deg, #2b303b 0%, #20232a 100%);
        color: #fff;
        text-align: center;
        margin-bottom: 5px; 
        font-weight: 700;
        font-size: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        font-variant-numeric: tabular-nums; /* 数字の幅を揃える */
        letter-spacing: 1px;
    }}
    .deadline-date {{
        text-align: center; font-size: 11px; color: #666; margin-top: 4px; font-weight: 500;
    }}
    .danger-mode {{
        background: linear-gradient(135deg, #3a1c1c 0%, #2a0f0f 100%) !important;
        color: #ff6b6b !important;
        border: 1px solid #ff4b4b !important;
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
    <div class="timer-container">
        <div id="countdown-box" class="timer-box">⌛ Syncing...</div>
        <div class="deadline-date">DEADLINE: {DEADLINE_DISPLAY}</div>
    </div>

    <script>
    (function() {{
        const serverTime = {server_now_ms}; 
        const deadline = new Date("{DEADLINE_ISO}");
        const localTime = Date.now();
        const timeOffset = serverTime - localTime; 

        const box = document.getElementById("countdown-box");

        function updateTimer() {{
            const now = new Date(Date.now() + timeOffset);
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
                emoji = "⚡"; // アイコン変更
                if (!box.classList.contains("danger-mode")) {{
                    box.classList.add("danger-mode");
                }}
            }} else {{
                box.classList.remove("danger-mode");
            }}
            
            box.innerHTML = emoji + " " + hStr + "<span style='font-size:12px'>H</span> " 
                            + mStr + "<span style='font-size:12px'>M</span> " 
                            + sStr + "<span style='font-size:12px'>S</span>";
        }}
        
        setInterval(updateTimer, 1000);
        updateTimer();
    }})();
    </script>
</body>
</html>
"""
components.html(timer_html_code, height=90)

# 自動更新スイッチ（目立たないように少し小さく）
auto_refresh = st.toggle("Auto Refresh (30s)", value=False)
if auto_refresh:
    time.sleep(30)
    st.rerun()

st.write("") # スペース

try:
    data, sheet = load_data()
    df = pd.DataFrame(data)
    
    # --- スタッツ表示 ---
    if not df.empty and "完了" in df.columns:
        total_tasks = len(df)
        completed_tasks = len(df[df["完了"].astype(str).str.upper() == "TRUE"])
        rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        
        # HTMLでカード型スタッツを描画
        st.markdown(f"""
        <div class="stats-bar">
            <div class="stats-item">
                <span class="stats-label">TOTAL</span>
                <span class="stats-value">{total_tasks}</span>
            </div>
            <div class="stats-item">
                <span class="stats-label" style="color:#4CAF50;">DONE</span>
                <span class="stats-value" style="color:#4CAF50;">{completed_tasks}</span>
            </div>
            <div class="stats-item">
                <span class="stats-label" style="color:#2196F3;">PROGRESS</span>
                <span class="stats-value" style="color:#2196F3;">{rate}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if rate == 100 and total_tasks > 0:
            st.balloons()
            st.success("🎉 MISSION COMPLETE!")
    
    # --- タブ ---
    tabs = st.tabs(list(SONG_MAP.values()))

    for i, (song_name, short_name) in enumerate(SONG_MAP.items()):
        with tabs[i]:
            # 曲名はシンプルに
            st.markdown(f"##### 🎵 {song_name}")
            
            if not df.empty and "曲名" in df.columns:
                song_tasks = df[df["曲名"] == song_name]
                song_tasks = song_tasks.sort_values(by="完了", ascending=True)
                
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"【{row['担当']}】" if row['担当'] not in ["-", ""] else ""
                    task_text = row['タスク名']
                    
                    # 完了時は色を薄くする演出
                    if is_done:
                        label = f"~~{person} {task_text}~~"
                    else:
                        label = f"**{person} {task_text}**" # 未完了は太字
                    
                    new_status = st.checkbox(label, value=is_done, key=f"t_{index}")
                    
                    if new_status != is_done:
                        sheet.update_cell(index + 2, 4, "TRUE" if new_status else "FALSE")
                        st.rerun()
            else:
                st.info("No Tasks")

            st.write("---")

            # 追加エリア
            with st.expander("➕ Add New Task"):
                with st.form(key=f"add_{i}", clear_on_submit=True):
                    new_task = st.text_input("Task Name")
                    
                    last_person_key = f"last_person_{i}"
                    default_index = 0
                    if last_person_key in st.session_state:
                        last_p = st.session_state[last_person_key]
                        if last_p in PERSON_OPTIONS:
                            default_index = PERSON_OPTIONS.index(last_p)

                    new_person = st.selectbox("Person", PERSON_OPTIONS, index=default_index)
                    
                    if st.form_submit_button("ADD", use_container_width=True):
                        if new_task:
                            p_val = new_person if new_person != "-" else ""
                            sheet.append_row([song_name, new_task, p_val, "FALSE"])
                            st.session_state[last_person_key] = new_person
                            st.success("Added!")
                            time.sleep(0.5)
                            st.rerun()

            # 削除エリア
            with st.expander("🗑️ Delete Tasks"):
                if not df.empty and "曲名" in df.columns and len(song_tasks) > 0:
                    with st.form(key=f"del_form_{i}"):
                        rows_to_delete = []
                        for idx, row in song_tasks.iterrows():
                            # 削除リストも見やすく
                            if st.checkbox(f"{row['タスク名']}", key=f"del_chk_{idx}"):
                                rows_to_delete.append(idx + 2)
                        
                        if st.form_submit_button("DELETE SELECTED", type="primary", use_container_width=True):
                            if rows_to_delete:
                                rows_to_delete.sort(reverse=True)
                                for r in rows_to_delete:
                                    sheet.delete_rows(r)
                                st.success("Deleted!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.warning("Select tasks to delete")
                else:
                    st.info("No tasks to delete")

except Exception as e:
    st.error("Error connecting to DB")
    # st.code(e) # エラー詳細は隠す（デザイン優先）
