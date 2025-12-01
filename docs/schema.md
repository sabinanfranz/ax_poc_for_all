# AX Agent Factory 스키마 개요

## 1. 전체 개념 지도(Top-level Overview)
JobRun → JobResearch → IVCResult → DNAResult → WorkflowResult → AXResult(AgentTable_for_AgentArchitect) → AgentSpecsResult(AgentSpecs_for_PromptBuilder) → SkillResult(+SkillSpec) → PromptResult(LLMPrompts_for_n8n) → AgentRun.  
- JobRun: 회사/직무 실행 식별용 루트 엔티티  
- JobResearch: 원문 직무 설명과 출처 묶음  
- IVCResult: IVC-A/B/C 태스크 리스트  
- DNAResult: TaskCard(IVC+DNA) 정규화 결과  
- WorkflowResult: 워크플로우 구조 + Mermaid 코드  
- AXResult: AgentTable_for_AgentArchitect 요약 테이블  
- AgentSpecsResult: AgentSpecs_for_PromptBuilder 상세 스펙  
- SkillResult: 스킬 카탈로그 및 에이전트별 스킬 스펙  
- PromptResult: 에이전트 실행용 LLM 프롬프트 묶음  
- AgentRun: 샘플 실행 I/O와 모델/평가 로그  
- Job AX Input Pack: Workflow Architect 입력 패키지 (job_meta + mermaid + task_cards)

## 2. 파이프라인 단계별 입·출력 흐름
| Step | Input 엔티티/필드 | Output 엔티티/필드 | 설명 |
|------|-------------------|--------------------|------|
| 0. Job Research | JobRun(company_name, job_title) | JobResearch(raw_job_desc, sources) | 직무/회사 기반 리서치 텍스트와 소스 수집 |
| 1. IVC | JobResearch.raw_job_desc | IVCResult.ivc_tasks | IVC-A/B/C로 태스크 추출·분류 |
| 2. DNA | IVCResult.ivc_tasks | DNAResult.task_cards | 태스크를 DNA(Primitive/Domain/Mechanism)로 주석화 |
| 3. Workflow Structuring | DNAResult.task_cards | WorkflowResult.workflow_structure | Stage/Stream/Task/Edge 구조화 |
| 4. Mermaid Visualization | WorkflowResult.workflow_structure | WorkflowResult.mermaid_code | Notion 호환 Mermaid 문자열 생성 |
| 5. AX Architect | WorkflowResult + Job AX Input Pack | AXResult.agent_table | Stage/Agent 요약 테이블 생성 |
| 6. Agent Architect | AXResult.agent_table | AgentSpecsResult.agent_specs | 에이전트별 상세 스펙(입출력/제약) 확정 |
| 7. Skill Planner & Deep Research | AgentSpecsResult.agent_specs | SkillResult.skill_catalog, SkillResult.agent_skill_specs | 스킬 정의 및 에이전트별 스킬 매핑 |
| 8. Prompt-Builder | AgentSpecsResult.agent_specs, SkillResult | PromptResult.llm_prompts_for_agents | 실행용 프롬프트 묶음 작성 |
| 9. Runner & Evaluation | PromptResult + 샘플 입력 | AgentRun | 샘플 실행, 모델 정보, 평가 기록 |

입출력 연결 요약:  
- job_run_id는 모든 Stage 결과에 FK로 공유된다.  
- Stage 5 출력 `agent_table` 전체가 Stage 6 입력으로 그대로 들어간다.  
- Stage 6 출력 `agent_specs`가 Stage 8 Prompt-Builder의 기본 입력, Stage 7 Skill Planner는 agent_id 기준으로 스킬을 매핑한다.  
- Stage 8 출력 `llm_prompts_for_agents`가 Stage 9 Runner의 실행 프롬프트로 사용된다.  

## 3. 엔티티(테이블/JSON 오브젝트)별 상세 스키마

### 3.1 JobRun
역할: 하나의 직무 실행을 식별하는 루트.  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| id | string | Y | JobRun PK |
| company_name | string | Y | 회사명 |
| job_title | string | Y | 직무명 |
| created_at | datetime | Y | 생성 시각 |

