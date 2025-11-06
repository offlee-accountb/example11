# MD to HWPX Converter - 디버깅용 프로젝트

## 🐛 알려진 문제점

### 1. **표(Table) 미지원**
- MD table이 텍스트로만 변환됨
- 셀 구조 없이 일반 텍스트로 처리

### 2. **굵게 처리 미완성**
- `**text**` 감지는 하지만 실제 굵게 적용 안 됨
- char_id만 바뀌고 bold 속성 미적용

### 3. **기울임(Italic) 미지원**
- `*text*` 파싱은 하지만 XML에 italic 태그 없음

## 📁 프로젝트 구조

```
md-to-hwpx-project/
├── md_to_hwpx_v2.py              # 메인 변환기 코드
├── extracted_styles_v2.json      # 스타일 정의
├── test_input.md                 # 테스트용 MD 파일
├── README.md                     # 이 파일
└── BUGS.md                       # 발견된 버그 목록
```

## 🚀 실행 방법

```bash
python md_to_hwpx_v2.py test_input.md output.hwpx
```

## 🔍 디버깅 포인트

### 1. MDParser.process_inline_formats() (라인 ~90)
**문제**: bold, italic 플래그는 설정하지만 실제 XML 생성에 사용 안 됨

**현재 코드**:
```python
segments.append({
    'text': match.group(2),
    'char_id': base_char_id,
    'bold': True,  # ← 사용 안 됨!
    'italic': False,
    'code': False
})
```

**필요한 수정**:
- HWPXGenerator.create_paragraph()에서 bold/italic 속성을 XML에 추가
- 또는 bold용 별도 char_id 사용

### 2. 표(Table) 파싱 (현재 미구현)
**위치**: MDParser.parse_line() (라인 ~70)

**필요한 작업**:
```python
# 표 시작 감지
if re.match(r'^\|(.+)\|$', line):
    return ('table_row', parse_table_row(line))

# 표 구분선 감지
if re.match(r'^\|[-:]+\|$', line):
    return ('table_separator', '')
```

### 3. HWPX 표 구조 생성 (현재 미구현)
**필요한 XML 구조**:
```xml
<hp:tbl>
  <hp:tr>
    <hp:tc>
      <hp:p>...</hp:p>
    </hp:tc>
  </hp:tr>
</hp:tbl>
```

## 🧪 테스트 케이스

### 테스트 1: 굵게 처리
**입력**: `이것은 **굵은 텍스트**입니다.`  
**기대**: 굵게 표시되어야 함  
**현재**: 일반 텍스트로 표시됨

### 테스트 2: 표
**입력**:
```markdown
| 항목 | 값 |
|------|-----|
| A    | 1   |
```
**기대**: 표 구조  
**현재**: 텍스트 3줄

## 💡 개선 아이디어

### 우선순위 1: 굵게 처리 수정
```python
# HWPXGenerator.create_paragraph() 수정
if seg['bold']:
    # 방법 1: bold 태그 추가
    xml += '<hh:bold/>'
    
    # 또는 방법 2: 굵은 스타일 ID 사용
    bold_char_id = get_bold_char_id(seg['char_id'])
```

### 우선순위 2: 표 지원 추가
1. 표 파싱 로직
2. 표 데이터 구조 생성
3. HWPX tbl XML 생성

### 우선순위 3: 이미지 지원
1. 이미지 파일 읽기
2. Base64 인코딩
3. BinData 섹션 추가

## 🔧 추천 디버깅 도구

- **Claude Code**: 코드 분석 및 수정 제안
- **GPT Codex**: 패턴 기반 버그 찾기
- **Python debugger**: 단계별 실행

## 📊 성능

- **테스트 파일**: 62 단락
- **변환 시간**: 즉시 (< 1초)
- **출력 크기**: 4.2KB

## ⚠️ 중요 노트

**이 코드는 프로토타입입니다!**
- 프로덕션 사용 전 충분한 테스트 필요
- 에지 케이스 처리 미흡
- 에러 핸들링 보완 필요

## 📝 변경 이력

- v2.0 (2025-11-02): 규칙북 기반 초기 버전
- 알려진 이슈: 굵게, 표 미지원

## 🆘 도움 요청

**수정이 필요한 부분을 발견하면:**
1. BUGS.md에 기록
2. 코드 수정
3. 테스트 실행
4. 결과 확인

**AI 도구 사용 팁:**
- 전체 프로젝트 폴더를 업로드
- "굵게 처리가 안 됩니다" 같이 구체적으로 질문
- 수정된 코드를 직접 테스트
## 🛠️ Troubleshooting
- 지속적인 트러블슈팅 기록은 `troubleshoot.md`에 정리합니다.
- 패키징/메타/헤더/섹션 구조 이슈 및 해결책, 한글에서의 동작 가이드를 수시로 업데이트합니다.

## 🔄 최근 업데이트(작업 요약)
- 스타일 정합성
  - header.xml의 itemCnt 동기화(실제 개수 기반)
  - 안정 ID 매핑: 제목(8/9), 본문(11/16), 설명*(15), 코드(44)
- 줄바꿈 보강
  - 소제목/본문(◦)/설명(-)/* 앞에 NBSP 빈 문단을 삽입(가시적 공백 유도)
  - 후속 계획: 빈 문단 대신 paraPr margin(prev)로 전 줄바꿈 표현
- 페이지 설정
  - 섹션 맨 앞 “컨트롤 전용 문단”에 secPr 배치(여백·그리드 안정 적용)
  - 방향 표시는 추가 검증 중(일부 환경에서 가로로 렌더링 보고됨)
- 패키징
  - OPF 패키징 정상 동작 확인, HEADREF는 한글 2020 호환성 검증 진행 중

실행 예시
```
# OPF 패키징 + 감사
python3 md_to_hwpx_v2.py test_input2.md output/_FINAL_FIX4.hwpx \
  --packaging opf --no-lineseg --audit --header-audit
```

알려진 남은 이슈(요약)
- 페이지 방향(세로 의도 → 가로 렌더링 사례)
- 전 줄바꿈 일부 환경에서 시각적 약함 → paraPr 여백 적용 예정
- HEADREF 일부 환경에서 “파일이 손상되었습니다” 경고

자세한 현황은 `handoff/01_current_issues.md`와 `handoff/02_troubleshooting_plan.md` 참고.

## 📦 Handoff 문서 안내
프로젝트 컨텍스트를 다른 LLM/개발자에게 빠르게 전달하기 위한 요약 자료입니다.

- `handoff/01_current_issues.md`
  - 현재 남아있는 이슈를 최신 상태로 정리(페이지 방향, 줄바꿈, HEADREF 등)
- `handoff/02_troubleshooting_plan.md`
  - 이번 컨텍스트에서의 해결 전략(페이지 방향 표기, 줄바꿈을 margin으로 처리, HEADREF 패키징 재구성)
  - 코드상 수정 포인트(함수/파일 위치)와 완료 기준 포함
- `handoff/03_transfer_rules_for_llm.md`
  - LLM이 바로 구현할 수 있도록 HWPX 패키징, header/section 작성 규칙, 파서 매핑 요령, Python 스니펫, 검증 루틴 수록

권장 사용 순서: 이 README → handoff/01 → handoff/02 → handoff/03.
