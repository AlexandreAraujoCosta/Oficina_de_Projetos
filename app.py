#!/usr/bin/env python3
"""
App Flask do Miro: expõe, por atividade, a conversa conduzida pelo
assistente-orientador. Generaliza agente_relatorio_leitura.py para múltiplas
atividades (cada uma um contexto em contextos/), carregadas dinamicamente
pelo slug na URL.

Duas famílias de rota:
- /miro/<atividade>/...      páginas HTML, pensadas para embutir num iframe
  do Canvas (aluno real).
- /api/miro/<atividade>/...  mesmas operações em JSON, usadas pelo script
  de aluno simulado (teste_aluno_simulado.py) e por qualquer outro cliente
  automatizado.

Identidade do aluno: autoidentificação simples (nome/matrícula digitado no
início) — ver nota em core.py sobre a migração futura para LTI.

Pré-requisitos:
  pip install flask anthropic
  set ANTHROPIC_API_KEY=...

Uso (local, piloto):
  python app.py
  Abra http://localhost:5000/miro/modulo-2-planejamento/iniciar
"""

import os
from pathlib import Path

from flask import Flask, request, render_template_string, redirect, url_for, abort, jsonify

from core import (
    nova_conversa,
    carregar_conversa,
    salvar_conversa,
    chamar_miro,
    gerar_abertura,
    slugificar_aluno_id,
    carregar_perfil,
    salvar_perfil_atividade,
)
from contextos import ATIVIDADES

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
PASTA_CONVERSAS = Path(__file__).parent / "conversas_miro"
PASTA_CONVERSAS.mkdir(exist_ok=True)
PASTA_PERFIS = Path(__file__).parent / "perfis_projeto"
PASTA_PERFIS.mkdir(exist_ok=True)

app = Flask(__name__)


def obter_atividade_ou_404(slug):
    atividade = ATIVIDADES.get(slug)
    if atividade is None:
        abort(404, description=f"Atividade '{slug}' não encontrada.")
    return atividade


def obter_client():
    """Devolve o client da Anthropic, ou None se não houver chave. Quem
    chama decide o que fazer sem ele (a abertura cai no fallback estático;
    um turno de conversa vira erro)."""
    if not ANTHROPIC_API_KEY:
        return None
    import anthropic
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def iniciar_conversa(atividade, identificacao):
    """Identifica o aluno, recupera o perfil de tentativas anteriores (se
    houver) e abre uma conversa nova com abertura gerada na hora."""
    aluno_id = slugificar_aluno_id(identificacao)
    perfil = carregar_perfil(PASTA_PERFIS, aluno_id)
    perfil_anterior = (perfil.get(atividade.slug) or {}).get("campos")
    abertura = gerar_abertura(obter_client(), atividade, perfil_anterior)
    return nova_conversa(PASTA_CONVERSAS, atividade, aluno_id, abertura=abertura)


def avancar_conversa(atividade_slug, conv_id, resposta):
    """Grava a resposta do aluno, chama o Miro, grava a réplica e atualiza o
    perfil de projeto do aluno. Usado tanto pelas rotas HTML quanto pelas
    JSON. Retorna (conv, erro)."""
    conv = carregar_conversa(PASTA_CONVERSAS, atividade_slug, conv_id)
    if conv is None:
        return None, "Conversa não encontrada."
    if conv["encerrada"]:
        return conv, None

    atividade = obter_atividade_ou_404(atividade_slug)
    conv["historico"].append({"role": "user", "content": resposta})
    salvar_conversa(PASTA_CONVERSAS, atividade_slug, conv_id, conv)  # grava antes de chamar a IA

    client = obter_client()
    if client is None:
        return conv, "ANTHROPIC_API_KEY não configurada no servidor."

    try:
        r = chamar_miro(client, atividade, conv["historico"])
        conv["historico"].append({"role": "assistant", "content": r["mensagem"]})
        conv["encerrada"] = not r["continuar"]
        conv["situacao"] = r["situacao"]
        conv["perfil_atual"] = r["perfil_atual"]
        salvar_conversa(PASTA_CONVERSAS, atividade_slug, conv_id, conv)
        salvar_perfil_atividade(
            PASTA_PERFIS, conv["aluno_id"], atividade_slug, r["perfil_atual"], r["situacao"], conv_id
        )
        return conv, None
    except Exception as e:
        return conv, str(e)


IDENTIFICAR_PAGE = """
<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>{{ atividade.titulo }}</title>
<style>
  body { font-family: Mulish, Arial, sans-serif; max-width: 500px; margin: 60px auto; padding: 0 16px; color: #222; }
  h1 { font-size: 19px; color: #003366; }
  input { width: 100%; box-sizing: border-box; padding: 8px; font-size: 15px; margin-top: 6px; }
  button { margin-top: 14px; padding: 10px 20px; font-size: 15px; cursor: pointer; }
  .aviso { font-size: 13px; color: #666; }
</style>
</head>
<body>
  <h1>{{ atividade.titulo }}</h1>
  <p class="aviso">Antes de começar, digite seu nome completo ou matrícula — é assim que o Miro vai reconhecer você se precisar continuar depois, ou numa atividade futura.</p>
  <form method="post" action="{{ url_for('iniciar_html', atividade_slug=atividade.slug) }}">
    <label>Nome ou matrícula<input type="text" name="identificacao" required autofocus></label>
    <button type="submit">Começar</button>
  </form>
</body>
</html>
"""

