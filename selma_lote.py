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
# A dimensao 5 nao tem nota e nao entra na media: leva o NIVEL.
# Os mesmos nomes, acentuados, para o que vai impresso. Os de DIMENSOES
# ficam sem acento porque e assim que o bloco de dados os traz e e assim
# que o programa os compara; peca que um examinador le nao sai sem acento.
NOMES_LEGIVEIS = ["problema e justificativa", "metodologia e teoria",
                  "contribuições e impacto", "bibliografia",
                  "indícios de IA"]

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
    notas, contagem, abaixo = {}, {}, None
    nivel = titulo = None
    condicoes = []
    for l in linhas:
        campos = [c.strip() for c in l.split("|")]
        if campos[0] == "TITULO":
            # LOCALIZADOR, E NUNCA TEXTO. O titulo identifica a peca, e uma
            # palavra trocada nele nao degrada uma citacao: faz a peca
            # apontar para outro projeto. Quem o copia e o programa.
            alvo = campos[1].strip()
            m2 = re.fullmatch(r"[Pp]?0*(\d{1,4})", alvo)
            if not m2:
                raise BlocoInvalido(
                    "%s: TITULO diz %r, e ali vai o LOCALIZADOR do titulo "
                    "(P002), nunca o titulo escrito" % (origem, alvo))
            titulo = int(m2.group(1))
        elif campos[0] == "CONDICAO":
            alvo = campos[1].strip()
            texto_c = campos[2].strip() if len(campos) > 2 else ""
            if alvo == "-":
                if texto_c.lower() not in ("nenhuma", "nenhum", ""):
                    raise BlocoInvalido(
                        "%s: CONDICAO com traco diz %r, esperava nenhuma"
                        % (origem, texto_c))
                continue
            if not alvo.isdigit() or not 1 <= int(alvo) <= 5:
                raise BlocoInvalido("%s: CONDICAO aponta a dimensao %r, "
                                    "esperava de 1 a 5" % (origem, alvo))
            if not texto_c:
                raise BlocoInvalido("%s: CONDICAO da dimensao %s nao diz o "
                                    "que fazer" % (origem, alvo))
            condicoes.append((int(alvo), texto_c))
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
            contagem[i] = (int(campos[2]), int(campos[3]), int(campos[4]))
        else:
            raise BlocoInvalido("%s: linha nao reconhecida: %r" % (origem, l))

    if len(notas) != 4:
        raise BlocoInvalido("%s: %d dimensoes com nota, esperava 4"
                            % (origem, len(notas)))
    if nivel is None:
        raise BlocoInvalido("%s: falta o nivel da dimensao 5" % origem)
    if titulo is None:
        raise BlocoInvalido("%s: falta a linha TITULO com o localizador"
                            % origem)
    if "CONDICAO" not in m.group(1):
        raise BlocoInvalido("%s: nenhuma linha CONDICAO. Quando nao ha "
                            "condicao, o bloco traz uma linha com traco e a "
                            "palavra nenhuma" % origem)

    # A CONTAGEM E A LISTA DE CONDICOES TEM DE SE CORRESPONDER. Impeditivo
    # e bloqueio de partida viram condicao sempre; localizado nao vira. O
    # bloco que diz zero impeditivos e zero bloqueios e traz condicao, ou o
    # contrario, esta contando uma coisa e concluindo outra.
    baixas = sorted(i for i, n in notas.items() if n < 7)
    caras = sorted(i for i in contagem if contagem[i][0] or contagem[i][1])
    com_condicao = sorted({d for d, _ in condicoes})
    faltando = [d for d in caras if d not in com_condicao]
    if faltando:
        raise BlocoInvalido(
            "%s: a dimensao %s tem impeditivo ou bloqueio e nenhuma condicao "
            "saiu dela" % (origem, ", ".join(str(x) for x in faltando)))
    sobrando = [d for d in com_condicao if d in contagem
                and not (contagem[d][0] or contagem[d][1])]
    if sobrando:
        raise BlocoInvalido(
            "%s: a dimensao %s tem condicao e nenhum impeditivo ou bloqueio"
            % (origem, ", ".join(str(x) for x in sobrando)))
    # O TEXTO DO RELATORIO VAI JUNTO, sem o bloco de dados: e ele que o
    # PDF do lote reproduz. O bloco sai porque ele existe para o programa
    # ler, e nao para a banca; deixa-lo faria a peca terminar em tabela
    # de campos separados por barra.
    corpo = (texto[:m.start()] + texto[m.end():]).strip()
    return {"notas": notas, "abaixo": baixas, "nivel": nivel,
            "titulo": titulo, "condicoes": condicoes, "texto": corpo}


