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
tiveram grave em cada dimensao, qual dimensao foi a mais fraca no
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

DIMENSOES = ["problema, objetivos e hipoteses", "justificativa",
             "metodologia e teoria", "bibliografia", "indicios de ia"]
# A dimensao 5 nao tem nota e nao entra na media: leva o NIVEL.
# Os mesmos nomes, acentuados, para o que vai impresso. Os de DIMENSOES
# ficam sem acento porque e assim que o bloco de dados os traz e e assim
# que o programa os compara; peca que um examinador le nao sai sem acento.
NOMES_LEGIVEIS = ["problema, objetivos e hipóteses", "justificativa",
                  "metodologia e teoria", "bibliografia",
                  "indícios de IA"]

NIVEIS = ["fortes-abusivo", "fortes", "medios", "fracos", "ausentes"]
# O NIVEL SAI POR EXTENSO NA PECA: no bloco de dados vai a palavra curta,
# que e o que o programa compara, e quem le a peca ve a frase.
# E A FORMA CURTA, para onde a palavra "indicios" ja esta escrita ao
# lado: na ficha, cuja linha se chama "5. indicios de IA", e no console.
NIVEIS_CURTOS = {
    "fortes-abusivo": "fortes (uso abusivo)",
    "fortes": "fortes",
    "medios": "médios",
    "fracos": "fracos",
    "ausentes": "não há",
}
NIVEIS_LEGIVEIS = {
    "fortes-abusivo": "indícios fortes (uso abusivo)",
    "fortes": "indícios fortes",
    "medios": "indícios médios",
    "fracos": "indícios fracos",
    "ausentes": "não há indícios",
}

# COMO A LEITURA CHAMA CADA ELEMENTO no titulo, quando o nome dela nao e o
# da tabela. So o quinto diverge: o prompt o chama de indicios de USO de
# IA, e a tabela o chama de indicios de IA.
OUTROS_NOMES = {5: ["indicios de uso de ia"]}


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
    nivel = titulo = impressao = None
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
        elif campos[0] == "IMPRESSAO":
            # A impressao digital da numeracao. Traco quando nao houve
            # numeracao: o localizador do titulo vale, e ninguem o conferiu.
            alvo = campos[1].strip()
            if alvo not in ("-", ""):
                if not re.fullmatch(r"\d+p-[0-9a-f]{8}", alvo):
                    raise BlocoInvalido(
                        "%s: IMPRESSAO diz %r, e ali vai a impressao da "
                        "numeracao, na forma 172p-a51ff850" % (origem, alvo))
                impressao = alvo
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
            # O QUARTO CAMPO, quando houver, e o ganho de arguicao: o que o
            # autor pode dizer para o elemento subir de faixa antes de a
            # condicao estar cumprida. Ele estava numa lista propria, e a
            # lista repetia o material das condicoes noutro lugar da peca.
            ganho = campos[3].strip() if len(campos) > 3 else ""
            condicoes.append((int(alvo), texto_c, ganho))
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

    # A CONTAGEM E A LISTA DE CONDICOES TEM DE SE CORRESPONDER. Grave
    # e médio viram condicao sempre; leve nao vira. O
    # bloco que diz zero graves e zero médios e traz condicao, ou o
    # contrario, esta contando uma coisa e concluindo outra.
    baixas = sorted(i for i, n in notas.items() if n < 7)
    caras = sorted(i for i in contagem if contagem[i][0] or contagem[i][1])
    com_condicao = sorted({c[0] for c in condicoes})
    faltando = [d for d in caras if d not in com_condicao]
    if faltando:
        raise BlocoInvalido(
            "%s: a dimensao %s tem grave ou médio e nenhuma condicao "
            "saiu dela" % (origem, ", ".join(str(x) for x in faltando)))
    sobrando = [d for d in com_condicao if d in contagem
                and not (contagem[d][0] or contagem[d][1])]
    if sobrando:
        raise BlocoInvalido(
            "%s: a dimensao %s tem condicao e nenhum grave ou médio"
            % (origem, ", ".join(str(x) for x in sobrando)))
    # O TEXTO DO RELATORIO VAI JUNTO, sem o bloco de dados: e ele que o
    # PDF do lote reproduz. O bloco sai porque ele existe para o programa
    # ler, e nao para a banca; deixa-lo faria a peca terminar em tabela
    # de campos separados por barra.
    corpo = (texto[:m.start()] + texto[m.end():]).strip()
    return {"notas": notas, "abaixo": baixas, "nivel": nivel,
            "titulo": titulo, "impressao": impressao, "contagens": contagem,
            "condicoes": condicoes, "texto": corpo}


