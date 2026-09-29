#!/usr/bin/env python3
"""Datenextraktion für die Schiri App 2026.

Erzeugt die in index.html eingebetteten Daten-Konstanten aus den offiziellen
Quelldateien und kann sie direkt in index.html einsetzen.

Benötigt: python3, openpyxl, Pillow sowie poppler-utils (pdftotext, pdftoppm).

Quelldateien (nicht Teil des Repos, bei DBB/NBV beziehen):
  - DBB_Schiedsrichter_Fragenkataloge_2026_*.xlsx
      Tab 1 "DBB Regelfragen 2026"  -> QUESTIONS   (Zeilen R-1..R-198)
      Tab 2 "DBB KR-Fragen 2026"    -> KRQUESTIONS (Zeilen K-1..K-142)
      Spalten: Nr. | Frage | J | N | Antwort | Art.
  - OffizielleBasketballRegeln_2026_*.pdf  -> RULES, SIGNALS, SIGPAGES, BPAGES
  - FEES (NBV-Gebührenkatalog Punkt 4.3) wird nicht extrahiert, sondern als
    kleine Tabelle direkt im JS gepflegt (const FEES in index.html).

Aufrufe:
  python3 tools/extract_data.py fragen  KATALOG.xlsx        # schreibt fragen.json + kr_fragen.json
  python3 tools/extract_data.py regeln  REGELN.pdf          # schreibt artikel.json
  python3 tools/extract_data.py bilder  REGELN.pdf          # schreibt sig_*.jpg, anhangA-*.webp, anhangB-*.webp
  python3 tools/extract_data.py inject  index.html          # ersetzt die const-Zeilen durch die erzeugten Dateien
"""
import base64
import glob
import json
import re
import subprocess
import sys


def clean(s):
    if s is None:
        return ''
    return re.sub(r'\s+', ' ', str(s).replace('\xa0', ' ')).strip()


def extract_fragen(xlsx):
    import openpyxl
    wb = openpyxl.load_workbook(xlsx, read_only=True)
    for sheet_idx, prefix, out in [(0, 'R', 'fragen.json'), (1, 'K', 'kr_fragen.json')]:
        ws = wb.worksheets[sheet_idx]
        qs = []
        for r in ws.iter_rows(values_only=True):
            nr = clean(r[0])
            if not re.match(rf'^{prefix}-\d+$', nr):
                continue
            j, n = clean(r[2]).lower() == 'x', clean(r[3]).lower() == 'x'
            assert j != n, f'{nr}: J/N-Spalte nicht eindeutig'
            qs.append({'nr': nr, 'q': clean(r[1]), 'a': j, 'e': clean(r[4]), 'art': clean(r[5])})
        json.dump(qs, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'{out}: {len(qs)} Fragen')


