import streamlit as st
import requests
import re

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


url = f"{SERVER_URL}/get_events/{latest_chat_id}"
res = requests.get(url)

if res.status_code == 200:
    data = res.json()
    events = data.get("events", [])

    if events:
        latest_event = events[-1]
        selected_event = latest_event.get("event_text", "해당없음")
        st.session_state["selected_event"] = selected_event



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
    groups = []
    current = None
    preface = []  # [1단계] 이전의 내용 저장

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
                preface.append(line)
            else:
                current["items"].append(line)
    flush()
    return preface, groups


# 옵션 불러오기
option_lines = fetch_options(st.session_state.get("selected_event", "해당없음"))

if option_lines:
    preface, groups = group_by_steps(option_lines)

    if preface:
        for line in preface:
            st.title(line)
    st.divider()

    for gi, g in enumerate(groups):
        with st.container(border=True):
            # 단계 제목 굵게
            st.markdown(f"<h3 style='color:orange'>[{g['title']}]</h4>", unsafe_allow_html=True)


            for ii, item in enumerate(g["items"]):
                if re.match(r'^\s*\d+\.\s', item):
                    # 숫자. 로 시작 → 체크박스 + h4 텍스트를 같은 줄에
                    c1, c2 = st.columns([1, 24])
                    with c1:
                        st.checkbox("", key=f"grp_{gi}_item_{ii}", label_visibility="collapsed")
                    with c2:
                        st.markdown(f"#### **{item}**")
                else:
                # 나머지 :들여쓰기 + 글머리기호
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;• {item}", unsafe_allow_html=True)

else:
    st.info('표시할 대처방안이 없습니다.')