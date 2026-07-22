#!/usr/bin/env python3
"""Expand the Methods/Results source draft into a final markdown and a PDF.

Reads manuscript_formatting/Methods_and_Results_draft.src.md and expands two placeholders:
  [[TABLE <id>]]                 -> a markdown table read from manuscript_formatting/tables/<id>.csv
  [[FIG <relpath> | <caption>]]  -> a markdown image plus an italic caption line

Table cells therefore come straight from the tidy CSVs (no hand-typed numbers). Writes
Methods_and_Results_draft.md at the repo root (relative image paths, GitHub-viewable) and renders
Methods_and_Results_draft.pdf via markdown + xhtml2pdf, resolving image paths from the repo root.

Run: python scripts/render_methods_results.py
Requires: pandas, markdown, xhtml2pdf
"""

import os
import re

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "manuscript_formatting", "sections", "Methods_and_Results_draft.src.md")
TAB = os.path.join(ROOT, "manuscript_formatting", "tables")
OUTDIR = os.path.join(ROOT, "manuscript_formatting", "sections", "draft")
MD_OUT = os.path.join(OUTDIR, "Methods_and_Results_draft.md")
PDF_OUT = os.path.join(OUTDIR, "Methods_and_Results_draft.pdf")
REL = os.path.relpath(ROOT, OUTDIR)                          # "../.." so repo-relative figures resolve


# the six renamed chapter-2 tables keep working from unedited [[TABLE Tn]] placeholders in the draft
OLD_ID_ALIAS = {"T1": "table_2_3", "T2": "table_2_4", "T3": "table_2_5",
                "T9": "table_2_6", "T8": "table_2_7", "T5": "table_2_8"}


def table_md(tid):
    tid = OLD_ID_ALIAS.get(tid, tid)
    df = pd.read_csv(os.path.join(TAB, f"{tid}.csv"))
    # comma-group integer-valued columns for readability
    def fmt(v):
        if isinstance(v, float) and v.is_integer():
            return f"{int(v):,}"
        if isinstance(v, (int,)):
            return f"{v:,}"
        return "" if pd.isna(v) else str(v)
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep = "| " + " | ".join("---" for _ in df.columns) + " |"
    rows = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, sep] + rows)


def expand(text):
    def do_table(m):
        return table_md(m.group(1).strip())

    def do_fig(m):
        body = m.group(1)
        path, _, cap = body.partition("|")
        path = path.strip(); cap = cap.strip()
        # rewrite repo-relative figure paths to be relative to the draft subfolder
        rel = path if (path.startswith("http") or os.path.isabs(path)) else f"{REL}/{path}"
        return f"![{cap}]({rel})\n\n*{cap}*"

    text = re.sub(r"\[\[TABLE\s+([^\]]+)\]\]", do_table, text)
    text = re.sub(r"\[\[FIG\s+(.+?)\]\]", do_fig, text, flags=re.S)
    return text


CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 9pt; line-height: 1.35; color: #111; }
h1 { font-size: 16pt; } h2 { font-size: 13pt; border-bottom: 1px solid #999; padding-bottom: 2px; }
h3 { font-size: 11pt; } h4 { font-size: 10pt; }
em { color: #333; }
table { border-collapse: collapse; width: 100%; margin: 6px 0; }
th, td { font-size: 7.5pt; padding: 2px 4px; text-align: right; }
th { border-top: 1.2px solid #000; border-bottom: 0.6px solid #000; font-weight: bold; }
tr:last-child td { border-bottom: 1.2px solid #000; }
td:first-child, th:first-child { text-align: left; }
img { width: 440pt; margin-top: 6px; }
"""


def to_pdf(md_text):
    import markdown
    from xhtml2pdf import pisa
    html_body = markdown.markdown(md_text, extensions=["tables", "sane_lists"])
    html = f"<html><head><style>{CSS}</style></head><body>{html_body}</body></html>"

    def link_callback(uri, rel):
        # image srcs in the md are relative to the draft subfolder; resolve them from there
        if uri.startswith("http"):
            return uri
        return uri if os.path.isabs(uri) else os.path.normpath(os.path.join(OUTDIR, uri))

    with open(PDF_OUT, "wb") as fh:
        status = pisa.CreatePDF(html, dest=fh, link_callback=link_callback)
    return status.err


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    src = open(SRC).read()
    md = expand(src)
    with open(MD_OUT, "w") as fh:
        fh.write(md)
    print("wrote", MD_OUT)
    err = to_pdf(md)
    print("wrote", PDF_OUT, "(errors:", err, ")")


if __name__ == "__main__":
    main()
