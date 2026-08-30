#!/usr/bin/env python3
"""
Monta o .docx do pre-projeto, no modelo de dez secoes, com o projeto
original acoplado como anexo.

    python gerar_docx_pre_projeto.py pre-projeto.md
    python gerar_docx_pre_projeto.py pre-projeto.md --anexo projeto.docx
    python gerar_docx_pre_projeto.py pre-projeto.md --anexo projeto.docx -o meu.docx

A entrada e o segundo bloco de codigo que o Miro entrega, salvo como .md.
A saida e um .docx com as dez secoes do modelo: as que a conversa
preencheu vem preenchidas, as outras vem como titulo mais uma linha
dizendo que estao por preencher. Secao vazia mostra onde o trabalho
continua; secao ausente esconde que ela existe.

POR QUE ISTO E UM PROGRAMA, E NAO TRABALHO DO ASSISTENTE. O anexo tem de
ser o texto do aluno, e nao a lembranca que um modelo tem dele. Aqui quem
copia e o pandoc, deterministicamente, do arquivo para o arquivo. Um
assistente que "transcrevesse" o projeto no bloco de saida entregaria
outro texto, parecido e diferente, sem avisar.

O QUE A CONVERSAO DO ANEXO PRESERVA E O QUE NAO PRESERVA: o texto,
titulos, listas, notas, tabelas simples e as imagens (extraidas para uma
pasta ao lado). Perde formatacao fina, tabelas complexas, caixas de texto
e comentarios do Word. Se o anexo precisar sair identico ao original,
nao use --anexo: entregue os dois arquivos separados.

Requer pandoc.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# A ordem e a do modelo de projeto de pesquisa usado na oficina. Cada
# entrada traz o titulo como sai no documento, as variantes com que o
# assistente pode te-la escrito no bloco, e se a secao e optativa.
#
# Optativa quer dizer que o mesmo conteudo cabe em titulo proprio ou
# diluido noutra secao: a revisao de literatura pode viver na secao dela,
# na introducao ou na justificativa. Vazia, ela sai do documento com um
# aviso em vez do "A preencher" das outras, para nao parecer pendencia.
SECOES = [
    ("Título", ("titulo", "título")),
    ("Introdução", ("introducao", "introdução"), True),
    ("Tema", ("tema",)),
    ("Problema de pesquisa", ("problema de pesquisa", "problema", "questao de pesquisa",
                              "questão de pesquisa", "pergunta de pesquisa")),
    ("Justificativa", ("justificativa",)),
    ("Revisão de literatura", ("revisao de literatura", "revisão de literatura",
                               "revisao bibliografica", "revisão bibliográfica",
                               "estado da arte"), True),
    ("Objetivos", ("objetivos", "objetivo geral e objetivos especificos",
                   "objetivo geral e objetivos específicos")),
    ("Estratégias de abordagem", ("estrategias de abordagem", "estratégias de abordagem",
                                  "estrategia de abordagem", "estratégia de abordagem",
                                  "abordagem metodologica", "abordagem metodológica",
                                  "metodologia")),
    ("Referencial teórico", ("referencial teorico", "referencial teórico",
                             "marco teorico", "marco teórico")),
    ("Referências", ("referencias", "referências", "bibliografia")),
]

A_PREENCHER = "*A preencher.*"
OPTATIVA = ("*Seção optativa, ainda vazia: use-a se quiser, ou deixe este conteúdo diluído nas outras seções.*")


def secoes():
    """Normaliza SECOES, cujas entradas tem dois ou tres campos."""
    for entrada in SECOES:
        nome, variantes = entrada[0], entrada[1]
        yield nome, variantes, (len(entrada) > 2 and entrada[2])

RE_TITULO = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
RE_TITULO_NEGRITO = re.compile(r"^\s{0,3}\*\*(.+?)\*\*\s*:?\s*$")


def normalizar(texto):
    """Compara titulos sem depender de acento, caixa ou pontuacao."""
    t = texto.strip().lower().rstrip(":.")
    for de, para in (("á", "a"), ("â", "a"), ("ã", "a"), ("à", "a"),
                     ("é", "e"), ("ê", "e"), ("í", "i"), ("ó", "o"),
                     ("ô", "o"), ("õ", "o"), ("ú", "u"), ("ç", "c")):
        t = t.replace(de, para)
    return re.sub(r"\s+", " ", t)


def qual_secao(titulo):
    alvo = normalizar(titulo)
    for canonico, variantes, _ in secoes():
        if alvo in (normalizar(v) for v in variantes):
            return canonico
    return None


def repartir(texto):
    """Separa o .md em (preambulo, {secao: conteudo}, [titulos nao reconhecidos]).

    O preambulo guarda o que vier antes do primeiro titulo, tipicamente a
    linha "> ESTADO:" que o pre-projeto abre. Ela nao pertence a secao
    nenhuma e nao pode se perder.
    """
    preambulo, achadas, estranhas = [], {}, []
    atual = None
    for linha in texto.splitlines():
        m = RE_TITULO.match(linha) or RE_TITULO_NEGRITO.match(linha)
        if m:
            nome = qual_secao(m.group(1))
            if nome:
                atual = nome
                achadas.setdefault(nome, [])
                continue
            # Titulo que nao e do modelo: nao se descarta em silencio.
            estranhas.append(m.group(1).strip())
            atual = m.group(1).strip()
            achadas.setdefault(atual, [])
            continue
        (achadas[atual] if atual else preambulo).append(linha)
    return preambulo, achadas, estranhas


def limpar(linhas):
    while linhas and not linhas[0].strip():
        linhas.pop(0)
    while linhas and not linhas[-1].strip():
        linhas.pop()
    return linhas


def tem_material(linhas):
    """Secao cujo conteudo e so comentario de metodo nao esta preenchida.

    A regra 2 do pre-projeto manda escrever "> A FAZER:" JUSTAMENTE onde
    nao ha material, entao contar essa linha como conteudo inverteria o
    sentido dela e produziria um placar que consola em vez de informar.
    """
    uteis = [l for l in linhas if l.strip()]
    return bool(uteis) and any(not l.lstrip().startswith(">") for l in uteis)


def anexo_em_markdown(caminho, pasta_midia):
    """Converte o projeto original em markdown. Quem copia e o pandoc."""
    cmd = ["pandoc", str(caminho), "-t", "markdown", "--wrap=none",
           "--extract-media", str(pasta_midia)]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        sys.exit("pandoc falhou ao ler o anexo:\n" + (out.stderr or "").strip())
    # Rebaixa os titulos do anexo para nao competirem com os do modelo.
    linhas = []
    for linha in out.stdout.splitlines():
        m = RE_TITULO.match(linha)
        linhas.append("#" + linha.lstrip() if m else linha)
    return "\n".join(linhas)


def montar(preambulo, achadas, anexo_md, titulo_anexo):
    partes = []
    cabeca = "\n".join(limpar(list(preambulo)))
    if cabeca:
        partes.append(cabeca)

    for canonico, _, optativa in secoes():
        corpo = "\n".join(limpar(list(achadas.get(canonico, []))))
        partes.append("# " + canonico)
        if corpo.strip():
            partes.append(corpo)
        else:
            partes.append(OPTATIVA if optativa else A_PREENCHER)

    # Titulos que o modelo nao previa entram no fim, com aviso, em vez de
    # sumirem. Perder material do aluno e o pior desfecho possivel.
    previstos = {c for c, _, _ in secoes()}
    extras = [(k, v) for k, v in achadas.items() if k not in previstos]
    if extras:
        partes.append("# Outras seções do documento de origem")
        for nome, linhas in extras:
            partes.append("## " + nome)
            corpo = "\n".join(limpar(list(linhas)))
            partes.append(corpo if corpo.strip() else A_PREENCHER)

    if anexo_md:
        partes.append("# " + titulo_anexo)
        partes.append(
            "*Texto do projeto original, copiado do arquivo do autor. "
            "As seções acima foram trabalhadas na conversa; o que está "
            "aqui volta ao documento aos poucos, uma seção por vez, na "
            "medida em que o autor puder dizer o que ela faz ali.*")
        partes.append(anexo_md)

    return "\n\n".join(partes) + "\n"


def main():
    p = argparse.ArgumentParser(
        description="Monta o .docx do pre-projeto no modelo de oito secoes.")
    p.add_argument("md", help="o pre-projeto salvo como .md")
    p.add_argument("--anexo", help="o projeto original (.docx, .odt, .md, .txt)")
    p.add_argument("-o", "--saida", help="o .docx de saida")
    p.add_argument("--referencia", help=".docx de referencia com os estilos")
    p.add_argument("--titulo-anexo", default="Anexo: projeto de origem")
    a = p.parse_args()

    if not shutil.which("pandoc"):
        sys.exit("pandoc nao encontrado. Instale-o para gerar o .docx.")

    origem = Path(a.md)
    if not origem.is_file():
        sys.exit("nao achei %s" % origem)
    texto = origem.read_text(encoding="utf-8")

    destino = Path(a.saida) if a.saida else origem.with_suffix(".docx")
    pasta_midia = destino.with_name(destino.stem + "-midia")

    preambulo, achadas, estranhas = repartir(texto)

    anexo_md = ""
    if a.anexo:
        caminho = Path(a.anexo)
        if not caminho.is_file():
            sys.exit("nao achei o anexo %s" % caminho)
        anexo_md = anexo_em_markdown(caminho, pasta_midia)

    completo = montar(preambulo, achadas, anexo_md, a.titulo_anexo)

    with tempfile.TemporaryDirectory() as tmp:
        intermediario = Path(tmp) / "pre-projeto.md"
        intermediario.write_text(completo, encoding="utf-8")
        cmd = ["pandoc", str(intermediario), "-o", str(destino),
               "--from", "markdown", "--to", "docx"]
        if a.referencia:
            cmd += ["--reference-doc", str(a.referencia)]
        out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if out.returncode != 0:
            sys.exit("pandoc falhou ao escrever o .docx:\n" + (out.stderr or "").strip())

    # O relatorio diz o que entrou e o que ficou por preencher, porque o
    # arquivo sozinho nao distingue secao vazia de secao esquecida.
    cheias = [c for c, _, _ in secoes() if tem_material(achadas.get(c, []))]
    vazias = [c for c, _, o in secoes() if c not in cheias and not o]
    optativas = [c for c, _, o in secoes() if c not in cheias and o]
    print("%s: %d de %d seções preenchidas" % (destino.name, len(cheias), len(SECOES)))
    if vazias:
        print("  por preencher: " + ", ".join(vazias))
    if optativas:
        print("  optativas, vazias: " + ", ".join(optativas))
    if estranhas:
        print("  títulos fora do modelo, mantidos no fim: " + ", ".join(estranhas))
    if anexo_md:
        print("  anexo: %s, copiado pelo pandoc" % Path(a.anexo).name)
        if pasta_midia.exists():
            print("  imagens do anexo em %s" % pasta_midia.name)
        print("  a conversão preserva texto, títulos, listas e tabelas simples;")
        print("  perde formatação fina, caixas de texto e comentários do Word.")


if __name__ == "__main__":
    main()
