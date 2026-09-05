#!/usr/bin/env python3
"""
A diagramacao dos PDFs que este repositorio produz: uma folha que desce e
vira sozinha, e uma tabela.

POR QUE ELA VIVE A PARTE. Tres saidas usam PDF (o relatorio da Selma num
projeto, o relatorio do lote e a tabela comparativa), e diagramacao
duplicada diverge sem avisar. Aqui ela e uma so.

E A ALTURA DE CADA BLOCO SAI DO PROPRIO MOTOR, nunca de conta minha. A
primeira versao media por fora e passava a caixa justa; insert_textbox
precisa da folga da fonte, devolvia negativo, e o tratamento de "nao
coube" consumia o resto da pagina: sete itens sairam em vinte e cinco
paginas. Agora a caixa vai ate a margem de baixo, e a altura usada e a
caixa menos a sobra.

E AS FONTES SAO AS BASE-14, que sao WinAnsi: acento cabe, U+2026 nao.
Reticencias se escrevem com tres pontos, ou o leitor ve um ponto de
interrogacao no fim de toda citacao cortada.
"""

import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Falta o PyMuPDF. Instale com: pip install pymupdf")


LARGURA, ALTURA = fitz.paper_size("a4")
MARGEM = 62
LARGURA_UTIL = LARGURA - 2 * MARGEM

CORPO = 11.5
ENTRELINHA = 1.42
COR_TINTA = (0.12, 0.12, 0.13)
COR_FRACA = (0.42, 0.42, 0.45)
COR_MARCA = (0.62, 0.42, 0.10)
COR_FUNDO = (0.975, 0.965, 0.94)

# Linhas que nao se deixam sozinhas de um lado da quebra. Uma linha solta
# no pe ou no alto de uma pagina le-se como erro de quem escreveu.
MINIMO_DE_LINHAS = 2


