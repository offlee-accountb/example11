# 현재 코드 vs pyhwpx 비교 분석

## 📊 개요

현재 우리는 **XML 직접 생성 방식**을 사용하고 있으며, pyhwpx는 **한/글 COM 자동화 방식**입니다.
리눅스 서버 환경에서는 pyhwpx를 사용할 수 없으므로, pyhwpx 핸드북을 "정답 확인용"으로 활용하여 현재 XML 생성 로직을 검증하고 개선합니다.

---

## ✅ 현재 코드의 강점

### 1. **CharShape (문자 스타일) 매핑**

| pyhwpx 속성 | 현재 XML 속성 | 구현 상태 | 위치 |
|------------|--------------|---------|-----|
| `Height` | `height` | ✅ 완료 | md_to_hwpx_v2.py:661 |
| `Bold` | `<hh:bold/>` | ✅ 완료 | md_to_hwpx_v2.py:664 |
| `Italic` | `<hh:italic/>` | ✅ 완료 | md_to_hwpx_v2.py:666 |
| `FaceName` | `<hh:fontRef hangul/latin>` | ✅ 완료 | md_to_hwpx_v2.py:662 |
| `TextColor` | `textColor` | ✅ 완료 | md_to_hwpx_v2.py:661 |
| `Spacing` (자간) | - | ❌ 미구현 | - |
| `Ratio` (장평) | - | ❌ 미구현 | - |

**결론:** 기본적인 문자 서식은 정확하게 구현되어 있으나, 고급 타이포그래피 속성(자간, 장평)은 없음.

---

### 2. **ParaShape (문단 스타일) 매핑**

| pyhwpx 속성 | 현재 XML 속성 | 구현 상태 | 위치 |
|------------|--------------|---------|-----|
| `AlignType` | `<hh:align horizontal>` | ✅ 완료 | md_to_hwpx_v2.py:714 |
| `LineSpacing` | `<hh:lineSpacing type/value>` | ✅ 완료 | md_to_hwpx_v2.py:715 |
| `PrevSpacing` (문단 위 여백) | - | ❌ 미구현 | - |
| `margin/intent` (들여쓰기) | - | ⚠️ 일부만 | - |

**결론:** 정렬과 줄 간격은 완벽하지만, 문단 간격과 들여쓰기는 개선 여지 있음.

---

### 3. **멀티 폰트 지원**

**현재 구현 (md_to_hwpx_v2.py:631-655):**
```xml
<hh:fontface lang="HANGUL" fontCnt="3">
  <hh:font id="0" face="HY헤드라인M" type="TTF"/>
  <hh:font id="1" face="휴먼명조" type="TTF"/>
  <hh:font id="2" face="맑은 고딕" type="TTF"/>
</hh:fontface>
<hh:fontface lang="LATIN" fontCnt="3">
  ... (동일)
</hh:fontface>
```

**pyhwpx 방식:**
```python
hwp.set_font(FaceName="HY헤드라인M")
hwp.set_font(FaceName="휴먼명조")
```

**✅ 결론:** 멀티 폰트 지원 완벽. HANGUL + LATIN 언어별 폰트 정의도 올바름.

---

### 4. **인라인 포맷팅 (Run 단위 서식)**

**pyhwpx 방식 (핸드북 예제):**
```python
hwp.insert_text("pyhwpx를 사용하면 문서 자동화가 쉬워집니다.")
hwp.MoveDocBegin()
if hwp.find("pyhwpx"):  # 텍스트 선택
    hwp.set_font(Bold=True, TextColor="Blue")  # 서식 변경
```

**현재 방식 (md_to_hwpx_v2.py:236-295):**
```python
def process_inline_formats(text, base_char_id):
    # 정규표현식으로 **굵게**, *기울임*, `코드` 파싱
    pattern = r'(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)'

    for match in re.finditer(pattern, text):
        # segments로 분리하여 각각 charPr 적용
        segments.append({
            'text': match.group(2),
            'char_id': base_char_id,
            'bold': True,
            ...
        })
```

