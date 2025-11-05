# 현재 이슈 요약

## 패키징/파일 구조
- mimetype: 무압축/첫 항목 필요(현재 충족)
- container.xml: rootfile → `Contents/content.hpf` (media-type=application/hwpml-package+xml)
- content.hpf: OPF 패키지(정상)/HeadRef 패키지(환경 따라 손상 위험) → 기본은 OPF 권장
- 메타 파일: `META-INF/manifest.xml`, `META-INF/container.rdf`, `settings.xml` 포함

## 헤더/스타일 적용
- charPr/paraPr ID는 생성·참조되지만, 렌더링에서 체감이 약한 경우가 있었음
  - 원인 후보: (1) 폰트 대체(설치 불가) (2) paraPr 구조 미세 불일치 시 무시 (3) 헤더 연결 경로 차이
  - 대응: 핀 폰트(`--pin-font "맑은 고딕"`) + OPF 패키징 고정 + 감사 로그로 확인

## 페이지 설정
- secPr를 단락에 직접 주입 시 한글에서 손상 발생(컨트롤-run 구조 요구) → 템플릿 ctrl 블록 복제 필요(보류)

## 마커/파서
- 마커 인식: `<주제목>`, `□`, `◦`, 들여쓴 `-`/`*`, `<강조>` 지원
- 결과 텍스트: 마커 포함/제거 규칙 반영(소제목/본문 등)
- 테이블: `| ... |` 감지하되 아직 텍스트로 유지(감사에 경고)

## 감사(진단 도구)
- 라인 감사: `output.audit.md`에 원문/마커/적용 paraPrID/charPrID/경고 기록
- 헤더 감사: `output.header.audit.md`에 실제 ID 정의(height/bold/align/lineSpacing/fontRef) 요약

## 환경/운영 이슈
- 파일 잠금: HWPX가 열려 있으면 PermissionError → 파일 닫고 실행 필요
- 세션 정책: read-only/on-request 모드에 따라 쓰기/승인 필요

## 미구현/미완성
- 표 렌더링(머리행/본문행/테두리/여백/열폭)
- 템플릿 기반 섹션 프롤로그(secPr ctrl) 주입
- 텍스트북(YAML) 직접 로더: 현재는 합성 스타일/핀 폰트로 대응 중

