#!/usr/bin/env python3
"""
Selma em lote: preparar os projetos e agregar os relatorios.

    python selma_lote.py preparar <pasta>     # PDF e DOCX viram .txt
    python selma_lote.py agregar   <pasta>    # relatorios viram tabela
    python selma_lote.py controle             # confere o conferidor

O QUE ESTE PROGRAMA FAZ E O QUE ELE NAO FAZ. Ele prepara e ele agrega. A
LEITURA nao esta aqui: cada projeto e lido por uma execucao propria da
Selma, com o prompt inteiro, e e assim de proposito.

POR QUE UMA LEITURA POR PROJETO, E NUNCA VARIOS NO MESMO CONTEXTO. Se um
modelo le vinte projetos seguidos, o setimo e lido contra a lembranca dos
seis anteriores, e o mesmo defeito recebe nota diferente conforme o que
veio antes. A comparabilidade vem da INDEPENDENCIA somada as dimensoes
fixas, e nao da co-presenca. Por isso o agregador recebe os RELATORIOS, e
nao os projetos: ele nao rele nada e nao tem como comparar documentos.

POR QUE A TABELA E MONTADA AQUI, E NAO PELO MODELO. Quem transcreve e o
codigo. Modelo que copia vinte linhas de numeros troca uma, e numa ficha
de selecao um numero trocado e o pior defeito possivel.

E POR QUE A TABELA NAO SAI ORDENADA PELA MEDIA. Tabela ordenada por media
e um ranking, chame-se ou nao de ranking, e a media nunca foi validada
como instrumento de ordenar: ela foi feita para dizer de que lado da linha
o projeto caiu. A ordem aqui e alfabetica, e as medias vao na tabela
inteiras. Quem quiser ordenar ordena, e sabera que foi decisao sua.

O RELATORIO DA COORTE SO CONTA. Quantos passaram cada linha, quantos
tiveram impeditivo em cada dimensao, qual dimensao foi a mais fraca no
conjunto. Contagem e transcricao; "a turma tem dificuldade com
metodologia" seria afirmacao nova sobre uma populacao, e cinco leituras
nao a sustentam.

E O CONTROLE EMBUTIDO: rode DUAS leituras independentes sobre dois ou tres
projetos do lote, com nomes terminados em -a e -b. O agregador as
reconhece, poe as duas na tabela e mostra a diferenca entre elas. Sem
isso, a tabela e um conjunto de numeros cuja estabilidade ninguem mediu.
"""
import io
import os
import re
import sys
from pathlib import Path

DIMENSOES = ["problema e justificativa", "metodologia e teoria", "contribuicoes e impacto",
             "bibliografia", "indicios de ia"]
LINHA_SELECAO = 7.0
# A dimensao 5 nao tem nota e nao entra na media: leva o NIVEL.
NIVEIS = ["fortes-abusivo", "fortes-indeterminado", "leves", "ausentes"]


# --------------------------------------------------------------- preparar
def extrair(caminho):
    """Devolve o texto de um .pdf ou .docx."""
    p = Path(caminho)
    if p.suffix.lower() == ".pdf":
        import fitz
        d = fitz.open(str(p))
        return re.sub(r"\n{3,}", "\n\n", "\n".join(x.get_text() for x in d))
    if p.suffix.lower() == ".docx":
        import zipfile
        z = zipfile.ZipFile(str(p))
        xml = z.read("word/document.xml").decode("utf-8")
        saida = []
        for par in re.findall(r"<w:p[ >].*?</w:p>", xml, re.S):
            txt = "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", par, re.S))
            for a, b in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                         ("&quot;", '"')):
                txt = txt.replace(a, b)
            txt = txt.replace(chr(0x200b), "").strip()
            if txt:
                saida.append(txt)
        return "\n".join(saida)
    raise ValueError("nao sei ler %s" % p.suffix)


def preparar(pasta):
    destino = Path(pasta) / "txt"
    destino.mkdir(exist_ok=True)
    n = 0
    for f in sorted(Path(pasta).iterdir()):
        if f.suffix.lower() not in (".pdf", ".docx") or f.name.startswith("~"):
            continue
        try:
            t = extrair(f)
        except Exception as e:
            print("  ERRO  %-44s %s" % (f.name[:42], e))
            continue
        nome = re.sub(r"[^A-Za-z0-9]+", "_", f.stem)[:44] + ".txt"
        (destino / nome).write_text(t, encoding="utf-8")
        print("  ok    %-44s %7d caracteres -> %s" % (f.name[:42], len(t), nome))
        n += 1
    print()
    print("%d projetos preparados em %s" % (n, destino))
    print("Agora rode UMA leitura da Selma por arquivo, cada uma em execucao")
    print("propria, e grave cada relatorio como <nome>.md na mesma pasta.")


