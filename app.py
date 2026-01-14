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
# 🎨 CSS (Pro Gear Aesthetics)
# ==========================================
st.markdown(f"""
<style>
    /* 1. 全体のトーン＆マナー：マットなダークグレー */
    .stApp {{
        background-color: #121212; /* 完全な黒ではなく、深みのあるグレー */
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }}
    
    /* 2. コンテナ幅と余白の厳密な制御 */
    .block-container {{ 
        padding-top: 2rem !important; 
        padding-bottom: 5rem !important; 
        max-width: 600px !important; 
    }}

    /* 3. タイトル：装飾排除、ソリッドな白 */
    .custom-title {{
        font-size: 20px !important;
        font-weight: 700;
        margin-bottom: 24px;
        color: #E0E0E0; /* 眩しすぎないオフホワイト */
        letter-spacing: 0.05em;
        text-transform: uppercase; /* プロ機材っぽく大文字に */
        border-left: 3px solid #E0E0E0; /* 左に小さなアクセントバーのみ */
        padding-left: 12px;
    }}
    
    /* 4. スタッツバー：メーターブリッジ風 */
    .stats-bar {{
        display: flex; justify-content: space-between;
        background: #1E1E1E; /* 背景より一段階明るいグレー */
        border: none;
        padding: 16px 20px;
        border-radius: 4px; /* 角丸は最小限に */
        margin-bottom: 30px;
    }}
    .stats-item {{ text-align: left; flex: 1; }}
    .stats-label {{ 
        font-size: 9px; 
        color: #666; 
        text-transform: uppercase; 
        letter-spacing: 1px; 
        display: block; 
        margin-bottom: 4px;
    }}
    .stats-value {{ 
        font-size: 16px; 
        font-weight: 500; 
        color: #DDD;
        display: block; 
        font-family: 'Courier New', monospace; /* 数字は等幅で */
    }}
    
    /* 5. チェックボックス：徹底的にミニマルに */
    div[data-testid="stCheckbox"] {{
        min-height: auto;
        margin-bottom: -12px !important; /* 日付との距離感 */
        padding: 0px;
    }}
    div[data-testid="stCheckbox"] label {{
        font-size: 15px;
        color: #D0D0D0;
        line-height: 1.5;
        padding-top: 4px;
    }}
    /* チェックボックスの四角い箱自体の色調整（Streamlitの仕様上限界はあるが極力馴染ませる） */
    div[data-testid="stCheckbox"] span[role="checkbox"] {{
        border-color: #444;
    }}

    /* 6. 曲ヘッダー：セパレーター */
    .song-header {{
        font-size: 14px;
        font-weight: 700;
        color: #888;
        margin-top: 30px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    .custom-hr {{
        border: 0;
        height: 1px;
        background: #333;
        margin-top: 0px;
        margin-bottom: 12px;
    }}
    
    /* 7. 日付メタデータ：2行目用スタイル */
    .task-meta {{
        font-family: 'Courier New', monospace; /* 等幅フォントで「データ感」を出す */
        font-size: 10px !important;
        margin-left: 28px; 
        margin-bottom: 12px;
        color: #555; /* 普段は目立たないように */
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }}
    
    /* タブのスタイル：シンプルに */
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

# ⏰ タイマー：タイムコードディスプレイ風
server_now_ms = int(datetime.now(tz).timestamp() * 1000)
timer_html_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ 
        margin: 0; padding: 0; 
        background: transparent; 
        display: flex; flex-direction: column; align-items: flex-start; /* 左寄せ */
    }}
    .timer-container {{
        width: 100%;
        margin-bottom: 10px;
    }}
    .timer-label {{
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 9px;
        color: #666;
        letter-spacing: 1px;
        margin-bottom: 2px;
        text-transform: uppercase;
    }}
    .timer-display {{
        font-family: 'Courier New', monospace;
        font-size: 28px;
        font-weight: 700;
        color: #E0E0E0;
        letter-spacing: 2px;
        /* デジタル時計特有の「光」ではなく「物質感」を出すためノーエフェクト */
    }}
    .danger-mode {{ color: #D32F2F !important; }} /* マットな赤 */
    
    .deadline-display {{
        font-family: 'Courier New', monospace;
        font-size: 10px;
        color: #444;
        margin-top: 4px;
    }}
</style>
</head>
<body>
    <div class="timer-container">
        <div class="timer-label">TIME REMAINING</div>
        <div id="countdown-text" class="timer-display">--:--:--</div>
        <div class="deadline-display">TARGET: {DEADLINE_STR}</div>
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

            // タイムコード風のゼロ埋め
            const hStr = String(hours).padStart(2, '0');
            const mStr = String(minutes).padStart(2, '0');
            const sStr = String(seconds).padStart(2, '0');
            
            // 6時間切ったら赤くなる
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

# --- スタッツ：メーターブリッジ風 ---
if not df.empty and "完了" in df.columns:
    total_tasks = len(df)
    completed_tasks = len(df[df["完了"].astype(str).str.upper() == "TRUE"])
    rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
    
    # 進行度バーの代わりにシンプルな数値表示
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

# --- タスクリスト（2行レイアウト・ミニマルデザイン） ---
if not df.empty and "曲名" in df.columns:
    formal_song_names = df["曲名"].unique()
    
    if len(formal_song_names) > 0:
        tab_labels = [song_map_db.get(name, name) for name in formal_song_names]
        tabs = st.tabs(tab_labels)
        
        for i, formal_name in enumerate(formal_song_names):
            with tabs[i]:
                # ソングヘッダー
                st.markdown(f'<div class="song-header">{formal_name}</div><hr class="custom-hr">', unsafe_allow_html=True)
                
                song_tasks = df[df["曲名"] == formal_name]
                song_tasks = song_tasks.sort_values(by="完了", ascending=True)
                
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"[{row['担当']}]" if row['担当'] else "" # 【】をやめて [] にしてcodeっぽく
                    task_text = row['タスク名']
                    
                    # 1行目：タスク名
                    if is_done:
                        # 完了時は色を落として目立たなくする
                        label = f"<span style='color:#555;'>{person} {task_text}</span>"
                    else:
                        label = f"{person} {task_text}"
                    
                    # チェックボックス（HTML可ラベルは使えないので、Markdownで擬似的にスタイル適用）
                    # ※Streamlitの仕様上、打ち消し線はMarkdownの ~~text~~ でやる必要がある
                    md_label = f"~~{person} {task_text}~~" if is_done else f"**{person} {task_text}**"
                    new_status = st.checkbox(md_label, value=is_done, key=f"t_{index}")

                    # 2行目：メタデータ（絵文字なし、テキストのみ、等幅フォント）
                    meta_html = ""
                    if is_done and "完了日時" in row and str(row["完了日時"]).strip() != "":
                         try:
                            d = datetime.strptime(str(row["完了日時"]), '%Y-%m-%d %H:%M:%S')
                            short_date = d.strftime('%m/%d %H:%M')
                            # 完了ログは極めて薄く表示（ノイズを減らす）
                            meta_html = f'<div class="task-meta" style="color:#444;">FINISHED AT {short_date}</div>'
                         except:
                            meta_html = '<div class="task-meta" style="color:#444;">FINISHED</div>'
                    elif not is_done and "期限" in row and str(row["期限"]).strip() != "":
                         # 期限は重要な情報なので、少しだけ色を入れるが、彩度は落とす
                         # #D32F2F (Matte Red)
                         meta_html = f'<div class="task-meta" style="color:#D32F2F;">DUE {row["期限"]}</div>'
                    
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
                
                # 追加エリア（ミニマルに）
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
