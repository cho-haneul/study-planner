import os
import sys
from urllib.parse import parse_qs

# Vercel Serverless Function 환경에서 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel Serverless 환경에서 rewrite로 인해 경로가 유실되는 현상 방지
class VercelPathFix:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. 쿼리스트링에 __path가 전달된 경우 우선 복원
        qs = parse_qs(environ.get('QUERY_STRING', ''))
        if '__path' in qs and qs['__path']:
            val = qs['__path'][0].lstrip('/')
            environ['PATH_INFO'] = ('/' + val) if val else '/'
        else:
            # 2. Vercel 원본 경로 헤더 확인
            orig = environ.get('HTTP_X_MATCHED_PATH') or environ.get('HTTP_X_FORWARDED_PATH')
            if orig and not orig.startswith('/api/index'):
                environ['PATH_INFO'] = orig
            else:
                path_info = environ.get('PATH_INFO', '')
                if path_info.startswith('/api/index'):
                    path_info = path_info[len('/api/index'):] or '/'
                    environ['PATH_INFO'] = path_info
                elif path_info.startswith('/api'):
                    path_info = path_info[len('/api'):] or '/'
                    environ['PATH_INFO'] = path_info
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFix(app.wsgi_app)
