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
    nivel = apto = mudar = None
    for l in linhas:
        campos = [c.strip() for c in l.split("|")]
        if campos[0] == "MEDIA":
            media = float(campos[1].replace(",", "."))
        elif campos[0] == "SELECAO":
            selecao = campos[1]
        elif campos[0] == "QUALIFICA":
            qualifica = campos[1]
            abaixo = campos[2] if len(campos) > 2 else "-"
        elif campos[0] == "APTO":
            # A TERCEIRA LINHA. Ela entrou no prompt da Selma e nao aqui, e
            # o agregador passou a RECUSAR TODA LEITURA REAL, dizendo
            # "linha nao reconhecida". Quem mexe no bloco mexe nos dois
            # lados, e o controle tem de ter um caso do lado novo.
            apto = campos[1]
            if apto not in ("apto", "nao apto"):
                raise BlocoInvalido("%s: APTO diz %r, esperava apto ou "
                                    "nao apto" % (origem, apto))
            mudar = campos[2] if len(campos) > 2 else ""
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
    if apto is None:
        raise BlocoInvalido("%s: falta a linha APTO" % origem)
    if apto == "apto" and not mudar.strip():
        raise BlocoInvalido("%s: APTO diz apto e nao diz o que mudaria"
                            % origem)

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
    # O TEXTO DO RELATORIO VAI JUNTO, sem o bloco de dados: e ele que o
    # PDF do lote reproduz. O bloco sai porque ele existe para o programa
    # ler, e nao para a banca; deixa-lo faria a peca terminar em tabela
    # de campos separados por barra.
    corpo = (texto[:m.start()] + texto[m.end():]).strip()
    return {"notas": notas, "media": media, "selecao": selecao,
            "qualifica": qualifica, "abaixo": baixas, "nivel": nivel,
            "apto": apto, "mudar": mudar, "texto": corpo}


