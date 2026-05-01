# 제품 요구사항 정의서 (PRD)
## 판례 AI 학습 서비스
### LegalTech AI Platform for Law Students

**버전:** v4.0  
**작성일:** 2026년 4월  
**상태:** 개발 착수용 PRD  
**핵심 기술:** Gemini 2.5 Flash + RAG + Supabase + pgvector + FastAPI + Next.js  

---

## 1. 서비스 개요

본 서비스는 로스쿨 준비생 및 법학과 학생이 문제집 판례, 판례 번호, PDF, 이미지를 입력하면 공식 법률 데이터 기반 RAG(Retrieval-Augmented Generation) 방식으로 근거 자료를 검색하고, 해당 근거 안에서만 판례를 IRAC 프레임워크로 구조화하며, 판례 변경 여부 검증과 판례 간 비교 분석을 제공하는 AI 기반 법률 학습 도구이다.

핵심 목적은 AI가 법률 조언을 제공하는 것이 아니라, 공식 출처에서 확인 가능한 판례와 법령 정보를 바탕으로 학습자가 판례의 구조와 차이를 더 정확히 이해하도록 돕는 것이다.

### 1.1 핵심 원칙

1. AI는 제공된 입력과 검색된 공식 근거 문서 안에서만 답변한다.
2. 공식 출처가 확인되지 않는 내용은 "확인할 수 없습니다"로 처리한다.
3. 모든 분석 결과에는 근거 판례, 법령 조문, 출처 URL을 함께 제공한다.
4. 법률 조언, 승소 가능성 예측, 사건 해결 전략 제시는 제공하지 않는다.
5. Gemini 호출은 캐시, 중복 방지, 단계별 호출 제한을 통해 최소화한다.

### 1.2 타겟 사용자

| 구분 | 타겟 | 핵심 니즈 | 주요 기능 |
| :--- | :--- | :--- | :--- |
| Primary | 로스쿨 준비생 / 법학과 학생 | 판례 구조화, 수험 검증, 판례 비교 | IRAC 구조화, 판례 변경 검증, 비교 분석 |
| Secondary | 자신의 상황과 유사한 판례를 찾고 싶은 일반 사용자 | 유사 상황 판례 탐색, 대법원 판단 확인 | 유사 판례 매칭, 대법원 판단 요지, 쉬운 언어 설명 |

### 1.3 수익 모델

| 항목 | 무료 플랜 | 구독 플랜 |
| :--- | :--- | :--- |
| 판례 분석 횟수 | 월 5~10회 | 무제한 또는 상한 확대 |
| RAG 검색 | 기본 검색 | 확장 검색 |
| 분석 결과 저장 | X | 제공 |
| 판례 비교 분석 | X | 제공 |
| 폴더 정리 | X | 제공 |
| PDF 내보내기 | X | 제공 |
| 무료 횟수 리셋 | 매월 초 | - |

---

## 2. 서비스 범위

### 2.1 MVP 기능

1. 텍스트, PDF, 이미지, 판례 번호 입력
2. 외부 공식 API 기반 판례/법령 검색
3. 검색 결과 정규화 및 chunking
4. Supabase pgvector 기반 검색 인덱스 저장
5. RAG 기반 IRAC 구조화
6. 전문가용 3종 다이어그램: 당사자 관계도, 사건 흐름, 법리 판단 분기
7. 판례 변경 여부 검증
8. 기본 인증 및 무료 사용량 제한
9. Gemini 중복 호출 방지 캐시
10. 출처와 근거 문단 표시

### 2.2 MVP 제외 기능

1. 결제 연동
2. 고급 판례 비교 분석
3. PDF 내보내기
4. 오답 노트
5. 암기 카드
6. 승소 가능성 예측
7. 개인 사건 법률 조언

---

## 3. 전체 기술 스택

