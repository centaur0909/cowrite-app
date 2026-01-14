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
# 🛠 接続設定
# ==========================================
@st.cache_resource
def init_connection():
    key_dict = json.loads(st.secrets["gcp_service_account"]["info"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    client = gspread.authorize(creds)
    wb = client.open("CoWrite_DB")
    return wb

def load_data():
    wb = init_connection()
    try:
        config_sheet = wb.worksheet("Config")
        config_records = config_sheet.get_all_records()
        config = {item['Key']: item['Value'] for item in config_records}
    except:
        config = {"ProjectTitle": "Project", "Deadline": "2026-01-01 00:00"}

    song_map = {}
    try:
        songs_sheet = wb.worksheet("Songs")
        songs_records = songs_sheet.get_all_records()
        for item in songs_records:
            if item['FormalName'] and item['ShortName']:
                song_map[item['FormalName']] = item['ShortName']
    except:
        pass

    main_sheet = wb.sheet1
    main_data = main_sheet.get_all_records()
    
    return config, song_map, main_data, main_sheet

# ---------------------------
# 初期設定
# ---------------------------
try:
    config, song_map_db, data, sheet = load_data()
    df = pd.DataFrame(data)

    PROJECT_TITLE = config.get("ProjectTitle", "Co-Write Task")
    DEADLINE_STR = config.get("Deadline", "2026-01-01 00:00")
    
    tz = pytz.timezone('Asia/Tokyo')
    try:
        dt_obj = datetime.strptime(str(DEADLINE_STR), '%Y-%m-%d %H:%M')
        dt_obj = tz.localize(dt_obj)
        DEADLINE_ISO = dt_obj.isoformat()
    except:
        DEADLINE_ISO = datetime.now(tz).isoformat()

except Exception as e:
    st.error("データベース読み込みエラー")
    st.stop()

st.set_page_config(page_title=PROJECT_TITLE, page_icon="🦁", layout="centered")

# ==========================================
# 🎨 CSS
# ==========================================
st.markdown(f"""
<style>
    /* 全体背景 */
    .stApp {{ background-color: #0E1117; }}
    
    /* コンテナ幅調整 */
    .block-container {{ 
        padding-top: 1rem !important; 
        padding-bottom: 5rem !important; 
        max-width: 600px !important; 
    }}

    /* タイトル */
    .custom-title {{
        font-size: 24px !important; font-weight: 900; margin-bottom: 10px;
        background: linear-gradient(90deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
    }}
    
    /* スタッツバー */
    .stats-bar {{
        display: flex; justify-content: space-between;
        background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 10px; border-radius: 8px; margin-bottom: 20px;
    }}
    .stats-item {{ text-align: center; flex: 1; color: #E0E0E0; }}
    .stats-label {{ font-size: 10px; color: #888; display: block; }}
    .stats-value {{ font-size: 18px; font-weight: 700; display: block; }}
    
    /* チェックボックス周りの調整 */
    div[data-testid="stCheckbox"] {{
        min-height: auto;
        margin-bottom: -15px !important; /* タスクと日付の距離を縮める */
        padding-top: 0px;
        padding-bottom: 0px;
    }}
    div[data-testid="stCheckbox"] label {{
        font-size: 15px;
        line-height: 1.5;
        padding-top: 6px;
        padding-bottom: 0px;
    }}

    /* 曲ごとのヘッダーデザイン */
    .song-header {{
        font-size: 1.1rem;
        font-weight: 700;
        color: #E0E0E0;
        margin-top: 8px;    
        margin-bottom: 8px; 
    }}
    .custom-hr {{
        border: 0;
        height: 1px;
        background: #333;
        margin-top: 0px;
        margin-bottom: 5px;
    }}
    
    /* 日付情報のスタイル（2行目用） */
    .task-meta {{
        font-size: 11px !important; /* 確実に小さくする */
        margin-left: 28px; /* チェックボックスのテキストに揃えるインデント */
        margin-bottom: 8px;
        color: #888;
        line-height: 1.2;
    }}

    /* 不要な要素を隠す */
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
    button[data-baseweb="tab"] {{ font-size: 13px !important; padding: 0px 10px !important; min-width: auto !important; }}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# メイン画面
# ---------------------------

st.markdown(f'<div class="custom-title">{PROJECT_TITLE}</div>', unsafe_allow_html=True)

# ⏰ 時計
server_now_ms = int(datetime.now(tz).timestamp() * 1000)
timer_html_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ margin: 0; padding: 0; font-family: sans-serif; background: transparent; display: flex; flex-direction: column; align-items: center; }}
    .timer-box {{
        width: 100%; padding: 10px; border-radius: 8px;
        background: linear-gradient(135deg, #2b303b 0%, #20232a 100%);
        color: #fff; text-align: center; font-weight: 700; font-size: 18px;
        border: 1px solid rgba(255,255,255,0.1);
        font-variant-numeric: tabular-nums; 
    }}
    .deadline-date {{ text-align: center; font-size: 10px; color: #666; margin-top: 4px; }}
    .danger-mode {{ background: linear-gradient(135deg, #3a1c1c 0%, #2a0f0f 100%) !important; border: 1px solid #ff4b4b !important; animation: pulse 2s infinite; }}
    @keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.4); }} 70% {{ box-shadow: 0 0 0 10px rgba(255, 75, 75, 0); }} 100% {{ box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }} }}
</style>
</head>
<body>
    <div id="countdown-box" class="timer-box">⌛ Syncing...</div>
    <div class="deadline-date">DEADLINE: {DEADLINE_STR}</div>
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
            if (diff <= 0) {{ box.innerHTML = "🚨 TIME UP 🚨"; box.className = "timer-box danger-mode"; return; }}
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);
            let emoji = "🔥";
            if (hours < 6) {{ emoji = "⚡"; if (!box.classList.contains("danger-mode")) {{ box.classList.add("danger-mode"); }} }} 
            else {{ box.classList.remove("danger-mode"); }}
            box.innerHTML = emoji + " " + String(hours).padStart(2,'0') + "H " + String(minutes).padStart(2,'0') + "M " + String(seconds).padStart(2,'0') + "S";
        }}
        setInterval(updateTimer, 1000); updateTimer();
    }})();
    </script>
</body>
</html>
"""
components.html(timer_html_code, height=85)

# --- スタッツ ---
if not df.empty and "完了" in df.columns:
    total_tasks = len(df)
    completed_tasks = len(df[df["完了"].astype(str).str.upper() == "TRUE"])
    rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    st.markdown(f"""
    <div class="stats-bar">
        <div class="stats-item"><span class="stats-label">TOTAL</span><span class="stats-value">{total_tasks}</span></div>
        <div class="stats-item"><span class="stats-label" style="color:#4CAF50;">DONE</span><span class="stats-value" style="color:#4CAF50;">{completed_tasks}</span></div>
        <div class="stats-item"><span class="stats-label" style="color:#2196F3;">PROGRESS</span><span class="stats-value" style="color:#2196F3;">{rate}%</span></div>
    </div>
    """, unsafe_allow_html=True)

# --- タスクリスト（V14.0 2行表示版） ---
if not df.empty and "曲名" in df.columns:
    formal_song_names = df["曲名"].unique()
    
    if len(formal_song_names) > 0:
        tab_labels = [song_map_db.get(name, name) for name in formal_song_names]
        tabs = st.tabs(tab_labels)
        
        for i, formal_name in enumerate(formal_song_names):
            with tabs[i]:
                st.markdown(f'<div class="song-header">🎵 {formal_name}</div><hr class="custom-hr">', unsafe_allow_html=True)
                
                song_tasks = df[df["曲名"] == formal_name]
                song_tasks = song_tasks.sort_values(by="完了", ascending=True)
                
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"【{row['担当']}】" if row['担当'] else ""
                    task_text = row['タスク名']
                    
                    # 1行目：タスク名だけ（シンプルに）
                    if is_done:
                        label = f"~~{person} {task_text}~~"
                    else:
                        label = f"**{person} {task_text}**"
                    
                    new_status = st.checkbox(label, value=is_done, key=f"t_{index}")

                    # 2行目：日付情報（HTMLで独立させて表示）
                    # ここなら文字サイズも絵文字サイズも自由自在です
                    meta_html = ""
                    if is_done and "完了日時" in row and str(row["完了日時"]).strip() != "":
                         try:
                            d = datetime.strptime(str(row["完了日時"]), '%Y-%m-%d %H:%M:%S')
                            short_date = d.strftime('%m/%d %H:%M')
                            # 緑色、小さめ
                            meta_html = f'<div class="task-meta" style="color:#4CAF50;">✔ {short_date} DONE</div>'
                         except:
                            meta_html = '<div class="task-meta" style="color:#4CAF50;">✔ DONE</div>'
                    elif not is_done and "期限" in row and str(row["期限"]).strip() != "":
                         # 赤色、小さめ
                         meta_html = f'<div class="task-meta" style="color:#FF4B4B;">📅 期限: {row["期限"]}</div>'
                    
                    # 日付がある場合のみ表示
                    if meta_html:
                        st.markdown(meta_html, unsafe_allow_html=True)

                    # --- 更新処理 ---
                    if new_status != is_done:
                        sheet.update_cell(index + 2, 4, "TRUE" if new_status else "FALSE")
                        if new_status:
                            now_str = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                            sheet.update_cell(index + 2, 6, now_str)
                        else:
                            sheet.update_cell(index + 2, 6, "")
                        st.rerun()
                
                st.write("") 
                
                # 追加エリア
                with st.expander("➕ タスク追加"):
                    with st.form(key=f"add_{i}", clear_on_submit=True):
                        new_task = st.text_input("タスク名")
                        task_deadline = st.text_input("期限 (例 1/20)")
                        new_person = st.selectbox("担当", ["-", "三好", "梅澤", "2人"])
                        
                        if st.form_submit_button("追加", use_container_width=True):
                            if new_task:
                                p_val = new_person if new_person != "-" else ""
                                sheet.append_row([formal_name, new_task, p_val, "FALSE", task_deadline, ""])
                                st.success("追加！")
                                time.sleep(0.5)
                                st.rerun()

                # 削除エリア
                with st.expander("🗑️ タスク削除"):
                    if len(song_tasks) > 0:
                        with st.form(key=f"del_form_{i}"):
                            rows_to_delete = []
                            for idx, row in song_tasks.iterrows():
                                if st.checkbox(f"{row['タスク名']}", key=f"del_chk_{idx}"):
                                    rows_to_delete.append(idx + 2)
                            
                            if st.form_submit_button("選択したタスクを削除", type="primary", use_container_width=True):
                                if rows_to_delete:
                                    rows_to_delete.sort(reverse=True)
                                    for r in rows_to_delete:
                                        sheet.delete_rows(r)
                                    st.success("削除完了")
                                    st.rerun()
    else:
        st.info("DBに曲がありません")
else:
    st.error("読み込みエラー")
