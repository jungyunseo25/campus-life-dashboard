import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import re

# ---------------------------------------------------------
# 1. 페이지 기본 설정 및 한글 폰트 설정
# ---------------------------------------------------------
st.set_page_config(page_title="학과별 학생 생활습관 및 의견 분석", layout="wide")

# Matplotlib 한글 폰트 설정 (Windows: Malgun Gothic, Mac: AppleGothic)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# ---------------------------------------------------------
# 2. 인터페이스: 제목 및 설명
# ---------------------------------------------------------
st.title("🎓 학과별 학생 생활습관 및 한 줄 의견 분석 앱")
st.write("학생들의 생활습관, 만족도 관계를 분석하고 한 줄 의견의 핵심 단어 및 긍정/부정 경향을 살펴봅니다.")
st.markdown("---")

# ---------------------------------------------------------
# 3. 인터페이스: CSV 파일 업로드
# ---------------------------------------------------------
st.header("1. CSV 파일 업로드")
uploaded_file = st.file_uploader("분석할 CSV 파일을 선택해주세요.", type=["csv"])

if uploaded_file is not None:
    # 데이터 불러오기 및 미리보기
    df_raw = pd.read_csv(uploaded_file)

    st.subheader("📋 데이터 미리보기 (원본)")
    st.dataframe(df_raw.head())  # 상위 5개 행 표시

    # ---------------------------------------------------------
    # 4. 데이터 전처리 및 오류 데이터 제외 건수 표시
    # ---------------------------------------------------------
    st.header("2. 데이터 전처리 결과")

    initial_count = len(df_raw)  # 원본 데이터 총 건수

    # 필수 컬럼 정의
    required_columns = ['학과', '공부시간', '수면시간', '스마트폰', '통학시간', '만족도', '한줄의견']

    # 필수 컬럼 존재 여부 확인
    if not all(col in df_raw.columns for col in required_columns):
        st.error(f"CSV 파일에 다음 컬럼들이 포함되어 있어야 합니다: {required_columns}")
    else:
        df_clean = df_raw.copy()

        # 수치형 데이터 컬럼들을 숫자로 강제 변환 (오류/문자는 NaN으로 변환됨)
        numeric_cols = ['공부시간', '수면시간', '스마트폰', '통학시간', '만족도']
        for col in numeric_cols:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        # 결측치(NaN) 제거
        df_clean = df_clean.dropna(subset=required_columns).copy()

        # 정상 범위 필터링 (음수 시간 제외, 만족도는 0~10점 사이)
        valid_condition = (
                (df_clean['공부시간'] >= 0) &
                (df_clean['수면시간'] >= 0) &
                (df_clean['스마트폰'] >= 0) &
                (df_clean['통학시간'] >= 0) &
                (df_clean['만족도'] >= 0) &
                (df_clean['만족도'] <= 10)
        )
        df_clean = df_clean[valid_condition]

        removed_count = initial_count - len(df_clean)  # 제외된 오류 데이터 건수

        # 전처리 결과 안내 메시지
        st.success(
            f"데이터 전처리 완료! (총 데이터: {initial_count}건 / **제외된 오류 데이터: {removed_count}건** / 최종 데이터: {len(df_clean)}건)")
        st.markdown("---")

        # ---------------------------------------------------------
        # 5. 학과 선택 필터 구현
        # ---------------------------------------------------------
        st.header("3. 학과 선택 및 분석 결과")

        # 학과 목록 추출 ('전체' 옵션 포함)
        dept_list = ['전체'] + list(df_clean['학과'].unique())
        selected_dept = st.selectbox("분석할 학과를 선택하세요:", dept_list)

        # 선택된 학과에 따라 데이터 필터링
        if selected_dept == '전체':
            filtered_df = df_clean
        else:
            filtered_df = df_clean[df_clean['학과'] == selected_dept]

        # 선택한 학과의 평균 만족도 표시
        avg_satisfaction = filtered_df['만족도'].mean()
        st.metric(label=f"[{selected_dept}] 평균 학교생활 만족도", value=f"{avg_satisfaction:.2f} / 10 점")

        # ---------------------------------------------------------
        # 6. 그래프 시각화 (산점도 및 막대그래프)
        # ---------------------------------------------------------
        st.subheader("📊 데이터 분석 시각화")

        col1, col2 = st.columns(2)

        # --- [그래프 1] 산점도: 공부시간과 만족도 관계 ---
        with col1:
            st.markdown("### ① 공부시간과 학교생활 만족도 관계 (산점도)")

            fig1, ax1 = plt.subplots(figsize=(6, 4))
            sns.scatterplot(
                data=filtered_df,
                x='공부시간',
                y='만족도',
                hue='학과' if selected_dept == '전체' else None,
                ax=ax1,
                s=70
            )
            ax1.set_title("공부시간 vs 만족도", fontsize=12)
            ax1.set_xlabel("일일 공부시간 (시간)", fontsize=10)
            ax1.set_ylabel("학교생활 만족도 (점)", fontsize=10)
            ax1.grid(True, linestyle='--', alpha=0.5)

            st.pyplot(fig1)

        # --- [그래프 2] 막대그래프: 평균 생활습관 비교 ---
        with col2:
            st.markdown("### ② 평균 주요 생활습관 시간 (막대그래프)")

            habit_means = filtered_df[['공부시간', '수면시간', '스마트폰', '통학시간']].mean()

            fig2, ax2 = plt.subplots(figsize=(6, 4))
            habit_means.plot(kind='bar', ax=ax2, color=['#4C72B0', '#55A868', '#C44E52', '#8172B0'])

            ax2.set_title("항목별 평균 시간", fontsize=12)
            ax2.set_xlabel("생활습관 항목", fontsize=10)
            ax2.set_ylabel("평균 시간 (시간)", fontsize=10)
            ax2.set_xticklabels(habit_means.index, rotation=0)
            ax2.grid(axis='y', linestyle='--', alpha=0.5)

            st.pyplot(fig2)

        # ---------------------------------------------------------
        # 7. [기능 추가] 한 줄 의견 상위 10개 단어 및 긍정/부정 분석
        # ---------------------------------------------------------
        st.markdown("---")
        st.subheader("③ 한 줄 의견 텍스트 분석 (상위 10개 단어 및 긍정/부정)")

        # 모든 한 줄 의견 합치기
        all_text = " ".join(filtered_df['한줄의견'].astype(str))
        # 한글 2글자 이상 단어 추출
        words = re.findall(r'\b[가-힣]{2,}\b', all_text)

        if words:
            # 상위 10개 단어 빈도 추출
            word_counts = Counter(words).most_common(10)
            words_df = pd.DataFrame(word_counts, columns=['단어', '빈도수'])

            # --- [그래프 3] 상위 10개 단어 막대그래프 ---
            fig3, ax3 = plt.subplots(figsize=(10, 4))
            sns.barplot(data=words_df, x='빈도수', y='단어', ax=ax3, palette='Blues_r')
            ax3.set_title("한 줄 의견에 가장 많이 등장한 핵심 단어 Top 10", fontsize=13)
            ax3.set_xlabel("빈도수 (회)", fontsize=11)
            ax3.set_ylabel("단어", fontsize=11)
            ax3.grid(axis='x', linestyle='--', alpha=0.5)

            st.pyplot(fig3)

            # --- [기능 추가] 긍정 / 부정 단어 등장 횟수 분석 ---
            st.markdown("#### 💬 긍정 vs 부정 의견 키워드 분석")

            # 간단한 감성 분석 사전 정의 (교육용 예시 단어들)
            positive_words = ['좋아요', '맛있어요', '재미있어요', '도움이', '편리해요', '친절해요', '즐거워요', '예뻐서']
            negative_words = ['부족해요', '힘들어요', '피곤해요', '아쉬워요', '불편해요', '후회돼요', '붐벼서', '길어서', '많아서']

            pos_count = sum(words.count(w) for w in positive_words)
            neg_count = sum(words.count(w) for w in negative_words)

            # 화면에 지표(Metric)로 긍정/부정 횟수 나란히 표시
            col_p, col_n = st.columns(2)
            with col_p:
                st.metric(label="😊 긍정 관련 키워드 등장 횟수", value=f"{pos_count} 회")
            with col_n:
                st.metric(label="😞 부정 관련 키워드 등장 횟수", value=f"{neg_count} 회")

        else:
            st.info("분석할 한 줄 의견 데이터가 충분하지 않습니다.")

else:
    st.info("👆 위에서 CSV 파일을 업로드하면 분석이 시작됩니다.")