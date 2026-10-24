"""Fill the Apart template (unpacked in SRC) with content.py; write the unpacked result to DST.

Rebuild the submission (needs python3 with lxml and Pillow):
  unzip -q docs/submission/template.docx -d /tmp/tpl && find /tmp/tpl -type l -delete
  python3 docs/submission/build_report.py /tmp/tpl /tmp/out
  (cd /tmp/out && zip -qXr ../report_submission.docx .)
"""
import copy, os, re, shutil, sys
from xml.sax.saxutils import escape
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import content as C

SRC, DST = sys.argv[1], sys.argv[2]
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)

WNS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = "{%s}" % WNS
NSDECL = ('xmlns:w="%s" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
          'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
          'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
          'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"' % WNS)
FONT = '<w:rFonts w:ascii="Old Standard TT" w:cs="Old Standard TT" w:eastAsia="Old Standard TT" w:hAnsi="Old Standard TT"/>'
MONO = '<w:rFonts w:ascii="Courier New" w:cs="Courier New" w:eastAsia="Courier New" w:hAnsi="Courier New"/>'

doc_path = os.path.join(DST, "word", "document.xml")
tree = etree.parse(doc_path)
body = tree.getroot().find(W + "body")


def frag(xml):
    return etree.fromstring("<root %s>%s</root>" % (NSDECL, xml))[0]


TOKEN = re.compile(r"(\*\*.+?\*\*|\[\[HL:.+?\]\](?!\])|(?<!\*)\*[^*\s][^*]*?\*(?!\*))")


