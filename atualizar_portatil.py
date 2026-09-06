#!/usr/bin/env python3
"""
Regenera os dois artefatos derivados do prompt, numa operação só:

  1. prompt_portatil_<atividade>.md, o texto que o aluno cola num chat de IA
     gratuito (gerado por gerar_prompt_portatil.py);
  2. o <textarea> dentro de pagina_prompt_portatil.html, a página que
     publicamos como Artifact com o botão de copiar.

Nenhum dos dois deve ser editado à mão: os dois saem de core.py e de
contextos/<atividade>.py. Depois de rodar este script, republique a página
como Artifact para que o link fique em dia.

Uso:
  python atualizar_portatil.py [nome_do_modulo_de_contexto]
"""

import re
import sys
from pathlib import Path

from gerar_prompt_portatil import gerar

from dividir_partes import dividir, conferir, folga

PASTA = Path(__file__).parent

# Cada assistente tem a sua pagina. O Miro herdou o nome antigo do arquivo e
# tambem alimenta o index.html, que e o que o GitHub Pages serve da raiz.
PAGINAS = {
    "modulo_2_planejamento": ("pagina_prompt_portatil.html", "index.html"),
}
PADRAO_TEXTAREA = re.compile(
    r'(<textarea id="prompt" readonly spellcheck="false">).*?(</textarea>)', re.S
)

# A pagina do Miro entrega o prompt em QUATRO partes, porque colagem longa
# vira anexo e anexo nao governa a conversa (ver dividir_partes.py). A forma de campo unico
# continua reconhecida, para paginas que ainda a usem.
def padrao_parte(k):
    return re.compile(
        r'(<textarea id="prompt-%d" readonly spellcheck="false">).*?(</textarea>)'
        % k,
        re.S,
    )

# A ferramenta que poe as sugestoes dentro do projeto do aluno mora num
# arquivo so e entra nas duas paginas por injecao, entre marcas. Assim ela
# nao vira duas copias que divergem na primeira correcao.
FERRAMENTA = PASTA / "ferramenta_comentar.html"
PADRAO_FERRAMENTA = re.compile(
    r"<!-- FERRAMENTA:INICIO -->.*?<!-- FERRAMENTA:FIM -->", re.S
)
ANCORA_FERRAMENTA = '  <div class="copybar">'
MARCA_CHAT = 'id="guia-chat"'
MARCA_AGENTE = 'id="guia-agente"'


def injetar_ferramenta(pagina, nome_pagina):
    """Substitui entre as marcas; na primeira vez, insere antes da copybar."""
    if not FERRAMENTA.is_file():
        sys.exit(f"ERRO: nao achei {FERRAMENTA.name}.")
    bloco = FERRAMENTA.read_text(encoding="utf-8").strip()

    if PADRAO_FERRAMENTA.search(pagina):
        return PADRAO_FERRAMENTA.sub(lambda _: bloco, pagina, count=1)

    i = pagina.find(ANCORA_FERRAMENTA)
    if i < 0:
        sys.exit(f"ERRO: nao achei onde por a ferramenta em {nome_pagina}.")
    return pagina[:i] + bloco + "\n\n" + pagina[i:]


def onde_esta_a_ferramenta(pagina):
    """Devolve None se a ferramenta esta dentro do modo chat, e o defeito
    em palavras se nao esta.

    POR QUE ISTO EXISTE. A ferramenta e do MODO CHAT: no agente, quem
    escreve o arquivo e o proprio agente. Ela estava FORA das duas guias,
    e por isso aparecia sempre, encabecando o modo agente. Ficou visivel
    para quem usa a pagina, e nao para quem a gera, e por isso a posicao
    passa a ser conferida aqui.

    E A CONTA COMECA NA ABERTURA DA TAG, e nao no id: comecando no id, a
    abertura da propria guia nao entra na conta, a profundidade sai uma
    unidade baixa, e os dois casos do controle dao a mesma resposta.
    """
    i = pagina.find(MARCA_CHAT)
    if i < 0:
        return None                        # pagina sem os dois modos
    a = pagina.rfind("<div", 0, i)
    f = pagina.find("<!-- FERRAMENTA:INICIO -->")
    b = pagina.find(MARCA_AGENTE)
    if f < 0:
        return "nao achei a ferramenta"
    if not (0 <= a < f < b):
        return "a ferramenta nao esta entre a abertura do chat e a do agente"
    prof = 0
    for m in re.finditer(r"<div\b|</div>|<!-- FERRAMENTA:INICIO -->", pagina[a:]):
        if m.group(0) == "<!-- FERRAMENTA:INICIO -->":
            if prof >= 1:
                return None
            return "a ferramenta esta fora da guia do chat, e aparece nos dois modos"
        prof += 1 if m.group(0).startswith("<div") else -1
    return "nao achei a ferramenta"


def provar_a_posicao(pagina):
    """Controle positivo. Conferidor que nunca reprovou nada nao informa
    nada quando fica em silencio."""
    casos = [
        ("a pagina como esta", pagina, True),
        ("um </div> a mais antes dela",
         pagina.replace("<!-- FERRAMENTA:INICIO -->",
                        "</div>" + chr(10) + "<!-- FERRAMENTA:INICIO -->", 1), False),
        ("a ferramenta depois do agente",
         pagina.replace("<!-- FERRAMENTA:INICIO -->", "", 1)
         + "<!-- FERRAMENTA:INICIO -->", False),
    ]
    ruins = []
    for nome, texto, esperado in casos:
        if (onde_esta_a_ferramenta(texto) is None) != esperado:
            ruins.append(nome)
    return ruins


