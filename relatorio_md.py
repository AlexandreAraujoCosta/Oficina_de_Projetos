#!/usr/bin/env python3
"""
Monta, em .md, o relatorio que o assistente escreveu sobre um projeto.

    python relatorio_md.py projeto.docx --numerar
    python relatorio_md.py projeto.pdf  --relatorio rel.txt -o relatorio.md
    python relatorio_md.py projeto.md   --provar

POR QUE .MD, E NAO PDF. O relatorio do Miro e material de trabalho: quem
o recebe copia item, cola numa conversa, edita, responde. PDF e documento
fechado, e fecha justamente o que ali precisa ficar aberto. O PDF vale
para o outro caso, que e a leitura de banca da Selma: ali o relatorio e
peca que o processo recebe pronta, e para isso ha o relatorio_pdf.py.

DE ONDE ELE LE O PROJETO: .docx, .md e .pdf. Os dois primeiros sao os
formatos com que o Miro trabalha, e o terceiro entra so como fonte de
leitura, nunca de escrita: o PDF do autor nao e tocado.

E O TRECHO CITADO E COPIADO POR ESTE PROGRAMA, nunca digitado pelo
assistente. O assistente escreve LOCALIZADOR E COMENTARIO; o programa
abre o projeto, acha o paragrafo daquele numero e copia o texto. O
relatorio EXIBE o trecho, e quem le confere abrindo o projeto: uma
palavra trocada na citacao descaracteriza a conferencia.

O FLUXO TEM DOIS PASSOS.

  1. --numerar lista os paragrafos com [P001], [P002]. O autor cola a
     lista na conversa, e a partir dai o assistente aponta sem
     transcrever.

  2. O assistente escreve o relatorio num arquivo de texto:

         # Titulo do relatorio
         ## Problema e justificativa
         Um paragrafo de prosa, que sai como prosa.
         P016 > A frase que declara ... esta redigida como conclusao
           fechada; reescrever como expectativa de trabalho.

     Linha comecada por dois espacos continua o item anterior.
     Localizador que o documento nao tem faz o programa parar e dizer
     qual e, em vez de escolher o paragrafo mais parecido.

E ELE CONFERE O QUE PROMETE. Antes de gravar, compara palavra a palavra
cada trecho que vai para o relatorio com o paragrafo de onde ele saiu, e
depois rele o arquivo gravado e confere de novo, porque o que interessa e
o que o leitor vai ver. --provar mostra o conferidor reprovando uma
citacao alterada de proposito.
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from relatorio_pdf import ler_relatorio, cortar, PALAVRAS_DO_TRECHO


def paragrafos_do_projeto(caminho):
    """Devolve [{"texto":..., "pagina": n ou None}] conforme o formato."""
    suf = caminho.suffix.lower()
    if suf == ".pdf":
        from comentar_pdf import ler
        return ler(str(caminho))
    if suf == ".docx":
        from comentar_projeto import texto_do_docx
        return [{"texto": p.strip(), "pagina": None}
                for p in texto_do_docx(caminho) if p.strip()]
    if suf in (".md", ".markdown", ".txt"):
        from comentar_projeto import texto_do_md
        return [{"texto": " ".join(p.split()), "pagina": None}
                for p in texto_do_md(caminho) if p.strip()]
    sys.exit("Formato nao reconhecido: %s. Uso .docx, .md ou .pdf." % suf)


def onde(p):
    return "" if p["pagina"] is None else ", página %d do projeto" % (p["pagina"] + 1)


def montar(pecas, paragrafos, nome_projeto):
    linhas, citados = [], []

    if not any(t == "titulo" for t, _ in pecas):
        linhas.append("# Relatório sobre " + nome_projeto)
        linhas.append("")

    abertura = ("*Os trechos citados foram copiados do próprio projeto por "
                "programa. O número entre colchetes é o do parágrafo na "
                "numeração que acompanha este relatório.*")
    posto = False

    for tipo, dado in pecas:
        if tipo == "titulo":
            linhas += ["# " + dado, ""]
            if not posto:
                linhas += [abertura, ""]
                posto = True
        elif tipo == "secao":
            if not posto:
                linhas += [abertura, ""]
                posto = True
            linhas += ["## " + dado, ""]
        elif tipo == "prosa":
            if not posto:
                linhas += [abertura, ""]
                posto = True
            linhas += [dado, ""]
        else:
            if not posto:
                linhas += [abertura, ""]
                posto = True
            n, comentarios = dado
            p = paragrafos[n - 1]
            trecho, cortado = cortar(p["texto"])
            citados.append((n, trecho, cortado))
            linhas.append("**[P%03d]**%s" % (n, onde(p)))
            linhas.append("")
            # O trecho vai em citacao de bloco, que e o que o markdown tem
            # para dizer "isto nao e meu". Numa linha so: quebra dentro da
            # citacao vira paragrafo novo em alguns leitores.
            linhas += ["> " + trecho, ""]
            for k, c in enumerate(comentarios):
                linhas.append(("%d. %s" % (k + 1, c)) if len(comentarios) > 1
                              else c)
                linhas.append("")

    return "\n".join(linhas).rstrip() + "\n", citados


# ------------------------------------------------------------- conferidor

def sem_marcador(trecho):
    """Tira o marcador de corte, e SO ele.

    rstrip(". ") tirava qualquer ponto final, e citacao curta termina em
    ponto como toda frase termina: ela perdia o ponto, deixava de bater
    com a origem, e o programa recusava a gravar um relatorio correto.
    """
    return trecho[:-4] if trecho.endswith(" ...") else trecho


def conferir_citacoes(citados, paragrafos, escrito):
    """Compara, palavra a palavra, cada citacao com o paragrafo de onde
    saiu, e confere que ela esta mesmo no texto que se vai gravar."""
    palavras_do_arquivo = escrito.split()
    for n, trecho, cortado in citados:
        origem = paragrafos[n - 1]["texto"].split()
        vindo = sem_marcador(trecho).split()
        if vindo != origem[:len(vindo)]:
            for i, (a, b) in enumerate(zip(vindo, origem)):
                if a != b:
                    return ("P%03d: a citação diz %r onde o projeto diz %r "
                            "(palavra %d)" % (n, a, b, i + 1))
            return "P%03d: a citação tem tamanho diferente do parágrafo" % n
        if not cortado and len(vindo) != len(origem):
            return ("P%03d: a citação não foi cortada e tem %d palavras "
                    "contra %d do parágrafo" % (n, len(vindo), len(origem)))
        if vindo and vindo[0] not in palavras_do_arquivo:
            return "P%03d: a citação não aparece no relatório gravado" % n
    return None


def provar(caminho):
    """Controle positivo. Sem ele o silencio do conferidor nao informa
    nada: conferidor quebrado e conferidor satisfeito tem a mesma cara."""
    paragrafos = paragrafos_do_projeto(Path(caminho))
    n = next((i for i, p in enumerate(paragrafos, 1)
              if len(p["texto"].split()) > 25), 1)
    trecho, cortado = cortar(paragrafos[n - 1]["texto"])
    arquivo = "> " + trecho

    trocado = trecho.split()
    trocado[3] = "PALAVRATROCADA"
    faltando = " ".join(trecho.split()[:-3])

    # O CASO CURTO, que e o que estava faltando: paragrafo que nao foi
    # cortado e termina em ponto. Era ele que o conferidor recusava.
    curto = next((p["texto"] for p in paragrafos
                  if 8 < len(p["texto"].split()) <= PALAVRAS_DO_TRECHO
                  and p["texto"].rstrip().endswith(".")), None)
    n_curto = next((i for i, p in enumerate(paragrafos, 1)
                    if p["texto"] == curto), n)

    casos = [
        ("uma citação curta, que termina em ponto",
         conferir_citacoes([(n_curto, curto, False)], paragrafos,
                           "> " + curto) if curto else None,
         True),
        ("a citação como o projeto a tem",
         conferir_citacoes([(n, trecho, cortado)], paragrafos, arquivo), True),
        ("uma palavra trocada na citação",
         conferir_citacoes([(n, " ".join(trocado), cortado)], paragrafos,
                           arquivo), False),
        ("a citação encurtada sem reticências",
         conferir_citacoes([(n, faltando, False)], paragrafos, arquivo), False),
        ("a citação fora do arquivo gravado",
         conferir_citacoes([(n, trecho, cortado)], paragrafos, "outra coisa"),
         False),
    ]
    print("Controle positivo do conferidor de citação:")
    ok = True
    for nome, r, esperado in casos:
        passou = r is None
        certo = passou == esperado
        ok = ok and certo
        print("  %-40s %-9s %s" % (nome, "passou" if passou else "reprovou",
                                   "ok" if certo else "DIVERGIU"))
    for nome, r, esperado in casos:
        if r and not esperado:
            print()
            print("  o que ele disse: " + r)
            break
    print()
    print("O conferidor separa os casos." if ok
          else "O CONFERIDOR NÃO SEPARA OS CASOS. Não use o resultado.")
    return 0 if ok else 1


# ------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description=__doc__.split("\n")[1],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto", help="o projeto, em .docx, .md ou .pdf")
    ap.add_argument("--numerar", action="store_true",
                    help="lista os parágrafos com [P001]")
    ap.add_argument("--relatorio", help="o arquivo que o assistente escreveu")
    ap.add_argument("-o", "--saida", help="o relatório em .md")
    ap.add_argument("--provar", action="store_true",
                    help="mostra o conferidor reprovando de propósito")
    a = ap.parse_args()

    entrada = Path(a.projeto)
    if not entrada.is_file():
        sys.exit("Não achei %s." % entrada)

    if a.provar:
        return provar(str(entrada))

    paragrafos = paragrafos_do_projeto(entrada)

    if a.numerar:
        for i, p in enumerate(paragrafos, 1):
            print("[P%03d] %s" % (i, p["texto"]))
            print()
        print("%d parágrafos." % len(paragrafos), file=sys.stderr)
        from comentar_pdf import impressao_digital
        print()
        print("IMPRESSAO | %s" % impressao_digital(paragrafos))
        return 0

    if not a.relatorio:
        sys.exit("Sem --numerar e sem --relatorio não há o que fazer. "
                 "Comece por --numerar.")

    bruto_do_relatorio = Path(a.relatorio).read_text(encoding="utf-8")
    from comentar_pdf import conferir_impressao
    nivel, recado = conferir_impressao(bruto_do_relatorio, paragrafos)
    if nivel == "diverge":
        sys.exit("PAREI: " + recado)
    if nivel == "sem":
        print("AVISO: " + recado)
        print()

    pecas = ler_relatorio(bruto_do_relatorio)
    itens = [d[0] for t, d in pecas if t == "item"]
    if not itens:
        sys.exit("Nenhum item com localizador em %s. Eles têm a forma "
                 "P004 > comentário." % a.relatorio)

    fora = sorted({n for n in itens if not 1 <= n <= len(paragrafos)})
    if fora:
        sys.exit("O relatório aponta parágrafos que o projeto não tem: %s.\n"
                 "Ele vai de P001 a P%03d. Numere-o com --numerar e peça ao "
                 "assistente que refaça com esses números. Eu não escolho o "
                 "parágrafo mais parecido."
                 % (", ".join("P%03d" % n for n in fora), len(paragrafos)))

    saida = Path(a.saida) if a.saida else entrada.with_name(
        entrada.stem + "-relatorio.md")
    texto, citados = montar(pecas, paragrafos, entrada.stem)

    defeito = conferir_citacoes(citados, paragrafos, texto)
    if defeito:
        sys.exit("PAREI: %s.\nO relatório teria exibido como citação um texto "
                 "que o projeto não tem. Nada foi produzido." % defeito)

    saida.write_text(texto, encoding="utf-8")

    # E de novo, no que ficou em disco.
    defeito = conferir_citacoes(citados, paragrafos,
                                saida.read_text(encoding="utf-8"))
    if defeito:
        saida.unlink(missing_ok=True)
        sys.exit("PAREI depois de gravar: %s. O arquivo foi apagado." % defeito)

    quantos = sum(len(d[1]) for t, d in pecas if t == "item")
    print("%s: %d comentários em %d parágrafos." % (saida.name, quantos,
                                                    len(itens)))
    print("Os %d trechos citados foram copiados do projeto e conferidos "
          "palavra a palavra, antes e depois de gravar. Use --provar para ver "
          "o conferidor reprovar de propósito." % len(citados))
    return 0


if __name__ == "__main__":
    sys.exit(main())
