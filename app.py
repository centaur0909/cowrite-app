import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# ---------------------------
# 設定エリア
# ---------------------------
st.set_page_config(page_title="Co-Write Sprinter", page_icon="🦁")

# 締め切り設定 (2026年1月14日 23:59 JST)
DEADLINE = datetime(2026, 1, 14, 23, 59, 0, tzinfo=pytz.timezone('Asia/Tokyo'))

# ---------------------------
# サイドバー：カウントダウン
# ---------------------------
st.sidebar.header("🦁 Co-Write Sprinter")
st.sidebar.markdown("---")

now = datetime.now(pytz.timezone('Asia/Tokyo'))
diff = DEADLINE - now

if diff.total_seconds() > 0:
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    st.sidebar.metric(label="🔥 DEADLINEまで", value=f"あと {days}日 {hours}時間 {minutes}分")
    st.sidebar.progress(max(0, min(100, int((1 - diff.total_seconds() / (7*24*60*60)) * 100))))
else:
    st.sidebar.error("🚨 締め切り過ぎてます！！")

# ---------------------------
# メイン画面：タスク管理
# ---------------------------
st.title("🚀 制作進行ボード")

# タブを作る
tab1, tab2, tab3 = st.tabs(["1. Pose & Gimmick", "2. 絶対的マスターピース！", "3. GO! GO! RUNNER!"])

def task_list(song_name):
    st.header(f"🎵 {song_name}")
    
    # 仮のデータ（本来はここをスプレッドシートと繋ぎます）
    tasks = {
        "ヘッドアレンジ作成": True,
        "ギター録音": True,
        "梅澤アレンジ待ち": False,
        "ボーカルRec": False,
        "ミックス確認": False
    }
    
    # 完了数カウント
    done_count = 0
    
    for task, is_done in tasks.items():
        # チェックボックスを表示
        checked = st.checkbox(task, value=is_done, key=f"{song_name}_{task}")
        if checked:
            done_count += 1
            
    # 進捗バー
    progress = done_count / len(tasks)
    st.caption(f"進捗率: {int(progress * 100)}%")
    st.progress(progress)

with tab1:
    task_list("Pose & Gimmick")

with tab2:
    task_list("絶対的マスターピース！")

with tab3:
    task_list("GO! GO! RUNNER!")

st.markdown("---")
st.caption("Developed by miyoshi & Gemini")
