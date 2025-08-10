import streamlit as st
import requests

st.set_page_config(
    page_title = "MINDoc"
)


SERVER_URL = st.secrets["server"]["SERVER_URL"]

#최근의 chat_id불러오기
res = requests.get(f"{SERVER_URL}/latest_chat_id")
if res.status_code == 200:
    data = res.json()

    latest_chat_id  = data.get("latest_chat_id")

else:
    st.error("최신 chat_id를 불러오는 데 실패했습니다.")
    st.stop()



def get_eul_reul(word):
    # 받침이 있으면 '을', 없으면 '를'
    last_char = word[-1]
    code = ord(last_char) - ord('가')
    jongseong = code % 28
    return '을' if jongseong != 0 else '를'


url = f"{SERVER_URL}/get_events/{latest_chat_id}"
res = requests.get(url)

if res.status_code == 200:
    data = res.json()
    events = data.get("events", [])

    if events:
        latest_event = events[-1]
        selected_event = latest_event.get("event_text", "해당없음")
        st.session_state["selected_event"] = selected_event
        particle = get_eul_reul(selected_event)
        st.title(f"{selected_event}{particle} 겪었을 때는 이렇게 해보세요!")


# 백엔드 연동

def fetch_options(category: str):
    try:
        r = requests.get(f"{SERVER_URL}/advice/options", params={"category": category}, timeout=20)
        if r.status_code == 200:
            return r.json().get("data", {}).get("sections", {}).get("대처방안", [])
        else:
            st.warning(f"옵션 API 오류: {r.status_code}")
            return []
    except requests.RequestException as e:
        st.error(f"옵션 API 요청 실패: {e}")
        return []
    
def group_by_steps(lines):
    """
    대괄호로 감싼 제목 줄([1단계...], [2단계...])을 '단계'로 보고
    그 아래 항목들을 묶어서 반환합니다.
    """
    groups = []
    current = None

    def flush():
        if current is not None:
            groups.append(current.copy())

    for line in lines:
        is_header = line.startswith("[") and line.endswith("]")
        if is_header:
            flush()
            current = {"title": line.strip("[]"), "items": []}
        else:
            if current is None:
                # 제목 없이 시작하는 경우를 대비해 '기타' 묶음 생성
                current = {"title": "기타", "items": []}
            current["items"].append(line)
    flush()
    return groups

# 옵션 불러오기
option_lines = fetch_options(st.session_state.get("selected_event", "해당없음"))

if option_lines:
    groups = group_by_steps(option_lines)

    st.divider()
    st.subheader("체크리스트")

    for gi, g in enumerate(groups):
        with st.container(border=True):
            # 단계/섹션 제목 (메인 체크박스: 단계 완료 여부)
            done = st.checkbox(g["title"], key=f"grp_done_{gi}")

            # 상세 항목 (서브 체크박스)
            for ii, item in enumerate(g["items"]):
                st.checkbox(f"• {item}", key=f"grp_{gi}_item_{ii}")

else:
    st.info("표시할 대처방안이 없습니다.")