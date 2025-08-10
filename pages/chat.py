import streamlit as st
from openai import OpenAI
import requests
import json

selected_event = "해당없음"
diagnosis_type = "해당없음"

SERVER_URL = st.secrets["server"]["SERVER_URL"]

# 페이지 설정
st.set_page_config(page_title="MINDoc")

# 페이지 타이틀
st.title("지친 마음, 혼자 끌어안지 말고 털어놓으세요")

# OpenAI 클라이언트 생성
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 모델 설정
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"

#최근의 chat_id불러오기
res = requests.get(f"{SERVER_URL}/latest_chat_id")
if res.status_code == 200:
    data = res.json()

    latest_chat_id  = data.get("latest_chat_id")

    if "chat_id" not in st.session_state or st.session_state.chat_id != latest_chat_id:
    # chat_id가 변경되면 새로운 chat_id로 저장하고 대화 내역 초기화
        st.session_state.chat_id = latest_chat_id
        st.session_state.chat_history = []  # 대화 내역 초기화
   

else:
    st.error("최신 chat_id를 불러오는 데 실패했습니다.")
    st.stop()

# chat_id가 없으면 에러
if st.session_state.chat_id is None:
    st.error("chat_id가 없습니다. 다시 user.py에서 시작해 주세요.")
    st.stop()

# 서버에서 해당 chat_id에 맞는 정보 가져오기
url = f"{SERVER_URL}/get_events/{st.session_state.chat_id}"
res = requests.get(url)

if res.status_code == 200:
    data = res.json()
    events = data.get("events", [])
    # st.write("서버에서 받은 이벤트:", events)

    if events:
        latest_event = events[-1]
        selected_event = latest_event.get("event_text", "해당없음")
        diagnosis_type = latest_event.get("event_type", "해당없음")

        # session_state에도 저장
        st.session_state["selected_event"] = selected_event
        st.session_state["diagnosis_type"] = diagnosis_type

        # 디버깅용
        # st.write("selected_event:", selected_event)
        # st.write(" diagnosis_type:", diagnosis_type)
    else:
        st.warning(" 불러올 이벤트가 없습니다.")
else:
    st.error(" 이전 경험 데이터를 불러오는 데 실패했어요")
    # st.write(" 응답 상태 코드:", res.status_code)
    # st.write(" 응답 내용:", res.text)



# 시스템 메시지 설정
def get_system_message(diagnosis_type, selected_event):
    # 안전장치
    if not diagnosis_type or not selected_event:
        return "너는 따뜻한 말투로 반말하는 상담 챗봇이야. 사용자의 이야기를 경청하고 공감해줘 😊"

    if diagnosis_type == "회피형":
        return f"""너는 반말로 말하는 친근한 상담 챗봇이야.
사용자는 '{selected_event}'를 겪고 나서 회피형 반응을 보이고 있어.
자꾸 돈 이야기를 피하려 하거나, 생각을 안 하려고 해.이걸 넌 해결하도록 도와줘야돼.

이런 사용자가 조금씩 마음을 열 수 있도록:
- '그때 어떤 기분이었어?', '누구한테도 말 못했구나?' 같은 질문으로 천천히 공감해줘.
- 너무 재촉하거나 판단하지 말고, 한마디씩 따뜻하게 말해줘.
- 모든 대답은 반말 + 공감 + 이모지 포함! 예: "그랬구나... 마음 진짜 복잡했겠다 😢"
"""

    elif diagnosis_type == "충동반복형":
        return f"""너는 반말로 말하는 친근한 상담 챗봇이야.
사용자는 '{selected_event}'을 겪고 나서 충동적으로 지출하거나 투자를 반복하고 있어.

감정을 다루기 어려워서 자꾸 비슷한 실수를 하게 되는 거야.
- '그때 왜 그랬던 것 같아?', '그럴 땐 어떤 기분이 들었어?'처럼 깊은 감정을 유도해봐.
- 비난 없이, 대신 감정을 끌어내는 방식으로 공감해줘.
"""

    elif diagnosis_type == "과잉통제형":
        return f"""너는 반말로 말하는 상담 챗봇이야.
'{selected_event}' 이후, 사용자는 돈을 지나치게 통제하려는 반응을 보이고 있어.

- '혹시 불안해서 그랬던 걸까?', '안정감을 느끼고 싶었던 거야?' 이런 식으로 질문해.
- 공감과 감정 언어 중심으로 대화를 이어가.
"""

    else:
        return f"""너는 반말로 말하는 친근한 상담 챗봇이야.
사용자는 '{selected_event}'을 겪었고, '{diagnosis_type}' 유형으로 분류되었어.

- 감정에 공감하고, 계속 대화를 이어가면서 사용자의 경험을 더 깊이 이해하려 해봐.  '{diagnosis_type}'성향을 보이는 사람에게 맞는 해결책을 말해줘.
- 예: '그때 어땠어?', '그 이후엔 어떤 변화가 있었어?', '지금은 좀 나아졌어?' 등
"""
    
