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
    # ワークブックを開く
    wb = client.open("CoWrite_DB")
    return wb

# データ読み込み（ConfigとMainの両方を取得）
def load_data():
    wb = init_connection()
    # 1. Configシート（設定）読み込み
    try:
        config_sheet = wb.worksheet("Config")
        config_records = config_sheet.get_all_records()
        # リストを辞書に変換 {Key: Value}
        config = {item['Key']: item['Value'] for item in config_records}
    except:
        # シートがない場合のフォールバック
        config = {"ProjectTitle": "設定読み込みエラー", "Deadline": "2026-01-01 00:00"}

    # 2. Mainシート（タスク）読み込み
    main_sheet = wb.sheet1
    main_data = main_sheet.get_all_records()
    
    return config, main_data, main_sheet

# ---------------------------
# データの取得 & 初期設定
# ---------------------------
try:
    config, data, sheet = load_data()
    df = pd.DataFrame(data)

    # Configからタイトルと締め切りを取得
    PROJECT_TITLE = config.get("ProjectTitle", "無題のプロジェクト")
    DEADLINE_STR = config.get("Deadline", "2026-01-01 00:00")
    
    # 締め切りをISO形式に変換（JS用）
    tz = pytz.timezone('Asia/Tokyo')
    try:
        # 入力が "2026-01-14 23:59" のような形式と想定
        dt_obj = datetime.strptime(str(DEADLINE_STR), '%Y-%m-%d %H:%M')
        dt_obj = tz.localize(dt_obj)
        DEADLINE_ISO = dt_obj.isoformat()
    except:
        # 形式が違う場合のエラー回避
        DEADLINE_ISO = datetime.now(tz).isoformat()

except Exception as e:
    st.error("データベース接続エラー: ConfigシートまたはMainシートの形式を確認してください")
    st.stop()

# ページ設定
st.set_page_config(page_title=PROJECT_TITLE, page_icon="🦁", layout="centered")

