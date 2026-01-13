import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# ---------------------------
# 1. ページ設定 & デザイン調整
# ---------------------------
st.set_page_config(page_title="Co-Write Sprinter", page_icon="🦁", layout="centered")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .big-font {
                font-size:20px !important;
                font-weight: bold;
                color: #FF4B4B;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------------------------
# 2. ロジック（時間計算）
# ---------------------------
DEADLINE = datetime(2026, 1, 14, 23, 59, 0, tzinfo=pytz.timezone('Asia/Tokyo'))
now = datetime.now(pytz.timezone('Asia/Tokyo'))
diff = DEADLINE - now

# ---------------------------
# 3. データ管理（ここが進化！）
# ---------------------------
# アプリがリロードされてもデータを保持するための「セッションステート」を使います

# もしデータがまだなければ、初期データを作る
if 'tasks' not in st.session_state:
    st.session_state['tasks'] = {
        "Pose & Gimmick": [
            {"name": "ギター本番録音", "person": "三好", "done": True},
            {"name": "サビ構成変更", "person": "梅澤", "done": True},
        ],
        "絶対的マスターピース！": [
            {"name": "歌データ送信", "person": "三好", "done": True},
            {"name": "ブラス追加・Mix", "person": "梅澤", "done": False},
        ],
        "GO! GO! RUNNER!": [
            {"name": "アレンジ提出", "person": "梅澤", "done": False},
            {"name": "BPM/Key固定確認", "person": "三好", "done": True},
        ]
    }

# ---------------------------
# 4. メイン画面
# ---------------------------
if diff.total_seconds() > 0:
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    progress_val = max(0, min(100, int((1 - diff.total_seconds() / (7*24*60*60)) * 100)))
    
    st.markdown(f'<p class="big-font">🔥 DEADLINEまで：あと {hours}時間 {minutes}分</p>', unsafe_allow_html=True)
    st.progress(progress_val)
else:
    st.error("🚨 締め切り過ぎてます！！提出急げ！！")

st.write("---") 

# タブ表示
tab1, tab2, tab3 = st.tabs(["1. Pose", "2. Masterpiece", "3. Runner"])

# タスク表示用の関数
def render_tab(song_key):
    st.markdown(f"**🎵 {song_key}**")
    
    # --- タスク追加フォーム ---
    with st.expander("➕ タスクを追加する"):
        with st.form(key=f"add_{song_key}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                new_task = st.text_input("タスク名")
            with col2:
                new_person = st.selectbox("担当", ["三好", "梅澤", "二人"])
            
            submit = st.form_submit_button("追加")
            
            if submit and new_task:
                # リストに追加する処理
                st.session_state['tasks'][song_key].append(
                    {"name": new_task, "person": new_person, "done": False}
                )
                st.success("追加しました！")
                st.rerun() # 即座に画面を更新

    # --- タスクリスト表示 ---
    task_list = st.session_state['tasks'][song_key]
    
    done_count = 0
    for i, task in enumerate(task_list):
        # アイコンではなく「名前」で表示
        label = f"【{task['person']}】 {task['name']}"
        
        # チェックボックス
        # keyを工夫して、どのタスクか特定できるようにする
        is_checked = st.checkbox(label, value=task["done"], key=f"{song_key}_{i}")
        
        # 状態を更新
        st.session_state['tasks'][song_key][i]["done"] = is_checked
        
        if is_checked:
            done_count += 1
            
    # 進捗率
    if len(task_list) > 0:
        progress = done_count / len(task_list)
        st.caption(f"進捗: {int(progress * 100)}%")
        st.progress(progress)
    else:
        st.info("タスクがありません")

with tab1:
    render_tab("Pose & Gimmick")

with tab2:
    render_tab("絶対的マスターピース！")

with tab3:
    render_tab("GO! GO! RUNNER!")