def copiar_titulo(projeto, localizador):
    """Copia do projeto o paragrafo que a leitura apontou como titulo.

    Devolve (titulo, aviso). O aviso e None quando deu certo, e diz o que
    houve quando nao deu. NUNCA levanta: peca sem titulo ainda serve, e
    peca com titulo inventado, nao.
    """
    caminho = Path(projeto)
    if not caminho.is_file():
        return None, "nao achei %s" % caminho
    suf = caminho.suffix.lower()
    try:
        if suf == ".pdf":
            from comentar_pdf import ler
            paras = [p["texto"] for p in ler(str(caminho))]
        elif suf == ".docx":
            from comentar_projeto import texto_do_docx
            paras = [p.strip() for p in texto_do_docx(caminho) if p.strip()]
        else:
            from comentar_projeto import texto_do_md
            paras = [" ".join(p.split()) for p in texto_do_md(caminho)
                     if p.strip()]
    except Exception as e:                      # extrator quebrado nao inventa
        return None, "nao consegui ler %s: %s" % (caminho.name, e)
    if not 1 <= localizador <= len(paras):
        return None, ("o relatorio aponta o titulo em P%03d e %s tem %d "
                      "paragrafos" % (localizador, caminho.name, len(paras)))
    return " ".join(paras[localizador - 1].split()), None


def e_titulo(linha):
    """Linha curta e toda em maiusculas e titulo.

    A leitura nao escreve "#": ela datilografa o titulo em caixa alta,
    como num parecer. Enquanto o programa so reconhecia "#", os titulos
    das cinco dimensoes sairam em corpo de texto, sem negrito e sem ar em
    volta, e a peca ficou sem hierarquia nenhuma no corpo.

    O TESTE E ESTRITO de proposito: todas as letras maiusculas. Paragrafo
    de prosa tem minuscula na primeira palavra, sempre.
    """
    s = linha.strip().rstrip(":")
    if not s or len(s) > 70:
        return False
    letras = [c for c in s if c.isalpha()]
    return len(letras) >= 3 and all(c.isupper() for c in letras)


def blocos_do_relatorio(texto):
    """Parte o relatorio em titulos e paragrafos.

    TITULO E BLOCO PROPRIO, ainda que nao venha seguido de linha em
    branco. Partindo so por linha em branco, o titulo grudava no
    paragrafo seguinte e A PAGINA INTEIRA SAIA EM NEGRITO, porque o bloco
    todo herdava a fonte do titulo. O titulo de primeiro nivel, marcado
    com um "#" so, sai fora: o nome do projeto ja encabeca a peca.
    """
    blocos, atual = [], []

    def fechar():
        if atual:
            blocos.append(("prosa", " ".join(" ".join(atual).split())))
            del atual[:]

    for linha in texto.split(chr(10)):
        crua = linha.strip()
        if crua.startswith(chr(96) * 3):
            # A CERCA DE CODIGO E MARCA DO TRANSPORTE, e nao do documento:
            # a leitura entrega o relatorio dentro de um bloco de codigo, e
            # as tres crases sairam impressas como se fossem paragrafo.
            fechar()
            continue
        if crua.startswith("#"):
            fechar()
            nivel = len(linha) - len(linha.lstrip("#"))
            if nivel > 1:
                blocos.append(("titulo", crua.lstrip("# ").strip()))
        elif e_titulo(crua):
            fechar()
            blocos.append(("titulo", crua.rstrip(":")))
        elif crua:
            atual.append(crua)
        else:
            fechar()
    fechar()
    return [(tipo, txt) for tipo, txt in blocos if txt]


