import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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
# データ取得 & 初期設定
# ---------------------------
# ボタンが押されたらリロードするためにcacheをクリアする手もあるが、
# 単純に再実行で最新を取る形にする
try:
    config, song_map_db, data, sheet = load_data()
    df = pd.DataFrame(data)

    PROJECT_TITLE = config.get("ProjectTitle", "Co-Write Task")
    DEADLINE_STR = config.get("Deadline", "2026-01-01 00:00")
    
    tz = pytz.timezone('Asia/Tokyo')
    now_py = datetime.now(tz) # Python側の現在時刻

    # 締め切り日時の解析
    try:
        dt_obj = datetime.strptime(str(DEADLINE_STR), '%Y-%m-%d %H:%M')
        dt_obj = tz.localize(dt_obj)
        DEADLINE_ISO = dt_obj.isoformat()
    except:
        # エラー時は現在時刻を入れて00:00:00にする
        dt_obj = now_py
        DEADLINE_ISO = now_py.isoformat()

except Exception as e:
    st.error("System Error: DB Connection Failed")
    st.stop()

st.set_page_config(page_title=PROJECT_TITLE, page_icon="▪️", layout="centered")

# ==========================================
# 🎨 CSS (フォント強制適用 & デザイン調整)
# ==========================================
st.markdown(f"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">

<style>
    /* 1. ベースフォント設定（全体をかっこよく） */
    .stApp {{
        background-color: #121212;
        font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    }}
    
    .block-container {{ 
        padding-top: 1.5rem !important; 
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
        display: flex; justify-content: space-between; align-items: center;
    }}
    
    /* 3. チェックボックスのフォント強制変更 (ここが重要！) */
    div[data-testid="stCheckbox"] label p {{
        font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif !important;
        font-size: 15px !important;
        font-weight: 500 !important; /* 少し太くして視認性アップ */
        color: #D0D0D0 !important;
        line-height: 1.5 !important;
    }}
    div[data-testid="stCheckbox"] {{
        margin-bottom: -14px !important; 
    }}

    /* 4. スタッツバー */
    .stats-bar {{
        display: flex; justify-content: space-around; align-items: center;
        background: #1E1E1E; border: none;
        padding: 16px 0px; margin-bottom: 30px; border-radius: 4px;
    }}
    .stats-item {{ text-align: center; flex: 1; border-right: 1px solid #333; }}
    .stats-item:last-child {{ border-right: none; }}
    .stats-label {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 6px; }}
    .stats-value {{ font-family: 'Roboto Mono', monospace; font-size: 18px; font-weight: 600; color: #F0F0F0; }}
    
    /* 5. 曲ヘッダー (シンメトリー) */
    .song-header {{
        font-family: 'Inter', sans-serif;
        font-size: 14px; font-weight: 700; color: #999;
        margin-top: 20px; margin-bottom: 20px;
        text-transform: uppercase; letter-spacing: 0.05em;
    }}
    .custom-hr {{ border: 0; height: 1px; background: #333; margin-top: 0px; margin-bottom: 8px; }}
    
    /* 6. メタデータ (日付・警告) */
    .task-meta {{
        font-family: 'Inter', sans-serif;
        font-size: 11px !important;
        margin-left: 28px; margin-bottom: 12px;
        display: flex; align-items: center; gap: 4px;
        font-weight: 500;
    }}
    .material-symbols-outlined {{ font-size: 14px !important; vertical-align: bottom; }}

    /* タブ */
    button[data-baseweb="tab"] {{ background-color: transparent !important; color: #666 !important; font-size: 12px !important; font-weight: 600 !important; padding: 8px 16px !important; border-radius: 0px !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color: #FFF !important; border-bottom: 2px solid #FFF !important; }}

    /* 更新ボタンのデザイン */
    div.stButton > button {{
        background-color: #1E1E1E; color: #888; border: 1px solid #333;
        font-size: 12px; padding: 4px 12px; border-radius: 4px;
    }}
    div.stButton > button:hover {{ color: #FFF; border-color: #555; background-color: #252525; }}

    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# メイン画面
# ---------------------------

# タイトルエリア（右側に更新ボタンを置くためのカラム分け）
c1, c2 = st.columns([0.8, 0.2])
with c1:
    st.markdown(f'<div class="custom-title">{PROJECT_TITLE}</div>', unsafe_allow_html=True)
with c2:
    # データを最新にするためのボタン
    if st.button("SYNC"):
        st.rerun()

# ⏰ タイマー：サーバー時間同期・完全版
server_now_ms = int(now_py.timestamp() * 1000)

timer_html_code = f"""
<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>
    body {{ 
        margin: 0; padding: 0; background: transparent; 
        display: flex; flex-direction: column; align-items: flex-start;
    }}
    .timer-container {{ width: 100%; margin-bottom: 10px; }}
    .timer-label {{
        font-family: 'Inter', sans-serif; font-size: 9px; color: #888; letter-spacing: 1px;
        margin-bottom: 2px; text-transform: uppercase; display: flex; align-items: center; gap: 4px;
    }}
    .timer-display {{
        font-family: 'Roboto Mono', monospace; font-size: 28px; font-weight: 700; color: #E0E0E0; letter-spacing: 2px;
    }}
    .danger-mode {{ color: #FF5252 !important; text-shadow: 0 0 10px rgba(255, 82, 82, 0.3); }} 
    
    .deadline-display {{
        font-family: 'Roboto Mono', monospace; font-size: 10px; color: #666; margin-top: 6px;
        display: flex; align-items: center; gap: 4px;
    }}
    .material-symbols-outlined {{ font-size: 12px; }}
</style>
</head>
<body>
    <div class="timer-container">
        <div class="timer-label"><span class="material-symbols-outlined">timer</span> TIME REMAINING</div>
        <div id="countdown-text" class="timer-display">--:--:--</div>
        <div class="deadline-display">
            <span class="material-symbols-outlined">flag</span> TARGET: {DEADLINE_STR}
        </div>
    </div>

    <script>
    (function() {{
        // Pythonから渡された「サーバー時刻」と「締め切り」
        const serverTime = {server_now_ms}; 
        const deadline = new Date("{DEADLINE_ISO}");
        
        // ページ読み込み時点でのローカル時間
        const localTime = Date.now();
        // ズレを計算 (サーバーが進んでれば正、遅れてれば負)
        const timeOffset = serverTime - localTime; 
        
        const display = document.getElementById("countdown-text");

        function updateTimer() {{
            // 現在時刻 = ローカル時刻 + ズレ (これでサーバー時刻になる)
            const now = new Date(Date.now() + timeOffset);
            const diff = deadline - now;

            // 締め切り過ぎた場合
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
            
            // 残り6時間で赤くする
            if (hours < 6) {{
                 if (!display.classList.contains("danger-mode")) {{
                    display.classList.add("danger-mode");
                }}
            }} else {{
                display.classList.remove("danger-mode");
            }}

            display.innerHTML = hStr + ":" + mStr + ":" + sStr;
        }}
        
        // 1秒ごとに更新
        setInterval(updateTimer, 1000); 
        updateTimer(); // 初回即実行
    }})();
    </script>
</body>
</html>
"""
components.html(timer_html_code, height=100)

# --- スタッツ ---
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

# --- タスクリスト ---
if not df.empty and "曲名" in df.columns:
    formal_song_names = df["曲名"].unique()
    
    if len(formal_song_names) > 0:
        tab_labels = [song_map_db.get(name, name) for name in formal_song_names]
        tabs = st.tabs(tab_labels)
        
        for i, formal_name in enumerate(formal_song_names):
            with tabs[i]:
                st.markdown(f'<div class="song-header">{formal_name}</div><hr class="custom-hr">', unsafe_allow_html=True)
                
                song_tasks = df[df["曲名"] == formal_name]
                song_tasks = song_tasks.sort_values(by="完了", ascending=True)
                
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"[{row['担当']}]" if row['担当'] else ""
                    task_text = row['タスク名']
                    
                    # 1行目：タスク名
                    if is_done:
                        label = f"<span style='color:#555;'>{person} {task_text}</span>"
                    else:
                        label = f"{person} {task_text}"
                    
                    md_label = f"~~{person} {task_text}~~" if is_done else f"**{person} {task_text}**"
                    new_status = st.checkbox(md_label, value=is_done, key=f"t_{index}")

                    # 2行目：メタデータ & 個別アラート判定
                    meta_html = ""
                    
                    # A. 完了している場合
                    if is_done and "完了日時" in row and str(row["完了日時"]).strip() != "":
                         try:
                            d = datetime.strptime(str(row["完了日時"]), '%Y-%m-%d %H:%M:%S')
                            short_date = d.strftime('%m/%d %H:%M')
                            meta_html = f'''
                            <div class="task-meta" style="color:#444;">
                                <span class="material-symbols-outlined" style="font-size:14px; color:#4CAF50;">check_circle</span>
                                FINISHED {short_date}
                            </div>
                            '''
                         except:
                            meta_html = '<div class="task-meta" style="color:#444;">FINISHED</div>'
                    
                    # B. 未完了で期限がある場合（ここがアラートロジック！）
                    elif not is_done and "期限" in row and str(row["期限"]).strip() != "":
                         limit_str = str(row["期限"]) # 例: 2026-1-17 20:00 (または 1/17 20:00)
                         
                         # 残り時間を計算して色を変える
                         try:
                             # フォーマット揺れに対応 (YYYY-MM-DD HH:MM または MM/DD HH:MM)
                             # 簡易的にパースを試みる
                             current_year = now_py.year
                             limit_dt = None
                             
                             # いくつかのパターンで日付パースを試す
                             patterns = ['%Y-%m-%d %H:%M', '%m/%d %H:%M', '%Y/%m/%d %H:%M']
                             for pat in patterns:
                                 try:
                                     limit_dt = datetime.strptime(limit_str, pat)
                                     # 年が省略されている場合は今年の年を付与
                                     if limit_dt.year == 1900: 
                                         limit_dt = limit_dt.replace(year=current_year)
                                     limit_dt = tz.localize(limit_dt)
                                     break
                                 except:
                                     continue
                             
                             if limit_dt:
                                 diff_task = limit_dt - now_py
                                 total_seconds = diff_task.total_seconds()
                                 
                                 if total_seconds < 0:
                                     # 期限切れ (赤 & 炎アイコン)
                                     meta_html = f'''
                                     <div class="task-meta" style="color:#FF5252;">
                                         <span class="material-symbols-outlined">local_fire_department</span>
                                         OVERDUE ({limit_str})
                                     </div>
                                     '''
                                 elif total_seconds < 3600 * 3: 
                                     # 3時間以内 (オレンジ & 警告アイコン)
                                     meta_html = f'''
                                     <div class="task-meta" style="color:#FFAB40;">
                                         <span class="material-symbols-outlined">warning</span>
                                         DUE SOON ({limit_str})
                                     </div>
                                     '''
                                 else:
                                     # 通常 (落ち着いた赤)
                                     meta_html = f'''
                                     <div class="task-meta" style="color:#D32F2F;">
                                         <span class="material-symbols-outlined">event</span>
                                         DUE {limit_str}
                                     </div>
                                     '''
                             else:
                                 # パースできなかった場合 (通常表示)
                                 meta_html = f'<div class="task-meta" style="color:#D32F2F;"><span class="material-symbols-outlined">event</span> DUE {limit_str}</div>'
                                 
                         except Exception as e:
                             # 計算エラー時も通常表示
                             meta_html = f'<div class="task-meta" style="color:#D32F2F;"><span class="material-symbols-outlined">event</span> DUE {limit_str}</div>'
                    
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
                        task_deadline = st.text_input("DUE DATE (ex. 2026-1-17 20:00)")
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
