# 🐛 버그 및 이슈 목록

## 🔴 Critical (치명적)

### Bug #1: 표(Table) 미지원
**증상**: MD table이 텍스트로만 변환됨
```markdown
| 제목1 | 제목2 |
|-------|-------|
| 값1   | 값2   |
```
→ 3줄의 일반 텍스트로 변환

**영향도**: 높음 (원본 MD에 표가 많음)  
**우선순위**: P1  
**해결 방안**: 
1. 표 파싱 로직 추가
2. HWPX tbl 구조 생성
3. 셀 단위 처리

---

### Bug #2: 굵게 처리 미작동
**증상**: `**text**`를 감지하지만 실제 XML에 bold 속성 없음

**위치**: `md_to_hwpx_v2.py` 라인 120-130
```python
# 현재 코드
segments.append({
    'text': match.group(2),
    'char_id': base_char_id,
    'bold': True,  # 이 값을 사용하지 않음!
    ...
})
```

**영향도**: 높음  
**우선순위**: P1  
**해결 방안**:
```python
# HWPXGenerator.create_paragraph() 수정
if seg['bold']:
    xml += f'      <hp:run charPrIDRef="{seg["char_id"]}">\n'
    xml += f'        <hh:bold/>\n'  # 이 줄 추가!
    xml += f'        <hp:t>{escaped_text}</hp:t>\n'
```

---

## 🟡 Major (중요)

### Bug #3: 기울임(Italic) 미구현
**증상**: `*text*` 파싱은 하지만 XML에 반영 안 됨

**위치**: 동일 (Bug #2와 같은 원인)

**영향도**: 중간  
**우선순위**: P2  
**해결 방안**: Bug #2와 동일한 방식으로 `<hh:italic/>` 추가

---

### Bug #4: 네임스페이스 누락
**증상**: header.xml에서 일부 태그가 네임스페이스 없이 사용됨

**위치**: `_create_header_xml()` 메서드
```xml
<!-- 현재 -->
<hh:bold/>

<!-- 올바른 형태 (?) -->
<!-- HWPX 스펙에 따라 확인 필요 -->
```

**영향도**: 낮음 (한글에서 무시되는 것으로 보임)  
**우선순위**: P3

---

## 🟢 Minor (경미)

### Bug #5: 에러 핸들링 부족
**증상**: 파일 읽기 실패 시 에러 메시지 불친절

**예시**:
```python
with open(md_file_path, 'r', encoding='utf-8') as f:
    md_content = f.read()
# → FileNotFoundError 발생 시 그대로 출력
```

**해결 방안**:
```python
try:
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
except FileNotFoundError:
    print(f"❌ 파일을 찾을 수 없습니다: {md_file_path}")
    sys.exit(1)
```

---

### Bug #6: UTF-8 외 인코딩 미지원
**증상**: ANSI, EUC-KR 등 다른 인코딩 파일 읽기 실패

**해결 방안**:
```python
# chardet 라이브러리로 인코딩 자동 감지
import chardet
```

---

## 📋 Feature Requests (기능 요청)

### FR #1: 이미지 지원
**요청**: `![alt](image.png)` → HWPX 이미지 삽입

**필요 작업**:
1. 이미지 파일 읽기
2. Base64 인코딩
3. BinData 섹션 생성
4. 이미지 참조 추가

---

### FR #2: 링크 지원
**요청**: `[text](url)` → 하이퍼링크

**현재**: 텍스트만 남음

---

### FR #3: 코드 블록 지원
**요청**: 
```markdown
\`\`\`python
code here
\`\`\`
```
→ 코드 블록 서식

---

## 🧪 테스트 필요

### Test #1: 긴 문서
- [ ] 1000줄 이상 문서 테스트
- [ ] 메모리 사용량 확인
- [ ] 변환 속도 측정

### Test #2: 특수문자
- [ ] XML 예약문자: `<`, `>`, `&`, `'`, `"`
- [ ] 이모지: 😀 🎉
- [ ] 한자: 漢字

### Test #3: 에지 케이스
- [ ] 빈 파일
- [ ] 제목만 있는 파일
- [ ] 중첩된 서식: `**굵은 *기울임***`

---

## 🔧 수정 우선순위

1. **P1 (즉시)**: Bug #1, Bug #2
2. **P2 (중요)**: Bug #3, FR #1
3. **P3 (낮음)**: Bug #4, Bug #5, Bug #6

---

## 📝 변경 추적

### 2025-11-02
- 초기 버그 목록 작성
- 알려진 이슈 2개 (표, 굵게)

### 앞으로 할 일
- [ ] Bug #1 수정 (표 지원)
- [ ] Bug #2 수정 (굵게 처리)
- [ ] 테스트 케이스 작성
- [ ] 한글에서 실제 검증

---

**이 파일에 발견한 버그를 계속 추가해주세요!**