def paragrafos_do_projeto_para_conferir(projeto):
    """Os paragrafos do projeto, no formato que a impressao digital pede."""
    caminho = Path(projeto)
    suf = caminho.suffix.lower()
    if suf == ".pdf":
        from comentar_pdf import ler
        return ler(str(caminho))
    if suf == ".docx":
        from comentar_projeto import texto_do_docx
        return [{"texto": p.strip()} for p in texto_do_docx(caminho)
                if p.strip()]
    from comentar_projeto import texto_do_md
    return [{"texto": " ".join(p.split())} for p in texto_do_md(caminho)
            if p.strip()]


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
    # E TITULO TAMBEM A LINHA CURTA QUE ABRE POR "Elemento 2.", que e a
    # outra forma em que a leitura escreve o titulo do elemento.
    if RE_ELEMENTO_ROTULADO.match(s):
        return True
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


RE_ELEMENTO = re.compile(r"^\s*(?:Elemento\s+)?([1-5])[.)]\s+(.+)$",
                         re.I)
RE_ELEMENTO_ROTULADO = re.compile(r"^Elemento\s+[1-5][.)]\s+\S", re.I)


def subtitulo_de_elemento(texto, numero_do_bloco):
    """Devolve "3.2 Justificativa", ou None se nao for isso.

    O TESTE E DUPLO, E O NUMERO SOZINHO NAO SERVE: tem de estar dentro da
    avaliacao analitica, e o nome tem de ser o nome daquele numero. Sem a
    segunda metade, "4. PERGUNTAS PARA AS QUAIS O AUTOR DEVE ESTAR
    PREPARADO" viraria o elemento 4.

    E O NOME SAI DA TABELA, e nao do que a leitura digitou: assim o
    titulo do elemento, a linha da ficha e a entrada da ementa dizem a
    mesma palavra.
    """
    if numero_do_bloco is None:
        return None
    m = RE_ELEMENTO.match(texto.strip())
    if not m:
        return None
    n = int(m.group(1))
    nome = NOMES_LEGIVEIS[n - 1]
    aceitos = [sem_acento(nome)] + [sem_acento(x)
                                    for x in OUTROS_NOMES.get(n, [])]
    if sem_acento(m.group(2)).strip(" .:") not in aceitos:
        return None
    return "%s.%d %s%s" % (numero_do_bloco, n, nome[0].upper(), nome[1:])


def partir_preambulo(blocos):
    """Separa as observacoes de abertura do corpo do relatorio.

    ELAS VEM DEPOIS DO PRIMEIRO TITULO, e nao antes: o relatorio abre com
    "RELATORIO DE LEITURA DE PROJETO DE PESQUISA", que e titulo, e as
    observacoes (a quem a peca serve, de onde vem o localizador, o que
    ficou fora) vem logo abaixo dele, ate o titulo seguinte.

    O TITULO DE ABERTURA NAO VOLTA, quando houver: ele repete o que o
    cabecalho da pagina ja diz. E ELE PODE NAO HAVER, porque o relatorio
    passou a abrir direto pelo paragrafo das circunstancias; nesse caso o
    preambulo e a prosa que vem antes do primeiro titulo.
    """
    if not blocos:
        return [], blocos
    comeco = 1 if blocos[0][0] == "titulo" else 0
    for i in range(comeco, len(blocos)):
        if blocos[i][0] == "titulo":
            return blocos[comeco:i], blocos[i:]
    return blocos[comeco:], []


RE_ENTRADA = re.compile(r"^\s*(\d\.\s*[^.]{3,60}\.)\s*(.*)$", re.S)
def partes_da_entrada(texto):
    """Parte uma entrada da ementa em (rotulo, resto).

    O ROTULO e o "2. Justificativa." do comeco, e e por onde o
    olho entra na lista: so ele fica em negrito.

    Quando a entrada nao tiver essa forma, devolve (None, texto) e quem
    chama a escreve como paragrafo comum: inventar rotulo onde nao ha
    poria em negrito o comeco de uma frase qualquer.
    """
    m = RE_ENTRADA.match(texto.strip())
    if not m:
        return None, texto
    return m.group(1), m.group(2)


def sem_acento(s):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").upper()