| 레이어 | 기술 / 라이브러리 | 역할 |
| :--- | :--- | :--- |
| AI 분석 엔진 | Google Gemini 2.5 Flash | IRAC 구조화, 근거 기반 요약, 비교 분석 |
| RAG 검색 | Supabase pgvector | 공식 문서 chunk embedding 검색 |
| 관계형 DB | Supabase PostgreSQL | 사용자, 분석 결과, 캐시, 사용량 저장 |
| 인증 / 접근 제어 | Supabase Auth + RLS | 사용자별 데이터 격리 |
| 백엔드 | Python + FastAPI | API 서버, 모듈별 라우터, 비동기 처리 |
| 프론트엔드 | Next.js + Tailwind CSS | 분석 UI, 결과 표시, Mermaid 렌더링 |
| 외부 API | 국가법령정보센터 Open API 등 | 판례 본문, 법령 조문, 최신 판례 조회 |
| PDF 파싱 | pdfplumber / PyPDF2 | 디지털 PDF 텍스트 추출 |
| 이미지 텍스트 추출 | Gemini Vision | 문제집 이미지 텍스트 추출 |
| 환경 설정 | pydantic-settings / python-dotenv | 환경별 설정 관리 |

---

## 4. 모듈식 아키텍처

본 서비스는 기능별 모듈을 독립적으로 구성한다. 각 모듈은 자체 `schemas.py`, `service.py`, `router.py`를 가지며, 외부 시스템은 `infrastructure/` 어댑터를 통해서만 접근한다.

### 4.1 백엔드 디렉토리 구조

```txt
app/
├── main.py
├── core/
│   ├── config.py
│   ├── dependencies.py
│   ├── exceptions.py
│   └── security.py
├── modules/
│   ├── input/
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   ├── retrieval/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   ├── chunking.py
│   │   └── ranker.py
│   ├── irac/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── prompts.py
│   │   └── schemas.py
│   ├── diagram/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── prompts.py
│   │   └── schemas.py
│   ├── verification/
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   ├── comparison/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── prompts.py
│   │   └── schemas.py
│   ├── usage/
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   └── user/
│       ├── router.py
│       ├── service.py
│       └── schemas.py
├── infrastructure/
│   ├── gemini_client.py
│   ├── embedding_client.py
│   ├── lawinfo_client.py
│   ├── supabase_client.py
│   ├── vector_store.py
│   └── cache.py
└── tests/
```

### 4.2 모듈 설계 원칙

1. 모듈 간 직접 참조를 최소화한다.
2. 외부 API 호출은 `infrastructure/` 계층에서만 수행한다.
3. 모든 입출력은 Pydantic schema로 고정한다.
4. Gemini 프롬프트는 각 모듈의 `prompts.py`에만 둔다.
5. RAG 검색 결과는 표준 `EvidenceChunk` schema로 전달한다.
6. 기능 추가 시 `modules/` 아래 새 모듈을 추가하고 `main.py`에 라우터만 등록한다.

### 4.3 프론트엔드 디렉토리 구조

```txt
src/
├── app/
│   ├── (expert)/
│   │   ├── analyze/page.tsx
│   │   ├── verify/page.tsx
│   │   └── compare/page.tsx
│   └── (general)/
│       └── search/page.tsx
├── components/
│   ├── input/
│   ├── irac/
│   ├── diagram/
│   ├── evidence/
│   ├── verification/
│   ├── comparison/
│   └── shared/
├── hooks/
├── lib/
└── types/
```

---

## 5. RAG 설계

### 5.1 RAG 처리 흐름

```txt
사용자 입력
→ 입력 정규화
→ 판례번호/사건명/법령명/조문/키워드 추출
→ 외부 공식 API 검색
→ 문서 정규화
→ chunking
→ embedding 생성
→ pgvector 저장 또는 조회
→ 관련 chunk top-k 검색
→ Gemini grounded prompt 구성
→ JSON 분석 결과 반환
→ 출처/근거 문단 표시
```

### 5.2 검색 대상

| 데이터 | 출처 | 사용 목적 |
| :--- | :--- | :--- |
| 판례 본문 | 국가법령정보센터 판례 API | 원문 대조, IRAC 근거 |
| 판례 목록 | 국가법령정보센터 판례 목록 API | 최신 판례 검색 |
| 법령 조문 | 국가법령정보센터 법령 API | Rule 근거 보강 |
| 판례 변경 정보 | 공식 판례 원문/최신 판례 조회 | 변경 여부 검증 |

### 5.3 EvidenceChunk 표준 스키마

