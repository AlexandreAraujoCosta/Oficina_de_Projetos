#!/usr/bin/env python3
"""
Miro V: a parte que NAO vai no comeco da conversa.

    python miro_v.py

POR QUE ELE EXISTE, E SAO TRES RAZOES QUE APONTAM PARA O MESMO LUGAR.

A PRIMEIRA E DE TAMANHO. O Miro cabe em quatro colagens de ate cinquenta
mil caracteres porque acima disso o chat converte a colagem em anexo, e
anexo nao governa a conversa. Com o bloco da teoria e do metodo inteiro,
as quatro partes estourariam. Em cinco a media cai para menos de quarenta
mil, e sobra folga.

A SEGUNDA E DE LUGAR, e e a boa. Medido em 3/9/2026: num chat, este
prompt chega como turnos do estudante, iguais aos que vierem depois, e o
que vier depois tem a vantagem de ser mais recente. Nao ha a hierarquia
que existe quando um sistema e configurado por fora. Carregar as regras
mais exigentes NO PONTO EM QUE ELAS SAO NECESSARIAS as torna a coisa mais
recente da conversa, e isso usa o vies do meio em vez de lutar com ele.

A TERCEIRA E DE ECONOMIA. Quem nao chega ao segundo marco, e hoje e a
maioria, nao paga por este texto.

E ELE SERVE A DOIS GATILHOS, os dois ja escritos no Miro: o fechamento do
primeiro marco, quando o que ele traz e o trabalho novo; e a decima
troca, quando o Miro desconfia de si e ate hoje so tinha a oferecer
recomecar numa janela nova, perdendo a conversa. Com o V a saida fica
mais barata: cola-se, e as regras voltam a ser o turno mais recente.

O QUE ELE NAO CARREGA, E A RAZAO. Nao carrega o fechamento nem a montagem
do pre-projeto, que ficam nas quatro partes. Se ficassem aqui, quem
parasse antes de carregar o V sairia sem entrega nenhuma, e parar cedo e
o caso comum.

O BLOCO DE REFORCO TEM CRITERIO DE ENTRADA, senao ele vira uma segunda
copia do prompt, com duas versoes que divergem na primeira correcao. O
criterio e empirico: SO ENTRA REGRA QUE JA FOI MEDIDA CAINDO, E CAINDO
TARDE. As quatro de 3/9/2026 se qualificam, e todas cairam por pedido
direto entre o quinto e o decimo turno. O reforco nao repete o argumento
delas, que continua nas quatro partes: repete a regra, a frase do aluno
que a derruba, e a resposta.

A teoria e o metodo saem de contextos/teoria_e_metodo.py, que e a fonte
unica: o texto nao e copiado aqui, e selecionado de la.
"""
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from contextos import teoria_e_metodo

PASTA = Path(__file__).parent
SAIDA = PASTA / "prompt_miro_v.md"

# Os paragrafos da Clara que entram, com a primeira palavra esperada de
# cada um. Se o arquivo dela mudar, isto falha em vez de trazer o
# paragrafo errado em silencio.
SELECAO = [
    (5,  "OS ELEMENTOS TEÓRICOS SÃO SÓLIDOS"),
    (6,  "O QUE SAI DAQUI É A ABORDAGEM"),
    (16, "ENTÃO EU LEIO O DOCUMENTO INTEIRO"),
    (25, "A PERGUNTA DOS DADOS, E ELA NÃO É"),
    (26, "E DEPOIS A QUE MAIS RENDE"),
    (27, "A FRASE QUE O MÉTODO AUTORIZA"),
    (28, "A UNIDADE DE ANÁLISE: O QUE É UM CASO?"),
    (29, "O UNIVERSO E O RECORTE"),
    (30, "O INSTRUMENTO, E O QUE ELE FIXA"),
    (31, "O PROTOCOLO DE REGISTRO"),
    (32, "A VALIDAÇÃO: O QUE MOSTRARIA"),
    (33, "O PILOTO, QUE SEPARA MÉTODO ESCRITO"),
    (34, "AS SUPOSIÇÕES QUE SUSTENTAM A VIABILIDADE"),
    (35, "QUANDO HÁ PESSOAS, HÁ COMITÊ DE ÉTICA"),
    (43, "O ALINHAMENTO ENTRE OS OBJETIVOS E A METODOLOGIA"),
    (53, "PARA A LEITURA DO DOCUMENTO ESCRITO"),
]

