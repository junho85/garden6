# Garden6 📝

정원사들 시즌6 출석부 시스템입니다. Slack #commit 채널의 메시지를 수집하여 자동으로 출석부를 관리합니다.

🌐 **[Live Demo](https://garden6.junho85.pe.kr/)**

## 📋 Overview

- **목적**: 정원사들의 일일 커밋 활동을 추적하고 관리
- **데이터 소스**: Slack #commit 채널 메시지
- **기술 스택**: Django 4.2, Python 3.11, MongoDB, SQLite

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- MongoDB (선택사항)
- Virtual Environment

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/junho85/garden6.git
   cd garden6
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database setup**
   ```bash
   python manage.py migrate
   ```

5. **Start development server**
   ```bash
   python manage.py runserver
   ```

### With Docker (MongoDB)

MongoDB를 사용하는 경우:
```bash
docker start mymongo
```

## 📁 Project Structure

```
garden6/
├── attendance/          # 출석부 관리 앱
├── common/             # 공통 기능
├── tools/              # 관리자 도구
├── templates/          # 템플릿 파일
├── docs/              # 프로젝트 문서
├── archive/           # 마이그레이션 관련
└── requirements.txt   # Python 의존성
```

## 🔧 Configuration

자세한 설정 방법은 [docs](docs) 폴더를 참고하세요:

- [MongoDB 설정](docs/01.mongodb.md)
- [Django 설정](docs/02.django.md)
- [Apache HTTPD WSGI 설정](docs/04.apache_httpd_wsgi.md)
- [Slack API 설정](docs/21.slack_api.md)

## 📚 Documentation

- **[GitHub Repository](https://github.com/junho85/garden6)**
- **[Wiki](https://github.com/junho85/garden6/wiki)**
- **[Docs Folder](docs/README.md)**

## 🔗 Related Projects

- [Garden5](https://github.com/junho85/garden5) - 이전 시즌
- [Garden4](https://github.com/junho85/garden4) - 이전 시즌

## 📊 Features

- ✅ Slack 메시지 자동 수집
- ✅ 사용자별 출석 현황 추적
- ✅ 웹 기반 관리 인터페이스
- ✅ 관리자 도구
- ✅ 다양한 출석 통계