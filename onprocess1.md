# HWPX 변환기 개선 프로세스 기록 (onprocess1)

## 날짜: 2025-11-06

## 목표
Markdown 파일을 HWPX (한글 문서) 형식으로 변환할 때, 폰트, 사이즈, 줄간격, 정렬 등 모든 스타일이 정상적으로 적용되도록 수정

---

## 문제 발견 과정

### 초기 증상
- 테스트 파일: `test_input2.md` → `test_output.hwpx`
- **문제점:**
  - ❌ 폰트 형태 미반영
  - ❌ 폰트 사이즈 미반영
  - ❌ 줄간격 미반영
  - ❌ 정렬 미반영
  - ❌ 줄바꿈 안됨
  - ✅ 표는 제대로 생성됨
  - ❌ 페이지 여백 설정 없음

### 참조 파일
- `test_input2model.hwpx`: 사용자가 수동으로 올바르게 작성한 참조 문서
- 이 파일과 생성된 파일을 비교하여 문제점 파악

---

## 발견된 문제들과 해결 과정

### 문제 1: header.xml 구조 부족
**발견:**
- Model header.xml: 59KB
- Generated header.xml: 3.6KB

**원인:**
1. `borderFill` 정의 누락 (0개 vs 6개)
2. `charPr` 정의 부족 (7개 vs 17개)
3. `paraPr` 정의 부족 (6개 vs 22개)

**해결:**
- borderFills 6개 추가 (id 1-6, 표 스타일용)
- charPr 17개로 확장 (id 0-16)
- paraPr 22개로 확장 (id 0-21)

**관련 코드:** `md_to_hwpx_v2.py` - `_create_header_xml()` 함수

---

### 문제 2: 폰트 호환성 (해결됨, 하지만 근본 원인 아님)
**시도:**
- 원본 폰트: HY헤드라인M, 휴먼명조
- 변경 폰트: 맑은 고딕, 바탕 (Windows 호환)

**결과:** 폰트만 바꿔서는 해결 안 됨

---

### 문제 3: linesegarray 누락 ⭐ (핵심 발견 #1)
**발견:**
- Model section0.xml: 모든 단락에 `<hp:linesegarray>` 존재
- Generated section0.xml: 하나도 없음!

**의미:**
`linesegarray`는 각 줄의 레이아웃을 정의하는 핵심 요소:
- `vertsize`: 폰트 높이
- `textheight`: 텍스트 높이
- `baseline`: 베이스라인 위치
- `spacing`: 줄간격

**이게 없으면 폰트 크기, 줄간격, 줄바꿈이 전부 무시됨!**

**해결:**
다음 함수들에 linesegarray 추가:
1. `create_paragraph()` - 일반 단락
2. `create_title_table()` - 제목 표 (3개 행)
3. `create_emphasis_table()` - 강조 표 (1개 행)

**계산 공식:**
```python
vertsize = font_height
textheight = font_height
baseline = int(font_height * 0.85)
spacing = int(font_height * (line_spacing_percent / 100) * 0.6)
```

**관련 코드:** `md_to_hwpx_v2.py`:320-381, 384-469, 471-518

---

### 문제 4: styles 섹션 완전 누락 ⭐⭐ (핵심 발견 #2, 최종 원인!)
**발견:**
- Model header.xml: `<hh:styles itemCnt="22">` 존재
- Generated header.xml: `<hh:styles>` 섹션 자체가 없음!

**의미:**
HWPX는 스타일 시스템을 사용:
- `styleIDRef="0"` → "바탕글" 스타일 참조
- 하지만 스타일 정의가 없으면 → 한글 프로그램이 렌더링 불가!

**왜 이게 문제였나:**
1. section0.xml에서 `styleIDRef="0"` 사용
2. 하지만 header.xml에 style id="0" 정의 없음
3. charPrIDRef, paraPrIDRef를 직접 지정해도 → 스타일이 우선 적용되어야 함
4. **스타일 정의 없음 → 모든 서식 무시!**

**해결 예정:**
Model에서 22개 스타일 정의 가져와서 header.xml에 추가 필요

**스타일 구조:**
```xml
<hh:style id="0" type="PARA" name="바탕글" engName="Normal"
          paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0"
          langID="1042" lockForm="0"/>
```

---

## 기술적 구조 이해