system_message = get_system_message(diagnosis_type, selected_event)

# 초기값 설정
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "first_bot_message_done" not in st.session_state:
    st.session_state.first_bot_message_done = False

# 대화 불러오기 (최초 1회)
if not st.session_state.chat_history:
    res = requests.get(f"{SERVER_URL}/get_conversations/{st.session_state.chat_id}")

    if res.status_code == 200:
        conversations = res.json().get("conversations", [])
        #st.write("서버에서 받은 대화 내역:", conversations)
        temp_history = []
        pair = {}
        for msg in conversations:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                if pair:
                    temp_history.append(pair)
                    pair = {}
                pair["user_text"] = content
            elif role == "gpt":
                if "user_text" not in pair:
                    pair["user_text"] = None
                pair["gpt_text"] = content
                temp_history.append(pair)
                pair = {}
        if pair:
            temp_history.append(pair)
        st.session_state.chat_history = temp_history

# 유틸 함수

def should_gpt_auto_respond():
    return len(st.session_state.chat_history) == 0

# GPT가 먼저 말해야 하는 조건
if should_gpt_auto_respond() and not st.session_state.first_bot_message_done:
        messages_for_openai = [{"role": "system", "content": system_message}]
        for pair in st.session_state.chat_history:
            if pair.get("user_text") is not None:
                messages_for_openai.append({"role": "user", "content": pair["user_text"]})
            if pair.get("gpt_text") is not None:
                messages_for_openai.append({"role": "assistant", "content": pair["gpt_text"]})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_openai
        )
        first_message = response.choices[0].message.content

        first_pair = {
        "user_text": "",
        "gpt_text": first_message,
        "chat_id": st.session_state.chat_id
        }
        
        st.session_state.chat_history.append(first_pair)
        st.session_state.first_bot_message_done = True
        res = requests.post(f"{SERVER_URL}/predict", json=first_pair)
        if res.status_code != 200:
            st.warning(f"첫 GPT 메시지 저장 실패: {res.status_code}")
            st.write("전송된 데이터:", first_pair)
            st.write("서버 응답:", res.text)
# UI 출력

for pair in st.session_state.chat_history:
    if pair.get("user_text"):  
        with st.chat_message("user"):
            st.markdown(pair["user_text"])

    if pair.get("gpt_text"):
        with st.chat_message("assistant"):
            st.markdown(pair["gpt_text"])



# 사용자 입력
if prompt := st.chat_input("너의 이야기를 들려줘!"):
    with st.chat_message("user"):
        st.markdown(prompt)

    messages_for_openai = [{"role": "system", "content": system_message}]
    for pair in st.session_state.chat_history:
            messages_for_openai.append({"role": "assistant", "content": pair["gpt_text"]})
    messages_for_openai.append({"role": "user", "content": prompt})

    # GPT 응답 받기
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4o",
            messages=messages_for_openai,
            stream=True
        )
        gpt_response = st.write_stream(stream)

    # 새 대화 쌍 저장 (GPT 응답은 `gpt_text`, 사용자 입력은 `user_text`)
    new_pair = {"gpt_text": gpt_response, "user_text": prompt, "chat_id": st.session_state.chat_id}
    st.session_state.chat_history.append(new_pair)
    # 서버로 저장
    res = requests.post(f"{SERVER_URL}/predict", json=new_pair)
   