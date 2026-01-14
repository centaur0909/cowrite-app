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
    st.error("System Error: DB Connection Failed")
    st.stop()

st.set_page_config(page_title=PROJECT_TITLE, page_icon="▪️", layout="centered")

# ==========================================
# 🎨 CSS (High Contrast & Material Icons)
# ==========================================
st.markdown(f"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />

<style>
    /* 1. ベースデザイン */
    .stApp {{
        background-color: #121212;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }}
    
    .block-container {{ 
        padding-top: 2rem !important; 
        padding-bottom: 5rem !important; 
        max-width: 600px !important; 
    }}

    /* 2. タイトル */
    .custom-title {{
        font-size: 20px !important;
        font-weight: 700;
        margin-bottom: 24px;
        color: #E0E0E0;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        border-left: 3px solid #E0E0E0;
        padding-left: 12px;
    }}
    
    /* 3. スタッツバー (センター揃え・バランス調整) */
    .stats-bar {{
        display: flex; 
        justify-content: space-around; /* 均等配置 */
        align-items: center;
        background: #1E1E1E;
        border: none;
        padding: 16px 0px; /* 左右のパディングをなくしspace-aroundに任せる */
        border-radius: 4px;
        margin-bottom: 30px;
    }}
    .stats-item {{ 
        text-align: center; /* 文字を中央揃え */
        flex: 1; 
        border-right: 1px solid #333; /* 区切り線 */
    }}
    .stats-item:last-child {{ border-right: none; }}
    
    .stats-label {{ 
        font-size: 10px; 
        color: #888; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
        display: block; 
        margin-bottom: 6px;
    }}
    .stats-value {{ 
        font-size: 18px; 
        font-weight: 600; 
        color: #F0F0F0; /* より明るく */
        display: block; 
        font-family: 'Courier New', monospace;
    }}
    
    /* 4. チェックボックス (マージン調整) */
    div[data-testid="stCheckbox"] {{
        min-height: auto;
        margin-bottom: -14px !important; 
        padding: 0px;
    }}
    div[data-testid="stCheckbox"] label {{
        font-size: 15px;
        color: #D0D0D0;
        line-height: 1.5;
        padding-top: 4px;
    }}

    /* 5. 曲ヘッダー (完全シンメトリー & 余白圧縮) */
    .song-header {{
        font-size: 14px;
        font-weight: 700;
        color: #999; /* 少し明るく */
        margin-top: 20px;    /* 上 */
        margin-bottom: 20px; /* 下 (上下同じ値でバランスをとる) */
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .custom-hr {{
        border: 0;
        height: 1px;
        background: #333;
        margin-top: 0px;
        margin-bottom: 8px;
    }}
    
    /* 6. 日付メタデータ (アイコン調整) */
    .task-meta {{
        font-family: 'Helvetica Neue', Arial, sans-serif; /* アイコンと相性の良いフォントへ */
        font-size: 11px !important;
        margin-left: 28px; 
        margin-bottom: 12px;
        display: flex;
        align-items: center; /* アイコンと文字の垂直位置合わせ */
        gap: 4px; /* アイコンと文字の間隔 */
    }}
    
    /* アイコン用クラス (Material Symbols) */
    .material-symbols-outlined {{
        font-size: 14px !important; /* 文字より少し大きく */
        vertical-align: bottom;
    }}

    /* タブのスタイル */
    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        color: #666 !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        border-radius: 0px !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: #FFF !important;
        border-bottom: 2px solid #FFF !important;
    }}

    /* 不要要素の削除 */
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# メイン画面
# ---------------------------

st.markdown(f'<div class="custom-title">{PROJECT_TITLE}</div>', unsafe_allow_html=True)

# ⏰ タイマー：視認性向上版
server_now_ms = int(datetime.now(tz).timestamp() * 1000)
timer_html_code = f"""
<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
<style>
    body {{ 
        margin: 0; padding: 0; 
        background: transparent; 
        display: flex; flex-direction: column; align-items: flex-start;
    }}
    .timer-container {{
        width: 100%;
        margin-bottom: 10px;
    }}
    .timer-label {{
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 9px;
        color: #888;
        letter-spacing: 1px;
        margin-bottom: 2px;
        text-transform: uppercase;
        display: flex; align-items: center; gap: 4px;
    }}
    .timer-display {{
        font-family: 'Courier New', monospace;
        font-size: 28px;
        font-weight: 700;
        color: #E0E0E0;
        letter-spacing: 2px;
    }}
    .danger-mode {{ color: #FF5252 !important; }} 
    
    /* ターゲット日付の視認性改善 */
    .deadline-display {{
        font-family: 'Courier New', monospace;
        font-size: 11px;
        color: #9E9E9E; /* 背景に埋もれない明るめのグレー */
        margin-top: 6px;
        display: flex; align-items: center; gap: 4px;
    }}
    .material-symbols-outlined {{ font-size: 12px; }}
</style>
</head>
<body>
    <div class="timer-container">
        <div class="timer-label"><span class="material-symbols-outlined">hourglass_empty</span> TIME REMAINING</div>
        <div id="countdown-text" class="timer-display">--:--:--</div>
        <div class="deadline-display">
            <span class="material-symbols-outlined">flag</span> TARGET: {DEADLINE_STR}
        </div>
    </div>

    <script>
    (function() {{
        const serverTime = {server_now_ms}; 
        const deadline = new Date("{DEADLINE_ISO}");
        const localTime = Date.now();
        const timeOffset = serverTime - localTime; 
        const display = document.getElementById("countdown-text");

        function updateTimer() {{
            const now = new Date(Date.now() + timeOffset);
            const diff = deadline - now;

            if (diff <= 0) {{
                display.innerHTML = "00:00:00";
                display.className = "timer-display danger-mode";
                return;
            }}

            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            const hStr = String(hours).padStart(2, '0');
            const mStr = String(minutes).padStart(2, '0');
            const sStr = String(seconds).padStart(2, '0');
            
            if (hours < 6) {{
                 if (!display.classList.contains("danger-mode")) {{
                    display.classList.add("danger-mode");
                }}
            }} else {{
                display.classList.remove("danger-mode");
            }}

            display.innerHTML = hStr + ":" + mStr + ":" + sStr;
        }}
        setInterval(updateTimer, 1000); updateTimer();
    }})();
    </script>
</body>
</html>
"""
components.html(timer_html_code, height=100)

# --- スタッツ (センター揃え) ---
if not df.empty and "完了" in df.columns:
    total_tasks = len(df)
    completed_tasks = len(df[df["完了"].astype(str).str.upper() == "TRUE"])
    rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    st.markdown(f"""
    <div class="stats-bar">
        <div class="stats-item">
            <span class="stats-label">TASKS</span>
            <span class="stats-value">{total_tasks}</span>
        </div>
        <div class="stats-item">
            <span class="stats-label">DONE</span>
            <span class="stats-value">{completed_tasks}</span>
        </div>
        <div class="stats-item">
            <span class="stats-label">COMPLETED</span>
            <span class="stats-value">{rate}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- タスクリスト (Webアイコン対応) ---
if not df.empty and "曲名" in df.columns:
    formal_song_names = df["曲名"].unique()
    
    if len(formal_song_names) > 0:
        tab_labels = [song_map_db.get(name, name) for name in formal_song_names]
        tabs = st.tabs(tab_labels)
        
        for i, formal_name in enumerate(formal_song_names):
            with tabs[i]:
                # ソングヘッダー (余白調整済み)
                st.markdown(f'<div class="song-header">{formal_name}</div><hr class="custom-hr">', unsafe_allow_html=True)
                
                song_tasks = df[df["曲名"] == formal_name]
                song_tasks = song_tasks.sort_values(by="完了", ascending=True)
                
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"[{row['担当']}]" if row['担当'] else ""
                    task_text = row['タスク名']
                    
                    # 1行目
                    if is_done:
                        label = f"<span style='color:#555;'>{person} {task_text}</span>"
                    else:
                        label = f"{person} {task_text}"
                    
                    md_label = f"~~{person} {task_text}~~" if is_done else f"**{person} {task_text}**"
                    new_status = st.checkbox(md_label, value=is_done, key=f"t_{index}")

                    # 2行目：アイコン付きメタデータ
                    meta_html = ""
                    if is_done and "完了日時" in row and str(row["完了日時"]).strip() != "":
                         try:
                            d = datetime.strptime(str(row["完了日時"]), '%Y-%m-%d %H:%M:%S')
                            short_date = d.strftime('%m/%d %H:%M')
                            # 緑のチェックアイコン + 明るめのグレー文字
                            meta_html = f'''
                            <div class="task-meta" style="color:#666;">
                                <span class="material-symbols-outlined" style="font-size:14px; color:#4CAF50;">check_circle</span>
                                FINISHED {short_date}
                            </div>
                            '''
                         except:
                            meta_html = '<div class="task-meta">FINISHED</div>'
                    elif not is_done and "期限" in row and str(row["期限"]).strip() != "":
                         # 赤いアラートアイコン + 明るい赤文字 (#FF5252)
                         # コントラスト比を高めて視認性を確保
                         meta_html = f'''
                         <div class="task-meta" style="color:#FF5252;">
                             <span class="material-symbols-outlined" style="font-size:14px;">event_busy</span>
                             DUE {row["期限"]}
                         </div>
                         '''
                    
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
                with st.expander("ADD TASK"):
                    with st.form(key=f"add_{i}", clear_on_submit=True):
                        new_task = st.text_input("TASK NAME")
                        task_deadline = st.text_input("DUE DATE (ex. 1/20)")
                        new_person = st.selectbox("ASSIGN", ["-", "三好", "梅澤", "2人"])
                        
                        if st.form_submit_button("ADD", use_container_width=True):
                            if new_task:
                                p_val = new_person if new_person != "-" else ""
                                sheet.append_row([formal_name, new_task, p_val, "FALSE", task_deadline, ""])
                                st.success("ADDED")
                                time.sleep(0.5)
                                st.rerun()

                # 削除エリア
                with st.expander("DELETE"):
                    if len(song_tasks) > 0:
                        with st.form(key=f"del_form_{i}"):
                            rows_to_delete = []
                            for idx, row in song_tasks.iterrows():
                                if st.checkbox(f"{row['タスク名']}", key=f"del_chk_{idx}"):
                                    rows_to_delete.append(idx + 2)
                            
                            if st.form_submit_button("DELETE SELECTED", type="primary", use_container_width=True):
                                if rows_to_delete:
                                    rows_to_delete.sort(reverse=True)
                                    for r in rows_to_delete:
                                        sheet.delete_rows(r)
                                    st.success("DELETED")
                                    st.rerun()
    else:
        st.info("NO SONG DATA")
else:
    st.error("DB CONNECTION ERROR")
