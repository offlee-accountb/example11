# 트러블슈팅 계획(통합)

## 1) 패키징 고정/검증
- 기본 OPF 패키징 사용(HeadRef는 손상 리스크) → `--packaging opf`
- 필수 엔트리: `mimetype(무압축)`, `META-INF/container.xml`, `META-INF/manifest.xml`, `META-INF/container.rdf`, `Contents/content.hpf`, `Contents/header.xml`, `Contents/section0.xml`, `settings.xml`
- 체크리스트: zip 엔트리 순서/유형, rootfile media-type, OPF manifest/spine 일치

## 2) 헤더/스타일 적용 신뢰도 향상
- 핀 폰트 적용: `--pin-font "맑은 고딕"`로 HANGUL/LATIN 동일
- charPr: 제목(18pt/Bold), 소제목(15pt), 본문(12pt/Emphasis/Bold/Italic), 코드(10pt) 확정
- paraPr: 제목(CENTER/130%), 본문(LEFT/160%) 등 최소 안전값부터 적용
- 감사 2종 병행: 라인→ID, ID→정의(align/lineSpacing/height/fontRef)로 실제 적용 검증

## 3) 섹션 페이지 설정(secPr)
- 직접 삽입 금지(손상 유발) → 템플릿에서 control-run 블록을 추출해 맨 앞에 삽입
- 이후 A4/여백(mm) 매핑: top/bottom 15, left/right 20, header/footer 10

## 4) 마커 규칙 확대/정교화
- 현재: `<주제목>`, `□`, `◦`, 들여쓴 `-`/`*`, `<강조>`
- 다음: YAML 가이드(`style_guide.yaml`)로 외부 규칙 로딩 → `mode: synthesize_new_styles`
- 전환 규칙(transitions): 앞→뒤 문단 조합별 spaceBefore/After 오버라이드

## 5) 표(Table) 렌더러(MVP)
- 파싱: `|...|` 블록 + 정렬(:---, :---:, ---:) 감지
- 생성: `hp:tbl > hp:tr > hp:tc > hp:p`
- 스타일: 머리행 배경/굵게/센터, 본문행 좌정렬, 셀 여백 3mm, 테두리 0.5pt(기본)

## 6) 템플릿 병합(제출 문서)
- 기존 HWPX 템플릿의 header/섹션/메타 유지, 섹션에 렌더 결과 삽입 or 플레이스홀더 교체

## 7) 실행 예시
```
# 스타일 적용 + 감사 + OPF 고정
python md_to_hwpx_v2.py test_input.md output.hwpx --packaging opf \
  --pin-font "맑은 고딕" --audit --header-audit

# 템플릿 헤더 사용(옵션)
python md_to_hwpx_v2.py test_input.md output.hwpx --packaging opf \
  --template target1.hwpx --audit --header-audit
```

## 8) 완료 기준
- 한글 2020에서 손상 없이 열림
- 제목/본문 스타일이 시각적으로 적용
- 감사 2종이 매핑/정의를 일관되게 보고
- 표/페이지 설정 등 후속 항목은 단계적 도입

