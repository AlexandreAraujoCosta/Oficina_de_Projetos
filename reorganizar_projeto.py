#!/usr/bin/env python3
"""
Reorganiza os elementos do projeto dentro dos topicos do modelo, no
proprio .docx, como alteracoes controladas do Word.

    python reorganizar_projeto.py projeto.docx --numerar
    python reorganizar_projeto.py projeto.docx --mapa mapa.txt -o novo.docx
    python reorganizar_projeto.py projeto.docx --mapa mapa.txt --sem-controle

A DIVISAO DE TRABALHO, QUE E O DESENHO INTEIRO. O assistente diz DE ONDE
PARA ONDE, e nada mais: um mapa de localizador e destino. Quem move o
texto e este programa, copiando do proprio arquivo.

E A REORGANIZACAO DE CONTEUDO NAO E DESTE PROGRAMA. Decidir que um
paragrafo pertence a justificativa e nao a introducao e juizo sobre o que
o paragrafo faz, e isso e trabalho de quem avalia: o Miro, para os quatro
elementos, e o Nelson, para a revisao. Este programa esta na familia da
Norma, que nao usa modelo e nao avalia nada, e por isso ele EXIGE o mapa
e NAO O INFERE: sem mapa ele para, e nunca adivinha destino a partir do
texto. Programa que adivinha produz documento errado com cara de
correto. Nao se pede a modelo
que reescreva o documento, porque modelo de linguagem nao copia, produz,
e o que sai de uma reescrita muda palavra sem avisar num documento que o
autor vai assinar.

POR QUE CONTROLE DE ALTERACOES, E NAO UM AVISO NO ALTO DO ARQUIVO. Um
subtitulo dizendo "este arquivo foi reorganizado, confira tudo" e o aviso
que ninguem cumpre, porque conferir fica caro quando nada mostra o que
mudou. Com marca de revisao, cada movimento aparece e se aceita ou recusa
um a um, no Word que o autor ja usa. O aviso existe como alternativa
(--sem-controle), para quando o controle atrapalhar, e nao como opcao
equivalente.

MOVER, EM MARCA DE REVISAO, E APAGAR NUM LUGAR E INSERIR NOUTRO. O Word
tem marcacao propria de movimento (w:moveFrom e w:moveTo), que exibe
melhor, mas exige pares de marcadores que qualquer erro de escrita
quebra; aqui se usa apagar-inserir, que sempre renderiza e so perde o
rotulo de "movido".

O PARAGRAFO E A UNIDADE. Nao se move meia frase: quem quiser mover parte
de um paragrafo divide o paragrafo antes, no Word.
"""

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gerar_docx_pre_projeto import qual_secao, secoes

