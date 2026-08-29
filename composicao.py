# -*- coding: utf-8 -*-
"""Compoe o Miro expandido: os tres estagios numa conversa so.

POR QUE ISTO EXISTE

O Miro portatil anda ate o primeiro equilibrio e manda buscar; o Nelson
trabalha a revisao; a teoria e o metodo ficam para depois. Sao tres
conversas porque cada uma tem de caber sozinha numa conta gratuita, e o
teto medido e de 92 mil caracteres.

No sistema de agentes nao ha teto: o prompt e arquivo que o assistente le,
como a LUIS.md da oficina irma, que tem 113 mil. La os tres estagios cabem
numa conversa so, com tres marcos, que e o que o desenho pede: quem
trabalha a revisao com o problema na mesma janela nao precisa recontar o
problema, e quem cotejou teoria e metodo ja viu a revisao que os justifica.

A FONTE E A MESMA, E ISSO E O PONTO

Nao ha doutrina escrita duas vezes. Esta composicao le os mesmos modulos
de contextos/ que geram as versoes portateis, e a unica coisa que ela faz
de proprio e descartar os blocos que existem SO porque o documento chega
de outra conversa, e que numa conversa unica seriam instrucao ativa
errada: pedir o pre-projeto que acabou de ser escrito ali, ou anunciar que
nao se sabe o que vem depois do segundo marco.

O DESCARTE E POR ANCORA DE TEXTO, E NAO POR INDICE

Marcar os blocos por numero de ordem seria fragil do pior modo: uma edicao
no Nelson desloca os indices e a montagem passa a descartar o bloco
errado, em silencio. Por ancora, uma edicao que mude a abertura do bloco
quebra a montagem com mensagem, que e o que se quer.

Uso:
    python composicao.py                      # grava o expandido
    python composicao.py --conferir           # so mede, nao grava
"""
import argparse
import importlib
import re
import sys
from pathlib import Path

import fechamentos
from core import base_com_nome
from gerar_prompt_portatil import TEMPLATE

# Os blocos do Nelson que existem so porque o documento chega de outra
# conversa. Numa conversa unica eles nao sao redundancia: sao instrucao
# errada, porque mandam pedir o que ja esta na mesa e prometem um segundo
# marco que aqui nao e o ultimo.
ENTRADA_DO_NELSON = [
    "NESTA ATIVIDADE eu sou o Nelson",
    "EU COMEÇO PEDINDO O PRÉ-PROJETO DO PROJETO",
    "AS LINHAS QUE SUMIRAM SÃO INFORMAÇÃO",
    "ANTES DOS TRÊS CASOS, UM DETALHE QUE POUPA DOIS TURNOS",
    "NOS TRÊS CASOS EU DIGO QUAL DELES É",
    "PRIMEIRO CASO: NÃO VEIO PRÉ-PROJETO NENHUM",
    "SEGUNDO CASO: VEIO O PRÉ-PROJETO E NÃO HÁ LEVANTAMENTO",
    "TERCEIRO CASO: JÁ HÁ ALGUMA COISA NAS SEÇÕES DE REVISÃO",
    "NESSE CASO EU MANDO O ALUNO DE VOLTA AO PRIMEIRO MARCO",
    "PARA ONDE A CONVERSA VAI DEPOIS DAQUI DEPENDE DO QUE",
    "SE O DESENHO SE MANTEVE, com a lacuna agora apoiada",
    "SE ALGUM DOS ELEMENTOS INICIAIS SE MOVEU",
    "SE O QUE FALTA É BUSCA, o caminho é continuar aqui",
    "EU NÃO PROMETO O QUE VEM DEPOIS DO SEGUNDO MARCO",
    "O QUE EU ENTREGO NO SEGUNDO MARCO",
    "O FECHAMENTO TEM DUAS ESCALAS",
]

