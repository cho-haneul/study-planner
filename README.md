# 📚 AI 맞춤형 학습 플래너 (AI Study Planner)

> **Google Gemini AI와 Python Flask 기반의 수험생 맞춤형 6대 영역 학습 로드맵 자동 생성 웹 애플리케이션**

목표 시험, 시험일, 가용 시간, 취약 영역, 선호 학습 방식을 입력받아 **인지심리학과 에빙하우스 망각곡선 복습 이론**을 적용한 초개인화 학습 플랜을 단 몇 초 만에 체계적으로 수립해 줍니다.

---

## ✨ 주요 기능 (Key Features)

1. **상세 조건 기반의 수험생 맞춤 분석**
   - 목표 시험/주제, 시험 예정일(D-Day 자동 계산), 일일 가용 학습 시간
   - 현재 수준(초보/보통/유경험자), 선호 학습 방식(개념 중심/기출 풀이/오답 위주/단기 벼락치기)
   - 집중 공략할 취약 영역 입력

2. **과학적 6대 영역 학습 플랜 자동 생성**
   - 🎯 **총평 및 로드맵**: 목표 달성 핵심 전략 & D-Day 페이스 조절 가이드
   - 📅 **주간 맞춤형 학습 계획**: 주차별 테마 및 단계별 마일스톤
   - ⏰ **상세 일일 실천 루틴**: 시간대별 추천 배분 및 인터랙티브 체크박스(`- [ ]`) 목록
   - 🧠 **에빙하우스 망각곡선 복습 가이드**: 당일 - 3일 - 7일 - 14일 주기적 누적 복습
   - ✍️ **취약 영역 셀프 점검 문항**: 이해도 측정을 위한 핵심 질문 3~4선
   - 📝 **진도 체크리스트 & KPT 회고**: Keep / Problem / Try 회고 가이드

3. **최신 기술 및 안정성 탑재**
   - **Google GenAI SDK** 적용 및 구글 서버 가용 모델 실시간 자동 감지
   - **Serper.dev 웹 검색 연동** (필요 시 최신 시험 정보/공부법 자동 반영)
   - **보안**: API Key는 `.env`로 격리하여 안전 관리 (Git 노출 차단)

4. **사용자 친화적 프론트엔드 인터랙션**
   - **인터랙티브 체크박스**: 플랜 내 할 일 항목을 브라우저에서 직접 체크
   - **원클릭 복사**: 생성된 마크다운 전체 내용을 클립보드로 원클릭 복사
   - **마크다운 (.md) 파일 다운로드**: 내 컴퓨터에 문서 파일로 즉시 저장
   - **감각적인 로딩 스피너**: 생성 대기 중 상태 시각화

---

## 🛠️ 기술 스택 (Tech Stack)

| 구분 | 기술 / 라이브러리 | 설명 |
| :--- | :--- | :--- |
| **Backend** | Python 3.10+ | 주 프로그래밍 언어 |
| | Flask | 경량 웹 프레임워크 & REST API 라우팅 |
| | google-genai | Google Gemini 최신 SDK (모델 실시간 자동 감지) |
| | python-dotenv | 환경변수(`.env`) 안전 로드 |
| | requests | Serper.dev 웹 검색 API 통신 |
| **Frontend** | HTML5 | 시맨틱 마크업 구조 |
| | CSS3 | 모던 인디고 테마, Flex/Grid 레이아웃, 모바일 반응형 |
| | JavaScript (ES6+) | 비동기 `fetch` 통신, DOM 제어, 동적 체크박스 바인딩 |
| **Version Control** | Git & GitHub | 버전 관리 및 세이브포인트 구축 |

---

## 📁 프로젝트 폴더 구조 (Project Structure)

```text
study-planner/
├── app.py              # Flask 백엔드 서버 및 Gemini API 연동 로직
├── requirements.txt    # 의존성 패키지 목록
├── .env                # API 키 및 환경변수 (보안 파일, .gitignore 처리)
├── .env.example        # 환경변수 예시 파일
├── .gitignore          # Git 추적 제외 설정
├── README.md           # 프로젝트 문서
├── templates/
│   └── index.html      # 프론트엔드 웹 페이지 템플릿
└── static/
    ├── css/
    │   └── style.css   # 스타일시트 (모던 반응형 디자인)
    └── js/
        └── app.js      # 클라이언트 비동기 통신 및 UI 상호작용
```

---

## 🚀 빠른 시작 (Quick Start)

### 1. 가상환경 활성화 및 패키지 설치

```powershell
# 가상환경 활성화 (Windows)
.\venv\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수(.env) 설정

`.env.example`을 복사하여 `.env`를 생성하고 API 키를 입력합니다:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
SERPER_API_KEY=your_serper_api_key_here  # 선택 사항
FLASK_PORT=5000
```

### 3. 애플리케이션 실행

```powershell
python app.py
```

브라우저에서 `http://127.0.0.1:5000`으로 접속하여 맞춤형 플랜 생성을 시작하세요!
