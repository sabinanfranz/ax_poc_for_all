# AX Agent Factory 스키마
> Last updated: 2025-12-02 (by AX Agent Factory Codex)

## 1. Stage 입출력 요약
| Stage | Input | Output | 구현 상태 |
| --- | --- | --- | --- |
| 0. Job Research | JobRun(company_name, job_title) + optional manual_jd_text | JobResearchResult(raw_job_desc, research_sources) + 디버그용 llm_raw_text/llm_error | 구현 & DB 저장(0.1 Collect → 0.2 Summarize) |
| 1-A. IVC Task Extractor | JobInput(job_meta, raw_job_desc) | TaskExtractionResult(task_atoms[], llm_raw_text/llm_error/llm_cleaned_json) | 구현(Gemini, 키 없으면 스텁) |
| 1-B. IVC Phase Classifier | IVCTaskListInput(job_meta, task_atoms) | PhaseClassificationResult(ivc_tasks[], phase_summary, task_atoms, llm_raw_text/llm_error/llm_cleaned_json) | 구현(Gemini, 키 없으면 스텁) |
| 2+. DNA/Workflow/AX… | 설계만 존재 | - | 미구현 |

## 2. 도메인 모델 (dataclass)

### JobRun (`models/job_run.py`)
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | int \| None | 자동 증가 PK |
| company_name | str | 회사명 |
| job_title | str | 직무명 |
| created_at | datetime | 생성 시각(UTC) |

### JobResearchResult (`models/job_run.py`)
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| job_run_id | int | JobRun FK |
| raw_job_desc | str | 통합 직무 설명 텍스트 |
| research_sources | list[dict] | 각 소스의 url/title/snippet/source_type/score 등 |
| (동적) llm_raw_text | str \| None | UI 디버그용, DB 미저장 |
| (동적) llm_error | str \| None | UI 디버그용, DB 미저장 |
| (동적) llm_cleaned_json | str \| None | UI 디버그용, DB 미저장 |

### JobResearchCollectResult (Stage 0.1, `models/job_run.py`)
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| job_run_id | int | JobRun FK |
| raw_sources | list[dict] | 수집된 원본 소스(url/title/snippet/source_type/score) |
| (동적) llm_raw_text | str \| None | UI 디버그용, DB 미저장 |
| (동적) llm_error | str \| None | UI 디버그용, DB 미저장 |
| (동적) llm_cleaned_json | str \| None | UI 디버그용, DB 미저장 |

### LLMCallLog (`models/llm_log.py`, `infra/db.py::llm_call_logs`)
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | int | PK (AUTOINCREMENT) |
| created_at | str | ISO 시각 |
| job_run_id | int \| None | JobRun FK |
| stage_name | str | 호출 스테이지 (예: stage0_collect, stage0_summarize) |
| agent_name | str \| None | 에이전트/역할 이름 |
| model_name | str | 호출 모델명 |
| prompt_version | str \| None | 프롬프트 버전 태그 |
| temperature | float \| None | 샘플링 설정 |
| top_p | float \| None | 샘플링 설정 |
| input_payload_json | str | LLM 입력 payload json 문자열 |
| output_text_raw | str \| None | LLM 원문 텍스트 |
| output_json_parsed | str \| None | 파싱된 JSON 문자열(성공 시) |
| status | str | success \| json_parse_error \| api_error \| stub_fallback |
| error_type | str \| None | 에러 클래스 |
| error_message | str \| None | 에러 메시지 |
| latency_ms | int \| None | 호출 소요(ms) |
| tokens_prompt | int \| None | 입력 토큰 수(가능한 경우) |
| tokens_completion | int \| None | 출력 토큰 수(가능한 경우) |
| tokens_total | int \| None | 총 토큰 수(가능한 경우) |

## 3. IVC Pydantic 모델 (`core/schemas/common.py`)

### JobMeta
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| company_name | str | 회사명 |
| job_title | str | 직무명 |
| industry_context | str | 산업/맥락 |
| business_goal | str \| None | 비즈니스 목표 |

### JobInput
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| job_meta | JobMeta | 직무 메타 |
| raw_job_desc | str | Stage 0 결과 텍스트 |

### IVCAtomicTask
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| task_id | str | "T01" 형태 |
| task_original_sentence | str | 근거가 된 문장/절 |
| task_korean | str | "[대상] [동사]하기" |
| task_english | str \| None | 영어 표현 |
| notes | str \| None | 메모 |

