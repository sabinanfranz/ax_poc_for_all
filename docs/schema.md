# AX Agent Factory 스키마
> Last updated: 2025-12-04 (by AX Agent Factory Codex, prompt-aligned)

## 1. Stage 입출력 요약
| Stage | Input | Output | 구현 상태 |
| --- | --- | --- | --- |
| 0. Job Research | JobRun(company_name, job_title) + optional manual_jd_text | JobResearchResult(raw_job_desc, research_sources) + 디버그용 llm_raw_text/llm_error; Collect 캐시: JobResearchCollectResult(job_meta, raw_sources) | 구현 & DB 저장(0.1 Collect → 0.2 Summarize) |
| 1.1 IVC Task Extractor | JobInput(job_meta, raw_job_desc) | TaskExtractionResult(task_atoms[], llm_raw_text/llm_error/llm_cleaned_json) | 구현(Gemini, 키 없으면 스텁) |
| 1.2 IVC Phase Classifier | IVCTaskListInput(job_meta, task_atoms) | PhaseClassificationResult(ivc_tasks[], phase_summary, task_atoms, llm_raw_text/llm_error/llm_cleaned_json) | 구현(Gemini, 키 없으면 스텁) |
| 1.3 Static Task Classifier | PhaseClassificationResult | StaticClassificationResult(task_static_meta[], static_summary, llm_raw_text/llm_error/llm_cleaned_json) | 구현(Gemini, 키 없으면 스텁) |
| 2.1 Workflow Struct | PhaseClassificationResult dict (+ optional task_static_meta, static_summary) | WorkflowPlan(stages, streams, nodes, edges, entry/exit_points, llm_raw_text/llm_error/llm_cleaned_json) | 구현(Gemini, 키 없으면 스텁) |
| 2.2 Workflow Mermaid | WorkflowPlan | MermaidDiagram(mermaid_code, warnings, llm_raw_text/llm_error/llm_cleaned_json) | 구현(Gemini, 키 없으면 스텁) |
| 4. AX Workflow Architect | WorkflowPlan + job_meta (+ task cards 등) | AXWorkflowDesignResult | 설계(미구현) |
| 5. Agent Architect | AXWorkflowDesignResult | AgentSpecsForPromptBuilder | 설계(미구현) |
| 6-A Deep Skill Research | AgentSpecsForPromptBuilder/ax_agents | DeepSkillResearchResult | 설계(미구현) |
| 6-B Skill Extractor | AgentSpecsForPromptBuilder + DeepSkillResearchResult | SkillCardSet | 설계(미구현) |
| 7. Prompt Builder | AgentSpecsForPromptBuilder + SkillCardSet | AgentPromptSet | 설계(미구현) |

## 2. 도메인 모델 (dataclass)

### JobRun (`models/job_run.py`)
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| id | int \| None | 자동 증가 PK |
| company_name | str | 회사명 |
| job_title | str | 직무명 |
| industry_context | str \| None | 산업/맥락 |
| business_goal | str \| None | 비즈니스 목표 |
| manual_jd_text | str \| None | 사용자가 붙여넣은 JD 원문 |
| status | str \| None | 파이프라인 상태 |
| created_at | datetime | 생성 시각(UTC) |
| updated_at | datetime | 갱신 시각(UTC) |

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
| job_meta | dict \| None | company_name/job_title/industry_context/business_goal 복사(optional) |
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
| industry_context | str \| None | 산업/맥락 (프롬프트 optional) |
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

### StaticClassificationResult (`core/schemas/common.py`)
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| job_meta | JobMeta | 입력 복사 |
| task_static_meta | list[TaskStaticMeta] | 정적 유형/도메인/RAG/가치/복잡도/실행환경 태깅 |
| static_summary | dict | 간단 집계 |
| llm_raw_text / llm_cleaned_json / llm_error | str \| None | 디버그 필드 |

## 4. Workflow Pydantic 모델 (`core/schemas/workflow.py`)

### WorkflowStage / WorkflowStream
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| stage_id / stream_id | str | 고유 ID (`S1`, `S1_ST1` 등) |
| name | str | 표시명 |
| description | str \| None | 설명 |
| stage_id (stream 전용) | str \| None | 상위 Stage |