def nivel_do_titulo(txt):
    """Bloco do relatorio (1., 2., 3.) ou dimensao (1, 2, 3)?

    Os dois sairam no mesmo corpo, e o segundo esta DENTRO do primeiro:
    quem folheia nao via o encaixe. O ponto depois do numero e o que os
    separa, e e a propria leitura que o escreve assim.
    """
    return 1 if re.match(r"^\d+\.", txt.strip()) else 2


def escrever_leitura(f, nome, d, com_tarja=True, cabecalho=True):
    """A leitura inteira de um projeto, na folha que vier."""
    from folha_pdf import COR_MARCA, CORPO as CORPO_TEXTO
    if cabecalho:
        f.texto(nome, corpo=14, fonte="tibo", espaco_depois=3)
    if com_tarja:
        f.texto("notas %s  |  indícios de IA: %s  |  %d condi%s"
                % ("  ".join("%d:%d" % (i, d["notas"][i]) for i in (1, 2, 3, 4)),
                   d["nivel"], len(d["condicoes"]),
                   "ção" if len(d["condicoes"]) == 1 else "ções"),
                corpo=9, fonte="tibo", cor=COR_MARCA, espaco_depois=10)
    blocos = blocos_do_relatorio(d["texto"])
    for i, (tipo, texto_bloco) in enumerate(blocos):
        if tipo == "titulo":
            nivel = nivel_do_titulo(texto_bloco)
            corpo = 12.5 if nivel == 1 else 11
            antes = 18 if nivel == 1 else 13
            # O TITULO NAO FICA SOZINHO NO PE DA PAGINA. Duas linhas do
            # que vem depois bastam, porque o paragrafo agora se parte: o
            # que nao couber continua na pagina seguinte.
            f.juntar([antes, f.altura_de(texto_bloco, corpo, "tibo"), 6,
                      2 * CORPO_TEXTO * 1.42])
            f.texto(texto_bloco, corpo=corpo, fonte="tibo",
                    espaco_antes=antes, espaco_depois=6)
        else:
            f.texto(texto_bloco, espaco_depois=7)


def escrever_um(nome, d, caminho, titulo=None):
    """A leitura de UM projeto, em PDF.

    SEM TABELA COMPARATIVA E SEM CONTAGEM DE COORTE: a primeira compara
    com nada, e a segunda, com um projeto so, e a repeticao das notas com
    outra redacao. No lugar delas, a ficha das quatro notas e as tres
    linhas por extenso, cada uma dizendo o que decide.
    """
    try:
        import fitz
    except ImportError:
        sys.exit("A saida em PDF precisa do PyMuPDF: pip install pymupdf")
    from folha_pdf import (Folha, numerar_paginas, tabela, gravar,
                           COR_FRACA, CORPO as CORPO_TEXTO)

    doc = fitz.open()
    f = Folha(doc)
    f.texto("Leitura de projeto de pesquisa", corpo=17, fonte="tibo",
            espaco_depois=4)
    if titulo:
        f.texto(titulo, corpo=11.5, fonte="tibo", espaco_depois=3)
        f.texto("Título copiado do próprio projeto por programa, do "
                "parágrafo P%03d." % d["titulo"],
                corpo=8.5, fonte="tiit", cor=COR_FRACA, espaco_depois=14)
    else:
        f.texto(nome, corpo=11.5, fonte="tibo", espaco_depois=3)
        f.texto("Este é o nome do arquivo, e não o título do projeto: o "
                "projeto não foi informado, e título não se digita.",
                corpo=8.5, fonte="tiit", cor=COR_FRACA, espaco_depois=14)

    n = d["notas"]
    tabela(f, ["dimensão", "nota"],
           [[NOMES_LEGIVEIS[i - 1], n[i]] for i in (1, 2, 3, 4)]
           + [[NOMES_LEGIVEIS[4] + " (sem nota)", d["nivel"]]],
           [70, 30])

    f.texto("Condições para que o projeto seja apresentável a uma banca de "
            "qualificação", corpo=12.5, fonte="tibo", espaco_antes=10,
            espaco_depois=7)
    if not d["condicoes"]:
        f.texto("Nenhuma. Nenhum impeditivo e nenhum bloqueio de partida em "
                "dimensão nenhuma.", espaco_depois=8)
    else:
        for k, (dim, texto_c) in enumerate(d["condicoes"], 1):
            f.texto("%d. %s" % (k, texto_c), corpo=10.5, espaco_depois=2)
            f.texto("dimensão %d, %s" % (dim, NOMES_LEGIVEIS[dim - 1]),
                    corpo=9, fonte="tiit", cor=COR_FRACA, recuo=14,
                    espaco_depois=7)

    f.texto("Esta lista não é recomendação de admitir ou não admitir. Ela diz "
            "o que falta ao documento, e a decisão se toma com coisas que a "
            "leitura não tem: os outros candidatos, as vagas, a linha de "
            "pesquisa, a trajetória de cada um. E o nível dos indícios de IA "
            "não vira condição e não entra em nota nenhuma: ele viaja ao lado, "
            "e quem decide o que fazer com ele é a banca.",
            corpo=9.5, fonte="tiit", cor=COR_FRACA, espaco_antes=4,
            espaco_depois=10)

    f.nova()
    # SEM CABECALHO: a pagina anterior ja traz o titulo copiado, e repetir
    # o nome do arquivo ali foi o que pos "deferencia2" no alto da peca.
    escrever_leitura(f, nome, d, com_tarja=False, cabecalho=False)
    numerar_paginas(doc)
    gravar(doc, caminho)
    doc.close()


