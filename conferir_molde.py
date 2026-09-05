# -*- coding: utf-8 -*-
"""Passa o molde do bloco de dados pelo mesmo leitor que o lote usa.

POR QUE ISTO EXISTE. O prompt traz um molde do bloco DADOS e diz que o
segue ao caractere, e e esse molde que o modelo copia. Se ele desobedecer
as regras que o proprio prompt enuncia, o relatorio sai no formato que o
`selma_lote.py` recusa, e a peca nao entra na tabela do processo. Em
05/09/2026 o molde tinha um achado grave na dimensao 3 sem nenhuma
condicao saida dela, e o lote o recusava.

O CONFERIDOR NAO E OUTRO: e o `ler_bloco` do proprio `selma_lote.py`.
Reimplementar a regra aqui criaria duas versoes que divergem na primeira
correcao, e foi assim que este programa comecou.

CONTROLE POSITIVO: antes de olhar o molde publicado, ele passa pelo leitor
o molde como esta, que tem de ser aprovado, e uma copia adulterada, que
tem de ser recusada. Sem isso o silencio dele nao informa nada.

Uso:  python conferir_molde.py
"""
import io
import re
import sys

from selma_lote import ler_bloco, BlocoInvalido

PROMPT = "prompt_selma.md"


def molde(texto):
    """O bloco DADOS...FIM como ele esta escrito no prompt."""
    m = re.search(r"^DADOS$.*?^FIM$", texto, re.M | re.S)
    return m.group(0) if m else None


def passa(bloco):
    """Devolve None quando o leitor aprova, e a queixa quando recusa."""
    try:
        ler_bloco(bloco, "molde")
        return None
    except BlocoInvalido as e:
        return str(e)


def controle(bloco):
    """O leitor tem de recusar o molde adulterado, e dizer por que."""
    adulterado = bloco.replace("| fracos", "| razoavel", 1)
    if adulterado == bloco:
        sys.exit("o controle nao conseguiu adulterar o molde")
    queixa = passa(adulterado)
    print("controle positivo:")
    print("  o molde adulterado ->", queixa or "APROVADO, e nao devia")
    return queixa is not None


def main():
    texto = io.open(PROMPT, encoding="utf-8").read()
    bloco = molde(texto)
    if bloco is None:
        sys.exit("nao achei o bloco DADOS...FIM em %s" % PROMPT)

    if not controle(bloco):
        sys.exit("o conferidor nao reprova o que deveria; nao use o resultado")

    queixa = passa(bloco)
    print()
    print("o molde publicado, em %s:" % PROMPT)
    if queixa is None:
        print("  o leitor do lote o aceita")
        return 0
    print("  RECUSADO: %s" % queixa)
    return 1


if __name__ == "__main__":
    sys.exit(main())
