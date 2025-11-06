# 문제 정의 (MD → HWPX, 정부 문서 양식)

## 목적
- Markdown 원문을 정부 문서 양식(HWPX)으로 자동 변환한다.
- 한글 2020에서 “손상 없이” 열리고, 지정한 폰트/문단/줄간격/마커 규칙이 적용된다.

## 입력
- MD 원문: 표준 Markdown + 추가 마커(예: `<주제목>`, `□`, `◦`, 들여쓴 `-`/`*`, `<강조>`)
- 선택 입력:
  - 텍스트북(`style_textbook.md`): 자연어 규칙(사람 친화형)
  - 스타일 가이드(YAML): 기계가 읽는 규칙(선택, 추후)
  - 템플릿 HWPX(`target1.hwpx` 등): 기존 문서 스타일/섹션 프롤로그 재사용

## 출력
- OPF 패키징 HWPX: `mimetype(무압축)`, `META-INF/*`, `Contents/content.hpf(OPF)`, `Contents/header.xml`, `Contents/section0.xml`, `settings.xml`
- 감사 로그(선택): `output.audit.md`(라인→스타일 매핑), `output.header.audit.md`(ID→정의 요약)

## 범위(Scope)
- 인라인: 굵게/기울임/코드 유지
- 문단: 제목/소제목/본문/설명/강조 등 스타일(폰트/크기/정렬/줄간격) 적용
- 마커: `<주제목>`, `□`, `◦`, 들여쓴 `-`/`*`, `<강조>` 인식
- 패키징: OPF(기본), 필요 시 템플릿 기반 secPr 주입

## 비범위(Out of Scope)
- 이미지/수식/각주/하이퍼링크/도형
- 표 렌더링(현시점 보류; 텍스트 유지)

## 수용 기준(AC)
- 한글 2020에서 “손상” 없이 열림
- 제목(≈18pt/CENTER/130%), 본문(≈12pt/LEFT/160%)이 체감될 정도로 적용
- 감사 로그에 라인별 매핑(paraPrID/charPrID)이 기록되고, 헤더 감사에서 해당 ID 정의가 의도대로 보임

## 실행 예시
```
python md_to_hwpx_v2.py test_input.md output.hwpx --packaging opf \
  --pin-font "맑은 고딕" --audit --header-audit
```

