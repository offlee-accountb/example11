다음은 제공하신 두 문서를 바탕으로 HWPX 파일 형식의 구조와 Python을 사용한 데이터 추출 방법을 정리한 Markdown 파일입니다. 이 문서는 LLM이 HWPX의 구조를 이해하고 코드 수정을 돕는 데 초점을 맞춰 핵심적인 기술 내용 위주로 구성되었습니다.
HWPX 문서 형식 구조 및 Python 파싱 가이드
1. HWPX란?
HWPX는 XML 기반의 '개방형 워드프로세서 마크업 언어(Open Word-Processor Markup Language, OWPML)'이며, 국가 표준(KS X 6101)을 따르는 개방형 문서 형식입니다.
기존의 바이너리 기반 HWP 형식과 달리, HWPX는 ZIP 파일 구조를 가지며 내부에 XML 파일들로 데이터를 저장합니다. 이 구조 덕분에 데이터 추출 및 해석이 용이합니다.
2. HWPX 파일의 전체 구조
HWPX 파일은 ZIP 압축 파일이므로, 확장자를 .zip으로 변경하여 압축을 해제하면 내부 폴더와 파일들을 확인할 수 있습니다.
code
Code
[루트]
├── BinData/
│   ├── image1.png
│   └── ...
├── Contents/
│   ├── header.xml
│   ├── section0.xml
│   └── content.hpf
├── META-INF/
│   └── manifest.xml
├── Preview/
├── Scripts/
├── mimetype
├── settings.xml
└── version.xml
3. HWPX 구성 요소별 역할
3.1. mimetype
HWPX 포맷임을 식별하는 시그니처 파일입니다.
파일 내용은 항상 application/hwp+zip 입니다.
3.2. version.xml
OWPML 파일 형식 버전과 문서를 저장한 환경 정보(프로그램 버전 등)를 담고 있습니다.
code
Xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version"
    tagetApplication="WORDPROCESSOR" major="5" minor="1" micro="1"
    buildNumber="0" os="1" xmlVersion="1.5" application="Hancom Office Hangul"
    appVersion="12, 0, 0, 65535 WIN32LEWindows_10"/>
3.3. settings.xml
저장 시점의 커서 위치(CaretPosition)와 같은 외부 설정 정보를 포함합니다.
code
Xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ha:HWPApplicationSetting xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app">
    <ha:CaretPosition listIDRef="0" paraIDRef="12" pos="6"/>
</ha:HWPApplicationSetting>
CaretPosition 속성:
listIDRef: 리스트 아이디
paraIDRef: 문단 아이디
pos: 문단 내 글자 위치
3.4. BinData/ 폴더
문서에 포함된 이미지, OLE 개체 등 바이너리 데이터를 저장하는 폴더입니다.
본문에서는 이 폴더에 있는 파일을 참조하는 방식으로 바이너리 데이터를 표시합니다.
3.5. Contents/ 폴더
문서의 본문 내용과 서식 등 핵심 정보를 담고 있는 폴더입니다.
3.5.1. Contents/content.hpf
OPF(Open Packaging Format) 표준을 따르는 패키징 파일로, 문서의 전체 구조를 정의합니다.
metadata 영역: 작성자, 제목, 날짜 등 문서의 메타데이터를 저장합니다.
manifest 영역: HWPX 패키지를 구성하는 모든 파일(XML, 이미지 등)의 목록과 경로를 정의합니다.
spine 영역: manifest에 정의된 파일들을 참조하여 문서의 내용을 읽어야 할 순서를 지정합니다.
code
Xml
<opf:package xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app">
    <opf:metadata>
        <opf:title>Welcome to Hwp</opf:title>
        ...
    </opf:metadata>
    
    <opf:manifest>
        <opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>
        <opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>
        <opf:item id="image1" href="BinData/image1.PNG" media-type="image/png"/>
        ...
    </opf:manifest>
    
    <opf:spine>
        <opf:itemref idref="header" linear="yes"/>
        <opf:itemref idref="section0" linear="yes"/>
    </opf:spine>
</opf:package>
3.5.2. Contents/header.xml
문서 전반에 사용되는 **모든 서식 정보(Shape Table)**를 정의하는 매우 중요한 파일입니다.
글자 모양, 문단 모양, 글꼴, 테두리/배경 등의 스타일 정보를 ID와 함께 목록으로 정의해두면, section.xml에서 해당 ID를 참조하여 스타일을 적용합니다.
<hh:beginNum>: 페이지, 각주, 그림 등의 시작 번호를 정의합니다.
code
Xml
<hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>
<hh:refList>: 문서에서 사용될 각종 서식 데이터에 대한 매핑 정보를 담고 있습니다. 폰트나 정렬 문제를 해결하기 위해 가장 핵심적인 부분입니다.
fontfaces: 글꼴 정보 목록
borderFills: 테두리/배경 정보 목록
charProperties: 글자 모양 목록 (글꼴, 크기, 색상, 기울임 등)
tabProperties: 탭 정의 목록
paraProperties: 문단 모양 목록 (정렬, 여백, 줄 간격 등)
styles: 스타일 목록
code
Xml
<hh:head>
    <hh:refList>
        <hh:fontfaces itemCnt="7">
            <hh:fontface lang="HANGUL" fontCnt="2">
                <hh:font id="0" face="함초롬돋움" type="TTF" ... />
                <hh:font id="1" face="함초롬바탕" type="TTF" ... />
            </hh:fontface>
        </hh:fontfaces>
        
        <hh:charProperties itemCnt="7">...</hh:charProperties>
        
        <hh:paraProperties itemCnt="20">...</hh:paraProperties>
        
        <hh:styles itemCnt="22">...</hh:styles>
    </hh:refList>
    ...