### 3.2 JobResearch
역할: 리서치 텍스트와 출처.  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| job_run_id | string | Y | JobRun FK |
| raw_job_desc | string | Y | 직무 설명 합성 텍스트 |
| sources[] | array | N | 리서치 소스 목록 |
| sources[].source_type | string | Y | web \| manual |
| sources[].url_or_id | string | Y | URL 또는 식별자 |
| sources[].note | string | N | 설명 |

### 3.3 IVCResult
역할: IVC-A/B/C 태스크 리스트.  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| job_run_id | string | Y | JobRun FK |
| ivc_tasks | array | Y | Phase별 태스크 리스트(태스크 atom + phase) |

### 3.4 DNAResult
역할: IVC 태스크를 DNA 주석 포함 TaskCard로 정규화.  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| job_run_id | string | Y | JobRun FK |
| task_cards | array | Y | TaskCard 리스트 (Job AX Input Pack 1.3 동일) |

TaskCard (공통):  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| task_id | string | Y | 예: "T01" |
| title | string | Y | 태스크 이름 |
| phase | string | Y | IVC Phase (예: "SENSE") |
| one_line_summary | string | N | 한 줄 요약 |
| trigger | string | N | 시작 트리거 |
| inputs | string | N | 주요 입력 |
| action | string | N | 수행 액션 |
| output | string | N | 산출물 |
| dna | object | Y | Primitive/Domain/Mechanism |

dna 서브필드:  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| primitive_lv1 | string | Y | 예: SENSE/DECIDE/TRANSFORM |
| primitive_lv2 | string | Y | 세부 Primitive 코드 |
| domain_lv1 | string | Y | Physical / Digital/Info / Financial … |
| domain_lv2 | string | Y | 세부 Domain |
| mechanism_m | string | Y | M1 / M2 등 |
| mechanism_lv2 | string | Y | 세부 Mechanism 코드 |

### 3.5 WorkflowResult
역할: 워크플로우 구조와 Mermaid 코드.  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| job_run_id | string | Y | JobRun FK |
| workflow_structure | object | Y | Stage/Stream/Task/Edge 구조 JSON |
| mermaid_code | string | Y | ```mermaid ...``` 문자열 |

### 3.6 AXResult (AgentTable_for_AgentArchitect)
역할: Agent Architect 입력용 요약 테이블.  
구조: `stage_context`(object), `global_policies`(array of string), `agents`(array of object)

stage_context:  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| stage_name | string | Y | Stage 이름 |
| business_goal | string | Y | Stage 비즈니스 목표 |
| primary_kpis | array | N | KPI 리스트 |
| pain_points | array | N | 문제/병목 리스트 |
| primary_sheets | array | N | 주요 구글 시트 |
| rag_usage | string | N | RAG 사용 방식 |

global_policies: string 리스트(스키마/언어/RAG/보안 규칙 등).

agents[]:  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| agent_id | string | Y | 에이전트 ID |
| stage_stream_step | string | Y | Stage / Stream / Step |
| agent_name | string | Y | 에이전트 이름 |
| agent_type | string | Y | structuring / rag / generator / … |
| execution_environment | string | Y | n8n_gpt_node / http_gpt_api / … |
| n8n_workflow_id | string | N | 연결 n8n WF ID |
| n8n_node_name | string | N | n8n 노드 이름 |
| primary_sheet | string | N | 주요 시트 |
| rag_required | boolean | Y | RAG 필요 여부 |
| rag_pattern | string | N | 예: gemini_file_search_basic |
| role_goal | string | Y | 역할/목표 |
| inputs_summary | string | N | 입력 요약 |
| outputs_summary | string | N | 출력 요약 |
| core_actions_summary | string | N | 핵심 액션 요약 |
| human_touchpoint_summary | string | N | HIL 요약 |
| risks_summary | string | N | 리스크 요약 |
| metrics_summary | string | N | 메트릭 요약 |

