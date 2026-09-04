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

import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Falta o PyMuPDF. Instale com: pip install pymupdf")


LARGURA, ALTURA = fitz.paper_size("a4")
MARGEM = 62
LARGURA_UTIL = LARGURA - 2 * MARGEM

CORPO = 10.5
ENTRELINHA = 1.42
COR_TINTA = (0.12, 0.12, 0.13)
COR_FRACA = (0.42, 0.42, 0.45)
COR_MARCA = (0.62, 0.42, 0.10)
COR_FUNDO = (0.975, 0.965, 0.94)


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
              recuo=0, espaco_antes=0, espaco_depois=6, fundo=None):
        """Escreve e desce o cursor pela altura QUE O PYMUPDF DIZ TER
        USADO, e nao por uma altura que eu calcule antes.

        A PRIMEIRA VERSAO MEDIA A ALTURA POR CONTA PROPRIA e passava a
        caixa justa. insert_textbox precisa de folga (ascendente e
        descendente da fonte) e devolvia negativo, que e o sinal de nao
        coube; o meu tratamento de nao coube consumia o resto da pagina,
        e sete itens sairam em vinte e cinco paginas. Agora a caixa vai
        ate a margem de baixo e a altura usada e a caixa menos a sobra.
        """
        largura = LARGURA_UTIL - recuo
        fundo_da_pagina = ALTURA - MARGEM - 18

        def tentar(y):
            caixa = fitz.Rect(MARGEM + recuo, y,
                              MARGEM + recuo + largura, fundo_da_pagina)
            sobra = self.pagina.insert_textbox(
                caixa, txt, fontsize=corpo, fontname=fonte, color=cor,
                lineheight=ENTRELINHA, align=fitz.TEXT_ALIGN_LEFT)
            return sobra, caixa

        y = self.y + espaco_antes
        sobra, caixa = tentar(y)
        if sobra < 0:                       # nao coube nesta pagina
            self.nova()
            y = self.y
            sobra, caixa = tentar(y)
            if sobra < 0:
                sys.exit("ERRO: um bloco nao cabe nem numa pagina inteira. "
                         "Encurte o comentario.")
        usada = caixa.height - sobra
        if fundo is not None:
            # overlay=False poe o retangulo ABAIXO do texto ja escrito.
            self.pagina.draw_rect(
                fitz.Rect(MARGEM + recuo - 8, y - 4,
                          MARGEM + LARGURA_UTIL, y + usada + 4),
                color=None, fill=fundo, overlay=False)
        self.y = y + usada + espaco_depois

    def altura_de(self, txt, corpo, fonte, recuo=0):
        """Quanto o bloco vai ocupar, medido pelo MESMO motor que escreve,
        numa pagina descartavel. Medir por conta propria e o que ja errou
        uma vez aqui."""
        rascunho = fitz.open()
        pg = rascunho.new_page(width=LARGURA, height=ALTURA)
        caixa = fitz.Rect(MARGEM + recuo, MARGEM,
                          MARGEM + recuo + LARGURA_UTIL - recuo,
                          ALTURA - MARGEM - 18)
        sobra = pg.insert_textbox(caixa, txt, fontsize=corpo, fontname=fonte,
                                  lineheight=ENTRELINHA,
                                  align=fitz.TEXT_ALIGN_LEFT)
        rascunho.close()
        return caixa.height - sobra if sobra >= 0 else caixa.height

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


def tabela(f, cabecalho, linhas, larguras, corpo=9):
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