# ---------------------------------------------------------------- agregar
class BlocoInvalido(Exception):
    pass


def ler_bloco(texto, origem="?"):
    """Extrai e confere o bloco DADOS...FIM de um relatorio da Selma."""
    m = re.search(r"^DADOS\s*$(.*?)^FIM\s*$", texto, re.S | re.M)
    if not m:
        raise BlocoInvalido("%s: nao achei o bloco DADOS...FIM" % origem)
    linhas = [l.strip() for l in m.group(1).strip().split("\n") if l.strip()]
    notas, media, selecao, qualifica, abaixo = {}, None, None, None, None
    nivel = None
    for l in linhas:
        campos = [c.strip() for c in l.split("|")]
        if campos[0] == "MEDIA":
            media = float(campos[1].replace(",", "."))
        elif campos[0] == "SELECAO":
            selecao = campos[1]
        elif campos[0] == "QUALIFICA":
            qualifica = campos[1]
            abaixo = campos[2] if len(campos) > 2 else "-"
        elif campos[0].isdigit():
            i = int(campos[0])
            if not 1 <= i <= 5:
                raise BlocoInvalido("%s: dimensao %d fora de 1-5" % (origem, i))
            nome = campos[1]
            if nome != DIMENSOES[i - 1]:
                raise BlocoInvalido("%s: dimensao %d chamada %r, esperava %r"
                                    % (origem, i, nome, DIMENSOES[i - 1]))
            if i == 5:
                if campos[5] not in NIVEIS:
                    raise BlocoInvalido("%s: nivel %r invalido, esperava um de %s"
                                        % (origem, campos[5], "/".join(NIVEIS)))
                nivel = campos[5]
                continue
            nota = int(campos[5])
            if not 0 <= nota <= 10:
                raise BlocoInvalido("%s: nota %d fora de 0-10" % (origem, nota))
            notas[i] = nota
        else:
            raise BlocoInvalido("%s: linha nao reconhecida: %r" % (origem, l))

    if len(notas) != 4:
        raise BlocoInvalido("%s: %d dimensoes com nota, esperava 4"
                            % (origem, len(notas)))
    if nivel is None:
        raise BlocoInvalido("%s: falta o nivel da dimensao 5" % origem)
    if media is None or selecao is None or qualifica is None:
        raise BlocoInvalido("%s: falta MEDIA, SELECAO ou QUALIFICA" % origem)

    # A media declarada tem de bater com as cinco notas. O relatorio e que
    # vale; o bloco so o repete, e bloco que nao bate se recusa.
    calc = round(sum(notas.values()) / 4.0, 1)
    if abs(calc - media) > 0.05:
        raise BlocoInvalido("%s: MEDIA diz %.1f e as notas dao %.1f"
                            % (origem, media, calc))
    passa = media >= LINHA_SELECAO
    if passa != selecao.startswith("passa"):
        raise BlocoInvalido("%s: SELECAO diz %r com media %.1f"
                            % (origem, selecao, media))
    baixas = sorted(i for i, n in notas.items() if n < 7)
    declaradas = [] if abaixo in ("-", "", None) else \
        sorted(int(x) for x in abaixo.split(",") if x.strip())
    if baixas != declaradas:
        raise BlocoInvalido("%s: QUALIFICA aponta %r e as notas dao %r"
                            % (origem, declaradas, baixas))
    return {"notas": notas, "media": media, "selecao": selecao,
            "qualifica": qualifica, "abaixo": baixas, "nivel": nivel}


