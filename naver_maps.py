import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import LocateControl
import requests
import streamlit.components.v1 as components
from datetime import datetime

# --- API 설정 ---
# 네이버 API
NAVER_CLIENT_ID = 'qo9JkJuflzQZg8UTD7Ns'
NAVER_CLIENT_SECRET = 'sQHQe1gafQ'

# 날씨 API (사용자가 제공한 키 적용)
WEATHER_API_KEY = 'd561aeb56991d4ee128fa0e544170f48'

# --- 데이터 설정: 최적 동선 순서 (A -> E) ---
# 구좌(북동) -> 성산(동부) -> 한라산(중앙) -> 서귀포(남부) -> 중문(남서) 순으로 구성
JEJU_STOPS = [
    {"id": "A", "name": "만장굴", "coords": [33.5284, 126.7716], "desc": "거대 용암동굴의 신비 (북동부)"},
    {"id": "B", "name": "성산일출봉", "coords": [33.4581, 126.9426], "desc": "유네스코 세계자연유산, 일출 명소 (동부)"},
    {"id": "C", "name": "한라산(성판악)", "coords": [33.3846, 126.6171], "desc": "제주의 영산, 백록담 산행 (중앙)"},
    {"id": "D", "name": "천지연 폭포", "coords": [33.2460, 126.5545], "desc": "아름다운 밤의 폭포 (남부)"},
    {"id": "E", "name": "대포주상절리", "coords": [33.2378, 126.4251], "desc": "자연이 만든 육각형 기둥 절벽 (남서부)"}
]

# --- 함수 정의 ---
def get_address_from_coords(lat, lng):
    """네이버 Reverse Geocoding API를 사용하여 좌표를 주소로 변환"""
    url = f"https://naveropenapi.apigw.ntruss.com/map-reversegeocode/v2/gc?coords={lng},{lat}&output=json"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None

def get_jeju_weather():
    """OpenWeatherMap을 이용한 제주도 실시간 날씨 가져오기"""
    lat, lon = 33.4890, 126.4983 # 제주 시청 기준
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=kr"
    try:
        res = requests.get(url).json()
        return res
    except:
        return None

# --- Streamlit UI 설정 ---
st.set_page_config(page_title="제주 AI 여행 대시보드", layout="wide")

# 사이드바: 날씨 정보 및 여행 요약
with st.sidebar:
    st.header("🌦️ 제주 실시간 정보")
    weather = get_jeju_weather()
    if weather and 'main' in weather:
        st.metric("현재 온도", f"{weather['main']['temp']}°C")
        st.write(f"상태: {weather['weather'][0]['description']}")
        st.write(f"습도: {weather['main']['humidity']}%")
    else:
        st.warning("날씨 API 정보를 불러올 수 없습니다.")
    
    st.divider()
    st.header("📝 최적 여행 동선 (A-E)")
    for stop in JEJU_STOPS:
        st.write(f"**{stop['id']}. {stop['name']}**")
        st.caption(stop['desc'])

# 메인 화면
st.title("🌴 제주도 AI 여행 추천 & 최적 동선")
st.markdown(f"**{JEJU_STOPS[0]['name']}(A)**에서 **{JEJU_STOPS[-1]['name']}(E)**까지 이어지는 최적의 여행 코스입니다.")

# 상단 대시보드 카드
col1, col2, col3 = st.columns(3)
col1.metric("총 방문지", "5곳")
col2.metric("권장 일정", "2박 3일")
col3.metric("총 이동거리", "약 82km")

st.divider()

# 지도를 위한 메인 레이아웃
m_col1, m_col2 = st.columns([3, 2])

with m_col1:
    st.subheader("📍 제주 여행 동선 지도 (A → E)")
    
    # 지도 중심 (제주도 중앙)
    m = folium.Map(location=[33.38, 126.65], zoom_start=10)

    # 동선 시각화용 좌표 리스트 (마커용)
    # route_coords = [stop['coords'] for stop in JEJU_STOPS] # 단일 PolyLine용으로, 여기서는 주석 처리

    # 1. 마커 추가 (A, B, C, D, E 라벨 적용)
    for stop in JEJU_STOPS:
        # 번호별 색상 차별화 (시작점 A는 빨간색, 나머지는 파란색)
        icon_color = 'red' if stop['id'] == 'A' else 'blue'
        
        folium.Marker(
            location=stop['coords'],
            popup=f"<b>[{stop['id']}] {stop['name']}</b><br>{stop['desc']}",
            tooltip=f"{stop['id']}: {stop['name']}",
            icon=folium.Icon(color=icon_color, icon='info-sign')
        ).add_to(m)

    # 2. 이동 경로 선(PolyLine) 그리기 - 구간별 다색 적용
    # 요청하신 빨강, 주황, 노랑, 초록 순서로 구간에 색상을 적용합니다.
    segment_colors = ['red', 'orange', '#FFD700', 'green'] # 노랑은 가시성을 위해 골드색(#FFD700) 사용

    for i in range(len(JEJU_STOPS) - 1):
        start_stop = JEJU_STOPS[i]
        end_stop = JEJU_STOPS[i+1]
        
        folium.PolyLine(
            locations=[start_stop['coords'], end_stop['coords']],
            color=segment_colors[i],
            weight=6, # 색상이 잘 보이도록 두께를 약간 늘림
            opacity=0.8,
            tooltip=f"{start_stop['name']}({start_stop['id']}) ➡️ {end_stop['name']}({end_stop['id']})"
        ).add_to(m)

    # 3. 내 위치 찾기 컨트롤
    LocateControl(
        auto_start=False,
        flyTo=True,
        strings={"title": "내 위치 찾기", "popup": "현재 위치"}
    ).add_to(m)

    # 지도 렌더링
    output = st_folium(m, width="100%", height=600)

with m_col2:
    st.subheader("🗺️ 네이버 실시간 상세지도")
    
    # 현재 선택된 장소 혹은 기본 A장소 표시
    target = JEJU_STOPS[0]
    naver_url = f"https://map.naver.com/v5/?c={target['coords'][1]},{target['coords'][0]},15,0,0,0,dh"
    
    components.iframe(naver_url, height=600, scrolling=True)

# --- 하단 주소 변환 정보 ---
st.divider()
if output.get('last_clicked'):
    lat = output['last_clicked']['lat']
    lng = output['last_clicked']['lng']
    address_data = get_address_from_coords(lat, lng)
    
    if address_data:
        try:
            res = address_data['results'][0]['region']
            addr = f"{res['area1']['name']} {res['area2']['name']} {res['area3']['name']}"
            st.success(f"📍 클릭하신 지점의 주소: {addr}")
        except:
            st.write(f"좌표: {lat}, {lng} (상세 주소가 없는 지역입니다)")
    else:
        st.write(f"좌표: {lat}, {lng}")
else:
    st.info("💡 지도의 마커나 임의의 지점을 클릭하면 네이버 API를 통해 주소를 확인할 수 있습니다.")