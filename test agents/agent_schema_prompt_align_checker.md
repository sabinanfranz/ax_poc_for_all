# Schema–Prompt Align Checker 에이전트 명세

## 1) Overview
- 목적: `schema.md`·Pydantic 스키마와 Stage별 프롬프트의 출력 정의가 일치하는지 자동 검수하고, 위험/수정안을 리포트한다.
- 사용 시점: PR 전 CI, 프롬프트 수정 직후 수동 실행, 주기적 야간 배치.
- 입력: Stage/Pydantic/스키마 마크다운/프롬프트 텍스트/샘플 출력.
- 출력: Align 상태(OK/WARN/ERROR), 필드 단위 불일치 목록, 샘플 검증 결과, 권고/자동수정 초안, 질문 리스트.

## 2) Input 스키마 (AlignCheckRequest)
- `stage_id` (string, required): 예 `stage1_phase_classifier`.
- `prompt_file` (string, required): 예 `ax_agent_factory/prompts/ivc_phase_classifier.txt`.
- `result_type_name` (string, required): 예 `PhaseClassificationResult`.
- `schema_block_markdown` (string, optional): `docs/schema.md`에서 잘라온 해당 타입 섹션.
- `pydantic_model_source` (string, optional): Pydantic 모델 소스 코드 텍스트.
- `prompt_text` (string, required): 프롬프트 전체 텍스트.
- `sample_outputs` (array<object|string>, optional): 실제/테스트 LLM 응답 JSON 또는 문자열.
- `strictness` (string, optional, default `normal`): `lenient|normal|strict` 비교 민감도.
- `autofix_mode` (string, optional, default `suggest`): `none|suggest|patch_prompt|patch_schema`.
- `notes` (string, optional): 실행자 메모.

예시:
```json
{
  "stage_id": "stage1_phase_classifier",
  "prompt_file": "ax_agent_factory/prompts/ivc_phase_classifier.txt",
  "result_type_name": "PhaseClassificationResult",
  "schema_block_markdown": "...schema.md 발췌...",
  "pydantic_model_source": "class PhaseClassificationResult(BaseModel): ...",
  "prompt_text": "...full prompt...",
  "sample_outputs": [],
  "strictness": "strict",
  "autofix_mode": "suggest"
}
```

## 3) Output 스키마 (AlignCheckResult)
- `stage_id` (string)
- `prompt_file` (string)
- `result_type_name` (string)
- `overall_status` (string): `OK | WARN | ERROR | UNKNOWN`
- `summary` (string): 핵심 불일치/리스크 한 줄.
- `top_level_alignment` (object):
  - `schema_keys` (array<string>)
  - `prompt_keys` (array<string>)
  - `missing_in_prompt` (array<string>)
  - `extra_in_prompt` (array<string>)
  - `maybe_optional` (array<string>)
- `field_mismatches` (array<object>):
  - `path` (string, 예 `ivc_tasks[*].ivc_phase`)
  - `schema_type` (string)
  - `prompt_type` (string)
  - `enum_diff` (object|null): `{ "schema": [...], "prompt": [...] }`
  - `severity` (`low|medium|high`)
  - `notes` (string)
- `sample_output_validation` (array<object>):
  - `sample_id` (string|int)
  - `status` (`pass|fail|not_provided`)
  - `errors` (array<string>)
- `recommendations` (array<string>)
- `autofix_suggestions` (array<object>):
  - `target` (`prompt|schema|both`)
  - `action` (string, 예 `rename field phase -> ivc_phase`)
  - `impact` (`low|medium|high`)
- `open_questions` (array<string>)
- `metadata` (object): 실행 시각, strictness, autofix_mode 등.

예시:
```json
{
  "stage_id": "stage1_phase_classifier",
  "prompt_file": "ax_agent_factory/prompts/ivc_phase_classifier.txt",
  "result_type_name": "PhaseClassificationResult",
  "overall_status": "ERROR",
  "summary": "top-level raw_job_desc 누락, phase/enum 구조 불일치",
  "top_level_alignment": {
    "schema_keys": ["job_meta","raw_job_desc","ivc_tasks","phase_summary","task_atoms"],
    "prompt_keys": ["job_meta","task_atoms","ivc_tasks","phase_summary"],
    "missing_in_prompt": ["raw_job_desc"],
    "extra_in_prompt": [],
    "maybe_optional": ["raw_job_desc"]
  },
  "field_mismatches": [
    {
      "path": "ivc_tasks[*].ivc_phase",
      "schema_type": "enum[P1_SENSE,P2_DECIDE,P3_EXECUTE_TRANSFORM,P3_EXECUTE_TRANSFER,P3_EXECUTE_COMMIT,P4_ASSURE]",
      "prompt_type": "enum[SENSE,DECIDE,EXECUTE,ASSURE]",
      "enum_diff": { "schema": ["P1_SENSE","P2_DECIDE","P3_EXECUTE_TRANSFORM","P3_EXECUTE_TRANSFER","P3_EXECUTE_COMMIT","P4_ASSURE"], "prompt": ["SENSE","DECIDE","EXECUTE","ASSURE"] },
      "severity": "high",
      "notes": "단순화된 enum으로 Pydantic 검증 실패"
    }
  ],
  "sample_output_validation": [
    { "sample_id": 1, "status": "not_provided", "errors": [] }
  ],
  "recommendations": [
    "ivc_tasks.phase -> ivc_phase 필드명 수정 및 EXECUTE 세분화 반영",
    "phase_summary 키를 P1_/P2_/P3_/P4_로 변경"
  ],
  "autofix_suggestions": [
    { "target": "prompt", "action": "출력 예시와 스키마 키를 동기화", "impact": "high" }
  ],
  "open_questions": [
    "phase_summary는 EXECUTE 단일 집계로 단순화할 계획인가?"
  ],
  "metadata": { "strictness": "strict", "autofix_mode": "suggest", "checked_at": "2025-12-04T10:00:00Z" }
}
```