def um(caminho_md, caminho_pdf=None, projeto=None):
    """Le UM relatorio da Selma e escreve o PDF dele."""
    arq = Path(caminho_md)
    if not arq.is_file():
        sys.exit("Nao achei %s" % arq)
    try:
        d = ler_bloco(arq.read_text(encoding="utf-8"), arq.name)
    except BlocoInvalido as e:
        sys.exit("RELATORIO RECUSADO: %s" % e)

    avisos = olhar_a_descricao(d["texto"], arq.stem)
    if avisos:
        print("O PARAGRAFO DESCRITIVO, em %d ponto(s):" % len(avisos))
        for a in avisos:
            print("  -", a)
        print("  Isto e busca por palavra, e ela acusa errado. Confira antes")
        print("  de pedir correcao; o programa nao recusou nada.")
        print()

    # O TITULO SE COPIA DO PROJETO, e nao se digita. Sem o projeto na mao,
    # a peca sai identificada pelo nome do arquivo, dizendo que e o nome do
    # arquivo: peca que exibe titulo que ninguem copiou parece identificada
    # e nao esta.
    titulo, aviso = (None, "o projeto nao foi informado (use --projeto)")
    if projeto:
        titulo, aviso = copiar_titulo(projeto, d["titulo"])
    if aviso:
        print("SEM O TITULO: %s." % aviso)
        print("A peca sai com o nome do arquivo, e dizendo que e o nome do")
        print("arquivo. O relatorio aponta o titulo em P%03d." % d["titulo"])
        print()

    saida = caminho_pdf or str(arq.with_suffix(".pdf"))
    escrever_um(arq.stem, d, saida, titulo)
    print("%s: notas %s, indicios %s, %d condicao(oes)."
          % (saida, ", ".join(str(d["notas"][i]) for i in (1, 2, 3, 4)),
             d["nivel"], len(d["condicoes"])))
    print("A ficha foi montada pelo programa a partir do bloco de dados ja")
    print("conferido, e nao redigitada.")


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
    from folha_pdf import (Folha, numerar_paginas, tabela, gravar,
                           COR_FRACA, COR_MARCA)

    doc = fitz.open()
    f = Folha(doc)
    f.texto("Leituras de projetos de pesquisa", corpo=17, fonte="tibo",
            espaco_depois=4)
    f.texto("%d projetos. As notas vão de 0 a 10 em quatro dimensões; os "
            "indícios de IA não têm nota e viajam ao lado. A última coluna traz "
            "quantas condições o projeto precisa cumprir para ser apresentável "
            "a uma banca de qualificação. A ordem é alfabética." % len(lidos),
            corpo=9.5, fonte="tiit", cor=COR_FRACA, espaco_depois=16)

    # AS TRES LINHAS DO VEREDITO VAO NA TABELA, e nao so as duas: a
    # aptidao e a que diz se o trabalho se conserta, e e a que muda o que
    # a banca faz depois. Deixa-la so no corpo do relatorio obrigaria a
    # abrir cada leitura para saber.
    cabecalho = ["projeto", "1", "2", "3", "4", "indícios de IA",
                 "condições"]
    linhas = []
    for nome in sorted(lidos):
        d = lidos[nome]
        n = d["notas"]
        linhas.append([nome, n[1], n[2], n[3], n[4], d["nivel"],
                       len(d["condicoes"])])
    # As larguras foram medidas na pagina renderizada, e nao chutadas:
    # com as anteriores, "media" quebrava em "medi/a" e "nao recomendo"
    # em duas linhas. As colunas de nota levam um digito e nao precisam
    # de espaco; as de veredito levam palavra e precisam.
    tabela(f, cabecalho, linhas, [38, 4, 4, 4, 4, 17, 10])

    total = len(lidos)
    sem_condicao = sum(1 for d in lidos.values() if not d["condicoes"])
    f.texto("A coorte, e aqui só se conta", corpo=12.5, fonte="tibo",
            espaco_antes=10, espaco_depois=6)
    conta = ["projetos lidos: %d" % total,
             "sem nenhuma condição a cumprir: %d" % sem_condicao,
             "condições ao todo: %d"
             % sum(len(d["condicoes"]) for d in lidos.values())]
    for i, nome in enumerate(NOMES_LEGIVEIS[:4], 1):
        baixas = sum(1 for d in lidos.values() if d["notas"][i] < 7)
        media = sum(d["notas"][i] for d in lidos.values()) / float(total)
        conta.append("dimensão %d, %s: abaixo de 7 em %d de %d, média %.1f"
                     % (i, nome, baixas, total, media))
    for nivel in NIVEIS:
        quantos = sum(1 for d in lidos.values() if d["nivel"] == nivel)
        if quantos:
            conta.append("indícios %s: %d" % (nivel, quantos))
    for c in conta:
        f.texto("- " + c, espaco_depois=3)
    f.texto("Contar é transcrever. Dizer que a turma tem dificuldade com "
            "metodologia seria afirmação nova sobre uma população, e não "
            "sai daqui.", corpo=9.5, fonte="tiit", cor=COR_FRACA,
            espaco_antes=8, espaco_depois=10)

    for nome in sorted(lidos):
        f.nova()
        escrever_leitura(f, nome, lidos[nome])

    numerar_paginas(doc)
    gravar(doc, caminho)
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
    cab = "%-*s  %4s %4s %4s %4s  %-22s %s" % (
        larg, "projeto (ordem alfabetica)", "1", "2", "3", "4",
        "indicios de IA", "condicoes")
    print(cab)
    print("-" * len(cab))
    for nome in sorted(lidos):
        d = lidos[nome]
        n = d["notas"]
        print("%-*s  %4d %4d %4d %4d  %-22s %d" % (
            larg, nome, n[1], n[2], n[3], n[4], d["nivel"],
            len(d["condicoes"])))
    print()

    # ------------------------------------------------ a coorte, so contagem
    total = len(lidos)
    sem_condicao = sum(1 for d in lidos.values() if not d["condicoes"])
    print("COORTE, e aqui so se conta:")
    print("  projetos lidos                         : %d" % total)
    print("  sem nenhuma condicao a cumprir         : %d" % sem_condicao)
    print("  condicoes ao todo                      : %d"
          % sum(len(d["condicoes"]) for d in lidos.values()))
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
    print("  A ordem da tabela e alfabetica, de proposito. Nao ha media, e a")
    print("  contagem de condicoes tambem nao ordena: duas condicoes pequenas")
    print("  nao valem menos que uma grande, e o que pesa esta escrito nelas.")

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
        difs = [abs(v["a"]["notas"][i] - v["b"]["notas"][i])
                for i in range(1, 5)]
        print("  %-30s por dimensao: %s | maior: %d | condicoes %d vs %d"
              % (k, difs, max(difs), len(v["a"]["condicoes"]),
                 len(v["b"]["condicoes"])))


