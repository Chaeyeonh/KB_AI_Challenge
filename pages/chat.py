import streamlit as st
from openai import OpenAI
import requests

selected_event = "해당없음"
diagnosis_type = "해당없음"
chat_id = 1 

# 페이지 설정
st.set_page_config(page_title="MINDoc")

# 페이지 타이틀
st.title("지친 마음, 혼자 끌어안지 말고 털어놓으세요")

# OpenAI 클라이언트 생성
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 모델 설정
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"


# 서버에서 정보 가져오기
url = f"https://a6872b71ec47.ngrok-free.app/get_events/{chat_id}"
res = requests.get(url)

if res.status_code == 200:
    data = res.json()
    events = data.get("events", [])

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
    st.write(" 응답 상태 코드:", res.status_code)
    st.write(" 응답 내용:", res.text)



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

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": system_message}]
else:
    st.session_state.messages[0] = {"role": "system", "content": system_message}  # 항상 갱신

if "first_bot_message_done" not in st.session_state:
    st.session_state.first_bot_message_done = False

# 첫 assistant 메시지 생성 (딱 한 번만 실행)
if not st.session_state.first_bot_message_done:
    response = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=st.session_state.messages,
        stream=False
    )
    first_message = response.choices[0].message.content

    st.session_state.messages.append({"role": "assistant", "content": first_message})
    st.session_state.first_bot_message_done = True

# 이전 메시지 출력 (첫 system 메시지는 출력 제외)
for idx, message in enumerate(st.session_state.messages):
    #  중복 방지: 첫 assistant 메시지일 경우, 생성 직후 출력했으니 건너뜀
    if idx == 1 and message["role"] == "assistant" and st.session_state.first_bot_message_done:
        continue
    if idx > 0:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# 사용자 입력 받기
if prompt := st.chat_input("너의 이야기를 들려줘!"):
    # 사용자 메시지 저장 및 출력
    st.session_state.messages.append({"role": "user", "content": prompt})
    url = "https://a6872b71ec47.ngrok-free.app/predict"
    data = {"text": prompt}
    res = requests.post(url, json=data)

    #디버깅용
    st.write("서버 응답 상태코드:", res.status_code)
    st.write("서버 응답 내용:", res.text)

    with st.chat_message("user"):
        st.markdown(prompt)

    # GPT 응답 생성
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=st.session_state.messages,
            stream=True
        )
        response = st.write_stream(stream)

    # 응답 저장
    st.session_state.messages.append({"role": "assistant", "content": response})