### 3.7 AgentSpecsResult (AgentSpecs_for_PromptBuilder)
역할: Prompt-Builder가 바로 소비할 에이전트 상세 스펙.  
구조: `stage_context`, `global_policies`, `agents[]`(자세한 입력/출력/제약 포함)

agents[] 주요 필드:  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| agent_id | string | Y | AgentTable와 동일 |
| agent_name | string | Y | 에이전트 이름 |
| stage_stream_step | string | Y | Stage/Stream |
| domain_context | string | N | 도메인 컨텍스트 |
| agent_type | string | Y | structuring 등 |
| execution_environment | string | Y | n8n_gpt_node 등 |
| n8n_node_name | string | N | n8n 노드명 |
| primary_sheet | string | N | 주요 시트 |
| rag_enabled | boolean | Y | RAG 여부 |
| file_search_corpus_hint | string/null | N | 파일 검색 힌트 |
| role_and_goal | string | Y | 역할/목표 문장 |
| success_metrics | array | N | 성공 기준 리스트 |
| input_schema | array | Y | 입력 필드 정의 |
| output_schema | array | Y | 출력 필드 정의 |
| core_actions | array | N | 핵심 액션 |
| tools_or_data_used | array | N | 사용 데이터/도구 |
| constraints | array | N | 제약 사항 |
| error_handling | string | N | 에러 처리 규칙 |
| human_touchpoint | string | N | HIL 규칙 |
| validator_dependencies | array | N | 검증 의존성 |

input_schema / output_schema 공통 필드:  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| name | string | Y | 필드 이름 |
| type | string | Y | string/object/enum 등 |
| required | boolean | Y | 필수 여부 |
| description | string | N | 필드 설명 |
| example | any | N | 예시 값 |
| source | string | N | 입력 출처 (input_schema) |
| validation_rules | string | N | 검증 규칙 |

### 3.8 SkillResult
역할: 스킬 카탈로그와 에이전트별 스킬 스펙.  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| job_run_id | string | Y | JobRun FK |
| skill_catalog | array | N | SkillSpec 요약 리스트 |
| agent_skill_specs | object | N | agent_id별 SkillSpec 묶음 |

### 3.9 SkillSpec (개념)
역할: 스킬 정의 자산.  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| skill_id | string | Y | 스킬 ID |
| name | string | Y | 스킬명 |
| description | string | N | 설명 |
| mental_model | string | N | 멘탈 모델 |
| frameworks | array | N | 프레임워크 텍스트 |
| heuristics | array | N | 휴리스틱 |
| checklist | array | N | 체크리스트 |
| examples | array | N | 예시 ({good, bad}) |

### 3.10 PromptResult (LLMPrompts_for_n8n)
역할: 실행용 프롬프트 묶음.  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| job_run_id | string | Y | JobRun FK |
| stage_name | string | Y | Stage 이름 |
| agents | array | Y | 에이전트별 프롬프트 |

agents[]:  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| agent_id | string | Y | AgentSpecs.agent_id |
| execution_environment | string | Y | n8n_gpt_node / http_gpt_api / … |
| prompt | string | N | n8n_gpt_node용 단일 프롬프트 |
| system_prompt | string | N | http_gpt_api용 system |
| user_prompt_template | string | N | http_gpt_api용 user 템플릿 |

### 3.11 AgentRun
역할: 샘플 실행 및 평가 로그.  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| job_run_id | string | Y | JobRun FK |
| agent_id | string | Y | 실행한 에이전트 |
| sample_input | object | Y | AgentSpec.input_schema 준수 |
| sample_output | object | Y | AgentSpec.output_schema 준수 |
| model_info | object | Y | 모델 호출 정보 |
| model_info.model_name | string | Y | 모델명 |
| model_info.tokens_input | number | N | 입력 토큰 |
| model_info.tokens_output | number | N | 출력 토큰 |
| model_info.estimated_cost | number | N | 추정 비용 |
| eval_score | object | N | 평가 정보 |
| eval_score.auto_score | number | N | 자동 점수 |
| eval_score.auto_reason | string | N | 자동 평가 설명 |
| eval_score.human_score | number/null | N | 사람 점수 |

