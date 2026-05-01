# 국가법령정보센터 연동 가이드

본 문서는 국가법령정보센터 연동 방식을 두 영역으로 구분해 정리한다.

1. **한글주소(Friendly URL)**: 사용자에게 공식 근거 링크를 보여주기 위한 URL 생성 규칙
2. **Open API 사용법**: 판례/법령 원문을 서버에서 조회하기 위한 API 호출 규칙

현재 문서에는 Friendly URL 규칙을 먼저 정리한다. Open API 세부 사용법은 별도 자료를 받은 뒤 이 문서의 2부에 추가한다.

---

## 1부. 한글주소(Friendly URL) 사용법

### 1.1 목적

한글주소는 API가 아니라, 사용자가 국가법령정보센터의 공식 문서 페이지로 이동할 수 있게 하는 링크 생성 규칙이다.

StackSync AI 또는 판례 AI 학습 서비스에서는 다음 용도로 사용한다.

- 분석 결과의 공식 근거 링크 표시
- 판례 원문 보기 링크 제공
- 참고 법령 조문 링크 제공
- 법률 용어 해설 링크 제공
- 법령 체계도 또는 3단 비교 화면 연결

AI는 이 링크를 근거로 새로운 법률 판단을 생성하면 안 된다. 링크는 사용자가 공식 원문을 직접 확인할 수 있도록 돕는 보조 수단이다.

### 1.2 Base URL

모든 한글주소는 아래 URL로 시작한다.

```txt
https://www.law.go.kr
```

---

## 1.3 판례 링크

판례 분석 결과에서 공식 판례 원문을 보여줄 때 사용한다. 판례 일련번호를 몰라도 사건번호 또는 판례명 기반으로 연결할 수 있다.

| 유형 | URL 구성 규칙 | 예시 |
| :--- | :--- | :--- |
| 사건번호 + 판결일자 | `/판례/(사건번호,판결일자)` | `https://www.law.go.kr/판례/(2013다214529,20150129)` |
| 사건번호만 | `/판례/(사건번호)` | `https://www.law.go.kr/판례/(2012다13507)` |
| 판례명 | `/판례/판례명` | `https://www.law.go.kr/판례/구상금` |

### 구현 예시

```ts
const baseUrl = "https://www.law.go.kr";
const caseNumber = "2023다12345";
const targetUrl = `${baseUrl}${encodeURI(`/판례/(${caseNumber})`)}`;
```

### 서비스 적용 위치

- 전문가 모드 IRAC 결과의 근거 판례 링크
- 판례 검증 결과의 원문 보기 링크
- 일반인 모드 유사 판례 후보의 공식 출처 링크

---

## 1.4 법령 링크

특정 법령 또는 조문을 사용자에게 보여줄 때 사용한다.

| 유형 | URL 구성 규칙 | 예시 |
| :--- | :--- | :--- |
| 법령명 또는 약칭 | `/법령/법령명` | `https://www.law.go.kr/법령/자동차관리법` |
| 특정 조항 | `/법령/법령명/제X조` | `https://www.law.go.kr/법령/민법/제10조` |
| 3단 비교 | `/법령/법령명/삼단비교` | `https://www.law.go.kr/법령/상법/삼단비교` |
| 연혁 공포번호 | `/법령/법령명/(공포번호)` | `https://www.law.go.kr/법령/건축법/(17235)` |

### 구현 예시

```ts
const baseUrl = "https://www.law.go.kr";
const lawName = "민법";
const article = "제750조";
const targetUrl = `${baseUrl}${encodeURI(`/법령/${lawName}/${article}`)}`;
```

### 서비스 적용 위치

- IRAC `Rule` 항목의 참고 조문 링크
- 일반인 모드의 쉬운 용어 설명 보조 링크
- 판례 비교 분석의 적용 법령 비교 링크

---

## 1.5 법령 용어 링크

사용자가 모르는 법률 용어를 클릭했을 때 국가법령정보센터의 용어 정의 페이지로 연결한다.

