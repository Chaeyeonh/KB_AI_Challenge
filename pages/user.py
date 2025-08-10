import streamlit as st
import requests

#  사이드바 감추기
hide_sidebar = """
    <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        div[data-testid="collapsedControl"] {
            display: none !important;
        }
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

#  사용자 경험 입력
st.title("당신의 이야기를 들려주세요😊")
st.markdown("아래 항목에서 해당하는 경험을 선택해주세요.")

# 세션 상태 초기화
if "has_filled_experience" not in st.session_state:
    st.session_state["has_filled_experience"] = False

SERVER_URL = st.secrets["server"]["SERVER_URL"]
# -------------------------------
# Step 1. 사건 (Trigger)
# -------------------------------
st.subheader("1. 어떤 사건을 겪었나요?")
event_options = [
    "겪은 사건을 선택하세요",
    "주식 투자 실패",
    "소비 중독",
    "전세 사기",
    "보이스피싱",
    "중고거래 사기"
]
selected_event = st.selectbox("당신이 경험한 사건을 선택하세요:", event_options)

# -------------------------------
# Step 2. 감정 (Emotion)
# -------------------------------
st.subheader("2. 그때 어떤 감정을 느꼈나요?")
emotion_options = [
    "불안",
    "죄책감",
    "혼란",
    "무기력",
    "후회",
    "아무 감정이 들지 않았다",
]
selected_emotions = st.multiselect("그 사건 이후 자주 느낀 감정을 모두 선택하세요:", emotion_options)

# -------------------------------
# Step 3. 반응 (Behavior)
# -------------------------------
st.subheader("3. 그 후 돈에 대해 어떤 반응을 보였나요?")
reaction_options = [
    "돈 얘기를 피하게 되었다",
    "위험한 지출/투자를 반복했다",
    "돈을 지나치게 통제하려 했다",
    "돈 얘기만 해도 내가 초라해진다",
    "돈과 관련된 감정을 피하고 잊으려 한다",
]
selected_reactions = st.multiselect("지금까지 보였던 행동에 체크해 주세요:", reaction_options)

all_selected = (
    selected_event != event_options[0]
    and len(selected_emotions) > 0
    and len(selected_reactions) > 0
)

# -------------------------------
# 제출 및 결과 계산
# -------------------------------
if all_selected:
    if st.button("제출하고 결과 보기"):
       

        score = {
            "회피형": 0,
            "충동반복형": 0,
            "과잉통제형": 0,
            "정체감 손상형": 0,
            "혼란 억제형": 0
        }


        

        # 감정 → 유형
        if "불안" in selected_emotions: score["회피형"] += 1; score["과잉통제형"] += 1
        if "후회" in selected_emotions: score["충동반복형"] += 1
        if "죄책감" in selected_emotions: score["정체감 손상형"] += 1
        if "무기력" in selected_emotions: score["혼란 억제형"] += 1; score["회피형"] += 1
        if "혼란" in selected_emotions: score["혼란 억제형"] += 1
        if "아무 감정이 들지 않았다" in selected_emotions: score["혼란 억제형"] += 2

        # 행동 → 유형
        if "돈 얘기를 피하게 되었다" in selected_reactions: score["회피형"] += 2
        if "위험한 지출/투자를 반복했다" in selected_reactions: score["충동반복형"] += 2
        if "돈을 지나치게 통제하려 했다" in selected_reactions: score["과잉통제형"] += 2
        if "돈 얘기만 해도 내가 초라해진다" in selected_reactions: score["정체감 손상형"] += 2
        if "돈과 관련된 감정을 피하고 잊으려 한다" in selected_reactions: score["혼란 억제형"] += 2

        # 최종 결과
        max_score = max(score.values())
        likely_types = [k for k, v in score.items() if v == max_score]

        st.success(f"🧠 당신은 다음 유형에 가까울 수 있습니다: **{', '.join(likely_types)}**")
        st.markdown("👉 이 결과는 초기 추정이며, 더 깊은 이해를 위해 AI 상담 챗봇과 대화를 이어가보세요.")
        st.session_state["has_filled_experience"] = True
        st.session_state["diagnosis_type"] = likely_types[0]
        st.session_state["selected_event"] = selected_event
        st.session_state["selected_emotions"] = selected_emotions
        st.session_state["selected_reactions"] = selected_reactions

        if "chat_id" not in st.session_state:
            st.session_state.chat_id = 1  # 초기값 1로 설정
        else:
            st.session_state.chat_id = int(st.session_state.chat_id) + 1

      

        # 이벤트 저장
        url = f"{SERVER_URL}/save_event"
        data = {
            'chat_id': st.session_state.chat_id, 
            'event_text': selected_event, 
            'event_type': likely_types[0]
        }
        res = requests.post(url, json=data)




#  chat으로 이동하는 버튼 
if st.session_state.get("has_filled_experience", False):
    col1, col2, col3 = st.columns([5, 2, 1])
    with col3:
        if st.button("▶ 상담하기"):
            st.switch_page("pages/chat.py")

            