def escrever_pdf(lidos, caminho):
    """O relatorio do lote: a tabela comparativa e, depois, cada leitura
    inteira.

    A TABELA VAI EM ORDEM ALFABETICA, e nao por media, e isto nao e
    detalhe de apresentacao. Tabela ordenada por media e um ranking,
    chame-se ou nao de ranking, e a media nao foi validada para ordenar:
    ela foi feita para dizer de que lado da linha o projeto caiu. Quem
    quiser ordenar ordena, sabendo que foi decisao sua.

    E O NIVEL DOS INDICIOS TEM COLUNA PROPRIA, sem nota e fora da media,
    para que ele chegue a banca sem ter mexido em nenhuma das duas linhas.
    """
    # O PyMuPDF entra AQUI, e nao no alto: o lote em texto tem de rodar
    # em maquina que nao o tenha, e so a saida em PDF depende dele.
    try:
        import fitz
    except ImportError:
        sys.exit("A saida em PDF precisa do PyMuPDF: pip install pymupdf")
    from folha_pdf import Folha, numerar_paginas, tabela, COR_FRACA, COR_MARCA

    doc = fitz.open()
    f = Folha(doc)
    f.texto("Leituras de banca de selecao", corpo=17, fonte="tibo",
            espaco_depois=4)
    f.texto("%d projetos. As notas vao de 0 a 10 em quatro dimensoes; os "
            "indicios de IA nao tem nota, nao entram na media e viajam ao "
            "lado. A ordem e alfabetica, e nao por media." % len(lidos),
            corpo=9.5, fonte="tiit", cor=COR_FRACA, espaco_depois=16)

    # AS TRES LINHAS DO VEREDITO VAO NA TABELA, e nao so as duas: a
    # aptidao e a que diz se o trabalho se conserta, e e a que muda o que
    # a banca faz depois. Deixa-la so no corpo do relatorio obrigaria a
    # abrir cada leitura para saber.
    cabecalho = ["projeto", "1", "2", "3", "4", "media", "selecao",
                 "qualifica", "apto", "indicios de IA"]
    linhas = []
    for nome in sorted(lidos):
        d = lidos[nome]
        n = d["notas"]
        linhas.append([nome, n[1], n[2], n[3], n[4], "%.1f" % d["media"],
                       d["selecao"], d["qualifica"], d["apto"], d["nivel"]])
    # As larguras foram medidas na pagina renderizada, e nao chutadas:
    # com as anteriores, "media" quebrava em "medi/a" e "nao recomendo"
    # em duas linhas. As colunas de nota levam um digito e nao precisam
    # de espaco; as de veredito levam palavra e precisam.
    tabela(f, cabecalho, linhas, [17, 3.2, 3.2, 3.2, 3.2, 7, 10, 13, 8.5, 14])

    total = len(lidos)
    passam = sum(1 for d in lidos.values() if d["media"] >= LINHA_SELECAO)
    qualif = sum(1 for d in lidos.values() if not d["abaixo"])
    f.texto("A coorte, e aqui so se conta", corpo=12.5, fonte="tibo",
            espaco_antes=10, espaco_depois=6)
    conta = ["projetos lidos: %d" % total,
             "media 7 ou mais, que e a linha da selecao: %d" % passam,
             "nenhuma dimensao abaixo de 7: %d" % qualif]
    for i, nome in enumerate(DIMENSOES[:4], 1):
        baixas = sum(1 for d in lidos.values() if d["notas"][i] < 7)
        media = sum(d["notas"][i] for d in lidos.values()) / float(total)
        conta.append("dimensao %d, %s: abaixo de 7 em %d de %d, media %.1f"
                     % (i, nome, baixas, total, media))
    for nivel in NIVEIS:
        quantos = sum(1 for d in lidos.values() if d["nivel"] == nivel)
        if quantos:
            conta.append("indicios %s: %d" % (nivel, quantos))
    for c in conta:
        f.texto("- " + c, espaco_depois=3)
    f.texto("Contar e transcrever. Dizer que a turma tem dificuldade com "
            "metodologia seria afirmacao nova sobre uma populacao, e nao "
            "sai daqui.", corpo=9.5, fonte="tiit", cor=COR_FRACA,
            espaco_antes=8, espaco_depois=10)

    for nome in sorted(lidos):
        f.nova()
        f.texto(nome, corpo=14, fonte="tibo", espaco_depois=3)
        d = lidos[nome]
        f.texto("media %.1f  |  selecao: %s  |  qualificacao: %s  |  "
                "%s  |  indicios de IA: %s"
                % (d["media"], d["selecao"], d["qualifica"], d["apto"],
                   d["nivel"]),
                corpo=9, fonte="tibo", cor=COR_MARCA, espaco_depois=10)
        # TITULO E BLOCO PROPRIO, ainda que nao venha seguido de linha em
        # branco. Partindo so por linha em branco, o titulo grudava no
        # paragrafo seguinte e a PAGINA INTEIRA SAIA EM NEGRITO, porque o
        # bloco todo herdava a fonte do titulo. E o titulo de primeiro
        # nivel sai fora: o nome do projeto ja encabeca a secao.
        blocos, atual = [], []
        for linha in d["texto"].split(chr(10)):
            if linha.strip().startswith("#"):
                if atual:
                    blocos.append(("prosa", " ".join(" ".join(atual).split())))
                    atual = []
                nivel = len(linha) - len(linha.lstrip("#"))
                if nivel > 1:
                    blocos.append(("titulo", linha.lstrip("# ").strip()))
            elif linha.strip():
                atual.append(linha.strip())
            elif atual:
                blocos.append(("prosa", " ".join(" ".join(atual).split())))
                atual = []
        if atual:
            blocos.append(("prosa", " ".join(" ".join(atual).split())))

        for tipo, texto_bloco in blocos:
            if not texto_bloco:
                continue
            if tipo == "titulo":
                f.texto(texto_bloco, corpo=12, fonte="tibo",
                        espaco_antes=6, espaco_depois=5)
            else:
                f.texto(texto_bloco, espaco_depois=6)

    numerar_paginas(doc)
    doc.save(caminho)
    doc.close()