### WorkflowNode
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| node_id | str | 노드 ID |
| label | str | 라벨(과업명) |
| stage_id / stream_id | str \| None | 소속 Stage/Stream |
| is_entry / is_exit / is_hub | bool | 진입/종료/분기·합류 플래그 |
| notes | str \| None | 메모 |

### WorkflowEdge
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| source | str | 출발 노드 ID |
| target | str | 도착 노드 ID |
| label | str \| None | 엣지 라벨 |

### WorkflowPlan
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| workflow_name | str | 워크플로우 명칭 |
| workflow_summary | str \| None | 요약 |
| stages/streams/nodes/edges | list | 구조 요소 리스트 |
| entry_points / exit_points | list[str] | 시작/종료 노드 ID 모음 |
| notes | str \| None | 메모 |
| llm_raw_text / llm_cleaned_json / llm_error | str \| None | 디버그 필드 |

### MermaidDiagram
| 필드 | 타입 | 설명 |
| --- | --- | --- |
| workflow_name | str | 워크플로우 명칭 |
| mermaid_code | str | 노션 호환 Mermaid flowchart TD 코드 |
| warnings | list[str] \| None | 경고 메시지 리스트 |
| llm_raw_text / llm_cleaned_json / llm_error | str \| None | 디버그 필드 |

## 5. LLM 출력 JSON 규칙 (LLM 응답에 llm_* 금지, Runner가 사후 주입)
- **단일 JSON 객체만** 응답(추가 설명/코드블록 금지).
- 허용 top-level 키  
  - Job Research Collect: ["job_meta", "raw_sources"]
  - Job Research Summarize: ["raw_job_desc", "research_sources"]
  - Task Extractor: ["job_meta", "task_atoms"]  
  - Phase Classifier: ["job_meta", "raw_job_desc", "task_atoms", "ivc_tasks", "phase_summary"]
  - Static Task Classifier: ["job_meta", "task_static_meta", "static_summary"]
  - Workflow Struct: ["workflow_name","workflow_summary","stages","streams","nodes","edges","entry_points","exit_points","notes"]
  - Workflow Mermaid: ["workflow_name","mermaid_code","warnings"]
  - AX Workflow Architect: ["workflow_name","workflow_summary","ax_workflow_mermaid_code","agent_table_for_agent_architect","n8n_workflows","sheet_schemas","validator_plan","observability_plan"]
  - Agent Architect: ["stage_context","global_policies","agents"]
  - Deep Skill Research: ["agent_id","research_focus","research_sections"]
  - Skill Extractor: ["skill_cards","agent_skill_map"]
  - Prompt Builder: ["summary","agents"]
- 문자열에 포함된 줄바꿈/펜스 제거를 위해 `_extract_json_from_text` 사용 후 `_parse_json_candidates`로 정규화. 경미한 문법 오류는 sanitizer가 보정하고, 여전히 실패하면 InvalidLLMJsonError → 스텁으로 대체.
- `llm_raw_text` / `llm_cleaned_json` / `llm_error` 필드는 LLM JSON에는 포함하지 않고 Runner/파서에서 결과 객체에 주입.

## 6. 예시 페이로드

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
    "industry_context": null,
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

### Stage 3-A 출력 예시 (WorkflowPlan)
```json
{
  "workflow_name": "Data Analyst Workflow",
  "stages": [{"stage_id": "S1", "name": "Sense/Decide"}],
  "streams": [{"stream_id": "S1_ST1", "name": "Main", "stage_id": "S1"}],
  "nodes": [
    {"node_id": "T1", "label": "데이터 수집하기", "stage_id": "S1", "stream_id": "S1_ST1", "is_entry": true},
    {"node_id": "T2", "label": "분석 결과 보고서 작성하기", "stage_id": "S1", "stream_id": "S1_ST1", "is_exit": true}
  ],
  "edges": [{"source": "T1", "target": "T2"}],
  "entry_points": ["T1"],
  "exit_points": ["T2"]
}
```