# --------------------------------------------------------------- controle
BOM = """DADOS
TITULO | P002
1 | problema e justificativa | 0 | 1 | 1 | 5
2 | metodologia e teoria | 1 | 0 | 2 | 4
3 | contribuicoes e impacto | 0 | 1 | 0 | 6
4 | bibliografia | 0 | 0 | 3 | 7
5 | indicios de ia | - | - | - | leves
CONDICAO | 1 | dizer quem decidiria diferente conforme a resposta
CONDICAO | 2 | fechar a lista de casos antes de comecar
CONDICAO | 3 | dizer que decisao passa a ser tomada de outro modo
FIM"""


def controle():
    """Positivo: cada defeito que o conferidor deveria pegar tem de reprovar."""
    ok = ler_bloco(BOM, "controle")
    assert ok["abaixo"] == [1, 2, 3], ok
    assert ok["nivel"] == "leves", ok
    assert ok["titulo"] == 2, ok
    assert len(ok["condicoes"]) == 3, ok
    assert ok["condicoes"][0][0] == 1 and ok["condicoes"][0][1], ok
    print("  o bloco bom passa                                 ok")

    casos = [
        ("nota fora de 0-10", BOM.replace("| 0 | 3 | 7", "| 0 | 3 | 17")),
        ("nivel invalido", BOM.replace("| leves", "| razoavel")),
        ("dimensao 5 com nota", BOM.replace("- | leves", "- | 8")),
        ("sem a linha TITULO",
         BOM.replace("TITULO | P002" + chr(10), "")),
        ("TITULO com o titulo escrito, e nao o localizador",
         BOM.replace("TITULO | P002",
                     "TITULO | A deferencia judicial como limite")),
        ("TITULO sem numero", BOM.replace("TITULO | P002", "TITULO | P")),
        ("sem nenhuma linha CONDICAO",
         chr(10).join(l for l in BOM.split(chr(10))
                      if not l.startswith("CONDICAO"))),
        ("CONDICAO aponta dimensao que nao existe",
         BOM.replace("CONDICAO | 1 |", "CONDICAO | 8 |")),
        ("CONDICAO que nao diz o que fazer",
         BOM.replace("CONDICAO | 1 | dizer quem decidiria diferente "
                     "conforme a resposta", "CONDICAO | 1 |")),
        ("dimensao com impeditivo e nenhuma condicao saida dela",
         BOM.replace("CONDICAO | 2 | fechar a lista de casos antes de "
                     "comecar" + chr(10), "")),
        ("condicao numa dimensao sem impeditivo nem bloqueio",
         BOM.replace("4 | bibliografia | 0 | 0 | 3 | 7",
                     "4 | bibliografia | 0 | 0 | 3 | 7" + chr(10) +
                     "CONDICAO | 4 | trocar a bibliografia inteira")),
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
    try:
        from folha_pdf import provar_a_folha
    except SystemExit:
        print("(sem PyMuPDF: o conferidor de sobreposicao nao rodou)")
    else:
        if not provar_a_folha():
            sys.exit(1)
    print()
    print("O conferidor reprova os %d casos. Sem este controle, um bloco"
          % len(casos))
    print("aceito nao informaria nada: silencio de conferidor quebrado tem a")
    print("mesma aparencia de silencio de dado correto.")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("preparar", "agregar", "um",
                                               "controle"):
        sys.exit(__doc__)
    if sys.argv[1] == "controle":
        controle()
    else:
        if len(sys.argv) < 3:
            sys.exit("falta a pasta")
        if sys.argv[1] == "um":
            # selma_lote.py um relatorio.md [saida.pdf] [projeto.pdf]
            um(sys.argv[2],
               sys.argv[3] if len(sys.argv) > 3 else None,
               sys.argv[4] if len(sys.argv) > 4 else None)
        elif sys.argv[1] == "preparar":
            preparar(sys.argv[2])
        else:
            # O terceiro argumento, se vier, e o PDF do lote.
            agregar(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
