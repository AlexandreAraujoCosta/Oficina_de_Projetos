#!/usr/bin/env python3
"""
Monta, em PDF, o relatorio que o assistente escreveu sobre um projeto que
chegou em PDF.

    python relatorio_pdf.py projeto.pdf --numerar
    python relatorio_pdf.py projeto.pdf --relatorio rel.md -o relatorio.pdf
    python relatorio_pdf.py projeto.pdf --provar

POR QUE ISTO EXISTE. O Miro trabalha com .docx e .md, que ele comenta por
dentro. Projeto que chega em PDF nao entra nesse caminho: converter
reconstroi o documento, e reconstrucao tem defeito medido (num projeto
real, o texto das notas de rodape saiu como paragrafo do corpo). Entao o
PDF recebe um RELATORIO, que e documento novo e nao mexe no do autor.

E O TRECHO CITADO E COPIADO POR ESTE PROGRAMA, nunca digitado pelo
assistente. O assistente escreve LOCALIZADOR E COMENTARIO; o programa
abre o PDF, acha o paragrafo daquele numero e copia o texto para o
relatorio. E a mesma regra dos outros programas da familia, e aqui ela
importa mais, porque o relatorio EXIBE o trecho: quem le confere abrindo
o projeto, e uma palavra trocada na citacao descaracteriza a conferencia.

O FLUXO TEM DOIS PASSOS.

  1. --numerar lista os paragrafos com [P001], [P002], exatamente como o
     comentar_pdf.py (os dois usam a mesma leitura, entao os numeros sao
     os mesmos). O autor cola a lista na conversa.

  2. O assistente escreve o relatorio num arquivo de texto:

         # Titulo do relatorio
         ## Problema e justificativa
         Um paragrafo de prosa, que sai como prosa.
         P016 > A frase que declara ... esta redigida como conclusao
           fechada; reescrever como expectativa de trabalho.

     Linha comecada por dois espacos continua o item anterior. Linha em
     branco separa paragrafos. Localizador que o documento nao tem faz o
     programa parar e dizer qual e, em vez de escolher o mais parecido.

O QUE O RELATORIO MOSTRA EM CADA ITEM: o numero do paragrafo, a pagina do
projeto em que ele esta, o trecho copiado (cortado com reticencias quando
e longo, e o corte e no fim, nunca no meio) e o comentario do assistente.

E ELE CONFERE O QUE PROMETE. Antes de gravar, compara palavra a palavra
cada trecho que vai para o relatorio com o paragrafo de onde ele saiu. Se
divergir, nao grava e diz onde. --provar mostra o conferidor reprovando
uma citacao alterada de proposito, antes que voce confie no silencio
dele.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from comentar_pdf import ler as ler_paragrafos

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

PALAVRAS_DO_TRECHO = 45          # o trecho citado corta aqui, e so no fim

RE_ITEM = re.compile(r"^\s*\[?\s*P?\s*(\d{1,4})\s*\]?\s*[>:–—-]\s*(.+?)\s*$", re.I)


# ---------------------------------------------------------------- leitura

def ler_relatorio(bruto):
    """Devolve a lista de pecas: ("titulo"|"secao"|"prosa"|"item", ...)."""
    pecas = []
    for linha in bruto.splitlines():
        if not linha.strip():
            pecas.append(("branco", None))
            continue
        m = RE_ITEM.match(linha)
        if m:
            pecas.append(("item", (int(m.group(1)), m.group(2))))
        elif pecas and pecas[-1][0] == "item" and re.match(r"^\s{2,}\S", linha):
            n, t = pecas[-1][1]
            pecas[-1] = ("item", (n, t + " " + linha.strip()))
        elif linha.startswith("## "):
            pecas.append(("secao", linha[3:].strip()))
        elif linha.startswith("# "):
            pecas.append(("titulo", linha[2:].strip()))
        elif pecas and pecas[-1][0] == "prosa":
            pecas[-1] = ("prosa", pecas[-1][1] + " " + linha.strip())
        else:
            pecas.append(("prosa", linha.strip()))
    pecas = [p for p in pecas if p[0] != "branco"]

    # ITENS SEGUIDOS NO MESMO PARAGRAFO VIRAM UM SO, com os comentarios
    # em lista. Sem isto, o paragrafo que recebe dois comentarios sai com
    # o trecho citado repetido inteiro, e o leitor le a mesma citacao
    # duas vezes para chegar ao segundo comentario.
    juntos = []
    for tipo, dado in pecas:
        if (tipo == "item" and juntos and juntos[-1][0] == "item"
                and juntos[-1][1][0] == dado[0]):
            juntos[-1][1][1].append(dado[1])
        elif tipo == "item":
            juntos.append(("item", (dado[0], [dado[1]])))
        else:
            juntos.append((tipo, dado))
    return juntos


def cortar(texto, quantas=PALAVRAS_DO_TRECHO):
    """Corta no fim, e nunca no meio: o leitor tem de saber que ha mais."""
    ps = texto.split()
    if len(ps) <= quantas:
        return texto, False
    # TRES PONTOS, E NAO O CARACTERE DE RETICENCIAS. As fontes base-14 do
    # PDF sao WinAnsi, e U+2026 nao esta la: o que aparecia na pagina era
    # um ponto de interrogacao no fim de toda citacao cortada.
    return " ".join(ps[:quantas]) + " ...", True


# ---------------------------------------------------------------- escrita

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


def montar(pecas, paragrafos, nome_projeto, saida):
    doc = fitz.open()
    f = Folha(doc)
    citados = []                      # (numero, trecho escrito) para conferir

    tem_titulo = any(p[0] == "titulo" for p in pecas)
    if not tem_titulo:
        f.texto("Relatorio sobre " + nome_projeto, corpo=17, fonte="tibo",
                espaco_depois=4)
        f.texto("Os trechos citados foram copiados do proprio projeto por "
                "programa. O numero entre colchetes e o do paragrafo na "
                "numeracao que acompanha este relatorio.",
                corpo=9, fonte="tiit", cor=COR_FRACA, espaco_depois=14)

    for tipo, dado in pecas:
        if tipo == "titulo":
            f.texto(dado, corpo=17, fonte="tibo", espaco_depois=4)
            f.texto("Os trechos citados foram copiados do proprio projeto "
                    "por programa. O numero entre colchetes e o do paragrafo "
                    "na numeracao que acompanha este relatorio.",
                    corpo=9, fonte="tiit", cor=COR_FRACA, espaco_depois=14)
        elif tipo == "secao":
            f.juntar([14, f.altura_de(dado, 12.5, "tibo"), 6, 7, 46])
            f.regua()
            f.texto(dado, corpo=12.5, fonte="tibo", espaco_antes=6,
                    espaco_depois=7)
        elif tipo == "prosa":
            f.texto(dado, espaco_depois=8)
        else:
            n, comentarios = dado
            p = paragrafos[n - 1]
            trecho, cortado = cortar(p["texto"])
            citados.append((n, trecho, cortado))
            etiqueta = "[P%03d]  pagina %d do projeto" % (n, p["pagina"] + 1)
            f.juntar([8,
                      f.altura_de(etiqueta, 8.5, "tibo"), 3,
                      f.altura_de(trecho, 9.5, "tiit", recuo=14), 5,
                      sum(f.altura_de(c, CORPO, "tiro", recuo=14) + 4
                          for c in comentarios)])
            f.texto(etiqueta, corpo=8.5, fonte="tibo", cor=COR_MARCA,
                    espaco_antes=8, espaco_depois=3)
            f.texto(trecho, corpo=9.5, fonte="tiit", cor=COR_FRACA, recuo=14,
                    espaco_depois=5, fundo=COR_FUNDO)
            for k, c in enumerate(comentarios):
                if len(comentarios) > 1:
                    c = "%d. %s" % (k + 1, c)
                f.texto(c, recuo=14,
                        espaco_depois=10 if k == len(comentarios) - 1 else 5)

    numerar_paginas(doc)
    doc.save(saida)
    doc.close()
    return citados


# ------------------------------------------------------------- conferidor

def conferir_citacoes(citados, paragrafos, saida):
    """Compara, palavra a palavra, o que foi escrito no relatorio com o
    paragrafo de onde saiu. Le do PDF GRAVADO, e nao da variavel: o que
    interessa e o que o leitor vai ver."""
    doc = fitz.open(saida)
    pagina_toda = " ".join(p.get_text() for p in doc).split()
    doc.close()

    for n, trecho, cortado in citados:
        origem = paragrafos[n - 1]["texto"].split()
        escrito = trecho.rstrip(". ").split()
        if escrito != origem[:len(escrito)]:
            for i, (a, b) in enumerate(zip(escrito, origem)):
                if a != b:
                    return ("P%03d: a citacao diz %r onde o projeto diz %r "
                            "(palavra %d)" % (n, a, b, i + 1))
            return "P%03d: a citacao tem tamanho diferente do paragrafo" % n
        if not cortado and len(escrito) != len(origem):
            return ("P%03d: a citacao nao foi cortada e tem %d palavras "
                    "contra %d do paragrafo" % (n, len(escrito), len(origem)))
        # e ela tem de estar mesmo na pagina gravada
        if escrito and escrito[0] not in pagina_toda:
            return "P%03d: a citacao nao aparece no PDF gravado" % n
    return None


def provar(caminho):
    """Controle positivo. Sem ele, o silencio do conferidor nao informa
    nada: conferidor quebrado e conferidor satisfeito tem a mesma cara."""
    paragrafos = ler_paragrafos(caminho)
    n = 1
    for i, p in enumerate(paragrafos, 1):
        if len(p["texto"].split()) > 25:
            n = i
            break
    original = paragrafos[n - 1]["texto"]
    trecho, cortado = cortar(original)

    fingido = "_prova_relatorio.pdf"
    doc = fitz.open()
    pg = doc.new_page(width=LARGURA, height=ALTURA)
    pg.insert_textbox(fitz.Rect(MARGEM, MARGEM, LARGURA - MARGEM,
                                ALTURA - MARGEM), trecho, fontsize=10,
                      fontname="tiro")
    doc.save(fingido)
    doc.close()

    trocado = trecho.split()
    trocado[3] = "PALAVRATROCADA"
    faltando = " ".join(trecho.split()[:-3]) + (" ..." if cortado else "")

    casos = [
        ("a citacao como o projeto a tem",
         conferir_citacoes([(n, trecho, cortado)], paragrafos, fingido), True),
        ("uma palavra trocada na citacao",
         conferir_citacoes([(n, " ".join(trocado), cortado)], paragrafos,
                           fingido), False),
        ("a citacao encurtada sem reticencias",
         conferir_citacoes([(n, faltando.rstrip(" ."), False)],
                           paragrafos, fingido), False),
    ]
    print("Controle positivo do conferidor de citacao:")
    ok = True
    for nome, r, esperado in casos:
        passou = r is None
        certo = passou == esperado
        ok = ok and certo
        print("  %-38s %-9s %s" % (nome, "passou" if passou else "reprovou",
                                   "ok" if certo else "DIVERGIU"))
    for nome, r, esperado in casos:
        if r and not esperado:
            print()
            print("  o que ele disse: " + r)
            break
    Path(fingido).unlink(missing_ok=True)
    print()
    print("O conferidor separa os casos." if ok
          else "O CONFERIDOR NAO SEPARA OS CASOS. Nao use o resultado.")
    return 0 if ok else 1


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n")[1],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", help="o projeto, em PDF")
    ap.add_argument("--numerar", action="store_true",
                    help="lista os paragrafos com [P001]")
    ap.add_argument("--relatorio", help="o arquivo que o assistente escreveu")
    ap.add_argument("-o", "--saida", help="o relatorio em PDF")
    ap.add_argument("--provar", action="store_true",
                    help="mostra o conferidor reprovando de proposito")
    a = ap.parse_args()

    entrada = Path(a.pdf)
    if not entrada.is_file():
        sys.exit("Nao achei %s." % entrada)

    if a.provar:
        return provar(str(entrada))

    paragrafos = ler_paragrafos(str(entrada))

    if a.numerar:
        for i, p in enumerate(paragrafos, 1):
            print("[P%03d] %s" % (i, p["texto"]))
            print()
        print("%d paragrafos." % len(paragrafos), file=sys.stderr)
        return 0

    if not a.relatorio:
        sys.exit("Sem --numerar e sem --relatorio nao ha o que fazer. "
                 "Comece por --numerar.")

    pecas = ler_relatorio(Path(a.relatorio).read_text(encoding="utf-8"))
    itens = [d[0] for t, d in pecas if t == "item"]
    quantos_comentarios = sum(len(d[1]) for t, d in pecas if t == "item")
    if not itens:
        sys.exit("Nenhum item com localizador em %s. Eles tem a forma "
                 "P004 > comentario." % a.relatorio)

    fora = sorted({n for n in itens if not 1 <= n <= len(paragrafos)})
    if fora:
        sys.exit("O relatorio aponta paragrafos que o projeto nao tem: %s.\n"
                 "Ele vai de P001 a P%03d. Numere-o com --numerar e peca ao "
                 "assistente que refaca com esses numeros. Eu nao escolho o "
                 "paragrafo mais parecido."
                 % (", ".join("P%03d" % n for n in fora), len(paragrafos)))

    saida = Path(a.saida) if a.saida else entrada.with_name(
        entrada.stem + "-relatorio.pdf")
    citados = montar(pecas, paragrafos, entrada.stem, str(saida))

    defeito = conferir_citacoes(citados, paragrafos, str(saida))
    if defeito:
        saida.unlink(missing_ok=True)
        sys.exit("PAREI: %s.\nO relatorio teria exibido como citacao um "
                 "texto que o projeto nao tem. Nada foi produzido." % defeito)

    doc = fitz.open(str(saida))
    paginas = doc.page_count
    doc.close()
    print("%s: %d comentarios em %d paragrafos, em %d paginas."
          % (saida.name, quantos_comentarios, len(itens), paginas))
    print("Os %d trechos citados foram copiados do projeto e conferidos "
          "palavra a palavra. Use --provar para ver o conferidor reprovar de "
          "proposito." % len(citados))
    return 0


if __name__ == "__main__":
    sys.exit(main())