class Folha:
    """Um cursor que desce pela pagina e vira a folha quando acaba."""

    def __init__(self, doc):
        self.doc = doc
        self.pagina = None
        self.y = 0
        self.nova()

    def nova(self):
        self.pagina = self.doc.new_page(width=LARGURA, height=ALTURA)
        self.y = MARGEM

    def cabe(self, altura):
        return self.y + altura <= ALTURA - MARGEM - 18

    def texto(self, txt, corpo=CORPO, fonte="tiro", cor=COR_TINTA,
              recuo=0, espaco_antes=0, espaco_depois=6, fundo=None,
              justificar=True):
        """Escreve e desce o cursor pela altura DA TINTA.

        DUAS MEDIDAS JA FALHARAM AQUI, e as duas no mesmo sentido, o que
        faz o bloco seguinte cair por cima do anterior. A sobra que o
        insert_textbox devolve e curta: no bloco mais longo de uma peca
        real, a tinta ocupou 328,0 pontos e a sobra disse 316,1. E a
        contagem de linhas por text_length tambem e curta, porque o
        insert_textbox quebra a linha um pouco antes: dizia 21 onde o
        texto ocupou 22.

        ENTAO A ALTURA SAI DO BBOX DO QUE FICOU DESENHADO, numa pagina
        descartavel de mesma largura. Nao e estimativa.
        """
        resto = txt
        primeiro = True
        while resto:
            resto = self._escrever_pedaco(
                resto, corpo, fonte, cor, recuo,
                espaco_antes if primeiro else 0,
                espaco_depois, fundo, inteiro=(fundo is not None),
                justificar=justificar)
            primeiro = False

    def _escrever_pedaco(self, txt, corpo, fonte, cor, recuo, espaco_antes,
                         espaco_depois, fundo, inteiro, justificar=True):
        """Escreve o que couber e devolve o que sobrou.

        BLOCO COM FUNDO NAO SE PARTE: a tarja pintada atras de uma citacao
        cortada ao meio fica pior que a quebra que ela evita.
        """
        largura = LARGURA_UTIL - recuo
        fundo_da_pagina = ALTURA - MARGEM - 18
        alt = self.altura_de(txt, corpo, fonte, recuo)
        linha = corpo * ENTRELINHA

        y = self.y + espaco_antes
        disponivel = fundo_da_pagina - y

        if alt > disponivel:
            cabem = int((disponivel - espaco_antes) // linha)
            if inteiro or cabem < MINIMO_DE_LINHAS:
                self.nova()
                y = self.y
                disponivel = fundo_da_pagina - y
                alt = self.altura_de(txt, corpo, fonte, recuo)
                if alt > disponivel:
                    if inteiro:
                        sys.exit("ERRO: um bloco com fundo nao cabe numa "
                                 "pagina inteira. Encurte o texto.")
                    cabem = int(disponivel // linha)
                else:
                    cabem = None
            if cabem is not None:
                aqui, sobra_txt = self._partir(txt, corpo, fonte, recuo,
                                               disponivel, linha)
                if sobra_txt:
                    self._pintar(aqui, corpo, fonte, cor, recuo, y, largura,
                                 fundo_da_pagina, None,
                                 justificar=justificar)
                    self.nova()
                    return sobra_txt
                txt = aqui

        alt = self.altura_de(txt, corpo, fonte, recuo)
        self._pintar(txt, corpo, fonte, cor, recuo, y, largura,
                     fundo_da_pagina, fundo, alt, justificar=justificar)
        self.y = y + alt + espaco_depois
        return ""

    def _partir(self, txt, corpo, fonte, recuo, disponivel, linha):
        """Acha onde partir, RECUANDO quando o resto ficaria com uma viuva.

        A PRIMEIRA VERSAO RECUSAVA A QUEBRA nesse caso, e o paragrafo
        inteiro saltava de pagina: media, oito linhas em branco no pe.
        Tipografo nao recusa a quebra por causa da viuva, ele recua o
        corte ate o resto ter duas linhas. Aqui e o mesmo: o teto do
        pedaco de cima e o menor entre o que cabe na pagina e o que deixa
        duas linhas para a seguinte.
        """
        palavras = txt.split()
        alt = self.altura_de(txt, corpo, fonte, recuo)
        teto = min(disponivel, alt - MINIMO_DE_LINHAS * linha)
        if teto < MINIMO_DE_LINHAS * linha:
            return "", txt            # nao ha como deixar duas de cada lado

        baixo, alto_i, melhor = 1, len(palavras), 0
        while baixo <= alto_i:
            meio = (baixo + alto_i) // 2
            h = self.altura_de(" ".join(palavras[:meio]), corpo, fonte, recuo)
            if h <= teto:
                melhor = meio
                baixo = meio + 1
            else:
                alto_i = meio - 1
        if melhor == 0:
            return "", txt
        aqui = " ".join(palavras[:melhor])
        sobra = " ".join(palavras[melhor:])
        if not sobra:
            return txt, ""
        if self.altura_de(aqui, corpo, fonte, recuo) < MINIMO_DE_LINHAS * linha:
            return "", txt
        return aqui, sobra

    def _pintar(self, txt, corpo, fonte, cor, recuo, y, largura,
                fundo_da_pagina, fundo, alt=None, justificar=True):
        caixa = fitz.Rect(MARGEM + recuo, y,
                          MARGEM + recuo + largura, fundo_da_pagina)
        self.pagina.insert_textbox(
            caixa, txt, fontsize=corpo, fontname=fonte, color=cor,
            lineheight=ENTRELINHA,
            align=(fitz.TEXT_ALIGN_JUSTIFY if justificar
                   else fitz.TEXT_ALIGN_LEFT))
        if fundo is not None:
            # overlay=False poe o retangulo ABAIXO do texto ja escrito.
            self.pagina.draw_rect(
                fitz.Rect(MARGEM + recuo - 8, y - 4,
                          MARGEM + LARGURA_UTIL, y + alt + 4),
                color=None, fill=fundo, overlay=False)

    def altura_de(self, txt, corpo, fonte, recuo=0):
        """Quanto a TINTA vai ocupar, medida no bbox do que fica desenhado
        numa pagina descartavel de mesma largura."""
        rascunho = fitz.open()
        pg = rascunho.new_page(width=LARGURA, height=ALTURA)
        topo = MARGEM
        caixa = fitz.Rect(MARGEM + recuo, topo,
                          MARGEM + recuo + LARGURA_UTIL - recuo,
                          ALTURA - MARGEM - 18)
        # O MESMO ALINHAMENTO DA ESCRITA: justificado e alinhado a esquerda
        # quebram nos mesmos pontos, mas medir com um e escrever com outro
        # e o tipo de descuido que so aparece quando a conta erra.
        sobra = pg.insert_textbox(caixa, txt, fontsize=corpo, fontname=fonte,
                                  lineheight=ENTRELINHA,
                                  align=fitz.TEXT_ALIGN_JUSTIFY)
        if sobra < 0:
            rascunho.close()
            return caixa.height          # nao coube: quem chama decide
        blocos = [b for b in pg.get_text("blocks") if b[6] == 0]
        alt = (max(b[3] for b in blocos) - topo) if blocos else 0.0
        rascunho.close()
        return alt

    def juntar(self, alturas):
        """Vira a folha ANTES do bloco quando o conjunto nao cabe. Sem
        isto, a etiqueta do item ficava no pe de uma pagina e o trecho
        citado abria a seguinte, que e o item partido justamente onde ele
        precisa estar inteiro."""
        if not self.cabe(sum(alturas)):
            self.nova()

    def regua(self):
        if not self.cabe(14):
            self.nova()
            return
        self.pagina.draw_line(fitz.Point(MARGEM, self.y),
                              fitz.Point(MARGEM + LARGURA_UTIL, self.y),
                              color=(0.86, 0.86, 0.88), width=0.6)
        self.y += 12


def numerar_paginas(doc):
    for i, p in enumerate(doc, 1):
        p.insert_text(fitz.Point(LARGURA / 2 - 6, ALTURA - MARGEM + 12),
                      str(i), fontsize=9, fontname="tiro", color=COR_FRACA)


def tabela(f, cabecalho, linhas, larguras, corpo=10):
    """Uma tabela, com o cabecalho repetido quando a folha vira.

    As larguras vem em fracoes da largura util. Celula que nao cabe QUEBRA
    EM DUAS LINHAS, e nunca e cortada: numero cortado numa ficha de
    selecao e o pior defeito possivel, e ele tem a aparencia de numero.
    """
    total = sum(larguras)
    cols = [LARGURA_UTIL * w / total for w in larguras]

    def altura_da(celulas, fonte):
        return max(f.altura_de(str(c), corpo, fonte,
                               recuo=LARGURA_UTIL - cols[k] + 10)
                   for k, c in enumerate(celulas))

    def escrever(celulas, fonte, fundo=None):
        alt = altura_da(celulas, fonte)
        if not f.cabe(alt + 6):
            f.nova()
            escrever(cabecalho, "hebo", (0.93, 0.92, 0.90))
            alt = altura_da(celulas, fonte)
        y = f.y
        if fundo is not None:
            f.pagina.draw_rect(
                fitz.Rect(MARGEM - 4, y - 3,
                          MARGEM + LARGURA_UTIL + 4, y + alt + 3),
                color=None, fill=fundo, overlay=False)
        x = MARGEM
        for k, c in enumerate(celulas):
            f.pagina.insert_textbox(
                fitz.Rect(x, y, x + cols[k] - 8, y + alt + 4), str(c),
                fontsize=corpo, fontname=fonte, color=COR_TINTA,
                lineheight=ENTRELINHA, align=fitz.TEXT_ALIGN_LEFT)
            x += cols[k]
        f.y = y + alt + 6

    escrever(cabecalho, "hebo", (0.93, 0.92, 0.90))
    for i, linha in enumerate(linhas):
        escrever(linha, "helv", (0.975, 0.972, 0.965) if i % 2 else None)
    f.y += 6



def escapar_html(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class _MetodosHtml:
    """Os dois metodos que a Folha ganha para escrever com negrito no meio."""


def _html_altura(self, html, recuo=0):
    """A tinta que o bloco html vai ocupar, medida numa pagina
    descartavel de mesma largura."""
    rascunho = fitz.open()
    pg = rascunho.new_page(width=LARGURA, height=ALTURA)
    caixa = fitz.Rect(MARGEM + recuo, MARGEM,
                      MARGEM + LARGURA_UTIL, ALTURA - MARGEM - 18)
    pg.insert_htmlbox(caixa, html)
    blocos = [b for b in pg.get_text("blocks") if b[6] == 0]
    alt = (max(b[3] for b in blocos) - MARGEM) if blocos else 0.0
    rascunho.close()
    return alt


def _marcar(texto, estilo):
    """O pedaco com a etiqueta que ele pede: nada, negrito ou italico."""
    s = escapar_html(texto)
    if estilo in (True, "b"):
        return "<b>%s</b>" % s
    if estilo == "i":
        return "<i>%s</i>" % s
    return s


def _montar_html(partes, corpo):
    return ('<div style="font-family:Times;font-size:%gpx;line-height:%g;'
            'text-align:justify">%s</div>'
            % (corpo, ENTRELINHA,
               "".join(_marcar(txt, est) for txt, est in partes)))


def _em_palavras(partes):
    """Desmancha as partes em (pedaco, estilo).

    O ESPACO QUE SEGUE CADA PALAVRA VIAJA PRESO A ELA. Colar os pedacos
    de volta com espaco unico inventa espaco onde nao havia: "A " mais
    "Metodologia" em italico mais " e a " voltava como "A Metodologiae
    a", e ". " voltaria como " . ".
    """
    fora = []
    for texto, estilo in partes:
        for m in re.finditer(r"\S+\s*|\s+", texto):
            fora.append((m.group(0), estilo))
    return fora


def _juntar_palavras(palavras):
    """Refaz as partes, colando pedacos vizinhos de mesmo estilo."""
    partes = []
    for pedaco, estilo in palavras:
        if partes and partes[-1][1] == estilo:
            partes[-1][0] += pedaco
        else:
            partes.append([pedaco, estilo])
    return [(a, b) for a, b in partes]


def _html(self, partes, corpo=None, recuo=0, espaco_antes=0, espaco_depois=6,
          partir=True):
    """Escreve um paragrafo com trechos em negrito ou italico.

    partes e uma lista de (texto, estilo), com estilo em None, "b" ou
    "i" (True e False continuam valendo, do tempo em que so havia
    negrito).

    E ELE PARTE ENTRE PAGINAS quando nao couber, deixando pelo menos duas
    linhas de cada lado: paragrafo inteiro empurrado para a pagina
    seguinte deixa meia folha em branco no meio da peca.
    """
    corpo = corpo or CORPO
    while True:
        html = _montar_html(partes, corpo)
        alt = self.altura_html(html, recuo)
        if self.cabe(espaco_antes + alt + espaco_depois):
            break
        if not partir:
            self.nova()
            espaco_antes = 0
            break
        palavras = _em_palavras(partes)
        disponivel = (ALTURA - MARGEM - 18) - (self.y + espaco_antes)
        minimo = MINIMO_DE_LINHAS * corpo * ENTRELINHA
        cabe_aqui = 0
        if disponivel >= minimo and len(palavras) > 2 * MINIMO_DE_LINHAS:
            baixo, cima = 1, len(palavras) - 1
            while baixo <= cima:
                meio = (baixo + cima) // 2
                a = self.altura_html(
                    _montar_html(_juntar_palavras(palavras[:meio]), corpo),
                    recuo)
                if a <= disponivel:
                    cabe_aqui = meio
                    baixo = meio + 1
                else:
                    cima = meio - 1
        if not cabe_aqui:
            self.nova()
            espaco_antes = 0
            continue
        # O RESTO TEM DE FICAR COM DUAS LINHAS, e nao com uma orfa: se
        # ficar curto demais, o corte recua ate sobrar o bastante.
        while cabe_aqui > 1:
            resto = _juntar_palavras(palavras[cabe_aqui:])
            if self.altura_html(_montar_html(resto, corpo), recuo) >= minimo:
                break
            cabe_aqui -= 1
        if cabe_aqui <= 1:
            self.nova()
            espaco_antes = 0
            continue
        aqui = _juntar_palavras(palavras[:cabe_aqui])
        html_aqui = _montar_html(aqui, corpo)
        alt_aqui = self.altura_html(html_aqui, recuo)
        y = self.y + espaco_antes
        self.pagina.insert_htmlbox(
            fitz.Rect(MARGEM + recuo, y, MARGEM + LARGURA_UTIL,
                      ALTURA - MARGEM - 18), html_aqui)
        self.y = y + alt_aqui
        self.nova()
        partes = _juntar_palavras(palavras[cabe_aqui:])
        espaco_antes = 0

    y = self.y + espaco_antes
    self.pagina.insert_htmlbox(
        fitz.Rect(MARGEM + recuo, y, MARGEM + LARGURA_UTIL,
                  ALTURA - MARGEM - 18), _montar_html(partes, corpo))
    self.y = y + self.altura_html(_montar_html(partes, corpo), recuo) \
        + espaco_depois


Folha.altura_html = _html_altura
Folha.html = _html


def conferir_sobreposicao(doc, folga=0.5):
    """Devolve a lista de sobreposicoes de tinta, pagina a pagina.

    POR QUE ISTO EXISTE. Sobreposicao so aparece a olho, e a olho so
    aparece quando alguem olha. Quatro pecas sairam hoje com um titulo
    desenhado por cima da ultima linha do paragrafo anterior, e ninguem
    olhou a pagina em que estava.

    A FOLGA existe porque bloco vizinho pode encostar por meio ponto sem
    que isso seja defeito; sobreposicao de verdade e de linha inteira.
    """
    achados = []
    for pg in doc:
        blocos = sorted((b for b in pg.get_text("blocks") if b[6] == 0),
                        key=lambda b: b[1])
        for i in range(1, len(blocos)):
            de_cima, de_baixo = blocos[i - 1], blocos[i]
            if de_baixo[1] < de_cima[3] - folga:
                achados.append(
                    "pagina %d: %r comeca em %.1f e o bloco acima acaba em "
                    "%.1f" % (pg.number + 1,
                              " ".join(de_baixo[4].split())[:40],
                              de_baixo[1], de_cima[3]))
    return achados


def gravar(doc, caminho):
    """Grava, e so grava se nada se sobrepuser."""
    achados = conferir_sobreposicao(doc)
    if achados:
        for a in achados:
            print("  SOBREPOSICAO: " + a)
        sys.exit("PAREI: ha texto desenhado por cima de texto. Nada foi "
                 "gravado.")
    doc.save(caminho)


def provar_a_folha():
    """Controle positivo do conferidor de sobreposicao."""
    bom = fitz.open()
    f = Folha(bom)
    for i in range(6):
        f.texto("Paragrafo %d. " % i + "Palavra " * 60)
    ruim = fitz.open()
    pg = ruim.new_page(width=LARGURA, height=ALTURA)
    pg.insert_textbox(fitz.Rect(MARGEM, 100, MARGEM + LARGURA_UTIL, 300),
                      "Primeiro bloco. " + "Palavra " * 40, fontsize=CORPO,
                      fontname="tiro")
    pg.insert_textbox(fitz.Rect(MARGEM, 110, MARGEM + LARGURA_UTIL, 300),
                      "Segundo bloco, desenhado por cima do primeiro.",
                      fontsize=CORPO, fontname="tibo")

    casos = [("uma folha montada pela Folha", bom, 0),
             ("dois blocos desenhados por cima", ruim, 1)]
    print("Controle positivo do conferidor de sobreposicao:")
    ok = True
    for nome, doc, esperados in casos:
        houve = len(conferir_sobreposicao(doc))
        certo = (houve == 0) == (esperados == 0)
        ok = ok and certo
        print("  %-36s %d achado(s), esperava %s  %s"
              % (nome, houve, "nenhum" if esperados == 0 else "algum",
                 "ok" if certo else "DIVERGIU"))
    bom.close()
    ruim.close()
    print()
    print("O conferidor separa os casos." if ok
          else "O CONFERIDOR NAO SEPARA OS CASOS.")
    return ok