PAGE = """
<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<title>{{ atividade.titulo }}</title>
<style>
  body { font-family: Mulish, Arial, sans-serif; max-width: 700px; margin: 20px auto; padding: 0 16px; color: #222; }
  h1 { font-size: 19px; color: #003366; }
  .aviso { font-size: 13px; color: #666; }
  .msg { margin: 12px 0; padding: 10px 14px; border-radius: 8px; white-space: pre-wrap; }
  .agente { background: #eef0f4; }
  .agente.pausa { background: #fff4e0; border-left: 3px solid #c98a1f; }
  .aluno { background: #f4f4f4; text-align: right; }
  textarea { width: 100%; box-sizing: border-box; padding: 8px; font-family: inherit; font-size: 15px; }
  button { margin-top: 10px; padding: 10px 20px; font-size: 15px; cursor: pointer; }
  .concluido { border-left: 4px solid #006633; padding: 12px; background: #eafaf0; margin-top: 20px; }
  .id-conversa { font-family: monospace; background: #fff; padding: 4px 8px; border: 1px solid #ccc; }
</style>
</head>
<body>
  <h1>{{ atividade.titulo }}</h1>
  <p class="aviso">Converse com o Miro até ele considerar suas respostas sólidas. Ao final, você recebe um código para colar no Canvas — a conversa em si é a entrega. Pode pausar e voltar quando quiser: a conversa fica salva.</p>

  {% for m in conv.historico %}
    {% set ultima_e_pausa = loop.last and m.role == 'assistant' and conv.situacao == 'sugestao_pausa' %}
    <div class="msg {{ 'aluno' if m.role == 'user' else 'agente' }} {{ 'pausa' if ultima_e_pausa else '' }}">{{ m.content }}</div>
  {% endfor %}

  {% if conv.encerrada %}
    <div class="concluido">
      <strong>Conversa encerrada.</strong> Cole este código na sua entrega do Canvas:<br>
      <span class="id-conversa">{{ conv_id }}</span>
    </div>
  {% else %}
    <form method="post" action="{{ url_for('responder_html', atividade_slug=atividade.slug, conv_id=conv_id) }}">
      <textarea name="resposta" rows="4" placeholder="Sua resposta..." required></textarea>
      <button type="submit">Enviar</button>
    </form>
  {% endif %}
  {% if erro %}<p style="color:#c00;">Erro: {{ erro }}</p>{% endif %}
</body>
</html>
"""


# --- rotas HTML (iframe do Canvas) -----------------------------------------

@app.route("/miro/<atividade_slug>/iniciar", methods=["GET", "POST"])
def iniciar_html(atividade_slug):
    atividade = obter_atividade_ou_404(atividade_slug)
    if request.method == "GET":
        return render_template_string(IDENTIFICAR_PAGE, atividade=atividade)
    identificacao = request.form.get("identificacao", "").strip()
    conv_id, _ = iniciar_conversa(atividade, identificacao)
    return redirect(url_for("ver_conversa_html", atividade_slug=atividade_slug, conv_id=conv_id))


@app.route("/miro/<atividade_slug>/c/<conv_id>", methods=["GET"])
def ver_conversa_html(atividade_slug, conv_id):
    atividade = obter_atividade_ou_404(atividade_slug)
    conv = carregar_conversa(PASTA_CONVERSAS, atividade_slug, conv_id)
    if conv is None:
        return "Conversa não encontrada.", 404
    return render_template_string(PAGE, atividade=atividade, conv=conv, conv_id=conv_id, erro=None)


@app.route("/miro/<atividade_slug>/c/<conv_id>/responder", methods=["POST"])
def responder_html(atividade_slug, conv_id):
    atividade = obter_atividade_ou_404(atividade_slug)
    resposta = request.form.get("resposta", "").strip()
    conv, erro = avancar_conversa(atividade_slug, conv_id, resposta)
    if conv is None:
        return erro, 404
    return render_template_string(PAGE, atividade=atividade, conv=conv, conv_id=conv_id, erro=erro)


# --- rotas JSON (aluno simulado / clientes automatizados) -------------------

@app.route("/api/miro/<atividade_slug>/iniciar", methods=["POST"])
def iniciar_api(atividade_slug):
    atividade = obter_atividade_ou_404(atividade_slug)
    identificacao = (request.get_json(silent=True) or {}).get("identificacao", "teste-anonimo")
    conv_id, conv = iniciar_conversa(atividade, identificacao)
    return jsonify(conv_id=conv_id, historico=conv["historico"], encerrada=conv["encerrada"])


@app.route("/api/miro/<atividade_slug>/c/<conv_id>", methods=["GET"])
def ver_conversa_api(atividade_slug, conv_id):
    obter_atividade_ou_404(atividade_slug)
    conv = carregar_conversa(PASTA_CONVERSAS, atividade_slug, conv_id)
    if conv is None:
        return jsonify(erro="Conversa não encontrada."), 404
    return jsonify(conv)


@app.route("/api/miro/<atividade_slug>/c/<conv_id>/responder", methods=["POST"])
def responder_api(atividade_slug, conv_id):
    obter_atividade_ou_404(atividade_slug)
    resposta = (request.get_json(silent=True) or {}).get("resposta", "").strip()
    conv, erro = avancar_conversa(atividade_slug, conv_id, resposta)
    if conv is None:
        return jsonify(erro=erro), 404
    if erro:
        return jsonify(historico=conv["historico"], encerrada=conv["encerrada"], erro=erro), 502
    return jsonify(historico=conv["historico"], encerrada=conv["encerrada"], situacao=conv.get("situacao"))


if __name__ == "__main__":
    if not ANTHROPIC_API_KEY:
        print("Aviso: ANTHROPIC_API_KEY não definida — as respostas vão dar erro até você definir.")
    print("Atividades registradas:", ", ".join(ATIVIDADES))
    app.run(debug=True, port=5000)