```json
{
  "id": "string",
  "source_type": "case|statute|metadata",
  "source_name": "string",
  "case_number": "string|null",
  "law_article": "string|null",
  "source_url": "string",
  "chunk_text": "string",
  "chunk_index": 0,
  "retrieval_score": 0.0,
  "published_at": "string|null"
}
```

### 5.4 RAG 검색 정책

1. 판례 번호가 있으면 판례 번호 기반 조회를 최우선한다.
2. 판례 번호가 없으면 사건명, 키워드, 법령명 기반 검색을 수행한다.
3. 검색 결과는 공식 출처만 허용한다.
4. 관련도 점수가 기준 미만이면 Gemini 분석으로 넘기지 않는다.
5. top-k 기본값은 5개, 비교 분석은 판례별 5개씩 최대 10개로 제한한다.
6. RAG 근거가 부족하면 분석 결과 대신 근거 부족 상태를 반환한다.

---

## 6. Gemini 중복 호출 방지 및 사용 제한

Gemini 호출은 비용과 응답 일관성에 직접 영향을 주므로 모든 호출 전에 사용량, 캐시, 중복 요청 상태를 확인한다.

### 6.1 호출 제한 원칙

1. 동일 입력, 동일 분석 유형, 동일 RAG 근거 조합이면 Gemini를 재호출하지 않는다.
2. 이미지 OCR 이후 사용자가 텍스트를 확정하기 전에는 분석 Gemini 호출을 금지한다.
3. RAG 검색 결과가 없거나 신뢰도 기준 미달이면 Gemini 분석 호출을 금지한다.
4. 무료 사용자는 월별 횟수를 초과하면 신규 Gemini 호출을 금지한다.
5. 같은 사용자가 같은 요청을 짧은 시간 안에 반복하면 in-flight lock으로 중복 실행을 막는다.
6. 네트워크 재시도는 최대 2회로 제한하고, 재시도에도 실패하면 부분 결과 또는 오류를 반환한다.

### 6.2 캐시 키 설계

```txt
cache_key = sha256(
  normalized_input_text
  + analysis_type
  + persona_mode
  + evidence_chunk_ids
  + prompt_version
  + model_version
)
```

### 6.3 캐시 레이어

| 레이어 | 대상 | 목적 |
| :--- | :--- | :--- |
| Input cache | PDF 추출 결과, 이미지 OCR 결과 | 동일 파일 재처리 방지 |
| Retrieval cache | 외부 API 검색 결과 | 공식 API 중복 호출 방지 |
| Embedding cache | chunk embedding | 같은 문서 재임베딩 방지 |
| Analysis cache | IRAC/비교/도식화 결과 | Gemini 중복 호출 방지 |
| In-flight lock | 진행 중 요청 | 동시 중복 요청 방지 |

### 6.4 사용량 제한

| 항목 | 정책 |
| :--- | :--- |
| 무료 사용자 | 월 5~10회 분석 |
| 미로그인 사용자 | 일 단위 IP 기반 제한 |
| 구독 사용자 | 서비스 안정성을 위한 soft limit 적용 |
| 이미지 OCR | 별도 카운트 또는 높은 비용 가중치 |
| 비교 분석 | 구독 전용, 분석 2회분으로 계산 가능 |

---

## 7. 환각 방지 정책

### 7.1 분석 전 방지

1. 공식 API에서 검색된 근거 chunk가 없으면 분석하지 않는다.
2. 근거 chunk마다 출처 URL과 판례번호 또는 법령 조문을 필수로 가진다.
3. 입력 텍스트와 검색 문서의 관련도 점수가 낮으면 사용자에게 재입력을 요청한다.
4. 판례 번호가 있는 경우 공식 원문과 입력 텍스트의 불일치를 먼저 표시한다.

### 7.2 프롬프트 방지

1. 시스템 프롬프트에 외부 지식 사용 금지를 명시한다.
2. 검색된 근거 밖의 내용은 null 또는 "확인할 수 없습니다"로 반환하게 한다.
3. 결론, 조언, 예측 표현을 금지한다.
4. 모든 주장에 `evidence_ids`를 연결하도록 강제한다.

### 7.3 응답 후 검증

