# ===== 라이브러리 불러오기 =====
import streamlit as st          # 웹 대시보드를 만드는 라이브러리
import pandas as pd             # 표 데이터를 다루는 라이브러리
import plotly.express as px     # 그래프를 그리는 라이브러리


# ===== 페이지 설정 =====
# 브라우저 탭 제목과 넓은 화면 설정 (가장 먼저 실행되는 st 명령이어야 함)
st.set_page_config(page_title="Titanic 대시보드", layout="wide")


# ===== 상수 =====
# [수정] 나이 슬라이더의 최소·최대값 (전체 범위인지 판단할 때도 사용)
AGE_MIN, AGE_MAX = 0, 80


# ===== 데이터 불러오기 =====
# st.cache_data: 처음 한 번만 파일을 읽고, 그다음부터는 저장해 둔 결과를 재사용
@st.cache_data
def load_data():
    # titanic.csv 파일을 읽어서 돌려주기
    return pd.read_csv("titanic.csv")

# 데이터를 df에 담기
df = load_data()


# ===== 함수: 데이터 필터 =====
# 성별·객실 등급·나이 조건을 모두 만족하는 승객만 골라내는 함수
def filter_data(df, sexes, classes, age_range):
    # 나이 범위에서 최소값과 최대값 꺼내기
    min_age, max_age = age_range
    # 조건 1: 성별이 선택 목록 안에 있는 행
    cond_sex = df["sex"].isin(sexes)
    # 조건 2: 객실 등급이 선택 목록 안에 있는 행
    cond_class = df["pclass"].isin(classes)
    # 조건 3: 나이가 범위 안에 있는 행 (양 끝 포함)
    cond_age = df["age"].between(min_age, max_age)
    # [수정] 슬라이더가 전체 범위(0~80)이면 나이 결측 승객도 포함하기
    if (min_age, max_age) == (AGE_MIN, AGE_MAX):
        # [수정] 범위 안에 있거나(|) 나이가 비어 있는 행도 통과
        cond_age = cond_age | df["age"].isna()
    # 세 조건을 모두 만족하는 행만 반환
    return df[cond_sex & cond_class & cond_age]


# ===== 함수: KPI 계산 =====
# 승객 수, 생존율(%), 평균 나이를 계산하는 함수
def kpi(df):
    # 데이터가 비어 있으면 0, 0, 0 반환
    if df.empty:
        return 0, 0, 0
    # 승객 수: 행 개수
    count = len(df)
    # 생존율(%): survived(0/1) 평균 × 100, 소수 첫째 자리 반올림
    survival_rate = round(float(df["survived"].mean() * 100), 1)
    # 평균 나이: 결측치 제외하고 계산
    mean_age = df["age"].mean()
    # 나이 정보가 하나도 없으면 0, 있으면 소수 첫째 자리 반올림
    avg_age = 0 if pd.isna(mean_age) else round(float(mean_age), 1)
    return count, survival_rate, avg_age


# ===== 함수: 차트 =====
# 객실 등급별 생존율(%) 막대그래프를 만드는 함수
def class_rate_bar(df):
    # 등급별 생존율(%) 계산 후 표 모양으로 정리
    rate = (df.groupby("pclass")["survived"].mean() * 100).round(1).reset_index()
    # 열 이름을 한글로 바꾸기
    rate.columns = ["객실 등급", "생존율"]
    # 등급을 "1등급"처럼 글자로 바꿔 x축을 범주로 표시
    rate["객실 등급"] = rate["객실 등급"].astype(str) + "등급"
    # 막대그래프 만들기, 막대 위에 생존율 값 표시
    fig = px.bar(rate, x="객실 등급", y="생존율", text="생존율",
                 title="객실 등급별 생존율(%)")
    # 값 뒤에 % 붙이고 막대 위쪽에 표시
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    # y축 범위를 0~100으로 고정
    fig.update_layout(yaxis_range=[0, 100])
    return fig


