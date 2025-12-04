# Iteration Log
> Last updated: 2025-12-04 (by AX Agent Factory Codex)

| 날짜 | 변경 내용 | 이유 | 영향 |
| --- | --- | --- | --- |
| 2025-12-04 | Stage 1.3 Static 추가, Stage 메타/ui_label 정비, “다음 단계 실행” 순차 런너/버튼 도입, max_tokens 81920 상향, docs 전면 싱크 | UI/파이프라인 일관성 확보, 정적 태깅/워크플로우 데이터 영속, 긴 토큰 허용 | 0.2→1.2→1.3→2.2 자연 실행, job_tasks/job_task_edges 저장, UI 탭/문서 싱크 |
| 2025-12-03 | Stage 3 Workflow Struct/Mermaid 구현 반영, 코드 설명 문서 추가, 전체 docs 동기화 | UI/코드에 맞춰 문서 최신화, 신규 워크플로우 파이프라인 공유 | 실행 버튼/탭/스키마 혼선 감소, 신규 Stage 이해도 향상 |
| 2025-12-02 | docs 최신화: Stage 0/1 스키마/플로우/프롬프트 규칙 반영, gemini_models 단순화 | 코드/문서 싱크 유지, 비개발자 가독성 확보 | 실행/문서 간 혼선 감소, 스텁/LLM 동작 이해도 향상 |
| 2025-12-02 | Stage 1 Gemini 헬퍼/파서/sanitizer 반영, parsing_guide/stage_runner 추가, 디버그 필드/스텁 정책 문서화 | 최신 코드 패턴 공유, 파서 오류 대응력 향상 | LLM 키 미설정/JSON 오류 시 동작 예측 가능, 신규 Stage 추가 시 재사용성 제고 |