### HWPX 파일 구조
```
hwpx (ZIP 파일)
├── Contents/
│   ├── header.xml      # 스타일, 폰트, 문단/문자 속성 정의
│   └── section0.xml    # 실제 문서 내용
└── mimetype
```

### 렌더링 체인
1. section0.xml: `<hp:p styleIDRef="0" paraPrIDRef="302">`
2. header.xml: style id="0" → paraPrIDRef="0", charPrIDRef="0" (기본값)
3. **하지만** 직접 지정한 paraPrIDRef="302"가 오버라이드
4. header.xml: paraPr id="302" → 정렬, 줄간격 정보
5. charPr → 폰트, 크기 정보
6. **linesegarray → 실제 줄 레이아웃 (이게 없으면 무용지물!)**
7. **styles → 전체 체계의 기반 (이게 없으면 시작조차 안 됨!)**

---

## 현재 상태

### 완료된 수정
✅ borderFills 6개 추가
✅ charPr 17개로 확장
✅ paraPr 22개로 확장
✅ linesegarray 추가 (create_paragraph, create_title_table, create_emphasis_table)
✅ 폰트를 Windows 호환 폰트로 변경

### 진행 중
🔄 styles 섹션 추가 (Model에서 22개 스타일 정의 가져오기)

### 남은 작업
⏳ styles 추가 후 테스트
⏳ 페이지 여백 설정 (secPr) 추가
⏳ 최종 검증

---

## 주요 파일 및 함수

### md_to_hwpx_v2.py
- `_create_header_xml()` (line 741-1007): header.xml 생성, borderFills/charPr/paraPr 정의
- `create_paragraph()` (line 320-381): 단락 XML 생성, linesegarray 포함
- `create_title_table()` (line 384-469): 제목 표 생성, linesegarray 포함
- `create_emphasis_table()` (line 471-518): 강조 표 생성, linesegarray 포함

### style_textbook.md
스타일 규칙 정의 파일:
- 주제목: 맑은 고딕 15pt, 줄간격 130%, 센터 정렬
- 소제목: 맑은 고딕 15pt, 줄간격 160%, 좌측 정렬
- 본문: 바탕 15pt, 줄간격 160%
- 설명: 바탕 15pt, 줄간격 160%
- 작은 설명: 맑은 고딕 12pt, 줄간격 160%
- 강조: 바탕 15pt bold, 줄간격 130%, 센터 정렬

---

## 학습한 교훈

### 1. 점진적 디버깅
- 처음에는 "폰트 문제"로 보였지만
- 실제로는 여러 계층의 문제가 쌓여 있었음
- **작은 차이를 하나씩 비교하며 근본 원인 찾기**

### 2. 참조 파일의 중요성
- Model 파일과 Generated 파일을 XML 레벨에서 비교
- 파일 크기 차이부터 시작해서 구조적 누락 발견

### 3. 한글 문서 포맷의 계층 구조
```
styles (최상위 체계)
  ↓
charPr / paraPr (속성 정의)
  ↓
linesegarray (실제 레이아웃)
```
**하나라도 빠지면 전체가 무너짐**

### 4. "왜 안 되지?"보다 "뭐가 다르지?"
- 증상에 집중하지 말고
- 정상 파일과의 구조적 차이에 집중

---

## 다음 단계

1. **styles 섹션 추가** (현재 작업)
2. 테스트 후 피드백
3. 필요시 추가 수정
4. 페이지 설정 (secPr) 추가
5. 최종 검증

---

## 참고 명령어

### HWPX 파일 압축 해제
```bash
python3 -m zipfile -e file.hwpx extracted_folder
```

### XML 비교
```bash
# 파일 크기 비교
ls -lh */Contents/header.xml

# 특정 요소 개수 비교
grep -c '<hh:charPr' */Contents/header.xml
grep -c '<hp:linesegarray' */Contents/section0.xml

# 특정 속성 추출
grep -o 'paraPr id="[0-9]*"' header.xml
```

### 변환 실행
```bash
python3 md_to_hwpx_v2.py test_input2.md test_output.hwpx
```

---

## 버전 정보
- Python: 3.12
- OS: WSL2 (Linux 6.6.87.2-microsoft-standard-WSL2)
- 작업 디렉토리: /home/d997/hwpxconverter1
- Git 브랜치: pyhwpx-plus
