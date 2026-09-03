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

O QUE ELE PRESERVA E O QUE ELE PERDE. Preserva o TEXTO, palavra por
palavra, e isso e conferido: o programa recusa a escrever se o que sai
nao tiver as mesmas palavras da extracao, na mesma ordem. Preserva a
ESTRUTURA em tres coisas: titulos viram estilos de verdade (e nao negrito
solto), o que faz o painel de navegacao do Word funcionar; as notas de
rodape viram notas de rodape, com a chamada no lugar em que ela estava; e
a pagina sai em A4 com margens da ABNT, corpo em Times 12 justificado
com entrelinha 1,5. Perde a formatacao fina (recuo, grifo, versalete),
as imagens e as tabelas. Numero de pagina solto no rodape e descartado.

COMO ELE DECIDE ONDE UM PARAGRAFO ACABA, que e a unica inferencia que ele
faz. Num texto justificado, a ultima linha de um paragrafo e curta,
porque nao precisa alcancar a margem direita. Entao: linha que termina
antes da margem fecha o paragrafo, e linha que a alcanca continua na
seguinte. A margem nao e chutada, e medida em cada pagina, pela linha
mais longa dela.

Esse criterio erra em dois casos conhecidos, e eu os digo porque quem
usar precisa saber onde olhar: paragrafo cuja ultima linha por acaso
alcanca a margem gruda no seguinte, e linha curta no meio de um
paragrafo (uma formula, um verso) parte o paragrafo em dois. Nenhum dos
dois altera palavra nenhuma: mudam so onde a divisao cai, e portanto a
numeracao dos localizadores. Confira a numeracao antes de levar as
sugestoes para a conversa.

COMO ELE ACHA A CHAMADA DA NOTA. Pelo sobrescrito, que o extrator
informa no bit 0 de flags, e nao por expressao regular no texto ja
juntado. A diferenca foi medida: procurando por padrao, a chamada
comia o segundo digito das secoes numeradas, e "6.1 Primeiro eixo"
virava "6." mais uma chamada de nota. O sobrescrito e o que a
tipografia de fato marca, e o conferidor nao pegava esse erro porque
ele confere a divisao em paragrafos, e nao a escrita do XML.

O QUE ELE NAO CONFERE, e isto e limite e nao defeito: que a extracao
corresponde ao que esta impresso. Isso depende do PDF ter camada de
texto. Se for digitalizado, nao sai nada, e o programa avisa em vez de
entregar um documento vazio.
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import estilos_docx as est

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

# Distancia tipica entre duas linhas seguidas, em pontos.
ENTRELINHA = 20.7

MARCA = chr(1)   # delimita a chamada de nota dentro do texto da linha

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# O NUMERO DA NOTA E O TEXTO DELA PODEM VIR SEPARADOS POR ESPACO, e a
# versao anterior exigia que a letra viesse colada ao digito. Foi assim
# que um projeto real perdeu as catorze notas de uma vez: o numero saia
# num span proprio, em corpo 6,5, e a juncao das pecas da linha punha um
# espaco entre ele e o texto, de modo que "12 Aqui, a investigacao" nao
# casava. Sem nota aberta, TODO o texto das notas caiu no corpo, no meio
# do argumento, e as chamadas viraram digito colado a palavra
# ("substituicao administrativa10"), porque a chamada so vira referencia
# quando ha nota com aquele numero.
ABRE_NOTA = re.compile(r"^(\d{1,3})\s?([A-ZÀ-Úa-zà-ú])")
NUMERO_SECAO = re.compile(r"^(\d+)(\.\d+)*\.?\s")


