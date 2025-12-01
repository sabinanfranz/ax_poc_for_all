# Gemini API 모델/스펙/비용 정리 (Codex 참고용)

> 기준 시점: 2025-11-30  
> 소스: 공식 Gemini API Docs + Pricing + Embeddings 문서 등  
> **주의:** Google이 모델/가격을 자주 바꾸므로, 실제 과금 설계/배포 전에 반드시 최신 문서를 다시 확인할 것.

---

## 1. 전체 개요

### 1.1 API 패밀리

- **Gemini API (ai.google.dev)**
  - `google-genai` SDK 또는 REST로 호출
  - `gemini-2.5-*`, `gemini-2.0-*`, `gemini-1.5-*`, `gemini-embedding-001` 등 사용 :contentReference[oaicite:0]{index=0}
- **모델 종류 (대분류)**
  - 텍스트/멀티모달 LLM: Flash / Flash-Lite / Pro (1.5 / 2.0 / 2.5) :contentReference[oaicite:1]{index=1}
  - 이미지: Gemini 2.5 Flash Image, Gemini 2.0 Flash Image :contentReference[oaicite:2]{index=2}
  - 오디오/Live: Flash Native Audio, Flash Live, Pro/Flash TTS :contentReference[oaicite:3]{index=3}
  - 임베딩: `gemini-embedding-001` :contentReference[oaicite:4]{index=4}
  - Computer Use: `gemini-2.5-computer-use-preview-10-2025` :contentReference[oaicite:5]{index=5}

---

## 2. 텍스트/멀티모달 LLM 모델 요약

### 2.1 Gemini 2.5 계열 (최신 메인)

공식 Models 페이지 기준 핵심 모델: **2.5 Flash, 2.5 Flash-Lite, 2.5 Pro** :contentReference[oaicite:6]{index=6}

| 모델 코드               | 컨텍스트               | 입출력 타입                                                                             | 특징 / 용도                                                                         |
| ----------------------- | ---------------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `gemini-2.5-flash`      | 1M 토큰 입력, 65k 출력 | 텍스트/이미지/비디오/오디오/PDF 입력, 텍스트 출력 :contentReference[oaicite:7]{index=7} | **하이브리드 reasoning + thinking** 기본 활성화, 에이전트/대량 처리용 메인 워크호스 |
| `gemini-2.5-flash-lite` | 1M 입력, 65k 출력      | 텍스트/이미지/비디오/오디오/PDF 입력, 텍스트 출력 :contentReference[oaicite:8]{index=8} | 가장 빠르고 저렴한 플래시 모델, 분류/요약/라벨링/간단 생성 등 고스루풋 작업         |
| `gemini-2.5-pro`        | 1M 입력, 65k 출력      | 오디오/이미지/비디오/텍스트/PDF 입력, 텍스트 출력 :contentReference[oaicite:9]{index=9} | **고난이도 reasoning/coding/STEM/대형 코드베이스** 분석용, thinking 지원            |

- **Thinking**:
  - 2.5 Flash/Pro는 기본적으로 “thinking” 활성화 상태이며, `ThinkingConfig`로 budget 조절 가능 :contentReference[oaicite:10]{index=10}
- **도구 지원** (2.5 Pro/Flash/Flash-Lite 공통):
  - Code execution, Search grounding, Maps, Function calling, File Search, Structured outputs 등 조합 지원 (모델별 지원 여부는 Models 페이지 capability 표 참고) :contentReference[oaicite:11]{index=11}

### 2.2 Gemini 2.0 계열 (이전 세대, 여전히 사용 가능)

- `gemini-2.0-flash`
  - 1M 토큰 컨텍스트, 멀티모달 입력(오디오/이미지/비디오/텍스트), 텍스트 출력 :contentReference[oaicite:12]{index=12}
  - 속도·품질 균형 좋은 워크호스, Live/Maps/코드 실행/검색 grounding 지원
- `gemini-2.0-flash-lite`
  - 플래시보다 더 가벼운 저비용 모델, 1M 컨텍스트, 텍스트 출력 위주 :contentReference[oaicite:13]{index=13}
- `gemini-2.0-flash-live-001`
  - Live API용, 오디오/비디오/텍스트 입력·오디오/텍스트 출력, 1M 컨텍스트 :contentReference[oaicite:14]{index=14}

> 코딩에서는 **2.5 계열을 기본**, 2.0 계열은 “레거시/비용 최적화” 용도로만 고려.

### 2.3 Gemini 1.5 계열 (이전 세대, 대부분 Previous 섹션)

Models 페이지의 “Previous Gemini models”에 1.5 Pro / 1.5 Flash / Flash-8B 등이 정리되어 있으며,  
현재는 2.0/2.5 대비 구세대라 **새 설계에는 추천하지 않음**. :contentReference[oaicite:15]{index=15}

---

## 3. 이미지/오디오/특수 모델

### 3.1 이미지