| 유형 | URL 구성 규칙 | 예시 |
| :--- | :--- | :--- |
| 용어 정의 | `/용어/용어명` | `https://www.law.go.kr/용어/선박` |

### 구현 예시

```ts
const baseUrl = "https://www.law.go.kr";
const term = "선박";
const targetUrl = `${baseUrl}${encodeURI(`/용어/${term}`)}`;
```

---

## 1.6 기타 공식 링크

| 유형 | URL 구성 규칙 | 예시 |
| :--- | :--- | :--- |
| 헌재결정례 | `/헌재결정례/(사건번호)` | `https://www.law.go.kr/헌재결정례/(2020헌마123)` |
| 법령해석례 | `/법령해석례/(사건번호)` | `https://www.law.go.kr/법령해석례/(사건번호)` |
| 법령체계도 | `/법령체계도/법령/법령명` | `https://www.law.go.kr/법령체계도/법령/민법` |

---

## 1.7 URL 인코딩 규칙

한글 경로가 포함되므로 코드에서 URL을 생성할 때 반드시 인코딩한다.

### JavaScript / TypeScript

```ts
function buildLawGoKrUrl(path: string): string {
  return `https://www.law.go.kr${encodeURI(path)}`;
}

const caseUrl = buildLawGoKrUrl("/판례/(2023다12345)");
const articleUrl = buildLawGoKrUrl("/법령/민법/제750조");
```

### Python

```python
from urllib.parse import quote


def build_law_go_kr_url(path: str) -> str:
    return "https://www.law.go.kr" + quote(path, safe="/(),")