## 4) 내부 동작 흐름 (Internal Workflow)
1. **스키마 추출**
   - `schema_block_markdown`에서 필드/타입/enum/필수 여부 파싱(테이블·코드블록 지원).
   - `pydantic_model_source`가 주어지면 AST 파싱으로 타입/필드 기본값 추출.
   - 두 소스 불일치 시 Pydantic > schema.md 우선, 로그에 차이 기록.
2. **프롬프트 출력 정의 추출**
   - `prompt_text`에서 `Output Format`, `허용 top-level 키`, 코드블록 JSON 예시를 정규식으로 추출.
   - 없을 경우 입력/목표 설명을 기반으로 휴리스틱 추정(경고 플래그).
3. **정합성 비교**
   - Top-level 키 집합 비교 → missing/extra/maybe_optional 도출.
   - 필드별 타입/enum 비교 → severity 스코어링(필수 불일치=high, enum 축소=high, casing/nullable=medium, 단순 extra=low).
   - alias 후보 감지(예: `phase` vs `ivc_phase`, `industry` vs `industry_context`) 후 추천.
4. **샘플 검증**
   - `sample_outputs`가 있으면 JSON 파싱 후 스키마 필수 필드 존재/타입 검사.
   - 실패 시 어떤 필드에서 깨졌는지 errors에 기록.
5. **권고/자동 수정 초안**
   - severity≥medium 항목을 중심으로 prompt 수정안 또는 schema 수정안 생성.
   - `autofix_mode=patch_prompt`면 프롬프트용 JSON 예시 패치 초안 문자열까지 생성.
6. **결과 집계**
   - 어떤 항목이라도 high severity → overall_status=ERROR
   - medium만 존재 → WARN
   - 불일치 없으면 OK, 정보 부족 시 UNKNOWN.

## 5) 에러/엣지케이스 처리
- 스키마와 Pydantic 불일치: 둘 다 기록하고 Pydantic 우선 비교, schema.md 갱신 권고 추가.
- 프롬프트에 출력 스키마 블록 부재: `overall_status=WARN`, `missing_in_prompt`에 전체 키 추가.
- 예시 JSON 부재: `sample_output_validation`에 `not_provided`.
- 프롬프트 키는 맞지만 타입 미기재: 타입을 `unknown`으로 표기, severity `medium`.
- 샘플 JSON 파싱 실패: 실패 원문 일부와 오류 메시지를 errors에 포함.

## 6) CI/자동화 연계
- GitHub Actions/n8n/CLI에서 `align_checker.py --stage stage1_phase_classifier --strictness strict` 형태로 실행.
- `overall_status=ERROR` 시 파이프라인 실패로 머지/배포 차단, WARN은 통과하되 요약 코멘트 남김.
- 산출물(JSON/Markdown)을 아티팩트로 업로드해 리뷰어가 바로 확인하도록 한다.

## 7) 사용자 질문 템플릿
- Source of Truth: 이 Stage에서 최종 진실은 Pydantic인가 schema.md인가 프롬프트인가?
- Optional 정책: `raw_job_desc`/`task_atoms` 등은 이후 Stage에서도 항상 유지해야 하는가?
- Enum 정밀도: IVC Phase를 P1_/P2_/P3_/P4_로 유지할지, SENSE/DECIDE/EXECUTE/ASSURE로 단순화할지?
- Stub 허용치: 경미한 위배(예: phase_summary 값 타입) 시 자동 변환을 허용할까, 실패로 처리할까?
- Execution env: static classifier의 `recommended_execution_env` 범위를 어디까지 표준화할까?
- Workflow granularity: Stage/Stream/Hubs를 최소 몇 단위로 강제할 것인가?
- Legacy 필드: `industry` vs `industry_context` 중 무엇을 canonical로 삼을 것인가?

## 8) 예시 실행 (stage1_phase_classifier)
- 요청 예시: 위 Input 예시 참고.
- 기대 결과(요약): `overall_status=ERROR`, missing `raw_job_desc`, enum 축소(SENSE/DECIDE/EXECUTE/ASSURE), `phase_summary` 구조 불일치, `ivc_tasks.phase` vs `ivc_phase` alias 경고, 샘플 없음 → `sample_output_validation.not_provided`.