1. Gemini 응답이 JSON schema를 만족하지 않으면 재파싱 또는 실패 처리한다.
2. 응답의 각 문장에 근거 ID가 없는 경우 해당 문장을 제거하거나 `unsupported`로 표시한다.
3. 출처 없는 법령명, 판례번호, 날짜가 생성되면 결과를 사용자에게 노출하지 않는다.
4. 법률 조언처럼 보이는 표현은 후처리 필터에서 차단한다.
5. 일반인 모드는 사용자의 상황에 대한 AI 의견을 제시하지 않고, 공식 API에 명시된 유사 판례와 대법원 판단 내용만 제시한다.

### 7.4 금지 표현

다음 표현은 결과에 포함하지 않는다.

1. "이 사건에서는 승소할 수 있습니다"
2. "따라서 이렇게 대응해야 합니다"
3. "법적으로 문제없습니다"
4. "반드시 인정됩니다"
5. "소송을 제기하세요"

허용 표현은 다음과 같다.

1. "제공된 판례에서 법원은 다음과 같이 판단했습니다"
2. "검색된 공식 근거 안에서는 확인되지 않습니다"
3. "유사한 구조로 볼 수 있는 요소는 다음과 같습니다"
4. "학습 관점에서 쟁점은 다음과 같이 정리할 수 있습니다"

---

## 8. AI 페르소나

AI는 기능별로 일관된 페르소나를 가진다. 페르소나는 `prompts.py`에서 버전 관리하며, 모듈별로 재사용 가능한 prompt block으로 분리한다.

### 8.1 공통 페르소나

```txt
당신은 대한민국 판례와 법령을 학습용으로 구조화하는 법학 튜터입니다.
당신의 역할은 법률 조언이 아니라, 제공된 판례와 공식 근거 문서를 바탕으로 학습자가 이해하기 쉬운 구조를 만드는 것입니다.

반드시 지켜야 할 원칙:
1. 제공된 사용자 입력과 검색된 공식 근거 문서만 사용합니다.
2. 근거 문서에 없는 사실, 판례, 법령, 날짜, 해석은 생성하지 않습니다.
3. 확실하지 않은 내용은 "확인할 수 없습니다"라고 답합니다.
4. 결론을 단정하거나 행동 지침을 제시하지 않습니다.
5. 모든 주요 설명은 근거 문서 ID와 연결합니다.
6. 결과는 요청된 JSON schema에 맞춰 반환합니다.
```

### 8.2 전문가 모드 페르소나

```txt
당신은 로스쿨 준비생과 법학과 학생을 돕는 판례 학습 튜터입니다.
법률 용어는 정확하게 유지하되, 판례의 쟁점, 법리, 적용, 결론을 시험 학습에 적합한 구조로 정리합니다.
수험생이 암기해야 할 법리와 사실관계의 결정적 차이를 구분해서 설명합니다.
단, 검색된 공식 근거 밖의 리딩케이스 판단이나 사견은 제시하지 않습니다.
```

### 8.3 일반인 모드 페르소나

```txt
당신은 일반 사용자의 상황과 유사한 공식 판례를 찾아 설명하는 판례 정보 제공 도우미입니다.
사용자의 상황에 대해 법률 의견, 대응 전략, 승소 가능성, 결론을 제시하지 않습니다.
공식 API 또는 제공된 근거 문서에 명시된 유사 판례의 사실관계와 대법원 판단 내용만 쉬운 문장으로 설명합니다.
근거 문서에 없는 내용은 "확인할 수 없습니다"라고 답합니다.
```

### 8.4 검증 모드 페르소나

```txt
당신은 공식 법률 데이터의 원문 대조를 돕는 검증 보조자입니다.
입력 판례와 공식 출처 판례의 차이를 사실적으로 비교합니다.
변경 여부는 공식 데이터에 근거해서만 표시하며, 법적 의미를 임의로 해석하지 않습니다.
```

---

## 9. 핵심 기능 명세

### 9.1 입력 처리

| 입력 유형 | 처리 방식 | Gemini 호출 |
| :--- | :--- | :--- |
| 텍스트 | 정규화 후 RAG 검색 | 분석 단계에서만 호출 |
| PDF | 텍스트 레이어 우선 추출 | 필요 시 호출 없음 |
| 이미지 | Gemini Vision OCR 후 사용자 확인 | OCR 1회, 확정 전 분석 호출 금지 |
| 판례 번호 | 공식 API 원문 조회 | 분석 단계에서만 호출 |