### TaskExtractionResult
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| job_meta | JobMeta | 입력 그대로 복사 |
| task_atoms | list[IVCAtomicTask] | 추출된 원자 과업 리스트 |
| llm_raw_text | str \| None | LLM 원문(디버그) |
| llm_cleaned_json | str \| None | 정규화된 JSON 문자열(디버그) |
| llm_error | str \| None | 파싱/검증 에러 메시지(스텁 시 기록) |

### IVCTaskListInput
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| job_meta | JobMeta | 입력 그대로 복사 |
| task_atoms | list[IVCAtomicTask] | Task Extractor 출력 |

### IVCTask
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| task_id | str | T## |
| task_korean | str | 원자 과업 문장 |
| task_original_sentence | str | 근거 문장 |
| ivc_phase | str | P1_SENSE \| P2_DECIDE \| P3_EXECUTE_* \| P4_ASSURE |
| ivc_exec_subphase | str \| None | EXECUTE 하위 구분(없으면 None) |
| primitive_lv1 | str | IVC Primitive 1레벨 |
| classification_reason | str | 간단한 근거 |

### PhaseSummary
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| P1_SENSE | dict | {"count": int} |
| P2_DECIDE | dict | {"count": int} |
| P3_EXECUTE_TRANSFORM | dict | {"count": int} |
| P3_EXECUTE_TRANSFER | dict | {"count": int} |
| P3_EXECUTE_COMMIT | dict | {"count": int} |
| P4_ASSURE | dict | {"count": int} |

### PhaseClassificationResult
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| job_meta | JobMeta | 입력 복사 |
| raw_job_desc | str \| None | Stage 0 결과 복사(옵션) |
| ivc_tasks | list[IVCTask] | 분류 결과 |
| phase_summary | PhaseSummary | 집계 |
| task_atoms | list[IVCAtomicTask] \| None | 편의상 첨부(Optional) |
| llm_raw_text | str \| None | LLM 원문(디버그) |
| llm_cleaned_json | str \| None | 정규화된 JSON 문자열(디버그) |
| llm_error | str \| None | 파싱/검증 에러 메시지(스텁 시 기록) |

`IVCPipelineOutput = PhaseClassificationResult`

## 4. LLM 출력 JSON 규칙
- **단일 JSON 객체만** 응답(추가 설명/코드블록 금지).
- 허용 top-level 키  
  - Task Extractor: ["job_meta", "task_atoms"]  
  - Phase Classifier: ["job_meta", "raw_job_desc", "task_atoms", "ivc_tasks", "phase_summary"]
- 문자열에 포함된 줄바꿈/펜스 제거를 위해 `_extract_json_from_text` 사용 후 `_parse_json_candidates`로 정규화. 경미한 문법 오류는 sanitizer가 보정하고, 여전히 실패하면 InvalidLLMJsonError → 스텁으로 대체.

## 5. 예시 페이로드

### Stage 0 출력 예시
```json
{
  "job_run_id": 1,
  "raw_job_desc": "AI 교육 컨설턴트는 고객사 HR과 요구사항을 정리하고, 교육 커리큘럼을 설계하여 제안서를 작성한다...",
  "research_sources": [
    {
      "url": "https://example.com/jd",
      "title": "Example JD",
      "snippet": "Responsibilities: manage client workshops...",
      "source_type": "jd",
      "score": 0.5
    }
  ]
}
```

### Stage 1 출력 예시 (PhaseClassificationResult)
```json
{
  "job_meta": {
    "company_name": "Acme",
    "job_title": "Data Analyst",
    "industry_context": "",
    "business_goal": null
  },
  "task_atoms": [
    {"task_id": "T01", "task_original_sentence": "데이터를 수집한다", "task_korean": "데이터 수집하기", "task_english": "collect data", "notes": null}
  ],
  "ivc_tasks": [
    {"task_id": "T01", "task_korean": "데이터 수집하기", "task_original_sentence": "데이터를 수집한다", "ivc_phase": "P1_SENSE", "ivc_exec_subphase": null, "primitive_lv1": "SENSE", "classification_reason": "정보 수집 활동"}
  ],
  "phase_summary": {
    "P1_SENSE": {"count": 1},
    "P2_DECIDE": {"count": 0},
    "P3_EXECUTE_TRANSFORM": {"count": 0},
    "P3_EXECUTE_TRANSFER": {"count": 0},
    "P3_EXECUTE_COMMIT": {"count": 0},
    "P4_ASSURE": {"count": 0}
  }
}
```
