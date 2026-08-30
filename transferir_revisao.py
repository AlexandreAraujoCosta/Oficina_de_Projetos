#!/usr/bin/env python3
"""
Move partes do anexo para as secoes do pre-projeto, segundo um mapa.

    python transferir_revisao.py --numerar projeto-original.docx
    python transferir_revisao.py pre-projeto.md --anexo projeto-original.docx \\
        --mapa mapa.txt -o pre-projeto-2.md

POR QUE UM PROGRAMA FAZ ISSO, E NAO O ASSISTENTE. Transferir uma secao
do anexo para o texto, dentro de um chat, e o modelo redigitar o texto do
aluno, e o que sai da redigitacao muda palavra sem avisar. Aqui o
assistente produz um MAPA, que e so origem e destino, e quem copia o
texto e este programa, do arquivo para o arquivo.

O FLUXO TEM DOIS PASSOS.

  1. --numerar produz o anexo com os paragrafos marcados [P001], [P002].
     O aluno cola essa versao numerada na conversa, e a partir dai o
     assistente tem como apontar sem transcrever.

  2. O assistente escreve o mapa, uma linha por destino:

         Revisão de literatura <- P012, P014-P017
         Justificativa <- P003
         Referências <- P045-P058

     e este programa move os paragrafos nomeados para as secoes do
     pre-projeto, na ordem em que estao no mapa, e os RETIRA do anexo,
     para o mesmo texto nao ficar em dois lugares.

O QUE ELE RECUSA FAZER. Numero de paragrafo que nao existe, destino que
nao e secao do modelo, e paragrafo nomeado duas vezes param o programa
com erro. Nenhum dos tres se resolve por adivinhacao: mapa errado que
roda em silencio produz documento errado com cara de correto.

Requer pandoc para ler .docx.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from gerar_docx_pre_projeto import (SECOES, normalizar, qual_secao, repartir,
                                    limpar, secoes)

RE_MARCA = re.compile(r"^\[P(\d{3,4})\]\s?")
RE_INTERVALO = re.compile(r"^P?(\d{1,4})\s*-\s*P?(\d{1,4})$", re.I)
RE_UNICO = re.compile(r"^P?(\d{1,4})$", re.I)


def ler_como_markdown(caminho):
    """Le .docx, .odt, .md ou .txt. Quem converte e o pandoc."""
    if caminho.suffix.lower() in (".md", ".markdown", ".txt"):
        return caminho.read_text(encoding="utf-8")
    if not shutil.which("pandoc"):
        sys.exit("pandoc nao encontrado, e ele e necessario para ler %s" % caminho.name)
    out = subprocess.run(
        ["pandoc", str(caminho), "-t", "markdown", "--wrap=none"],
        capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        sys.exit("pandoc falhou ao ler %s:\n%s" % (caminho.name, (out.stderr or "").strip()))
    return out.stdout


def em_paragrafos(texto):
    """Um paragrafo e um bloco separado por linha em branco.

    Titulos contam como paragrafo proprio, porque mover uma secao sem o
    titulo dela deixa o titulo orfao no anexo.
    """
    blocos, atual = [], []
    for linha in texto.splitlines():
        if linha.strip():
            atual.append(linha)
        elif atual:
            blocos.append("\n".join(atual))
            atual = []
    if atual:
        blocos.append("\n".join(atual))
    return blocos


def numerar(caminho, destino):
    blocos = em_paragrafos(ler_como_markdown(caminho))
    saida = "\n\n".join("[P%03d] %s" % (i, b) for i, b in enumerate(blocos, 1))
    destino.write_text(saida + "\n", encoding="utf-8")
    print("%s: %d parágrafos numerados" % (destino.name, len(blocos)))
    print("Cole este arquivo na conversa: é dele que saem os localizadores.")


def ler_mapa(caminho):
    """Le o mapa e devolve [(destino, [numeros])], preservando a ordem."""
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
        for p in numeros:
            if p in vistos:
                sys.exit("parágrafo P%03d aparece duas vezes no mapa, nas linhas %d e %d.\n"
                         "Um parágrafo só pode ir para um lugar." % (p, vistos[p], n))
            vistos[p] = n
        mapa.append((secao, numeros))
    return mapa


def main():
    p = argparse.ArgumentParser(
        description="Move partes do anexo para as seções do pré-projeto.")
    p.add_argument("md", nargs="?", help="o pré-projeto")
    p.add_argument("--numerar", metavar="ARQUIVO",
                   help="só numera os parágrafos do anexo e sai")
    p.add_argument("--anexo", help="o projeto original, já numerado ou não")
    p.add_argument("--mapa", help="o mapa de origem e destino")
    p.add_argument("-o", "--saida", help="o pré-projeto de saída")
    p.add_argument("--anexo-saida", help="o anexo sem o que foi movido")
    a = p.parse_args()

    if a.numerar:
        origem = Path(a.numerar)
        if not origem.is_file():
            sys.exit("não achei %s" % origem)
        numerar(origem, Path(origem.stem + "-numerado.md"))
        return

    if not (a.md and a.anexo and a.mapa):
        sys.exit("faltam argumentos: o pré-projeto, --anexo e --mapa.\n"
                 "Ou use --numerar para o primeiro passo.")

    pp = Path(a.md)
    anexo = Path(a.anexo)
    for c in (pp, anexo, Path(a.mapa)):
        if not c.is_file():
            sys.exit("não achei %s" % c)

    blocos = em_paragrafos(ler_como_markdown(anexo))
    # O anexo pode chegar ja numerado (foi ele que o assistente leu) ou
    # cru. Se estiver numerado, a marca manda, porque e a ela que o mapa
    # se refere; renumerar aqui deslocaria tudo em silencio.
    por_numero = {}
    for i, b in enumerate(blocos, 1):
        m = RE_MARCA.match(b)
        if m:
            por_numero[int(m.group(1))] = RE_MARCA.sub("", b, count=1)
        else:
            por_numero[i] = b
    if len(por_numero) != len(blocos):
        sys.exit("o anexo tem marcas [P###] repetidas; renumere-o antes.")

    mapa = ler_mapa(Path(a.mapa))
    faltando = sorted({n for _, ns in mapa for n in ns} - set(por_numero))
    if faltando:
        sys.exit("o mapa cita parágrafos que o anexo não tem: %s\n"
                 "O anexo vai de P%03d a P%03d."
                 % (", ".join("P%03d" % n for n in faltando),
                    min(por_numero), max(por_numero)))

    preambulo, achadas, estranhas = repartir(pp.read_text(encoding="utf-8"))

    movidos = set()
    for secao, numeros in mapa:
        trechos = [por_numero[n] for n in numeros]
        achadas.setdefault(secao, [])
        if achadas[secao] and "".join(achadas[secao]).strip():
            achadas[secao].append("")
        achadas[secao].extend(("\n\n".join(trechos)).splitlines())
        movidos.update(numeros)

    partes = []
    if limpar(list(preambulo)):
        partes.append("\n".join(limpar(list(preambulo))))
    for canonico, _, _ in secoes():
        corpo = "\n".join(limpar(list(achadas.get(canonico, []))))
        partes.append("# " + canonico)
        partes.append(corpo if corpo.strip() else "*A preencher.*")
    for nome, linhas in achadas.items():
        if nome not in {c for c, _, _ in secoes()}:
            partes.append("# " + nome)
            partes.append("\n".join(limpar(list(linhas))))

    saida = Path(a.saida) if a.saida else pp.with_name(pp.stem + "-2.md")
    saida.write_text("\n\n".join(partes) + "\n", encoding="utf-8")

    # O anexo perde o que foi movido, para o mesmo texto nao ficar em dois
    # lugares: e o "retire do anexo" feito por programa, sem depender de
    # ninguem apagar a mao nem de um assistente reescrever o que corta.
    resto = ["[P%03d] %s" % (n, por_numero[n])
             for n in sorted(por_numero) if n not in movidos]
    anexo_saida = (Path(a.anexo_saida) if a.anexo_saida
                   else anexo.with_name(anexo.stem + "-restante.md"))
    anexo_saida.write_text("\n\n".join(resto) + "\n", encoding="utf-8")

    print("%s: %d parágrafos movidos" % (saida.name, len(movidos)))
    for secao, numeros in mapa:
        print("  %s <- %s" % (secao, ", ".join("P%03d" % n for n in numeros)))
    print("%s: %d parágrafos restantes no anexo" % (anexo_saida.name, len(resto)))
    if estranhas:
        print("  títulos fora do modelo, preservados: " + ", ".join(estranhas))


if __name__ == "__main__":
    main()
