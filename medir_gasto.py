# -*- coding: utf-8 -*-
"""Quanto custou uma leitura: minutos e tokens, medidos e nao estimados.

PARA QUE SERVE. A peca abre dizendo quem a escreveu, e pode dizer tambem
o que a leitura consumiu. Esse numero a assistente nao sabe: modelo nao
tem acesso ao proprio relogio nem ao proprio contador, e um prompt que
pedisse a frase receberia numero inventado. Quem sabe e o programa que
rodou a leitura, e e dele que o numero sai.

DE ONDE SAI. No modo agente, cada leitura roda como subagente, e a
sessao registra, no fim, quanto durou e quantos tokens gastou. Este
modulo le esse registro pelo identificador da tarefa.

O QUE O NUMERO COBRE, e isso vai declarado junto: a execucao inteira do
subagente, do primeiro turno ao ultimo, incluindo ler o prompt, ler o
projeto, as buscas e escrever o relatorio.

NO MODO CHAT NAO HA MEDIDA. Quem cola o prompt num chat nao tem esse
registro, e entao a frase simplesmente nao entra na peca. Peca sem a
frase e peca sem a medida; peca com a frase tem numero medido.

    python medir_gasto.py <id-da-tarefa> [transcript.jsonl]
    python medir_gasto.py --controle
"""
import glob
import io
import os
import re
import sys

SESSOES = os.path.join(os.path.expanduser("~"), ".claude", "projects")

RE_ID = re.compile(r"<task-id>([0-9a-f]+)</task-id>")
RE_TOKENS = re.compile(r"<subagent_tokens>(\d+)</subagent_tokens>")
RE_MS = re.compile(r"<duration_ms>(\d+)</duration_ms>")


def transcricoes():
    """Os arquivos de sessao, do mais recente para o mais antigo."""
    achados = glob.glob(os.path.join(SESSOES, "*", "*.jsonl"))
    return sorted(achados, key=os.path.getmtime, reverse=True)


def medir(tarefa, caminho=None):
    """(minutos, tokens) da tarefa, ou None se ela nao estiver registrada.

    A BUSCA E POR LINHA E POR SUBSTRING ANTES DA EXPRESSAO: o arquivo
    passa de cem megabytes, e casar expressao em cada linha custa caro
    sem necessidade.

    A MESMA TAREFA APARECE MAIS DE UMA VEZ, porque a notificacao se
    repete. As repeticoes trazem o mesmo par, e fica a ultima.
    """
    caminhos = [caminho] if caminho else transcricoes()
    for c in caminhos:
        achado = None
        with io.open(c, encoding="utf-8", errors="replace") as f:
            for linha in f:
                if tarefa not in linha or "subagent_tokens" not in linha:
                    continue
                # o par vem no mesmo bloco de notificacao que traz o id
                for bloco in linha.split("<task-id>"):
                    if not bloco.startswith(tarefa):
                        continue
                    t = RE_TOKENS.search(bloco)
                    ms = RE_MS.search(bloco)
                    if t and ms:
                        achado = (int(ms.group(1)) / 60000.0, int(t.group(1)))
        if achado:
            return achado
    return None


def por_extenso(minutos, tokens):
    """A frase que entra na peca, com o numero no formato daqui."""
    m = int(round(minutos))
    m = max(m, 1)
    mil = "{:,}".format(tokens).replace(",", ".")
    return "em leitura que consumiu %d minuto%s e %s tokens" % (
        m, "" if m == 1 else "s", mil)


def controle():
    """Duas tarefas cujo par eu ja conheco, e uma que nao existe.

    SEM ISTO O SILENCIO NAO INFORMA: uma funcao que devolve None para
    tudo passaria como "tarefa nao registrada" em qualquer chamada.
    """
    print("CONTROLE POSITIVO")
    casos = [
        ("ab5857cbf4c03ced6", 527641, 142595),
        ("adf2f2bbb54bdcc77", 751661, 162830),
    ]
    bom = True
    for tarefa, ms, tokens in casos:
        r = medir(tarefa)
        esperado = (ms / 60000.0, tokens)
        ok = r is not None and abs(r[0] - esperado[0]) < 0.01 and r[1] == tokens
        bom = bom and ok
        print("  %-20s %s  %s" % (
            tarefa,
            "%.1f min, %d tokens" % r if r else "NAO ACHOU",
            "ok" if ok else "ERRADO, esperava %.1f min e %d" % esperado))
    inexistente = medir("0000000000000000")
    print("  %-20s %s  %s" % ("tarefa inexistente",
                              inexistente or "None",
                              "ok" if inexistente is None else "ERRADO"))
    bom = bom and inexistente is None
    print()
    print("A FRASE, com os numeros do primeiro caso:")
    print("  " + por_extenso(*medir(casos[0][0])))
    print()
    print("passa" if bom else "REPROVA")
    return 0 if bom else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--controle":
        sys.exit(controle())
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    r = medir(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    if r is None:
        sys.exit("tarefa nao registrada nas sessoes: %s" % sys.argv[1])
    print("%.2f minutos, %d tokens" % r)
    print(por_extenso(*r))
    print()
    print("na peca:  python selma_lote.py um relatorio.md saida.pdf "
          "--minutos %d --tokens %d" % (int(round(r[0])), r[1]))
