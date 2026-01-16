import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import gspread
from google.oauth2.service_account import Credentials
import json
import time
import requests
import streamlit.components.v1 as components

# ==========================================
# 🛠 接続設定
# ==========================================
@st.cache_resource(ttl=600)
def init_connection():
    key_dict = json.loads(st.secrets["gcp_service_account"]["info"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(key_dict, scopes=scopes)
    client = gspread.authorize(creds)
    wb = client.open("CoWrite_DB")
    return wb

# マルチプロジェクト対応のデータ読み込み
def load_data():
    wb = init_connection()
    
    # 1. Configシート（プロジェクト一覧）の取得
    project_list = []
    try:
        config_sheet = wb.worksheet("Config")
        # 全データを辞書リストとして取得 [{'ProjectName': '...', 'Deadline': '...'}, ...]
        project_list = config_sheet.get_all_records()
    except:
        pass

    # 2. 曲名マッピング
    song_map = {}
    try:
        songs_sheet = wb.worksheet("Songs")
        songs_records = songs_sheet.get_all_records()
        for item in songs_records:
            if item['FormalName'] and item['ShortName']:
                song_map[item['FormalName']] = item['ShortName']
    except:
        pass

    # 3. タスクデータ
    main_sheet = wb.sheet1
    main_data = main_sheet.get_all_records()
    
    return project_list, song_map, main_data, main_sheet

# 🔔 通知機能
def send_discord_notification(message):
    try:
        if "discord_webhook" not in st.secrets: return
        webhook_url = st.secrets["discord_webhook"]
        requests.post(webhook_url, json={"content": message})
    except: pass

# ---------------------------
# データ処理 & 優先プロジェクト決定
# ---------------------------
try:
    project_list, song_map_db, data, sheet = load_data()
    df = pd.DataFrame(data)

    tz = pytz.timezone('Asia/Tokyo')
    now_py = datetime.now(tz)

    # === 🔥 一番近い締め切りを探すロジック ===
    target_project = "No Active Project"
    target_deadline_str = "---"
    target_timestamp = 0
    
    min_diff = float('inf') # 無限大で初期化

    for p in project_list:
        p_name = p.get("ProjectName", "")
        p_date = str(p.get("Deadline", ""))
        
        if p_name and p_date:
            try:
                # 日付解析
                clean = p_date.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)})).replace('/', '-').strip()
                if ':' not in clean: clean += ' 23:59'
                try: dt = datetime.strptime(clean, '%Y-%m-%d %H:%M:%S')
                except: dt = datetime.strptime(clean, '%Y-%m-%d %H:%M')
                
                dt_aware = tz.localize(dt)
                diff = dt_aware.timestamp() - now_py.timestamp()

                # 未来の締め切り、かつ一番近いものを採用
                # (もし全部過去なら、一番直近の過去を表示する)
                if diff > -86400: # 1日以上前の過去は無視
                    if diff < min_diff:
                        min_diff = diff
                        target_project = p_name
                        target_deadline_str = dt_aware.strftime('%Y-%m-%d %H:%M')
                        target_timestamp = int(dt_aware.timestamp() * 1000)
            except:
                continue
    
    # 有効なプロジェクトがなかった場合のフォールバック
    if target_timestamp == 0:
        target_timestamp = int(now_py.timestamp() * 1000)

except Exception as e:
    st.error(f"System Error: {e}")
    st.stop()

st.set_page_config(page_title=target_project, page_icon="▪️", layout="centered")

