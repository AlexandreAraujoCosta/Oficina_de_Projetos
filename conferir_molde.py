# -*- coding: utf-8 -*-
"""Confere o molde do bloco de dados contra as regras do proprio prompt.

Regras conferidas, todas enunciadas no prompt_selma.md:
  (a) o nivel da dimensao 5 e um dos cinco valores admitidos;
  (b) a dimensao 5 leva tres tracos nos campos de contagem;
  (c) cada CONDICAO corresponde a um grave ou a um medio contado na
      dimensao dela, e cada grave ou medio produz uma condicao.

CONTROLE POSITIVO: o conferidor roda antes sobre dois moldes fabricados,
um correto e um adulterado, e tem de aprovar o primeiro e reprovar o
segundo. Sem isso o silencio dele nao informa nada.
"""
import io
import re

PROMPT = "D:/Claude/Oficina_de_Projetos/prompt_selma.md"
NIVEIS = {"fortes-abusivo", "fortes", "medios", "fracos", "ausentes"}


def bloco(texto):
    i = texto.find("\nDADOS\n")
    j = texto.find("\nFIM\n", i)
    if i < 0 or j < 0:
        return None
    return texto[i + 1:j].split("\n")


def conferir(linhas):
    faltas = []
    contagem = {}
    condicoes = {}
    for l in linhas:
        campos = [c.strip() for c in l.split("|")]
        if len(campos) == 6 and campos[0].isdigit():
            n = campos[0]
            if n == "5":
                if campos[2:5] != ["-", "-", "-"]:
                    faltas.append("a dimensao 5 devia levar tres tracos, e leva %r"
                                  % campos[2:5])
                if campos[5] not in NIVEIS:
                    faltas.append("o nivel da dimensao 5 e %r, fora dos cinco admitidos"
                                  % campos[5])
            else:
                try:
                    contagem[n] = int(campos[2]) + int(campos[3])
                except ValueError:
                    faltas.append("a dimensao %s tem contagem ilegivel" % n)
        elif campos and campos[0] == "CONDICAO":
            condicoes[campos[1]] = condicoes.get(campos[1], 0) + 1
    for n, quantos in sorted(contagem.items()):
        tem = condicoes.get(n, 0)
        if quantos != tem:
            faltas.append("a dimensao %s conta %d achado(s) grave ou medio e tem "
                          "%d condicao(oes)" % (n, quantos, tem))
    for n in condicoes:
        if n not in contagem:
            faltas.append("ha condicao na dimensao %s, que nao tem contagem" % n)
    return faltas


CERTO = """DADOS
TITULO | P002
IMPRESSAO | 172p-a51ff850
1 | um | 0 | 1 | 1 | 5
2 | dois | 0 | 0 | 2 | 8
5 | indicios de ia | - | - | - | fracos
CONDICAO | 1 | fazer alguma coisa
FIM
"""

ERRADO = """DADOS
TITULO | P002
IMPRESSAO | 172p-a51ff850
1 | um | 1 | 0 | 0 | 4
2 | dois | 0 | 1 | 0 | 6
5 | indicios de ia | - | - | - | leves
CONDICAO | 2 | fazer alguma coisa
CONDICAO | 2 | fazer outra
FIM
"""


def main():
    ok = conferir(bloco("\n" + CERTO))
    ruim = conferir(bloco("\n" + ERRADO))
    print("controle positivo:")
    print("  molde correto  ->", ok or "aprovado (esperado)")
    print("  molde adulterado ->", "%d falta(s) (esperado)" % len(ruim) if ruim
          else "APROVOU, e nao devia")
    if ok or len(ruim) < 3:
        raise SystemExit("o conferidor esta quebrado; nao use o resultado")

    texto = io.open(PROMPT, encoding="utf-8").read()
    linhas = bloco(texto)
    if linhas is None:
        raise SystemExit("nao achei o bloco DADOS no prompt")
    faltas = conferir(linhas)
    print("\no molde publicado, no prompt_selma.md:")
    if not faltas:
        print("  conforme")
    for f in faltas:
        print("  -", f)


if __name__ == "__main__":
    main()
