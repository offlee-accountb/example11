# HWPX 파일 포맷 간단 가이드

## HWPX란?
- 한글의 표준 포맷 (국가 표준 KS X 6101, OWPML 기반)
- **ZIP 압축된 XML 파일들의 집합**
- 바이너리 HWP와 달리 XML 기반이라 데이터 추출이 쉬움

## 파일 구조
```
mydocument.hwpx (실제로는 ZIP 파일)
├── mimetype                    # 파일 타입 지정
├── version.xml                 # OWPML 버전 정보
├── settings.xml                # 편집기 설정 (커서 위치 등)
├── BinData/                    # 이미지, 바이너리 파일
├── Contents/
│   ├── content.hpf             # 파일 순서 정의 (OPF 표준)
│   ├── header.xml              # 스타일/속성 정의 (중요!)
│   └── section0.xml            # 실제 본문 내용
└── META-INF/                   # 암호화 정보
```

## 핵심 개념: 스타일 "정의" → "참조" 구조

### 1단계: header.xml에서 정의
스타일을 **유일한 ID와 함께 정의**합니다.

```xml
<hh:refList>
  <!-- 글꼴 정의 -->
  <hh:fontfaces>
    <hh:fontface lang="HANGUL">
      <hh:font id="0" face="함초롬돋움"/>
      <hh:font id="1" face="함초롬바탕"/>
    </hh:fontface>
  </hh:fontfaces>
  
  <!-- 글자 모양 정의 (크기, 색, 진하기 등) -->
  <hh:charProperties id="10">
    <!-- 12pt, 함초롬바탕, 검은색 등 -->
  </hh:charProperties>
  
  <!-- 문단 모양 정의 (정렬, 여백, 줄간격 등) -->
  <hh:paraProperties id="3">
    <!-- 가운데 정렬 등 -->
  </hh:paraProperties>
</hh:refList>
```

### 2단계: section.xml에서 참조
본문에서 정의된 ID를 **참조**합니다.

```xml
<hs:sec>
  <hp:p id="2147483648" paraPrIDRef="3">
    <!-- paraPrIDRef="3" → header.xml의 id="3"인 문단 스타일 사용 -->
    
    <hp:run charPrIDRef="10">
      <!-- charPrIDRef="10" → header.xml의 id="10"인 글자 스타일 사용 -->
      <hp:t>회색조</hp:t>
    </hp:run>
    
  </hp:p>
</hs:sec>
```

## Python 파싱 기본

### ZIP 파일 열기
```python
import zipfile
import xml.etree.ElementTree as ET

zipf = zipfile.ZipFile('mydocument.hwpx', 'r')
```

### XML 파싱 (네임스페이스 주의)
```python
def extract_namespaces(xml_bytes):
    namespaces = {}
    for event, (prefix, uri) in ET.iterparse(xml_bytes, events=('start-ns',)):
        namespaces[prefix] = uri
    return namespaces

ns = extract_namespaces(zipf.read('Contents/header.xml'))
# 예: {'hh': 'http://www.hancom.co.kr/hwpml/2011/head', ...}

header_root = ET.parse(zipf.open('Contents/header.xml')).getroot()
```

### 글꼴 정보 추출
```python
ref_list = header_root.find('hh:refList', ns)
font_faces = ref_list.find('hh:fontfaces', ns)

for fontface in font_faces.findall('hh:fontface', ns):
    if fontface.get('lang') == 'HANGUL':
        for font in fontface.findall('hh:font', ns):
            font_id = font.get('id')
            font_name = font.get('face')
            print(f"ID {font_id}: {font_name}")
```

## MD → HWPX 변환 시 필수 체크리스트

1. **header.xml에 스타일 정의**
   - 필요한 글꼴들을 fontfaces에 등록하고 ID 부여
   - 각 글자 스타일을 charProperties로 정의하고 ID 부여
   - 각 문단 스타일을 paraProperties로 정의하고 ID 부여

2. **section.xml에서 ID 참조**
   - `<hp:p paraPrIDRef="X">` 형태로 문단 스타일 지정
   - `<hp:run charPrIDRef="Y">` 형태로 글자 스타일 지정

3. **ID 일관성 확인**
   - 참조하는 ID가 header.xml에 실제로 정의되어 있는지 확인
   - ID가 없거나 잘못되면 스타일이 적용 안 됨

## 핵심 요약

HWPX는 **XML 기반 ZIP 파일**이고, 스타일은 **header.xml에서 정의하고 section.xml에서 ID로 참조**하는 구조입니다. 이 ID 매핑 관계가 정확해야만 스타일이 제대로 적용됩니다.