- **Gemini 2.5 Flash Image (`gemini-2.5-flash-image`)**

  - 입력: 이미지 + 텍스트, 출력: 이미지 + 텍스트 :contentReference[oaicite:16]{index=16}
  - 이미지 생성에 최적화, 텍스트 토큰 과금 + 이미지당 별도 과금(약 $0.039/이미지, 1024x1024 기준) :contentReference[oaicite:17]{index=17}

- **Gemini 2.0 Flash Image (`gemini-2.0-flash-preview-image-generation`)**
  - 멀티모달 입력(오디오/이미지/비디오/텍스트), 텍스트+이미지 출력, 32k 입력 컨텍스트 :contentReference[oaicite:18]{index=18}

### 3.2 오디오 / Live / TTS

- **Gemini 2.5 Flash Native Audio (`gemini-2.5-flash-native-audio-preview-09-2025`)**
  - Live API용, 오디오/비디오/텍스트 입력 → 오디오/텍스트 출력, 고품질 TTS/대화용 :contentReference[oaicite:19]{index=19}
- **Gemini Live 2.5 Flash (`gemini-live-2.5-flash-preview`)**
  - half-cascade 오디오 모델, Native Audio와 동일한 가격 정책 :contentReference[oaicite:20]{index=20}
- **TTS용**
  - `gemini-2.5-flash-preview-tts`, `gemini-2.5-pro-preview-tts`: 텍스트→오디오 TTS, 스탠다드/배치 가격 별도 :contentReference[oaicite:21]{index=21}

### 3.3 Computer Use (브라우저 조작 등)

- **Gemini 2.5 Computer Use Preview (`gemini-2.5-computer-use-preview-10-2025`)**
  - 브라우저 컨트롤 에이전트 구축용, 프롬프트 길이에 따라 다른 단가 ($1.25~$2.50/1M input, $10~$15/1M output) :contentReference[oaicite:22]{index=22}
  - 에이전트 기반 워크플로우(예: UI 클릭, 폼 작성) 자동화에 적합

---

## 4. 임베딩 모델

### 4.1 `gemini-embedding-001`

- 용도: 텍스트/코드 임베딩 (RAG, 검색, 분류 등) :contentReference[oaicite:23]{index=23}
- 입력 토큰 제한: 2,048 tokens :contentReference[oaicite:24]{index=24}
- 출력 차원: 128 ~ 3072 (추천: 768 / 1536 / 3072) :contentReference[oaicite:25]{index=25}
- 호출 예시 (Python / google-genai):

  ```python
  from google import genai

  client = genai.Client()

  result = client.models.embed_content(
      model="gemini-embedding-001",
      contents=["text1", "text2"]
  )
  vectors = result.embeddings
  ``
  ```

* Batch Embedding 사용 시 토큰당 가격 50% 수준 (Batch API Embedding) ([Google AI for Developers][1])

> Vertex AI 쪽에는 `text-embedding-005`, `text-multilingual-embedding-002` 등 추가 임베딩이 있으나,
> **Gemini API(키 기반)** 관점에선 `gemini-embedding-001`이 메인. ([Google Cloud Documentation][2])

---

## 5. 가격(Developer Gemini API 기준, 2025-11 시점)

> **중요:** 아래 수치는 PRD/설계 참고용 “오더 오브 매그니튜드”다.
> 실제 청구는 지역/환율/업데이트에 따라 달라질 수 있으니,
> 배포 직전에는 반드시 공식 Pricing 페이지를 다시 확인할 것. ([Google AI for Developers][3])

### 5.1 2.5 Flash / Flash-Lite / Pro (텍스트/멀티모달)

공식 Pricing 페이지 + 정리 사이트 기준 요약: ([Google AI for Developers][3])

| 모델                                                | 용도                                        | 대략적 단가 (Paid, /1M tokens)                                        |
| --------------------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------- |
| **Gemini 2.5 Flash-Lite (`gemini-2.5-flash-lite`)** | 고속·저비용 플래시                          | Input ~$0.10, Output ~$0.40                                           |
| **Gemini 2.5 Flash (`gemini-2.5-flash`)**           | 하이브리드 reasoning + thinking, 1M context | Input ~0.30, Output ~2.50(텍스트/이미지/비디오); 오디오 더 비쌈       |
| **Gemini 2.5 Pro (`gemini-2.5-pro`)**               | 고난이도 reasoning/coding                   | Input ~1.25–2.50(프롬프트 길이에 따라), Output ~10–15 (thinking 포함) |

- 위 수치는 외부 정리 문서와 공식 표를 기반으로 한 **대략 값**이다. ([Google AI for Developers][3])
- 실제 표에서는 Free Tier와 Paid Tier를 구분하여,
  Free Tier는 **일정 토큰까지 무료**, 이후 Paid 단가 적용. ([Google AI for Developers][3])

### 5.2 이미지 / 오디오 / 임베딩

- **2.5 Flash Image**

  - 텍스트/이미지 입력: 약 $0.30 / 1M tokens
  - 이미지 출력: 약 $0.039 / 이미지 (1024x1024, 1290 tokens 기준) ([Google AI for Developers][3])

