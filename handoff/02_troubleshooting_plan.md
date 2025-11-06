# 트러블슈팅 계획 (갱신: FIX4 컨텍스트)

## 목표
- 한글 2020에서 손상 없이 열림(OPF/HEADREF)
- 페이지 방향=세로(PORTRAIT)와 여백 완전 반영
- 소제목/본문/설명 앞 ‘전 줄바꿈’이 시각적으로 확실히 보임
- 제목/본문/강조 폰트/크기/굵기 안정 적용

## 단계별 계획

### 1) 페이지 방향 안정화
- 접근 A(권장): `<hp:pagePr>`에서 `landscape` 속성을 제거하고 width < height로만 세로를 표현
  - 장점: 버전별 enum 해석차 제거
  - 확인: section0.xml 첫 컨트롤 문단의 secPr에 적용, 감사 스크립트로 width/height만 확인
- 접근 B(대안): `landscape="NARROWLY"`로 표기(일부 샘플과 호환) + width/height 유지

### 2) ‘전 줄바꿈’은 빈 문단 대신 스타일 여백으로 처리
- header.xml의 paraPr(23: 소제목, 24: 본문, 25: 설명-, 26: 설명*)에 위쪽 여백(prev)을 부여
  - 예) `<hh:margin><hc:prev value="283" unit="HWPUNIT"/></hh:margin>` (약 1/2줄)
- NBSP 빈 문단은 보조 옵션으로 유지(환경별 편차 대비)
- 검증: 동일 입력에서 NBSP 유무/여백값별 가시성 비교

### 3) HEADREF 패키징 재구성
- HEADREF 시 META-INF를 아래처럼 구성
  - `META-INF/container.xml` (OCF rootfile → `Contents/content.hpf`)
  - `META-INF/container.rdf` (header/section 파트 매핑)
- `Contents/content.hpf`(HwpDoc)에서는 `href="header.xml"`, `href="section0.xml"` (동일 디렉터리 상대)
- 확인: HEADREF 파일 단독 열기/저장 가능 여부

### 4) 소제목 크기 안정화
- paraPr에 `snapToGrid="0"`, `fontLineHeight="0"` 유지, `lineWrap="BREAK"`
- 필요 시 소제목 charPr를 한 번 더 명시(bold 여부 포함)하여 상속 영향 최소화

### 5) 회귀 방지와 로그
- `--audit`/`--header-audit`를 기본 켜기(로컬 검증용)
- audit에 secPr 요약(landscape 존재 여부, width/height, margin) 추가

## 구현 체크리스트(코드 위치)
- 페이지 방향: `HWPXGenerator.create_section` 첫 컨트롤 문단의 `<hp:pagePr>` 생성부
- 여백으로 줄바꿈: `MDtoHWPXConverter._create_header_xml`의 paraPr(22~27) 생성부
- HEADREF 패키징: `MDtoHWPXConverter.create_hwpx`의 META-INF/Contents 분기

## 완료 기준
- OPF/HEADREF 모두 한글 2020에서 오류 없이 열림
- 첫 페이지가 확실히 세로 방향, 여백 값 일치
- 소제목/본문/설명 앞 공백 라인이 명확히 보임
- 감사 로그에서 para/char/페이지 설정이 기대치와 일치