case_url = build_law_go_kr_url("/판례/(2023다12345)")
article_url = build_law_go_kr_url("/법령/민법/제750조")
```

---

## 1.8 유효성 검사

Friendly URL은 사용자가 공식 페이지로 이동하는 링크이므로, 가능하면 링크 생성 후 유효성을 검사한다.

### 검사 방식

1. 서버에서 `HEAD` 또는 `GET` 요청으로 상태 코드 확인
2. 404 또는 오류 페이지가 감지되면 링크를 숨기거나 `공식 링크 확인 필요`로 표시
3. RAG 근거로 사용하지 않고, 사용자 확인용 링크로만 사용

### 주의 사항

- Friendly URL이 열리는 것과 API 원문 조회 성공은 별개의 문제다.
- AI 분석의 grounding은 Open API 응답 또는 저장된 공식 문서 chunk를 기준으로 해야 한다.
- Friendly URL은 결과 화면의 출처 링크로 사용한다.

---

## 1.9 서비스별 적용 가이드

### 전문가 모드

전문가 모드는 판례 구조화 결과에 공식 링크를 붙인다.

예시:

```md
해당 분석은 [대법원 2023다12345 판결](https://www.law.go.kr/판례/(2023다12345))에 기반합니다.
참고 조문: [민법 제750조](https://www.law.go.kr/법령/민법/제750조)
```

### 일반인 모드

일반인 모드는 사용자의 상황과 유사한 판례를 제시할 때 공식 링크를 붙인다.

예시:

```md
비슷한 상황의 판례로 대법원 2023다12345 판결이 있습니다.
대법원은 해당 판례에서 공식 원문에 기재된 사실관계와 판단을 기준으로 다음과 같이 보았습니다.
[원문 보기](https://www.law.go.kr/판례/(2023다12345))
```

일반인 모드에서도 AI는 다음을 금지한다.

- 개인 사건에 대한 결론 제시
- 승소 가능성 예측
- 대응 전략 제안
- 법률 조언

---

# 2부. Open API 사용법

이 섹션은 서버에서 공식 판례/법령 데이터를 조회해 RAG 근거 문서로 사용하기 위한 API 호출 규칙을 정리한다.

Friendly URL은 사용자에게 보여주는 링크이고, Open API는 서버에서 공식 데이터를 수집하는 용도다. AI 분석의 grounding은 Friendly URL이 아니라 Open API 응답으로 생성한 `EvidenceChunk`를 기준으로 한다.

---

## 2.1 공통 규칙

### Base URL

```txt
http://www.law.go.kr/DRF
```

운영 환경에서는 가능하면 HTTPS 사용 가능 여부를 확인한다. 공식 가이드의 예시는 HTTP 기준이다.

### 공통 파라미터

| 파라미터 | 필수 | 설명 |
| :--- | :--- | :--- |
| `OC` | 필수 | 국가법령정보센터 Open API 인증값 |
| `target` | 필수 | 조회 대상 |
| `type` | API별 상이 | `HTML`, `XML`, `JSON` 등 출력 형태 |

### 환경 변수

```txt
LAWINFO_API_KEY=발급받은_OC_값
LAWINFO_BASE_URL=https://www.law.go.kr/DRF
```

### 보안 원칙

1. `OC` 인증값은 서버 환경 변수에만 저장한다.
2. 브라우저 클라이언트에 `OC` 값을 노출하지 않는다.
3. 사용자에게 보여주는 `source_url`에는 `OC` 값을 포함하지 않는다.
4. API 응답 원문은 서버에서 정규화한 뒤 `EvidenceChunk`로 변환한다.

---

## 2.2 판례 목록 조회 API

사용자 입력 상황이나 판례번호/키워드로 관련 판례 후보를 찾을 때 사용한다.

### 공식 가이드

- [판례 목록 조회 API](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=precListGuide)
- [모바일 판례 목록 조회 API](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=mobPrecListGuide)

### 요청 URL

```txt
http://www.law.go.kr/DRF/lawSearch.do?target=prec
```

모바일 여부를 붙이는 경우:

```txt
http://www.law.go.kr/DRF/lawSearch.do?target=prec&mobileYn=Y
```

### 주요 파라미터

| 파라미터 | 값 | 설명 |
| :--- | :--- | :--- |
| `OC` | string | API 인증값 |
| `target` | `prec` | 판례 검색 |
| `type` | `HTML`, `XML`, `JSON` | 출력 형태 |
| `search` | `1`, `2` | 검색 범위. 기본 `1`은 판례명, `2`는 본문검색 |
| `query` | string | 검색어 |
| `display` | int | 결과 개수. 기본 20, 최대 100 |
| `page` | int | 페이지 번호. 기본 1 |
| `org` | string | 법원 종류. 대법원 `400201`, 하위법원 `400202` |

### 추천 사용 방식

#### 일반인 모드

사용자의 상황에서 키워드를 추출한 뒤 본문검색을 우선 사용한다.

```txt
GET /DRF/lawSearch.do
  ?OC={LAWINFO_API_KEY}
  &target=prec
  &type=JSON
  &search=2
  &query={상황_키워드}
  &display=10
  &page=1
  &org=400201
```

#### 전문가 모드

판례번호가 있다면 `query`에 판례번호를 넣고, 검색 결과에서 사건번호가 일치하는 후보를 우선 선택한다.

```txt
GET /DRF/lawSearch.do
  ?OC={LAWINFO_API_KEY}
  &target=prec
  &type=JSON
  &search=2
  &query=2020다12345
  &display=5
  &page=1
```

### RAG 변환

판례 목록 API 결과는 본문 전체가 아니라 후보 탐색용으로 사용한다.

1. 검색 결과에서 판례 일련번호 `ID` 또는 상세 링크를 확보한다.
2. 판례 본문 조회 API로 원문을 다시 가져온다.
3. 원문을 chunking한 뒤 `EvidenceChunk`로 저장한다.

---

## 2.3 판례 본문 조회 API

판례 일련번호로 공식 판례 본문을 조회할 때 사용한다.

### 공식 가이드

- [모바일 판례 본문 조회 API](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=mobPrecInfoGuide)

### 요청 URL

```txt
http://www.law.go.kr/DRF/lawService.do?target=prec&mobileYn=Y
```

### 주요 파라미터

| 파라미터 | 값 | 설명 |
| :--- | :--- | :--- |
| `OC` | string | API 인증값 |
| `target` | `prec` | 판례 본문 조회 |
| `ID` | string | 판례 일련번호 |
| `LM` | string | 판례명 |
| `type` | `HTML` | 출력 형태 |
| `mobileYn` | `Y` | 모바일 여부 |

### 샘플

```txt
http://www.law.go.kr/DRF/lawService.do?OC=test&target=prec&ID=228547&type=HTML&mobileYn=Y
```

### 추천 사용 방식

```txt
GET /DRF/lawService.do
  ?OC={LAWINFO_API_KEY}
  &target=prec
  &ID={판례일련번호}
  &type=HTML
  &mobileYn=Y
```

### 정규화 규칙

1. HTML 응답에서 script/style/tag를 제거한다.
2. 공백을 정규화한다.
3. 사건명, 사건번호, 선고일자, 법원명, 판단 요지, 본문을 가능한 범위에서 분리한다.
4. 원문 전체는 chunking 대상이 된다.
5. 사용자에게 보여줄 링크는 Friendly URL 또는 `source_url`을 별도로 생성한다.

### `EvidenceChunk` 변환 예시

```json
{
  "source_type": "case",
  "source_name": "대법원 2020다12345 판결",
  "case_number": "2020다12345",
  "law_article": null,
  "source_url": "https://www.law.go.kr/판례/(2020다12345)",
  "chunk_text": "판례 본문 일부",
  "chunk_index": 0,
  "retrieval_score": 1.0
}
```

---

## 2.4 법령 조문 조회 API

IRAC의 `Rule` 항목, 참고 조문 링크, 판례 비교 분석에서 법령 조문 원문을 확인할 때 사용한다.

### 공식 가이드

- [현행법령 조항호목 조회 API](https://open.law.go.kr/LSO/openApi/guideResult.do?htmlName=lsNwJoListGuide)

### 요청 URL

```txt
http://www.law.go.kr/DRF/lawService.do?target=lawjosub
```

### 주요 파라미터

| 파라미터 | 값 | 설명 |
| :--- | :--- | :--- |
| `OC` | string | API 인증값 |
| `target` | `lawjosub` | 법령 조항호목 조회 |
| `type` | `HTML`, `XML`, `JSON` | 출력 형태 |
| `ID` | string | 법령 ID. `ID` 또는 `MST` 중 하나 필요 |
| `MST` | string | 법령 마스터 번호. 법령테이블의 `lsi_seq` |
| `JO` | string | 조 번호 6자리 숫자 |
| `HANG` | string | 항 번호 6자리 숫자 |

### 조 번호 변환 규칙

| 조문 | `JO` 값 |
| :--- | :--- |
| 제2조 | `000200` |
| 제10조 | `001000` |
| 제10조의2 | `001002` |

### 구현 예시

```ts
function toJoCode(article: string): string {
  const numbers = article.match(/\d+/g);
  if (!numbers) throw new Error("조문 번호를 찾을 수 없습니다.");
  const main = String(Number(numbers[0])).padStart(4, "0");
  const branch = String(Number(numbers[1] ?? "0")).padStart(2, "0");
  return `${main}${branch}`;
}

toJoCode("제10조의2"); // "001002"
```

### 추천 사용 방식

법령 ID 또는 MST를 알고 있을 때:

```txt
GET /DRF/lawService.do
  ?OC={LAWINFO_API_KEY}
  &target=lawjosub
  &type=JSON
  &ID={법령ID}
  &JO=001002
```

법령명만 있을 때는 먼저 법령 검색 API로 `ID` 또는 `MST`를 찾은 뒤 조문 조회를 수행한다.

---

## 2.5 법령 검색 API

법령명으로 법령 ID 또는 MST를 찾을 때 사용한다. 조문 조회 전에 선행 호출로 사용한다.

### 공식 API 목록

- [Open API 활용가이드 목록](https://open.law.go.kr/LSO/openApi/guideList.do)

### 요청 URL

```txt
http://www.law.go.kr/DRF/lawSearch.do?target=law
```

### 주요 파라미터

| 파라미터 | 값 | 설명 |
| :--- | :--- | :--- |
| `OC` | string | API 인증값 |
| `target` | `law` | 법령 검색 |
| `type` | `HTML`, `XML`, `JSON` | 출력 형태 |
| `search` | int | 검색 범위 |
| `query` | string | 법령명 검색어 |
| `display` | int | 결과 개수 |
| `page` | int | 페이지 번호 |

### 추천 사용 방식

```txt
GET /DRF/lawSearch.do
  ?OC={LAWINFO_API_KEY}
  &target=law
  &type=JSON
  &query=민법
  &display=5
  &page=1
```

검색 결과에서 `법령ID`, `법령일련번호`, `MST`, `lsi_seq` 등 사용 가능한 식별자를 추출한다.

---

## 2.6 서비스 내 호출 흐름

### 전문가 모드

```txt
사용자 판례 입력
→ 판례번호/법령명/조문 추출
→ 판례 목록 검색 API
→ 판례 본문 조회 API
→ 법령 검색 API
→ 법령 조문 조회 API
→ EvidenceChunk 생성
→ Gemini grounded prompt
→ IRAC 결과 + 출처 링크
```

### 일반인 모드

```txt
사용자 상황 입력
→ 상황 키워드 추출
→ 판례 목록 검색 API(search=2 본문검색)
→ 대법원 판례 후보 우선 필터(org=400201)
→ 판례 본문 조회 API
→ 유사한 사실관계와 대법원 판단만 표시
→ AI 의견/대응 전략/승소 가능성 출력 금지
```

### 판례 검증

```txt
판례번호 입력
→ 판례 목록 검색 API
→ 사건번호 일치 후보 선택
→ 판례 본문 조회 API
→ 사용자 입력 원문과 공식 원문 비교
→ valid / modified / unknown 반환
```

---

## 2.7 캐시 정책

### Retrieval Cache

같은 검색 요청은 외부 API를 반복 호출하지 않는다.

```txt
cache_key = sha256("lawinfo" + endpoint + sorted_query_params_without_OC)
```

### Document Cache

판례 본문 또는 법령 조문 본문은 content hash로 중복 저장을 방지한다.

```txt
content_hash = sha256(source_type + source_url + normalized_text)
```

### Analysis Cache

AI 분석 결과는 다음 조합으로 캐시한다.

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

---

## 2.8 오류 처리 정책

| 상황 | 처리 |
| :--- | :--- |
| API 키 없음 | 서버에서 `lawinfo_error` 반환 |
| 검색 결과 없음 | `insufficient_evidence` 또는 `unknown` |
| 판례 본문 조회 실패 | 후보에서 제외하거나 사용자에게 공식 원문 확인 필요 표시 |
| 법령 조문 조회 실패 | 해당 조문 링크만 표시하고 AI 근거로는 사용하지 않음 |
| API 응답 파싱 실패 | 원문 저장 금지, graceful failure |
| Friendly URL은 열리지만 API 조회 실패 | Friendly URL은 출처 링크로만 사용, RAG 근거로 사용하지 않음 |

---

## 2.9 현재 코드 반영 상태

현재 `backend/app/infrastructure/lawinfo_client.py`는 다음 흐름을 기준으로 작성되어 있다.

- `search_cases(query)`: `lawSearch.do?target=prec&type=JSON`
- `get_case_by_id(case_id)`: `lawService.do?target=prec&type=HTML&mobileYn=Y`
- `get_case_by_number(case_number)`: 판례 목록 검색 후 일치 후보의 본문 조회
- `get_statute_article(law_name, article)`: 법령 검색 후 `lawjosub` 조문 조회
- `_normalize_article_number("제10조의2")`: `001002`

추후 실제 API 응답 필드명이 확인되면 정규화 함수에서 필드명을 보강한다.
