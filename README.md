# 판례 AI 학습 서비스

공식 법률 데이터 기반 RAG와 Gemini를 사용해 판례를 학습용으로 구조화하는 서비스입니다.

## 문서

- `PRD.md`: 제품 요구사항 정의서
- `IMPLEMENTATION_ROADMAP.md`: 단계별 구현 로드맵과 체크리스트
- `LAWINFO_INTEGRATION_GUIDE.md`: 국가법령정보센터 Friendly URL 및 Open API 연동 가이드
- `DEPLOY_RENDER.md`: Render 무료 배포 가이드

## 프로젝트 구조

```txt
backend/
  app/
    main.py
    core/
frontend/
  src/
    app/
```

## 백엔드 로컬 실행

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

헬스체크:

```bash
curl http://127.0.0.1:8000/api/health
```

## 프론트엔드 로컬 실행

```bash
cd frontend
npm install
npm run dev
```

접속:

```txt
http://localhost:3000
```

## 환경 변수

루트의 `.env.example`을 참고해 실제 `.env`를 생성합니다. API 키는 Git에 커밋하지 않습니다.

## 외부 공식 API

국가법령정보센터 Open API는 `LAWINFO_API_KEY`와 `LAWINFO_BASE_URL`을 사용합니다.

기본 URL:

```txt
https://www.law.go.kr/DRF
```

현재 백엔드 어댑터는 다음 API 흐름을 기준으로 구성되어 있습니다.

- 판례 목록 검색: `lawSearch.do?target=prec&type=JSON`
- 판례 본문 조회: `lawService.do?target=prec&type=HTML&mobileYn=Y`
- 법령 검색: `lawSearch.do?target=law&type=JSON`
- 법령 조항 조회: `lawService.do?target=lawjosub&type=JSON`

라이브 검증은 실제 API 인증값을 `.env`에 넣은 뒤 진행합니다.
