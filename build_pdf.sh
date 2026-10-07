#!/usr/bin/env bash
# build_pdf.sh — builds the submitted report PDF from track_1a/technical_report.md
# with pandoc + weasyprint, using track_1a/docs/report.css (A4, 2 cm margins, 11 pt).
# WeasyPrint ignores pandoc's LaTeX-style geometry variable, so the page setup lives in the CSS.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT/track_1a"
TMP=".report.build.html"
pandoc technical_report.md --standalone --css docs/report.css -o "$TMP"
weasyprint "$TMP" ArberArifi_Report.pdf
rm -f "$TMP"
PAGES="$(pdftotext ArberArifi_Report.pdf - | tr -cd '\f' | wc -c)"
echo "PDF built: $PAGES pages -> track_1a/ArberArifi_Report.pdf"