### 9.2 IRAC 구조화

| 항목 | 내용 |
| :--- | :--- |
| 입력 | 사용자 입력 + EvidenceChunk 목록 |
| 출력 | issue, rule, application, conclusion, key_terms, referenced_laws, evidence_ids |
| 근거 정책 | 각 항목은 최소 1개 이상의 evidence_id 필요 |
| 실패 처리 | 근거 부족 시 분석하지 않고 `insufficient_evidence` 반환 |

### 9.3 전문가용 다이어그램

| 항목 | 내용 |
| :--- | :--- |
| 입력 | 검증된 IRAC JSON 및 evidence id |
| 출력 | 당사자 관계도, 사건 흐름, 법리 판단 분기 Mermaid 코드 |
| 생성 원칙 | 긴 설명 문장 대신 짧은 노드 라벨, 행위, 법적 요건, 판단 결과만 표시 |
| 호출 제한 | IRAC 결과가 캐시에 있으면 다이어그램도 캐시 사용 |
| 렌더링 | 프론트엔드 Mermaid.js에서 렌더링 |
| Claude 사용 | `ANTHROPIC_API_KEY`가 있으면 Claude Haiku 4.5로 Mermaid 코드 생성 가능. 없으면 로컬 규칙 기반 생성 |

### 9.4 판례 변경 검증

| 항목 | 내용 |
| :--- | :--- |
| 입력 | 판례 번호 또는 판례 텍스트 |
| 처리 | 공식 API 원문 조회 후 입력과 대조 |
| 출력 | valid, modified, overruled, unknown |
| Gemini 역할 | diff 요약 보조에만 사용 |
| 우선순위 | 공식 원문 대조가 Gemini 판단보다 우선 |

### 9.5 판례 비교 분석

| 항목 | 내용 |
| :--- | :--- |
| 입력 | 판례 A, 판례 B |
| 처리 | 각 판례별 RAG 검색 후 근거 chunk를 분리 주입 |
| 출력 | 사실관계 비교, 법령 비교, 판단 비교, 결정적 차이, 유사도 |
| 제한 | 구독 전용 |
| 주의 | 결론 예측이 아니라 학습용 차이 설명만 제공 |

---

## 10. 데이터베이스 스키마

| 테이블 | 주요 컬럼 | 용도 |
| :--- | :--- | :--- |
| users | id, email, plan, monthly_count, reset_at | 사용자 및 사용량 |
| documents | id, source_type, source_name, source_url, content_hash | 공식 문서 원본 메타데이터 |
| evidence_chunks | id, document_id, chunk_text, chunk_index, embedding, metadata | RAG 검색 단위 |
| retrieval_logs | id, user_id, query_hash, evidence_ids, created_at | 검색 이력 및 디버깅 |
| analysis_cache | id, cache_key, analysis_type, result_json, created_at | Gemini 결과 캐시 |
| analyses | id, user_id, case_text_hash, irac_json, mermaid_code, evidence_ids | 저장된 분석 |
| verifications | id, user_id, case_number, status, diff_json, source_url | 검증 결과 |
| comparisons | id, user_id, case_a_hash, case_b_hash, result_json | 비교 분석 |
| folders | id, user_id, name, analysis_ids | 구독자 폴더 |

모든 사용자 데이터 테이블에는 Supabase RLS 정책을 적용한다.

---

## 11. API 엔드포인트

| 메서드 | 경로 | 모듈 | 설명 | 인증 |
| :--- | :--- | :--- | :--- | :--- |
| POST | /api/input/text | input | 텍스트 입력 정규화 | 선택 |
| POST | /api/input/image | input | 이미지 OCR | 선택 |
| POST | /api/input/pdf | input | PDF 텍스트 추출 | 선택 |
| POST | /api/retrieval/search | retrieval | 공식 근거 검색 | 선택 |
| POST | /api/irac/analyze | irac | RAG 기반 IRAC 분석 | 선택, 횟수 차감 |
| POST | /api/diagram/generate | diagram | Mermaid 생성 | 선택 |
| POST | /api/verification/check | verification | 판례 변경 검증 | 선택, 횟수 차감 |
| POST | /api/comparison/analyze | comparison | 판례 비교 분석 | 필수, 구독 전용 |
| GET | /api/user/analyses | user | 저장 분석 목록 | 필수 |
| POST | /api/user/analyses | user | 분석 저장 | 필수, 구독 전용 |
| GET | /api/user/folders | user | 폴더 목록 | 필수, 구독 전용 |