def partir_peca(blocos):
    """Devolve (observacoes, capa, analise).

    A CAPA e o que uma banca le quando le uma coisa so: a descricao geral
    e a ementa. A analise vem depois, para quem precisa do detalhe.

    A BUSCA E POR NOME, e nao por posicao, porque posicao muda quando a
    forma do relatorio muda e ninguem percebe. Quando os nomes nao
    aparecem, o programa cai no recurso posicional E DIZ QUE CAIU.
    """
    observacoes, resto = partir_preambulo(blocos)
    indices = [i for i, (tipo, _) in enumerate(resto) if tipo == "titulo"]
    fim = None
    for k, i in enumerate(indices):
        nome = sem_acento(resto[i][1])
        if "EMENTA" in nome:
            fim = indices[k + 1] if k + 1 < len(indices) else len(resto)
            break
    if fim is None:
        # Recurso: os dois primeiros blocos titulados sao a capa.
        fim = indices[2] if len(indices) > 2 else len(resto)
        print("AVISO: nao achei o bloco EMENTA pelo nome; usei os dois "
              "primeiros blocos como capa.")
    capa, analise = resto[:fim], resto[fim:]
    # AS CONDICOES SAEM DO CORPO, sempre: a peca as monta na primeira
    # pagina a partir do bloco de dados ja conferido, e lista repetida e
    # onde as duas versoes divergem sem que ninguem veja.
    analise = sem_condicoes(analise)
    capa = sem_condicoes(capa)
    return observacoes, capa, analise


def sem_condicoes(blocos):
    """Tira o bloco de condicoes e o que vem sob ele, ate o titulo seguinte."""
    saida, pulando = [], False
    for tipo, texto in blocos:
        if tipo == "titulo":
            pulando = "CONDIC" in sem_acento(texto) or "CONDIÇ" in texto.upper()
            if pulando:
                continue
        if not pulando:
            saida.append((tipo, texto))
    return saida


def sem_ganhos(blocos):
    """Tira o bloco dos ganhos de arguicao, e o que vem sob ele.

    O GANHO MORA NA CONDICAO, e a peca ja o imprime la. Reunido num bloco
    proprio, o mesmo material sai duas vezes, e a segunda vem dizendo que
    o elemento sobe de faixa, que e a mecanica da regua.

    E A REMOCAO SAI DITA NO CONSOLE: peca que perde um bloco em silencio
    esconde que a leitura escreveu fora da forma.
    """
    saida, pulando = [], False
    for tipo, texto in blocos:
        if tipo == "titulo":
            pulando = "ARGUIC" in sem_acento(texto)
            if pulando:
                print("AVISO: a leitura escreveu o bloco %r. A forma tem "
                      "quatro blocos," % " ".join(texto.split())[:52])
                print("  e o ganho vai dentro da condicao. Ele nao entrou "
                      "na peca.")
                continue
        if not pulando:
            saida.append((tipo, texto))
    return saida


RE_TITULO_DE_SECAO = re.compile(
    r"^\s*\d{1,2}(?:\.\d{1,2})*[.)]?\s+"
    r"([A-ZÀ-Ú][^\d,;:.]{3,68})\.?\s*$")


def secoes_do_projeto(paragrafos):
    """Os nomes das secoes, tirados dos titulos do proprio projeto.

    TITULO E UMA LINHA CURTA que abre por numero (com subdivisao, se
    houver) e traz um nome comecado por maiuscula, sem virgula, sem
    digito e sem ponto no meio. A CAIXA ALTA NAO SERVE DE TESTE: um
    projeto escreve "1 DELIMITACAO DO TEMA E JUSTIFICATIVA" e outro
    escreve "3.1. Objetivos.".

    E A NOTA DE RODAPE FICA FORA, que era o que a caixa alta protegia:
    "9 ADI 5.501/DF, Rel. Min. Marco Aurelio" tem virgula, digito e
    pontos no meio.
    """
    nomes = []
    for p in paragrafos:
        texto = " ".join(p["texto"].split())
        m = RE_TITULO_DE_SECAO.match(texto)
        if not m:
            continue
        nome = " ".join(m.group(1).split())
        if nome and nome not in nomes:
            nomes.append(nome)
    return nomes