def escapar_para_html(texto):
    """Converte tudo que não é ASCII em referência numérica. Evita depender da
    codificação com que a página venha a ser lida ou reescrita depois."""
    saida = []
    for ch in texto:
        if ord(ch) > 127:
            saida.append(f"&#{ord(ch)};")
        elif ch == "&":
            saida.append("&amp;")
        elif ch == "<":
            saida.append("&lt;")
        elif ch == ">":
            saida.append("&gt;")
        elif ch == '"':
            saida.append("&quot;")
        else:
            saida.append(ch)
    return "".join(saida)


def main(nome_contexto="modulo_2_planejamento"):
    prompt = gerar(nome_contexto)

    caminho_md = PASTA / f"prompt_portatil_{nome_contexto}.md"
    caminho_md.write_text(prompt, encoding="utf-8")

    if nome_contexto not in PAGINAS:
        sys.exit(f"ERRO: nao sei qual pagina corresponde a {nome_contexto}.")
    nome_pagina, nome_indice = PAGINAS[nome_contexto]
    pagina_arq = PASTA / nome_pagina

    pagina = pagina_arq.read_text(encoding="utf-8")

    if 'id="prompt-1"' in pagina:
        # pagina em partes: divide, confere e injeta uma a uma
        partes = dividir(prompt)
        if not conferir(prompt, partes):
            sys.exit("ERRO: as partes nao reproduzem o prompt original.")
        nova = pagina
        for k, parte in enumerate(partes, 1):
            nova, trocas = padrao_parte(k).subn(
                lambda m, p=parte: m.group(1) + escapar_para_html(p) + m.group(2),
                nova,
            )
            if trocas == 0:
                sys.exit(f"ERRO: não achei o <textarea> da parte {k} em {nome_pagina}.")
        print(
            "partes: "
            + ", ".join("%d=%d" % (k, len(p)) for k, p in enumerate(partes, 1))
        )
        # O AVISO DE FOLGA EXISTIA E NINGUEM O CHAMAVA: em 6/9/2026 a maior
        # parte chegou a 1.473 caracteres do teto e o programa que sabia
        # disso nao disse nada. Quem roda na pratica e este arquivo.
        aviso = folga(partes)
        if aviso:
            print("ATENCAO: " + aviso)

        # A QUINTA PARTE NAO E UMA DAS QUATRO: ela nao entra na divisao,
        # porque nao se cola no comeco. E gerada a parte e injetada no
        # campo proprio, se a pagina tiver um.
        if 'id="prompt-5"' in nova:
            from miro_v import gerar as gerar_v
            texto_v = gerar_v()
            (PASTA / "prompt_miro_v.md").write_text(texto_v, encoding="utf-8")
            nova, trocas = padrao_parte(5).subn(
                lambda m: m.group(1) + escapar_para_html(texto_v) + m.group(2),
                nova,
            )
            if trocas == 0:
                sys.exit("ERRO: nao achei o <textarea> da parte 5.")
            print("miro V: %d caracteres" % len(texto_v))
    else:
        nova, trocas = PADRAO_TEXTAREA.subn(
            lambda m: m.group(1) + escapar_para_html(prompt) + m.group(2), pagina
        )
        # Nao achar o textarea e erro; achar e o conteudo ja estar em dia nao e.
        if trocas == 0:
            sys.exit(f"ERRO: não achei o <textarea> do prompt em {nome_pagina}.")

    nova = injetar_ferramenta(nova, nome_pagina)
    ruins = provar_a_posicao(nova)
    if ruins:
        sys.exit("ERRO: o conferidor de posicao da ferramenta nao separa "
                 "os casos (%s). Nao confie no silencio dele."
                 % ", ".join(ruins))
    defeito = onde_esta_a_ferramenta(nova)
    if defeito:
        sys.exit("ERRO em %s: %s." % (nome_pagina, defeito))

    if nova == pagina:
        print(f"{nome_pagina}: já estava em dia")
    else:
        pagina_arq.write_text(nova, encoding="utf-8")
        print(f"{nome_pagina}: textarea e ferramenta atualizadas")

    print(f"{caminho_md.name}: {len(prompt)} caracteres")

    # A VARIANTE COMPACTA SAI DAQUI TAMBEM, e nao a mao. Ela foi gerada
    # uma vez em 29/8/2026 e nunca mais: quando o Nelson foi excluido, ela
    # ficou sendo o unico arquivo do repositorio que ainda mandava o aluno
    # para um assistente que nao existe mais, com link e tudo. Arquivo
    # gerado que nao entra na rotina de geracao envelhece em silencio.
    # O nome dela nao se deriva do contexto: o arquivo em disco chama-se
    # prompt_portatil_modulo_2_compacto.md, sem "_planejamento". Montar o
    # nome pelo contexto achava arquivo nenhum, e o passo passava em
    # silencio, que e o mesmo silencio que deixou o arquivo envelhecer.
    compactos = sorted(PASTA.glob("prompt_portatil_*_compacto.md"))
    for caminho_compacto in compactos:
        compacto = gerar(nome_contexto, compacto=True)
        caminho_compacto.write_text(compacto, encoding="utf-8")
        print(f"{caminho_compacto.name}: {len(compacto)} caracteres "
              f"({100 - round(100 * len(compacto) / len(prompt))}% menor)")

    if nome_indice:
        # O GitHub Pages serve index.html da raiz, então ele precisa ser cópia
        # fiel da página. Sem este passo o site fica servindo a versão anterior,
        # sem nenhum aviso: foi o que aconteceu em 24/8/2026.
        (PASTA / nome_indice).write_text(nova, encoding="utf-8")
        print(f"{nome_indice}: cópia para o GitHub Pages atualizada")
    print("Falta republicar a página como Artifact para o link ficar em dia.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "modulo_2_planejamento")