# Palavras que julgam, e que por isso nao cabem no paragrafo descritivo.
# EM FORMA DE PADRAO, E NAO DE PALAVRA SOLTA: a primeira versao listou
# "vago" e o caso de teste dizia "vaga", e o controle acusou o silencio.
# Flexao de genero e numero e a regra do portugues, nao a excecao.
# A lista e curta de proposito: quanto maior, mais acusacao errada, e
# acusacao errada custa mais que silencio aqui.
PADROES_QUE_JULGAM = [
    r"vag[oa]s?", r"fr[aá]gil|fr[aá]geis", r"insuficiente s?".replace(" ", ""),
    r"gen[eé]ric[oa]s?", r"superficia(?:l|is)", r"s[oó]lid[oa]s?",
    r"consistente s?".replace(" ", ""), r"promissor(?:a|es|as)?",
    r"bem construíd[oa]s?", r"bem construid[oa]s?",
    r"(?:in)?adequad[oa]s?", r"imprecis[oa]s?", r"confus[oa]s?",
    r"excelente s?".replace(" ", ""), r"frac[oa]s?", r"robust[oa]s?",
]
RE_JULGAM = [(p, re.compile(r"\b(?:%s)\b" % p, re.I)) for p in PADROES_QUE_JULGAM]


def olhar_a_descricao(texto, origem="?"):
    """Devolve os avisos sobre o primeiro paragrafo de cada dimensao.

    A REGRA QUE ELE OLHA: em cada dimensao, o paragrafo aberto por
    "Descricao." descreve o que o projeto traz, e o aberto por
    "Avaliacao." julga. Descricao com adjetivo de qualidade ja e
    avaliacao, e a banca que le so ela recebe juizo achando que recebeu
    fato.

    O ROTULO E A FRONTEIRA, e nao a linha em branco. A primeira versao
    fechava o paragrafo descritivo na primeira linha vazia, e a leitura
    real nao pos linha vazia entre os dois: o conferidor tomou a dimensao
    inteira por descricao e acusou "adequada" que estava na AVALIACAO,
    nomeando a tese do proprio projeto. Num lote de vinte, isso e um jorro
    de acusacao errada, e acusacao errada custa mais que silencio.

    O QUE ELE NAO FAZ: recusar. Busca por palavra acusa errado, e "falha"
    e o nome de fenomeno estudado em mais de um projeto deste acervo.
    """
    avisos = []
    linhas = texto.split(chr(10))
    dimensao, paragrafo, dentro = None, [], False
    fim_do_descritivo = re.compile(r"^\s*Avalia[cç][aã]o\s*[.:]", re.I)
    abre_descritivo = re.compile(r"^\s*Descri[cç][aã]o\s*[.:]", re.I)

    def fechar():
        # SO O PRIMEIRO paragrafo de cada dimensao, que e o descritivo.
        if dimensao is None or not paragrafo:
            return False
        junto = " ".join(paragrafo)
        for padrao, rx in RE_JULGAM:
            m = rx.search(junto)
            if m:
                avisos.append("%s, dimensao %s: a descricao usa %r"
                              % (origem, dimensao, m.group(0)))
        if chr(34) in junto or chr(8220) in junto:
            avisos.append("%s, dimensao %s: a descricao tem aspas, e ela e "
                          "reconstrucao, nao transcricao" % (origem, dimensao))
        return True

    for linha in linhas:
        cabeca = re.match(r"^\s*#*\s*([1-5])[.)]\s+([A-ZÀ-Ú][^\n]*)", linha)
        if cabeca:
            dimensao, paragrafo, dentro = cabeca.group(1), [], True
            continue
        if not dentro:
            continue
        if fim_do_descritivo.match(linha):
            fechar()
            dentro = False
            paragrafo = []
            continue
        if linha.strip():
            if abre_descritivo.match(linha) and paragrafo:
                paragrafo = []          # o que veio antes nao era a descricao
            paragrafo.append(linha.strip())
        elif paragrafo:
            if fechar():
                dentro = False
            paragrafo = []
    if paragrafo:
        fechar()
    return avisos