def partes_com_secoes(texto, nomes):
    """Parte a prosa em (trecho, estilo), com "i" nos nomes de secao.

    E O NOME DE UMA PALAVRA SO ENTRA COM MAIUSCULA, porque ele costuma
    ser substantivo comum: grifar toda "metodologia" grifaria a palavra,
    e nao a remissao a secao.
    """
    if not nomes or not texto:
        return [(texto, None)]
    ordem = sorted(nomes, key=len, reverse=True)
    alt = []
    for nome in ordem:
        if len(nome.split()) == 1:
            n = nome.capitalize()
            alt.append("(?-i:%s)" % re.escape(n[0].upper() + n[1:].lower()))
        else:
            alt.append(re.escape(nome))
    padrao = re.compile("(?i:%s)" % "|".join(alt))
    partes, fim = [], 0
    for m in padrao.finditer(texto):
        if m.start() > fim:
            partes.append((texto[fim:m.start()], None))
        partes.append((m.group(0), "i"))
        fim = m.end()
    if fim < len(texto):
        partes.append((texto[fim:], None))
    return partes or [(texto, None)]


def escrever_leitura(f, nome, d, com_tarja=True, cabecalho=True,
                     blocos=None, secoes=()):
    """A leitura inteira de um projeto, na folha que vier."""
    from folha_pdf import COR_MARCA, CORPO as CORPO_TEXTO
    if cabecalho:
        f.texto(nome, corpo=15, fonte="tibo", espaco_depois=3, justificar=False)
    if com_tarja:
        f.texto("notas %s  |  indícios de IA: %s  |  %d condi%s"
                % ("  ".join("%d:%d" % (i, d["notas"][i]) for i in (1, 2, 3, 4)),
                   NIVEIS_CURTOS[d["nivel"]], len(d["condicoes"]),
                   "ção" if len(d["condicoes"]) == 1 else "ções"),
                corpo=10, fonte="tibo", cor=COR_MARCA, espaco_depois=10)
    if blocos is None:
        blocos = blocos_do_relatorio(d["texto"])
    na_ementa = False
    # O NUMERO DO BLOCO DA ANALISE, quando estamos dentro dele: e ele que
    # prefixa os elementos, e fora dele nao ha subtitulo nenhum.
    analise = None
    for i, (tipo, texto_bloco) in enumerate(blocos):
        if tipo == "titulo":
            sub = subtitulo_de_elemento(texto_bloco, analise)
            if sub is None:
                na_ementa = "EMENTA" in sem_acento(texto_bloco)
                nivel = nivel_do_titulo(texto_bloco)
                m_bloco = re.match(r"^\s*(\d+)[.)]", texto_bloco.strip())
                analise = (m_bloco.group(1) if m_bloco
                           and "ANALITICA" in sem_acento(texto_bloco) else None)
            else:
                na_ementa, nivel, texto_bloco = False, 3, sub
            corpo = {1: 13.5, 2: 12.5, 3: 11}[nivel]
            antes = {1: 18, 2: 16, 3: 14}[nivel]
            # O TITULO NAO FICA SOZINHO NO PE DA PAGINA. Duas linhas do
            # que vem depois bastam, porque o paragrafo agora se parte: o
            # que nao couber continua na pagina seguinte.
            f.juntar([antes, f.altura_de(texto_bloco, corpo, "tibo"), 6,
                      2 * CORPO_TEXTO * 1.42])
            f.texto(texto_bloco, corpo=corpo, fonte="tibo",
                    espaco_antes=antes, espaco_depois=6, justificar=False)
        else:
            # DENTRO DA EMENTA, o negrito e so do rotulo: e por onde o
            # olho entra na lista.
            rotulo, resto = (partes_da_entrada(texto_bloco)
                             if na_ementa else (None, texto_bloco))
            if rotulo:
                f.html([(rotulo + " ", "b")]
                       + partes_com_secoes(resto.strip(), secoes),
                       espaco_depois=7)
            elif secoes:
                f.html(partes_com_secoes(texto_bloco, secoes),
                       espaco_depois=7)
            else:
                f.texto(texto_bloco, espaco_depois=7)


OFICINA_NOME = "Oficina de Projetos do PMPD"
OFICINA_URL = "https://claude.ai/code/artifact/1d29d917-d73f-48b3-9f89-1eaab12cfffd"
CREDITO = ("Relatório escrito pela assistente Selma, da %s." % OFICINA_NOME)


