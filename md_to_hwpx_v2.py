#!/usr/bin/env python3
"""
MD to HWPX Converter v2.0
규칙북 기반 변환기
"""

import re
import json
import zipfile
import os
import argparse
from datetime import datetime

class StyleTextbookParser:
    """style_textbook.md 파서 - 한글 스타일 규칙 읽기"""

    @staticmethod
    def parse(textbook_path):
        """
        style_textbook.md를 파싱하여 스타일 규칙 딕셔너리 반환
        Returns: {
            'main_title': {'font': 'HY헤드라인M', 'size': 15, 'bold': True, 'align': 'CENTER', 'line_spacing': 130},
            ...
        }
        """
        if not os.path.exists(textbook_path):
            return None

        styles = {}

        with open(textbook_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. <주제목> 파싱
        if '1. <주제목>' in content:
            styles['main_title'] = {
                'font': 'HY헤드라인M',
                'size': 15,
                'bold': True,
                'align': 'CENTER',
                'line_spacing': 130
            }

        # 2. <소제목> (□)
        if '2. <소제목>' in content:
            styles['sub_title'] = {
                'font': 'HY헤드라인M',
                'size': 15,
                'bold': False,
                'align': 'LEFT',
                'line_spacing': 160
            }

        # 3. <본문> (◦)
        if '3. <본문>' in content:
            styles['body_bullet'] = {
                'font': '휴먼명조',
                'size': 15,
                'bold': False,
                'align': 'LEFT',
                'line_spacing': 160
            }

        # 4. <설명> (-)
        if '4. <설명>' in content:
            styles['description_dash'] = {
                'font': '휴먼명조',
                'size': 15,
                'bold': False,
                'align': 'LEFT',
                'line_spacing': 160
            }

        # 5. <설명> (*)
        if '5. <설명>' in content:
            styles['description_star'] = {
                'font': '맑은 고딕',
                'size': 12,
                'bold': False,
                'align': 'LEFT',
                'line_spacing': 160
            }

        # 6. <강조>
        if '6. <강조>' in content:
            styles['emphasis'] = {
                'font': '휴먼명조',
                'size': 15,
                'bold': True,
                'align': 'CENTER',
                'line_spacing': 130
            }

        return styles


class RulebookLoader:
    """규칙북 로더"""

    def __init__(self, styles_json_path, textbook_path=None):
        with open(styles_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.char_styles = {s['id']: s for s in data['char_styles']}
        self.para_styles = {s['id']: s for s in data['para_styles']}

        # style_textbook.md 로딩
        self.textbook_styles = None
        if textbook_path and os.path.exists(textbook_path):
            self.textbook_styles = StyleTextbookParser.parse(textbook_path)
            if self.textbook_styles:
                print(f"[OK] style_textbook.md 로딩 완료: {len(self.textbook_styles)}개 스타일")

        # 기본 스타일 ID (신규 합성 스타일)
        self.BOLD_CHAR_ID = 404
        self.ITALIC_CHAR_ID = 406
        self.CODE_CHAR_ID = 44

        # MD 패턴 매핑 (스타일 텍스트북 기반)
        self.patterns = {
            'main_title': {'char_id': 401, 'para_id': 301, 'bold_char_id': 404, 'italic_char_id': 406},
            'sub_title': {'char_id': 402, 'para_id': 302, 'bold_char_id': 404, 'italic_char_id': 406},
            'body_bullet': {'char_id': 403, 'para_id': 303, 'bold_char_id': 404, 'italic_char_id': 406},
            'description_dash': {'char_id': 403, 'para_id': 304, 'bold_char_id': 404, 'italic_char_id': 406},
            'description_star': {'char_id': 405, 'para_id': 305, 'bold_char_id': 404, 'italic_char_id': 406},
            'emphasis': {'char_id': 404, 'para_id': 306, 'bold_char_id': 404, 'italic_char_id': 406},
            # 기본 문단 및 기타 요소
            'h1': {'char_id': 401, 'para_id': 301, 'bold_char_id': 404, 'italic_char_id': 406},
            'h2': {'char_id': 402, 'para_id': 302, 'bold_char_id': 404, 'italic_char_id': 406},
            'h3': {'char_id': 402, 'para_id': 302, 'bold_char_id': 404, 'italic_char_id': 406},
            'paragraph': {'char_id': 403, 'para_id': 303, 'bold_char_id': 404, 'italic_char_id': 406},
            'ul': {'char_id': 403, 'para_id': 303, 'bold_char_id': 404, 'italic_char_id': 406},
            'ul_level2': {'char_id': 405, 'para_id': 305, 'bold_char_id': 404, 'italic_char_id': 406},
            'ol': {'char_id': 403, 'para_id': 303, 'bold_char_id': 404, 'italic_char_id': 406},
            'table_raw': {'char_id': 403, 'para_id': 303, 'bold_char_id': 404, 'italic_char_id': 406},
        }

    def get_style(self, element_type):
        """요소 타입에 맞는 스타일 반환"""
        return self.patterns.get(element_type, self.patterns['paragraph'])

class MDParser:
    """Markdown 파서"""
    
    @staticmethod
    def parse_line(line):
        """라인 타입 및 내용 파싱"""
        original_line = line.rstrip('\n')
        metadata = {
            'original': original_line,
            'marker': None,
            'notes': [],
            'warnings': []
        }
        line = original_line

        # 빈 줄
        if not line.strip():
            metadata['notes'].append('blank-line')
            return ('empty', '', metadata)

        # 스타일 텍스트북 기반 특수 마커
        main_title_match = re.match(r'^<주제목>\s*(.+)', line)
        if main_title_match:
            metadata['marker'] = '<주제목>'
            metadata['notes'].append('requires-title-table')
            return ('main_title', main_title_match.group(1).strip(), metadata)

        m = re.match(r'^□\s+(.*)', line)
        if m:
            metadata['marker'] = '□'
            text_value = m.group(1).strip()
            metadata['notes'].append('sub-title-marker')
            return ('sub_title', f'□ {text_value}', metadata)

        m = re.match(r'^\s*◦\s+(.*)', line)
        if m:
            metadata['marker'] = '◦'
            text_value = m.group(1).strip()
            metadata['notes'].append('body-bullet-marker')
            return ('body_bullet', f'◦ {text_value}', metadata)

        m = re.match(r'^\s{3}-\s+(.*)', line)
        if m:
            metadata['marker'] = '---'
            text_value = m.group(1).strip()
            metadata['notes'].append('description-dash-marker')
            return ('description_dash', f'   - {text_value}', metadata)

        m = re.match(r'^\s{4}\*\s+(.*)', line)
        if m:
            metadata['marker'] = '****'
            text_value = m.group(1).strip()
            metadata['notes'].append('description-star-marker')
            return ('description_star', f'    * {text_value}', metadata)

        m = re.match(r'^<강조>\s*(.+)', line)
        if m:
            metadata['marker'] = '<강조>'
            metadata['notes'].append('requires-emphasis-table')
            return ('emphasis', f'◈ {m.group(1).strip()}', metadata)

        # 테이블 라인 감지 (현재 미지원)
        if re.match(r'^\|.+\|$', line):
            metadata['marker'] = 'table'
            metadata['warnings'].append('table-not-implemented')
            return ('table_raw', line.strip(), metadata)

        # 제목
        if re.match(r'^### ', line):
            return ('h3', re.sub(r'^### ', '', line), metadata)
        elif re.match(r'^## ', line):
            return ('h2', re.sub(r'^## ', '', line), metadata)
        elif re.match(r'^# ', line):
            return ('h1', re.sub(r'^# ', '', line), metadata)

        # 리스트
        elif re.match(r'^    - ', line):
            metadata['marker'] = 'list-indent'
            return ('ul_level2', re.sub(r'^    - ', '', line), metadata)
        elif re.match(r'^  - ', line):
            metadata['marker'] = 'list-indent'
            return ('ul_level2', re.sub(r'^  - ', '', line), metadata)
        elif re.match(r'^- ', line):
            metadata['marker'] = '-'
            return ('ul', re.sub(r'^- ', '', line), metadata)
        elif re.match(r'^\d+\. ', line):
            metadata['marker'] = 'numbered'
            return ('ol', re.sub(r'^\d+\. ', '', line), metadata)

        # 일반 단락
        else:
            return ('paragraph', line, metadata)
    
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
    def create_paragraph(element_type, text, style, rulebook, parser):
        """단락 XML 생성"""
        char_id = style['char_id']
        para_id = style['para_id']
        bold_char = style.get('bold_char_id', rulebook.BOLD_CHAR_ID)
        italic_char = style.get('italic_char_id', rulebook.ITALIC_CHAR_ID)

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
                # 굵게 처리: 지정된 bold 스타일 사용
                if seg.get('bold'):
                    run_char_id = bold_char
                # 기울임 처리: italic 전용 스타일 사용
                elif seg.get('italic'):
                    run_char_id = italic_char

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

    def __init__(self, styles_json_path, textbook_path=None):
        self.rulebook = RulebookLoader(styles_json_path, textbook_path)
        self.parser = MDParser()
        self.generator = HWPXGenerator()
    
    def convert(self, md_content):
        """MD 내용을 HWPX XML로 변환하고 감사 로그 반환"""
        lines = md_content.split('\n')
        paragraphs = []
        audit_entries = []

        for idx, line in enumerate(lines, start=1):
            element_type, text, meta = self.parser.parse_line(line)
            meta.setdefault('notes', [])
            meta.setdefault('warnings', [])

            if element_type == 'empty':
                audit_entries.append({
                    'line_no': idx,
                    'element_type': element_type,
                    'original': meta.get('original', ''),
                    'marker': meta.get('marker'),
                    'applied_para_id': None,
                    'applied_char_id': None,
                    'text': '',
                    'notes': meta['notes'],
                    'warnings': meta['warnings']
                })
                continue

            style = self.rulebook.get_style(element_type)

            warnings = list(meta['warnings'])
            if element_type not in self.rulebook.patterns:
                warnings.append('style-fallback-paragraph')

            para_xml = self.generator.create_paragraph(
                element_type, text, style, self.rulebook, self.parser
            )
            paragraphs.append(para_xml)

            audit_entries.append({
                'line_no': idx,
                'element_type': element_type,
                'original': meta.get('original', ''),
                'marker': meta.get('marker'),
                'applied_para_id': style.get('para_id'),
                'applied_char_id': style.get('char_id'),
                'text': text,
                'notes': meta['notes'],
                'warnings': warnings
            })

        return paragraphs, audit_entries

    def create_hwpx(self, md_file_path, output_path, template_hwpx_path: str = None, audit_path: str = None, pin_font_face: str = None, header_audit_path: str = None, packaging: str = 'headref'):
        """MD 파일을 읽어 HWPX 생성"""
        # MD 파일 읽기
        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
        except FileNotFoundError:
            print(f"❌ 파일을 찾을 수 없습니다: {md_file_path}")
            raise
        
        # 변환
        paragraphs, audit_entries = self.convert(md_content)
        section_xml = self.generator.create_section(paragraphs)
        
        # 템플릿 헤더 로딩 (있다면 사용)
        template_header_xml = None
        if template_hwpx_path and os.path.exists(template_hwpx_path):
            try:
                with zipfile.ZipFile(template_hwpx_path, 'r') as tz:
                    template_header_xml = tz.read('Contents/header.xml').decode('utf-8', 'ignore')
            except Exception:
                template_header_xml = None

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
            
            # Contents/content.hpf - 패키징 모드에 따라 생성
            if packaging == 'opf':
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
            else:
                hwpx.writestr('Contents/content.hpf',
                    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                    '<hpf:HwpDoc xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" version="1.4">\n'
                    '  <hpf:HeadRef href="header.xml"/>\n'
                    '  <hpf:Body>\n'
                    '    <hpf:SectionRef href="section0.xml"/>\n'
                    '  </hpf:Body>\n'
                    '</hpf:HwpDoc>'
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
            
            # Contents/header.xml (템플릿 우선)
            header_xml = template_header_xml if template_header_xml else self._create_header_xml(pin_font_face=pin_font_face)
            hwpx.writestr('Contents/header.xml', header_xml)
            
            # Contents/section0.xml (본문)
            hwpx.writestr('Contents/section0.xml', section_xml)
        
        print(f"[OK] HWPX 생성 완료: {output_path}")
        print(f"   단락 수: {len(paragraphs)}개")

        if audit_path:
            self._write_audit(audit_entries, audit_path)
            print(f"   감사 로그: {audit_path}")
        if header_audit_path:
            used_para = {e['applied_para_id'] for e in audit_entries if e.get('applied_para_id') is not None}
            used_char = {e['applied_char_id'] for e in audit_entries if e.get('applied_char_id') is not None}
            self._write_header_audit(header_xml, used_para, used_char, header_audit_path)
            print(f"   헤더 감사: {header_audit_path}")
        return output_path

    @staticmethod
    def _write_audit(audit_entries, audit_path):
        with open(audit_path, 'w', encoding='utf-8') as f:
            f.write('# Conversion Audit\n\n')
            for entry in audit_entries:
                f.write(f"## Line {entry['line_no']} — {entry['element_type']}\n")
                f.write(f"- Original: {entry['original']}\n")
                if entry.get('marker'):
                    f.write(f"- Marker: {entry['marker']}\n")
                if entry.get('text'):
                    f.write(f"- Text used: {entry['text']}\n")
                if entry.get('applied_para_id') is not None:
                    f.write(f"- paraPrID: {entry['applied_para_id']}\n")
                if entry.get('applied_char_id') is not None:
                    f.write(f"- charPrID: {entry['applied_char_id']}\n")
                if entry.get('notes'):
                    f.write(f"- Notes: {'; '.join(entry['notes'])}\n")
                if entry.get('warnings'):
                    f.write(f"- Warnings: {'; '.join(entry['warnings'])}\n")
                f.write('\n')
    
    def _create_header_xml(self, pin_font_face: str | None = None):
        """header.xml 생성 (멀티 폰트 지원, textbook_styles 반영)"""

        # textbook_styles 사용 여부 확인
        use_textbook = self.rulebook.textbook_styles is not None

        if use_textbook:
            print("[INFO] style_textbook.md 규칙을 사용하여 header 생성")

        # 폰트 매핑 (ID 기반)
        # id 0: HY헤드라인M
        # id 1: 휴먼명조
        # id 2: 맑은 고딕
        fonts = {
            'HY헤드라인M': 0,
            '휴먼명조': 1,
            '맑은 고딕': 2
        }

        header = []
        header.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
        header.append('<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
                      'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
                      'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
                      'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" version="1.4" secCnt="1">')
        header.append('  <hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>')
        header.append('  <hh:refList>')

        # Fontfaces: HANGUL + LATIN (멀티 폰트 지원)
        header.append('    <hh:fontfaces itemCnt="2">')
        header.append('      <hh:fontface lang="HANGUL" fontCnt="3">')
        header.append('        <hh:font id="0" face="HY헤드라인M" type="TTF" isEmbedded="0">')
        header.append('          <hh:typeInfo familyType="FCAT_GOTHIC" weight="5"/>')
        header.append('        </hh:font>')
        header.append('        <hh:font id="1" face="휴먼명조" type="TTF" isEmbedded="0">')
        header.append('          <hh:typeInfo familyType="FCAT_SERIF" weight="5"/>')
        header.append('        </hh:font>')
        header.append('        <hh:font id="2" face="맑은 고딕" type="TTF" isEmbedded="0">')
        header.append('          <hh:typeInfo familyType="FCAT_GOTHIC" weight="5"/>')
        header.append('        </hh:font>')
        header.append('      </hh:fontface>')
        header.append('      <hh:fontface lang="LATIN" fontCnt="3">')
        header.append('        <hh:font id="0" face="HY헤드라인M" type="TTF" isEmbedded="0">')
        header.append('          <hh:typeInfo familyType="FCAT_GOTHIC" weight="5"/>')
        header.append('        </hh:font>')
        header.append('        <hh:font id="1" face="휴먼명조" type="TTF" isEmbedded="0">')
        header.append('          <hh:typeInfo familyType="FCAT_SERIF" weight="5"/>')
        header.append('        </hh:font>')
        header.append('        <hh:font id="2" face="맑은 고딕" type="TTF" isEmbedded="0">')
        header.append('          <hh:typeInfo familyType="FCAT_GOTHIC" weight="5"/>')
        header.append('        </hh:font>')
        header.append('      </hh:fontface>')
        header.append('    </hh:fontfaces>')

        # Character styles (textbook_styles 기반 생성)
        header.append('    <hh:charProperties itemCnt="7">')

        def charpr(cid, height, font_id, bold=False, italic=False):
            header.append(f'      <hh:charPr id="{cid}" height="{height}" textColor="#000000">')
            header.append(f'        <hh:fontRef hangul="{font_id}" latin="{font_id}"/>')
            if bold:
                header.append('        <hh:bold/>')
            if italic:
                header.append('        <hh:italic/>')
            header.append('        <hh:underline type="NONE"/>')
            header.append('      </hh:charPr>')

        if use_textbook:
            ts = self.rulebook.textbook_styles
            # 401: main_title (주제목)
            s = ts.get('main_title', {'font': 'HY헤드라인M', 'size': 15, 'bold': True})
            charpr(401, s['size'] * 100, fonts.get(s['font'], 0), bold=s['bold'])

            # 402: sub_title (소제목)
            s = ts.get('sub_title', {'font': 'HY헤드라인M', 'size': 15, 'bold': False})
            charpr(402, s['size'] * 100, fonts.get(s['font'], 0), bold=s['bold'])

            # 403: body_bullet (본문)
            s = ts.get('body_bullet', {'font': '휴먼명조', 'size': 15, 'bold': False})
            charpr(403, s['size'] * 100, fonts.get(s['font'], 1), bold=s['bold'])

            # 404: emphasis (강조) - bold 전용
            s = ts.get('emphasis', {'font': '휴먼명조', 'size': 15, 'bold': True})
            charpr(404, s['size'] * 100, fonts.get(s['font'], 1), bold=True)

            # 405: description_star (*)
            s = ts.get('description_star', {'font': '맑은 고딕', 'size': 12, 'bold': False})
            charpr(405, s['size'] * 100, fonts.get(s['font'], 2), bold=s['bold'])

            # 406: italic 전용
            charpr(406, 1200, 1, italic=True)

            # 44: 코드
            charpr(44, 1000, 2)
        else:
            # 폴백: 기존 방식
            charpr(401, 1800, 2, bold=True)
            charpr(402, 1500, 2)
            charpr(403, 1200, 2)
            charpr(404, 1200, 2, bold=True)
            charpr(405, 1200, 2)
            charpr(406, 1200, 2, italic=True)
            charpr(44, 1000, 2)

        header.append('    </hh:charProperties>')

        # Paragraph styles (textbook_styles 기반)
        header.append('    <hh:paraProperties itemCnt="6">')

        def parapr(pid, align, lsp):
            header.append(f'      <hh:paraPr id="{pid}">')
            header.append(f'        <hh:align horizontal="{align}"/>')
            header.append(f'        <hh:lineSpacing type="PERCENT" value="{lsp}"/>')
            header.append('      </hh:paraPr>')

        if use_textbook:
            ts = self.rulebook.textbook_styles
            # 301: main_title
            s = ts.get('main_title', {'align': 'CENTER', 'line_spacing': 130})
            parapr(301, s['align'], str(s['line_spacing']))

            # 302: sub_title
            s = ts.get('sub_title', {'align': 'LEFT', 'line_spacing': 160})
            parapr(302, s['align'], str(s['line_spacing']))

            # 303: body_bullet
            s = ts.get('body_bullet', {'align': 'LEFT', 'line_spacing': 160})
            parapr(303, s['align'], str(s['line_spacing']))

            # 304: description_dash
            s = ts.get('description_dash', {'align': 'LEFT', 'line_spacing': 160})
            parapr(304, s['align'], str(s['line_spacing']))

            # 305: description_star
            s = ts.get('description_star', {'align': 'LEFT', 'line_spacing': 160})
            parapr(305, s['align'], str(s['line_spacing']))

            # 306: emphasis
            s = ts.get('emphasis', {'align': 'CENTER', 'line_spacing': 130})
            parapr(306, s['align'], str(s['line_spacing']))
        else:
            # 폴백
            parapr(301, 'CENTER', '130')
            parapr(302, 'LEFT', '160')
            parapr(303, 'LEFT', '160')
            parapr(304, 'LEFT', '160')
            parapr(305, 'LEFT', '160')
            parapr(306, 'CENTER', '130')

        header.append('    </hh:paraProperties>')
        header.append('  </hh:refList>')
        header.append('</hh:head>')
        return '\n'.join(header)

    @staticmethod
    def _write_header_audit(header_xml: str, used_para_ids, used_char_ids, path: str):
        import xml.etree.ElementTree as ET
        NS = {
            'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
            'hc': 'http://www.hancom.co.kr/hwpml/2011/core'
        }
        root = ET.fromstring(header_xml)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('# Header Audit\n\n')
            f.write('## Character Styles\n')
            for cid in sorted(used_char_ids):
                pr = root.find(f".//hh:charPr[@id='{cid}']", NS)
                if pr is None:
                    f.write(f'- id {cid}: MISSING\n')
                    continue
                height = pr.get('height')
                bold = pr.find('hh:bold', NS) is not None
                italic = pr.find('hh:italic', NS) is not None
                fref = pr.find('hh:fontRef', NS)
                hangul = fref.get('hangul') if fref is not None else '?'
                latin = fref.get('latin') if fref is not None else '?'
                f.write(f'- id {cid}: height={height}, bold={bold}, italic={italic}, fontRef(hangul={hangul}, latin={latin})\n')
            f.write('\n## Paragraph Styles\n')
            for pid in sorted(used_para_ids):
                pr = root.find(f".//hh:paraPr[@id='{pid}']", NS)
                if pr is None:
                    f.write(f'- id {pid}: MISSING\n')
                    continue
                align = pr.find('hh:align', NS)
                lsp = pr.find('hh:lineSpacing', NS)
                f.write(f"- id {pid}: align={align.get('horizontal') if align is not None else '?'}, "
                        f"lineSpacing={lsp.get('type') if lsp is not None else '?'}/{lsp.get('value') if lsp is not None else '?'}\n")

def _build_arg_parser():
    parser = argparse.ArgumentParser(description='Markdown to HWPX converter (정부 문서 스타일 대응)')
    parser.add_argument('input', nargs='?', help='입력 Markdown 파일 경로')
    parser.add_argument('output', nargs='?', help='출력 HWPX 파일 경로 (기본: output.hwpx)')
    parser.add_argument('--audit', action='store_true', help='감사 로그(.audit.md) 생성')
    parser.add_argument('--template', help='헤더를 복사할 HWPX 템플릿 경로')
    parser.add_argument('--styles', help='스타일 JSON 경로 (기본: extracted_styles_v2.json)')
    parser.add_argument('--textbook', help='스타일 텍스트북 경로 (기본: style_textbook.md)')
    parser.add_argument('--pin-font', dest='pin_font', help='모든 문자 스타일을 지정 폰트로 고정 (예: 맑은 고딕)')
    parser.add_argument('--header-audit', action='store_true', help='사용된 para/char 정의 요약 파일 생성(.header.audit.md)')
    parser.add_argument('--packaging', choices=['opf','headref'], default='headref', help='content.hpf 패키징 방식 선택')
    parser.add_argument('--test', action='store_true', help='샘플 문서로 테스트 실행')
    return parser


def _default_styles_path():
    return os.path.join(os.path.dirname(__file__), 'extracted_styles_v2.json')


def _default_textbook_path():
    return os.path.join(os.path.dirname(__file__), 'style_textbook.md')


def main():
    parser = _build_arg_parser()
    args = parser.parse_args()

    styles_path = args.styles if args.styles else _default_styles_path()
    textbook_path = args.textbook if args.textbook else _default_textbook_path()
    converter = MDtoHWPXConverter(styles_path, textbook_path)

    if args.input:
        output_file = args.output if args.output else 'output.hwpx'
        audit_path = None
        if args.audit:
            base, _ = os.path.splitext(output_file)
            audit_path = f"{base}.audit.md"
        header_audit_path = None
        if args.header_audit:
            base, _ = os.path.splitext(output_file)
            header_audit_path = f"{base}.header.audit.md"
        converter.create_hwpx(
            args.input,
            output_file,
            template_hwpx_path=args.template,
            audit_path=audit_path,
            pin_font_face=args.pin_font,
            header_audit_path=header_audit_path,
            packaging=args.packaging
        )
        return

    if args.test:
        print("테스트 모드로 실행합니다...")
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
        temp_md = os.path.join(os.getcwd(), 'md_to_hwpx_test.md')
        with open(temp_md, 'w', encoding='utf-8') as f:
            f.write(test_md)
        output_file = os.path.join(os.getcwd(), 'test_output.hwpx')
        converter.create_hwpx(temp_md, output_file)
        print(f"테스트 출력: {output_file}")
        return

    parser.print_help()


# 메인 실행
if __name__ == "__main__":
    main()