**비교:**
| 항목 | pyhwpx | 현재 XML 방식 |
|------|--------|-------------|
| 방식 | 텍스트 검색 → 선택 → 서식 변경 | 마크다운 파싱 → segment 분리 → XML 생성 |
| 장점 | 한/글 UI와 동일한 방식 | 정확한 파싱, 빠른 처리 |
| 단점 | 느림, 한/글 의존 | 정규표현식 복잡도 |

**✅ 결론:** 현재 방식이 마크다운 변환에는 더 적합. pyhwpx는 참고용.

---

## ⚠️ 개선 가능한 부분

### 1. **자간(Spacing) 지원 추가**

**pyhwpx 예제:**
```python
cs = hwp.CharShape
cs.SetItem("Spacing", -5)  # 자간 좁게
hwp.CharShape = cs
```

**제안:**
```xml
<hh:charPr id="401" height="1500" textColor="#000000">
  <hh:fontRef hangul="0" latin="0"/>
  <hh:spacing value="-5"/>  <!-- 추가 -->
</hh:charPr>
```

**우선순위:** 낮음 (style_textbook.md에 요구사항 없음)

---

### 2. **장평(Ratio) 지원 추가**

**pyhwpx 예제:**
```python
cs.SetItem("Ratio", 95)  # 장평 95%
```

**제안:**
```xml
<hh:charPr id="401" ...>
  <hh:ratio value="95"/>  <!-- 추가 -->
</hh:charPr>
```

**우선순위:** 낮음

---

### 3. **문단 간격(PrevSpacing) 지원**

**pyhwpx 예제:**
```python
ps = hwp.ParaShape
ps.SetItem("PrevSpacing", 1000)  # 문단 위 여백
```

**제안:**
```xml
<hh:paraPr id="301">
  <hh:align horizontal="CENTER"/>
  <hh:lineSpacing type="PERCENT" value="130"/>
  <hh:spacing prev="1000"/>  <!-- 추가 -->
</hh:paraPr>
```

**우선순위:** 중간 (정부 문서에서 자주 사용)

---

### 4. **리스트 처리 개선**

**현재 상태:**
- 리스트용 paraPr는 있으나 실제 불릿/번호는 텍스트로 처리됨

**pyhwpx 핸드북:**
> "프로그래밍 방식으로 글머리표(불릿)나 문단 번호 스타일을 직접 생성하는 방법에 대한 명시적인 설명이 없음. 매크로 녹화 필요."

**제안:**
- 실제 한/글 문서에서 불릿 리스트 생성 후 .hwpx 언패킹
- XML 구조 분석하여 `<hh:numbering>` 등의 요소 확인
- 현재 코드에 반영

**우선순위:** 높음 (많은 문서에서 사용)

---

## 🎯 다음 단계

### **Phase 1: 검증 (현재)**
- [x] pyhwpx 핸드북 분석
- [x] 현재 코드와 비교
- [ ] 테스트 케이스 작성 (동일 내용을 XML/pyhwpx로 생성 후 비교)

### **Phase 2: 기본 개선**
- [ ] 문단 간격(PrevSpacing) 추가
- [ ] 들여쓰기(margin/intent) 개선
- [ ] 인라인 포맷 정규표현식 강화 (중첩 처리)

### **Phase 3: 고급 기능**
- [ ] 리스트 불릿/번호 XML 구조 분석
- [ ] 자간/장평 지원 (필요시)
- [ ] 테이블 지원 (현재 미구현)

---

## 📌 결론

**현재 XML 생성 방식은 pyhwpx 대비:**
- ✅ 리눅스 서버 지원 (필수)
- ✅ 기본 스타일 매핑 정확도 높음
- ✅ 멀티 폰트 지원 완벽
- ✅ 인라인 포맷 로직 마크다운에 최적화
- ⚠️ 문단 간격, 리스트 처리 개선 필요

**pyhwpx 핸드북 활용 방법:**
1. 속성 이름 매핑 확인 (Height → height, Bold → `<hh:bold/>`)
2. 테스트: 같은 내용을 두 방식으로 생성 → XML 비교
3. 누락된 기능 발견 시 XML 구조 분석 후 추가

**권장 사항:**
- 현재 XML 방식 유지
- pyhwpx는 "정답 체크용"으로만 활용
- 리눅스 서버 배포 시 의존성 문제 없음
