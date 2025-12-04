# Iteration Log
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

| 날짜 | 변경 내용 | 이유 | 영향 |
| --- | --- | --- | --- |
| 2025-12-04 | 문서 운영 지침 `doc_ops_guide.md` 추가, Docs Index 반영 | md 최신화 기준을 팀에 공유 | 문서 유지보수 일관성 강화 |
| 2025-12-04 | Align 체크 결과 재검수: Stage0/1/2 정합 OK로 갱신 | 코드/스키마/프롬프트 동기화 반영 | 추가 정합성 조치 불필요 명시 |
| 2025-12-04 | database_and_table.md에 Stage 2.1 static_meta 전달/DB fallback UI 반영 | 실제 코드의 static_result 전달 및 UI DB fallback 동작 반영 | 문서-코드 일관성 유지 |
| 2025-12-04 | file_structure.md에 stage_runner_ax/AX repos/doc_ops_guide 반영 | 신규 파일/리포지토리/문서 추가를 구조도에 반영 | 탐색성 향상, 문서 최신화 |
| 2025-12-04 | UX/UI 가이드에 Stage1/2 DB 캐시 표시 규칙 반영, troubleshooting에 탭 빈 화면 대응 업데이트 | UI가 세션 없이도 DB 데이터를 보여주는 최신 코드 반영 | 사용자 혼선 감소, 디버깅 가이드 최신화 |
| 2025-12-04 | Stage 1.3 Static 추가, Stage 메타/ui_label 정비, “다음 단계 실행” 순차 런너/버튼 도입, max_tokens 81920 상향, docs 전면 싱크 | UI/파이프라인 일관성 확보, 정적 태깅/워크플로우 데이터 영속, 긴 토큰 허용 | 0.2→1.2→1.3→2.2 자연 실행, job_tasks/job_task_edges 저장, UI 탭/문서 싱크 |
| 2025-12-03 | Stage 3 Workflow Struct/Mermaid 구현 반영, 코드 설명 문서 추가, 전체 docs 동기화 | UI/코드에 맞춰 문서 최신화, 신규 워크플로우 파이프라인 공유 | 실행 버튼/탭/스키마 혼선 감소, 신규 Stage 이해도 향상 |
| 2025-12-02 | docs 최신화: Stage 0/1 스키마/플로우/프롬프트 규칙 반영, gemini_models 단순화 | 코드/문서 싱크 유지, 비개발자 가독성 확보 | 실행/문서 간 혼선 감소, 스텁/LLM 동작 이해도 향상 |
| 2025-12-02 | Stage 1 Gemini 헬퍼/파서/sanitizer 반영, parsing_guide/stage_runner 추가, 디버그 필드/스텁 정책 문서화 | 최신 코드 패턴 공유, 파서 오류 대응력 향상 | LLM 키 미설정/JSON 오류 시 동작 예측 가능, 신규 Stage 추가 시 재사용성 제고 |
