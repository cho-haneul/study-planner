import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, make_response, send_from_directory
from dotenv import load_dotenv
import requests
from google import genai
from google.genai import types

# .env 환경변수 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH, override=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("StudyPlanner")

from urllib.parse import parse_qs

app = Flask(__name__)

# Vercel Serverless rewrite 환경에서 실제 요청 경로 복원
class VercelPathFix:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        qs = parse_qs(environ.get('QUERY_STRING', ''))
        if '__path' in qs and qs['__path'] and qs['__path'][0]:
            environ['PATH_INFO'] = '/' + qs['__path'][0].lstrip('/')
        elif environ.get('PATH_INFO') in ('/api', '/api/index'):
            environ['PATH_INFO'] = '/'
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFix(app.wsgi_app)

def get_gemini_client():
    """요청 시점에 .env를 확인하여 Gemini 클라이언트 생성"""
    load_dotenv(ENV_PATH, override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    
    if not api_key:
        return None, ".env 파일에 GEMINI_API_KEY가 없습니다."
    
    try:
        client = genai.Client(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"클라이언트 생성 실패: {str(e)}"


def get_available_models(client):
    """구글 서버에서 현재 사용 가능한 실제 모델들을 자동 조회"""
    try:
        models = []
        for m in client.models.list():
            name = m.name if hasattr(m, "name") else str(m)
            clean_name = name.replace("models/", "")
            models.append(clean_name)
        logger.info(f"구글 사용 가능 모델 목록: {models[:5]} (총 {len(models)}개)")
        return models
    except Exception as e:
        logger.warning(f"모델 목록 자동 조회 중 예외: {str(e)}")
        return ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]


def search_web_serper(query: str) -> str:
    """Serper.dev 웹 검색 (선택적)"""
    serper_key = os.getenv("SERPER_API_KEY", "").strip()
    if not serper_key:
        return ""

    logger.info(f"[Serper 검색] '{query}'")
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": serper_key, "Content-Type": "application/json"}
    payload = {"q": query, "gl": "kr", "hl": "ko", "num": 3}

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=4)
        if res.status_code == 200:
            organic = res.json().get("organic", [])
            if not organic:
                return ""
            summary = ["### 최신 웹 검색 참고 자료:"]
            for idx, item in enumerate(organic[:3], 1):
                summary.append(f"{idx}. [{item.get('title')}]({item.get('link')})\n   {item.get('snippet')}")
            return "\n".join(summary)
    except Exception as e:
        logger.warning(f"Serper 검색 건너뜀: {str(e)}")
    return ""