def ancorar(f, texto, url):
    """Poe um link sobre TEXTO na pagina em que ele acabou de ser escrito.

    POR BUSCA, E NAO POR COORDENADA: quem escreveu o paragrafo foi o
    insert_textbox, e onde cada palavra caiu depende da quebra de linha.
    Achado o retangulo, o link vai nele.

    E SE NAO HOUVER EXATAMENTE UM ACHADO, nao ancora e avisa: link em
    lugar errado e pior que link nenhum, e o silencio aqui esconderia
    que a frase do credito mudou e ninguem viu.
    """
    caixas = f.pagina.search_for(texto)
    if len(caixas) != 1:
        print("AVISO: %r aparece %d vez(es) na pagina; o link nao foi posto."
              % (texto, len(caixas)))
        return False
    f.pagina.insert_link({"kind": 2, "from": caixas[0], "uri": url})
    return True


def escrever_um(nome, d, caminho, titulo=None, secoes=()):
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
    f.texto("Análise de Projeto de Pesquisa", corpo=18, fonte="tibo",
            espaco_depois=4, justificar=False)
    if titulo:
        f.texto(titulo, corpo=12.5, fonte="tibo", espaco_depois=14,
                justificar=False)
    else:
        f.texto(nome, corpo=12.5, fonte="tibo", espaco_depois=3, justificar=False)
        f.texto("Este é o nome do arquivo, e não o título do projeto: o "
                "projeto não foi informado, e título não se digita.",
                corpo=9.5, fonte="tiit", cor=COR_FRACA, espaco_depois=14)

    # AS OBSERVACOES DA LEITURA VEM ANTES DE QUALQUER NUMERO: elas dizem o
    # que a peca e, e quem le um numero antes disso ja o le como veredito.
    blocos = blocos_do_relatorio(d["texto"])
    preambulo, capa, corpo_da_leitura = partir_peca(blocos)
    # O CREDITO E DO PROGRAMA, e nao da leitura: assinatura que o modelo
    # digita é assinatura que pode sair diferente a cada execucao.
    abertura = " ".join([CREDITO] + [x for _, x in preambulo])
    f.texto(abertura, corpo=10.5, fonte="tiit", cor=COR_FRACA,
            espaco_depois=6)
    ancorar(f, OFICINA_NOME, OFICINA_URL)
    f.y += 8

    f.texto("Avaliação proposta", corpo=13.5, fonte="tibo", espaco_antes=6,
            espaco_depois=7, justificar=False)
    n = d["notas"]
    # SEM A PALAVRA "dimensao": a numeracao ja diz o que ela diria, e o
    # nome e vocabulario de quem construiu a regua, nao de quem le a peca.
    tabela(f, ["", "nota"],
           [["%d. %s" % (i, NOMES_LEGIVEIS[i - 1]), n[i]] for i in (1, 2, 3, 4)]
           + [["5. %s (sem nota)" % NOMES_LEGIVEIS[4],
               NIVEIS_CURTOS[d["nivel"]]]],
           [70, 30])

    f.texto("Condições para que o projeto seja apresentável a uma banca de "
            "qualificação", corpo=13.5, fonte="tibo", espaco_antes=10,
            espaco_depois=7)
    if not d["condicoes"]:
        f.texto("Nenhuma. Nenhum achado grave e nenhum médio em "
                "dimensão nenhuma.", espaco_depois=8)
    else:
        for k, (dim, texto_c, ganho) in enumerate(d["condicoes"], 1):
            f.texto("%d. %s" % (k, texto_c), corpo=11.5, espaco_depois=2)
            f.texto("%d. %s" % (dim, NOMES_LEGIVEIS[dim - 1]),
                    corpo=10, fonte="tiit", cor=COR_FRACA, recuo=14,
                    espaco_depois=3 if ganho else 7)
            if ganho:
                # SEM A REGRA: quem le a condicao quer saber o que dizer,
                # e nao como a regua reage ao que for dito.
                f.texto("Na arguição: %s" % ganho, corpo=10,
                        fonte="tiit", cor=COR_FRACA, recuo=14,
                        espaco_depois=7)

    f.texto("Esta lista não é recomendação de admitir ou não admitir. Ela diz "
            "o que falta ao documento, e a decisão se toma com coisas que a "
            "leitura não tem: os outros candidatos, as vagas, a linha de "
            "pesquisa, a trajetória de cada um. E o nível dos indícios de IA "
            "não vira condição e não entra em nota nenhuma: ele viaja ao lado, "
            "e quem decide o que fazer com ele é a banca.",
            corpo=10.5, fonte="tiit", cor=COR_FRACA, espaco_antes=4,
            espaco_depois=10)

    # A CAPA FECHA A PRIMEIRA PARTE: descricao geral e ementa, logo depois
    # das condicoes, para quem le uma coisa so ler tudo o que precisa.
    escrever_leitura(f, nome, d, com_tarja=False, cabecalho=False,
                     blocos=capa, secoes=secoes)

    # A AVALIACAO ANALITICA SEGUE NA MESMA PAGINA. A quebra ja esteve aqui
    # duas vezes e saiu duas vezes, e a razao de sair e a mesma: ela gasta
    # meia folha em branco no meio de uma peca de oito.
    #
    # SEM CABECALHO E SEM PREAMBULO: a pagina anterior ja traz o titulo
    # copiado e as observacoes, e repetir o nome do arquivo ali foi o que
    # pos "deferencia2" no alto da peca.
    escrever_leitura(f, nome, d, com_tarja=False, cabecalho=False,
                     blocos=sem_ganhos(corpo_da_leitura), secoes=secoes)
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
    secoes = []
    if projeto:
        # OS NOMES DAS SECOES SAEM DO PROJETO, para o italico da peca ter
        # de onde vir. Sem projeto nao ha italico: nao ha autoridade.
        secoes = secoes_do_projeto(
            paragrafos_do_projeto_para_conferir(projeto))
        # A NUMERACAO PRIMEIRO. O localizador do titulo so vale contra a
        # numeracao que o produziu, e copiar contra outra poe na peca o
        # texto de outro paragrafo, com a aparencia inteira de estar certo.
        if d["impressao"]:
            from comentar_pdf import conferir_impressao
            nivel, recado = conferir_impressao(
                "IMPRESSAO | " + d["impressao"],
                paragrafos_do_projeto_para_conferir(projeto),
                "A leitura")
            if nivel == "diverge":
                sys.exit("PAREI: " + recado)
        titulo, aviso = copiar_titulo(projeto, d["titulo"])
        if titulo and not d["impressao"]:
            print("AVISO: a leitura nao informou a impressao da numeracao, "
                  "entao ninguem conferiu se P%03d ainda e o titulo."
                  % d["titulo"])
            print()
    if aviso:
        print("SEM O TITULO: %s." % aviso)
        print("A peca sai com o nome do arquivo, e dizendo que e o nome do")
        print("arquivo. O relatorio aponta o titulo em P%03d." % d["titulo"])
        print()

    saida = caminho_pdf or str(arq.with_suffix(".pdf"))
    escrever_um(arq.stem, d, saida, titulo, secoes)
    if secoes:
        print("Secoes do projeto reconhecidas, e grifadas na peca: %d."
              % len(secoes))
    print("%s: notas %s, indicios %s, %d condicao(oes)."
          % (saida, ", ".join(str(d["notas"][i]) for i in (1, 2, 3, 4)),
             NIVEIS_CURTOS[d["nivel"]], len(d["condicoes"])))
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
    f.texto("Leituras de projetos de pesquisa", corpo=18, fonte="tibo",
            espaco_depois=4, justificar=False)
    f.texto("%d projetos. As notas vão de 0 a 10 em quatro dimensões; os "
            "indícios de IA não têm nota e viajam ao lado. A última coluna traz "
            "quantas condições o projeto precisa cumprir para ser apresentável "
            "a uma banca de qualificação. A ordem é alfabética." % len(lidos),
            corpo=10.5, fonte="tiit", cor=COR_FRACA, espaco_depois=16)

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
    f.texto("A coorte, e aqui só se conta", corpo=13.5, fonte="tibo",
            espaco_antes=10, espaco_depois=6, justificar=False)
    conta = ["projetos lidos: %d" % total,
             "sem nenhuma condição a cumprir: %d" % sem_condicao,
             "condições ao todo: %d"
             % sum(len(d["condicoes"]) for d in lidos.values())]
    for i, nome in enumerate(NOMES_LEGIVEIS[:4], 1):
        baixas = sum(1 for d in lidos.values() if d["notas"][i] < 7)
        media = sum(d["notas"][i] for d in lidos.values()) / float(total)
        conta.append("%d. %s: abaixo de 7 em %d de %d, média %.1f"
                     % (i, nome, baixas, total, media))
    for nivel in NIVEIS:
        quantos = sum(1 for d in lidos.values() if d["nivel"] == nivel)
        if quantos:
            conta.append("indícios %s: %d" % (nivel, quantos))
    for c in conta:
        f.texto("- " + c, espaco_depois=3)
    f.texto("Contar é transcrever. Dizer que a turma tem dificuldade com "
            "metodologia seria afirmação nova sobre uma população, e não "
            "sai daqui.", corpo=10.5, fonte="tiit", cor=COR_FRACA,
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
          "Avaliacao. Isso e médio." + chr(10)), 1),
        ("o adjetivo no paragrafo AVALIATIVO nao acusa",
         ("## 1. Problema e justificativa" + chr(10) +
          "O projeto enuncia a pergunta no topico 2." + chr(10) * 2 +
          "A pergunta e vaga e generica, e isso e grave." + chr(10)), 0),
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
        print("  %d. %-26s abaixo de 7 em %d de %d, media %.1f"
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
IMPRESSAO | 172p-a51ff850
1 | problema, objetivos e hipoteses | 0 | 1 | 1 | 5
2 | justificativa | 0 | 1 | 0 | 6
3 | metodologia e teoria | 1 | 0 | 2 | 4
4 | bibliografia | 0 | 0 | 3 | 7
5 | indicios de ia | - | - | - | fracos
CONDICAO | 1 | dizer quem decidiria diferente conforme a resposta | dizer que decisao mudaria
CONDICAO | 2 | fechar a lista de casos antes de comecar
CONDICAO | 3 | dizer que decisao passa a ser tomada de outro modo
FIM"""


def controle():
    """Positivo: cada defeito que o conferidor deveria pegar tem de reprovar."""
    ok = ler_bloco(BOM, "controle")
    assert ok["abaixo"] == [1, 2, 3], ok
    assert ok["nivel"] == "fracos", ok
    assert ok["titulo"] == 2, ok
    assert ok["impressao"] == "172p-a51ff850", ok
    assert len(ok["condicoes"]) == 3, ok
    assert ok["condicoes"][0][0] == 1 and ok["condicoes"][0][1], ok
    assert ok["condicoes"][0][2], "a primeira condicao tem ganho"
    assert ok["condicoes"][1][2] == "", "a segunda nao tem"
    print("  o bloco bom passa                                 ok")

    casos = [
        ("nota fora de 0-10", BOM.replace("| 0 | 3 | 7", "| 0 | 3 | 17")),
        ("nivel invalido", BOM.replace("| fracos", "| razoavel")),
        ("dimensao 5 com nota", BOM.replace("- | fracos", "- | 8")),
        ("sem a linha TITULO",
         BOM.replace("TITULO | P002" + chr(10), "")),
        ("TITULO com o titulo escrito, e nao o localizador",
         BOM.replace("TITULO | P002",
                     "TITULO | A deferencia judicial como limite")),
        ("TITULO sem numero", BOM.replace("TITULO | P002", "TITULO | P")),
        ("IMPRESSAO com forma que nao existe",
         BOM.replace("IMPRESSAO | 172p-a51ff850", "IMPRESSAO | ontem")),
        ("sem nenhuma linha CONDICAO",
         chr(10).join(l for l in BOM.split(chr(10))
                      if not l.startswith("CONDICAO"))),
        ("CONDICAO aponta dimensao que nao existe",
         BOM.replace("CONDICAO | 1 |", "CONDICAO | 8 |")),
        ("CONDICAO que nao diz o que fazer",
         BOM.replace("CONDICAO | 1 | dizer quem decidiria diferente "
                     "conforme a resposta", "CONDICAO | 1 |")),
        ("dimensao com grave e nenhuma condicao saida dela",
         BOM.replace("CONDICAO | 2 | fechar a lista de casos antes de "
                     "comecar" + chr(10), "")),
        ("condicao numa dimensao sem grave nem médio",
         BOM.replace("4 | bibliografia | 0 | 0 | 3 | 7",
                     "4 | bibliografia | 0 | 0 | 3 | 7" + chr(10) +
                     "CONDICAO | 4 | trocar a bibliografia inteira")),
        ("dimensao com o nome velho da dimensao",
         BOM.replace("| justificativa |", "| contribuicoes e impacto |")),
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
    print()

    print("Controle positivo do subtitulo do elemento:")
    casos_sub = [
        ("3", "1. PROBLEMA, OBJETIVOS E HIPÓTESES",
         "3.1 Problema, objetivos e hipóteses"),
        ("3", "2. JUSTIFICATIVA", "3.2 Justificativa"),
        ("3", "Elemento 2. Justificativa", "3.2 Justificativa"),
        ("3", "4. BIBLIOGRAFIA", "3.4 Bibliografia"),
        ("3", "5. INDICIOS DE USO DE IA", "3.5 Indícios de IA"),
        ("3", "4. PERGUNTAS PARA AS QUAIS O AUTOR DEVE ESTAR PREPARADO", None),
        ("3", "2. EMENTA", None),
        (None, "1. PROBLEMA, OBJETIVOS E HIPÓTESES", None),
    ]
    for bloco, titulo, esperado in casos_sub:
        saiu = subtitulo_de_elemento(titulo, bloco)
        marca = "ok" if saiu == esperado else "ERRADO (saiu %r)" % saiu
        print("  %-56s %-30s %s"
              % (titulo[:56], esperado or "nao e elemento", marca))
        assert saiu == esperado, (titulo, saiu, esperado)
    print()
    print()
    print("Controle positivo do titulo de secao:")
    linhas = [
        ("1 DELIMITAÇÃO DO TEMA E JUSTIFICATIVA", "Delimitação"),
        ("3.1. Objetivos.", "Objetivos"),
        ("5. Metodologia de Investigação.", "Metodologia"),
        ("9 ADI 5.501/DF, Rel. Min. Marco Aurélio (fosfoetanolamina).", None),
        ("10 MENEGAT, Fernando; PEREZ, Marcos Augusto. Idem.", None),
        ("O projeto pergunta como e quando decisões judiciais proferidas "
         "em litígios podem provocar a atuação regulatória.", None),
    ]
    for linha, esperado in linhas:
        saiu = secoes_do_projeto([{"texto": linha}])
        certo = (not esperado and not saiu) or (
            esperado and saiu
            and sem_acento(saiu[0]).startswith(sem_acento(esperado)))
        print("  %-58s %-14s %s"
              % (linha[:58], (saiu[0][:14] if saiu else "nao e secao"),
                 "ok" if certo else "ERRADO"))
        assert certo, (linha, saiu)
    print()

    print("Controle positivo do preambulo:")
    T, P = "titulo", "prosa"
    casos = [
        ("com titulo em cima",
         [(T, "RELATORIO"), (P, "a"), (P, "b"), (T, "1. DESCRICAO"), (P, "c")],
         2, "1. DESCRICAO"),
        ("sem titulo em cima",
         [(P, "a"), (P, "b"), (T, "1. DESCRICAO"), (P, "c")],
         2, "1. DESCRICAO"),
        ("dois titulos seguidos",
         [(T, "RELATORIO"), (T, "1. DESCRICAO"), (P, "c")],
         0, "1. DESCRICAO"),
    ]
    for nome, entra, quantos, primeiro in casos:
        pre, resto = partir_preambulo(entra)
        certo = len(pre) == quantos and resto[0][1] == primeiro
        print("  %-24s preambulo de %d, corpo abre em %r  %s"
              % (nome, len(pre), resto[0][1], "ok" if certo else "ERRADO"))
        assert certo, (nome, pre, resto)
    print()

    print("Controle positivo do bloco fora da forma:")
    entra = [("titulo", "4. PERGUNTAS PARA AS QUAIS O AUTOR DEVE ESTAR "
              "PREPARADO"), ("prosa", "Que resultado contrariaria a "
              "hipotese?"), ("titulo", "O QUE A ARGUICAO PODE GANHAR"),
             ("prosa", "Dizer que resultado observavel contrariaria.")]
    sai = sem_ganhos(entra)
    print("  entraram %d blocos, sairam %d" % (len(entra), len(sai)))
    assert len(sai) == 2, sai
    assert sai[0][1].startswith("4. PERGUNTAS"), sai
    print("  o bloco das perguntas fica, o dos ganhos sai              ok")
    print()

    print("Controle positivo de e_titulo:")
    for linha, esperado in [
            ("Elemento 2. Justificativa", True),
            ("2. EMENTA", True),
            ("Elemento nenhum ficou sem parágrafo, e a leitura diz isso.",
             False),
            ("Descrição. A pergunta aparece na Delimitação do tema.", False)]:
        saiu = e_titulo(linha)
        print("  %-58s %-5s %s"
              % (linha[:58], saiu, "ok" if saiu == esperado else "ERRADO"))
        assert saiu == esperado, linha
    print()
    print("Sem os tres que devolvem None, o numero sozinho bastaria, e o")
    print("bloco 4 viraria o elemento 4.")


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
