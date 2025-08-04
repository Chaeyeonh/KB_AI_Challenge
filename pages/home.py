
import streamlit as st

# 조건 보고 자동 리디렉션
if not st.session_state.get("has_filled_experience"):
    st.switch_page("pages/user.py")
else:
    st.switch_page("pages/chat.py")