</hh:head>
3.5.3. Contents/section[N].xml
문서의 구역(Section)별 실제 본문 내용을 담고 있는 파일입니다.
<hp:p> (문단) 단위로 내용이 구분되며, 각 문단은 서식 정보가 동일한 <hp:run> (글자 묶음)으로 구성됩니다. 실제 텍스트는 <hp:t> 태그 안에 들어갑니다.
paraPrIDRef 속성을 통해 header.xml에 정의된 문단 모양(paraProperties)을, charPrIDRef 속성을 통해 글자 모양(charProperties)을 참조하여 서식을 적용합니다.
code
Xml
<hs:sec ...>
    <hp:p id="p1" paraPrIDRef="3" styleIDRef="0">
        <hp:run charPrIDRef="11">
            <hp:t>이 텍스트는 11번 글자 모양을 따릅니다.</hp:t>
        </hp:run>
        <hp:run charPrIDRef="10">
            <hp:t>이 텍스트는 10번 글자 모양을 따릅니다.</hp:t>
        </hp:run>
    </hp:p>
</hs:sec>
4. Python을 이용한 HWPX 파싱
HWPX 파일은 ZIP 압축 형식이므로 Python의 내장 라이브러리인 zipfile과 xml.etree.ElementTree를 사용하여 별도 설치 없이 파싱할 수 있습니다.
4.1. 사용할 라이브러리
code
Python
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
4.2. 파싱 과정 예제 코드
1. ZIP 파일 읽기 및 XML 파일 접근
code
Python
# HWPX 파일을 ZIP으로 읽기
zipf = zipfile.ZipFile('example.hwpx', 'r')

# 파일 목록 확인
print(zipf.namelist())

# header.xml 파일 내용 읽기
# zipf.read()는 bytes를 반환하므로 XML 파서는 bytes를 처리할 수 있어야 함
header_xml_bytes = zipf.read('Contents/header.xml')

# XML 파싱
header_root = ET.fromstring(header_xml_bytes)
2. XML Namespace 추출
HWPX의 XML은 Namespace를 사용하므로, 요소에 접근하려면 Namespace를 지정해야 합니다.
code
Python
def extract_namespaces(xml_bytes):
    """XML 바이트 데이터에서 네임스페이스 맵을 추출합니다."""
    namespaces = {}
    for event, (prefix, uri) in ET.iterparse(BytesIO(xml_bytes), events=['start-ns']):
        namespaces[prefix] = uri
    return namespaces

# header.xml의 네임스페이스 추출
ns = extract_namespaces(header_xml_bytes)
# 예: ns = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph', ...}
3. header.xml에서 데이터 추출
find() 또는 findall() 메소드에 Namespace 맵을 전달하여 원하는 요소에 접근합니다.
code
Python
# ns 변수에는 이전에 추출한 namespace 맵이 들어있다고 가정
begin_num = header_root.find('hh:beginNum', ns)
if begin_num is not None:
    page_start_num = begin_num.get('page')
    footnote_start_num = begin_num.get('footnote')
    print(f"페이지 시작 번호: {page_start_num}")
code
Python
ref_list = header_root.find('hh:refList', ns)
if ref_list is not None:
    font_faces = ref_list.find('hh:fontfaces', ns)
    if font_faces is not None:
        # 언어별(HANGUL, LATIN 등)로 fontface가 나뉨
        for fontface in font_faces.findall('hh:fontface', ns):
            lang = fontface.get('lang')
            font_count = fontface.get('fontCnt')
            print(f"언어: {lang}, 글꼴 수: {font_count}")
            # 개별 폰트 정보 접근
            for font in fontface.findall('hh:font', ns):
                font_id = font.get('id')
                font_name = font.get('face')
                print(f"  ID: {font_id}, 글꼴 이름: {font_name}")
4. content.hpf에서 바이너리 파일 목록 추출
code
Python
content_hpf_xml_bytes = zipf.read('Contents/content.hpf')
content_hpf_root = ET.fromstring(content_hpf_xml_bytes)
ns_opf = {'opf': 'http://www.idpf.org/2007/opf'} # OPF 네임스페이스

manifest = content_hpf_root.find('opf:manifest', ns_opf)
binary_data_list = []
if manifest is not None:
    for item in manifest.findall('opf:item', ns_opf):
        href = item.get('href')
        if href and href.startswith('BinData/'):
            binary_data_list.append(href)

print(f"바이너리 데이터 목록: {binary_data_list}")
binary_data_count = len(binary_data_list)