RE_P = re.compile(rb"<w:p(?:\s[^>]*)?(?:/>|>.*?</w:p>)", re.S)
RE_T = re.compile(rb"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.S)
RE_RUN = re.compile(rb"<w:r(?:\s[^>]*)?>.*?</w:r>", re.S)
RE_PPR = re.compile(rb"<w:pPr(?:\s[^>]*)?(?:/>|>.*?</w:pPr>)", re.S)
RE_RPR_EM_PPR = re.compile(rb"<w:rPr(?:\s[^>]*)?(?:/>|>.*?</w:rPr>)", re.S)
RE_INTERVALO = re.compile(r"^P?(\d{1,4})\s*-\s*P?(\d{1,4})$", re.I)
RE_UNICO = re.compile(r"^P?(\d{1,4})$", re.I)

AUTOR = "Norma"
DATA = "2026-01-01T00:00:00Z"


def texto(p):
    """O texto visivel de um paragrafo, para casar titulo e mostrar ao autor."""
    return "".join(m.group(1).decode("utf-8") for m in RE_T.finditer(p))


def desescapar(s):
    return (s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&apos;", "'"))


def marca(ident):
    return ('w:id="%d" w:author="%s" w:date="%s"' % (ident, AUTOR, DATA)).encode()


def marcar_apagado(p, ident):
    """Envolve os runs em w:del e converte w:t em w:delText.

    A marca do proprio paragrafo tambem vai apagada, dentro do w:pPr, para
    que ao aceitar a revisao o paragrafo desapareca em vez de deixar uma
    linha em branco onde ele estava.
    """
    def env(m):
        r = m.group(0)
        r = r.replace(b"<w:t>", b"<w:delText>").replace(b"</w:t>", b"</w:delText>")
        r = re.sub(rb"<w:t(\s[^>]*)>", rb"<w:delText\1>", r)
        return b"<w:del " + marca(next(ident)) + b">" + r + b"</w:del>"

    corpo = RE_PPR.sub(b"", p, count=1)
    corpo = RE_RUN.sub(env, corpo)
    ppr = RE_PPR.search(p)
    novo_ppr = b""
    if ppr:
        dentro = ppr.group(0)
        del_marca = b"<w:rPr><w:del " + marca(next(ident)) + b"/></w:rPr>"
        if dentro.endswith(b"/>"):
            novo_ppr = b"<w:pPr>" + del_marca + b"</w:pPr>"
        elif RE_RPR_EM_PPR.search(dentro):
            novo_ppr = RE_RPR_EM_PPR.sub(
                lambda m: m.group(0).replace(b"<w:rPr>", b"<w:rPr><w:del " + marca(next(ident)) + b"/>", 1),
                dentro, count=1)
        else:
            novo_ppr = dentro.replace(b"</w:pPr>", del_marca + b"</w:pPr>", 1)
    if not novo_ppr:
        # Paragrafo sem w:pPr: sem marcar a marca dele, aceitar a revisao
        # deixaria uma linha em branco onde o paragrafo estava.
        novo_ppr = b"<w:pPr><w:rPr><w:del " + marca(next(ident)) + b"/></w:rPr></w:pPr>"
    return corpo.replace(b">", b">" + novo_ppr, 1)


def marcar_inserido(p, ident):
    """Envolve os runs em w:ins e marca como inserida a marca do paragrafo."""
    def env(m):
        return b"<w:ins " + marca(next(ident)) + b">" + m.group(0) + b"</w:ins>"

    corpo = RE_PPR.sub(b"", p, count=1)
    corpo = RE_RUN.sub(env, corpo)
    ppr = RE_PPR.search(p)
    ins_marca = b"<w:rPr><w:ins " + marca(next(ident)) + b"/></w:rPr>"
    if ppr:
        dentro = ppr.group(0)
        if dentro.endswith(b"/>"):
            novo_ppr = b"<w:pPr>" + ins_marca + b"</w:pPr>"
        elif RE_RPR_EM_PPR.search(dentro):
            novo_ppr = RE_RPR_EM_PPR.sub(
                lambda m: m.group(0).replace(b"<w:rPr>", b"<w:rPr><w:ins " + marca(next(ident)) + b"/>", 1),
                dentro, count=1)
        else:
            novo_ppr = dentro.replace(b"</w:pPr>", ins_marca + b"</w:pPr>", 1)
    else:
        novo_ppr = b"<w:pPr>" + ins_marca + b"</w:pPr>"
    return corpo.replace(b">", b">" + novo_ppr, 1)


def titulo_novo(nome, ident, com_controle):
    """Um paragrafo de titulo, para a secao de destino que nao existe."""
    p = ('<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>%s</w:t>'
         '</w:r></w:p>' % nome).encode()
    return marcar_inserido(p, ident) if com_controle else p


def ler_mapa(caminho):
    mapa, vistos = [], {}
    for n, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        if "<-" not in linha:
            sys.exit("linha %d do mapa não tem '<-': %s" % (n, linha))
        alvo, itens = linha.split("<-", 1)
        secao = qual_secao(alvo.strip())
        if not secao:
            sys.exit("linha %d: '%s' não é seção do modelo.\nSeções: %s"
                     % (n, alvo.strip(), ", ".join(c for c, _, _ in secoes())))
        numeros = []
        for item in itens.split(","):
            item = item.strip()
            if not item:
                continue
            m = RE_INTERVALO.match(item)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                if a > b:
                    sys.exit("linha %d: intervalo invertido em %s" % (n, item))
                numeros.extend(range(a, b + 1))
                continue
            m = RE_UNICO.match(item)
            if not m:
                sys.exit("linha %d: não entendi '%s'" % (n, item))
            numeros.append(int(m.group(1)))
        for x in numeros:
            if x in vistos:
                sys.exit("parágrafo P%03d aparece duas vezes no mapa, nas linhas %d e %d.\n"
                         "Um parágrafo só pode ir para um lugar." % (x, vistos[x], n))
            vistos[x] = n
        mapa.append((secao, numeros))
    return mapa


def main():
    p = argparse.ArgumentParser(
        description="Reorganiza os elementos do projeto nos tópicos do modelo.")
    p.add_argument("docx", help="o projeto do autor")
    p.add_argument("--numerar", action="store_true",
                   help="lista os parágrafos numerados e sai")
    p.add_argument("--mapa", help="o mapa de localizador e destino")
    p.add_argument("-o", "--saida", help="o .docx de saída")
    p.add_argument("--sem-controle", action="store_true",
                   help="move sem marca de revisão, avisando no alto do arquivo")
    a = p.parse_args()

    origem = Path(a.docx)
    if not origem.is_file():
        sys.exit("não achei %s" % origem)

    with zipfile.ZipFile(origem) as z:
        doc = z.read("word/document.xml")

    paras = [m.group(0) for m in RE_P.finditer(doc)]
    if not paras:
        sys.exit("não achei parágrafos em %s" % origem.name)

    if a.numerar:
        for i, q in enumerate(paras, 1):
            t = desescapar(texto(q)).strip()
            print("[P%03d] %s" % (i, t[:110] if t else "(vazio)"))
        print("\n%d parágrafos. Escreva o mapa com estes localizadores." % len(paras))
        return

    if not a.mapa:
        sys.exit("falta --mapa. Ou use --numerar para o primeiro passo.")
    mapa = ler_mapa(Path(a.mapa))

    fora = sorted({n for _, ns in mapa for n in ns} - set(range(1, len(paras) + 1)))
    if fora:
        sys.exit("o mapa cita parágrafos que o documento não tem: %s\n"
                 "O documento vai de P001 a P%03d."
                 % (", ".join("P%03d" % n for n in fora), len(paras)))

    # Onde esta cada titulo de secao do modelo, para saber o destino.
    destino_de = {}
    for i, q in enumerate(paras, 1):
        nome = qual_secao(desescapar(texto(q)).strip())
        if nome and nome not in destino_de:
            destino_de[nome] = i

    ident = iter(range(1000, 100000))
    com_controle = not a.sem_controle

    # Cada paragrafo movido sai do lugar e entra depois do titulo de destino.
    a_inserir = {}
    movidos = set()
    criados = []
    for secao, numeros in mapa:
        alvo = destino_de.get(secao)
        if alvo is None:
            criados.append(secao)
        for n in numeros:
            copia = paras[n - 1]
            corpo = marcar_inserido(copia, ident) if com_controle else copia
            a_inserir.setdefault((secao, alvo), []).append(corpo)
            movidos.add(n)

    saida = []
    for i, q in enumerate(paras, 1):
        if i in movidos:
            saida.append(marcar_apagado(q, ident) if com_controle else b"")
        else:
            saida.append(q)
        for (secao, alvo), blocos in a_inserir.items():
            if alvo == i:
                saida.extend(blocos)

    # Secao de destino que nao existia entra no fim, com o titulo criado.
    for (secao, alvo), blocos in a_inserir.items():
        if alvo is None:
            saida.append(titulo_novo(secao, ident, com_controle))
            saida.extend(blocos)

    if a.sem_controle:
        aviso = ('<w:p><w:r><w:t xml:space="preserve">Este arquivo foi '
                 'reorganizado por programa, a partir de um mapa produzido na '
                 'conversa. Nenhum texto foi reescrito: os parágrafos foram '
                 'movidos como estavam. Confira todos os elementos antes de '
                 'usar.</w:t></w:r></w:p>').encode()
        saida.insert(0, aviso)

    novo = doc
    for velho, novo_p in zip(paras, saida):
        novo = novo.replace(velho, b"\x00MARCA\x00", 1)
    partes = novo.split(b"\x00MARCA\x00")
    montado = partes[0]
    for k, pedaco in enumerate(partes[1:]):
        montado += saida[k] + pedaco
    # os inseridos que nao correspondem a um paragrafo original vao no fim do corpo
    extras = b"".join(saida[len(paras):])
    if extras:
        montado = montado.replace(b"</w:body>", extras + b"</w:body>", 1)

    destino = Path(a.saida) if a.saida else origem.with_name(
        origem.stem + "-reorganizado.docx")
    shutil.copy(origem, destino)
    with zipfile.ZipFile(origem) as zin:
        nomes = zin.namelist()
        dados = {n: zin.read(n) for n in nomes}
    dados["word/document.xml"] = montado
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in nomes:
            zout.writestr(n, dados[n])

    print("%s: %d parágrafos movidos%s"
          % (destino.name, len(movidos),
             ", com marca de revisão" if com_controle else ", sem controle"))
    for secao, numeros in mapa:
        print("  %s <- %s" % (secao, ", ".join("P%03d" % n for n in numeros)))
    if criados:
        print("  seções criadas: " + ", ".join(criados))
    if com_controle:
        print("  abra no Word e aceite ou recuse cada movimento.")


if __name__ == "__main__":
    main()
