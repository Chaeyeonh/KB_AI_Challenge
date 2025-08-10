import streamlit as st
import requests
import os
from datetime import date

st.set_page_config(page_title="MINDoc", layout="wide")
st.title("데일리 챌린지✅")

SERVER_URL = st.secrets["server"]["SERVER_URL"]
XP_PER_LEVEL = 5
MAX_LEVEL_IMAGE = 4

# -----------------------------
# USER_ID (세션 보존)
# -----------------------------
if "USER_ID" not in st.session_state:
    st.session_state.USER_ID = 300
# 표시 전용 캐릭터 오버라이드(미리보기)
if "OVERRIDE_CHAR" not in st.session_state:
    st.session_state.OVERRIDE_CHAR = None

USER_ID = st.session_state.USER_ID
TODAY = date.today().isoformat()
TODAY_KEY = f"{USER_ID}:{TODAY}"

# -----------------------------
# 캐릭터 이미지
# -----------------------------
def get_character_image(level: int) -> str | None:
    lvl = min(int(level), MAX_LEVEL_IMAGE)
    path = f"images/level_{lvl}.png"
    return path if os.path.exists(path) else None

# -----------------------------
# API
# -----------------------------
def api_get_dashboard():
    r = requests.get(f"{SERVER_URL}/api/users/{USER_ID}/dashboard", timeout=5)
    r.raise_for_status()
    return r.json()

def api_complete_mission(mission_id: int):
    return requests.post(
        f"{SERVER_URL}/api/users/{USER_ID}/missions/{mission_id}/complete",
        timeout=5
    )


def clear_all_cache_and_rerun(release_today_lock: bool = False):
    try:
        st.cache_data.clear()
    except Exception:
        pass
    if release_today_lock and "today_mission_lock" in st.session_state:
        st.session_state.today_mission_lock.pop(TODAY_KEY, None)
    st.rerun()

# -----------------------------
# “오늘 미션 고정” 세션 가드
# -----------------------------
if "today_mission_lock" not in st.session_state:
    st.session_state.today_mission_lock = {}  # key: f"{USER_ID}:{YYYY-MM-DD}" -> {"mission_id","title"}

data = api_get_dashboard()
character = data["character"]
backend_today = data["todayMission"] or {"mission_id": None, "title":"오늘 미션이 없습니다", "is_completed": True}

# 1) 오늘-유저 키에 락이 없으면 지금 받은 미션으로 고정
if TODAY_KEY not in st.session_state.today_mission_lock and backend_today["mission_id"] is not None:
    st.session_state.today_mission_lock[TODAY_KEY] = {
        "mission_id": backend_today["mission_id"],
        "title": backend_today["title"]
    }

# 2) 락이 있으면 백엔드가 다른 걸 보내도 오늘은 “고정된 것”으로 표기
if TODAY_KEY in st.session_state.today_mission_lock:
    locked = st.session_state.today_mission_lock[TODAY_KEY]
    mission_id = locked["mission_id"]
    mission_title = locked["title"]
    is_completed = bool(backend_today.get("is_completed", False)) if backend_today["mission_id"] == mission_id else False
else:
    mission_id = backend_today["mission_id"]
    mission_title = backend_today["title"]
    is_completed = backend_today["is_completed"]

# -----------------------------
# 표시용 캐릭터(미리보기 적용)
# -----------------------------
effective_char = st.session_state.OVERRIDE_CHAR or character

# -----------------------------
# 레이아웃
# -----------------------------
left, center = st.columns([2, 5])

with left:
    with st.container(border=False):
        st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align:center;'>LV. {effective_char['level']}</h3>", unsafe_allow_html=True)

        img_path = get_character_image(effective_char['level'])
        if img_path:
            st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
            st.image(img_path, width=270)
        else:
            st.markdown("<div style='font-size:60px;text-align:center;margin-top:24px;'>🧑‍🚀</div>", unsafe_allow_html=True)

        # === XP 표시(백엔드 규칙: total_exp=현재 레벨 누적, next_exp_req=필요치) ===
        need_total = int(effective_char['next_exp_req'])       # 5→6→7… 가변
        earned_in_level = int(effective_char['total_exp'])     # 현재 레벨 누적
        col_xp1, col_xp2 = st.columns(2)
        with col_xp1:
            st.metric("이번 레벨 누적", f"{earned_in_level}/{need_total} XP")
        with col_xp2:
            st.metric("총 XP(현재 레벨 내)", f"{earned_in_level} XP")

with center:
    with st.container(border=True):
        st.markdown(
            f"""
            <div style="background:white; border-radius:10px; padding:12px; min-height:510px;">
                <h3 style="margin-bottom:180px; text-align:center;">🌟오늘의 챌린지🌟</h3>
                <p style="font-weight:400; font-size:25px; margin:24px 0 0 0; text-align:center;">{mission_title}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_spacer, col_btn = st.columns([5, 2])
        with col_btn:
            if mission_id is not None and not is_completed:
                if st.button("✅ 완료(+1 XP)", use_container_width=True, key=f"done-{TODAY_KEY}-{mission_id}"):
                    resp = api_complete_mission(mission_id)
                    if resp.status_code == 200:
                        st.toast("완료 처리됐어요! 갱신중…", icon="✅")
                        st.rerun() 
                    elif resp.status_code == 409:
                        st.warning("이미 완료한 미션입니다!")
                    else:
                        try:
                            st.error(resp.json())
                        except Exception:
                            st.error(resp.text)
            else:
                st.markdown(
                    """
                    <style>
                    .done-btn {
                        background-color: rgba(0, 0, 0, 0.1) !important;
                        color: #000 !important;
                        border: 1px solid rgba(49, 51, 63, 0.2);
                        padding: 0.6rem;
                        border-radius: 0.5rem;
                        width: 100%;
                        text-align: center;
                        cursor: not-allowed;
                        font-family: "Source Sans Pro", sans-serif;
                        font-size: 0.9rem;
                        margin-bottom: 15px;
                        font-weight: 600;
                    }
                    </style>
                    <div class="done-btn">✅ 완료됨</div>
                    """,
                    unsafe_allow_html=True,
                )

# -----------------------------
# 사이드바
# -----------------------------
with st.sidebar:
    st.markdown("### 👤 테스트 유저 전환")
    new_id = st.number_input("USER_ID", min_value=1, value=int(USER_ID), step=1)
    if st.button("이 유저로 보기", use_container_width=True):
        st.session_state.USER_ID = int(new_id)
        # 프론트 상태 정리
        st.session_state.today_mission_lock = {}
        st.session_state.OVERRIDE_CHAR = None
        try:
            st.cache_data.clear()
        except Exception:
            pass
        st.success(f"USER_ID {new_id} 로 전환")
        st.rerun()