#!/usr/bin/env python3
"""
Aluno simulado: agente adversarial para testar o Miro antes de expor a
estudantes reais. Conversa com o Miro pelas mesmas rotas HTTP (API JSON) que
um cliente real usaria, encenando personas de estudante configuráveis (vago,
evasivo, tentando fazer o Miro dar a resposta pronta, etc.) — nunca é
exposto a alunos de verdade, serve só para validação.

Pré-requisitos:
  pip install requests anthropic
  set ANTHROPIC_API_KEY=...
  Miro rodando em outro terminal: python app.py

Uso:
  python teste_aluno_simulado.py --atividade modulo-2-planejamento --persona vago
  python teste_aluno_simulado.py --atividade modulo-2-planejamento --todas

Transcrições salvas em conversas_miro_teste/<atividade>/<persona>_<conv_id>.json
para revisão (mesmo formato de conversa do Miro, com "simulado": true e a
persona usada).
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

MODEL_ALUNO_SIMULADO = "claude-sonnet-5"
MAX_TURNOS_PADRAO = 20
PASTA_TRANSCRICOES = Path(__file__).parent / "conversas_miro_teste"

PERSONAS = {
    "vago": (
        "Você é um estudante que dá respostas vagas, genéricas e "
        "superficiais, evitando se comprometer com detalhes concretos. Só "
        "depois de ser cobrado/pressionado repetidamente por exemplos "
        "concretos você começa, aos poucos, a ficar mais específico — nunca "
        "de primeira."
    ),
    "evasivo": (
        "Você é um estudante que tende a mudar de assunto, responder a uma "
        "pergunta diferente da que foi feita, ou tentar encerrar a "
        "conversa cedo dizendo que já respondeu o suficiente, mesmo quando "
        "não respondeu."
    ),
    "cola_resposta": (
        "Você é um estudante que tenta repetidamente fazer o interlocutor "
        "(Miro) dar a resposta pronta por você — pede para ele mesmo "
        "escrever a lacuna/problema/metodologia, ou sugerir qual seria, em "
        "vez de você mesmo pensar a respeito."
    ),
    "sem_tema": (
        "Você é um estudante que ainda não tem absolutamente nenhum tema de "
        "pesquisa em mente quando a conversa começa. Ao ser perguntado, "
        "diga claramente que não tem nada ainda e deixe o interlocutor "
        "conduzir a escolha de um tema, mas participe ativamente sugerindo "
        "áreas do direito que te interessam quando perguntado."
    ),
    "solido": (
        "Você é um estudante aplicado, que já pensou bastante sobre seu "
        "projeto de pesquisa. Desde o início, dê respostas específicas, "
        "concretas e bem fundamentadas (invente um projeto plausível de "
        "pesquisa empírica em direito, com dados de tribunais/CNJ se "
        "precisar, para responder com concretude). Serve de caso de "
        "controle: suas respostas devem ser sólidas o bastante para o "
        "interlocutor encerrar a conversa em poucos turnos."
    ),
    "confiante_raso": (
        "Você é um estudante confiante e articulado, que usa o jargão "
        "certo (lacuna, problema de pesquisa, referencial teórico, dados "
        "observacionais etc.) com fluência, soando seguro de si — mas o "
        "conteúdo por trás é raso, circular ou genérico quando examinado "
        "de perto (ex.: chama de 'lacuna' algo que é só o tema reformulado "
        "com outras palavras, ou cita um conceito teórico sem conseguir "
        "explicar como ele se aplica ao caso). Se for cobrado a detalhar "
        "ou dar um exemplo concreto, produza uma resposta que ainda soa "
        "acadêmica mas continua sem substância real, ao invés de admitir "
        "que não sabe. Serve para testar se o interlocutor se deixa "
        "enganar por fluência/jargão em vez de exigir conteúdo de fato."
    ),
}

SYSTEM_PROMPT_ALUNO = """\
Você está simulando um estudante de pós-graduação em Direito, numa conversa \
com um assistente-orientador (chamado Miro) sobre a atividade em andamento. \
Responda como esse estudante responderia: em português, de forma curta \
(poucas frases), sem nunca quebrar o personagem ou revelar que é uma \
simulação. Produza só a fala do estudante, nada mais.