- **2.5 Flash Native Audio**

  - 텍스트 입력: $0.50 / 1M tokens, 오디오 입력: $3.00 / 1M tokens
  - 텍스트 출력: $2.00 / 1M, 오디오 출력: $12.00 / 1M ([Google AI for Developers][3])

- **2.5 Flash/Pro TTS**

  - Flash TTS: 입력 $0.50, 출력 $10.00 / 1M 토큰 수준 ([Google AI for Developers][3])
  - Pro TTS: 입력 $1.00, 출력 $20.00 / 1M 토큰 수준 ([Google AI for Developers][3])

- **임베딩 (`gemini-embedding-001`)**

  - $0.15 / 1M tokens (인터랙티브), Batch Embedding은 이의 50% (약 $0.075) ([Google AI for Developers][1])

### 5.3 도구 툴 가격 (Search/Maps/Code/File 등)

- Google Search / Maps / Code execution / URL context / File search 등은
  **모델 토큰 요금 + 별도 툴 요금** 조합. ([Google AI for Developers][3])
- 예:

  - Search grounding: Flash/Flash-Lite Free Tier 500RPD, 이후 1500RPD free + $35/1,000 요청 등 ([Google AI for Developers][3])

---

## 6. 코드에서 사용할 모델 alias 설계 (프로젝트 로컬 규칙)

Codex가 구현할 `infra/llm_client.py`에서 사용할 **로컬 모델 키**를 아래처럼 정의하는 걸 추천:

```python
# 내부 alias → 실제 Gemini 모델 코드
MODEL_REGISTRY = {
  "analysis_main":     "gemini-2.5-pro",         # 깊은 reasoning/coding
  "fast_general":      "gemini-2.5-flash-lite",  # 저비용/고속 요약, 분류
  "agent_workhorse":   "gemini-2.5-flash",       # 에이전트 플로우 메인
  "image_generate":    "gemini-2.5-flash-image", # 이미지 생성/편집
  "audio_tts_fast":    "gemini-2.5-flash-preview-tts",
  "audio_tts_quality": "gemini-2.5-pro-preview-tts",
  "audio_live":        "gemini-2.5-flash-native-audio-preview-09-2025",
  "embed_main":        "gemini-embedding-001",
  "computer_use":      "gemini-2.5-computer-use-preview-10-2025",
}
```

- **core 모듈(IVC/DNA/Workflow/Skill/Prompt/Runner)**에서는
  가능하면 **`"analysis_main"`, `"fast_general"`, `"embed_main"` 같은 alias만** 쓰고
  실제 모델 코드는 `llm_client`에서만 관리하도록.

---

## 7. Python SDK 사용법 (google-genai 기준)

### 7.1 설치

공식 Quickstart 기준: ([Google AI for Developers][4])

```bash
pip install -U google-genai
```

### 7.2 텍스트/멀티모달 생성 예시

```python
from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="How does AI work?"
)
print(response.text)
```

멀티모달 입력 예시 (이미지 + 텍스트): ([Google AI for Developers][5])

```python
from PIL import Image
from google import genai

client = genai.Client()
image = Image.open("/path/to/image.png")

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[image, "이 이미지에 대해 설명해줘"]
)
print(response.text)
```

Thinking 비활성화 예시: ([Google AI for Developers][5])

```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="How does AI work?",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=0)  # thinking 끄기
    ),
)
print(response.text)
```

### 7.3 임베딩 예시

```python
from google import genai

client = genai.Client()

result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=[
        "What is the meaning of life?",
        "How does photosynthesis work?",
    ],
)
for emb in result.embeddings:
    print(len(emb.values))  # 차원 수
```

### 7.4 REST 호출 패턴 (텍스트 생성)

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent" \
  -H "x-goog-api-key: $GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "How does AI work?"
          }
        ]
      }
    ]
  }'
```

---

## 8. Codex를 위한 구현 메모

Codex/Claude Code에 전달할 **핵심 요약 포인트**:

1. **모델 종류와 alias**는 위 `MODEL_REGISTRY` 표를 기준으로 구현.
2. `infra/llm_client.py`에서만 실제 모델 이름을 알고 있어야 하며,
   core 모듈은 alias만 사용한다.
3. 비용/성능 관점에서:

   - `fast_general`(2.5 Flash-Lite)를 기본값으로 두고,
   - 깊은 reasoning이 필요한 부분만 `analysis_main`(2.5 Pro)로 올리는 전략.

4. 임베딩은 `gemini-embedding-001`만 사용, 차원은 768/1536/3072 중 하나로 고정.
5. 가격/스펙은 **이 문서를 참고하되, 배포 전에 항상**
   [`https://ai.google.dev/gemini-api/docs/models`](https://ai.google.dev/gemini-api/docs/models) 와
   [`https://ai.google.dev/gemini-api/docs/pricing`](https://ai.google.dev/gemini-api/docs/pricing)
   을 다시 확인해야 한다.
