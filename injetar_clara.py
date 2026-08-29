"""Injeta o prompt da Clara na pagina da Oficina de Projetos.

O texto do prompt nunca e digitado a mao na pagina: este programa le
prompt_clara.md e o insere no lugar do marcador. E o mesmo principio do
inserir_trechos.py da outra oficina, e pela mesma razao: quem transcreve e o
codigo, entao nao existe palavra trocada.

Uso:  python injetar_clara.py
"""
import html
from pathlib import Path

PAGINA = Path("pagina_oficina_projetos.html")
PROMPT = Path("prompt_clara.md")
MARCADOR = "{{PROMPT_CLARA}}"

def main():
    prompt = PROMPT.read_text(encoding="utf-8").strip()
    pagina = PAGINA.read_text(encoding="utf-8")
    if MARCADOR not in pagina:
        raise SystemExit(
            "O marcador nao esta na pagina. Se ela ja foi gerada, refaca a "
            "partir do modelo em vez de editar o texto do prompt a mao.")
    nova = pagina.replace(MARCADOR, html.escape(prompt, quote=False))
    PAGINA.write_text(nova, encoding="utf-8")
    print(f"Injetados {len(prompt)} caracteres do prompt da Clara.")
    print(f"Pagina com {len(nova)} caracteres.")

if __name__ == "__main__":
    main()
