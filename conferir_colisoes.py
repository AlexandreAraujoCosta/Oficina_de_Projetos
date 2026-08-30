#!/usr/bin/env python3
"""
Acha os pontos em que duas regras do prompt se atropelam.

    python conferir_colisoes.py prompt.md
    python conferir_colisoes.py prompt.md --relatorios pasta/

POR QUE ISTO EXISTE. Num prompt grande o defeito que sobra nao e regra
ruim: e duas regras boas que se encontram e nao dizem qual cede. Numa
sessao de medicao, doze dos defeitos achados foram desse tipo e nenhum
foi regra ruim. E o paradoxo e pior que a lacuna: falta de instrucao
aparece como ausencia, e o modelo pergunta ou improvisa a vista; colisao
aparece como o modelo escolhendo um lado EM SILENCIO, e a escolha varia
de modelo para modelo e de momento para momento.

DUAS FONTES, E A SEGUNDA VALE MAIS.

  OBSERVADA (--relatorios): varre relatorios de teste atras das frases em
  que o modelo declara ter tido de decidir. Sao colisoes que DISPARARAM,
  e nao que poderiam disparar. Modelo com reflexividade alta escreve os
  passos, e e nesses passos que a colisao aparece; por isso a fonte
  melhora quando se aumenta a reflexividade de quem roda o teste.

  ESTATICA (sempre): poe lado a lado os blocos que governam o MESMO
  OBJETO com verbo normativo. Nao decide nada, e nao precisa: a maioria
  das colisoes se ve pondo dois paragrafos um ao lado do outro.

O QUE ELE NAO FAZ. Nao diz qual regra cede, nao mede gravidade e nao
conta achado como defeito. Ele diz onde olhar, e quem le decide. Lista de
pares e material de triagem, e boa parte dela sera coincidencia de
vocabulario.
"""

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

# Os objetos sobre os quais duas regras podem legislar ao mesmo tempo.
# Cada um traz as formas com que aparece no texto.
OBJETOS = {
    "turno": r"\bturnos?\b|\bfala\b|\bpor turno\b",
    "rodada": r"\brodadas?\b",
    "pergunta": r"\bpergunt\w+",
    "abertura": r"\baberturas?\b|primeira (?:fala|mensagem)",
    "fechamento": r"\bfechamento\b|\bencerr\w+",
    "comentario": r"\bcomentários?\b",
    "nota": r"\bnota\b(?! sobre a conversa)|\bnotas\b",
    "pre-projeto": r"pré-projeto",
    "anexo": r"\banexos?\b",
    "titulo": r"\btítulos?\b",
    "revisao": r"revisão de literatura|\brevisão\b",
    "referencia": r"referências?\b|\bobra\b|\bautor\b",
    "endereco": r"endereços?\b|\blink\b",
    "acoplamento": r"acoplad\w+|acoplamento",
    "veredito": r"\bveredito\b|\bestados?\b",
    "relatorio": r"\brelatório\b",
    "leitura": r"\bleituras?\b|\bM[1-5]\b",
    "corte": r"\bcortes?\b|\bcortar\b",
    "busca": r"\bbuscas?\b|\bbuscar\b",
    "localizador": r"localizador\w*",
}

# Verbo que faz do bloco uma regra, e nao uma explicacao.
NORMATIVO = re.compile(
    r"\bNÃO\b|\bNUNCA\b|\bSEMPRE\b|\bSÓ\b|\bAPENAS\b|\bEU RECUSO\b|"
    r"\bobrigatóri\w+|\bproib\w+|\btem de\b|\bdeve\b|\bexige\b", re.I)

# As frases com que um modelo reflexivo declara ter tido de decidir.
# Sao o achado direto: onde elas aparecem, duas regras se encontraram.
MARCAS = [
    (r"a escolha foi minha", "declarou escolha propria"),
    (r"decisão minha|decidi por conta própria|resolvi por", "decidiu sozinho"),
    (r"o prompt não (?:diz|resolve|dá|prevê|distingue)", "o prompt nao resolve"),
    (r"não diz qual (?:cede|prevalece|manda|vale)", "nao diz qual prevalece"),
    (r"colid\w+|colisão|se atropelam|em atrito", "colisao nomeada"),
    # "contraditorio" tambem sai da boca do aluno simulado dentro da
    # conversa, entao a marca so vale perto de uma referencia ao prompt.
    (r"(?:prompt|regra|linha|instru\w+)[^.]{0,90}contradi\w+|contradi\w+[^.]{0,90}(?:prompt|regra|linha|instru\w+)", "contradicao no prompt"),
    (r"as duas (?:regras|instruções|coisas) não cabem|"
     r"não (?:há|existe) como cumprir as (?:duas|três)", "regras incompativeis"),
    (r"por interpretação, e não por instrução", "acertou sem instrucao"),
    (r"segui (?:o prompt|a linha|a regra)", "seguiu contra o proprio juizo"),
    (r"eu (?:teria|faria) diferente", "faria diferente"),
    (r"letra morta|sem objeto|perde o (?:sentido|referente)", "regra sem objeto"),
]


