import streamlit as st

st.set_page_config(
    page_title = "MINDoc", page_icon="💸", layout="wide"
)


print(st.Page)  # 이게 무엇인지 확인


#페이지 정의
user = st.Page("pages/user.py", title="나의 경험 입력하기", default=True)
chat = st.Page("pages/chat.py", title = "AI 상담 챗봇")
challenge = st.Page("pages/challenge.py", title = "데일리 챌린지")
emotionReport = st.Page("pages/emotionReport.py", title = "감정 리포트")
solution = st.Page("pages/solution.py", title = "대처 방법")

pg = st.navigation([user, chat, challenge, emotionReport, solution])
# 실행
pg.run()