def agregar(pasta):
    lidos, ruins = {}, []
    for f in sorted(Path(pasta).glob("*.md")):
        try:
            lidos[f.stem] = ler_bloco(f.read_text(encoding="utf-8"), f.name)
        except BlocoInvalido as e:
            ruins.append(str(e))
    if ruins:
        print("RELATORIOS RECUSADOS (%d):" % len(ruins))
        for r in ruins:
            print("  -", r)
        print()
    if not lidos:
        sys.exit("Nenhum relatorio valido em %s" % pasta)

    larg = max(len(k) for k in lidos)
    cab = "%-*s  %4s %4s %4s %4s %4s  %5s  %-10s %s" % (
        larg, "projeto (ordem alfabetica)", "1", "2", "3", "4", "5",
        "media", "selecao", "qualifica")
    print(cab)
    print("-" * len(cab))
    for nome in sorted(lidos):
        d = lidos[nome]
        n = d["notas"]
        print("%-*s  %4d %4d %4d %4d %4d  %5.1f  %-10s %s" % (
            larg, nome, n[1], n[2], n[3], n[4], n[5], d["media"],
            d["selecao"], d["qualifica"]))
    print()

    # ------------------------------------------------ a coorte, so contagem
    total = len(lidos)
    passam = sum(1 for d in lidos.values() if d["media"] >= LINHA_SELECAO)
    qualif = sum(1 for d in lidos.values() if not d["abaixo"])
    print("COORTE, e aqui so se conta:")
    print("  projetos lidos                         : %d" % total)
    print("  media 7 ou mais (linha da selecao)     : %d" % passam)
    print("  nenhuma dimensao abaixo de 7           : %d" % qualif)
    for i, nome in enumerate(DIMENSOES, 1):
        baixas = sum(1 for d in lidos.values() if d["notas"][i] < 7)
        media = sum(d["notas"][i] for d in lidos.values()) / float(total)
        print("  dim %d %-24s abaixo de 7 em %d de %d, media %.1f"
              % (i, nome, baixas, total, media))
    print()
    print("  A ordem da tabela e alfabetica, e nao por media, de proposito:")
    print("  ordenar por media transforma a leitura em ranking, e a media nao")
    print("  foi validada para ordenar. Ela diz de que lado da linha caiu.")

    # ------------------------------------------------- o controle embutido
    pares = {}
    for nome in lidos:
        m = re.match(r"^(.*)-([ab])$", nome)
        if m:
            pares.setdefault(m.group(1), {})[m.group(2)] = lidos[nome]
    duplos = {k: v for k, v in pares.items() if len(v) == 2}
    print()
    if not duplos:
        print("SEM CONTROLE DE ESTABILIDADE neste lote. Rode duas leituras")
        print("independentes de dois ou tres projetos, gravando-as como")
        print("<nome>-a.md e <nome>-b.md: sem isso ninguem mediu se duas")
        print("leituras do mesmo projeto chegam a mesma nota.")
        return
    print("CONTROLE DE ESTABILIDADE (duas leituras do mesmo projeto):")
    for k, v in sorted(duplos.items()):
        difs = [abs(v["a"]["notas"][i] - v["b"]["notas"][i]) for i in range(1, 6)]
        print("  %-30s por dimensao: %s | maior: %d | media %.1f vs %.1f"
              % (k, difs, max(difs), v["a"]["media"], v["b"]["media"]))


# --------------------------------------------------------------- controle
BOM = """DADOS
1 | problema e justificativa | 0 | 1 | 1 | 5
2 | metodologia e teoria | 1 | 0 | 2 | 4
3 | contribuicoes e impacto | 0 | 1 | 0 | 6
4 | bibliografia | 0 | 0 | 3 | 7
5 | indicios de ia | - | - | - | leves
MEDIA | 5.5
SELECAO | nao passa
QUALIFICA | nao recomendo | 1,2,3
FIM"""


def controle():
    """Positivo: cada defeito que o conferidor deveria pegar tem de reprovar."""
    ok = ler_bloco(BOM, "controle")
    assert ok["media"] == 5.5 and ok["abaixo"] == [1, 2, 3], ok
    assert ok["nivel"] == "leves", ok
    print("  o bloco bom passa                                 ok")

    casos = [
        ("media que nao bate", BOM.replace("MEDIA | 5.5", "MEDIA | 7.4")),
        ("selecao contradiz a media", BOM.replace("nao passa", "passa")),
        ("qualifica omite uma dimensao baixa",
         BOM.replace("| 1,2,3", "| 1,2")),
        ("nota fora de 0-10", BOM.replace("| 0 | 3 | 7", "| 0 | 3 | 17")),
        ("nivel invalido", BOM.replace("| leves", "| razoavel")),
        ("dimensao 5 com nota", BOM.replace("- | leves", "- | 8")),
        ("dimensao com nome trocado",
         BOM.replace("metodologia e teoria", "metodologia")),
        ("falta uma dimensao",
         "\n".join(l for l in BOM.split("\n") if not l.startswith("4 |"))),
        ("sem o bloco", BOM.replace("DADOS", "DADO")),
    ]
    for nome, mau in casos:
        try:
            ler_bloco(mau, "controle")
        except BlocoInvalido as e:
            print("  %-50s reprovou: %s" % (nome, str(e)[10:70]))
        else:
            sys.exit("CONTROLE FALHOU: %s passou e devia reprovar" % nome)
    print()
    print("O conferidor reprova os %d casos. Sem este controle, um bloco"
          % len(casos))
    print("aceito nao informaria nada: silencio de conferidor quebrado tem a")
    print("mesma aparencia de silencio de dado correto.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("preparar", "agregar", "controle"):
        sys.exit(__doc__)
    if sys.argv[1] == "controle":
        controle()
    else:
        if len(sys.argv) < 3:
            sys.exit("falta a pasta")
        (preparar if sys.argv[1] == "preparar" else agregar)(sys.argv[2])