@app.route('/sw.js')
@app.route('/api/sw.js')
@app.route('/api/index/sw.js')
def service_worker():
    """PWA Service Worker 서빙"""
    response = make_response(send_from_directory(app.static_folder, 'sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response


@app.route('/manifest.json')
@app.route('/api/manifest.json')
@app.route('/api/index/manifest.json')
def manifest():
    """PWA Web App Manifest 서빙"""
    response = make_response(send_from_directory(app.static_folder, 'manifest.json'))
    response.headers['Content-Type'] = 'application/manifest+json'
    return response


@app.route('/static/<path:filename>')
def custom_static(filename):
    """정적 에셋 서빙"""
    return send_from_directory(app.static_folder, filename)


@app.route("/")
@app.route("/api")
@app.route("/api/index")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
@app.route("/api/generate", methods=["POST"])
@app.route("/api/index/generate", methods=["POST"])
def generate_plan():
    start_time = datetime.now()
    logger.info("=== [플랜 생성 요청 수신] ===")

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "요청 형식이 올바르지 않습니다."}), 400

    goal = data.get("goal", "").strip()
    exam_date = data.get("exam_date", "").strip()
    daily_hours = data.get("daily_hours", "").strip()
    weakness = data.get("weakness", "").strip()
    level = data.get("level", "보통").strip()
    study_style = data.get("study_style", "개념 중심").strip()

    if not goal or not exam_date or not daily_hours:
        return jsonify({"success": False, "error": "필수 입력 항목을 입력해 주세요."}), 400

    try:
        target_dt = datetime.strptime(exam_date, "%Y-%m-%d")
        days_left = (target_dt.date() - datetime.now().date()).days
        if days_left < 0:
            return jsonify({"success": False, "error": "시험일은 오늘 이후 날짜여야 합니다."}), 400
    except ValueError:
        return jsonify({"success": False, "error": "날짜 형식이 올바르지 않습니다."}), 400

    genai_client, err_msg = get_gemini_client()
    if not genai_client:
        return jsonify({"success": False, "error": err_msg}), 400

    search_context = search_web_serper(f"{goal} 시험 공부법 커리큘럼")

    system_instruction = (
        "당신은 상위 0.1% 합격생들을 다수 배출한 '10년 차 전문 입시 및 자격증 학습 컨설턴트'입니다. "
        "단순한 일정 나열을 넘어, 인지심리학과 에빙하우스 망각곡선, 효율적인 시간 배분 원칙을 적용하여 "
        "수험생이 압도적인 몰입감과 실행력을 발휘할 수 있는 실전 맞춤형 학습 솔루션을 제시합니다.\n\n"
        "반드시 아래 6대 핵심 구성을 마크다운(Markdown) 형식으로 체계적으로 작성하세요:\n"
        "1. 🎯 총평 및 학습 로드맵 (목표 달성 핵심 전략 & D-Day 페이스 조절)\n"
        "2. 📅 주간 맞춤형 학습 계획 (주차별 집중 테마 및 단계별 마일스톤)\n"
        "3. ⏰ 상세 일일 실천 루틴 (시간대별 추천 배분 및 체크박스 '- [ ] ' 형식의 구체적 실천 과제 목록)\n"
        "4. 🧠 에빙하우스 망각곡선 기반 과학적 복습 주기 (당일-3일-7일-14일 주기적 누적 복습 가이드)\n"
        "5. ✍️ 취약 영역 극복을 위한 셀프 점검 문항 (이해도 측정을 위한 핵심 질문 3~4선)\n"
        "6. 📝 주간 진도 체크리스트 및 학습 회고(KPT: Keep, Problem, Try) 가이드\n\n"
        "말투는 전문적이면서도 수험생의 사기를 북돋아 주는 따뜻하고 확신에 찬 어조를 사용하세요. "
        "일일 실천 과제에는 사용자가 직접 체크할 수 있도록 반드시 마크다운 체크박스 `- [ ] ` 문법을 적극 포함해 주세요."
    )

    user_prompt = f"""
[수강생 프로필]
- 목표 시험 / 학습 주제: {goal}
- 시험 예정일: {exam_date} (D-{days_left}일 남음)
- 현재 수준: {level}
- 하루 가용 학습 시간: {daily_hours}시간
- 가장 취약한 영역: {weakness if weakness else "전체 기본기 확립 필요"}
- 선호하는 학습 방식: {study_style}

{search_context}

위 수강생을 위한 고품질 맞춤형 6대 영역 학습 플랜을 마크다운으로 상세히 작성해 주세요.
"""

    # 1. 구글 서버에서 실제 사용 가능한 모델 목록 자동 조회
    available_models = get_available_models(genai_client)

    # 2. flash 계열 모델 우선 정렬
    flash_models = [m for m in available_models if "flash" in m.lower() and "thinking" not in m.lower()]
    other_models = [m for m in available_models if m not in flash_models]
    models_to_try = flash_models + other_models

    if not models_to_try:
        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash"]

    plan_markdown = ""
    last_err = ""

    # 3. 발견된 모델로 순차 호출
    for m in models_to_try[:4]:
        try:
            logger.info(f"구글 자동 감지 모델 '{m}' 호출 시도...")
            resp = genai_client.models.generate_content(
                model=m,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                )
            )
            if resp and resp.text:
                plan_markdown = resp.text
                logger.info(f"🎉 모델 '{m}' 호출 대성공! 응답 완료.")
                break
        except Exception as e:
            last_err = str(e)
            logger.warning(f"모델 '{m}' 시도 실패: {last_err}")

    if not plan_markdown:
        return jsonify({"success": False, "error": f"AI 생성 실패: {last_err}"}), 500

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"=== [플랜 생성 완료] 총 소요 시간: {elapsed:.2f}초 ===")

    return jsonify({
        "success": True,
        "goal": goal,
        "days_left": days_left,
        "plan_markdown": plan_markdown
    })

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=True)
