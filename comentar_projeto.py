#!/usr/bin/env python3
"""
Poe as sugestoes do assistente no projeto do autor, como comentarios,
sem tocar numa palavra do texto.

    python comentar_projeto.py projeto.docx --numerar
    python comentar_projeto.py projeto.docx --sugestoes sug.txt -o comentado.docx
    python comentar_projeto.py projeto.md   --sugestoes sug.txt -o comentado.md

POR QUE ISTO EXISTE. O assistente devolve o projeto comentado, e havia
duas maneiras de fazer isso. Uma era ele redigitar o documento inteiro
dentro do chat com as sugestoes no meio; a outra e esta. A primeira e
impossivel de cumprir: modelo de linguagem nao copia, produz, e mil
palavras redigitadas saem com frase alisada e sinonimo trocado num
documento que o autor vai assinar. Aqui o assistente produz LOCALIZADOR E
TEXTO DA SUGESTAO, e quem escreve no arquivo e este programa, que nao le
o texto do autor para nada alem de achar o paragrafo.

O FLUXO TEM DOIS PASSOS, como nos outros programas da familia.

  1. --numerar lista os paragrafos com [P001], [P002]. O autor cola essa
     lista na conversa, e a partir dai o assistente aponta sem transcrever.

  2. O assistente escreve as sugestoes, uma por linha:

         P004 > O objetivo geral nao diz o que se vai fazer.
         P012 > Esta obra nao toca nenhum dos quatro elementos.
         P012 > E a referencia esta sem veiculo.

     Linha comecada por espaco continua a sugestao anterior. Um mesmo
     paragrafo aceita quantas sugestoes tiver.

O QUE ELE NAO FAZ. Nao avalia, nao decide onde a sugestao cabe e nao
infere localizador a partir do texto. Sem arquivo de sugestoes ele para.
Localizador que o documento nao tem faz ele parar e dizer qual e, em vez
de escolher o paragrafo mais parecido: programa que adivinha produz
documento errado com cara de correto.

E ELE CONFERE O QUE PROMETE. Depois de escrever, rele a saida e compara o
texto de cada paragrafo com o da entrada. Se um caractere mudou, ele
apaga a saida e diz onde. A promessa de nao alterar o original nao vale
como intencao, e sim como conferencia; use --provar para ver o
conferidor reprovar uma alteracao de proposito antes de confiar nele.
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

RE_P = re.compile(rb"<w:p(?:\s[^>]*)?(?:/>|>.*?</w:p>)", re.S)
RE_T = re.compile(rb"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.S)

AUTOR = "assistente"
DATA = "2026-01-01T00:00:00Z"
NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL_COMENT = ("http://schemas.openxmlformats.org/officeDocument/2006/"
              "relationships/comments")


def texto(p):
    """O texto visivel de um paragrafo."""
    return "".join(m.group(1).decode("utf-8") for m in RE_T.finditer(p))


def desescapar(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&apos;", "'"))


def escapar(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ler_sugestoes(caminho):
    """P004 > texto. Linha comecada por espaco continua a anterior."""
    if not caminho.is_file():
        sys.exit("nao achei %s" % caminho)
    itens = []
    for n, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        if not linha.strip() or linha.lstrip().startswith("#"):
            continue
        if linha[0].isspace():
            if not itens:
                sys.exit("linha %d continua uma sugestao que nao comecou." % n)
            itens[-1][1] += " " + linha.strip()
            continue
        m = re.match(r"^P?(\d{1,4})\s*>\s*(.+)$", linha.strip(), re.I)
        if not m:
            sys.exit("linha %d nao tem a forma 'P004 > texto':\n  %s" % (n, linha))
        itens.append([int(m.group(1)), m.group(2).strip()])
    if not itens:
        sys.exit("o arquivo de sugestoes esta vazio.")
    return itens


# ----------------------------------------------------------------- docx

def comentarios_xml(itens):
    partes = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
              '<w:comments xmlns:w="%s">' % NS_W]
    for i, (_, txt) in enumerate(itens):
        partes.append(
            '<w:comment w:id="%d" w:author="%s" w:date="%s" w:initials="A">'
            '<w:p><w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
            '</w:comment>' % (i, AUTOR, DATA, escapar(txt)))
    partes.append("</w:comments>")
    return "".join(partes).encode("utf-8")


def envolver(p, ids):
    """Poe o paragrafo entre commentRangeStart/End, com a referencia."""
    inicio = "".join('<w:commentRangeStart w:id="%d"/>' % i for i in ids)
    fim = "".join('<w:commentRangeEnd w:id="%d"/>'
                  '<w:r><w:commentReference w:id="%d"/></w:r>' % (i, i)
                  for i in ids)
    corte = p.rfind(b"</w:p>")
    return p[:corte] + fim.encode("utf-8") + p[corte:], inicio.encode("utf-8")


def com_relacao(rels):
    """Acrescenta a relacao do comments.xml, se ainda nao houver."""
    if b"comments.xml" in rels:
        return rels
    novo = ('<Relationship Id="rId9001" Type="%s" Target="comments.xml"/>'
            % REL_COMENT).encode("utf-8")
    corte = rels.rfind(b"</Relationships>")
    return rels[:corte] + novo + rels[corte:]


def com_tipo(tipos):
    if b"/word/comments.xml" in tipos:
        return tipos
    novo = (b'<Override PartName="/word/comments.xml" ContentType='
            b'"application/vnd.openxmlformats-officedocument.'
            b'wordprocessingml.comments+xml"/>')
    corte = tipos.rfind(b"</Types>")
    return tipos[:corte] + novo + tipos[corte:]


def fazer_docx(origem, saida, itens):
    with zipfile.ZipFile(origem) as z:
        conteudo = {n: z.read(n) for n in z.namelist()}

    doc = conteudo["word/document.xml"]
    paras = [m.group(0) for m in RE_P.finditer(doc)]
    if not paras:
        sys.exit("nao achei paragrafos em %s" % origem.name)

    conferir_localizadores(itens, len(paras), origem.name)

    por_paragrafo = {}
    for i, (n, _) in enumerate(itens):
        por_paragrafo.setdefault(n, []).append(i)

    # Reconstroi o document.xml paragrafo a paragrafo, mexendo so nos citados.
    partes, pos, n = [], 0, 0
    for m in RE_P.finditer(doc):
        n += 1
        partes.append(doc[pos:m.start()])
        p = m.group(0)
        if n in por_paragrafo:
            p, inicio = envolver(p, por_paragrafo[n])
            partes.append(inicio)
        partes.append(p)
        pos = m.end()
    partes.append(doc[pos:])

    conteudo["word/document.xml"] = b"".join(partes)
    conteudo["word/comments.xml"] = comentarios_xml(itens)
    conteudo["[Content_Types].xml"] = com_tipo(conteudo["[Content_Types].xml"])
    conteudo["word/_rels/document.xml.rels"] = com_relacao(
        conteudo["word/_rels/document.xml.rels"])

    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
        for nome, dados in conteudo.items():
            z.writestr(nome, dados)
    return [desescapar(texto(q)) for q in paras]


def texto_do_docx(caminho):
    with zipfile.ZipFile(caminho) as z:
        doc = z.read("word/document.xml")
    return [desescapar(texto(m.group(0))) for m in RE_P.finditer(doc)]


# ----------------------------------------------------------------- md

SEP = re.compile(r"\n[ \t]*\n")


def trechos_md(bruto):
    """Onde cada paragrafo comeca e acaba, em deslocamento."""
    trechos, pos = [], 0
    for m in SEP.finditer(bruto):
        trechos.append((pos, m.start()))
        pos = m.end()
    trechos.append((pos, len(bruto)))
    return trechos


def paragrafos_md(bruto):
    return [bruto[a:b] for a, b in trechos_md(bruto)]


def fazer_md(origem, saida, itens):
    """Insere no deslocamento, e nao reconstroi: reconstruir e redigitar."""
    bruto = origem.read_text(encoding="utf-8")
    trechos = trechos_md(bruto)
    antes = [bruto[a:b] for a, b in trechos]
    conferir_localizadores(itens, len(trechos), origem.name)

    por_paragrafo = {}
    for n, txt in itens:
        por_paragrafo.setdefault(n, []).append(txt)

    # De tras para a frente, para os deslocamentos nao se moverem.
    for n in sorted(por_paragrafo, reverse=True):
        fim = trechos[n - 1][1]
        while fim > 0 and bruto[fim - 1] in "\r\n\t ":
            fim -= 1          # o ultimo paragrafo traz a quebra final do arquivo
        bloco = "".join("\n\n> SUGESTAO: " + t for t in por_paragrafo[n])
        bruto = bruto[:fim] + bloco + bruto[fim:]

    saida.write_text(bruto.rstrip("\n") + "\n", encoding="utf-8")
    return antes


def texto_do_md(caminho):
    return [p for p in paragrafos_md(caminho.read_text(encoding="utf-8"))
            if not p.lstrip().startswith("> SUGESTAO:")]


# ----------------------------------------------------------------- comuns

def conferir_localizadores(itens, quantos, nome):
    fora = sorted({n for n, _ in itens} - set(range(1, quantos + 1)))
    if fora:
        sys.exit("as sugestoes citam paragrafos que %s nao tem: %s\n"
                 "O documento vai de P001 a P%03d. Eu nao escolho o "
                 "paragrafo mais parecido." %
                 (nome, ", ".join("P%03d" % n for n in fora), quantos))


def conferir_texto(antes, depois, saida):
    """O conferidor. Texto que mudou faz a saida ser apagada."""
    if len(antes) != len(depois):
        if saida and saida.exists():
            saida.unlink()
        sys.exit("o documento saiu com %d paragrafos e entrou com %d."
                 % (len(depois), len(antes)))
    # Compara sem o espaco das pontas: quebra de linha no fim do arquivo
    # nao e palavra do autor, e sinonimo trocado continua reprovando.
    for i, (a, d) in enumerate(zip(antes, depois), 1):
        if a.strip() != d.strip():
            if saida and saida.exists():
                saida.unlink()
            sys.exit("O TEXTO DE P%03d MUDOU, e a saida foi apagada.\n"
                     "  entrou: %s\n  saiu:   %s" % (i, a[:90], d[:90]))
    return True


def provar():
    """Controle positivo: o conferidor tem de reprovar uma alteracao."""
    a = ["O problema de pesquisa e este.", "A justificativa e aquela."]
    print("controle 1: texto identico deve passar...", end=" ")
    conferir_texto(a, list(a), None)
    print("passou")

    print("controle 2: sinonimo trocado deve reprovar...", end=" ")
    b = ["O problema de pesquisa e esse.", "A justificativa e aquela."]
    try:
        conferir_texto(a, b, None)
    except SystemExit as e:
        print("reprovou:", str(e).splitlines()[0])
    else:
        sys.exit("O CONFERIDOR NAO REPROVOU. Nao use este programa.")

    print("controle 3: paragrafo a menos deve reprovar...", end=" ")
    try:
        conferir_texto(a, a[:1], None)
    except SystemExit as e:
        print("reprovou:", str(e).splitlines()[0])
    else:
        sys.exit("O CONFERIDOR NAO REPROVOU. Nao use este programa.")

    print("\nO conferidor reprova o que deve reprovar.")


def main():
    p = argparse.ArgumentParser(
        description="Poe as sugestoes no projeto, como comentarios, sem "
                    "tocar no texto.")
    p.add_argument("arquivo", nargs="?", help="o projeto do autor (.docx ou .md)")
    p.add_argument("--numerar", action="store_true",
                   help="lista os paragrafos numerados e sai")
    p.add_argument("--sugestoes", help="arquivo com 'P004 > texto', uma por linha")
    p.add_argument("-o", "--saida", help="o arquivo de saida")
    p.add_argument("--provar", action="store_true",
                   help="mostra o conferidor reprovando uma alteracao")
    a = p.parse_args()

    if a.provar:
        provar()
        return
    if not a.arquivo:
        p.error("falta o arquivo. Ou use --provar.")

    origem = Path(a.arquivo)
    if not origem.is_file():
        sys.exit("nao achei %s" % origem)
    docx = origem.suffix.lower() == ".docx"

    if a.numerar:
        paras = (texto_do_docx(origem) if docx
                 else paragrafos_md(origem.read_text(encoding="utf-8")))
        for i, t in enumerate(paras, 1):
            t = " ".join(t.split())
            print("[P%03d] %s" % (i, t[:110] if t else "(vazio)"))
        print("\n%d paragrafos. Escreva as sugestoes com estes localizadores."
              % len(paras))
        return

    if not a.sugestoes:
        sys.exit("falta --sugestoes. Ou use --numerar para o primeiro passo.\n"
                 "Eu nao invento sugestao nem adivinho onde ela cabe.")
    itens = ler_sugestoes(Path(a.sugestoes))

    if not a.saida:
        sys.exit("falta -o. Eu nao escrevo por cima do arquivo do autor.")
    saida = Path(a.saida)
    if saida.exists() and saida.resolve() == origem.resolve():
        sys.exit("a saida nao pode ser o proprio arquivo do autor.")

    antes = (fazer_docx(origem, saida, itens) if docx
             else fazer_md(origem, saida, itens))
    depois = texto_do_docx(saida) if docx else texto_do_md(saida)
    conferir_texto(antes, depois, saida)

    print("%d sugestoes em %d paragrafos de %s."
          % (len(itens), len({n for n, _ in itens}), origem.name))
    print("O texto do autor saiu identico ao que entrou, conferido "
          "paragrafo a paragrafo.\n")

    # ONDE CADA SUGESTAO FOI PARAR. Se o assistente numerou o que foi
    # colado no chat e o arquivo tem paragrafos a mais (titulo, linha em
    # branco, cabecalho), os numeros escorregam e o comentario vai para o
    # paragrafo errado EM SILENCIO. Mostrar a ancora faz o erro aparecer
    # antes de o autor abrir o arquivo.
    print("CONFIRA AS ANCORAS. Cada linha diz em que paragrafo a sugestao")
    print("foi ancorada. Se alguma nao corresponder, a numeracao usada nao")
    print("era a deste arquivo: rode --numerar e refaca as sugestoes.\n")
    for n, txt in itens:
        alvo = " ".join(antes[n - 1].split())
        print("  P%03d [%s]" % (n, alvo[:58] if alvo else "(vazio)"))
        print("       %s" % txt[:64])
    print("\nSaida: %s" % saida)


if __name__ == "__main__":
    main()