def _clean_pdf_lines(lines):
    out = []
    for l in lines:
        l = l.replace('\f', '').rstrip()
        if re.match(r'^\s*\d+\s*$', l) or re.match(r'^\s*REGEL [IVX]+', l):
            continue
        lead = len(l) - len(l.lstrip(' '))
        body = re.sub(r' {2,}', ' ', l.strip())
        out.append(' ' * (min(lead // 4, 3) * 2) + body if body else '')
    return re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).strip('\n')


def extract_regeln(pdf):
    """Artikel 1-51 + Anhang B + Anhang C als artikel.json."""
    txt = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
    lines = txt.split('\n')
    # Überschriften im Fließtext finden (TOC überspringen: erst ab dem 2. Vorkommen von "Artikel 1")
    starts, anh = [], {}
    seen_toc = 0
    for i, l in enumerate(lines):
        s = l.replace('\f', '').strip()
        m = re.match(r'^Artikel (\d+)\s+(\S.*)$', s)
        if m and int(m.group(1)) == 1:
            seen_toc += 1
        if m and seen_toc >= 2:
            starts.append((i, m.group(1), m.group(2).strip()))
        for key in ('A', 'B', 'C', 'D'):
            if s.startswith(f'Anhang {key}') and seen_toc >= 2 and key not in anh:
                anh[key] = i
    arts = {}
    ends = [s[0] for s in starts[1:]] + [anh['A']]
    for (i, num, title), end in zip(starts, ends):
        arts[num] = {'t': title, 'x': _clean_pdf_lines(lines[i + 1:end])}
    arts['B'] = {'t': 'Anschreibebogen (Anhang B)', 'x': _clean_pdf_lines(lines[anh['B'] + 1:anh['C']])}
    arts['C'] = {'t': 'Verfahren im Falle eines Protests (Anhang C)', 'x': _clean_pdf_lines(lines[anh['C'] + 1:anh['D']])}
    json.dump(arts, open('artikel.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'artikel.json: {len(arts)} Einträge (1-51, B, C)')


def extract_bilder(pdf):
    """Handzeichen (S. 72-78, Ausschnitte S. 77) und Anschreibebogen-Bilder (S. 79-82, 89-91)."""
    from PIL import Image
    subprocess.run(['pdftoppm', '-f', '72', '-l', '78', '-r', '120', '-jpeg', '-jpegopt', 'quality=78', pdf, 'anhangA'], check=True)
    subprocess.run(['pdftoppm', '-f', '79', '-l', '91', '-r', '110', '-jpeg', '-jpegopt', 'quality=75', pdf, 'anhangB'], check=True)
    for f in glob.glob('anhangA-0*.jpg') + glob.glob('anhangB-0*.jpg'):
        Image.open(f).save(f.replace('.jpg', '.webp'), 'WEBP', quality=72, method=6)
    # Foul-Handzeichen-Ausschnitte von S. 77 (Koordinaten bei 150 dpi)
    subprocess.run(['pdftoppm', '-f', '77', '-l', '77', '-r', '150', '-png', pdf, 's77hi'], check=True)
    img = Image.open('s77hi-077.png')
    for name, box in {'technisches-foul': (395, 172, 630, 610),
                      'disruptive-foul': (645, 172, 885, 610),
                      'flagrant-foul': (895, 172, 1140, 610)}.items():
        img.crop(box).convert('RGB').save(f'sig_{name}.jpg', quality=82, optimize=True)
    print('Bilder erzeugt: anhangA-*.webp, anhangB-*.webp, sig_*.jpg')


def _data_uri(path, mime):
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()


def inject(index_html):
    """Ersetzt die const-Zeilen in index.html durch die erzeugten Datendateien."""
    html = open(index_html, encoding='utf-8').read()

    def esc(js):  # </ in JSON-Strings gegen </script>-Abbruch schützen
        return js.replace('</', '<\\/')

    consts = {}
    if glob.glob('fragen.json'):
        consts['QUESTIONS'] = esc(open('fragen.json', encoding='utf-8').read())
    if glob.glob('kr_fragen.json'):
        consts['KRQUESTIONS'] = esc(open('kr_fragen.json', encoding='utf-8').read())
    if glob.glob('artikel.json'):
        consts['RULES'] = esc(open('artikel.json', encoding='utf-8').read())
    if glob.glob('sig_*.jpg'):
        consts['SIGNALS'] = json.dumps({k: _data_uri(f'sig_{n}.jpg', 'image/jpeg') for k, n in
                                        [('tech', 'technisches-foul'), ('disruptive', 'disruptive-foul'), ('flagrant', 'flagrant-foul')]})
    if glob.glob('anhangA-0*.webp'):
        consts['SIGPAGES'] = json.dumps([_data_uri(f, 'image/webp') for f in sorted(glob.glob('anhangA-0*.webp'))])
    if glob.glob('anhangB-0*.webp'):
        pages = [f'anhangB-0{p}.webp' for p in (79, 80, 81, 82, 89, 90, 91)]
        consts['BPAGES'] = json.dumps([_data_uri(f, 'image/webp') for f in pages])

    for name, value in consts.items():
        pattern = re.compile(rf'^const {name} = .*?;$', re.M)
        assert pattern.search(html), f'const {name} nicht gefunden'
        html = pattern.sub(lambda m: f'const {name} = {value};', html, count=1)
        print(f'const {name} ersetzt')
    open(index_html, 'w', encoding='utf-8').write(html)
    print(f'{index_html} aktualisiert ({len(html) // 1024} KB)')


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)
    cmd, arg = sys.argv[1], sys.argv[2]
    {'fragen': extract_fragen, 'regeln': extract_regeln, 'bilder': extract_bilder, 'inject': inject}[cmd](arg)