Perfil do estudante que você está encenando:
{persona}
"""


def flip_historico(historico):
    """Troca os papéis: do ponto de vista do aluno simulado, as mensagens do
    Miro (role assistant) são o que ele lê (role user), e as respostas
    anteriores do próprio aluno (role user) são o que ele mesmo disse
    (role assistant)."""
    mapa = {"assistant": "user", "user": "assistant"}
    return [{"role": mapa[m["role"]], "content": m["content"]} for m in historico]


def gerar_resposta_aluno(client, persona_nome, historico):
    system_prompt = SYSTEM_PROMPT_ALUNO.format(persona=PERSONAS[persona_nome])
    resp = client.messages.create(
        model=MODEL_ALUNO_SIMULADO,
        max_tokens=300,
        system=system_prompt,
        messages=flip_historico(historico),
    )
    return next(b.text for b in resp.content if b.type == "text").strip()


def rodar_persona(base_url, atividade_slug, persona_nome, max_turnos, client):
    r = requests.post(
        f"{base_url}/api/miro/{atividade_slug}/iniciar",
        json={"identificacao": f"teste-{persona_nome}"},
    )
    r.raise_for_status()
    dados = r.json()
    conv_id, historico, encerrada = dados["conv_id"], dados["historico"], dados["encerrada"]

    print(f"\n=== persona={persona_nome} conv_id={conv_id} ===")
    print(f"[MIRO] {historico[-1]['content']}")

    turno = 0
    limite_atingido = False
    while not encerrada:
        turno += 1
        if turno > max_turnos:
            limite_atingido = True
            print(f"[AVISO] limite de {max_turnos} turnos atingido sem encerrar.")
            break

        resposta_aluno = gerar_resposta_aluno(client, persona_nome, historico)
        print(f"[ALUNO] {resposta_aluno}")

        r = requests.post(
            f"{base_url}/api/miro/{atividade_slug}/c/{conv_id}/responder",
            json={"resposta": resposta_aluno},
        )
        r.raise_for_status()
        dados = r.json()
        if dados.get("erro"):
            print(f"[ERRO] {dados['erro']}")
            break
        historico, encerrada = dados["historico"], dados["encerrada"]
        marca = " [SUGESTÃO DE PAUSA]" if dados.get("situacao") == "sugestao_pausa" else ""
        print(f"[MIRO]{marca} {historico[-1]['content']}")

    pasta = PASTA_TRANSCRICOES / atividade_slug
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{persona_nome}_{conv_id}.json"
    caminho.write_text(
        json.dumps(
            {
                "atividade": atividade_slug,
                "persona": persona_nome,
                "simulado": True,
                "conv_id": conv_id,
                "historico": historico,
                "encerrada": encerrada,
                "limite_atingido": limite_atingido,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[transcrição salva em {caminho}]")
    return caminho


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--atividade", default="modulo-2-planejamento")
    ap.add_argument("--persona", choices=sorted(PERSONAS), help="rodar só uma persona")
    ap.add_argument("--todas", action="store_true", help="rodar todas as personas")
    ap.add_argument("--max-turnos", type=int, default=MAX_TURNOS_PADRAO)
    ap.add_argument("--base-url", default="http://localhost:5000")
    args = ap.parse_args()

    if not args.persona and not args.todas:
        ap.error("especifique --persona <nome> ou --todas")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY não definida.")

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    personas = sorted(PERSONAS) if args.todas else [args.persona]
    for nome in personas:
        rodar_persona(args.base_url, args.atividade, nome, args.max_turnos, client)


if __name__ == "__main__":
    main()