def escapar(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ------------------------------------------------------------------ leitura

def linhas_do_pdf(caminho):
    """Devolve, por pagina, a lista de linhas.

    O EXTRATOR PARTE UMA LINHA VISUAL EM VARIAS quando o espacamento entre
    palavras e grande, o que acontece em bloco justificado estreito, e a
    capa de um projeto e sempre um desses. Sem juntar de volta, a capa sai
    em pedacos de uma palavra, cada um virando um paragrafo, e a numeracao
    do documento inteiro anda antes de o texto comecar."""
    doc = fitz.open(caminho)
    paginas = []
    for pagina in doc:
        pecas = []
        for bloco in pagina.get_text("dict")["blocks"]:
            for linha in bloco.get("lines", []):
                trechos = linha.get("spans", [])
                if not trechos:
                    continue
                # A CHAMADA DE NOTA E UM SPAN SOBRESCRITO, e o extrator diz
                # isso no bit 0 de flags. Marca-la aqui e o que impede o
                # erro que se mediu: procurar a chamada por expressao
                # regular no texto ja juntado comia o segundo digito das
                # secoes numeradas, e "6.1" virava "6." mais uma chamada.
                partes_texto = []
                for t in trechos:
                    if t["flags"] & 1 and t["text"].strip().isdigit():
                        partes_texto.append(MARCA + t["text"].strip() + MARCA)
                    else:
                        partes_texto.append(t["text"])
                texto = "".join(partes_texto)
                if not texto.strip():
                    continue
                # O NEGRITO SE DECIDE SEM OS ESPACOS. Todo titulo deste PDF
                # termina num span de espaco que nao e negrito, e exigir
                # negrito em todos os spans reprovava o titulo inteiro: era
                # por isso que so nove de vinte e poucos eram detectados.
                cheios = [t for t in trechos if t["text"].strip()]
                pecas.append({
                    "texto": texto.strip(),
                    "y": linha["bbox"][1],
                    "x0": linha["bbox"][0],
                    "x1": linha["bbox"][2],
                    "negrito": bool(cheios) and all(t["flags"] & 16 for t in cheios),
                    "nota": max(t["size"] for t in cheios) < CORPO_MINIMO,
                })

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


def estilo_do_titulo(texto, primeira_pagina):
    """O nivel sai da numeracao da secao, que e o que o autor escreveu.
    Sem numeracao, na capa e titulo do trabalho, e no corpo e nivel 1."""
    m = NUMERO_SECAO.match(texto)
    if m:
        return "Heading2" if m.group(2) else "Heading1"
    return "Title" if primeira_pagina else "Heading1"


def itens_da_pagina(linhas, primeira):
    """Devolve (itens, notas). Item e (estilo, texto); nota e (numero, texto)."""
    corpo = [l for l in linhas if not l["nota"]]
    linhas_nota = [l for l in linhas if l["nota"]]

    if corpo and so_numero(corpo[-1]["texto"]):
        corpo = corpo[:-1]
    margem = max((l["x1"] for l in corpo), default=0.0)

    itens, atual, negrito_atual = [], [], None

    def fechar():
        if not atual:
            return
        texto = juntar(atual)
        estilo = (estilo_do_titulo(sem_marca(texto), primeira) if negrito_atual
                  else "Normal")
        itens.append((estilo, texto))
        atual.clear()

    anterior_y = None
    for l in corpo:
        if negrito_atual is not None and l["negrito"] != negrito_atual:
            fechar()
        # DOIS TITULOS SEGUIDOS NAO SAO UM TITULO SO. Sem isto, "4.
        # OBJETIVOS" e "4.1. Objetivo geral", que sao negrito um atras do
        # outro, saiam grudados num paragrafo. Fecha-se quando o negrito
        # recomeca numerado, e quando o salto vertical passa de uma linha
        # e meia, que e o espaco que separa blocos.
        if atual and l["negrito"] and negrito_atual:
            salto = anterior_y is not None and (l["y"] - anterior_y) > 1.6 * ENTRELINHA
            if NUMERO_SECAO.match(sem_marca(l["texto"])) or salto:
                fechar()
        anterior_y = l["y"]
        negrito_atual = l["negrito"]
        atual.append(l["texto"])
        # A REGRA DA MARGEM CURTA VALE PARA O CORPO, E NAO PARA O TITULO.
        # Titulo e alinhado a esquerda, entao TODA linha dele termina antes
        # da margem, e aplicar a regra ali partia em dois cada titulo de
        # duas linhas: "6.1 Primeiro eixo..." de um lado e "dissuasoria"
        # sozinha do outro, como se fosse outra secao. Titulo se fecha
        # quando o negrito acaba.
        if not l["negrito"] and l["x1"] < margem - FOLGA_MARGEM:
            fechar()
            negrito_atual = None
    fechar()

    notas, atual_nota = [], []
    for l in linhas_nota:
        if ABRE_NOTA.match(l["texto"]) and atual_nota:
            notas.append(juntar(atual_nota))
            atual_nota = []
        atual_nota.append(l["texto"])
    if atual_nota:
        notas.append(juntar(atual_nota))

    numeradas = []
    for n in notas:
        m = ABRE_NOTA.match(n)
        if m:
            # SEM strip(): o espaco que separa o numero do texto e uma
            # palavra a menos ou a mais na conferencia. Com ele, o
            # conferidor recusava o documento porque a extracao tinha
            # '1' e 'MERRILL,' e o documento tinha '1MERRILL,'.
            numeradas.append((int(m.group(1)), n[len(m.group(1)):]))
        else:                      # nota sem numero legivel fica como corpo
            itens.append(("Normal", n))
    return itens, numeradas


def converter(caminho):
    """Devolve (itens, notas, paginas, por_pagina). O ultimo guarda a
    divisao pagina a pagina, porque a conferencia precisa dela: a extracao
    entrega corpo e notas alternando por pagina, e o documento leva todas
    as notas para o rodape do Word."""
    paginas = linhas_do_pdf(caminho)
    itens, notas, por_pagina = [], [], []
    for i, pagina in enumerate(paginas):
        it, nt = itens_da_pagina(pagina, i == 0)
        itens.extend(it)
        notas.extend(nt)
        por_pagina.append((it, nt))
    return itens, notas, paginas, por_pagina


# ------------------------------------------------------------------ escrita

def corpo_com_chamadas(texto, numeros):
    """O texto vem com as chamadas ja marcadas na leitura. Aqui elas viram
    referencia de nota; o que nao tiver nota correspondente volta a ser o
    digito que era, para nao sumir palavra nenhuma."""
    partes = []
    for i, pedaco in enumerate(texto.split(MARCA)):
        marcado = i % 2 == 1
        if marcado and pedaco.isdigit() and int(pedaco) in numeros:
            partes.append('<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/>'
                          '</w:rPr><w:footnoteReference w:id="%d"/></w:r>'
                          % int(pedaco))
        elif pedaco:
            partes.append('<w:r><w:t xml:space="preserve">%s</w:t></w:r>'
                          % escapar(pedaco))
    return "".join(partes) or '<w:r><w:t xml:space="preserve"></w:t></w:r>'


def sem_marca(s):
    return s.replace(MARCA, "")


def documento_xml(itens, numeros):
    partes = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
              '<w:document xmlns:w="%s"><w:body>' % NS_W]
    for estilo, texto in itens:
        ppr = ('<w:pPr><w:pStyle w:val="%s"/></w:pPr>' % estilo
               if estilo != "Normal" else "")
        partes.append("<w:p>%s%s</w:p>" % (ppr, corpo_com_chamadas(texto, numeros)))
    partes.append(est.SECT_PR + "</w:body></w:document>")
    return "".join(partes).encode("utf-8")


