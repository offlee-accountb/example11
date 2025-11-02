#!/usr/bin/env python3
"""
Extract core styles from an HWPX package into a concise Markdown report.

Reads:
- Contents/header.xml (char/para styles, fonts)
- Contents/section*.xml (usage counts)

Usage:
  python tools/extract_hwpx_styles.py target1.hwpx > style_report_target1.md
  # or
  python tools/extract_hwpx_styles.py target1.hwpx -o style_report_target1.md
"""

import argparse
import collections
import io
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {
    'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
    'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
}


def _read_xml_from_zip(zf: zipfile.ZipFile, path: str) -> ET.Element:
    data = zf.read(path)
    # Try utf-8 first, fallback to utf-16
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        text = data.decode('utf-16')
    return ET.fromstring(text)


def extract_fonts(head_root: ET.Element):
    fonts = {}
    for font in head_root.findall('.//hh:fontfaces//hh:font', NS):
        fid = font.get('id')
        face = font.get('face')
        if fid is not None:
            fonts[int(fid)] = face
    return fonts


def extract_char_styles(head_root: ET.Element, fonts):
    results = []
    for pr in head_root.findall('.//hh:charProperties/hh:charPr', NS):
        item = {
            'id': int(pr.get('id', '0')),
            'height': pr.get('height'),
            'textColor': pr.get('textColor'),
            'bold': pr.find('hh:bold', NS) is not None,
            'italic': pr.find('hh:italic', NS) is not None,
            'underline': None,
            'font_hangul': None,
            'font_latin': None,
        }
        und = pr.find('hh:underline', NS)
        if und is not None:
            item['underline'] = und.get('type')
        fref = pr.find('hh:fontRef', NS)
        if fref is not None:
            try:
                hid = int(fref.get('hangul')) if fref.get('hangul') is not None else None
                lid = int(fref.get('latin')) if fref.get('latin') is not None else None
            except (TypeError, ValueError):
                hid = lid = None
            item['font_hangul'] = fonts.get(hid) if hid is not None else None
            item['font_latin'] = fonts.get(lid) if lid is not None else None
        results.append(item)
    results.sort(key=lambda x: x['id'])
    return results


def extract_para_styles(head_root: ET.Element):
    results = []
    for pr in head_root.findall('.//hh:paraProperties/hh:paraPr', NS):
        item = {
            'id': int(pr.get('id', '0')),
            'align': None,
            'lineSpacing': None,
            'indent': None,
            'spaceBefore': None,
            'spaceAfter': None,
        }
        align = pr.find('hh:align', NS)
        if align is not None:
            item['align'] = align.get('horizontal')
        lsp = pr.find('hh:lineSpacing', NS)
        if lsp is not None:
            item['lineSpacing'] = {
                'type': lsp.get('type'),
                'value': lsp.get('value')
            }
        margin = pr.find('hh:margin', NS)
        if margin is not None:
            intent = margin.find('hc:intent', NS)
            if intent is not None:
                item['indent'] = intent.get('value')
        # Some docs use explicit space before/after
        sb = pr.find('hc:spaceBefore', NS)
        sa = pr.find('hc:spaceAfter', NS)
        if sb is not None:
            item['spaceBefore'] = sb.get('value')
        if sa is not None:
            item['spaceAfter'] = sa.get('value')
        results.append(item)
    results.sort(key=lambda x: x['id'])
    return results


def extract_usage(zf: zipfile.ZipFile):
    para_count = collections.Counter()
    char_count = collections.Counter()
    for name in zf.namelist():
        if name.startswith('Contents/') and name.lower().endswith('.xml') and 'section' in name.lower():
            root = _read_xml_from_zip(zf, name)
            for p in root.findall('.//hp:p', NS):
                pid = p.get('paraPrIDRef')
                if pid:
                    para_count[int(pid)] += 1
                for run in p.findall('.//hp:run', NS):
                    cid = run.get('charPrIDRef')
                    if cid:
                        char_count[int(cid)] += 1
    return para_count, char_count


def generate_report(hwpx_path: str) -> str:
    with zipfile.ZipFile(hwpx_path) as zf:
        head_root = _read_xml_from_zip(zf, 'Contents/header.xml')
        fonts = extract_fonts(head_root)
        chars = extract_char_styles(head_root, fonts)
        paras = extract_para_styles(head_root)
        para_use, char_use = extract_usage(zf)

    out = io.StringIO()
    out.write(f"# Style Report for {hwpx_path}\n\n")
    out.write("## Character Styles (hh:charPr)\n")
    for c in chars:
        use = char_use.get(c['id'], 0)
        out.write(f"- id {c['id']}: height={c['height']}, color={c['textColor']}, "
                  f"bold={c['bold']}, italic={c['italic']}, underline={c['underline']}, "
                  f"hangulFont={c['font_hangul']} latinFont={c['font_latin']} (used {use} runs)\n")
    out.write("\n## Paragraph Styles (hh:paraPr)\n")
    for p in paras:
        use = para_use.get(p['id'], 0)
        lsp = p['lineSpacing'] or {}
        out.write(
            f"- id {p['id']}: align={p['align']}, lineSpacing={lsp.get('type')}/{lsp.get('value')}, "
            f"indent={p['indent']}, spaceBefore={p['spaceBefore']}, spaceAfter={p['spaceAfter']} (used {use} paras)\n"
        )

    # Quick guess for mappings: most-used para/char
    if para_use:
        common_para = para_use.most_common(5)
        out.write("\n## Heuristic Suggestions\n")
        out.write("- Common paragraph styles: " + ", ".join([f"{pid}({cnt})" for pid, cnt in common_para]) + "\n")
    if char_use:
        common_char = char_use.most_common(5)
        out.write("- Common character styles: " + ", ".join([f"{cid}({cnt})" for cid, cnt in common_char]) + "\n")

    out.write("\n## Notes\n")
    out.write("- Use this as input to craft a style_guide.yaml with explicit mappings.\n")
    out.write("- Government doc quirks (leading spaces, transition spacing) should be captured in the style guide.\n")
    return out.getvalue()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('hwpx', help='Path to .hwpx file')
    ap.add_argument('-o', '--output', help='Output report path (md). If omitted, prints to stdout')
    args = ap.parse_args()

    try:
        report = generate_report(args.hwpx)
    except KeyError as e:
        print(f"Missing expected entry in package: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
    else:
        print(report)


if __name__ == '__main__':
    main()