---

## 12. 단계별 출시 로드맵

### Phase 1: RAG 기반 MVP, 0~2개월

1. FastAPI / Next.js / Supabase 기본 구조 생성
2. 외부 공식 API 어댑터 구현
3. 문서 정규화, chunking, embedding, pgvector 검색 구현
4. Gemini 호출 캐시 및 in-flight lock 구현
5. RAG 기반 IRAC 분석 구현
6. 전문가용 3종 다이어그램 구현
7. 판례 변경 검증 구현
8. 전문가 모드 UI 구현
9. 출처/근거 표시 UI 구현

목표: 공식 근거 기반 판례 구조화 기능 검증

### Phase 2: 구독 기능 및 고급 분석, 2~4개월

1. 판례 비교 분석
2. 분석 결과 저장
3. 폴더 정리
4. PDF 내보내기
5. 결제/구독 권한 분기
6. 캐시 비용 리포트

목표: 수익 모델 검증

### Phase 3: 일반인 모드 및 검색 확장, 4~8개월

1. 일반인 모드 UI
2. 사용자 상황 기반 유사 판례 매칭
3. 대법원 판단 요지 표시
4. 모바일 최적화
5. 검색 품질 개선

목표: 사용자층 확장

### Phase 4: 학습 플랫폼 고도화, 8개월 이후

1. 암기 카드
2. 오답 노트
3. 반복 학습 큐
4. 학습 진도 관리
5. 판례별 복습 추천

목표: 지속 학습 플랫폼화

---

## 13. 개발 착수 순서

1. 환경 설정
   - Supabase 프로젝트 생성
   - pgvector 활성화
   - Gemini API 키 설정
   - 국가법령정보센터 API 키 설정

2. 백엔드 기반
   - `core/config.py`
   - `infrastructure/lawinfo_client.py`
   - `infrastructure/gemini_client.py`
   - `infrastructure/embedding_client.py`
   - `infrastructure/vector_store.py`
   - `infrastructure/cache.py`

3. RAG 기반
   - `modules/retrieval/schemas.py`
   - `modules/retrieval/chunking.py`
   - `modules/retrieval/ranker.py`
   - `modules/retrieval/service.py`
   - `modules/retrieval/router.py`

4. 분석 기반
   - `modules/irac/prompts.py`
   - `modules/irac/schemas.py`
   - `modules/irac/service.py`
   - `modules/irac/router.py`

5. 검증과 도식화
   - `modules/verification`
   - `modules/diagram`

6. 사용량 제한
   - `modules/usage`
   - 무료/구독 플랜 정책
   - Gemini 호출 제한

7. 프론트엔드
   - 입력 컴포넌트
   - 분석 결과 뷰어
   - 근거 문서 패널
   - Mermaid 렌더러: 당사자 관계도, 사건 흐름, 법리 판단 분기
   - 검증 결과 배지

---

## 14. 성공 기준

| 기준 | 목표 |
| :--- | :--- |
| IRAC JSON schema 성공률 | 95% 이상 |
| 출처 없는 주장 노출률 | 0% |
| 동일 요청 Gemini 재호출률 | 5% 이하 |
| 공식 API 검색 실패 시 graceful failure | 100% |
| MVP 사용자 테스트 | 로스쿨 준비생 기준 핵심 기능 유용성 확인 |

---

## 15. 법적 고지

모든 분석 결과 하단에는 다음 문구를 표시한다.

```txt
본 서비스는 법률 조언이 아닌 학습 및 정보 제공 서비스입니다.
분석 결과는 입력된 판례와 공식 출처로 확인된 자료를 학습용으로 구조화한 것이며,
개별 사건에 대한 법률 판단이나 대응 방안을 제시하지 않습니다.
```