def escrever_docx(itens, notas, saida):
    numeros = {n for n, _ in notas}
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", est.TIPOS)
        z.writestr("_rels/.rels", est.RELS)
        z.writestr("word/_rels/document.xml.rels", est.RELS_DOC)
        z.writestr("word/styles.xml", est.ESTILOS)
        z.writestr("word/footnotes.xml", est.footnotes_xml(notas, escapar))
        z.writestr("word/document.xml", documento_xml(itens, numeros))


# ------------------------------------------------------------------ conferencia

def normalizar(s):
    return re.sub(r"\s+", " ", s).strip()


def conferir(por_pagina, paginas):
    """As mesmas palavras da extracao, na mesma ordem. A nota sai do pe da
    pagina e vai para o rodape do Word, entao a comparacao remonta a ordem
    da extracao: corpo da pagina, depois as notas DAQUELA pagina, e nao
    todas as notas no fim."""
    lidas, escritas = [], []
    for pagina, (itens, notas) in zip(paginas, por_pagina):
        corpo = [l for l in pagina if not l["nota"]]
        if corpo and so_numero(corpo[-1]["texto"]):
            corpo = corpo[:-1]
        lidas.extend(sem_marca(l["texto"]) for l in corpo)
        lidas.extend(sem_marca(l["texto"]) for l in pagina if l["nota"])
        escritas.extend(sem_marca(t) for _, t in itens)
        escritas.extend("%d%s" % (n, sem_marca(t)) for n, t in notas)

    a = normalizar(" ".join(lidas)).replace("- ", "-")
    b = normalizar(" ".join(escritas)).replace("- ", "-")
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
    bons = [("Normal", "O problema de pesquisa e este. A justificativa e aquela.")]
    casos = [
        ("texto identico", bons, None),
        ("uma palavra trocada",
         [("Normal", "O problema de pesquisa e esse. A justificativa e aquela.")], "x"),
        ("uma palavra a menos",
         [("Normal", "O problema de pesquisa e este. A justificativa aquela.")], "x"),
        ("um paragrafo a menos",
         [("Normal", "O problema de pesquisa e este.")], "x"),
    ]
    ok = True
    for nome, itens, espera in casos:
        r = conferir([(itens, [])], [pagina])
        passou = (r is None) if espera is None else (r is not None)
        ok = ok and passou
        print("  %-22s %s" % (nome, ("passou (correto)" if r is None
                                     else "reprovou: " + r)))
    # e a nota tem de contar como texto, e nao sumir da conferencia
    pag_nota = pagina + [{"texto": "1Uma nota qualquer.", "y": 9, "x1": 300,
                          "negrito": False, "nota": True}]
    sem_nota = conferir([(bons, [])], [pag_nota])
    com_nota = conferir([(bons, [(1, "Uma nota qualquer.")])], [pag_nota])
    print("  %-22s %s" % ("nota esquecida",
                          "reprovou (correto)" if sem_nota else "PASSOU (erro)"))
    print("  %-22s %s" % ("nota no lugar",
                          "passou (correto)" if com_nota is None
                          else "REPROVOU: " + com_nota))
    ok = ok and sem_nota is not None and com_nota is None
    print("\n" + ("O conferidor reprova o que deve reprovar."
                  if ok else "O CONFERIDOR ESTA QUEBRADO. Nao use o resultado."))
    return 0 if ok else 1


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
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

    itens, notas, paginas, por_pagina = converter(origem)
    if not itens:
        sys.exit("nao saiu texto nenhum de %s. Se o PDF for digitalizado, "
                 "ele nao tem camada de texto, e este programa nao serve."
                 % origem.name)

    erro = conferir(por_pagina, paginas)
    if erro:
        sys.exit("PAREI: %s\nO texto teria saido diferente do que entrou, e e "
                 "isto que este programa existe para impedir. Nada foi escrito."
                 % erro)

    saida = Path(a.saida) if a.saida else origem.with_suffix(".docx")
    escrever_docx(itens, notas, saida)

    titulos = sum(1 for e, _ in itens if e != "Normal")
    palavras = sum(len(sem_marca(t).split()) for _, t in itens)
    print("%s: %d paginas, %d paragrafos (%d deles titulos), %d notas de "
          "rodape, %d palavras."
          % (saida.name, len(paginas), len(itens), titulos, len(notas), palavras))
    print("Texto conferido palavra a palavra contra a extracao.")
    print("Titulos como estilos, notas como notas, A4 com margens da ABNT.")
    print("Nao vieram: formatacao fina, imagens e tabelas.")
    print("Agora: python comentar_projeto.py %s --numerar" % saida.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
