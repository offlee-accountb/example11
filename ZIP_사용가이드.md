# 📦 MD to HWPX 프로젝트 - 압축 파일 가이드

## ✅ 준비 완료!

**다운로드**: [md-to-hwpx-project.zip](computer:///mnt/user-data/outputs/md-to-hwpx-project.zip) (12KB)

---

## 📁 압축 파일 내용

```
md-to-hwpx-project/
├── md_to_hwpx_v2.py              # 변환기 코드
├── extracted_styles_v2.json      # 스타일 설정
├── test_input.md                 # 실제 테스트 파일 (62단락)
├── test_simple.md                # 간단 테스트 파일
├── README.md                     # 프로젝트 설명
└── BUGS.md                       # 알려진 버그 목록
```

---

## 🚀 Claude Code에서 사용하는 방법

### 1단계: 압축 해제
```bash
# 원하는 위치에 압축 해제
unzip md-to-hwpx-project.zip
```

### 2단계: Claude Code 실행
```bash
# VSCode에서
code md-to-hwpx-project

# 또는 터미널에서 직접
cd md-to-hwpx-project
```

### 3단계: Claude Code에 요청
```
이 프로젝트의 버그를 찾아서 수정해줘.
특히:
1. 굵게 처리가 안 되는 문제 (BUGS.md #2)
2. 표가 텍스트로만 변환되는 문제 (BUGS.md #1)
```

### 4단계: 테스트
```bash
python md_to_hwpx_v2.py test_simple.md output.hwpx
```

---

## 🤖 GPT Codex에서 사용하는 방법

### 1단계: 프로젝트 업로드
- ZIP 파일 전체를 업로드하거나
- 압축 해제 후 폴더 전체 업로드

### 2단계: 문제 설명
```
이 Python 프로젝트는 Markdown을 HWPX로 변환하는데,
**굵게** 처리가 제대로 작동하지 않습니다.

BUGS.md 파일을 보고 수정해주세요.
```

### 3단계: 수정 요청
```
1. MDParser.process_inline_formats() 함수 분석
2. HWPXGenerator.create_paragraph() 수정
3. bold 플래그를 실제 XML에 반영
```

---

## 🐛 주요 버그 요약

### Bug #1: 표 미지원 ⚠️
**증상**: `| 표 |` 형식이 텍스트로만 변환
**우선순위**: 높음
**파일**: `md_to_hwpx_v2.py` 라인 60-80

### Bug #2: 굵게 미작동 ⚠️
**증상**: `**text**` 파싱은 하지만 XML에 반영 안 됨
**우선순위**: 높음  
**파일**: `md_to_hwpx_v2.py` 라인 120-180

### Bug #3: 기울임 미구현
**증상**: `*text*` 동일한 문제
**우선순위**: 중간

---

## 💡 수정 힌트

### 힌트 1: 굵게 처리
```python
# 현재 (작동 안 함)
xml += f'      <hp:run charPrIDRef="{seg["char_id"]}">\n'
xml += f'        <hp:t>{escaped_text}</hp:t>\n'

# 수정안 1: bold 태그 추가
if seg['bold']:
    xml += f'      <hp:run charPrIDRef="{seg["char_id"]}">\n'
    xml += f'        <hh:bold/>\n'  # 이 줄 추가!
    xml += f'        <hp:t>{escaped_text}</hp:t>\n'

# 수정안 2: 굵은 스타일 ID 사용
if seg['bold']:
    bold_char_id = 23  # extracted_styles_v2.json에서 bold 스타일
    xml += f'      <hp:run charPrIDRef="{bold_char_id}">\n'
```

### 힌트 2: 표 파싱
```python
# MDParser.parse_line() 에 추가
if re.match(r'^\|(.+)\|$', line):
    # 표 행 감지
    cells = [cell.strip() for cell in line.split('|')[1:-1]]
    return ('table_row', cells)

if re.match(r'^\|[-:]+\|$', line):
    # 표 구분선 감지
    return ('table_separator', '')
```

---

## 🧪 테스트 방법

### 기본 테스트
```bash
python md_to_hwpx_v2.py test_simple.md output.hwpx
```

### 실제 파일 테스트
```bash
python md_to_hwpx_v2.py test_input.md output_real.hwpx
```

### 결과 확인
- 생성된 `.hwpx` 파일을 한글(HWP)로 열기
- 굵게, 표가 제대로 나오는지 확인

---

## 📋 AI 도구 질문 예시

### Claude Code에게
```
이 프로젝트의 md_to_hwpx_v2.py 파일에서:
1. MDParser.process_inline_formats() 함수를 분석해줘
2. bold 플래그가 왜 사용되지 않는지 찾아줘
3. HWPXGenerator.create_paragraph()를 수정해서 bold 태그를 추가해줘
```

### GPT Codex에게
```
Python으로 Markdown을 HWPX로 변환하는 프로젝트입니다.
**굵게** 처리가 작동하지 않는 버그가 있어요.

BUGS.md의 Bug #2를 참고해서:
1. 원인 분석
2. 수정 코드 제안
3. 테스트 방법 알려줘
```

---

## 🎯 성공 체크리스트

수정 후 다음을 확인하세요:

- [ ] 테스트 실행 (`python md_to_hwpx_v2.py test_simple.md output.hwpx`)
- [ ] 에러 없이 완료되었나요?
- [ ] HWPX 파일 생성되었나요?
- [ ] 한글에서 파일이 열리나요?
- [ ] **굵은 텍스트**가 실제로 굵게 보이나요?
- [ ] 표가 표 형태로 보이나요? (아직이면 정상)

---

## 📞 추가 도움

**수정 후에도 문제가 있다면:**
1. 에러 메시지 전체를 복사
2. 수정한 코드 부분을 명시
3. AI 도구에 다시 질문

**수정 성공하면:**
1. BUGS.md를 업데이트
2. 테스트 케이스 추가
3. README.md에 변경사항 기록

---

## 🎉 화이팅!

이 프로젝트는 프로토타입이라 버그가 있는 게 정상입니다.
AI 도구로 차근차근 수정하면서 배우는 좋은 기회예요!

**다운로드**: [md-to-hwpx-project.zip](computer:///mnt/user-data/outputs/md-to-hwpx-project.zip)

---

**작성일**: 2025-11-02  
**버전**: Debug Ready v1.0  
**목적**: AI 도구 디버깅용
