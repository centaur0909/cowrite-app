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

st.set_page_config(page_title=PROJECT_TITLE, page_icon="🦁", layout="centered")

# ---------------------------
# 🎨 CSS: 演出強化 & スマホ最適化
# ---------------------------
hide_streamlit_style = """
<style>
    /* 基本設定 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 5rem !important;
        max-width: 100% !important;
    }

    /* タイトル */
    .custom-title {
        font-size: 24px !important;
        font-weight: 800;
        margin-bottom: 5px;
        background: -webkit-linear-gradient(45deg, #FF4B4B, #FF914D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* タイマー（通常） */
    .timer-box {
        padding: 10px;
        border-radius: 8px;
        background-color: #f0f2f6;
        text-align: center;
        margin-bottom: 15px;
        font-weight: bold;
        font-size: 18px;
    }
    
    /* タイマー（ヤバイ時） */
    .timer-danger {
        color: #FF4B4B;
        border: 2px solid #FF4B4B;
        background-color: #fff0f0;
    }

    /* 横スクロール対策 */
    body { overflow-x: hidden !important; }
    
    /* チェックボックス */
    .stCheckbox { margin-bottom: 8px !important; }
    
    /* スタッツ表示 */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #eee;
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

# タイトル（グラデーション文字にしました）
st.markdown(f'<div class="custom-title">{PROJECT_TITLE}</div>', unsafe_allow_html=True)

# デッドライン表示（色が変わる演出）
if diff.total_seconds() > 0:
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    # 6時間を切ったら赤くなる
    timer_class = "timer-box timer-danger" if hours < 6 else "timer-box"
    emoji = "😱" if hours < 6 else "🔥"
    
    st.markdown(
        f'<div class="{timer_class}">{emoji} 残り {hours}時間 {minutes}分</div>', 
        unsafe_allow_html=True
    )
else:
    st.error("🚨 締め切り過ぎてます！提出急げ！")

# 自動更新スイッチ（上部に配置）
auto_refresh = st.toggle("🔄 自動更新 (30秒)", value=False)
if auto_refresh:
    time.sleep(30)
    st.rerun()

st.markdown("---") 

try:
    data, sheet = load_data()
    df = pd.DataFrame(data)
    
    # --- 全体の進捗率を計算してカッコよく表示 ---
    if not df.empty and "完了" in df.columns:
        total_tasks = len(df)
        completed_tasks = len(df[df["完了"].astype(str).str.upper() == "TRUE"])
        
        # 3カラムでスタッツ表示
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("全タスク", f"{total_tasks}個")
        kpi2.metric("完了", f"{completed_tasks}個")
        # 進捗率
        rate = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        kpi3.metric("進捗率", f"{rate}%")
        
        st.progress(rate / 100)
        
        # コンプリート演出！
        if rate == 100 and total_tasks > 0:
            st.balloons() # 風船が飛ぶ！
            st.success("🎉 全タスク完了！お疲れ様でした！！！")
    
    st.write("") # スペース

    tabs = st.tabs([f"{s.split()[0]}" for s in SONG_LIST])

    for i, song_name in enumerate(SONG_LIST):
        with tabs[i]:
            st.markdown(f"**🎵 {song_name}**")
            
            if not df.empty and "曲名" in df.columns:
                song_tasks = df[df["曲名"] == song_name]
                
                # その曲が100%ならチェックマークをつける
                s_total = len(song_tasks)
                s_done = len(song_tasks[song_tasks["完了"].astype(str).str.upper() == "TRUE"])
                if s_total > 0 and s_total == s_done:
                    st.success("✅ この曲はコンプリート！")
                elif s_total > 0:
                    st.caption(f"あと {s_total - s_done} タスク")
                    st.progress(s_done / s_total)

                # リスト表示
                for index, row in song_tasks.iterrows():
                    is_done = str(row["完了"]).upper() == "TRUE"
                    person = f"【{row['担当']}】" if row['担当'] not in ["-", ""] else ""
                    
                    # 完了したタスクは取り消し線を引く演出（Markdownハック）
                    task_text = row['タスク名']
                    if is_done:
                        label = f"~~{person}{task_text}~~" # 取り消し線
                    else:
                        label = f"{person}{task_text}"
                    
                    new_status = st.checkbox(label, value=is_done, key=f"t_{index}")
                    
                    if new_status != is_done:
                        sheet.update_cell(index + 2, 4, "TRUE" if new_status else "FALSE")
                        st.rerun()
            else:
                st.info("タスクなし")

            st.write("---")

            # 追加エリア（シンプル）
            with st.expander("➕ タスク追加"):
                with st.form(key=f"add_{i}", clear_on_submit=True):
                    new_task = st.text_input("タスク名")
                    new_person = st.selectbox("担当", ["-", "三好", "梅澤", "二人"])
                    if st.form_submit_button("追加", use_container_width=True):
                        if new_task:
                            p_val = new_person if new_person != "-" else ""
                            sheet.append_row([song_name, new_task, p_val, "FALSE"])
                            st.success("追加！")
                            time.sleep(0.5)
                            st.rerun()

            # 削除エリア（まとめて）
            with st.expander("🗑️ タスク整理"):
                if not df.empty and "曲名" in df.columns and len(song_tasks) > 0:
                    del_opts = [f"{r['タスク名']}" for idx, r in song_tasks.iterrows()]
                    # 選択肢に行番号を含めず、内部で照合する（見た目スッキリ）
                    selected_text = st.multiselect("削除するタスク", del_opts)
                    
                    if st.button("削除実行", key=f"del_{i}"):
                        if selected_text:
                            # 名前で逆引きして削除（同名タスクがある場合は注意だが、簡易的にはこれでOK）
                            rows_to_del = []
                            for txt in selected_text:
                                # この曲の中で、かつ名前が一致する行を探す
                                target_rows = song_tasks[song_tasks['タスク名'] == txt].index
                                for r_idx in target_rows:
                                    rows_to_del.append(r_idx + 2)
                            
                            # 重複を除いて降順ソート
                            rows_to_del = sorted(list(set(rows_to_del)), reverse=True)
                            for r in rows_to_del:
                                sheet.delete_rows(r)
                            st.success("削除完了")
                            time.sleep(1)
                            st.rerun()

except Exception as e:
    st.error("エラー")
    st.code(e)