def provar_a_descricao():
    """Controle positivo. Conferidor que nunca acusou nada nao informa
    nada quando fica em silencio."""
    base = ("## 1. Problema e justificativa" + chr(10) +
            "%s" + chr(10) * 2 +
            "Avaliacao: a pergunta nao se responde com a fonte escolhida." +
            chr(10) * 2 + "## 2. Metodologia e teoria" + chr(10) +
            "O projeto nomeia como fonte os acordaos do topico 4." + chr(10) * 2 +
            "Avaliacao: falta a operacao." + chr(10))
    casos = [
        ("descricao limpa",
         base % "O projeto enuncia a pergunta no topico 2 e a fonte no 4.", 0),
        ("adjetivo de qualidade na descricao",
         base % "O projeto enuncia uma pergunta vaga no topico 2.", 1),
        ("aspas na descricao",
         base % ("O projeto enuncia a pergunta como " + chr(34) +
                 "de que modo o juiz decide" + chr(34) + " no topico 2."), 1),
        ("o adjetivo na Avaliacao, SEM linha em branco antes dela",
         ("## 1. Problema e justificativa" + chr(10) +
          "Descricao. O projeto enuncia a pergunta no topico 2." + chr(10) +
          "Avaliacao. A categoria e adequada e a pergunta e vaga." + chr(10)), 0),
        ("o adjetivo na Descricao rotulada",
         ("## 1. Problema e justificativa" + chr(10) +
          "Descricao. O projeto enuncia uma pergunta vaga no topico 2." + chr(10) +
          "Avaliacao. Isso e bloqueio de partida." + chr(10)), 1),
        ("o adjetivo no paragrafo AVALIATIVO nao acusa",
         ("## 1. Problema e justificativa" + chr(10) +
          "O projeto enuncia a pergunta no topico 2." + chr(10) * 2 +
          "A pergunta e vaga e generica, e isso e impeditivo." + chr(10)), 0),
    ]
    print("Controle positivo do olhar sobre a descricao:")
    ok = True
    for nome, texto, esperados in casos:
        houve = len(olhar_a_descricao(texto, "teste"))
        certo = houve == esperados
        ok = ok and certo
        print("  %-42s %d aviso(s), esperava %d  %s"
              % (nome, houve, esperados, "ok" if certo else "DIVERGIU"))
    print()
    print("O olhar separa os casos." if ok
          else "O OLHAR NAO SEPARA OS CASOS. Nao confie no silencio dele.")
    return ok


