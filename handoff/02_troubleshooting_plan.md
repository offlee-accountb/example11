# 트러블슈팅 기록 (이번 컨텍스트)

목표
- 세로 방향 표시, 전(前) 줄간격 가시성, 줄겹침 제거를 동시에 만족

문제와 원인
- 페이지가 가로로 렌더링됨
  - `landscape` enum 해석 차이(PORTRAIT/NARROWLY)가 환경마다 달라 샘플과 불일치
- 전 줄간격이 모두 동일하게 보임(10으로 고정)
  - 빈 문단/lineseg 고정값 영향으로 엔진이 최소 높이로 보정
- 줄바꿈이 안 되고 겹쳐 보임
  - snapToGrid=1 + 잘못된 lineseg/textheight 고정이 겹치면서 라인 메트릭 충돌

조치 사항(최종 안정 해법)
- 페이지 방향: 샘플(`basictest1.hwpx`)과 동일하게 `<hp:pagePr landscape="WIDELY" width="59528" height="84186">`
- 전 줄간격: header의 paraPr 23/24/25/26에 `<hc:prev>` 1000/800/600/400(HWPUNIT)
- 줄겹침 방지: 커스텀 문단(22~27) `snapToGrid="0"`, lineSpacing은 `<hh:lineSpacing type="PERCENT" value="...">`로만 표기
- 기타: 문단 내부 `<hp:br>` 제거, 기본 실행에서 `--no-lineseg` 사용으로 엔진 자동 줄높이 활용

왜 해결되었나
- 방향: 동일 제품군에서 확인된 샘플과 같은 조합을 사용해 enum 해석 차를 제거
- 간격: 스타일(prev) 기반의 space-before는 환경별 최소 라인 보정 영향을 받지 않음
- 겹침: grid 스냅/라인 세그 고정 제거로 메트릭 충돌 해소, 퍼센트 줄간격은 렌더러가 일관 처리

검증
- 산출물 `output/_FINAL_FIX10.hwpx`를 한글 2020에서 열어 세로 표기/줄겹침 무/전 줄간격 구분 확인
- 감사 로그로 para/char 존재/값 요약, section의 pagePr 속성 확인

회귀 방지
- 옵션 유지: `--audit`, `--header-audit`, `--no-lineseg`
- 향후 `--page-orient {widely|narrowly|omit}` 옵션 추가 검토