# 생존 여부로 색을 나눈 나이 히스토그램을 만드는 함수
def age_hist(df):
    # 원본은 그대로 두고 survived를 "사망"/"생존" 글자로 바꾼 복사본 만들기
    plot_df = df.assign(생존여부=df["survived"].map({0: "사망", 1: "생존"}))
    # 나이 히스토그램, 생존 여부로 색 구분, 겹쳐 그리기, 투명도 0.6
    fig = px.histogram(plot_df, x="age", color="생존여부",
                       barmode="overlay", opacity=0.6,
                       category_orders={"생존여부": ["사망", "생존"]},
                       labels={"age": "나이"},
                       title="생존 여부별 나이 분포")
    # y축 이름을 한글로 바꾸기
    fig.update_layout(yaxis_title="승객 수")
    return fig


# ===== 제목 =====
st.title("타이타닉, 누가 살아남았나?")


# ===== 사이드바 =====
# 사이드바 위쪽에 안내 제목 표시
st.sidebar.header("필터")

# 성별 선택: 여러 개 선택 가능, 기본값은 둘 다 선택
sexes = st.sidebar.multiselect("성별", ["male", "female"], ["male", "female"])

# 객실 등급 선택: 여러 개 선택 가능, 기본값은 1·2·3 모두 선택
classes = st.sidebar.multiselect("객실 등급", [1, 2, 3], [1, 2, 3])

# [수정] 나이 범위 선택: 상수로 범위 지정, 기본값은 전체 범위
age_range = st.sidebar.slider("나이 범위", AGE_MIN, AGE_MAX, (AGE_MIN, AGE_MAX))

# [수정] 전체 범위일 때 결측 포함 여부를 사이드바에 안내
if age_range == (AGE_MIN, AGE_MAX):
    st.sidebar.caption("전체 범위: 나이 정보가 없는 승객도 포함")
else:
    st.sidebar.caption("범위 지정: 나이 정보가 없는 승객은 제외")


# ===== 입력값 검사 =====
# [수정] 성별이나 객실 등급을 하나도 고르지 않았으면 안내하고 멈추기
if not sexes or not classes:
    st.warning("성별과 객실 등급을 각각 하나 이상 선택하세요.")
    st.stop()


# ===== 데이터 필터 적용 =====
# 사이드바에서 고른 조건으로 승객 골라내기
filtered = filter_data(df, sexes, classes, age_range)

# [수정] 필터 결과가 0명이면 안내하고 멈추기
if filtered.empty:
    st.info("조건에 맞는 승객이 없습니다. 필터를 다시 선택하세요.")
    st.stop()


# ===== 본문: KPI 카드 =====
# 필터된 데이터로 승객 수, 생존율, 평균 나이 계산하기
count, survival_rate, avg_age = kpi(filtered)

# 화면을 가로 3칸으로 나누기
col1, col2, col3 = st.columns(3)

# 첫 번째 칸: 승객 수 카드
col1.metric("승객 수", f"{count}명")

# 두 번째 칸: 생존율 카드
col2.metric("생존율", f"{survival_rate}%")

# 세 번째 칸: 평균 나이 카드
col3.metric("평균 나이", f"{avg_age}세")


# ===== 본문: 차트 =====
# KPI 아래 화면을 가로 2칸으로 나누기
left, right = st.columns(2)

# 왼쪽 칸: 객실 등급별 생존율 막대그래프
left.plotly_chart(class_rate_bar(filtered))

# 오른쪽 칸: 생존 여부별 나이 히스토그램
right.plotly_chart(age_hist(filtered))


# ===== 본문: 데이터 표 =====
# 접었다 펼 수 있는 "데이터 보기" 상자 만들기 (처음에는 접힌 상태)
with st.expander("데이터 보기"):
    # 상자 안에 필터된 승객 표 보여 주기
    st.dataframe(filtered)