# O terceiro estagio tambem foi escrito para rodar sozinho: pede o documento,
# trata tres casos de entrada, e encaminha para os outros dois assistentes. Numa
# conversa unica os encaminhamentos sao pior que redundantes: mandam sair de uma
# conversa que ja e a que eles indicam.
ENTRADA_DO_TERCEIRO = [
    "EU COMEÇO PEDINDO O PRÉ-PROJETO, inteiro",
    "TRÊS CASOS NA ENTRADA, E EU OS TRATO DIFERENTE",
    "PRIMEIRO CASO: NÃO VEIO DOCUMENTO NENHUM",
    "SEGUNDO CASO: VEIO O DOCUMENTO E AS DUAS COISAS",
    "TERCEIRO CASO: AS DUAS SEÇÕES JÁ ESTÃO ESCRITAS",
    "=== ENCAMINHAMENTOS ===",
    "DE VOLTA AO MIRO, quando o trabalho aqui mostrar",
    "DE VOLTA AO NELSON, quando aparecer que o quadro",
    "PARA A LEITURA DO DOCUMENTO ESCRITO, quando o par fechar",
]

# E o que entra no lugar deles, porque a volta continua existindo: o que muda
# e o destino, que deixa de ser outro assistente e passa a ser um marco desta
# mesma conversa.
VOLTAS_NA_CONVERSA_UNICA = """=== QUANDO É PRECISO VOLTAR ===

AO PRIMEIRO MARCO, quando o trabalho no método mostrar que a pergunta não se \
sustenta ou que os objetivos não correspondem a etapa nenhuma. Não é recuo: a \
pergunta é a peça de que tudo depende, e consertá-la de lado produz remendo. Eu \
digo que estamos voltando e por quê, e retomo dali.

AO SEGUNDO MARCO, quando aparecer que o quadro teórico precisa de literatura que \
não foi levantada, ou quando o método replicar um protocolo de outro trabalho que \
ninguém leu até o fim. A busca que falta é curta e nomeada, e não recomeça a \
revisão inteira.

E QUANDO O TERCEIRO MARCO FECHA, o que vem depois não é conversa: é a leitura do \
projeto escrito, com os programas, que devolve o arquivo anotado. Eu digo isso ao \
encerrar, sem prometer prazo nem resultado."""


def blocos(texto):
    """Os paragrafos do prompt: o que linha em branco separa, com as
    continuacoes de linha ja juntadas para a ancora casar."""
    plano = texto.replace(chr(92) + chr(10), "")
    return [b for b in plano.split(chr(10) + chr(10))]


def sem_os_blocos(instrucoes, ancoras, origem):
    """Tira os blocos que abrem por uma das ancoras, e exige que cada
    ancora tenha casado uma vez. Ancora que nao casa e edicao que mudou a
    abertura do bloco, e a montagem para para alguem olhar."""
    bs = blocos(instrucoes)
    contagem = {a: 0 for a in ancoras}
    ficam = []
    for b in bs:
        limpo = re.sub(r"\s+", " ", b).strip()
        casou = None
        for a in ancoras:
            if limpo.startswith(re.sub(r"\s+", " ", a).strip()):
                casou = a
                break
        if casou:
            contagem[casou] += 1
        else:
            ficam.append(b)
    erradas = {a: n for a, n in contagem.items() if n != 1}
    if erradas:
        raise SystemExit(
            "A composicao parou porque uma ancora nao casou uma vez so em "
            f"{origem}:\n"
            + "\n".join(f"  {n}x  {a}" for a, n in erradas.items())
            + "\n\nIsso quer dizer que o bloco mudou de abertura, ou sumiu. "
            "Conferir a lista ENTRADA_DO_NELSON em composicao.py antes de "
            "gerar de novo: descartar o bloco errado nao produz erro visivel "
            "no prompt, so um assistente que se comporta mal."
        )
    return (chr(10) + chr(10)).join(ficam)


