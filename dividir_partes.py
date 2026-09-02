#!/usr/bin/env python3
"""Divide o prompt portatil em partes colaveis COMO TEXTO num chat.

POR QUE ISTO EXISTE, e o problema nao e o que parecia. Colar o prompt
inteiro num chat gratuito nao produz texto na conversa: acima de um
limiar, o servico converte a colagem em ANEXO. E anexo nao governa a
conversa do mesmo jeito, porque boa parte destas instrucoes sao
proibicoes e postura, que precisam estar na conversa para valer. Foi
relatado por alunos, e depois medido: o Miro estava entrando como anexo
em varios casos.

LIMIAR MEDIDO em 02/09/2026, por colagem real (area de transferencia do
sistema, Ctrl+V, e nao evento sintetico, que nao passa pelo tratador do
aplicativo):

  ChatGPT   50.000 caracteres ainda oferecem o botao "Mostrar no campo
            de texto", que despeja o conteudo no compositor; 55.000 ja
            nao oferecem, e o cartao passa a dizer "demasiado longo
            para ser apresentado".
  claude.ai converte mais cedo (43.862 ja viram "PASTED"), mas ali o
            conteudo colado entra no contexto de qualquer modo, e o
            fluxo em partes funcionou igual.

Por isso o TETO e 50.000, com folga.

O QUE MAIS MUDA, alem de cortar. O prompt tem, na primeira linha, a
frase que diz que o estudante colou o texto inteiro e manda conversar a
partir da resposta seguinte. Deixada na parte 1, ela faz o modelo abrir
a conversa com um quarto das instrucoes. Entao ela e MOVIDA para junto
do bloco final que manda escrever a primeira fala. Nada mais do texto e
alterado.

E CADA PARTE LEVA UM ENVELOPE, que e a unica coisa acrescentada. As
tres primeiras pedem a parte seguinte; a quarta diz que a conversa
ainda nao comecou e que a proxima resposta e a primeira mensagem que o
estudante vai ler. Sem essa ultima frase, medido, o modelo abre com
"Vamos comecar" e nao se apresenta, porque ja falou tres vezes pedindo
partes e nao trata aquilo como primeira mensagem.
"""
from __future__ import annotations

TETO = 50000

ENVELOPES = [
    "[PARTE 1 DE 4 DAS INSTRUÇÕES. Elas não cabem numa mensagem só, então "
    "vêm em quatro. NÃO COMECE A CONVERSA E NÃO COMENTE O CONTEÚDO: responda "
    "apenas pedindo que eu cole a parte 2.]",

    "[PARTE 2 DE 4, continuando exatamente de onde a parte 1 parou. Ainda não "
    "comece: responda apenas pedindo que eu cole a parte 3.]",

    "[PARTE 3 DE 4, continuando de onde a parte 2 parou. Ainda não comece: "
    "responda apenas pedindo que eu cole a parte 4, que é a última.]",

    "[PARTE 4 DE 4, a última, continuando de onde a parte 3 parou. As quatro "
    "partes juntas são o texto único a que elas se referem. A CONVERSA COM O "
    "ESTUDANTE AINDA NÃO COMEÇOU: as três mensagens anteriores foram só a "
    "entrega das instruções, e nada do que você respondeu até aqui faz parte "
    "da conversa. A sua próxima resposta é a PRIMEIRA MENSAGEM QUE O ESTUDANTE "
    "VAI LER, e por isso precisa cumprir TODOS os critérios de abertura, "
    "inclusive apresentar-se. Escreva-a agora.]",
]

MARCA_ABERTURA = "colou este texto inteiro"
ANCORA_PRIMEIRA_FALA = "Escreva agora a sua primeira fala"


def dividir(texto, n=4, teto=TETO):
    """Devolve a lista das n partes, cada uma com o seu envelope.

    Levanta AssertionError se alguma parte estourar o teto, se o corte
    nao achar quebra de paragrafo, ou se a recomposicao nao reproduzir o
    original: e melhor falhar na geracao do que publicar parte que o
    chat vai converter em anexo.
    """
    assert n == len(ENVELOPES), "ha %d envelopes para %d partes" % (len(ENVELOPES), n)

    fim = texto.find("\n\n")
    assert fim > 0, "nao achei o fim do primeiro paragrafo"
    abertura = texto[:fim]
    assert MARCA_ABERTURA in abertura, (
        "o primeiro paragrafo mudou e nao e mais o que manda conversar: %r"
        % abertura[:80])

    corpo = texto[fim + 2:]
    assert corpo.count(ANCORA_PRIMEIRA_FALA) == 1, (
        "a ancora da primeira fala aparece %d vezes"
        % corpo.count(ANCORA_PRIMEIRA_FALA))
    i = corpo.find(ANCORA_PRIMEIRA_FALA)
    corpo = corpo[:i] + abertura + "\n\n" + corpo[i:]

    alvo = len(corpo) // n
    cortes, pos = [], 0
    for k in range(n - 1):
        c = corpo.find("\n\n", pos + alvo)
        assert c > 0, "nao achei quebra de paragrafo para o corte %d" % (k + 1)
        cortes.append(c + 2)
        pos = c + 2

    pedacos, ant = [], 0
    for c in cortes:
        pedacos.append(corpo[ant:c])
        ant = c
    pedacos.append(corpo[ant:])
    assert "".join(pedacos) == corpo, "a divisao perdeu ou duplicou texto"

    partes = [env + "\n\n" + ped for env, ped in zip(ENVELOPES, pedacos)]
    for k, p in enumerate(partes, 1):
        assert len(p) <= teto, (
            "a parte %d tem %d caracteres e o teto e %d: o chat converteria em "
            "anexo" % (k, len(p), teto))
    return partes


def conferir(texto, partes):
    """Controle: as partes, sem envelope e com a abertura devolvida ao
    lugar de origem, reproduzem o texto original."""
    sem_env = []
    for env, p in zip(ENVELOPES, partes):
        assert p.startswith(env + "\n\n"), "parte sem o envelope esperado"
        sem_env.append(p[len(env) + 2:])
    junto = "".join(sem_env)
    fim = texto.find("\n\n")
    abertura = texto[:fim]
    j = junto.find(abertura)
    if j < 0:
        return False
    junto = junto[:j] + junto[j + len(abertura) + 2:]
    return abertura + "\n\n" + junto == texto


if __name__ == "__main__":
    import io, sys
    from pathlib import Path
    fonte = Path(__file__).parent / "prompt_portatil_modulo_2_planejamento.md"
    t = io.open(fonte, encoding="utf-8").read()
    ps = dividir(t)
    for k, p in enumerate(ps, 1):
        print("parte %d  %7d caracteres   folga %6d" % (k, len(p), TETO - len(p)))
    ok = conferir(t, ps)
    print("controle (as partes reproduzem o original):", "OK" if ok else "FALHOU")
    if not ok:
        sys.exit(1)