### 3.12 Job AX Input Pack
역할: Workflow Architect 입력 패키지.  
| 필드명 | 타입 | 필수 | 설명 |
| --- | --- | --- | --- |
| job_meta | object | Y | 직무 메타 |
| job_meta.job_title | string | Y | 직무명 |
| job_meta.industry_context | string | Y | 산업/맥락 |
| job_meta.business_goal | string | N | 상위 목표 |
| workflow_blueprint_mermaid | string | N | mermaid 코드 문자열 |
| task_cards | array | Y | DNAResult와 동일 TaskCard |

## 4. 엔티티 간 관계 & 참조 구조
| From 엔티티 | To 엔티티 | 관계/키 | 설명 |
| --- | --- | --- | --- |
| JobResearch | JobRun | job_run_id(FK) | 실행별 리서치 연결 |
| IVCResult | JobRun | job_run_id(FK) | 실행별 IVC 결과 연결 |
| DNAResult | JobRun | job_run_id(FK) | 실행별 DNA 결과 연결 |
| WorkflowResult | JobRun | job_run_id(FK) | 실행별 워크플로우 결과 연결 |
| AXResult | JobRun | job_run_id(FK) | 실행별 AgentTable 연결 |
| AgentSpecsResult | JobRun | job_run_id(FK) | 실행별 AgentSpecs 연결 |
| SkillResult | JobRun | job_run_id(FK) | 실행별 스킬 결과 연결 |
| PromptResult | JobRun | job_run_id(FK) | 실행별 프롬프트 연결 |
| AgentRun | JobRun | job_run_id(FK) | 실행별 평가 연결 |
| AgentSpecsResult | AXResult | agent_id, stage_context 등 | AgentTable 기반 상세화 |
| PromptResult | AgentSpecsResult | agent_id | AgentSpec → 프롬프트 생성 |
| SkillResult | AgentSpecsResult | agent_id | 에이전트별 스킬 매핑 |
| AgentRun | PromptResult/AgentSpecsResult | agent_id | 프롬프트/스펙으로 실행 |

## 5. Codex용 구현 힌트 (코드 관점 요약)
- 각 엔티티를 Python dataclass 또는 Pydantic 모델로 매핑 시 공통 키 `job_run_id`와 타임스탬프를 표준화; TaskCard, agents[], input_schema/output_schema는 재사용 타입으로 정의.  
- 단계별 함수 시그니처 예: `run_stage_0_job_research(job_run: JobRun) -> JobResearch`, `run_stage_1_ivc(job_research: JobResearch) -> IVCResult`, `run_stage_2_dna(ivc: IVCResult) -> DNAResult`, `run_stage_5_ax(workflow: WorkflowResult, job_pack: JobAXInputPack) -> AXResult`, `run_stage_6_agent_arch(ax: AXResult) -> AgentSpecsResult`, `run_stage_8_prompt_builder(agent_specs: AgentSpecsResult, skills: SkillResult) -> PromptResult`, `run_stage_9_runner(prompt_result: PromptResult, sample_input) -> AgentRun`.  
- AgentTable_for_AgentArchitect → AgentSpecs_for_PromptBuilder는 agents[]를 그대로 이어가며 필드 확장(입출력/제약)만 추가한다.  
- SkillSpec 필드는 텍스트 자산 중심(mental_model, frameworks, heuristics, checklist, examples)으로, 스키마 확정 전까지는 옵션 필드로 취급.  
- PromptResult는 실행 환경별 필드가 상이하므로 `execution_environment` 기준으로 required 필드 분기 처리.

핵심 요약(구현자용):  
- 모든 결과 엔티티는 `job_run_id`로 연결되며, Stage 5~8은 `agent_id`로 연쇄된다.  
- TaskCard 스키마는 DNAResult와 Job AX Input Pack에서 동일하게 재사용된다.  
- AgentTable → AgentSpecs → PromptResult는 agents[]를 확장하는 패턴이다.  
- Runner는 AgentSpecs의 입출력 스키마를 그대로 따르는 `sample_input`/`sample_output`을 기록한다.
