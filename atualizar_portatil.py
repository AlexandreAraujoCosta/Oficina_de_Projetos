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

from dividir_partes import dividir, conferir

PASTA = Path(__file__).parent

# Cada assistente tem a sua pagina. O Miro herdou o nome antigo do arquivo e
# tambem alimenta o index.html, que e o que o GitHub Pages serve da raiz.
PAGINAS = {
    "modulo_2_planejamento": ("pagina_prompt_portatil.html", "index.html"),
    "revisao_literatura": ("pagina_nelson.html", None),
}
PADRAO_TEXTAREA = re.compile(
    r'(<textarea id="prompt" readonly spellcheck="false">).*?(</textarea>)', re.S
)

# A pagina do Miro entrega o prompt em QUATRO partes, porque colagem longa
# vira anexo e anexo nao governa a conversa (ver dividir_partes.py). A do
# Nelson continua com um campo so, e por isso as duas formas coexistem aqui.
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
    else:
        nova, trocas = PADRAO_TEXTAREA.subn(
            lambda m: m.group(1) + escapar_para_html(prompt) + m.group(2), pagina
        )
        # Nao achar o textarea e erro; achar e o conteudo ja estar em dia nao e.
        if trocas == 0:
            sys.exit(f"ERRO: não achei o <textarea> do prompt em {nome_pagina}.")

    nova = injetar_ferramenta(nova, nome_pagina)

    if nova == pagina:
        print(f"{nome_pagina}: já estava em dia")
    else:
        pagina_arq.write_text(nova, encoding="utf-8")
        print(f"{nome_pagina}: textarea e ferramenta atualizadas")

    print(f"{caminho_md.name}: {len(prompt)} caracteres")

    if nome_indice:
        # O GitHub Pages serve index.html da raiz, então ele precisa ser cópia
        # fiel da página. Sem este passo o site fica servindo a versão anterior,
        # sem nenhum aviso: foi o que aconteceu em 24/8/2026.
        (PASTA / nome_indice).write_text(nova, encoding="utf-8")
        print(f"{nome_indice}: cópia para o GitHub Pages atualizada")
    print("Falta republicar a página como Artifact para o link ficar em dia.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "modulo_2_planejamento")
