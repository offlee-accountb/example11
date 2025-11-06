# 현재 남아있는 이슈 (이번 컨텍스트)

- 블로킹 이슈: 없음 (세로 방향·전 줄간격·줄겹침 해결)

정리
- 세로 방향 표시
  - 적용: `Contents/section0.xml` `<hp:pagePr landscape="WIDELY" width="59528" height="84186">` (샘플 `basictest1.hwpx`와 동일)
- 전(前) 줄간격
  - 적용: header의 paraPr 23/24/25/26에 `<hc:prev>` 값을 각각 1000/800/600/400(HWPUNIT)로 설정
- 줄겹침/줄바꿈 깨짐
  - 적용: 커스텀 문단(22~27) `snapToGrid="0"`, lineSpacing은 PERCENT로 지정, 문단 내부 강제 `<hp:br>` 제거

향후 과제(계획)
- “중기부 표준” 방식 옵션화
  - 각 스타일 앞줄에 전용 스페이서 문자를 1개(10/8/6/4pt 등) 출력하고 Enter로 줄 전환
  - 구현: header에 스페이서 전용 char/para 정의(para는 snapToGrid=0), CLI 옵션 `--spacer-mode`
  - 현재는 “기재부 예타” 방식(para prev 여백)으로 안정화되어 있음
