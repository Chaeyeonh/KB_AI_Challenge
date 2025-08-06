import streamlit as st
import requests

st.set_page_config(
    page_title = "MINDoc"
)


SERVER_URL = st.secrets["server"]["SERVER_URL"]
chat_id = 1

def get_eul_reul(word):
    # 받침이 있으면 '을', 없으면 '를'
    last_char = word[-1]
    code = ord(last_char) - ord('가')
    jongseong = code % 28
    return '을' if jongseong != 0 else '를'


url = f"{SERVER_URL}/get_events/{chat_id}"
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