MARCO_EXPANDIDO = """\
SÃO TRÊS MARCOS NESTA CONVERSA, e eu digo em qual estamos ao chegar a cada \
um, porque o aluno precisa saber o que já está fechado e o que ainda não.

O PRIMEIRO MARCO é o equilíbrio entre lacuna, problema, estratégia de abordagem \
e referencial, no nível de esboço. Ao alcançá-lo eu entrego o comentário e o \
pré-projeto, e digo que daqui a conversa segue para a revisão de literatura.

O SEGUNDO MARCO é a revisão adequada e concatenada com o resto. Se não houver \
revisão nenhuma, eu mando fazer e digo o que trazer de volta; se houver, eu \
trabalho o que ela fez com os outros elementos; e se o que voltar não sustentar \
a lacuna, eu mando refazer, dizendo o que precisa mudar.

O TERCEIRO MARCO é o cotejo da metodologia com a teoria, e ele só começa quando \
a revisão fecha, porque desenhar o método antes de saber o que o campo já fez \
produz um desenho que repete o que outro já executou.

EU ENTREGO UM DOCUMENTO A CADA MARCO, e o novo substitui o anterior. O último \
não encerra o projeto: dele sai o texto que vai ser escrito, e é o projeto \
escrito, e não este documento, que vai à qualificação."""


def montar(nome="Miro"):
    mi = importlib.import_module("contextos.modulo_2_planejamento")
    ne = importlib.import_module("contextos.revisao_literatura")

    ins_miro = mi.ATIVIDADE.instrucoes
    ins_nelson = sem_os_blocos(ne.ATIVIDADE.instrucoes, ENTRADA_DO_NELSON,
                               "revisao_literatura")

    partes = [ins_miro,
              "=== SEGUNDO ESTÁGIO: A REVISÃO DE LITERATURA ===",
              ins_nelson]

    tm = Path("contextos/teoria_e_metodo.py")
    if tm.exists():
        te = importlib.import_module("contextos.teoria_e_metodo")
        ins_terceiro = sem_os_blocos(te.ATIVIDADE.instrucoes,
                                     ENTRADA_DO_TERCEIRO, "teoria_e_metodo")
        partes += ["=== TERCEIRO ESTÁGIO: A METODOLOGIA E A TEORIA ===",
                   ins_terceiro,
                   VOLTAS_NA_CONVERSA_UNICA]

    fech = fechamentos.montar(mi.CONTEUDO_DO_COMENTARIO
                              if hasattr(mi, "CONTEUDO_DO_COMENTARIO")
                              else fechamentos.CONTEUDO_PLANEJAMENTO,
                              fechamentos.VEREDITO_PLANEJAMENTO,
                              MARCO_EXPANDIDO,
                              antes=fechamentos.PEDIDO_DE_TITULO)

    return TEMPLATE.format(
        base=base_com_nome(nome),
        fechamento=fech,
        instrucoes=(chr(10) + chr(10)).join(partes),
        criterios_abertura=mi.ATIVIDADE.criterios_abertura,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--saida", default="prompt_miro_expandido.md")
    ap.add_argument("--conferir", action="store_true",
                    help="mede e nao grava")
    a = ap.parse_args()
    texto = montar()
    print(f"  Miro expandido: {len(texto)} caracteres")
    portateis = [("Miro", "prompt_portatil_modulo_2_planejamento.md"),
                 ("Nelson", "prompt_portatil_revisao_literatura.md")]
    for nome, arq in portateis:
        p = Path(arq)
        if p.exists():
            print(f"  {nome} portatil: {len(p.read_text(encoding='utf-8'))}")
    if a.conferir:
        return
    Path(a.saida).write_text(texto, encoding="utf-8")
    print(f"  gravado em {a.saida}")
    print("  Este arquivo e para o sistema de agentes, e nao cabe numa conta")
    print("  gratuita: para o chat continuam valendo os dois portateis.")


if __name__ == "__main__":
    main()