### Stage 3-B 출력 예시 (MermaidDiagram)
```json
{
  "workflow_name": "Data Analyst Workflow",
  "mermaid_code": "flowchart TD\\n    T1[\"데이터 수집하기\"] --> T2[\"분석 결과 보고서 작성하기\"]",
  "warnings": []
}
```

## 7. DB 테이블 요약 (job_tasks/job_task_edges)

### job_tasks
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK | 내부 PK |
| job_run_id | INTEGER | JobRun FK |
| task_id | TEXT | "T01" 등 논리 ID (job_run_id와 UNIQUE) |
| task_original_sentence | TEXT | 근거 구절 |
| task_korean | TEXT | "[대상] [동사]하기" |
| task_english | TEXT \| NULL | 영어 표현 |
| notes | TEXT \| NULL | 메모 |
| ivc_phase / ivc_exec_subphase / primitive_lv1 / classification_reason | TEXT \| NULL | Stage 1.2 분류 결과 |
| static_type_lv1 / static_type_lv2 | TEXT \| NULL | Static 유형 |
| domain_lv1 / domain_lv2 | TEXT \| NULL | 도메인 |
| rag_required | INTEGER \| NULL | 0/1 |
| rag_reason | TEXT \| NULL | RAG 필요 이유 |
| value_score / complexity_score | INTEGER \| NULL | 가치/복잡도 점수 |
| value_complexity_quadrant | TEXT \| NULL | 사분면 |
| recommended_execution_env | TEXT \| NULL | 권장 실행 환경 |
| autoability_reason | TEXT \| NULL | 자동화 근거 |
| data_entities_json / tags_json | TEXT \| NULL | JSON 배열 문자열 |
| stage_id / stream_id | TEXT \| NULL | Workflow 구조화 결과 |
| workflow_node_label | TEXT \| NULL | 노드 라벨 |
| is_entry / is_exit / is_hub | INTEGER \| NULL | 0/1 플래그 |
| review_status | TEXT \| NULL | HITL 상태 |
| created_at / updated_at | TEXT | ISO 시각 |

### job_task_edges
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK | 내부 PK |
| job_run_id | INTEGER | JobRun FK |
| source_task_id | TEXT | 출발 task_id |
| target_task_id | TEXT | 도착 task_id |
| label | TEXT \| NULL | 엣지 라벨 |
| created_at / updated_at | TEXT | ISO 시각 |

## 8. AX 확장 스키마 (Stage 4~7, `core/schemas/ax.py` 제안)

### AXWorkflowDesignResult (Stage 4 – AX Workflow Architect)
- top-level 키: `["workflow_name","workflow_summary","ax_workflow_mermaid_code","agent_table_for_agent_architect","n8n_workflows","sheet_schemas","validator_plan","observability_plan"]`
- 필드
  - workflow_name: str
  - workflow_summary: str \| None
  - ax_workflow_mermaid_code: str (n8n + Agents + Sheets + Validators mermaid)
  - agent_table_for_agent_architect: AgentTableForAgentArchitect
  - n8n_workflows: list[AXN8nWorkflow]
  - sheet_schemas: list[AXSheetSchema]
  - validator_plan: list[AXValidatorPlanItem]
  - observability_plan: list[AXMetricPlanItem]
  - llm_raw_text / llm_cleaned_json / llm_error: str \| None (LLM 응답에는 미포함)

#### AgentTableForAgentArchitect 서브 모델
- AgentTableStageOverview: stage_id, stage_name, stage_goal
- AgentTableAgentRow:
  - agent_id, agent_name, stage_stream_step
  - agent_type: structuring|generator|validator|rag|orchestrator|utility
  - execution_environment: n8n_gpt_node|http_gpt_api|pure_n8n_logic|human_only
  - n8n_workflow_id, n8n_node_name, primary_sheet: str \| None
  - rag_enabled: bool
  - file_search_corpus_hint: str \| None
  - role_and_goal: str
  - tasks_covered: list[str]
  - risks: list[str]
  - success_metrics: list[str]
- AgentTableForAgentArchitect: job_title, stage_overview[list], agents[list]

