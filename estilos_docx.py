# -*- coding: utf-8 -*-
"""As pecas de estilo do .docx que o pdf_para_docx.py monta.

Ficam aqui, e nao no conversor, porque sao XML de formato e nao logica de
conversao, e misturar as duas coisas faz o conversor dobrar de tamanho
sem ficar mais claro.

O QUE ELAS RESOLVEM. Um .docx sem styles.xml e sem sectPr abre com o
padrao do Word: fonte da instalacao, margens de carta, sem entrelinha e
sem espaco entre paragrafos, e os titulos indistinguiveis do corpo.
Aqui o documento sai em A4 com margens da ABNT, corpo em Times 12
justificado com entrelinha 1,5, titulos como ESTILOS DE VERDADE (e nao
negrito solto), o que faz o painel de navegacao do Word funcionar, e
notas de rodape como notas, e nao como paragrafos no fim da pagina.
"""

TIPOS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-'
    'package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.'
    'openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
    '<Override PartName="/word/styles.xml" ContentType="application/vnd.'
    'openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
    '<Override PartName="/word/footnotes.xml" ContentType="application/vnd.'
    'openxmlformats-officedocument.wordprocessingml.footnotes+xml"/>'
    "</Types>"
)

RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
    'relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
    'officeDocument/2006/relationships/officeDocument" Target="word/'
    'document.xml"/>'
    "</Relationships>"
)

RELS_DOC = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/'
    'relationships">'
    '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/'
    'officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    '<Relationship Id="rIdFootnotes" Type="http://schemas.openxmlformats.org/'
    'officeDocument/2006/relationships/footnotes" Target="footnotes.xml"/>'
    "</Relationships>"
)

_W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

# Corpo em Times 12, justificado, entrelinha 1,5 (360 vinte-avos de linha
# acima do simples), 6pt depois do paragrafo. Titulos em tres niveis, com
# outlineLvl para o painel de navegacao.
ESTILOS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:styles %s>' % _W +
    '<w:docDefaults><w:rPrDefault><w:rPr>'
    '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>'
    '<w:sz w:val="24"/><w:szCs w:val="24"/><w:lang w:val="pt-BR"/>'
    '</w:rPr></w:rPrDefault></w:docDefaults>'

    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
    '<w:name w:val="Normal"/><w:pPr>'
    '<w:jc w:val="both"/>'
    '<w:spacing w:line="360" w:lineRule="auto" w:after="120"/>'
    '</w:pPr></w:style>'

    '<w:style w:type="paragraph" w:styleId="Title">'
    '<w:name w:val="Title"/><w:basedOn w:val="Normal"/>'
    '<w:pPr><w:jc w:val="center"/><w:spacing w:before="240" w:after="240"/></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>'

    '<w:style w:type="paragraph" w:styleId="Heading1">'
    '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>'
    '<w:pPr><w:outlineLvl w:val="0"/><w:keepNext/>'
    '<w:spacing w:before="360" w:after="180"/><w:jc w:val="left"/></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>'

    '<w:style w:type="paragraph" w:styleId="Heading2">'
    '<w:name w:val="heading 2"/><w:basedOn w:val="Normal"/>'
    '<w:pPr><w:outlineLvl w:val="1"/><w:keepNext/>'
    '<w:spacing w:before="280" w:after="140"/><w:jc w:val="left"/></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>'

    '<w:style w:type="paragraph" w:styleId="Heading3">'
    '<w:name w:val="heading 3"/><w:basedOn w:val="Normal"/>'
    '<w:pPr><w:outlineLvl w:val="2"/><w:keepNext/>'
    '<w:spacing w:before="240" w:after="120"/><w:jc w:val="left"/></w:pPr>'
    '<w:rPr><w:b/><w:i/></w:rPr></w:style>'

    '<w:style w:type="paragraph" w:styleId="FootnoteText">'
    '<w:name w:val="footnote text"/><w:basedOn w:val="Normal"/>'
    '<w:pPr><w:spacing w:line="240" w:lineRule="auto" w:after="0"/></w:pPr>'
    '<w:rPr><w:sz w:val="20"/></w:rPr></w:style>'

    '<w:style w:type="character" w:styleId="FootnoteReference">'
    '<w:name w:val="footnote reference"/>'
    '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>'

    '<w:style w:type="paragraph" w:styleId="Comentario">'
    '<w:name w:val="Comentario da oficina"/><w:basedOn w:val="Normal"/>'
    '<w:pPr><w:spacing w:after="60"/><w:ind w:left="284"/>'
    '<w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="808080"/></w:pBdr>'
    '</w:pPr><w:rPr><w:i/><w:color w:val="595959"/><w:sz w:val="20"/></w:rPr>'
    '</w:style>'

    "</w:styles>"
)

# A4 (11906 x 16838 vinte-avos de ponto) com margens da ABNT: 3cm em cima
# e a esquerda, 2cm embaixo e a direita.
SECT_PR = (
    '<w:sectPr>'
    '<w:pgSz w:w="11906" w:h="16838"/>'
    '<w:pgMar w:top="1701" w:right="1134" w:bottom="1134" w:left="1701" '
    'w:header="709" w:footer="709" w:gutter="0"/>'
    "</w:sectPr>"
)

# As duas notas separadoras que o Word espera existir.
FOOTNOTES_FIXAS = (
    '<w:footnote w:type="separator" w:id="-1"><w:p><w:pPr><w:spacing '
    'w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
    '<w:r><w:separator/></w:r></w:p></w:footnote>'
    '<w:footnote w:type="continuationSeparator" w:id="0"><w:p><w:pPr>'
    '<w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
    '<w:r><w:continuationSeparator/></w:r></w:p></w:footnote>'
)


def footnotes_xml(notas, escapar):
    """notas: lista de (id, texto). Devolve o word/footnotes.xml."""
    partes = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
              "<w:footnotes %s>" % _W, FOOTNOTES_FIXAS]
    for i, texto in notas:
        partes.append(
            '<w:footnote w:id="%d"><w:p><w:pPr><w:pStyle w:val="FootnoteText"/>'
            '</w:pPr><w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr>'
            '<w:footnoteRef/></w:r><w:r><w:t xml:space="preserve"> %s</w:t>'
            "</w:r></w:p></w:footnote>" % (i, escapar(texto)))
    partes.append("</w:footnotes>")
    return "".join(partes).encode("utf-8")
