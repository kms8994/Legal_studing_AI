# Render 배포 가이드

본 문서는 현재 FastAPI MVP를 Render Free Web Service로 배포하는 절차를 정리한다.

현재 구조에서는 FastAPI가 `/`에서 프론트 HTML을 서빙하고, `/api/*`에서 API를 제공한다. 따라서 Render에는 백엔드 서비스 하나만 배포하면 된다.

---

## 1. 배포 구조

```txt
Render Web Service
→ Dockerfile
→ uvicorn app.main:app
→ /          MVP 프론트
→ /api/*     FastAPI API
```

---

## 2. 준비물

1. GitHub 저장소
2. Render 계정
3. 국가법령정보센터 Open API `OC` 값
4. 선택 사항: Gemini API key

---

## 3. 포함된 배포 파일

| 파일 | 용도 |
| :--- | :--- |
| `Dockerfile` | Render Docker 배포 |
| `.dockerignore` | Docker build 제외 파일 |
| `render.yaml` | Render Blueprint 설정 |

---

## 4. Render 배포 방법

### 4.1 GitHub에 코드 push

프로젝트를 GitHub 저장소에 올린다.

### 4.2 Render에서 Web Service 생성

1. Render Dashboard 접속
2. `New +` 선택
3. `Web Service` 선택
4. GitHub 저장소 연결
5. Runtime은 Docker 사용
6. Plan은 Free 선택

또는 `render.yaml`을 이용해 Blueprint로 생성할 수 있다.

### 4.3 환경변수 설정

Render Dashboard의 Environment에서 아래 값을 설정한다.

필수:

```txt
APP_ENV=production
APP_NAME=Case AI Learning Service
LAWINFO_API_KEY=국가법령정보센터_OC_값
LAWINFO_BASE_URL=http://www.law.go.kr/DRF
```

선택:

```txt
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
VECTOR_TOP_K=5
RETRIEVAL_SCORE_THRESHOLD=0.72
```

초기 MVP는 `LAWINFO_API_KEY`만 있어도 충분하다.

---

## 5. 배포 후 확인

배포가 끝나면 Render가 제공하는 URL에서 확인한다.

```txt
https://your-service.onrender.com/
https://your-service.onrender.com/api/health
```

정상 응답 예:

```json
{
  "status": "ok",
  "environment": "production"
}
```

---

## 6. 국가법령 API IP 등록 확인

국가법령정보센터 Open API는 요청 서버의 IP/도메인을 검증할 수 있다.

Render에서 공식 API 호출이 실패하고 다음 메시지가 나오면:

```txt
사용자 정보 검증에 실패하였습니다.
```

Render 서비스의 outbound IP를 확인해 국가법령정보센터 Open API 신청 정보에 등록해야 한다.

Render Dashboard에서 서비스의 networking/outbound IP 정보를 확인한다. Render Free 플랜에서는 outbound IP가 고정 단일 IP가 아닐 수 있으므로, 국가법령정보센터가 해당 IP 또는 IP 범위를 허용하는지 확인해야 한다.

등록이 어렵다면 다음 대안이 필요하다.

1. Render 유료 static outbound IP 기능 사용 가능 여부 확인
2. Fly.io static egress IP 사용
3. AWS EC2 / Oracle Cloud / 기타 VPS 사용

---

## 7. 무료 플랜 주의 사항

Render Free Web Service는 일정 시간 사용하지 않으면 sleep 상태가 될 수 있다.

영향:

- 첫 접속이 느릴 수 있음
- API 호출이 처음에 지연될 수 있음

초기 개발/시연용으로는 충분하지만, 실제 운영에서는 유료 플랜 또는 VPS를 고려한다.

---

## 8. 로컬과 Render 차이

로컬:

```txt
http://127.0.0.1:8000
```

Render:

```txt
https://your-service.onrender.com
```

국가법령 API 등록은 로컬 PC IP가 아니라 Render에서 외부로 나가는 IP/도메인을 기준으로 해야 한다.

---

## 9. 문제 해결

### `LAWINFO_API_KEY가 설정되어 있지 않습니다`

Render 환경변수에 `LAWINFO_API_KEY`를 추가하고 서비스를 재배포한다.

### `사용자 정보 검증에 실패하였습니다`

국가법령정보센터 Open API 관리 페이지에서 Render outbound IP 또는 도메인을 등록한다.

### `필수 입력값이 존재하지 않습니다`

요청 파라미터가 공식 API 요구사항과 맞는지 확인한다.

현재 구현 기준:

- 판례 검색: `lawSearch.do?target=prec&type=JSON`
- 판례번호 검색: `lawSearch.do?target=prec&type=JSON&nb=...`
- 판례 본문: `lawService.do?target=prec&type=HTML&mobileYn=Y`

### 첫 접속이 느림

Render Free 플랜의 sleep 이후 cold start일 수 있다.