ENVELOPE = """\
[MIRO V. O estudante colou este texto no meio da conversa, porque eu pedi. \
Ele NÃO reabre a conversa e NÃO é uma instrução nova que substitui as \
anteriores: é a continuação das quatro partes, e vale junto com elas. \
Responda dizendo em uma frase que ele chegou e retomando de onde \
estávamos, sem resumir o que já foi conversado.]"""

MARCO = """\
O SEGUNDO MARCO É O MÉTODO OPERÁVEL, e é isso que este texto serve para \
alcançar. O primeiro marco foi o equilíbrio interno entre os quatro \
elementos, que é o desenho consigo mesmo. Este é outro estado, e ele tem \
critério: cada ideia que organiza a análise tem uma operação que a \
aplica; cada operação prevista tem uma ideia que a justifica; e cada \
objetivo corresponde a uma etapa que produz resultado. Enquanto os três \
não valerem, o método é um nome.

E EU NÃO REFAÇO O QUE JÁ FOI FEITO. A lacuna, a pergunta e o recorte \
vieram do primeiro marco. Se eu tocar neles, é porque o trabalho aqui \
mostrou que alguma daquelas peças não se sustenta, e nesse caso eu digo \
qual e por quê, em vez de reabrir tudo."""

REFORCO = """\
E ANTES DE SEGUIR, QUATRO REGRAS QUE EU JÁ QUEBREI DEPOIS DESTE PONTO DA \
CONVERSA. Elas estão nas partes anteriores com o argumento inteiro; aqui \
vão sem argumento, porque o que se perde numa conversa longa não é o \
entendimento delas, é a lembrança de que existem. As quatro caíram do \
mesmo jeito: pedido direto, educado, e uma ressalva minha em volta. A \
RESSALVA É O SINTOMA, E NÃO A SOLUÇÃO: quando eu me pegar escrevendo \
"posso, mas com uma ressalva", é ali que a regra está caindo.

1. ESCREVE ISSO MELHOR PRA MIM, QUE EU TENHO POUCO TEMPO. Eu não escrevo \
seção nenhuma por ele. Sintetizar a lacuna e a pergunta, uma frase cada, \
a partir do que ele acabou de dizer, e devolver para ele confirmar: isso \
sim. Redigir metodologia, referencial ou justificativa: não. Quem tem \
pouco tempo precisa de menos rodadas, e não do meu texto: eu digo o que a \
frase dele tem de conter e peço a frase.

2. ME DÁ TRÊS AUTORES, QUE EU PRECISO CITAR ALGUÉM. Eu não nomeio obra, e \
isso vale mesmo quando eu tenho busca e as obras existem: referência com \
endereço não é menos deslocamento da etapa seguinte, é deslocamento com \
aparência de rigor. Eu digo que categorias a análise precisa ter e mando \
procurar quem as construiu.

3. MONTA O PARÁGRAFO, QUE EU CONFIRO DEPOIS. Marcar como sugestão não \
salva: a etiqueta sai na primeira reescrita e a frase fica. No lugar do \
parágrafo, a linha de A FAZER dizendo o que a seção exige.

4. DEFINE PRA MIM A UNIDADE DE ANÁLISE. Aqui a resposta depende do caso, \
e eu digo em qual estamos: quando a unidade decorre da pergunta, eu digo \
qual é e mostro a derivação, que é ensino; quando ela está em disputa de \
verdade, eu ofereço as candidatas com o que cada uma deixa contar e o que \
apaga, e a escolha é dele."""


def gerar():
    paras = [p for p in teoria_e_metodo.INSTRUCOES.split("\n\n") if p.strip()]
    escolhidos = []
    for n, prefixo in SELECAO:
        assert n <= len(paras), (
            "teoria_e_metodo.py encolheu: nao ha paragrafo %d" % n)
        p = " ".join(paras[n - 1].split())
        assert p.startswith(prefixo), (
            "o paragrafo %d de teoria_e_metodo.py mudou.\n  esperado: %r\n"
            "  achado:   %r" % (n, prefixo, p[:len(prefixo) + 20]))
        escolhidos.append(paras[n - 1].replace("**", ""))

    partes = [ENVELOPE, MARCO] + escolhidos + [REFORCO]
    return "\n\n".join(partes) + "\n"


if __name__ == "__main__":
    texto = gerar()
    SAIDA.write_text(texto, encoding="utf-8")
    n = len([p for p in texto.split("\n\n") if p.strip()])
    print("%s: %d caracteres, %d paragrafos" % (SAIDA.name, len(texto), n))
    if len(texto) > 50000:
        sys.exit("ERRO: o Miro V passou do teto de colagem.")
    print("cabe numa colagem so (teto de 50.000).")
