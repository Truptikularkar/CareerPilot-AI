# CareerPilot AI — One-Page ATS Resume Specification

## 1. Specification Objective

For early-to-mid career professionals (~1.9 to 3 years of experience), hiring managers and Applicant Tracking Systems (ATS) strongly prefer a **concise, high-impact, single-page resume**. 

CareerPilot enforces a strict **One-Page ATS Target** across both PDF and DOCX exports, avoiding multi-page spills without compromising readability, ATS parser compatibility, or factual grounding.

---

## 2. Layout & Styling Standards

| Dimension | Specification | Implementation Detail |
| :--- | :--- | :--- |
| **Page Count** | **Strictly 1 Page** | Enforced via content budgeting and adaptive ReportLab spacing. |
| **Page Format** | Standard Letter (8.5 × 11 in) | $612 \times 792$ pt canvas. |
| **Margins** | Standard $0.42$ in ($30.24$ pt) | Uniform left, right, top, and bottom margins. |
| **Layout Structure** | **Single-Column Linear** | No tables, no multi-column floats, no text boxes. |
| **Typography (PDF)** | Helvetica / Helvetica-Bold | Clean vector glyphs with 100% extractable/searchable text. |
| **Typography (DOCX)**| Calibri / Calibri-Bold | Semantic Word hierarchy using standard `List Bullet` styles. |
| **Color Palette** | Navy `#0A2540` & Charcoal `#1A1A1A` | High contrast ratio (>10:1), professional, no background tints. |
| **Section Dividers** | Thin horizontal line ($0.5$ pt) | Clean visual demarcation without breaking ATS parsers. |

---

## 3. One-Page Section Budgeting Matrix

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CANDIDATE HEADER (Name, Email, Phone, Location, Links)   │ ~45 pt
├─────────────────────────────────────────────────────────────┤
│ 2. PROFESSIONAL SUMMARY (Role-targeted, concise narrative)  │ ~60 pt
├─────────────────────────────────────────────────────────────┤
│ 3. TECHNICAL SKILLS (5 compact, categorized bullet groups)  │ ~95 pt
├─────────────────────────────────────────────────────────────┤
│ 4. PROFESSIONAL EXPERIENCE                                  │ ~260 pt
│    • Primary Role: Title, Company, Dates, 4 verified bullets │
│    • Trainee/Prior: Title, Company, Dates, 2 verified bullets│
├─────────────────────────────────────────────────────────────┤
│ 5. KEY PROJECTS (Top 2 JD-relevant projects, 2 bullets each)│ ~140 pt
├─────────────────────────────────────────────────────────────┤
│ 6. EDUCATION (Degree, Field, Institution, Year, Honors)     │ ~35 pt
├─────────────────────────────────────────────────────────────┤
│ 7. CERTIFICATIONS (Compact line with issuer and year)       │ ~30 pt
└─────────────────────────────────────────────────────────────┘
TOTAL HEIGHT: ~665 pt (Fits comfortably within 730 pt printable height)
```

---

## 4. Deterministic Compression & Priority Hierarchy

If user edits or expanded project descriptions cause the content to exceed the 1-page canvas, `PDFResumeExporter` and `BulletSelector` apply intelligent compression in this strict priority order:

1. **Summary Compression**: Remove conversational filler; focus on core value proposition.
2. **Project Selection**: Select the top 2 most JD-relevant projects rather than listing all 4.
3. **Bullet Trimming**: Trim secondary bullets while preserving high-impact metric bullets.
4. **Skills Grouping**: Deduplicate overlapping skill aliases.
5. **Adaptive Micro-Spacing**: If page count $> 1$, automatically adjust font size ($8.8 \rightarrow 8.4$ pt) and margins ($0.42 \rightarrow 0.36$ in) to guarantee a strict 1-page output.

---

## 5. Automated ATS Validation with `PDFValidator`

Every generated PDF is audited programmatically with `PDFValidator` (powered by PyMuPDF) to verify:
- `page_count == 1`
- `total_words >= 350` and `total_characters >= 2000`
- `is_single_column == True`
- `is_searchable == True`
- Complete section heading detection (`SUMMARY`, `SKILLS`, `EXPERIENCE`, `PROJECTS`, `EDUCATION`).
