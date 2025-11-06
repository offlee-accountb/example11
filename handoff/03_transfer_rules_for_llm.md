# LLM용 HWPX 구현 가이드 (요점 정리)

## 1) 패키징(권장: OPF)
- zip 엔트리
  - `mimetype`(무압축/첫 항목, 값=`application/hwp+zip`)
  - `version.xml`, `settings.xml`
  - `META-INF/container.xml`(OCF rootfile → `Contents/content.hpf`), `META-INF/manifest.xml`
  - `Contents/content.hpf`(OPF), `Contents/header.xml`, `Contents/section0.xml`
- HEADREF 대안(한글 2020 호환 강화)
  - `META-INF/container.xml` + `META-INF/container.rdf` 포함
  - `Contents/content.hpf`는 `<hpf:HwpDoc>`, `<hpf:HeadRef href="header.xml">`, `<hpf:SectionRef href="section0.xml">`

## 2) header.xml 작성 규칙
- `<hh:fontfaces>`: 7개 언어(HANGUL/LATIN/HANJA/JAPANESE/OTHER/SYMBOL/USER)에 동일한 폰트를 등록
  - HANGUL: 0=맑은 고딕, 1=휴먼명조, 2=맑은 고딕(보조)
  - LATIN: 0=Malgun Gothic, 1=Times New Roman, 2=Malgun Gothic
- `<hh:charProperties itemCnt="N">` 실제 개수로 N을 기록
  - 각 `<hh:charPr id>`에 `fontRef`(7슬롯), `ratio/spacing/relSz/offset`, `underline/strikeout/outline/shadow` 포함
  - 제목/소제목/본문/강조/설명* 등 필요한 스타일에 안정 ID 사용(예: 8/9/11/15/16)
- `<hh:paraProperties itemCnt="M">` 실제 개수로 M을 기록
  - `<hh:paraPr>`에 `align`, `lineSpacing`, `snapToGrid="0"`(겹침 방지), `lineWrap="BREAK"`
  - ‘전 줄바꿈’이 필요한 스타일에는 `<hh:margin><hc:prev value="X" unit="HWPUNIT"/></hh:margin>` 권장
    - 예: 소제목/내용/설명/별표설명 → 1000/800/600/400(HWPUNIT)
- `<hh:styles>`는 기본 스타일 집합 유지(필요 시 확장)

## 3) section0.xml 작성 규칙
- 섹션 프롤로그(컨트롤 전용 문단) 먼저 배치
  - 첫 `hp:p` 내 run에 `<hp:secPr>` 포함
  - 페이지 방향은 샘플과 동일 조합 사용(환경차 회피)
    - 예: `landscape="WIDELY"` + width=59528, height=84186 (A4 세로)
  - 여백은 mm→HWPUNIT로 변환해 `<hp:margin>`에 기록
- 본문 문단
  - 각 문단: `<hp:p paraPrIDRef=...>`로 para 스타일 참조
  - 인라인: `<hp:run charPrIDRef=...>`로 char 스타일 참조
  - 줄간격 자동화: `hp:linesegarray`는 생략하거나 옵션화(--no-lineseg)
- ‘전 줄바꿈’ 처리
  - NBSP 빈 문단은 보조 수단(환경별 편차 있음)
  - 권장: paraPr의 위쪽 여백(prev)로 시각적 빈 줄 확보
  - 대안(중기부 표준): 각 스타일 앞줄에 1문자 스페이서(NBSP 등, 10/8/6/4pt)를 출력 후 Enter — 전용 char/para 정의가 필요

## 4) 파서/매핑 요령
- 마커 인식 예시
  - `<주제목>` → title para/char
  - `□` → subtitle
  - `◦` → body bullet
  - 들여쓴 `-`/`*` → description
  - `<강조>` → emphasis table or 강조 문단
- 텍스트 전처리
  - 불릿 앞 공백 1칸 보장(예: ` ◦ ...`)
  - 인라인 굵게/기울임/코드 → run 분리(`**`, `*`, `` ` ``, 각각 bold/italic/code charPr)

## 5) Python 구현 관례(스니펫)
```python
# itemCnt는 실제 개수로 넣는다
char_items = []
def charpr(cid, height, font_id, bold=False, italic=False):
    char_items.append(f'<hh:charPr id="{cid}" height="{height}" textColor="#000000">')
    char_items.append(f'  <hh:fontRef hangul="{font_id}" latin="{font_id}" hanja="{font_id}" japanese="{font_id}" other="{font_id}" symbol="{font_id}" user="{font_id}"/>')
    if bold: char_items.append('  <hh:bold/>')
    if italic: char_items.append('  <hh:italic/>')
    char_items.append('  <hh:underline type="NONE"/>')
    char_items.append('</hh:charPr>')

para_items = []
def parapr(pid, align, lsp, space_before=None, snap_to_grid='0'):
    para_items.append(f'<hh:paraPr id="{pid}" snapToGrid="{snap_to_grid}">')
    para_items.append(f'  <hh:align horizontal="{align}"/>')
    if space_before is not None:
        para_items.append('  <hh:margin>')
        para_items.append(f'    <hc:prev value="{space_before}" unit="HWPUNIT"/>')
        para_items.append('  </hh:margin>')
    para_items.append(f'  <hh:lineSpacing type="PERCENT" value="{lsp}"/>')
    para_items.append('</hh:paraPr>')
```

스페이서 모드(옵션)
```python
# 전용 스페이서 para/char 정의
charpr(201, 1000, body_font_id)  # 10pt
charpr(202,  800, body_font_id)  # 8pt
charpr(203,  600, body_font_id)  # 6pt
charpr(204,  400, body_font_id)  # 4pt
parapr(28, 'LEFT', '100', snap_to_grid='0')
parapr(29, 'LEFT', '100', snap_to_grid='0')
parapr(30, 'LEFT', '100', snap_to_grid='0')
parapr(31, 'LEFT', '100', snap_to_grid='0')

# 사용: 대상 문단 앞에 NBSP 빈 문단을 삽입
create_blank_paragraph(para_id=28, char_id=201)  # sub_title 앞
```

## 6) 검증 루틴
- 헤더 감사: 참조된 para/char ID가 header.xml에 실제 존재하는지, 정의값(height/align/lineSpacing/fontRef) 요약
- 섹션 감사: 첫 문단에 secPr 유무, pagePr width/height/landscape, margin 값 로깅
- 패키징 감사: mimetype 무압축, META-INF/OCF/manifest 유무, content.hpf 내부 링크 경로 검사

## 7) 실무 팁
- 표 래핑 run은 `charPrIDRef="0"`로 두어 내부 텍스트 스타일을 덮어쓰지 않게 한다.
- 폰트 대체 방지: 설치 환경의 실제 폰트명(face)을 정확히 기록.
- OPF를 기본 포맷으로 삼고, HEADREF는 필요한 경우에만 엄격한 META-INF 구성으로 제공.
