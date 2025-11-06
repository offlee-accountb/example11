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
        """단락 XML 생성 (linesegarray 포함)"""
        char_id = style['char_id']
        para_id = style['para_id']
        bold_char = style.get('bold_char_id', rulebook.BOLD_CHAR_ID)
        italic_char = style.get('italic_char_id', rulebook.ITALIC_CHAR_ID)

        # 인라인 서식 처리
        segments = parser.process_inline_formats(text, char_id)

        # 스타일 정보에서 글자 크기/줄간격 추출 (textbook_styles 사용)
        # rulebook.textbook_styles에서 현재 element_type의 스타일 가져오기
        font_height = 1500  # 기본값 (15pt)
        line_spacing_percent = 160  # 기본값

        if rulebook.textbook_styles and element_type in ['main_title', 'sub_title', 'body_bullet', 'description_dash', 'description_star', 'emphasis']:
            ts = rulebook.textbook_styles.get(element_type, {})
            font_height = ts.get('size', 15) * 100
            line_spacing_percent = ts.get('line_spacing', 160)

        # linesegarray 계산
        vertsize = font_height
        textheight = font_height
        baseline = int(font_height * 0.85)
        # spacing = lineSpacing에 비례 (160% → 약 900, 130% → 약 452)
        spacing = int(font_height * (line_spacing_percent / 100) * 0.6)

        # XML 생성 (Model과 동일한 속성 추가)
        xml = f'    <hp:p id="0" paraPrIDRef="{para_id}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">\n'

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

        # linesegarray 추가 (줄바꿈/줄간격 정의)
        xml += '      <hp:linesegarray>\n'
        xml += f'        <hp:lineseg textpos="0" vertpos="0" vertsize="{vertsize}" textheight="{textheight}" baseline="{baseline}" spacing="{spacing}" horzpos="0" horzsize="48188" flags="393216"/>\n'
        xml += '      </hp:linesegarray>\n'

        xml += '    </hp:p>\n'

        return xml
    
    @staticmethod
    def create_title_table(text, style, rulebook, parser):
        """<주제목> 3행 표 생성"""
        char_id = style.get('bold_char_id', 9)  # 굵은 글씨
        para_id = style.get('para_id', 20)  # 중앙정렬

        # 인라인 서식 처리
        segments = parser.process_inline_formats(text, char_id)

        # 텍스트 내용 생성
        text_content = ''
        for seg in segments:
            if not seg['text']:
                continue
            run_char_id = seg.get('bold') and style.get('bold_char_id', char_id) or char_id
            escaped_text = HWPXGenerator.escape_xml(seg['text'])
            text_content += f'<hp:run charPrIDRef="{run_char_id}"><hp:t>{escaped_text}</hp:t></hp:run>'

        # 3행 표 생성 (빈행-제목-빈행)
        xml = '    <hp:p paraPrIDRef="0" styleIDRef="0">\n'
        xml += '      <hp:run charPrIDRef="10">\n'
        xml += '        <hp:tbl id="1998390486" zOrder="0" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="3" colCnt="1" cellSpacing="0" borderFillIDRef="3" noAdjust="0">\n'
        xml += '          <hp:sz width="48189" widthRelTo="ABSOLUTE" height="4216" heightRelTo="ABSOLUTE" protect="0"/>\n'
        xml += '          <hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>\n'
        xml += '          <hp:outMargin left="283" right="283" top="283" bottom="283"/>\n'
        xml += '          <hp:inMargin left="510" right="510" top="141" bottom="141"/>\n'

        # 첫 번째 행 (빈행)
        xml += '          <hp:tr>\n'
        xml += '            <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="5">\n'
        xml += '              <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">\n'
        xml += '                <hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">\n'
        xml += '                  <hp:run charPrIDRef="7"/>\n'
        xml += '                  <hp:linesegarray>\n'
        xml += '                    <hp:lineseg textpos="0" vertpos="0" vertsize="100" textheight="100" baseline="85" spacing="60" horzpos="0" horzsize="47168" flags="393216"/>\n'
        xml += '                  </hp:linesegarray>\n'
        xml += '                </hp:p>\n'
        xml += '              </hp:subList>\n'
        xml += '              <hp:cellAddr colAddr="0" rowAddr="0"/>\n'
        xml += '              <hp:cellSpan colSpan="1" rowSpan="1"/>\n'
        xml += '              <hp:cellSz width="48189" height="521"/>\n'
        xml += '              <hp:cellMargin left="510" right="510" top="141" bottom="141"/>\n'
        xml += '            </hp:tc>\n'
        xml += '          </hp:tr>\n'

        # 두 번째 행 (제목)
        xml += '          <hp:tr>\n'
        xml += '            <hp:tc name="" header="0" hasMargin="1" protect="0" editable="0" dirty="0" borderFillIDRef="4">\n'
        xml += '              <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">\n'
        xml += f'                <hp:p id="0" paraPrIDRef="{para_id}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">\n'
        xml += f'                  {text_content}\n'
        xml += '                  <hp:linesegarray>\n'
        xml += '                    <hp:lineseg textpos="0" vertpos="0" vertsize="1500" textheight="1500" baseline="1275" spacing="452" horzpos="0" horzsize="45352" flags="393216"/>\n'
        xml += '                  </hp:linesegarray>\n'
        xml += '                </hp:p>\n'
        xml += '              </hp:subList>\n'
        xml += '              <hp:cellAddr colAddr="0" rowAddr="1"/>\n'
        xml += '              <hp:cellSpan colSpan="1" rowSpan="1"/>\n'
        xml += '              <hp:cellSz width="48189" height="3174"/>\n'
        xml += '              <hp:cellMargin left="1417" right="1417" top="141" bottom="141"/>\n'
        xml += '            </hp:tc>\n'
        xml += '          </hp:tr>\n'

        # 세 번째 행 (빈행)
        xml += '          <hp:tr>\n'
        xml += '            <hp:tc name="" header="0" hasMargin="0" protect="0" editable="0" dirty="0" borderFillIDRef="5">\n'
        xml += '              <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">\n'
        xml += '                <hp:p id="0" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">\n'
        xml += '                  <hp:run charPrIDRef="7"/>\n'
        xml += '                  <hp:linesegarray>\n'
        xml += '                    <hp:lineseg textpos="0" vertpos="0" vertsize="100" textheight="100" baseline="85" spacing="60" horzpos="0" horzsize="47168" flags="393216"/>\n'
        xml += '                  </hp:linesegarray>\n'
        xml += '                </hp:p>\n'
        xml += '              </hp:subList>\n'
        xml += '              <hp:cellAddr colAddr="0" rowAddr="2"/>\n'
        xml += '              <hp:cellSpan colSpan="1" rowSpan="1"/>\n'
        xml += '              <hp:cellSz width="48189" height="521"/>\n'
        xml += '              <hp:cellMargin left="510" right="510" top="141" bottom="141"/>\n'
        xml += '            </hp:tc>\n'
        xml += '          </hp:tr>\n'

        xml += '        </hp:tbl>\n'
        xml += '        <hp:t/>\n'
        xml += '      </hp:run>\n'
        xml += '    </hp:p>\n'

        return xml

    @staticmethod
    def create_emphasis_table(text, style, rulebook, parser):
        """<강조> 1행 표 생성 (배경색)"""
        char_id = style.get('bold_char_id', 16)
        para_id = style.get('para_id', 20)

        # 인라인 서식 처리 (◈ 기호는 이미 parse_line에서 추가됨)
        segments = parser.process_inline_formats(text, char_id)

        # 텍스트 내용 생성
        text_content = ''
        for seg in segments:
            if not seg['text']:
                continue
            run_char_id = seg.get('bold') and style.get('bold_char_id', char_id) or char_id
            escaped_text = HWPXGenerator.escape_xml(seg['text'])
            text_content += f'<hp:run charPrIDRef="{run_char_id}"><hp:t>{escaped_text}</hp:t></hp:run>'

        # 1행 표 생성 (강조 배경색)
        xml = '    <hp:p paraPrIDRef="21" styleIDRef="0">\n'
        xml += '      <hp:run charPrIDRef="11">\n'
        xml += '        <hp:tbl id="1998390487" zOrder="1" numberingType="TABLE" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" dropcapstyle="None" pageBreak="CELL" repeatHeader="1" rowCnt="1" colCnt="1" cellSpacing="0" borderFillIDRef="3" noAdjust="0">\n'
        xml += '          <hp:sz width="48189" widthRelTo="ABSOLUTE" height="2632" heightRelTo="ABSOLUTE" protect="0"/>\n'
        xml += '          <hp:pos treatAsChar="0" affectLSpacing="0" flowWithText="1" allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" horzRelTo="COLUMN" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" horzOffset="0"/>\n'
        xml += '          <hp:outMargin left="283" right="283" top="283" bottom="283"/>\n'
        xml += '          <hp:inMargin left="510" right="510" top="141" bottom="141"/>\n'
        xml += '          <hp:tr>\n'
        xml += '            <hp:tc name="" header="0" hasMargin="1" protect="0" editable="0" dirty="0" borderFillIDRef="6">\n'
        xml += '              <hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" vertAlign="CENTER" linkListIDRef="0" linkListNextIDRef="0" textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">\n'
        xml += f'                <hp:p id="0" paraPrIDRef="{para_id}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">\n'
        xml += f'                  {text_content}\n'
        xml += '                  <hp:linesegarray>\n'
        xml += '                    <hp:lineseg textpos="0" vertpos="0" vertsize="1500" textheight="1500" baseline="1275" spacing="452" horzpos="0" horzsize="47056" flags="393216"/>\n'
        xml += '                  </hp:linesegarray>\n'
        xml += '                </hp:p>\n'
        xml += '              </hp:subList>\n'
        xml += '              <hp:cellAddr colAddr="0" rowAddr="0"/>\n'
        xml += '              <hp:cellSpan colSpan="1" rowSpan="1"/>\n'
        xml += '              <hp:cellSz width="48189" height="521"/>\n'
        xml += '              <hp:cellMargin left="566" right="566" top="566" bottom="566"/>\n'
        xml += '            </hp:tc>\n'
        xml += '          </hp:tr>\n'
        xml += '        </hp:tbl>\n'
        xml += '        <hp:t/>\n'
        xml += '      </hp:run>\n'
        xml += '    </hp:p>\n'

        return xml

    @staticmethod
    def create_section(paragraphs):
        """섹션 XML 생성 (첫 단락에 secPr 추가)"""
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        xml += '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
        xml += 'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">\n'

        # 첫 번째 단락에 secPr 삽입
        for i, para_xml in enumerate(paragraphs):
            if i == 0:
                # 첫 단락의 <hp:p ...> 다음에 secPr을 삽입
                # <hp:p ...>를 찾아서 그 뒤에 <hp:run>을 추가하고 그 안에 secPr 넣기
                # 간단하게: 첫 번째 <hp:run> 전에 secPr run 삽입

                # <hp:p ...> 태그를 찾아서 분리
                p_start = para_xml.find('<hp:p ')
                p_end = para_xml.find('>', p_start) + 1

                # secPr을 포함한 run 생성
                secPr_run = '''      <hp:run charPrIDRef="0">
        <hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" tabStopVal="4000" tabStopUnit="HWPUNIT" outlineShapeIDRef="1" memoShapeIDRef="0" textVerticalWidthHead="0" masterPageCnt="0">
          <hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/>
          <hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>
          <hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/>
          <hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/>
          <hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY">
            <hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/>
          </hp:pagePr>
          <hp:footNotePr>
            <hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>
            <hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>
            <hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/>
            <hp:numbering type="CONTINUOUS" newNum="1"/>
            <hp:placement place="EACH_COLUMN" beneathText="0"/>
          </hp:footNotePr>
          <hp:endNotePr>
            <hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>
            <hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/>
            <hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/>
            <hp:numbering type="CONTINUOUS" newNum="1"/>
            <hp:placement place="END_OF_DOCUMENT" beneathText="0"/>
          </hp:endNotePr>
          <hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER">
            <hp:offset left="1417" right="1417" top="1417" bottom="1417"/>
          </hp:pageBorderFill>
          <hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER">
            <hp:offset left="1417" right="1417" top="1417" bottom="1417"/>
          </hp:pageBorderFill>
          <hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER">
            <hp:offset left="1417" right="1417" top="1417" bottom="1417"/>
          </hp:pageBorderFill>
        </hp:secPr>
        <hp:ctrl>
          <hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/>
        </hp:ctrl>
      </hp:run>
'''
                # 첫 단락 재구성: <hp:p> + secPr run + 나머지
                modified_para = para_xml[:p_end] + '\n' + secPr_run + para_xml[p_end:]
                xml += modified_para
            else:
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

            # 특수 표 처리 확인
            if 'requires-title-table' in meta['notes']:
                # <주제목> 3행 표 생성
                para_xml = self.generator.create_title_table(
                    text, style, self.rulebook, self.parser
                )
            elif 'requires-emphasis-table' in meta['notes']:
                # <강조> 1행 표 생성
                para_xml = self.generator.create_emphasis_table(
                    text, style, self.rulebook, self.parser
                )
            else:
                # 일반 단락 생성
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

    def create_hwpx(self, md_file_path, output_path, template_hwpx_path: str = None, audit_path: str = None, pin_font_face: str = None, header_audit_path: str = None, packaging: str = 'opf'):
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

        # 폰트 매핑 (ID 기반) - Windows 호환 폰트 사용
        # id 0: 맑은 고딕 (Windows 기본, 제목용)
        # id 1: 바탕 (Windows 기본, 본문용)
        # id 2: 맑은 고딕 (Windows 기본)
        fonts = {
            'HY헤드라인M': 0,    # 맑은 고딕으로 대체
            '휴먼명조': 1,        # 바탕으로 대체
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

        # Fontfaces: 7개 언어 (HANGUL, LATIN, HANJA, JAPANESE, OTHER, SYMBOL, USER)
        header.append('    <hh:fontfaces itemCnt="7">')

        # 7개 언어 모두에 동일한 폰트 3개 적용
        for lang in ['HANGUL', 'LATIN', 'HANJA', 'JAPANESE', 'OTHER', 'SYMBOL', 'USER']:
            header.append(f'      <hh:fontface lang="{lang}" fontCnt="3">')

            # font id="0": 맑은 고딕
            if lang == 'LATIN':
                face0, face1, face2 = 'Malgun Gothic', 'Batang', 'Malgun Gothic'
            else:
                face0, face1, face2 = '맑은 고딕', '바탕', '맑은 고딕'

            header.append(f'        <hh:font id="0" face="{face0}" type="TTF" isEmbedded="0">')
            header.append('          <hh:typeInfo familyType="FCAT_GOTHIC" weight="6"/>')
            header.append('        </hh:font>')

            # font id="1": 바탕
            header.append(f'        <hh:font id="1" face="{face1}" type="TTF" isEmbedded="0">')
            header.append('          <hh:typeInfo familyType="FCAT_SERIF" weight="5"/>')
            header.append('        </hh:font>')

            # font id="2": 맑은 고딕
            header.append(f'        <hh:font id="2" face="{face2}" type="TTF" isEmbedded="0">')
            header.append('          <hh:typeInfo familyType="FCAT_GOTHIC" weight="5"/>')
            header.append('        </hh:font>')

            header.append('      </hh:fontface>')

        header.append('    </hh:fontfaces>')

        # borderFills (표 테두리/배경색 정의)
        header.append('    <hh:borderFills itemCnt="6">')
        # id="1": 테두리 없음
        header.append('      <hh:borderFill id="1" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">')
        header.append('        <hh:leftBorder type="NONE" width="0.1 mm" color="#000000"/>')
        header.append('        <hh:rightBorder type="NONE" width="0.1 mm" color="#000000"/>')
        header.append('        <hh:topBorder type="NONE" width="0.1 mm" color="#000000"/>')
        header.append('        <hh:bottomBorder type="NONE" width="0.1 mm" color="#000000"/>')
        header.append('        <hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>')
        header.append('      </hh:borderFill>')

        # id="2": 테두리 없음 (default background)
        header.append('      <hh:borderFill id="2" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">')
        header.append('        <hh:leftBorder type="NONE" width="0.1 mm" color="#000000"/>')
        header.append('        <hh:rightBorder type="NONE" width="0.1 mm" color="#000000"/>')
        header.append('        <hh:topBorder type="NONE" width="0.1 mm" color="#000000"/>')
        header.append('        <hh:bottomBorder type="NONE" width="0.1 mm" color="#000000"/>')
        header.append('        <hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>')
        header.append('        <hc:fillBrush>')
        header.append('          <hc:winBrush faceColor="none" hatchColor="#999999" alpha="0"/>')
        header.append('        </hc:fillBrush>')
        header.append('      </hh:borderFill>')

        # id="3": 표 외곽 테두리 (실선)
        header.append('      <hh:borderFill id="3" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">')
        header.append('        <hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>')
        header.append('      </hh:borderFill>')

        # id="4": 테두리 없음 (제목행)
        header.append('      <hh:borderFill id="4" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">')
        header.append('        <hh:leftBorder type="NONE" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:rightBorder type="NONE" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:topBorder type="NONE" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:bottomBorder type="NONE" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>')
        header.append('      </hh:borderFill>')

        # id="5": 테두리 없음 + 보라색 배경 (빈행)
        header.append('      <hh:borderFill id="5" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">')
        header.append('        <hh:leftBorder type="NONE" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:rightBorder type="NONE" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:topBorder type="NONE" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:bottomBorder type="NONE" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>')
        header.append('        <hc:fillBrush>')
        header.append('          <hc:winBrush faceColor="#EBDEF1" hatchColor="#999999" alpha="0"/>')
        header.append('        </hc:fillBrush>')
        header.append('      </hh:borderFill>')

        # id="6": 테두리 있음 + 초록색 배경 (강조)
        header.append('      <hh:borderFill id="6" threeD="0" shadow="0" centerLine="NONE" breakCellSeparateLine="0">')
        header.append('        <hh:leftBorder type="SOLID" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:rightBorder type="SOLID" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:topBorder type="SOLID" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:bottomBorder type="SOLID" width="0.12 mm" color="#000000"/>')
        header.append('        <hh:diagonal type="SOLID" width="0.1 mm" color="#000000"/>')
        header.append('        <hc:fillBrush>')
        header.append('          <hc:winBrush faceColor="#CDF2E4" hatchColor="#999999" alpha="0"/>')
        header.append('        </hc:fillBrush>')
        header.append('      </hh:borderFill>')

        header.append('    </hh:borderFills>')

        # Character styles (textbook_styles 기반 생성)
        header.append('    <hh:charProperties itemCnt="17">')

        def charpr(cid, height, font_id, bold=False, italic=False):
            header.append(f'      <hh:charPr id="{cid}" height="{height}" textColor="#000000">')
            header.append(f'        <hh:fontRef hangul="{font_id}" latin="{font_id}"/>')
            if bold:
                header.append('        <hh:bold/>')
            if italic:
                header.append('        <hh:italic/>')
            header.append('        <hh:underline type="NONE"/>')
            header.append('      </hh:charPr>')

        # 기본 charPr (0-6, Model 호환)
        charpr(0, 1000, 1)      # 기본
        charpr(1, 1000, 1)      # 기본
        charpr(2, 900, 1)       # 작은 글씨
        charpr(3, 900, 1)       # 작은 글씨
        charpr(4, 900, 1)       # 작은 글씨
        charpr(5, 1600, 1)      # 큰 글씨
        charpr(6, 1100, 1)      # 중간 글씨

        # 표 전용 charPr
        charpr(7, 100, 1)       # 빈행 (매우 작은 글씨)
        charpr(8, 1500, 0)      # HY헤드라인M (소제목용)
        charpr(9, 1500, 0, bold=True)  # HY헤드라인M Bold (주제목용)
        charpr(10, 1000, 1)     # 휴먼명조 기본
        charpr(11, 1500, 1)     # 휴먼명조 (본문용)
        charpr(12, 800, 1)      # 휴먼명조 작게
        charpr(13, 600, 1)      # 휴먼명조 더 작게
        charpr(14, 400, 1)      # 휴먼명조 매우 작게
        charpr(15, 1200, 2)     # 맑은 고딕
        charpr(16, 1500, 1, bold=True)  # 휴먼명조 Bold (강조용)

        # textbook_styles 기반 (400번대)
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

        # ========== tabProperties 섹션 추가 ==========
        header.append('    <hh:tabProperties itemCnt="3">')
        header.append('      <hh:tabPr id="0" autoTabLeft="0" autoTabRight="0"/>')
        header.append('      <hh:tabPr id="1" autoTabLeft="1" autoTabRight="0"/>')
        header.append('      <hh:tabPr id="2" autoTabLeft="0" autoTabRight="1"/>')
        header.append('    </hh:tabProperties>')

        # ========== numberings 섹션 추가 ==========
        header.append('    <hh:numberings itemCnt="1">')
        header.append('      <hh:numbering id="1" start="0">')
        header.append('        <hh:paraHead start="1" level="1" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" textOffset="50" numFormat="DIGIT" charPrIDRef="4294967295" checkable="0">^1.</hh:paraHead>')
        header.append('        <hh:paraHead start="1" level="2" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" textOffset="50" numFormat="HANGUL_SYLLABLE" charPrIDRef="4294967295" checkable="0">^2.</hh:paraHead>')
        header.append('        <hh:paraHead start="1" level="3" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" textOffset="50" numFormat="DIGIT" charPrIDRef="4294967295" checkable="0">^3)</hh:paraHead>')
        header.append('        <hh:paraHead start="1" level="4" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" textOffset="50" numFormat="HANGUL_SYLLABLE" charPrIDRef="4294967295" checkable="0">^4)</hh:paraHead>')
        header.append('        <hh:paraHead start="1" level="5" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" textOffset="50" numFormat="DIGIT" charPrIDRef="4294967295" checkable="0">(^5)</hh:paraHead>')
        header.append('        <hh:paraHead start="1" level="6" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" textOffset="50" numFormat="HANGUL_SYLLABLE" charPrIDRef="4294967295" checkable="0">(^6)</hh:paraHead>')
        header.append('        <hh:paraHead start="1" level="7" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" textOffset="50" numFormat="CIRCLED_DIGIT" charPrIDRef="4294967295" checkable="1">^7</hh:paraHead>')
        header.append('        <hh:paraHead start="1" level="8" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" textOffset="50" numFormat="CIRCLED_HANGUL_SYLLABLE" charPrIDRef="4294967295" checkable="1">^8</hh:paraHead>')
        header.append('        <hh:paraHead start="1" level="9" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" textOffset="50" numFormat="HANGUL_JAMO" charPrIDRef="4294967295" checkable="0"/>')
        header.append('        <hh:paraHead start="1" level="10" align="LEFT" useInstWidth="1" autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" textOffset="50" numFormat="ROMAN_SMALL" charPrIDRef="4294967295" checkable="1"/>')
        header.append('      </hh:numbering>')
        header.append('    </hh:numberings>')

        # Paragraph styles (textbook_styles 기반)
        header.append('    <hh:paraProperties itemCnt="22">')

        def parapr(pid, align, lsp):
            header.append(f'      <hh:paraPr id="{pid}">')
            header.append(f'        <hh:align horizontal="{align}"/>')
            header.append(f'        <hh:lineSpacing type="PERCENT" value="{lsp}"/>')
            header.append('      </hh:paraPr>')

        # 기본 paraPr (0-21, Model 호환)
        parapr(0, 'JUSTIFY', '160')     # 기본
        parapr(1, 'JUSTIFY', '160')     # 본문
        parapr(2, 'JUSTIFY', '160')     # 개요 1
        parapr(3, 'JUSTIFY', '160')     # 개요 2
        parapr(4, 'JUSTIFY', '160')     # 개요 3
        parapr(5, 'JUSTIFY', '160')     # 개요 4
        parapr(6, 'JUSTIFY', '160')     # 개요 5
        parapr(7, 'JUSTIFY', '160')     # 개요 6
        parapr(8, 'JUSTIFY', '160')     # 개요 7
        parapr(9, 'JUSTIFY', '150')     # 머리말
        parapr(10, 'LEFT', '130')       # 각주
        parapr(11, 'LEFT', '130')       # 캡션
        parapr(12, 'LEFT', '160')       # 차례 제목
        parapr(13, 'LEFT', '160')       # 차례 1
        parapr(14, 'LEFT', '160')       # 차례 2
        parapr(15, 'LEFT', '160')       # 차례 3
        parapr(16, 'JUSTIFY', '160')    # 개요 8
        parapr(17, 'JUSTIFY', '160')    # 개요 9
        parapr(18, 'JUSTIFY', '160')    # 개요 10
        parapr(19, 'JUSTIFY', '150')    # 기타
        parapr(20, 'CENTER', '130')     # 중앙정렬 (표 제목용)
        parapr(21, 'JUSTIFY', '160')    # 기본 2

        # textbook_styles 기반 (300번대)
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

        # ========== styles 섹션 추가 (Model에서 가져옴) ==========
        header.append('    <hh:styles itemCnt="22">')
        header.append('      <hh:style id="0" type="PARA" name="바탕글" engName="Normal" paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="1" type="PARA" name="본문" engName="Body" paraPrIDRef="1" charPrIDRef="0" nextStyleIDRef="1" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="2" type="PARA" name="개요 1" engName="Outline 1" paraPrIDRef="2" charPrIDRef="0" nextStyleIDRef="2" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="3" type="PARA" name="개요 2" engName="Outline 2" paraPrIDRef="3" charPrIDRef="0" nextStyleIDRef="3" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="4" type="PARA" name="개요 3" engName="Outline 3" paraPrIDRef="4" charPrIDRef="0" nextStyleIDRef="4" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="5" type="PARA" name="개요 4" engName="Outline 4" paraPrIDRef="5" charPrIDRef="0" nextStyleIDRef="5" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="6" type="PARA" name="개요 5" engName="Outline 5" paraPrIDRef="6" charPrIDRef="0" nextStyleIDRef="6" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="7" type="PARA" name="개요 6" engName="Outline 6" paraPrIDRef="7" charPrIDRef="0" nextStyleIDRef="7" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="8" type="PARA" name="개요 7" engName="Outline 7" paraPrIDRef="8" charPrIDRef="0" nextStyleIDRef="8" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="9" type="PARA" name="개요 8" engName="Outline 8" paraPrIDRef="18" charPrIDRef="0" nextStyleIDRef="9" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="10" type="PARA" name="개요 9" engName="Outline 9" paraPrIDRef="16" charPrIDRef="0" nextStyleIDRef="10" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="11" type="PARA" name="개요 10" engName="Outline 10" paraPrIDRef="17" charPrIDRef="0" nextStyleIDRef="11" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="12" type="CHAR" name="쪽 번호" engName="Page Number" paraPrIDRef="0" charPrIDRef="1" nextStyleIDRef="0" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="13" type="PARA" name="머리말" engName="Header" paraPrIDRef="9" charPrIDRef="2" nextStyleIDRef="13" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="14" type="PARA" name="각주" engName="Footnote" paraPrIDRef="10" charPrIDRef="3" nextStyleIDRef="14" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="15" type="PARA" name="미주" engName="Endnote" paraPrIDRef="10" charPrIDRef="3" nextStyleIDRef="15" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="16" type="PARA" name="메모" engName="Memo" paraPrIDRef="11" charPrIDRef="4" nextStyleIDRef="16" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="17" type="PARA" name="차례 제목" engName="TOC Heading" paraPrIDRef="12" charPrIDRef="5" nextStyleIDRef="17" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="18" type="PARA" name="차례 1" engName="TOC 1" paraPrIDRef="13" charPrIDRef="6" nextStyleIDRef="18" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="19" type="PARA" name="차례 2" engName="TOC 2" paraPrIDRef="14" charPrIDRef="6" nextStyleIDRef="19" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="20" type="PARA" name="차례 3" engName="TOC 3" paraPrIDRef="15" charPrIDRef="6" nextStyleIDRef="20" langID="1042" lockForm="0"/>')
        header.append('      <hh:style id="21" type="PARA" name="캡션" engName="Caption" paraPrIDRef="19" charPrIDRef="0" nextStyleIDRef="21" langID="1042" lockForm="0"/>')
        header.append('    </hh:styles>')

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
    parser.add_argument('--packaging', choices=['opf','headref'], default='opf', help='content.hpf 패키징 방식 선택')
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
