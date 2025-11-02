#!/usr/bin/env python3
"""
MD to HWPX Converter v2.0
규칙북 기반 변환기
"""

import re
import json
import zipfile
import os
from datetime import datetime

class RulebookLoader:
    """규칙북 로더"""
    
    def __init__(self, styles_json_path):
        with open(styles_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.char_styles = {s['id']: s for s in data['char_styles']}
        self.para_styles = {s['id']: s for s in data['para_styles']}
        
        # MD 패턴 매핑 (규칙북 기반)
        self.patterns = {
            'h1': {'char_id': 15, 'para_id': 1},
            'h2': {'char_id': 17, 'para_id': 25},
            'h3': {'char_id': 23, 'para_id': 27},
            'paragraph': {'char_id': 18, 'para_id': 25},
            'ul': {'char_id': 18, 'para_id': 31},
            'ul_level2': {'char_id': 18, 'para_id': 33},
            'ol': {'char_id': 18, 'para_id': 37},
        }
    
    def get_style(self, element_type):
        """요소 타입에 맞는 스타일 반환"""
        return self.patterns.get(element_type, self.patterns['paragraph'])

class MDParser:
    """Markdown 파서"""
    
    @staticmethod
    def parse_line(line):
        """라인 타입 및 내용 파싱"""
        line = line.rstrip()
        
        # 빈 줄
        if not line.strip():
            return ('empty', '')
        
        # 제목
        if re.match(r'^### ', line):
            return ('h3', re.sub(r'^### ', '', line))
        elif re.match(r'^## ', line):
            return ('h2', re.sub(r'^## ', '', line))
        elif re.match(r'^# ', line):
            return ('h1', re.sub(r'^# ', '', line))
        
        # 리스트
        elif re.match(r'^    - ', line):
            return ('ul_level2', re.sub(r'^    - ', '', line))
        elif re.match(r'^  - ', line):
            return ('ul_level2', re.sub(r'^  - ', '', line))
        elif re.match(r'^- ', line):
            return ('ul', re.sub(r'^- ', '', line))
        elif re.match(r'^\d+\. ', line):
            return ('ol', re.sub(r'^\d+\. ', '', line))
        
        # 일반 단락
        else:
            return ('paragraph', line)
    
    @staticmethod
    def process_inline_formats(text, base_char_id):
        """인라인 서식 처리 - 여러 run으로 분리"""
        segments = []
        pos = 0
        
        # 패턴: **굵게**, *기울임*, `코드`
        pattern = r'(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)'
        
        for match in re.finditer(pattern, text):
            # 매치 전 일반 텍스트
            if match.start() > pos:
                segments.append({
                    'text': text[pos:match.start()],
                    'char_id': base_char_id,
                    'bold': False,
                    'italic': False,
                    'code': False
                })
            
            # 매치된 서식
            full_match = match.group(0)
            if full_match.startswith('**'):
                segments.append({
                    'text': match.group(2),
                    'char_id': base_char_id,
                    'bold': True,
                    'italic': False,
                    'code': False
                })
            elif full_match.startswith('`'):
                segments.append({
                    'text': match.group(4),
                    'char_id': 44,  # 코드 스타일
                    'bold': False,
                    'italic': False,
                    'code': True
                })
            elif full_match.startswith('*'):
                segments.append({
                    'text': match.group(3),
                    'char_id': base_char_id,
                    'bold': False,
                    'italic': True,
                    'code': False
                })
            
            pos = match.end()
        
        # 남은 텍스트
        if pos < len(text):
            segments.append({
                'text': text[pos:],
                'char_id': base_char_id,
                'bold': False,
                'italic': False,
                'code': False
            })
        
        # 세그먼트가 없으면 원본 텍스트 반환
        if not segments:
            segments.append({
                'text': text,
                'char_id': base_char_id,
                'bold': False,
                'italic': False,
                'code': False
            })
        
        return segments

class HWPXGenerator:
    """HWPX XML 생성기"""
    
    @staticmethod
    def escape_xml(text):
        """XML 특수문자 이스케이프"""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text
    
    @staticmethod
    def create_paragraph(element_type, text, rulebook, parser):
        """단락 XML 생성"""
        style = rulebook.get_style(element_type)
        char_id = style['char_id']
        para_id = style['para_id']
        
        # 인라인 서식 처리
        segments = parser.process_inline_formats(text, char_id)
        
        # XML 생성
        xml = f'    <hp:p paraPrIDRef="{para_id}">\n'
        
        for seg in segments:
            # 빈 텍스트 스킵
            if not seg['text']:
                continue
            
            # run 시작 - 인라인 서식 매핑
            run_char_id = seg["char_id"]
            if not seg.get('code'):
                # 굵게 처리: 미리 정의된 bold 스타일(23) 사용
                if seg.get('bold'):
                    run_char_id = 23
                # 기울임 처리: italic 전용 스타일(45) 사용
                elif seg.get('italic'):
                    run_char_id = 45

            xml += f'      <hp:run charPrIDRef="{run_char_id}">\n'
            
            # 텍스트
            escaped_text = HWPXGenerator.escape_xml(seg['text'])
            xml += f'        <hp:t>{escaped_text}</hp:t>\n'
            
            # run 종료
            xml += f'      </hp:run>\n'
        
        xml += '    </hp:p>\n'
        
        return xml
    
    @staticmethod
    def create_section(paragraphs):
        """섹션 XML 생성"""
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        xml += '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
        xml += 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">\n'
        
        for para_xml in paragraphs:
            xml += para_xml
        
        xml += '</hs:sec>\n'
        
        return xml

class MDtoHWPXConverter:
    """메인 변환기"""
    
    def __init__(self, styles_json_path):
        self.rulebook = RulebookLoader(styles_json_path)
        self.parser = MDParser()
        self.generator = HWPXGenerator()
    
    def convert(self, md_content):
        """MD 내용을 HWPX XML로 변환"""
        lines = md_content.split('\n')
        paragraphs = []
        
        for line in lines:
            element_type, text = self.parser.parse_line(line)
            
            # 빈 줄 스킵
            if element_type == 'empty':
                continue
            
            # 단락 생성
            para_xml = self.generator.create_paragraph(
                element_type, text, self.rulebook, self.parser
            )
            paragraphs.append(para_xml)
        
        return paragraphs
    
    def create_hwpx(self, md_file_path, output_path):
        """MD 파일을 읽어 HWPX 생성"""
        # MD 파일 읽기
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
        except FileNotFoundError:
            print(f"❌ 파일을 찾을 수 없습니다: {md_file_path}")
            raise
        
        # 변환
        paragraphs = self.convert(md_content)
        section_xml = self.generator.create_section(paragraphs)
        
        # HWPX 파일 생성
        with zipfile.ZipFile(output_path, 'w') as hwpx:
            # mimetype - 반드시 무압축/첫 항목
            info = zipfile.ZipInfo('mimetype')
            info.compress_type = zipfile.ZIP_STORED
            hwpx.writestr(info, 'application/hwp+zip')
            
            # version.xml
            hwpx.writestr('version.xml', 
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                '<version>5.0.0.0</version>'
            )
            
            # META-INF/container.xml
            hwpx.writestr('META-INF/container.xml',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
                '<ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container" xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf">'
                '<ocf:rootfiles>'
                '<ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/>'
                '</ocf:rootfiles>'
                '</ocf:container>'
            )

            # META-INF/manifest.xml (샘플과 동일하게 최소 odf 루트)
            hwpx.writestr('META-INF/manifest.xml',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
                '<odf:manifest xmlns:odf="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>'
            )

            # META-INF/container.rdf (헤더/섹션 파트 매핑)
            hwpx.writestr('META-INF/container.rdf',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
                '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
                '<rdf:Description rdf:about="">'
                '<ns0:hasPart xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" rdf:resource="Contents/header.xml"/>'
                '</rdf:Description>'
                '<rdf:Description rdf:about="Contents/header.xml">'
                '<rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#HeaderFile"/>'
                '</rdf:Description>'
                '<rdf:Description rdf:about="">'
                '<ns0:hasPart xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" rdf:resource="Contents/section0.xml"/>'
                '</rdf:Description>'
                '<rdf:Description rdf:about="Contents/section0.xml">'
                '<rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#SectionFile"/>'
                '</rdf:Description>'
                '<rdf:Description rdf:about="">'
                '<rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#Document"/>'
                '</rdf:Description>'
                '</rdf:RDF>'
            )
            
            # Contents/content.hpf - OPF 패키지로 구성 (manifest/spine)
            hwpx.writestr('Contents/content.hpf',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
                '<opf:package '
                'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
                'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
                'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
                'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
                'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/" '
                'xmlns:opf="http://www.idpf.org/2007/opf/" '
                'version="" unique-identifier="" id="">'
                '<opf:metadata>'
                '<opf:title/>'
                '<opf:language>ko</opf:language>'
                '</opf:metadata>'
                '<opf:manifest>'
                '<opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>'
                '<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>'
                '<opf:item id="settings" href="settings.xml" media-type="application/xml"/>'
                '</opf:manifest>'
                '<opf:spine>'
                '<opf:itemref idref="header" linear="yes"/>'
                '<opf:itemref idref="section0"/>'
                '</opf:spine>'
                '</opf:package>'
            )

            # settings.xml (최소 애플리케이션 설정)
            hwpx.writestr('settings.xml',
                '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
                '<ha:HWPApplicationSetting '
                'xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
                'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0">'
                '<ha:CaretPosition listIDRef="0" paraIDRef="0" pos="0"/>'
                '<config:config-item-set name="PrintInfo">'
                '<config:config-item name="PrintAutoFootNote" type="boolean">false</config:config-item>'
                '<config:config-item name="PrintAutoHeadNote" type="boolean">false</config:config-item>'
                '<config:config-item name="ZoomX" type="short">100</config:config-item>'
                '<config:config-item name="ZoomY" type="short">100</config:config-item>'
                '</config:config-item-set>'
                '</ha:HWPApplicationSetting>'
            )
            
            # Contents/header.xml (기본 스타일)
            header_xml = self._create_header_xml()
            hwpx.writestr('Contents/header.xml', header_xml)
            
            # Contents/section0.xml (본문)
            hwpx.writestr('Contents/section0.xml', section_xml)
        
        print(f"✅ HWPX 생성 완료: {output_path}")
        print(f"   단락 수: {len(paragraphs)}개")
        return output_path
    
    def _create_header_xml(self):
        """간단한 header.xml 생성"""
        return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" 
         xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" 
         xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"
         xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" version="1.4" secCnt="1">
  <hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>
  <hh:refList>
    <hh:fontfaces itemCnt="1">
      <hh:fontface lang="HANGUL" fontCnt="1">
        <hh:font id="0" face="맑은 고딕" type="TTF" isEmbedded="0">
          <hh:typeInfo familyType="FCAT_GOTHIC" weight="5"/>
        </hh:font>
      </hh:fontface>
    </hh:fontfaces>
    
    <hh:charProperties itemCnt="6">
      <hh:charPr id="15" height="1500" textColor="#000000">
        <hh:fontRef hangul="0" latin="0"/>
        <hh:bold/>
        <hh:underline type="NONE"/>
      </hh:charPr>
      <hh:charPr id="17" height="1200" textColor="#000000">
        <hh:fontRef hangul="0" latin="0"/>
        <hh:bold/>
        <hh:underline type="NONE"/>
      </hh:charPr>
      <hh:charPr id="18" height="1200" textColor="#000000">
        <hh:fontRef hangul="0" latin="0"/>
        <hh:underline type="NONE"/>
      </hh:charPr>
      <hh:charPr id="23" height="1200" textColor="#000000">
        <hh:fontRef hangul="0" latin="0"/>
        <hh:bold/>
        <hh:underline type="NONE"/>
      </hh:charPr>
      <hh:charPr id="45" height="1200" textColor="#000000">
        <hh:fontRef hangul="0" latin="0"/>
        <hh:italic/>
        <hh:underline type="NONE"/>
      </hh:charPr>
      <hh:charPr id="44" height="800" textColor="#000000">
        <hh:fontRef hangul="0" latin="0"/>
        <hh:underline type="NONE"/>
      </hh:charPr>
    </hh:charProperties>
    
    <hh:paraProperties itemCnt="6">
      <hh:paraPr id="1">
        <hh:align horizontal="CENTER"/>
        <hh:lineSpacing type="PERCENT" value="160"/>
      </hh:paraPr>
      <hh:paraPr id="25">
        <hh:align horizontal="JUSTIFY"/>
        <hh:lineSpacing type="PERCENT" value="145"/>
      </hh:paraPr>
      <hh:paraPr id="27">
        <hh:align horizontal="CENTER"/>
        <hh:lineSpacing type="PERCENT" value="130"/>
      </hh:paraPr>
      <hh:paraPr id="31">
        <hh:align horizontal="JUSTIFY"/>
        <hh:margin>
          <hc:intent value="-3024" unit="HWPUNIT"/>
        </hh:margin>
        <hh:lineSpacing type="PERCENT" value="145"/>
      </hh:paraPr>
      <hh:paraPr id="33">
        <hh:align horizontal="JUSTIFY"/>
        <hh:margin>
          <hc:intent value="-2777" unit="HWPUNIT"/>
        </hh:margin>
        <hh:lineSpacing type="PERCENT" value="145"/>
      </hh:paraPr>
      <hh:paraPr id="37">
        <hh:align horizontal="JUSTIFY"/>
        <hh:margin>
          <hc:intent value="-3024" unit="HWPUNIT"/>
        </hh:margin>
        <hh:lineSpacing type="PERCENT" value="155"/>
      </hh:paraPr>
    </hh:paraProperties>
  </hh:refList>
</hh:head>'''

# 메인 실행
if __name__ == "__main__":
    import sys
    
    # 스타일 JSON 경로 (스크립트 기준 상대경로)
    styles_json = os.path.join(os.path.dirname(__file__), 'extracted_styles_v2.json')
    
    # 변환기 초기화
    converter = MDtoHWPXConverter(styles_json)
    
    # 테스트 MD 파일이 주어진 경우
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else 'output.hwpx'
        converter.create_hwpx(md_file, output_file)
    else:
        print("사용법: python md_to_hwpx_v2.py <input.md> [output.hwpx]")
        print("\n테스트 모드로 실행합니다...")
        
        # 테스트 MD 생성
        test_md = """# 프로젝트 보고서

이것은 **중요한** 내용을 담은 보고서입니다.

## 주요 내용

다음은 *강조된 텍스트*와 `코드`를 포함한 본문입니다.

### 세부 항목

- 첫 번째 항목
- 두 번째 항목
- 세 번째 항목

1. 번호 항목 1
2. 번호 항목 2
3. 번호 항목 3

일반 단락도 포함되어 있습니다.
"""
        
        # 임시 MD 파일 생성
        with open('/home/claude/test.md', 'w', encoding='utf-8') as f:
            f.write(test_md)
        
        # 변환 실행
        output_path = '/mnt/user-data/outputs/test_output_v2.hwpx'
        converter.create_hwpx('/home/claude/test.md', output_path)
        
        print("\n🎉 변환 완료!")
        print(f"📄 출력 파일: {output_path}")
        print("\n한글(HWP)로 열어서 확인하세요!")