# ==========================================
# 🎨 CSS (V10のデザインを維持)
# ==========================================
st.markdown(f"""
<style>
    .stApp {{ background-color: #0E1117; }}
    .block-container {{ padding-top: 2rem !important; padding-bottom: 5rem !important; max-width: 700px !important; }}
    .custom-title {{
        font-size: 28px !important; font-weight: 900; margin-bottom: 10px;
        background: linear-gradient(90deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 0.05em;
    }}
    /* スタッツバー */
    .stats-bar {{
        display: flex; justify-content: space-between;
        background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px; border-radius: 12px; margin-bottom: 20px; backdrop-filter: blur(10px);
    }}
    .stats-item {{ text-align: center; flex: 1; color: #E0E0E0; }}
    .stats-label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; display: block; }}
    .stats-value {{ font-size: 20px; font-weight: 700; display: block; }}
    
    /* タスクカード */
    div[data-testid="stCheckbox"] {{
        background-color: #1A1C24; padding: 12px 15px; border-radius: 8px;
        border-left: 4px solid #333; margin-bottom: 8px; transition: all 0.2s ease;
    }}
    div[data-testid="stCheckbox"]:hover {{ background-color: #262830; border-left: 4px solid #FF4B4B; }}
    
    /* タスク詳細情報の文字 */
    .task-meta {{ font-size: 12px; color: #666; margin-left: 28px; margin-bottom: 10px; display: block; }}
    .task-late {{ color: #FF4B4B; font-weight: bold; }}
    .task-early {{ color: #4CAF50; }}

    /* その他非表示 */
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# メイン画面表示
# ---------------------------

# タイトル
st.markdown(f'<div class="custom-title">{PROJECT_TITLE}</div>', unsafe_allow_html=True)

# ⏰ 時計コンポーネント
server_now_ms = int(datetime.now(tz).timestamp() * 1000)
timer_html_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ margin: 0; padding: 0; font-family: sans-serif; background: transparent; display: flex; flex-direction: column; align-items: center; }}
    .timer-box {{
        width: 100%; padding: 12px; border-radius: 12px;
        background: linear-gradient(135deg, #2b303b 0%, #20232a 100%);
        color: #fff; text-align: center; font-weight: 700; font-size: 20px;
        border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        font-variant-numeric: tabular-nums; letter-spacing: 1px;
    }}
    .deadline-date {{ text-align: center; font-size: 11px; color: #666; margin-top: 4px; }}
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
components.html(timer_html_code, height=90)

# 自動更新スイッチ
auto_refresh = st.toggle("Auto Refresh (30s)", value=False)
if auto_refresh:
    time.sleep(30)
    st.rerun()

st.write("")

# --- スタッツ表示 ---
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
    
    if rate == 100 and total_tasks > 0:
        st.balloons()
        st.success("🎉 MISSION COMPLETE!")

# --- タブ (DBから曲名を自動取得) ---
if not df.empty and "曲名" in df.columns:
    # 曲名の重複を除いてリスト化（出現順を維持したい場合は工夫が必要ですが、今回はuniqueで）
    song_list = df["曲名"].unique()
    
    if len(song_list) > 0:
        tabs = st.tabs(list(song_list))
        
        for i, song_name in enumerate(song_list):
            with tabs[i]:
                st.markdown(f"##### 🎵 {song_name}")
                
                # その曲のタスクのみ抽出
                song_tasks = df[df["曲名"] == song_name]
                # 完了順にソート
                song_tasks = song_tasks.sort_values(by="完了", ascending=True)
                
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"【{row['担当']}】" if row['担当'] else ""
                    task_text = row['タスク名']
                    
                    # 個別締め切り & 完了日時の表示用ロジック
                    meta_info = ""
                    # 期限がある場合
                    if "期限" in row and str(row["期限"]).strip() != "":
                        meta_info += f"📅 期限: {row['期限']} "
                    
                    # 完了している場合、完了日時を表示
                    if is_done and "完了日時" in row and str(row["完了日時"]).strip() != "":
                         meta_info += f"  ✅ 完了: {row['完了日時']}"
                    
                    # チェックボックス表示
                    label = f"~~{person} {task_text}~~" if is_done else f"**{person} {task_text}**"
                    new_status = st.checkbox(label, value=is_done, key=f"t_{index}")
                    
                    # メタ情報（期限など）を小さく表示
                    if meta_info:
                        st.markdown(f'<span class="task-meta">{meta_info}</span>', unsafe_allow_html=True)

                    # --- 更新処理 ---
                    if new_status != is_done:
                        # 4列目: 完了フラグ
                        sheet.update_cell(index + 2, 4, "TRUE" if new_status else "FALSE")
                        
                        # 6列目: 完了日時 (F列)
                        if new_status:
                            # チェック入れたら現在時刻を書き込む
                            now_str = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                            sheet.update_cell(index + 2, 6, now_str)
                        else:
                            # チェック外したら日時を消す
                            sheet.update_cell(index + 2, 6, "")
                            
                        st.rerun()
                
                st.write("---")
                
                # 追加エリア（曲名は自動固定）
                with st.expander("➕ Add New Task"):
                    with st.form(key=f"add_{i}", clear_on_submit=True):
                        c1, c2 = st.columns([2, 1])
                        with c1:
                            new_task = st.text_input("Task Name")
                        with c2:
                             # 期限入力（任意）
                            task_deadline = st.text_input("Deadline (例 1/20 15:00)")
                        
                        PERSON_OPTIONS = ["-", "三好", "梅澤", "2人"]
                        new_person = st.selectbox("Person", PERSON_OPTIONS)
                        
                        if st.form_submit_button("ADD", use_container_width=True):
                            if new_task:
                                p_val = new_person if new_person != "-" else ""
                                # 曲名, タスク名, 担当, 完了, 期限, 完了日時(空)
                                sheet.append_row([song_name, new_task, p_val, "FALSE", task_deadline, ""])
                                st.success("Added!")
                                time.sleep(0.5)
                                st.rerun()

                # 削除エリア
                with st.expander("🗑️ Delete Tasks"):
                    if len(song_tasks) > 0:
                        with st.form(key=f"del_form_{i}"):
                            rows_to_delete = []
                            for idx, row in song_tasks.iterrows():
                                if st.checkbox(f"{row['タスク名']}", key=f"del_chk_{idx}"):
                                    rows_to_delete.append(idx + 2)
                            
                            if st.form_submit_button("DELETE SELECTED", type="primary"):
                                if rows_to_delete:
                                    rows_to_delete.sort(reverse=True)
                                    for r in rows_to_delete:
                                        sheet.delete_rows(r)
                                    st.success("Deleted!")
                                    st.rerun()
    else:
        st.info("DBに曲が登録されていません。スプレッドシートに追加してください。")
else:
    st.error("データ読み込みエラー")
