#!/usr/bin/env python3
"""
Poe as sugestoes do assistente DENTRO do PDF do autor, como comentarios,
sem tocar numa palavra e sem converter o arquivo.

    python comentar_pdf.py projeto.pdf --numerar
    python comentar_pdf.py projeto.pdf --sugestoes sug.txt -o comentado.pdf
    python comentar_pdf.py projeto.pdf --provar

POR QUE ISTO EXISTE, E O QUE ELE SUBSTITUI. O caminho anterior era
converter o PDF em .docx e comentar o .docx. A conversao RECONSTROI o
documento, e reconstrucao tem defeito: num projeto real, as chamadas de
nota nao vinham marcadas como sobrescrito, entao o programa nao as
reconhecia, e O TEXTO DAS NOTAS DE RODAPE SAIU COMO PARAGRAFO DO CORPO,
no meio do argumento. O leitor recebia um documento que parece o dele e
tem trechos ilegiveis. Aqui nao ha reconstrucao: o PDF do autor sai do
outro lado byte a byte igual no conteudo das paginas, e o que se
acrescenta sao ANOTACOES, que sao objetos a parte do texto.

O FLUXO TEM DOIS PASSOS, como nos outros programas da familia.

  1. --numerar lista os paragrafos com [P001], [P002]. O autor cola essa
     lista na conversa, e a partir dai o assistente aponta sem
     transcrever. Junto sai um arquivo .locais.json com a pagina e o
     retangulo de cada paragrafo: e por ele que a anotacao acha onde ir,
     e nao por procurar o texto de novo.

  2. O assistente escreve as sugestoes, uma por linha, no mesmo formato
     do comentar_projeto.py:

         P004 > O objetivo geral nao diz o que se vai fazer.
         P012 > Esta obra nao toca nenhum dos quatro elementos.

     Localizador que o documento nao tem faz o programa parar e dizer
     qual e, em vez de escolher o paragrafo mais parecido.

O QUE ELE ESCREVE NO PDF. Uma anotacao de destaque sobre as linhas do
paragrafo e um balao com o texto da sugestao. Acrobat, Edge, Firefox,
Chrome e Preview mostram os dois, e o painel de comentarios do Acrobat
lista todos em ordem. Nada e enviado a lugar nenhum.

COMO ELE DIVIDE OS PARAGRAFOS, que e a unica inferencia que ele faz. Num
texto justificado, a ultima linha de um paragrafo e curta, porque nao
precisa alcancar a margem direita. Entao: linha que termina antes da
margem fecha o paragrafo, e linha que a alcanca continua na seguinte. A
margem e medida em cada pagina, pela linha mais longa dela. Muda-se de
paragrafo tambem quando o negrito comeca ou acaba, quando o corpo muda
de tamanho (que e onde a nota de rodape se separa do texto) e no fim da
pagina.

E AQUI A NOTA DE RODAPE NAO PRECISA SER RECONHECIDA COMO NOTA. Ela ganha
o numero dela na sequencia, na posicao em que esta na pagina, e pode
receber sugestao como qualquer outro paragrafo. O erro que estragava a
conversao nao tem como acontecer: no maximo um paragrafo fica com
fronteira diferente da que o autor veria, e a sugestao continua caindo
sobre o texto certo, porque ela vai para o RETANGULO guardado, e nao
para um texto procurado de novo.

E ELE CONFERE O QUE PROMETE. Depois de escrever, ele abre a saida e
compara, pagina a pagina, o texto extraido com o da entrada. Se um
caractere mudou, ele apaga a saida e diz em que pagina. A promessa de
nao alterar o original nao vale como intencao, e sim como conferencia:
--provar mostra o conferidor reprovando uma alteracao feita de
proposito antes que voce confie no silencio dele.
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Falta o PyMuPDF. Instale com: pip install pymupdf")

# Duas pecas ate esta distancia vertical estao na mesma linha.
TOLERANCIA_LINHA = 3.0

# Quanto uma linha pode ficar aquem da margem direita e ainda contar como
# linha cheia, em pontos.
FOLGA_MARGEM = 12.0

# Fracao das linhas que precisa comecar na mesma margem esquerda para a
# pagina contar como texto corrido. Medido nos projetos deste acervo:
# paginas de corpo dao 92% e 97%, e capas centradas dao 50% e 55%.
FRACAO_ALINHADA = 0.70

# Duas margens esquerdas ate esta distancia contam como a mesma.
TOLERANCIA_MARGEM = 2.0

# Numa pagina que nao e texto corrido, o bloco fecha quando o salto
# vertical passa desta fracao do salto tipico da pagina. Medido nas capas
# deste acervo: dentro do bloco, 20,5 a 20,8 pontos; entre blocos, 62 a 95.
SALTO_DE_BLOCO = 1.6

# Diferenca de corpo a partir da qual duas linhas nao sao do mesmo bloco.
# E o que separa a nota de rodape do texto, sem precisar decidir qual e
# qual: basta que nao se juntem.
DIFERENCA_CORPO = 1.0

RE_SUGESTAO = re.compile(
    r"^\s*\[?\s*P?\s*(\d{1,4})\s*\]?\s*[>:–—-]\s*(.+?)\s*$", re.I)

COR_DESTAQUE = (1.0, 0.85, 0.35)


# --------------------------------------------------------------- leitura

def linhas_da_pagina(pagina):
    """Junta os spans em linhas visuais, com o retangulo de cada uma.

    O EXTRATOR PARTE UMA LINHA VISUAL EM VARIAS quando o espacamento entre
    palavras e grande, o que acontece em bloco justificado estreito. Sem
    juntar de volta, a capa de um projeto sai em pedacos de uma palavra,
    cada um virando um paragrafo, e a numeracao anda antes de o texto
    comecar.
    """
    pecas = []
    for bloco in pagina.get_text("dict")["blocks"]:
        for linha in bloco.get("lines", []):
            cheios = [t for t in linha.get("spans", []) if t["text"].strip()]
            if not cheios:
                continue
            pecas.append({
                "texto": "".join(t["text"] for t in linha["spans"]).strip(),
                "y": linha["bbox"][1],
                "x0": linha["bbox"][0],
                "x1": linha["bbox"][2],
                "y1": linha["bbox"][3],
                "negrito": all(t["flags"] & 16 for t in cheios),
                "corpo": max(t["size"] for t in cheios),
            })

    pecas.sort(key=lambda p: (round(p["y"] / TOLERANCIA_LINHA), p["x0"]))
    linhas, atual = [], []

    def fechar():
        if not atual:
            return
        linhas.append({
            "texto": " ".join(p["texto"] for p in atual),
            "y": min(p["y"] for p in atual),
            "y1": max(p["y1"] for p in atual),
            "x0": min(p["x0"] for p in atual),
            "x1": max(p["x1"] for p in atual),
            "negrito": all(p["negrito"] for p in atual),
            "corpo": max(p["corpo"] for p in atual),
        })
        atual.clear()

    for p in pecas:
        if atual and abs(p["y"] - atual[0]["y"]) > TOLERANCIA_LINHA:
            fechar()
        atual.append(p)
    fechar()
    linhas.sort(key=lambda l: l["y"])
    return linhas


def so_numero(t):
    return re.fullmatch(r"\d{1,4}", t.strip()) is not None


def alinhada_a_esquerda(linhas):
    """A pagina e texto corrido, ou e capa e folha de rosto?

    A regra da margem direita so vale onde o texto e justificado. Numa
    capa centrada ela nunca fecha paragrafo, porque as linhas mais longas
    da pagina sao as do titulo, e e a linha mais longa que define a
    margem. O resultado era a capa inteira virando um paragrafo so, com o
    titulo grudado no nome da instituicao.
    """
    if not linhas:
        return True
    grupos = {}
    for l in linhas:
        chave = round(l["x0"] / TOLERANCIA_MARGEM)
        grupos[chave] = grupos.get(chave, 0) + 1
    return max(grupos.values()) >= FRACAO_ALINHADA * len(linhas)


def blocos_por_salto(linhas, indice):
    """Agrupa as linhas de uma pagina centrada pelos saltos verticais.

    Sem isto, a capa saia linha a linha e O TITULO OCUPAVA DOIS
    PARAGRAFOS, de modo que o localizador do titulo alcancava metade dele.
    """
    saltos = sorted(linhas[i + 1]["y"] - linhas[i]["y"]
                    for i in range(len(linhas) - 1))
    tipico = saltos[len(saltos) // 2] if saltos else 0.0
    limite = SALTO_DE_BLOCO * tipico if tipico > 0 else float("inf")

    saida, atual = [], []

    def fechar():
        if not atual:
            return
        saida.append({
            "pagina": indice,
            "texto": " ".join(l["texto"] for l in atual),
            "rects": [[l["x0"], l["y"], l["x1"], l["y1"]] for l in atual],
        })
        atual.clear()

    for l in linhas:
        if atual:
            a = atual[-1]
            if l["y"] - a["y"] > limite or l["negrito"] != a["negrito"]:
                fechar()
        atual.append(l)
    fechar()
    return saida


def paragrafos_da_pagina(linhas, indice):
    """Devolve os paragrafos da pagina, cada um com texto e retangulos."""
    if linhas and so_numero(linhas[-1]["texto"]):
        linhas = linhas[:-1]                    # numero de pagina solto
    if not linhas:
        return []
    if not alinhada_a_esquerda(linhas):
        return blocos_por_salto(linhas, indice)
    margem = max(l["x1"] for l in linhas)

    saida, atual = [], []

    def fechar():
        if not atual:
            return
        texto = ""
        for l in atual:
            if not texto:
                texto = l["texto"]
            elif texto.endswith("-"):
                texto += l["texto"]
            else:
                texto += " " + l["texto"]
        saida.append({
            "pagina": indice,
            "texto": texto,
            "rects": [[l["x0"], l["y"], l["x1"], l["y1"]] for l in atual],
        })
        atual.clear()

    for l in linhas:
        if atual:
            a = atual[-1]
            if (l["negrito"] != a["negrito"]
                    or abs(l["corpo"] - a["corpo"]) >= DIFERENCA_CORPO):
                fechar()
        atual.append(l)
        if not l["negrito"] and l["x1"] < margem - FOLGA_MARGEM:
            fechar()
    fechar()
    return saida


def ler(caminho):
    """Devolve a lista de paragrafos do documento inteiro, em ordem."""
    doc = fitz.open(caminho)
    if not any(p.get_text().strip() for p in doc):
        doc.close()
        sys.exit("Este PDF nao tem camada de texto (parece digitalizado). "
                 "Nao ha o que numerar nem onde ancorar comentario.")
    saida = []
    for i, pagina in enumerate(doc):
        saida.extend(paragrafos_da_pagina(linhas_da_pagina(pagina), i))
    doc.close()
    return saida


def texto_por_pagina(caminho):
    """So as palavras, pagina a pagina. E o que o conferidor compara."""
    doc = fitz.open(caminho)
    saida = [p.get_text().split() for p in doc]
    doc.close()
    return saida


# ------------------------------------------------------------- conferidor

def conferir(antes, depois):
    """None se o texto das paginas nao mudou, e o defeito em palavras se
    mudou. Compara palavra a palavra: espaco a mais nao e alteracao do
    texto do autor, e palavra trocada e."""
    if len(antes) != len(depois):
        return ("o documento entrou com %d paginas e saiu com %d"
                % (len(antes), len(depois)))
    for i, (a, b) in enumerate(zip(antes, depois), 1):
        if a != b:
            for j, (pa, pb) in enumerate(zip(a, b)):
                if pa != pb:
                    return ("a pagina %d mudou na palavra %d: %r virou %r"
                            % (i, j + 1, pa, pb))
            return ("a pagina %d entrou com %d palavras e saiu com %d"
                    % (i, len(a), len(b)))
    return None


# ---------------------------------------------------------------- escrita

def ler_sugestoes(bruto):
    """Devolve (itens, ignoradas). Linha comecada por dois espacos
    continua a sugestao anterior."""
    itens, ignoradas = [], 0
    for linha in bruto.splitlines():
        if not linha.strip():
            continue
        m = RE_SUGESTAO.match(linha)
        if m:
            itens.append((int(m.group(1)), m.group(2)))
        elif itens and re.match(r"^\s{2,}\S", linha):
            itens[-1] = (itens[-1][0], itens[-1][1] + " " + linha.strip())
        else:
            ignoradas += 1
    return itens, ignoradas


def anotar(entrada, saida, paragrafos, itens):
    doc = fitz.open(entrada)
    por_par = {}
    for n, txt in itens:
        por_par.setdefault(n, []).append(txt)

    for n in sorted(por_par):
        p = paragrafos[n - 1]
        pagina = doc[p["pagina"]]
        for r in p["rects"]:
            # O update() e obrigatorio: sem ele a cor e a opacidade ficam
            # no objeto e nao chegam a aparencia, e o destaque sai no
            # amarelo cheio do visualizador, que cobre o texto do autor.
            h = pagina.add_highlight_annot(fitz.Rect(r))
            h.set_colors(stroke=COR_DESTAQUE)
            h.set_opacity(0.32)
            h.update()
        primeiro = fitz.Rect(p["rects"][0])
        for k, txt in enumerate(por_par[n]):
            ponto = fitz.Point(primeiro.x1 + 2, primeiro.y0 + 12 * k)
            a = pagina.add_text_annot(ponto, txt, icon="Comment")
            a.set_info(title="Sugestao P%03d" % n, content=txt)
            a.update()
    doc.save(saida)
    doc.close()


# ----------------------------------------------------------------- provas

def provar(entrada):
    """Controle positivo do conferidor. Sem isto, o silencio dele nao
    informa nada: conferidor quebrado e conferidor satisfeito tem a mesma
    aparencia."""
    antes = texto_por_pagina(entrada)
    casos = []

    # 1. o mesmo documento, so gravado de novo: tem de passar
    tmp = Path(entrada).with_name("_prova_igual.pdf")
    d = fitz.open(entrada)
    d.save(str(tmp))
    d.close()
    casos.append(("gravado de novo, sem tocar no texto",
                  conferir(antes, texto_por_pagina(tmp)) is None, True))

    # 2. so com anotacoes: tem de passar, e e isto que o programa faz
    tmp2 = Path(entrada).with_name("_prova_anotado.pdf")
    d = fitz.open(entrada)
    p = d[0]
    p.add_highlight_annot(fitz.Rect(72, 72, 300, 90))
    a = p.add_text_annot(fitz.Point(320, 80), "sugestao de teste")
    a.update()
    d.save(str(tmp2))
    d.close()
    casos.append(("com destaque e balao acrescentados",
                  conferir(antes, texto_por_pagina(tmp2)) is None, True))

    # 3. uma palavra escrita na pagina: tem de reprovar
    tmp3 = Path(entrada).with_name("_prova_alterado.pdf")
    d = fitz.open(entrada)
    d[0].insert_text(fitz.Point(72, 400), "PALAVRAINTRUSA", fontsize=11)
    d.save(str(tmp3))
    d.close()
    r3 = conferir(antes, texto_por_pagina(tmp3))
    casos.append(("uma palavra escrita na pagina", r3 is None, False))

    # 4. uma pagina a menos: tem de reprovar
    casos.append(("uma pagina a menos",
                  conferir(antes, antes[:-1]) is None, False))

    print("Controle positivo do conferidor:")
    ok = True
    for nome, passou, esperado in casos:
        certo = passou == esperado
        ok = ok and certo
        print("  %-38s %-9s %s" % (nome, "passou" if passou else "reprovou",
                                   "ok" if certo else "DIVERGIU"))
    if r3:
        print()
        print("  o que ele disse no caso 3: " + r3)
    # SO OS TRES QUE ESTE PROGRAMA CRIOU. A versao anterior apagava
    # tambem o PDF DE ENTRADA, porque eu guardei doc.name de um documento
    # aberto a partir dele: doc.name e o caminho de origem, e nao o da
    # copia. O programa que promete nao alterar o original destruia o
    # original ao provar que nao o alterava.
    entrada_real = Path(entrada).resolve()
    for t in (tmp, tmp2, tmp3):
        if t.resolve() == entrada_real:
            continue
        try:
            t.unlink()
        except OSError:
            pass
    print()
    print("O conferidor separa os casos." if ok
          else "O CONFERIDOR NAO SEPARA OS CASOS. Nao use o resultado.")
    return 0 if ok else 1


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--numerar", action="store_true",
                    help="lista os paragrafos com [P001] e grava o .locais.json")
    ap.add_argument("--sugestoes", help="arquivo com as sugestoes P004 > texto")
    ap.add_argument("-o", "--saida", help="o PDF comentado")
    ap.add_argument("--provar", action="store_true",
                    help="mostra o conferidor reprovando de proposito")
    a = ap.parse_args()

    entrada = Path(a.pdf)
    if not entrada.is_file():
        sys.exit("Nao achei %s." % entrada)

    if a.provar:
        return provar(str(entrada))

    paragrafos = ler(str(entrada))

    if a.numerar:
        locais = entrada.with_suffix(".locais.json")
        locais.write_text(json.dumps(paragrafos, ensure_ascii=False),
                          encoding="utf-8")
        for i, p in enumerate(paragrafos, 1):
            print("[P%03d] %s" % (i, p["texto"]))
            print()
        print("%d paragrafos em %d paginas. Os lugares ficaram em %s."
              % (len(paragrafos), 1 + max(p["pagina"] for p in paragrafos),
                 locais.name), file=sys.stderr)
        print("Cole a lista acima na conversa, dizendo que e a numeracao do "
              "seu projeto.", file=sys.stderr)
        return 0

    if not a.sugestoes:
        sys.exit("Sem --numerar e sem --sugestoes nao ha o que fazer. "
                 "Comece por --numerar.")

    itens, ignoradas = ler_sugestoes(
        Path(a.sugestoes).read_text(encoding="utf-8"))
    if not itens:
        sys.exit("Nenhuma sugestao com localizador em %s. Elas tem a forma "
                 "P004 > texto da sugestao." % a.sugestoes)

    fora = sorted({n for n, _ in itens if not 1 <= n <= len(paragrafos)})
    if fora:
        sys.exit("As sugestoes apontam paragrafos que o documento nao tem: %s.\n"
                 "Ele vai de P001 a P%03d. Numere-o com --numerar e peca ao "
                 "assistente que refaca as sugestoes com esses numeros. Eu nao "
                 "escolho o paragrafo mais parecido."
                 % (", ".join("P%03d" % n for n in fora), len(paragrafos)))

    saida = Path(a.saida) if a.saida else entrada.with_name(
        entrada.stem + "-comentado.pdf")
    antes = texto_por_pagina(str(entrada))
    anotar(str(entrada), str(saida), paragrafos, itens)

    defeito = conferir(antes, texto_por_pagina(str(saida)))
    if defeito:
        saida.unlink(missing_ok=True)
        sys.exit("PAREI: %s.\nO seu texto teria saido diferente do que entrou, "
                 "e e exatamente isso que este programa existe para impedir. "
                 "Nada foi produzido." % defeito)

    quantos = len({n for n, _ in itens})
    print("%s: %d sugestoes em %d paragrafos, como comentarios."
          % (saida.name, len(itens), quantos))
    print("O texto das paginas saiu identico ao que entrou, conferido palavra "
          "a palavra. Use --provar para ver o conferidor reprovar de proposito.")
    if ignoradas:
        print("Ignorei %d linha%s sem localizador. Se alguma era sugestao, ela "
              "nao entrou." % (ignoradas, "s" if ignoradas > 1 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
