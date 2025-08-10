import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import platform
import requests 
import pandas as pd
import matplotlib.dates as mdates

st.set_page_config(
    page_title = "MINDoc"
)

st.title("나의 감정 리포트를 확인해보세요😃")

SERVER_URL = st.secrets["server"]["SERVER_URL"]

# 한글 폰트 설정
if platform.system() == "Windows":
    matplotlib.rc('font', family='Malgun Gothic')  # 윈도우 기본 한글 폰트
elif platform.system() == "Darwin":
    matplotlib.rc('font', family='AppleGothic')  # 맥 기본 폰트
else:
    matplotlib.rc('font', family='NanumGothic')  # 리눅스나 기타 환경

# 음수 깨짐 방지
matplotlib.rcParams['axes.unicode_minus'] = False

#  날짜 선택
selected_date = st.date_input("날짜를 선택하세요")
date_str = selected_date.strftime("%Y-%m-%d")
#  리포트용 날짜 계산
start_week = selected_date - pd.Timedelta(days=3)
end_week = selected_date + pd.Timedelta(days=3)
month_str = selected_date.strftime("%Y-%m") 

#레이아웃
col1, col2 = st.columns([1,2])

# ---------------------------
#  1. 일일 리포트
# ---------------------------
with col1:

    st.subheader("📅 일일 감정 리포트")
    daily_url = f"{SERVER_URL}/summary/daily/{date_str}"
    daily_res = requests.get(daily_url)
    daily_res.encoding = 'utf-8'


    if daily_res.status_code == 200:
        daily_data_raw = daily_res.json()["data"]

        daily_data = {item["emotion"]: item["avg_percent"] for item in daily_data_raw}

        # 감정 비율이 3% 이상인 데이터만 시각화
        filtered_data = {emotion: percent for emotion, percent in daily_data.items() if percent >= 3.0}

        # 전체 퍼센트 중 3% 미만 감정은 '기타'로 합쳐주기
        etc_sum = sum(percent for percent in daily_data.values() if percent < 3.0)
        if etc_sum > 0:
            filtered_data["기타"] = etc_sum


        # 원형그래프 시각화
        fig1, ax1 = plt.subplots(figsize=(4, 4))
        ax1.pie(filtered_data.values(), labels=filtered_data.keys(), autopct="%1.1f%%")
        ax1.set_title(f"{date_str}의 감정 리포트")
        st.pyplot(fig1)
    else:
        st.error("❌ 이 날은 상담하지 않았어요.")

# ---------------------------
#  2. 주간 감정 꺾은선 그래프
# ---------------------------
with col2:

    st.subheader("📈 주간 감정 리포트")
    weekly_url = f"{SERVER_URL}/summary/weekly/{start_week}/{end_week}"

    week_res = requests.get(weekly_url)
    # st.write("응답 json type:", type(week_res.json()))
    # st.write("응답 내용:", week_res.json())

    if week_res.status_code == 200:
        json_data = week_res.json()
        emotion_data = json_data["data"]

        # 데이터를 DataFrame으로 변환
        df = pd.DataFrame(emotion_data)

        # 'date'를 datetime으로 변환
        df["date"] = pd.to_datetime(df["date"])

        # 감정 pivot: 행=date, 열=emotion, 값=avg_percent
        pivot_df = df.pivot(index="date", columns="emotion", values="avg_percent")

        # 누락된 날짜 보완: index 재설정 (모든 날짜 포함)
        full_date_range = pd.date_range(start=start_week, end=end_week)
        pivot_df = pivot_df.reindex(full_date_range)  # 누락된 날짜는 NaN


        fig2, ax2 = plt.subplots(figsize=(6, 3))

        for emotion in pivot_df.columns:
            y = pivot_df[emotion]
            if y.isnull().all():
                continue  # 전부 NaN이면 생략
            ax2.plot(pivot_df.index, y, label=emotion, marker='o')

        ax2.legend()
        ax2.set_title("주간 감정 변화")
        ax2.set_xlabel("날짜")
        ax2.set_ylabel("감정 비율 (%)")
        
        ax2.set_xlim(full_date_range.min(), full_date_range.max())
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        fig2.autofmt_xdate()
        st.pyplot(fig2)
    else:
        st.error("❌ 주간 리포트를 불러오지 못했습니다.")
