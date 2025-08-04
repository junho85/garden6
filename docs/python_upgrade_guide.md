# Python 버전 업그레이드 가이드

이 문서는 Django 프로젝트의 Python 버전을 업그레이드하는 과정을 정리한 가이드입니다.  
Garden6 프로젝트의 Python 3.7 → 3.11 업그레이드 경험을 바탕으로 작성되었습니다.

## 1. 개요

### 1.1 업그레이드 이유
- Python 3.7 공식 지원 종료 (2023년 6월)
- 최신 라이브러리 호환성
- 성능 향상 및 새로운 언어 기능 활용
- 보안 업데이트

### 1.2 주요 변경사항
- Python: 3.7.x → 3.11.x
- Django: 3.0.x → 4.2.x
- 관련 패키지들 최신 버전으로 업데이트

## 2. 사전 준비

### 2.1 현재 환경 백업
```bash
# 현재 패키지 목록 저장
pip freeze > requirements_backup.txt

# 현재 Python 버전 확인
python --version
```

### 2.2 호환성 확인
- [Python 3.11 변경사항](https://docs.python.org/3/whatsnew/3.11.html) 확인
- 사용 중인 주요 패키지의 Python 3.11 지원 여부 확인
- Django 버전별 Python 지원 매트릭스 확인

## 3. 업그레이드 절차

### 3.1 새로운 가상환경 생성
```bash
# Python 3.11 설치 (macOS)
brew install python@3.11

# 새로운 가상환경 생성
python3.11 -m venv .venv_new

# 가상환경 활성화
source .venv_new/bin/activate
```

### 3.2 requirements.txt 업데이트

**기존 requirements.txt (Python 3.7)**
```txt
Django==3.0.3
pymongo==3.10.1
slackclient==2.5.0
# ... 기타 패키지
```

**새로운 requirements.txt (Python 3.11)**
```txt
Django>=4.2,<5.0
pymongo>=4.0.0
slackclient==2.9.4
PyYAML>=6.0
Markdown>=3.4.0
requests>=2.28.0
```

### 3.3 패키지 설치 및 테스트
```bash
# 새로운 requirements.txt로 패키지 설치
pip install -r requirements.txt

# 테스트 실행
python manage.py test

# 개발 서버 실행
python manage.py runserver
```

## 4. 코드 수정 사항

### 4.1 Django 설정 파일 업데이트

**settings.py 수정사항**
```python
# 기존 (Django 3.0)
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 변경 (Django 4.2)
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
```

### 4.2 deprecated 기능 대체
- `django.conf.urls.url()` → `django.urls.re_path()`
- `force_text()` → `force_str()`
- 기타 Django 4.2 변경사항 반영

### 4.3 타입 힌트 추가 (선택사항)
Python 3.11의 향상된 타입 힌트 기능 활용:
```python
from typing import List, Dict, Optional

def process_data(items: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in items}
```

## 5. 테스트 및 검증

### 5.1 단위 테스트
```bash
# Django 테스트 실행
python manage.py test

# 특정 앱 테스트
python manage.py test attendance
```

### 5.2 통합 테스트
- 모든 주요 기능 동작 확인
- API 엔드포인트 테스트
- 데이터베이스 연결 및 쿼리 확인

### 5.3 성능 테스트
- 응답 시간 비교
- 메모리 사용량 확인
- CPU 사용률 모니터링

## 6. 배포

### 6.1 단계적 배포
1. 개발 환경에서 충분한 테스트
2. 스테이징 환경 배포
3. 일부 사용자 대상 카나리 배포
4. 전체 프로덕션 배포

### 6.2 롤백 계획
- 이전 버전의 가상환경 보관
- 데이터베이스 백업
- 빠른 롤백을 위한 스크립트 준비

## 7. 주의사항

### 7.1 호환성 이슈
- `collections.abc` 모듈 import 변경
- `asyncio` 관련 변경사항
- 문자열 포맷팅 개선사항

### 7.2 성능 고려사항
- Python 3.11은 일반적으로 10-60% 더 빠름
- 메모리 사용량 개선
- 시작 시간 단축

### 7.3 보안 개선사항
- 최신 보안 패치 적용
- SSL/TLS 라이브러리 업데이트
- 취약점 스캔 도구 실행

## 8. 문제 해결

### 8.1 일반적인 오류들

**ImportError**
```python
# 문제
from collections import Iterable

# 해결
from collections.abc import Iterable
```

**Django 관련 오류**
```python
# 문제
from django.utils.encoding import force_text

# 해결
from django.utils.encoding import force_str
```

### 8.2 디버깅 팁
- `pip check` 명령으로 패키지 호환성 확인
- `python -m py_compile` 로 구문 오류 확인
- 로그 레벨을 DEBUG로 설정하여 상세 정보 확인

## 9. 참고 자료

- [Python 3.11 Release Notes](https://docs.python.org/3/whatsnew/3.11.html)
- [Django 4.2 Release Notes](https://docs.djangoproject.com/en/4.2/releases/4.2/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Django Upgrade Guide](https://docs.djangoproject.com/en/4.2/howto/upgrade-version/)

## 결론

Python 버전 업그레이드는 신중한 계획과 테스트가 필요한 작업입니다. 이 가이드를 참고하여 체계적으로 진행하면 안전하게 업그레이드할 수 있습니다. 특히 다음 사항을 기억하세요:

1. **충분한 테스트**: 모든 기능을 철저히 테스트
2. **단계적 접근**: 한 번에 모든 것을 바꾸지 말고 점진적으로 진행
3. **백업 준비**: 언제든 롤백할 수 있도록 준비
4. **문서화**: 변경사항을 상세히 기록

업그레이드 후에는 성능 향상과 새로운 기능들을 활용할 수 있으며, 장기적으로 유지보수가 더 쉬워집니다.