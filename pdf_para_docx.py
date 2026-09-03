#!/usr/bin/env python3
"""
Converte o projeto que chegou em PDF num .docx que o comentar_projeto.py
sabe anotar.

    python pdf_para_docx.py projeto.pdf
    python pdf_para_docx.py projeto.pdf -o projeto.docx
    python pdf_para_docx.py --provar

POR QUE ISTO EXISTE, E QUAL E O PROBLEMA QUE ELE NAO RESOLVE. O aluno
manda o projeto em PDF, e a promessa desta oficina e que o arquivo dele
volte com as sugestoes dentro e sem uma palavra alterada. Num .docx isso
se cumpre ao pe da letra, porque o comentar_projeto.py acha o paragrafo e
escreve so o comentario. Num PDF nao ha o que anotar dessa forma: PDF nao
tem paragrafos, tem linhas posicionadas numa pagina. Entao alguem precisa
reconstruir o texto, e a unica pergunta que importa e QUEM reconstroi.
Aqui quem reconstroi e este programa, lendo a geometria da pagina. Se
fosse o assistente, ele nao copiaria, produziria de novo, e sairia frase
alisada e sinonimo trocado num documento que o aluno vai assinar.

O QUE ELE PRESERVA E O QUE ELE PERDE, dito antes de alguem descobrir
sozinho. Preserva o TEXTO, palavra por palavra, e isso e conferido: o
.docx que sai tem exatamente as mesmas palavras que a extracao, na mesma
ordem, e o programa recusa a escrever se nao tiver. Perde a formatacao
(fonte, negrito, recuo, alinhamento), perde as imagens e as tabelas, e
MOVE AS NOTAS DE RODAPE: elas saem do pe da pagina e viram paragrafos ao
fim daquela pagina, com o numero grudado no comeco, que e como o PDF as
entrega. Numero de pagina solto no rodape e descartado.

COMO ELE DECIDE ONDE UM PARAGRAFO ACABA, que e a unica inferencia que ele
faz. Num texto justificado, a ultima linha de um paragrafo e curta,
porque nao precisa alcancar a margem direita. Entao: linha que termina
antes da margem fecha o paragrafo, e linha que a alcanca continua na
seguinte. E a margem nao e chutada, e medida em cada pagina, pela linha
mais longa dela. Titulos vem em negrito e sao agrupados a parte.

Esse criterio erra em dois casos conhecidos, e eu os digo porque quem
usar precisa saber onde olhar: paragrafo cuja ultima linha por acaso
alcanca a margem gruda no seguinte, e linha curta no meio de um
paragrafo (uma formula, um verso) parte o paragrafo em dois. Nenhum dos
dois altera palavra nenhuma: mudam so onde a divisao cai, e portanto a
numeracao dos localizadores. Confira a numeracao antes de levar as
sugestoes para a conversa.

O QUE ELE NAO CONFERE, e isto e limite e nao defeito: que a extracao
corresponde ao que esta impresso na pagina. Isso depende do PDF (texto
de verdade ou imagem escaneada) e da biblioteca. Se o PDF for digitalizado
sem camada de texto, nao sai nada, e o programa avisa em vez de entregar
um documento vazio.
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Falta o PyMuPDF. Instale com: pip install pymupdf")

# Linha em corpo menor que isto e nota de rodape, e nao texto.
CORPO_MINIMO = 10.5

# Quanto uma linha pode ficar aquem da margem direita e ainda contar
# como linha cheia. Em pontos.
FOLGA_MARGEM = 12.0

# Duas pecas ate esta distancia vertical estao na mesma linha.
TOLERANCIA_LINHA = 3.0

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

TIPOS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-'
    'package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/word/document.xml" ContentType="application/vnd.'
    'openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
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
    'relationships"></Relationships>'
)


def escapar(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# ------------------------------------------------------------------ leitura

def linhas_do_pdf(caminho):
    """Devolve, por pagina, a lista de linhas com o que decide o resto:
    texto, borda direita, se e negrito, e se e corpo ou nota.

    O EXTRATOR PARTE UMA LINHA VISUAL EM VARIAS quando o espacamento
    entre palavras e grande, o que acontece em bloco justificado estreito,
    e a capa de um projeto e sempre um desses. Sem juntar de volta, a capa
    sai em pedacos de uma palavra ("de", "avaliacao", "do"), cada um
    virando um paragrafo, e a numeracao do documento inteiro anda onze
    casas antes de comecar o texto. Entao as pecas que dividem a mesma
    linha de base voltam a ser uma linha so, na ordem da esquerda para a
    direita."""
    doc = fitz.open(caminho)
    paginas = []
    for pagina in doc:
        pecas = []
        for bloco in pagina.get_text("dict")["blocks"]:
            for linha in bloco.get("lines", []):
                trechos = linha.get("spans", [])
                if not trechos:
                    continue
                texto = "".join(t["text"] for t in trechos)
                if not texto.strip():
                    continue
                tamanho = max(t["size"] for t in trechos)
                pecas.append({
                    "texto": texto.strip(),
                    "y": linha["bbox"][1],
                    "x0": linha["bbox"][0],
                    "x1": linha["bbox"][2],
                    "negrito": all("Bold" in t["font"] for t in trechos),
                    "nota": tamanho < CORPO_MINIMO,
                })

        # Mesma linha de base, dentro da tolerancia, e a mesma linha.
        pecas.sort(key=lambda p: (round(p["y"] / TOLERANCIA_LINHA), p["x0"]))
        linhas, atual = [], []

        def fechar_linha():
            if not atual:
                return
            linhas.append({
                "texto": " ".join(p["texto"] for p in atual),
                "y": min(p["y"] for p in atual),
                "x1": max(p["x1"] for p in atual),
                "negrito": all(p["negrito"] for p in atual),
                "nota": all(p["nota"] for p in atual),
            })
            atual.clear()

        for p in pecas:
            if atual and abs(p["y"] - atual[0]["y"]) > TOLERANCIA_LINHA:
                fechar_linha()
            atual.append(p)
        fechar_linha()

        linhas.sort(key=lambda l: l["y"])
        paginas.append(linhas)
    doc.close()
    return paginas


# ------------------------------------------------------------------ juncao

def juntar(pedacos):
    """Junta as linhas de um paragrafo. Palavra partida no fim da linha
    fica junta, sem o espaco."""
    saida = ""
    for p in pedacos:
        if not saida:
            saida = p
        elif saida.endswith("-"):
            saida += p
        else:
            saida += " " + p
    return saida


def so_numero(t):
    return re.fullmatch(r"\d{1,4}", t.strip()) is not None


ABRE_NOTA = re.compile(r"^\d{1,3}[A-ZÀ-Ú]")


def paragrafos_da_pagina(linhas):
    corpo = [l for l in linhas if not l["nota"]]
    notas = [l for l in linhas if l["nota"]]

    # O numero da pagina e a ultima linha, sozinha e so com digitos.
    if corpo and so_numero(corpo[-1]["texto"]):
        corpo = corpo[:-1]
    if not corpo:
        margem = 0.0
    else:
        margem = max(l["x1"] for l in corpo)

    saida, atual, negrito_atual = [], [], None
    def fechar():
        if atual:
            saida.append(juntar(atual))
            atual.clear()

    for l in corpo:
        if negrito_atual is not None and l["negrito"] != negrito_atual:
            fechar()
        negrito_atual = l["negrito"]
        atual.append(l["texto"])
        if l["x1"] < margem - FOLGA_MARGEM:
            fechar()
            negrito_atual = None
    fechar()

    # As notas de rodape, na ordem em que aparecem, uma por numero.
    atual_nota = []
    for l in notas:
        if ABRE_NOTA.match(l["texto"]) and atual_nota:
            saida.append(juntar(atual_nota))
            atual_nota = []
        atual_nota.append(l["texto"])
    if atual_nota:
        saida.append(juntar(atual_nota))

    return saida


def converter(caminho):
    paginas = linhas_do_pdf(caminho)
    paragrafos, linhas = [], []
    for pagina in paginas:
        paragrafos.extend(paragrafos_da_pagina(pagina))
        for l in pagina:
            linhas.append(l)
    return paragrafos, paginas


# ------------------------------------------------------------------ escrita

def documento_xml(paragrafos):
    partes = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
              '<w:document xmlns:w="%s"><w:body>' % NS_W]
    for p in paragrafos:
        partes.append('<w:p><w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
                      % escapar(p))
    partes.append("</w:body></w:document>")
    return "".join(partes).encode("utf-8")


def escrever_docx(paragrafos, saida):
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", TIPOS)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/_rels/document.xml.rels", RELS_DOC)
        z.writestr("word/document.xml", documento_xml(paragrafos))


# ------------------------------------------------------------------ conferencia

def normalizar(s):
    return re.sub(r"\s+", " ", s).strip()


def conferir(paragrafos, paginas):
    """O .docx tem de ter as mesmas palavras que a extracao, na mesma
    ordem. Devolve None se estiver certo, ou a frase do defeito."""
    lidas = []
    for pagina in paginas:
        corpo = [l for l in pagina if not l["nota"]]
        if corpo and so_numero(corpo[-1]["texto"]):
            corpo = corpo[:-1]
        lidas.extend(l["texto"] for l in corpo)
        lidas.extend(l["texto"] for l in pagina if l["nota"])

    a = normalizar(" ".join(lidas)).replace("- ", "-")
    b = normalizar(" ".join(paragrafos)).replace("- ", "-")
    if a == b:
        return None
    for i, (x, y) in enumerate(zip(a.split(), b.split())):
        if x != y:
            return ("a palavra %d mudou: a extracao tem %r e o documento tem %r"
                    % (i + 1, x, y))
    return "o documento tem %d palavras e a extracao tem %d" % (
        len(b.split()), len(a.split()))


def provar():
    """Controle positivo. Conferidor que nunca reprovou nada nao informa
    nada quando fica em silencio."""
    pagina = [
        {"texto": "O problema de pesquisa e este.", "y": 1, "x1": 400,
         "negrito": False, "nota": False},
        {"texto": "A justificativa e aquela.", "y": 2, "x1": 200,
         "negrito": False, "nota": False},
    ]
    bons = ["O problema de pesquisa e este. A justificativa e aquela."]
    casos = [
        ("texto identico", bons, None),
        ("uma palavra trocada",
         ["O problema de pesquisa e esse. A justificativa e aquela."], "reprovar"),
        ("uma palavra a menos",
         ["O problema de pesquisa e este. A justificativa aquela."], "reprovar"),
        ("um paragrafo a menos",
         ["O problema de pesquisa e este."], "reprovar"),
    ]
    ok = True
    for nome, paras, espera in casos:
        r = conferir(paras, [pagina])
        passou = (r is None) if espera is None else (r is not None)
        ok = ok and passou
        print("  %-22s %s" % (nome, ("passou (correto)" if r is None
                                     else "reprovou: " + r)))
    print("\n" + ("O conferidor reprova o que deve reprovar."
                  if ok else "O CONFERIDOR ESTA QUEBRADO. Nao use o resultado."))
    return 0 if ok else 1


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", nargs="?", help="o projeto, em PDF")
    ap.add_argument("-o", "--saida", help="o .docx de saida")
    ap.add_argument("--provar", action="store_true",
                    help="mostra o conferidor reprovando de proposito")
    a = ap.parse_args()

    if a.provar:
        return provar()
    if not a.pdf:
        ap.error("diga qual e o PDF, ou use --provar")

    origem = Path(a.pdf)
    if not origem.is_file():
        sys.exit("nao achei %s" % origem)

    paragrafos, paginas = converter(origem)
    if not paragrafos:
        sys.exit("nao saiu texto nenhum de %s. Se o PDF for digitalizado, "
                 "ele nao tem camada de texto, e este programa nao serve."
                 % origem.name)

    erro = conferir(paragrafos, paginas)
    if erro:
        sys.exit("PAREI: %s\nO texto teria saido diferente do que entrou, e e "
                 "isto que este programa existe para impedir. Nada foi escrito."
                 % erro)

    saida = Path(a.saida) if a.saida else origem.with_suffix(".docx")
    escrever_docx(paragrafos, saida)

    palavras = sum(len(p.split()) for p in paragrafos)
    print("%s: %d paginas, %d paragrafos, %d palavras."
          % (saida.name, len(paginas), len(paragrafos), palavras))
    print("Texto conferido palavra a palavra contra a extracao.")
    print("Formatacao, imagens e tabelas nao vieram; as notas de rodape "
          "viraram paragrafos ao fim de cada pagina.")
    print("Agora: python comentar_projeto.py %s --numerar" % saida.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
