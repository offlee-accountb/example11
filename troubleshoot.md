# Troubleshooting Log

This file collects issues, root causes, fixes, and decisions while stabilizing the MD → HWPX converter.

## 2025-11-03 — HWPX packaging and open failures
- Symptom: Hanword showed “손상된 파일입니다” / opened as raw ZIP (“PK…”) or failed to read.
- Root causes and fixes:
  - mimetype must be first and uncompressed.
    - Fix: write `mimetype` as the first ZIP entry with `application/hwp+zip` and ZIP_STORED.
  - Rootfile media-type mismatch.
    - Fix: use `META-INF/container.xml` with rootfile media-type `application/hwpml-package+xml` (per sample).
  - content.hpf structure not recognized.
    - Fix: switch to OPF-style package (`<opf:package>` with metadata/manifest/spine) and list header/section/settings.
  - Missing meta files.
    - Fix: add `META-INF/manifest.xml` (minimal ODF manifest) and `META-INF/container.rdf` (Header/Section types), plus `settings.xml`.
  - Header counts mismatch.
    - Fix: align `itemCnt` in `header.xml` with actual `charPr`/`paraPr` entries; add italic charPr; ensure IDs referenced by runs exist.

## 2025-11-03 — Page settings injection broke file
- Symptom: “파일을 읽거나 저장하는데 오류가 있습니다.” when opening.
- Change that caused it: Injecting `<hp:secPr>` inside a paragraph at the top of `section0.xml` without full control-run structure.
- Root cause: Hanword expects `secPr` to appear within a specific control run (with ctrl/lineseg etc.) consistent with HWPMl; the minimal insertion was invalid.
- Fix: Revert the `secPr` injection. Keep section body simple (paragraphs only) until we reproduce the proper control structure from a template.
- Next step: Implement a “template-driven” section prolog.
  - Approach: load a minimal `secPr`+ctrl block from a known-good template (e.g., `target1.hwpx`) and splice before document content.
  - Only then apply page margins (A4 portrait, top/bottom 15mm, left/right 20mm, header/footer 10mm).

## 2025-11-03 — Inline formatting (Bold/Italic)
- Decision: Preserve MD bold/italic via character styles.
- Implementation: map `**text**` → charPr 23 (bold), `*text*` → charPr 45 (italic), code → charPr 44.
- Header update: ensure charPr 45 (italic) exists and `itemCnt` matches.

## Open items / TODOs
- Table support: parse MD tables and emit `hp:tbl` with header/body cell styles.
- Marker-based paragraph mapping (e.g., `□ Body1`, `○ Bullet1`).
- YAML style guide loader: read `style_guide.yaml` and map md → para/char + transitions.
- Template merging: inject rendered content into an existing HWPX template (placeholders).

## 2025-11-04 — Style textbook mapping phase 1
- Added synthetic styles based on `style_textbook.md` guidance.
- Implemented marker detection: `<주제목>`, `□`, `◦`, indented `-`, `*`, `<강조>`.
- Created new char/para styles (IDs 401–406, 301–306) with fonts HY헤드라인M, 휴먼명조, 맑은 고딕 and predefined spacing.
- Updated inline bold/italic handling to use new style IDs.
- Current gaps: main title/강조 표 구조 미구현, 들여쓰기/줄바꿈 세부 제어, 페이지 여백은 템플릿 기반 control block 필요.

## Validation checklist
- Zip entries: `mimetype` first/stored; meta files present; `Contents/content.hpf`, `Contents/header.xml`, `Contents/section0.xml` present.
- Header IDs: all `charPrIDRef` / `paraPrIDRef` referenced in section exist in header.
- Hanword (2020+) opens file via File → Open (not text editor association).