def blocos(texto):
    """Um bloco e um paragrafo. Guarda a posicao, para o relatorio."""
    pos = 0
    for b in re.split(r"\n\n+", texto):
        yield pos, b.strip()
        pos += len(b) + 2


def primeira_frase(b, n=95):
    s = re.sub(r"\s+", " ", b).strip()
    return s[:n] + ("..." if len(s) > n else "")


def estatica(caminho, minimo):
    texto = Path(caminho).read_text(encoding="utf-8")
    por_objeto = defaultdict(list)
    for pos, b in blocos(texto):
        if len(b) < 200 or not NORMATIVO.search(b):
            continue
        for nome, padrao in OBJETOS.items():
            if re.search(padrao, b, re.I):
                por_objeto[nome].append((pos, b))

    # Um par so interessa quando os dois blocos legislam sobre varios
    # objetos em comum: coincidencia de uma palavra e ruido.
    pares = defaultdict(set)
    for nome, lista in por_objeto.items():
        for i in range(len(lista)):
            for j in range(i + 1, len(lista)):
                a, c = lista[i][0], lista[j][0]
                pares[(a, c)].add(nome)

    texto_de = {pos: b for pos, b in blocos(texto)}
    fortes = [(len(objs), par, objs) for par, objs in pares.items()
              if len(objs) >= minimo]
    fortes.sort(reverse=True)

    print("=" * 72)
    print("COLISOES POSSIVEIS  (blocos normativos sobre os mesmos objetos)")
    print("=" * 72)
    if not fortes:
        print("  nenhum par com %d objetos em comum." % minimo)
    for n, (a, c), objs in fortes[:25]:
        print()
        print("  %d objetos: %s" % (n, ", ".join(sorted(objs))))
        print("   A  %s" % primeira_frase(texto_de.get(a, "")))
        print("   B  %s" % primeira_frase(texto_de.get(c, "")))
    print()
    print("  %d pares acima do corte, de %d examinados." % (len(fortes), len(pares)))


def observada(pasta):
    arquivos = [p for p in sorted(Path(pasta).glob("*.md"))
                if not p.name.startswith("projeto_")]
    if not arquivos:
        print("  nenhum relatorio em %s" % pasta)
        return

    achados = defaultdict(list)
    for p in arquivos:
        try:
            t = p.read_text(encoding="utf-8")
        except Exception as e:
            print("  (nao li %s: %s)" % (p.name, e))
            continue
        for padrao, rotulo in MARCAS:
            for m in re.finditer(padrao, t, re.I):
                ini = max(0, t.rfind(".", 0, m.start()) + 1)
                fim = t.find(".", m.end())
                frase = re.sub(r"\s+", " ", t[ini:fim if fim > 0 else m.end()]).strip()
                if 30 < len(frase) < 400:
                    achados[rotulo].append((p.name, frase))

    print("=" * 72)
    print("COLISOES OBSERVADAS  (o modelo declarou ter tido de decidir)")
    print("=" * 72)
    print("  %d relatorios lidos" % len(arquivos))
    for rotulo, lista in sorted(achados.items(), key=lambda x: -len(x[1])):
        print()
        print("  [%s]  %d ocorrencias" % (rotulo, len(lista)))
        vistos = set()
        for nome, frase in lista:
            chave = frase[:60]
            if chave in vistos:
                continue
            vistos.add(chave)
            print("    %-24s %s" % (nome[:24], frase[:150]))
            if len(vistos) >= 6:
                if len(lista) > 6:
                    print("    %-24s (e mais %d)" % ("", len(lista) - 6))
                break


def main():
    p = argparse.ArgumentParser(
        description="Acha onde duas regras do prompt se atropelam.")
    p.add_argument("prompt", nargs="?", help="o prompt a examinar")
    p.add_argument("--relatorios", help="pasta com relatorios de teste")
    p.add_argument("--minimo", type=int, default=4,
                   help="objetos em comum para o par entrar (padrão 4)")
    a = p.parse_args()

    if a.relatorios:
        observada(a.relatorios)
        print()
    if a.prompt:
        if not Path(a.prompt).is_file():
            sys.exit("não achei %s" % a.prompt)
        estatica(a.prompt, a.minimo)
    if not a.prompt and not a.relatorios:
        p.print_help()


if __name__ == "__main__":
    main()