def agregar(pasta, pdf=None):
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

    # A DIMENSAO 5 NAO TEM COLUNA DE NOTA: ela tem coluna de nivel, e
    # fica fora da media. Enquanto ela pontuava, esta tabela imprimia
    # notas[5]; depois que ela saiu da conta, notas[5] deixou de existir e
    # o agregador quebrava na primeira linha. O controle nao pegou porque
    # ele exercita ler_bloco, e nao agregar.
    larg = max([len(k) for k in lidos] + [len("projeto (ordem alfabetica)")])
    cab = "%-*s  %4s %4s %4s %4s  %5s  %-10s %-13s %s" % (
        larg, "projeto (ordem alfabetica)", "1", "2", "3", "4",
        "media", "selecao", "qualifica", "indicios de IA")
    print(cab)
    print("-" * len(cab))
    for nome in sorted(lidos):
        d = lidos[nome]
        n = d["notas"]
        print("%-*s  %4d %4d %4d %4d  %5.1f  %-10s %-13s %s" % (
            larg, nome, n[1], n[2], n[3], n[4], d["media"],
            d["selecao"], d["qualifica"], d["nivel"]))
    print()

    # ------------------------------------------------ a coorte, so contagem
    total = len(lidos)
    passam = sum(1 for d in lidos.values() if d["media"] >= LINHA_SELECAO)
    qualif = sum(1 for d in lidos.values() if not d["abaixo"])
    print("COORTE, e aqui so se conta:")
    print("  projetos lidos                         : %d" % total)
    print("  media 7 ou mais (linha da selecao)     : %d" % passam)
    print("  nenhuma dimensao abaixo de 7           : %d" % qualif)
    # SO AS QUATRO QUE TEM NOTA. Percorrer DIMENSOES inteira aqui buscava
    # notas[5], que deixou de existir quando os indicios sairam da conta, e
    # o lote quebrava DEPOIS de imprimir metade do relatorio, que e o pior
    # momento para quebrar: parece que terminou.
    for i, nome in enumerate(DIMENSOES[:4], 1):
        baixas = sum(1 for d in lidos.values() if d["notas"][i] < 7)
        media = sum(d["notas"][i] for d in lidos.values()) / float(total)
        print("  dim %d %-24s abaixo de 7 em %d de %d, media %.1f"
              % (i, nome, baixas, total, media))
    for nivel in NIVEIS:
        quantos = sum(1 for d in lidos.values() if d["nivel"] == nivel)
        if quantos:
            print("  indicios %-24s %d de %d" % (nivel, quantos, total))
    print()
    avisos = []
    for nome in sorted(lidos):
        avisos.extend(olhar_a_descricao(lidos[nome]["texto"], nome))
    if avisos:
        print("O PARAGRAFO DESCRITIVO, em %d ponto(s):" % len(avisos))
        for a in avisos:
            print("  -", a)
        print("  Isto e busca por palavra, e ela acusa errado: 'consistente'")
        print("  pode estar descrevendo o que o projeto diz de si. Confira")
        print("  antes de pedir correcao; o programa nao recusou nada.")
        print()

    if pdf:
        escrever_pdf(lidos, pdf)
        print("  %s: relatorio do lote com a tabela comparativa." % pdf)
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
APTO | apto | delimitar a lista de casos
FIM"""


def controle():
    """Positivo: cada defeito que o conferidor deveria pegar tem de reprovar."""
    ok = ler_bloco(BOM, "controle")
    assert ok["media"] == 5.5 and ok["abaixo"] == [1, 2, 3], ok
    assert ok["nivel"] == "leves", ok
    assert ok["apto"] == "apto" and ok["mudar"], ok
    print("  o bloco bom passa                                 ok")

    casos = [
        ("media que nao bate", BOM.replace("MEDIA | 5.5", "MEDIA | 7.4")),
        ("selecao contradiz a media", BOM.replace("nao passa", "passa")),
        ("qualifica omite uma dimensao baixa",
         BOM.replace("| 1,2,3", "| 1,2")),
        ("nota fora de 0-10", BOM.replace("| 0 | 3 | 7", "| 0 | 3 | 17")),
        ("nivel invalido", BOM.replace("| leves", "| razoavel")),
        ("dimensao 5 com nota", BOM.replace("- | leves", "- | 8")),
        ("sem a linha APTO",
         BOM.replace("APTO | apto | delimitar a lista de casos" + chr(10), "")),
        ("APTO com palavra que nao existe",
         BOM.replace("APTO | apto |", "APTO | talvez |")),
        ("APTO diz apto e nao diz o que mudaria",
         BOM.replace("APTO | apto | delimitar a lista de casos",
                     "APTO | apto | ")),
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
    print()
    if not provar_a_descricao():
        sys.exit(1)
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
        if sys.argv[1] == "preparar":
            preparar(sys.argv[2])
        else:
            # O terceiro argumento, se vier, e o PDF do lote.
            agregar(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