def runs(text, size=None, italic=False, bold=False, mono=False):
    out = []
    for part in TOKEN.split(text):
        if not part:
            continue
        b, i, hl = bold, italic, False
        if part.startswith("**") and part.endswith("**"):
            part, b = part[2:-2], True
        elif part.startswith("[[HL:"):
            part, hl = part[5:-2], True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            part, i = part[1:-1], True
        rpr = (MONO if mono else FONT) + ('<w:b w:val="1"/><w:bCs w:val="1"/>' if b else "") + \
              ('<w:i w:val="1"/><w:iCs w:val="1"/>' if i else "") + \
              ('<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (size, size) if size else "") + \
              ('<w:highlight w:val="yellow"/>' if hl else "")
        lines = part.split("\n")
        t = '<w:br/>'.join('<w:t xml:space="preserve">%s</w:t>' % escape(l) for l in lines)
        out.append("<w:r><w:rPr>%s</w:rPr>%s</w:r>" % (rpr, t))
    return "".join(out)


def para(text, jc="both", after=120, before=0, size=None, italic=False, bold=False, mono=False,
         num=None, keep_next=False, ind=None):
    ppr = ""
    if keep_next:
        ppr += "<w:keepNext/>"
    if num is not None:
        ppr += '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="%d"/></w:numPr>' % num
    ppr += '<w:spacing w:before="%d" w:after="%d"/>' % (before, after)
    if num is not None:
        ppr += '<w:ind w:left="720" w:hanging="360"/>'
    elif ind:
        ppr += ind
    ppr += '<w:jc w:val="%s"/>' % jc
    return frag("<w:p><w:pPr>%s</w:pPr>%s</w:p>" % (ppr, runs(text, size, italic, bold, mono)))


def heading3(text):
    return frag('<w:p><w:pPr><w:pStyle w:val="Heading3"/><w:keepNext/><w:spacing w:before="200" w:after="60"/></w:pPr>'
                '%s</w:p>' % runs(text, 26, bold=True))


def table(caption, header, rows, widths):
    out = [para(caption, jc="left", size=18, italic=True, after=60, before=120, keep_next=True)]
    border = "".join('<w:%s w:val="single" w:sz="4" w:space="0" w:color="000000"/>' % s
                     for s in ("top", "left", "bottom", "right", "insideH", "insideV"))
    grid = "".join('<w:gridCol w:w="%d"/>' % w for w in widths)

    def row(cells, head):
        tcs = []
        for c, w in zip(cells, widths):
            shd = '<w:shd w:val="clear" w:color="auto" w:fill="E7E6E6"/>' if head else ""
            p = ('<w:p><w:pPr>%s<w:spacing w:before="20" w:after="20" w:line="240" w:lineRule="auto"/></w:pPr>%s</w:p>'
                 % ("<w:keepNext/>" if head else "", runs(c, 17, bold=head)))
            tcs.append('<w:tc><w:tcPr><w:tcW w:w="%d" w:type="dxa"/>%s</w:tcPr>%s</w:tc>' % (w, shd, p))
        trpr = '<w:trPr><w:cantSplit/>%s</w:trPr>' % ('<w:tblHeader/>' if head else "")
        return "<w:tr>%s%s</w:tr>" % (trpr, "".join(tcs))

    tbl = ('<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>%s</w:tblBorders>'
           '<w:tblLayout w:type="fixed"/><w:tblCellMar><w:left w:w="70" w:type="dxa"/><w:right w:w="70" w:type="dxa"/>'
           '</w:tblCellMar></w:tblPr><w:tblGrid>%s</w:tblGrid>%s%s</w:tbl>'
           % (sum(widths), border, grid, row(header, True), "".join(row(r, False) for r in rows)))
    out.append(frag(tbl))
    out.append(para("", after=0))
    return out


media = []


def figure(path, caption):
    from PIL import Image
    n = len(media) + 1
    name = "image%d.png" % n
    media.append((path, name))
    wpx, hpx = Image.open(path).size
    cx = int(6.0 * 914400)
    cy = int(cx * hpx / wpx)
    rid = "rIdImg%d" % n
    drawing = (
        '<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/>'
        '<wp:docPr id="%d" name="Figure %d"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
        '<pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing>' % (cx, cy, 1000 + n, n, 1000 + n, name, rid, cx, cy))
    return [frag('<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="60"/><w:jc w:val="center"/></w:pPr>'
                 '<w:r>%s</w:r></w:p>' % drawing),
            para(caption, jc="both", size=18, italic=True, after=160)]


def blocks(items):
    out = []
    for b in items:
        kind = b[0]
        if kind == "p":
            out.append(para(b[1]))
        elif kind == "h3":
            out.append(heading3(b[1]))
        elif kind == "bullets":
            out += [para(x, num=3, after=60) for x in b[1]]
        elif kind == "numbered":
            out += [para(x, num=5, after=60) for x in b[1]]
        elif kind == "table":
            out += table(*b[1:])
        elif kind == "figure":
            out += figure(*b[1:])
        elif kind == "code":
            out.append(para(b[1], jc="left", size=15, mono=True, after=120,
                            ind='<w:ind w:left="360" w:right="360"/>'))
        else:
            raise ValueError(kind)
    return out


def text_of(e):
    return "".join(e.itertext())


# ---- title block ----
title_tbl = body[1]
for t in title_tbl.iter(W + "t"):
    if t.text == "PROJECT TITLE":
        t.text = C.TITLE
authors_done = False
for p in title_tbl.iter(W + "p"):
    s = text_of(p)
    m = re.match(r"Author name (\d)Affiliation", s)
    if not m:
        continue
    r = p.find(W + "r")
    for t in r.findall(W + "t"):
        t.text = ""
    if m.group(1) == "1":
        ts = r.findall(W + "t")
        ts[0].text, ts[1].text = "[Your name]", "[Affiliation]"
        rpr = r.find(W + "rPr")
        rpr.find(W + "rtl").addprevious(etree.fromstring('<w:highlight xmlns:w="%s" w:val="yellow"/>' % WNS))
    else:
        for br in r.findall(W + "br"):
            r.remove(br)
# one author: first author cell spans the row; drop the other author cells and the second author row
for tr in list(title_tbl.iter(W + "tr")):
    tcs = tr.findall(W + "tc")
    s = text_of(tr)
    if "[Your name]" in s and len(tcs) == 3 and "Abstract" not in s:
        for tc in tcs[1:]:
            tr.remove(tc)
        tcpr = tcs[0].find(W + "tcPr")
        tcpr.insert(0, frag('<w:gridSpan w:val="3"/>'))
    elif len(tcs) == 3 and not s.strip() and tr.getparent().find(W + "tblGrid") is not None \
            and len(tr.getparent().find(W + "tblGrid").findall(W + "gridCol")) == 3 and "Abstract" not in s:
        tr.getparent().remove(tr)
for p in title_tbl.iter(W + "p"):
    if "Summarize your project" in text_of(p):
        ppr = p.find(W + "pPr")
        for r in p.findall(W + "r"):
            p.remove(r)
        u = ppr.find(W + "rPr/" + W + "u")
        if u is not None:
            u.getparent().remove(u)
        p.extend(list(frag("<w:p>%s</w:p>" % runs(C.ABSTRACT, 20))))

# ---- remove the "How to use this template" box ----
body.remove(body[3])

# ---- body sections: drop guidance, keep Heading2s, insert content ----
fill = dict(C.SECTIONS)
fill["Code and Data"] = [("bullets", C.CODE_AND_DATA)]
fill["Author Contributions"] = [("p", C.AUTHOR_CONTRIB)]
fill["References"] = None  # numbered refs below
fill["Appendix"] = C.APPENDIX
fill["LLM Usage Statement"] = [("p", C.LLM_USAGE)]
rename = {"Author Contributions (optional)": "Author Contributions", "Appendix (optional)": "Appendix"}

children = list(body)
start = next(i for i, e in enumerate(children) if text_of(e).strip() == "1. Introduction")
for e in children[start:]:
    if etree.QName(e).localname == "sectPr":
        continue
    st = e.find(W + "pPr/" + W + "pStyle")
    if st is not None and st.get(W + "val") == "Heading2":
        continue
    body.remove(e)

for h in [e for e in body if e.find(W + "pPr/" + W + "pStyle") is not None
          and e.find(W + "pPr/" + W + "pStyle").get(W + "val") == "Heading2"]:
    name = text_of(h).strip()
    if name in rename:
        ts = h.findall(".//" + W + "t")
        ts[0].text = rename[name]
        for t in ts[1:]:
            t.text = ""
        name = rename[name]
    if name not in fill:
        continue
    if name == "Appendix":
        h.find(W + "pPr").insert(1, frag('<w:pageBreakBefore/>'))
    new = ([para(x, jc="left", num=1, after=60) for x in C.REFS] if name == "References" else blocks(fill[name]))
    anchor = h
    for e in new:
        anchor.addnext(e)
        anchor = e

tree.write(doc_path, xml_declaration=True, encoding="UTF-8", standalone=True)

# ---- media, rels, content types ----
os.makedirs(os.path.join(DST, "word", "media"), exist_ok=True)
rels_path = os.path.join(DST, "word", "_rels", "document.xml.rels")
rels = open(rels_path).read()
for i, (src, name) in enumerate(media, 1):
    shutil.copy(src, os.path.join(DST, "word", "media", name))
    rels = rels.replace("</Relationships>",
                        '<Relationship Id="rIdImg%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
                        'Target="media/%s"/></Relationships>' % (i, name))
open(rels_path, "w").write(rels)
ct_path = os.path.join(DST, "[Content_Types].xml")
ct = open(ct_path).read()
if 'Extension="png"' not in ct:
    ct = ct.replace("<Default ", '<Default ContentType="image/png" Extension="png"/><Default ', 1)
open(ct_path, "w").write(ct)
print("ok", len(media), "images")