#### AXN8nWorkflow & Sheet/Validator/Metric
- AXN8nWorkflowNode: node_id, node_type(trigger|sheets_read|sheets_write|llm|http|function|slack|other), label
- AXN8nWorkflow: workflow_id, name, description, stage_id, nodes[list]
- AXSheetColumn: name, type(string|number|boolean|date|json|unknown), required: bool, description
- AXSheetSchema: sheet_name, description, columns[list]
- AXValidatorPlanItem: target(agent_output|sheet_row|workflow), target_id, validation_type(human_review|validator_agent), criteria[list[str]]
- AXMetricPlanItem: metric_name, metric_type(counter|gauge|histogram), description, source(workflow|agent|sheet), aggregation(per_run|daily|weekly)

### AgentSpecsForPromptBuilder (Stage 5 – Agent Architect)
- top-level 키: `["stage_context","global_policies","agents"]`
- 필드
  - stage_context: StageContextForPrompt (stage_overview[list AgentTableStageOverview], business_goal: str\|None, primary_kpis: list[str], pain_points: list[str])
  - global_policies: list[str]
  - agents: list[PromptAgentSpec]
  - llm_raw_text / llm_cleaned_json / llm_error: str \| None
- PromptAgentSpec: agent_id, agent_name, stage_stream_step, agent_type, execution_environment, n8n_workflow_id, n8n_node_name, primary_sheet: str\|None, rag_enabled: bool, file_search_corpus_hint: str\|None, domain_context: str, role_and_goal: str, input_schema/output_schema: list[AgentIOField], success_metrics: list[AgentSuccessMetric], error_policy: str, validation_policy: str, notes: str\|None
- AgentIOField: name, type(string|number|boolean|date|json|unknown), required: bool, description: str, example: str\|None
- AgentSuccessMetric: name, description
- StageContextForPrompt: stage_overview[list AgentTableStageOverview], business_goal: str\|None, primary_kpis: list[str], pain_points: list[str]

### DeepSkillResearchResult (Stage 6-A)
- top-level 키: `["agent_id","research_focus","research_sections"]`
- 필드: agent_id, research_focus("skill"|"info+skill"), research_sections(DeepSkillResearchSections: core_skills, thinking_process, frameworks_and_questions, common_pitfalls, good_vs_bad_examples), llm_raw_text/llm_cleaned_json/llm_error

### SkillCardSet (Stage 6-B)
- top-level 키: `["skill_cards","agent_skill_map"]`
- SkillCard: skill_id("S01"...), skill_name, target_agent_ids[list[str]], related_task_ids[list[str]], purpose, when_to_use, core_heuristics[list[str]], step_checklist[list[str]], bad_signs[list[str]], good_signs[list[str]]
- AgentSkillMapItem: agent_id, skill_ids[list[str]]
- llm_raw_text/llm_cleaned_json/llm_error optional(LLM 응답 미포함)

### AgentPromptSet (Stage 7 – Prompt Builder)
- top-level 키: `["summary","agents"]`
- AgentPromptBundle: agent_id, execution_environment, single_prompt/system_prompt/user_prompt_template/logic_hint/human_checklist (env별 선택), examples[list[PromptExample]]
- PromptExample: example_id, input_example, output_example, notes: str\|None
- llm_raw_text/llm_cleaned_json/llm_error optional(LLM 응답 미포함)

## 9. AX DB 테이블 요약 (제안)

### ax_workflows
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK | 내부 PK |
| job_run_id | INTEGER | JobRun FK |
| workflow_name | TEXT | AX 워크플로우 이름 |
| workflow_summary | TEXT \| NULL | 요약 |
| ax_workflow_mermaid_code | TEXT | n8n+Agents+Sheets+Validators mermaid |
| agent_table_json | TEXT | AgentTableForAgentArchitect JSON |
| n8n_workflows_json | TEXT | AXWorkflowDesignResult.n8n_workflows JSON |
| sheet_schemas_json | TEXT | AXWorkflowDesignResult.sheet_schemas JSON |
| validator_plan_json | TEXT | AXWorkflowDesignResult.validator_plan JSON |
| observability_plan_json | TEXT | AXWorkflowDesignResult.observability_plan JSON |
| created_at / updated_at | TEXT | ISO 시각 |

