#!/usr/bin/env python3
"""
Gera uma versão "portátil" do prompt de uma atividade do Miro: um único
texto autocontido que o aluno cola como primeira mensagem em qualquer chat
de IA gratuito (sem custear API), preservando o mesmo comportamento da
versão hospedada em app.py.

Diferença em relação ao core.py/app.py: aqui não há servidor interceptando
a resposta em JSON estruturado — o encerramento é dito em linguagem
natural. O Miro escreve, ao encerrar, um comentário final de fechamento (o
desenho a que se chegou, tensões reconhecidas, suposições fáticas) mais
uma nota curta sobre a condução da conversa.

A entrega passou por duas mudanças. Em 29/7/2026 deixou de ser a conversa
inteira e passou a ser só o comentário mais a nota. Em 24/8/2026 voltou a
ser a conversa inteira, agora fechada pelo comentário e pela nota, e a
razão veio do primeiro uso com alunos de verdade: das 22 entregas da
primeira turma, 10 mostravam conversas que nunca chegaram a fechamento
nenhum, e isso só foi possível descobrir porque aqueles alunos tinham
colado o diálogo todo. Com a entrega reduzida ao comentário, uma conversa
que não fecha não produz entrega, e o que falhou fica invisível. A
conversa é a evidência; o comentário é a leitura dela.

POR QUE TRÊS REGRAS DO FECHAMENTO SÃO COMO SÃO. Cada uma vem de um caso
real observado nas rodadas de teste do Miro, da Ana e do Quim. Não são
preferências de redação, e "melhorá-las" costuma significar desfazê-las.

1. PROIBIÇÃO DE ASPAS. Um modelo mais fraco, obrigado a produzir citação
literal, inventou uma frase e atribuiu ao estudante na avaliação final.
Exigir citação cria demanda por citação, e o modelo sem memória exata
preenche o espaço fabricando. Como é o próprio aluno que lê e entrega esse
texto, ele percebe na hora que não disse aquilo, e a entrega inteira perde
credibilidade. Por isso a ancoragem é por descrição de momento, e o que
substitui a aspas é nomear a coisa concreta: qual elemento do projeto
mudou, qual pergunta provocou a mudança.

2. PROIBIÇÃO DE AFIRMAÇÃO GERAL sobre o formato da conversa ("ela andou",
"nunca voltou atrás"). Um modelo negou, na própria nota, um episódio que
tinha acontecido na conversa. Resumo de memória sobre o conjunto é onde a
alucinação aparece; evento localizado é verificável.

3. PROIBIÇÃO DE DAR NOTA. Houve caso real de assistente atribuindo nota 9
numa atividade que não tem nota. O aluno cola isso como entrega e acredita.

Gerado a partir do mesmo código-fonte usado pela versão hospedada
(core.SYSTEM_PROMPT_BASE + contextos/<atividade>.py), para as duas versões
não divergirem com o tempo — não edite o .md gerado diretamente, edite a
atividade e rode este script de novo.

Uso:
  python gerar_prompt_portatil.py modulo_2_planejamento prompt_portatil_modulo_2.md
"""
import importlib
import sys
from pathlib import Path

import fechamentos
from core import SYSTEM_PROMPT_BASE, base_com_nome

TEMPLATE = """\
Um estudante colou este texto inteiro como primeira mensagem para você, \
num assistente de IA qualquer. A partir da sua resposta seguinte, \
converse normalmente com ele seguindo as instruções abaixo.

{base}

QUANDO ENCERRAR: esta versão não usa nenhum formato de dados estruturado. \
Diga em linguagem natural, claramente, quando considerar os elementos da \
atividade sólidos (o critério está nas instruções da atividade, abaixo). \
Antes de decidir encerrar, sempre teste mentalmente contra esse critério: \
nunca encerre só porque a conversa já está longa. Mas encerro sempre que o \
aluno pedir: se ele disser que quer parar, eu paro e escrevo o comentário \
do ponto em que estamos, sem negociar mais uma rodada e sem fazer com que \
ele peça duas vezes.

{fechamento}

COMO EU ANCORO ESSE COMENTÁRIO, e isso é regra rígida que vale também \
para o esboço, onde a tentação é maior porque as seções pedem justamente \
as formulações dele: eu NÃO uso aspas
e NÃO cito frases do aluno. Descrevo o momento em discurso indireto, \
dizendo o que ele fez e quando, e nomeando a coisa concreta de que se \
trata: qual elemento do projeto mudou, qual pergunta provocou a mudança. \
Por exemplo: quando eu perguntei que \
dados permitiriam testar aquilo, você percebeu que a sua fonte só \
mostraria o que os autores escreveram, e aí reformulou a estratégia. \
Aspas exigiriam palavras exatas que eu posso não ter guardado direito, e \
preencher esse espaço com uma frase plausível seria atribuir ao aluno \
algo que ele não disse, num texto que ele vai ler e entregar, e que ele \
percebe na hora que não é dele. O que continua proibido é a frase geral \
sem momento nenhum: dizer que o aluno desenvolveu bem o projeto não \
vale, porque não aponta para nada que tenha acontecido. E eu nunca \
afirmo no comentário uma compreensão sem conseguir dizer em que momento \
da conversa ela apareceu.

{instrucoes}

Escreva agora a sua primeira fala para este estudante, atendendo aos \
critérios de abertura abaixo. A redação é sua e não deve ser uma fórmula \
decorada: se o estudante já tiver usado este prompt antes, ele não deve \
reencontrar as mesmas frases. Produza apenas a fala, sem comentários seus \
sobre ela.

CRITÉRIOS DE ABERTURA:
{criterios_abertura}
"""


def gerar(nome_modulo_contexto):
    mod = importlib.import_module(f"contextos.{nome_modulo_contexto}")
    atividade = mod.ATIVIDADE
    # Cada contexto pode trazer o seu proprio bloco de fechamento; sem
    # isso, vale o do planejamento, que foi o primeiro a existir.
    fechamento = getattr(mod, "FECHAMENTO", fechamentos.PLANEJAMENTO)
    return TEMPLATE.format(
        base=base_com_nome(getattr(mod, "NOME", "Miro")),
        fechamento=fechamento,
        instrucoes=atividade.instrucoes,
        criterios_abertura=atividade.criterios_abertura,
    )


if __name__ == "__main__":
    nome = sys.argv[1] if len(sys.argv) > 1 else "modulo_2_planejamento"
    texto = gerar(nome)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(texto, encoding="utf-8")
        print(f"Gravado em {sys.argv[2]} ({len(texto)} caracteres).")
    else:
        sys.stdout.buffer.write(texto.encode("utf-8"))
