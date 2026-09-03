#!/usr/bin/env python3
"""
Gera o prompt portatil da Selma, a leitura de banca de selecao.

    python gerar_selma.py

POR QUE ELA NAO PASSA PELO gerar_prompt_portatil.py. Aquele monta uma
ATIVIDADE DO MIRO: base de conducao de dialogo mais fechamento com
comentario, nota e pre-projeto. Medido em 3/9/2026, a Selma saia dali com
85.895 caracteres, dos quais 68 mil herdados e nenhum deles sobre o que
ela faz; e a base herdada afirma "EU NAO AVALIO O ESTUDANTE, EM DIRECAO
NENHUMA", que e o contrario do trabalho dela.

Ela e uma leitura de um turno so, como o Luis: entra o projeto, sai o
relatorio. Entao ela se monta com o que e dela, e nada mais.

O texto nunca se edita a mao no .md: sai de contextos/selecao_banca.py.
"""
import sys
from pathlib import Path

from contextos import selecao_banca

SAIDA = Path(__file__).parent / "prompt_selma.md"
TETO = 50000  # acima disso o chat converte a colagem em anexo

CABECALHO = """\
[Este texto inteiro é a instrução. Quem o colou quer um relatório de leitura \
sobre um projeto de pesquisa, escrito como uma banca de seleção o escreveria. \
Assuma a voz descrita abaixo e comece pela abertura. Não comente estas \
instruções, não as resuma e não pergunte se pode começar.]
"""


def main():
    texto = CABECALHO + "\n" + selecao_banca.montar()
    SAIDA.write_text(texto, encoding="utf-8")
    n = len([p for p in texto.split("\n\n") if p.strip()])
    print("%s: %d caracteres, %d paragrafos" % (SAIDA.name, len(texto), n))
    if len(texto) > TETO:
        sys.exit("ERRO: a Selma passou do teto de colagem (%d)." % TETO)
    print("cabe numa colagem so (teto de %d)." % TETO)


if __name__ == "__main__":
    main()