### ax_agents
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK | 내부 PK |
| job_run_id | INTEGER | JobRun FK |
| agent_id | TEXT | 논리 ID (job_run 내 UNIQUE) |
| agent_name | TEXT | 에이전트 이름 |
| stage_stream_step | TEXT | 예: "S1/Structuring" |
| agent_type | TEXT | structuring/generator/validator/rag/orchestrator/utility |
| execution_environment | TEXT | n8n_gpt_node/http_gpt_api/pure_n8n_logic/human_only |
| n8n_workflow_id | TEXT | n8n 워크플로우 ID |
| n8n_node_name | TEXT | n8n 노드명 |
| primary_sheet | TEXT \| NULL | 주요 시트 |
| rag_enabled | INTEGER \| NULL | 0/1 |
| file_search_corpus_hint | TEXT \| NULL | RAG 대상 힌트 |
| domain_context | TEXT | 도메인/업무 맥락 |
| role_and_goal | TEXT | 역할/목표 |
| success_metrics_json | TEXT \| NULL | AgentSuccessMetric 리스트 |
| error_policy | TEXT \| NULL | 에러 처리 정책 |
| validation_policy | TEXT \| NULL | 검증 정책 |
| notes | TEXT \| NULL | 메모 |
| agent_spec_json | TEXT | AgentSpecsForPromptBuilder.agents[*] 원본 |
| created_at / updated_at | TEXT | ISO 시각 |

### ax_agent_task_links
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK | 내부 PK |
| job_run_id | INTEGER | JobRun FK |
| agent_id | TEXT | ax_agents.agent_id |
| task_id | TEXT | job_tasks.task_id |
| link_type | TEXT | primary/secondary/validator/observer 등 |
| notes | TEXT \| NULL | 메모 |
| created_at / updated_at | TEXT | ISO 시각 |

### ax_deep_research_results
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK | 내부 PK |
| job_run_id | INTEGER | JobRun FK |
| agent_id | TEXT | 대상 agent_id |
| research_focus | TEXT | "skill" \| "info+skill" |
| research_sections_json | TEXT | DeepSkillResearchSections JSON |
| created_at / updated_at | TEXT | ISO 시각 |

### ax_skill_cards
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK | 내부 PK |
| job_run_id | INTEGER | JobRun FK |
| skill_public_id | TEXT | "S01" 등 (job_run 내 unique) |
| skill_name | TEXT | 스킬 이름 |
| target_agent_ids_json | TEXT | ["agent1", ...] |
| related_task_ids_json | TEXT | ["T01", ...] |
| purpose | TEXT | 목적 |
| when_to_use | TEXT | 사용 시점 |
| core_heuristics_json | TEXT | ["..."] |
| step_checklist_json | TEXT | ["..."] |
| bad_signs_json | TEXT | ["..."] |
| good_signs_json | TEXT | ["..."] |
| created_at / updated_at | TEXT | ISO 시각 |

### ax_prompts
| 컬럼 | 타입 | 설명 |
| --- | --- | --- |
| id | INTEGER PK | 내부 PK |
| job_run_id | INTEGER | JobRun FK |
| agent_id | TEXT | ax_agents.agent_id |
| execution_environment | TEXT | n8n_gpt_node/http_gpt_api/pure_n8n_logic/human_only |
| prompt_version | TEXT | "v0.1" 등 |
| single_prompt | TEXT \| NULL | n8n_gpt_node용 |
| system_prompt | TEXT \| NULL | http_gpt_api system |
| user_prompt_template | TEXT \| NULL | http_gpt_api user 템플릿 |
| logic_hint | TEXT \| NULL | pure_n8n_logic 힌트 |
| human_checklist | TEXT \| NULL | human_only 체크리스트 |
| examples_json | TEXT \| NULL | PromptExample 리스트 JSON |
| mode | TEXT \| NULL | poc/advanced |
| created_at / updated_at | TEXT | ISO 시각 |