# ---------------------------
#  3. 월간 감정 꺾은선 그래프
# ---------------------------
with st.container():
    st.subheader(" 😄월간 감정 리포트")

    month_url = f"{SERVER_URL}/summary/monthly/{month_str}"
    try:
        month_res = requests.get(month_url, timeout=5)

        if month_res.status_code == 200:
            json_data = month_res.json()

            if not json_data.get("data"):
                st.warning("월간 데이터가 없습니다.")
            else:
                emotion_data = json_data["data"]
                # 감정 이모지 매핑
                emotion_to_emoji = {
                    "기쁨": "😄", "슬픔": "😢", "분노": "😠",
                    "불안": "😨", "상처": "💔", "당황": "😳",
                    "중립": "😐"
                }

                 # 감정 비율 내림차순 정렬
                sorted_data = sorted(emotion_data, key=lambda x: x["avg_percent"], reverse=True)

                # 상단: 이모지와 텍스트 박스를 좌우로 나누기
                col1, col2 = st.columns([1, 3])  # 좌측 이모지, 우측 텍스트 박스

                #  왼쪽: 이모지
                top_emotion = sorted_data[0]["emotion"]
                emoji = emotion_to_emoji.get(top_emotion, "❓")
                with col1:
                    st.markdown(
                        f"<div style='font-size: 100px; margin-top: 20px; text-align: center;'>{emoji}</div>",
                        unsafe_allow_html=True
                    )

                #  오른쪽: 텍스트 박스들
                with col2:
                    st.markdown("""
                    <div style='font-size:20px; font-weight:600; margin-bottom:10px'>
                        이번달에 많이 느낀 감정이에요
                    </div>
                    """, unsafe_allow_html=True)

                    for rank, item in enumerate(sorted_data[:3], 1):
                        emo = item["emotion"]
                        percent = item["avg_percent"]
                        st.markdown(f"""
                            <div style="background-color: #f9f9f9;
                                        border: 1px solid #ddd;
                                        border-radius: 10px;
                                        padding: 10px 15px;
                                        margin-bottom: 8px;
                                        box-shadow: 1px 1px 4px rgba(0,0,0,0.05);
                                        ">
                                <b>{rank}위</b>: {emotion_to_emoji.get(emo, '')} <b>{emo}</b> — {percent:.1f}%
                            </div>
                        """, unsafe_allow_html=True)


                #  전월 비교 텍스트
                prev_month = (pd.to_datetime(month_str + "-01") - pd.DateOffset(months=1)).strftime("%Y-%m")
                prev_url = f"{SERVER_URL}/summary/monthly/{prev_month}"
                prev_res = requests.get(prev_url, timeout=5)

                if prev_res.status_code == 200:
                    prev_data = prev_res.json().get("data", [])
                    prev_map = {item["emotion"]: item["avg_percent"] for item in prev_data}

                
                    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)
                    st.markdown("#### 📉 <span style='font-size:20px'>지난달 대비 감정 변화</span>", unsafe_allow_html=True)
                    for item in sorted_data[:3]:
                        emo = item["emotion"]
                        cur = item["avg_percent"]
                        prev = prev_map.get(emo, 0.0)
                        diff = cur - prev
                        if diff > 0:
                            msg = f"{diff:.1f}% 증가했어요!"
                        elif diff < 0:
                            msg = f"{abs(diff):.1f}% 감소했어요!"
                        else:
                            msg = "변화가 없어요!"
                        st.markdown(f"- {emotion_to_emoji.get(emo, '')} **{emo}**: {msg}")
                else:
                  
                    st.markdown("#### 📉 지난달 대비 감정 변화")
                    st.info("지난달 데이터가 없어 비교할 수 없어요.")

        else:
            st.error(f"월간 리포트 실패: {month_res.status_code}")
            st.text(month_res.text)

    except Exception as e:
        st.error(f"❌ 예외 발생: {e}")