# ==========================================
# 🎨 UI表示
# ==========================================
st.markdown(f"""
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
    .stApp {{ background-color: #121212; font-family: 'Inter', sans-serif; }}
    .custom-title {{
        font-size: 20px !important; font-weight: 700; margin-bottom: 24px; color: #E0E0E0;
        letter-spacing: 0.05em; text-transform: uppercase; border-left: 3px solid #E0E0E0; padding-left: 12px;
    }}
    /* その他CSSは省略せず維持 */
    .song-header {{ font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 700; color: #999; margin-top: 20px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 0.05em; }}
    .custom-hr {{ border: 0; height: 1px; background: #333; margin-top: 0px; margin-bottom: 8px; }}
    .task-meta {{ font-family: 'Inter', sans-serif; font-size: 11px !important; margin-left: 28px; margin-bottom: 12px; display: flex; align-items: center; gap: 5px; font-weight: 500; }}
    div[data-testid="stCheckbox"] label p {{ font-family: 'Inter', sans-serif !important; font-size: 15px !important; font-weight: 500 !important; color: #D0D0D0 !important; }}
    button[data-baseweb="tab"] {{ background-color: transparent !important; color: #666 !important; font-size: 12px !important; font-weight: 600 !important; padding: 8px 16px !important; border-radius: 0px !important; }}
    button[data-baseweb="tab"][aria-selected="true"] {{ color: #FFF !important; border-bottom: 2px solid #FFF !important; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

st.markdown(f'<div class="custom-title">{target_project}</div>', unsafe_allow_html=True)

# ⏰ タイマー (一番近い締め切りを表示)
components.html(f"""
<!DOCTYPE html>
<html>
<head>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
<link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>
    body {{ margin: 0; padding: 0; background: transparent; display: flex; flex-direction: column; align-items: flex-start; }}
    .timer-container {{ width: 100%; margin-bottom: 10px; }}
    .timer-label {{ font-family: 'Inter', sans-serif; font-size: 9px; color: #888; letter-spacing: 1px; margin-bottom: 2px; text-transform: uppercase; display: flex; align-items: center; gap: 4px; }}
    .timer-display {{ font-family: 'Roboto Mono', monospace; font-size: 28px; font-weight: 700; color: #E0E0E0; letter-spacing: 2px; }}
    .danger-mode {{ color: #FF5252 !important; text-shadow: 0 0 15px rgba(255, 82, 82, 0.4); }} 
    .deadline-display {{ font-family: 'Roboto Mono', monospace; font-size: 11px; color: #9E9E9E; margin-top: 6px; display: flex; align-items: center; gap: 4px; }}
    .material-symbols-outlined {{ font-size: 13px; }}
</style>
</head>
<body>
    <div class="timer-container">
        <div class="timer-label"><span class="material-symbols-outlined">timer</span> TIME REMAINING</div>
        <div id="countdown-text" class="timer-display">--:--:--</div>
        <div class="deadline-display"><span class="material-symbols-outlined">flag</span> TARGET: {target_deadline_str}</div>
    </div>
    <script>
    (function() {{
        const targetTime = {target_timestamp};
        const display = document.getElementById("countdown-text");
        function tick() {{
            const now = Date.now();
            const diff = targetTime - now;
            if (diff <= 0) {{ display.innerHTML = "00:00:00"; display.className = "timer-display danger-mode"; return; }}
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);
            if (hours < 6) {{ if (!display.classList.contains("danger-mode")) {{ display.classList.add("danger-mode"); }} }} else {{ display.classList.remove("danger-mode"); }}
            display.innerHTML = String(hours).padStart(2,'0') + ":" + String(minutes).padStart(2,'0') + ":" + String(seconds).padStart(2,'0');
            requestAnimationFrame(tick);
        }}
        tick();
    }})();
    </script>
</body>
</html>
""", height=100)

# --- スタッツ (変更なし) ---
if not df.empty and "完了" in df.columns:
    total_tasks = len(df)
    completed_tasks = len(df[df["完了"].astype(str).str.upper() == "TRUE"])
    rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; background:#1E1E1E; border-radius:4px; padding:0; margin-bottom:30px;">
        <div style="flex:1; text-align:center; padding:16px 0; border-right:1px solid #333;"><div style="font-size:10px; color:#888;">TASKS</div><div style="font-family:'Roboto Mono'; font-size:18px; color:#F0F0F0;">{total_tasks}</div></div>
        <div style="flex:1; text-align:center; padding:16px 0; border-right:1px solid #333;"><div style="font-size:10px; color:#888;">DONE</div><div style="font-family:'Roboto Mono'; font-size:18px; color:#F0F0F0;">{completed_tasks}</div></div>
        <div style="flex:1; text-align:center; padding:16px 0;"><div style="font-size:10px; color:#888;">COMPLETED</div><div style="font-family:'Roboto Mono'; font-size:18px; color:#F0F0F0;">{rate}%</div></div>
    </div>
    """, unsafe_allow_html=True)

# --- タスクリスト (変更なし) ---
if not df.empty and "曲名" in df.columns:
    formal_song_names = df["曲名"].unique()
    if len(formal_song_names) > 0:
        tab_labels = [song_map_db.get(name, name) for name in formal_song_names]
        tabs = st.tabs(tab_labels)
        
        for i, formal_name in enumerate(formal_song_names):
            with tabs[i]:
                st.markdown(f'<div class="song-header">{formal_name}</div><hr class="custom-hr">', unsafe_allow_html=True)
                song_tasks = df[df["曲名"] == formal_name].sort_values(by="完了", ascending=True)
                
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"[{row['担当']}]" if row['担当'] else ""
                    task_text = row['タスク名']
                    md_label = f"~~{person} {task_text}~~" if is_done else f"**{person} {task_text}**"
                    new_status = st.checkbox(md_label, value=is_done, key=f"t_{index}")

                    # メタデータ(完了日時・期限)の表示処理
                    meta_html = ""
                    if is_done and "完了日時" in row and str(row["完了日時"]).strip() != "":
                         try:
                            d = datetime.strptime(str(row["完了日時"]), '%Y-%m-%d %H:%M:%S')
                            meta_html = f'<div class="task-meta" style="color:#444;"><span class="material-symbols-outlined" style="font-size:14px; color:#4CAF50;">check_circle</span> FINISHED {d.strftime("%m/%d %H:%M")}</div>'
                         except: pass
                    elif not is_done and "期限" in row and str(row["期限"]).strip() != "":
                         limit_str = str(row["期限"])
                         try:
                             clean_limit = limit_str.translate(str.maketrans({chr(0xFF01 + i): chr(0x21 + i) for i in range(94)})).replace('/', '-').strip()
                             if ':' not in clean_limit: clean_limit += ' 23:59'
                             limit_dt = tz.localize(datetime.strptime(clean_limit, '%Y-%m-%d %H:%M' if len(clean_limit) <= 16 else '%Y-%m-%d %H:%M:%S'))
                             total_seconds = (limit_dt - now_py).total_seconds()
                             if total_seconds < 0: meta_html = f'<div class="task-meta" style="color:#FF5252;"><span class="material-symbols-outlined">local_fire_department</span> OVERDUE ({limit_str})</div>'
                             elif total_seconds < 3600: meta_html = f'<div class="task-meta" style="color:#FF9100;"><span class="material-symbols-outlined">priority_high</span> DUE SOON ({limit_str})</div>'
                             elif total_seconds < 3600*3: meta_html = f'<div class="task-meta" style="color:#FFD740;"><span class="material-symbols-outlined">warning</span> DUE ({limit_str})</div>'
                             else: meta_html = f'<div class="task-meta" style="color:#D84315;"><span class="material-symbols-outlined">event</span> DUE {limit_str}</div>'
                         except: meta_html = f'<div class="task-meta" style="color:#D84315;"><span class="material-symbols-outlined">event</span> DUE {limit_str}</div>'
                    if meta_html: st.markdown(meta_html, unsafe_allow_html=True)

                    if new_status != is_done:
                        sheet.update_cell(index + 2, 4, "TRUE" if new_status else "FALSE")
                        if new_status:
                            now_str = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                            sheet.update_cell(index + 2, 6, now_str)
                            msg = f"✅ **{person} {task_text}** が完了しました！\n(Song: {formal_name})"
                            send_discord_notification(msg)
                        else:
                            sheet.update_cell(index + 2, 6, "")
                            msg = f"↩️ **{person} {task_text}** が未完了に戻されました。\n(Song: {formal_name})"
                            send_discord_notification(msg)
                        st.rerun()
                
                st.write("") 
                with st.expander("ADD TASK"):
                    with st.form(key=f"add_{i}", clear_on_submit=True):
                        new_task = st.text_input("TASK NAME")
                        task_deadline = st.text_input("DUE DATE")
                        new_person = st.selectbox("ASSIGN", ["-", "三好", "梅澤", "2人"])
                        if st.form_submit_button("ADD", use_container_width=True):
                            if new_task:
                                p_val = new_person if new_person != "-" else ""
                                sheet.append_row([formal_name, new_task, p_val, "FALSE", task_deadline, ""])
                                msg = f"🆕 新しいタスク **[{p_val}] {new_task}** が追加されました！\n(Song: {formal_name} / Limit: {task_deadline})"
                                send_discord_notification(msg)
                                st.success("ADDED")
                                st.rerun()
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
                                    for r in rows_to_delete: sheet.delete_rows(r)
                                    st.success("DELETED")
                                    st.rerun()
    else: st.info("NO SONG DATA")
else: st.error("DB CONNECTION ERROR")
