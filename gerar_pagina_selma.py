#!/usr/bin/env python3
"""
Gera pagina_selma.html, a pagina propria da Selma.

    python gerar_pagina_selma.py

POR QUE ELA EXISTE. O Miro tem pagina propria, com o prompt e o botao de
copiar; a Selma so vivia dentro da pagina da Oficina. Agora ela tem a dela,
e a oficina aponta para ca.

O ESTILO NAO E COPIADO A MAO: sai do modelo da oficina, lido em tempo de
geracao. Duas folhas de estilo escritas em paralelo divergem na primeira
correcao, e a diferenca aparece so no navegador de outra pessoa.

O PROMPT TAMBEM NAO: sai de prompt_selma.md, que sai de
contextos/selecao_banca.py. Quem transcreve e o codigo.
"""
import io
import re
import sys
from pathlib import Path

PASTA = Path(__file__).parent
MODELO = PASTA / "modelo_pagina_oficina_projetos.html"
PROMPT = PASTA / "prompt_selma.md"
SAIDA = PASTA / "pagina_selma.html"
OFICINA = "https://claude.ai/code/artifact/1d29d917-d73f-48b3-9f89-1eaab12cfffd"
MIRO = "https://claude.ai/code/artifact/6912df2d-dc98-40b3-beb8-172219b077bb"

CORPO = """<meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,400;7..72,600&family=Mulish:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap">
<title>Selma: leitura de projeto de pesquisa</title>

%(estilo)s

<style>
  /* as duas vias, na forma da pagina do Miro */
  .vias-grade { display: grid; grid-template-columns: repeat(2, 1fr); gap: .8rem;
                margin: 1.2rem 0 .6rem; }
  @media (max-width: 44rem) { .vias-grade { grid-template-columns: 1fr; } }
  .via-bt { display: block; text-align: left; font: inherit; color: inherit;
            background: var(--surface); border: 1px solid var(--rule);
            border-radius: 3px; padding: 1rem 1.1rem; cursor: pointer; }
  .via-bt:hover, .via-bt:focus-visible { border-color: var(--accent); }
  .via-bt[aria-pressed="true"] { border-color: var(--accent);
                                 box-shadow: inset 0 0 0 1px var(--accent); }
  .via-nome { display: block; font-family: var(--serif); font-size: var(--t-h3);
              line-height: 1.15; margin-bottom: .4rem; color: var(--accent); }
  .via-txt { display: block; font-size: var(--t-sm); line-height: 1.5;
             margin-bottom: .4rem; color: var(--ink-soft); }
  .via-volta { display: block; font-size: var(--t-sm); color: var(--muted);
               line-height: 1.45; }
  .via-guia { margin: 1.2rem 0 2.4rem; }
  .via-guia ol { margin: 0 0 1.2rem; padding-left: 1.3rem; max-width: var(--measure); }
  .via-guia li { margin-bottom: .55rem; font-size: var(--t-sm); }
</style>


<nav class="indice" aria-label="Índice da página">
  <details class="indice-caixa" id="indice">
    <summary>Índice</summary>
    <div class="indice-lista">
      <a href="#dimensoes">As dimensões analisadas</a>
      <a href="#nota">A nota sai de uma contagem</a>
      <a href="#ia">Os indícios de IA</a>
      <a href="#descricao">Dois parágrafos por dimensão</a>
      <a class="grupo" href="#lote">Uso em lote</a>
      <a href="#usar">Como usar: chat e agente</a>
    </div>
  </details>
</nav>

<script>
  /* Na tela larga o índice fica aberto, porque ali ele é trilho e não
     controle. details fechado não se abre por CSS, e por isso esta linha
     existe; sem ela, o que sobra é a linha clicável. */
  (function () {
    var larga = window.matchMedia("(min-width: 78rem)");
    var caixa = document.getElementById("indice");
    function ajustar() { if (larga.matches) { caixa.open = true; } }
    ajustar();
    larga.addEventListener("change", ajustar);
  })();
</script>

<div class="wrap">

<header>
  <p class="eyebrow"><span class="eb-linha"><a href="https://direito.unb.br/">Faculdade de Direito da UnB</a> &middot; <a href="https://pmpd.unb.br/">PMPD</a> &middot; <a href="https://claude.ai/code/artifact/4fe98c90-3461-4d03-8c83-7ba2fe0c1c72">Oficinas Acadêmicas</a></span><span class="eb-linha eb-baixo">Assistentes: <a href="https://claude.ai/code/artifact/6912df2d-dc98-40b3-beb8-172219b077bb">Miro</a> &middot; <span class="eb-atual" aria-current="page">Selma</span></span></p>
  <h1>Selma</h1>
  <p class="lead"><strong>Selma lê um projeto de pesquisa e escreve o parecer
  que uma banca escreveria.</strong> O relatório sai em quatro partes: a
  descrição do que o projeto pergunta e de como pretende responder; a ementa,
  com uma entrada e uma nota por elemento; a avaliação de cada um dos cinco
  elementos, com os achados classificados e localizados na seção em que estão;
  e as perguntas para as quais o autor deve estar preparado. A conclusão é uma
  só: <strong>as condições que o projeto precisa cumprir para ser apresentável
  a uma banca de qualificação</strong>. Não há conversa: ela lê, classifica e
  entrega. O <a href="%(miro)s">Miro</a> trabalha com quem escreve o projeto;
  a Selma lê o que já está escrito.</p>

<div class="autoria">
  <p>Ferramenta desenvolvida por <a href="https://sigaa.unb.br/sigaa/public/docente/portal.jsf?siape=2332291"><b>Alexandre Araújo Costa</b></a> (Doutor em Direito, Professor da UnB, Coordenador do PMPD, <a href="mailto:alexandrearcos@unb.br">alexandrearcos@unb.br</a>), com assistência do modelo Claude Opus 5, em Claude Code. O código está no repositório <a href="https://github.com/AlexandreAraujoCosta/Oficina_de_Projetos">Oficina_de_Projetos</a>.</p>
  <p>Trata-se de protótipos, ainda em fase de testes, e todo feedback será muito útil para aperfeiçoá-los. Se você usar as ferramentas, envie por favor um relato por <a href="https://docs.google.com/forms/d/e/1FAIpQLSdziEHALH04stCpbVCHqDODK072YKzRRWCaN4ZhsiHojYrKmg/viewform?usp=dialog">este formulário</a>, pois, a partir deles, é possível compreender o funcionamento dos prompts em situações reais.</p>
</div>
</header>

<h2 id="usar">Como usar</h2>

<p class="deck">Duas vias. No chat você cola o prompt e o projeto, e o
relatório sai na resposta. No agente, o assistente busca o prompt sozinho, lê o
projeto que está na sua pasta e grava o relatório como arquivo.</p>

<div class="vias-grade">
  <button type="button" class="via-bt" data-via="chat">
    <span class="via-nome">Modo chat</span>
    <span class="via-txt">Você tem uma conta de assistente e nada instalado.
    Cola-se o prompt numa janela nova e, em seguida, o projeto.</span>
    <span class="via-volta">O relatório sai na resposta, para copiar.</span>
  </button>

  <button type="button" class="via-bt" data-via="agente">
    <span class="via-nome">Modo agente</span>
    <span class="via-txt">Um assistente que roda dentro de um programa e lê a
    pasta do seu projeto: Claude Code, Copilot em modo agente, e outros.</span>
    <span class="via-volta">O relatório sai em PDF, e a existência das obras da
    bibliografia é conferida na busca.</span>
  </button>
</div>

<div class="via-guia" id="guia-chat" hidden>
  <ol>
    <li><strong>Abra uma janela nova.</strong> O que já foi dito numa conversa em
    andamento entra na leitura sem avisar.</li>
    <li><strong>Cole o prompt</strong>, da caixa abaixo, e envie.</li>
    <li><strong>Cole o projeto como texto</strong>, e não como anexo: de anexo ela
    lê com menos fidelidade justamente onde precisa ser exata, que é o
    localizador. Se não der, ela trabalha com o que tem e registra que os
    localizadores podem estar deslocados.</li>
    <li><strong>Ela pede quatro coisas</strong>, e cada uma muda o que sai: o
    projeto como foi submetido; o <strong>edital</strong>, se houver, porque com
    ele o relatório sai na forma da ficha que a banca preenche; a <strong>linha
    de pesquisa</strong>, sem a qual ela não examina aderência; e a
    <strong>numeração dos parágrafos</strong>, se você tiver como fornecê-la,
    porque é dela que sai o localizador do bloco de dados.</li>
    <li><strong>O relatório sai numa resposta só</strong>, com a descrição, a
    ementa, a avaliação dos cinco elementos, as condições e as perguntas para a
    arguição.</li>
  </ol>

  <div class="caixa-prompt">
    <div class="barra">
      <span id="tamanho"></span>
      <button class="copiar" id="btn-copiar" type="button">Copiar prompt</button>
    </div>
    <textarea id="selma" readonly spellcheck="false">{{PROMPT_SELMA}}</textarea>
  </div>

  <p class="nota" style="margin-top: 1.2rem;"><strong>A colagem é grande, e o que
  acontece com ela depende do serviço.</strong> São 49 mil caracteres. No ChatGPT
  eles ainda entram como texto; no Claude, acima de cerca de 44 mil a colagem
  vira um cartão &#8220;PASTED&#8221;, e ali o conteúdo entra na conversa do mesmo
  jeito. As duas medidas são de 02/09/2026, por colagem real.</p>
</div>

<div class="via-guia" id="guia-agente" hidden>
  <p style="color: var(--ink-soft);">Você não copia nada desta página. Abra no
  agente a pasta onde está o projeto, ponha-o em modo agente, e cole o pedido
  abaixo.</p>

  <div class="caixa-prompt">
    <div class="barra">
      <span>o pedido, para colar no agente</span>
      <button class="copiar" id="btn-copiar-agente" type="button">Copiar pedido</button>
    </div>
    <textarea id="pedido-agente" readonly spellcheck="false">Busque este arquivo e leia-o por inteiro:

https://raw.githubusercontent.com/AlexandreAraujoCosta/Oficina_de_Projetos/master/prompt_selma.md

Antes de começar, escreva a última frase dele, para eu conferir que a leitura chegou ao fim.

Depois siga as instruções como se fossem suas: leia o projeto que está nesta pasta e escreva o relatório. Grave-o como arquivo, em vez de mostrá-lo na tela.</textarea>
  </div>

  <p class="nota"><strong>A última frase é a conferência.</strong> Ferramenta de
  busca que resume em vez de devolver o texto entrega o prompt pela metade sem
  avisar. O arquivo termina em <em>&#8220;… e que o diagnóstico com localizador é o
  que ele leva.&#8221;</em> Se o que ele repetir não for isso, peça que busque de
  novo, ou clone o repositório:</p>
  <p class="mono" style="font-size: var(--t-sm); overflow-wrap: anywhere;">git clone https://github.com/AlexandreAraujoCosta/Oficina_de_Projetos</p>

  <p><strong>O que o agente acrescenta</strong> é a busca, que confere se as obras
  da bibliografia existem, e o arquivo de volta. Os programas do repositório
  montam o resto: <span class="mono">relatorio_pdf.py</span> transforma o
  relatório em PDF, e <span class="mono">selma_lote.py</span> monta a tabela
  comparativa de um processo seletivo a partir do bloco de dados de cada
  leitura, recusando o relatório cujo bloco não fecha.</p>
</div>

<h2 id="dimensoes">As dimensões analisadas</h2>

<div class="fluxo">
  <ol>
    <li><strong>Problema, objetivos e hipóteses</strong>, lidos um contra o
    outro. Há pergunta, ou só tema? O recorte (que material, que período), a
    clareza (a mesma formulação nas seções em que ela volta) e a viabilidade.
    <b>O objetivo geral responde à pergunta</b>, e cada objetivo específico
    corresponde a uma etapa da metodologia? E a hipótese é sujeita a teste ao
    longo do trabalho, ou é afirmação que nenhum resultado previsto poderia
    contrariar?</li>
    <li><strong>Justificativa.</strong> A lacuna nomeada como falta de
    conhecimento, e <b>de que modo enfrentar esta pergunta justifica o
    trabalho</b>, que não é a mesma coisa que a importância do tema: um tema
    importante justifica qualquer pesquisa sobre ele, e portanto nenhuma. Os
    impactos, o acadêmico e o social, com alguém concreto que decidiria
    diferente (categoria profissional não é destinatário). E o produto técnico,
    que é o que faz a apropriação social dos resultados acontecer.</li>
    <li><strong>Metodologia e teoria</strong>, lidas juntas, e a primeira coisa
    é se <b>o método responde à pergunta do elemento 1</b>: método suficiente é método
    articulado à pergunta, e não método bem descrito. A fonte, as
    categorias, a operação (contar, classificar, qualificar, comparar,
    interpretar) e a forma do resultado. A proporção entre as duas: método
    rarefeito demais faz a teoria deixar de restringir qualquer conclusão.
    E <b>o escopo</b>: o que o projeto promete cabe no prazo e nas mãos de uma
    pessoa?</li>
    <li><strong>Bibliografia.</strong> A lista contra o texto, a composição da
    lista, e a existência das obras quando há busca.</li>
    <li><strong>Indícios de uso de IA.</strong> As marcas que se conferem na
    página, e o que elas custam. <b>Esta não tem nota:</b> é graduada em
    cinco níveis, e viaja ao lado das outras.</li>
  </ol>
</div>

<p><strong>Se vier um edital junto com o projeto, são os critérios dele que
valem</strong>, na ordem e com os nomes que ele usa, porque quem avalia
preenche uma ficha e relatório organizado por outros critérios obriga a banca
a traduzir cada achado. O que o edital pontua e ela não lê (currículo,
entrevista, proficiência) fica de fora, sem nota inventada, e ela diz
quantos critérios entraram e quantos ficaram de fora.</p>

<h2 id="nota">A nota sai de uma contagem</h2>

<p>Cada achado se classifica em uma de três classes, com o teste feito
<strong>com o defeito no lugar</strong>, e não depois de imaginá-lo
consertado. <b>Grave:</b> do jeito que está, a dimensão não entrega o que
promete, e nenhum prazo resolve. <b>Médio:</b> a dimensão
entrega, e há coisa a resolver antes de começar, que se resolve fazendo.
<b>Leve:</b> resolve-se no caminho. Depois a contagem manda na faixa e
no dígito, e o relatório mostra a conta.</p>

<p>Duas regras de subida corrigem o que a contagem sozinha não veria, e as
duas se contam na página: defeito que aparece em <b>mais da metade das
subdivisões</b> de uma seção sobe uma classe, e achado que atinge afirmação
que o projeto repete em <b>três ou mais tópicos</b> também sobe. A subida é de
uma classe só.</p>

<h3>Uma conclusão só: as condições</h3>
<p>Ela não calcula média e não dá veredito de aprovação. <b>A única coisa
que ela conclui é a lista de condições para o projeto ser apresentável a uma
banca de qualificação</b>, e essa lista já está na contagem, sem conta nova,
porque as três classes são uma escala de custo de conserto. Grave vira
condição sempre; médio vira condição sempre; leve não vira,
porque se resolve no caminho, e listá-lo transformaria a peça numa lista de
reparos.</p>

<p><b>Cada condição se escreve como coisa a fazer</b>, no infinitivo, com a
dimensão de onde vem e o tópico em que o problema está. Fechar a lista de casos
antes de começar, e não “o corpus é frágil”. Quem lê decide com a primeira
forma; com a segunda, não decide nada. E quando não há nenhuma, isso se
escreve, e é a frase mais forte que a leitura pode produzir sobre um projeto:
nenhum achado grave e nenhum médio em dimensão nenhuma.</p>

<p><b>A média saiu junto com o veredito</b>, e a razão é que ela só servia para
dizer de que lado da linha de 7 o projeto caía. Sem a linha, seria número sem
âncora, e número sem âncora numa ficha de banca é convite a ordenar por ele. As
quatro notas por dimensão ficam: são o diagnóstico, e é delas que as condições
saem.</p>

<div class="confere">
  <section class="sim">
    <h3>Confere</h3>
    <p>Todo achado traz o <b>tópico</b> em que está, porque quem lê responde
    pela decisão e tem de poder abrir a página e discordar. A nota vem depois
    do achado, nunca no lugar dele.</p>
  </section>
  <section class="nao">
    <h3>Não confere</h3>
    <p>Não diz se a lacuna existe de fato no campo, nem se as obras dizem o que
    o projeto lhes atribui. Não julga originalidade. Não lê o candidato. Não
    compara projetos entre si. E <b>não recomenda admitir ou não admitir</b>: a
    decisão se toma com as vagas, a linha e os outros candidatos.</p>
  </section>
</div>

<h3>O que a contagem diz sobre o custo de consertar</h3>
<p>As três classes são uma escala de custo de conserto, e por isso a contagem
informa mais que a nota. Um projeto com cinco achados leves fica em 7, e um com
um achado grave fica em 4: quem lê vê, na conta, que o primeiro se conserta no
caminho e o segundo não. Diante de um achado grave ela diz o que teria de mudar
e de que tamanho é a mudança, porque reescrever uma seção é uma coisa e
refazer a pergunta é outra. <strong>O juízo de aprovação não é dela</strong>:
ela entrega a contagem e as condições, e quem decide tem as vagas, a linha e os
outros candidatos.</p>
<p><strong>O ganho de arguição viaja com a condição a que pertence</strong>, no
terceiro campo da linha de dados, e não num bloco de prosa no fim. É o que o
autor pode dizer diante da banca para aquele elemento subir de faixa antes de a
condição estar cumprida; só entra o que sobe de faixa, e a maioria das
condições fica sem ganho nenhum.</p>

<h3>A pergunta do escopo, e o movimento de subtrair</h3>
<p>As três classes são todas sobre <b>falta</b>: apontam o que não está lá.
Excesso não tinha classe, e é o defeito mais comum de projeto ambicioso, além
de ser o que uma banca de qualificação diz com mais frequência. Então ela conta
as frentes, uma a uma: quantas coletas distintas o projeto promete, quantas
exigem acesso de terceiro, quantas exigem campo, comitê ou deslocamento.</p>
<p>E aí faz o movimento que a régua não sabia fazer, que é <strong>nomear a
frente que pode sair</strong>, por dois critérios que ela confere separados: o
de <b>necessidade</b> (que frente sai sem que a pergunta morra) e o de
<b>custo</b> (que frente consome mais tempo, acesso e autorização de terceiro),
que é o que uma banca usa primeiro. Quando os dois apontam para frentes
diferentes, ela diz as duas e diz qual critério levou a cada uma, porque a
escolha depende de coisas que o documento não informa. Se nenhuma puder sair, o
que se corta é a pergunta.</p>

<h3>A bibliografia se avalia por conteúdo, não por forma</h3>
<p>Editora trocada, ano divergente entre o texto e a lista, sobrenome grafado
de dois jeitos: nada disso é achado. É revisão de texto, e num parecer de
banca desloca a atenção do que decide, além de ser o erro mais comum de
qualquer bibliografia escrita por gente. O que fica é conteúdo: se as obras
existem, se a lista dá conta da pergunta, se afirmação central se apoia em obra
ausente da lista, e o autor nomeado uma vez e nunca retomado.</p>

<h2 id="ia">Os indícios de IA se graduam, e não se contam</h2>

<div class="nota" style="border-left-color: var(--warn);">
  <p><strong>Esta dimensão não tem nota</strong>, e a correção veio de um
  defeito medido: enquanto ela pontuava, <b>não ter marca valia 10</b>, e
  nenhuma outra dimensão dá 10 por ausência de achado. A falta de defeito
  estava sendo premiada como excelência.</p>
  <p>No lugar da nota, cinco níveis: <b>indícios fortes (uso abusivo)</b>, quando
  as marcas mostram na página que o texto não foi controlado por quem o assina;
  <b>indícios fortes</b>, quando são várias e ainda compatíveis com pressa ou
  revisão mal feita; <b>indícios médios</b>, quando se somam sem que nenhuma
  sozinha alcance o que o documento afirma; <b>indícios fracos</b>; e <b>não há
  indícios</b>. O nível não
  vira condição e não entra em nota nenhuma: viaja ao lado, e quem decide o
  que fazer com ele é a banca.</p>
</div>

<p>Ela não diz que o projeto foi gerado por inteligência artificial, não
insinua e não pede confissão, e a razão não é delicadeza: <strong>a marca é
probabilística, e um candidato reprovado por ela não teria como se defender de
uma objeção que ninguém enuncia.</strong> O que ela relata está na página e se
conta: a simetria repetida entre seções sem relação entre si, a seção que não
entrega o que o título promete, a subdivisão que sai sem que nada mude, e a
fluência uniforme com afirmação que excede o material previsto.</p>
<p><b>Duas marcas saíram nos testes de 03/09/2026, e o registro fica.</b> A
referência arrolada e não citada, que num projeto de lista única é o estado
normal; e a mesma obra com dados diferentes em dois pontos, que é o erro humano
mais comum de uma bibliografia. <strong>Marca que dispara em escrita normal é
pior que marca nenhuma</strong>, porque produz achado onde não há nada e gasta
a confiança de quem lê o resto. São quatro marcas, e não cinco.</p>

<div class="nota">
  <p><strong>Referência não encontrada não é obra inexistente.</strong> Com
  busca, ela confere se as obras existem, porque projeto escrito com IA e sem
  revisão traz referência inventada em ABNT impecável. Mas busca que falha é
  busca que falha, e há obra real fora das bases. Ela escreve que não
  encontrou, com os termos que usou, e manda conferir; nunca que o candidato
  fabricou. Sem busca, diz que não conferiu, e não julga por memória.</p>
</div>

<h2 id="descricao">Cada dimensão sai em dois parágrafos</h2>

<p>Cada um abre pelo seu rótulo. O primeiro, <b>Descrição</b>, descreve o que o projeto traz naquela dimensão, com os
tópicos onde cada coisa está: a pergunta como o projeto a enuncia, a fonte que
ele diz que vai usar, o recorte, as categorias que nomeia, os autores que
mobiliza e para quê, o que promete entregar. O segundo <b>avalia</b>, com o
achado, o tópico, a contagem por classe e a nota.</p>

<p><b>A descrição vem primeiro, e isso não é arrumação.</b> Escrita depois da
avaliação, ela se curva para justificar a nota, e quem lê recebe como descrição
o que já é argumento. Escrita antes, ela é o que a leitura entendeu do
documento, e é contra ela que a avaliação se confere.</p>

<p>No parágrafo descritivo não entra adjetivo de qualidade, em direção nenhuma:
nem frágil, insuficiente ou vago; nem sólido, consistente ou promissor. Quando
não há material, isso também se descreve, e é frase de fato: o projeto não
enuncia pergunta, não nomeia fonte. <b>E a descrição é reconstrução, não
transcrição:</b> sai com as palavras de quem lê e nunca entre aspas, porque
aspas afirmam literalidade. Onde a palavra exata importa, vem o tópico e o
convite a ler.</p>

<div class="nota">
  <p><strong>Por que isto entrou.</strong> Sem a descrição, quem lê o relatório
  não sabe o que está sendo avaliado, e num processo com vinte projetos ninguém
  abre os vinte documentos para descobrir. O relatório passa a bastar como
  apresentação do projeto, e não só como parecer sobre ele.</p>
</div>

<h2 id="lote">Uso em lote, num processo seletivo</h2>

<p>Para ler vinte projetos, ela roda <b>uma vez por projeto</b>, e nunca os
vinte no mesmo contexto. Isso não é limitação a superar: se um modelo lê vinte
seguidos, o sétimo é lido contra a lembrança dos seis anteriores, e o mesmo
defeito recebe nota diferente conforme o que veio antes.</p>

<p>Cada relatório fecha com um <b>bloco de dados</b>, que traz também o
localizador do título (o programa é que copia o título do projeto, porque
título digitado por modelo faz a peça apontar para outro trabalho), e é dele
que a tabela do lote se monta, <b>por um programa e não por um modelo</b>: quem copia vinte
linhas de números troca uma. O programa recusa o relatório cujo bloco não
fecha. <b>E a tabela sai em ordem alfabética</b>: não há média para ordenar, e
a contagem de condições também não ordena, porque duas condições pequenas não
valem menos que uma grande.</p>

<p><b>A saída do lote é um PDF</b>: a tabela comparativa, as contagens da
coorte (só contagens: dizer que a turma tem dificuldade com metodologia seria
afirmação nova sobre uma população) e, depois, cada leitura inteira, uma por
página.</p>

<p><b>Num projeto só, o PDF é outro, e não a tabela com uma linha.</b> Sai a
comparação, que compararia com nada, e saem as contagens da coorte, que com um
projeto são as notas ditas de outro jeito. Entra uma ficha das quatro notas com
o nível dos indícios ao lado, e as três linhas escritas por extenso, cada uma
dizendo o que decide. Depois vem a leitura inteira. <b>A ficha é montada pelo
programa</b> a partir do bloco de dados já conferido, e não redigitada.</p>

<p>O relatório do Miro, que é material de trabalho, sai em <code>.md</code>. O
da Selma sai em PDF porque é peça que o processo recebe pronta, e porque se lê
melhor assim.</p>

<div class="nota" style="border-left-color: var(--deep); background: var(--deep-soft);">
  <p><strong>E o lote traz de graça o controle que falta.</strong> Duas
  leituras independentes do mesmo projeto, em dois ou três do lote, medem o que
  nenhuma leitura isolada mede: se duas leituras chegam à mesma nota. Sem isso,
  a tabela é um conjunto de números cuja estabilidade ninguém verificou.</p>
</div>

<footer>
  <p>Assistente de leitura para projetos de pesquisa, feito por Alexandre
  Araújo Costa, Faculdade de Direito da UnB. Protótipo em fase de testes.</p>
  <p>Feedback para <a href="mailto:alexandrearcos@unb.br">alexandrearcos@unb.br</a>.</p>
</footer>

</div>

<script>
  (function () {
    var ta = document.getElementById('selma');
    var btn = document.getElementById('btn-copiar');
    var medida = document.getElementById('tamanho');
    if (medida && ta) {
      medida.textContent = ta.value.length.toLocaleString('pt-BR') + ' caracteres';
    }
    if (btn && ta) {
      btn.addEventListener('click', function () {
        var antes = btn.textContent;
        function feito() {
          btn.textContent = 'Copiado';
          setTimeout(function () { btn.textContent = antes; }, 1800);
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(ta.value).then(feito, function () {
            ta.select(); feito();
          });
        } else {
          ta.select();
          try { document.execCommand('copy'); feito(); } catch (e) {}
        }
      });
    }
  })();
</script>

<script>
  // a via escolhida mostra so a sua guia, no molde da pagina do Miro
  (function () {
    var bts = Array.prototype.slice.call(document.querySelectorAll(".via-bt"));
    var guias = { chat: "guia-chat", agente: "guia-agente" };
    function mostrar(via) {
      bts.forEach(function (o) {
        o.setAttribute("aria-pressed", String(o.dataset.via === via));
      });
      Object.keys(guias).forEach(function (k) {
        var el = document.getElementById(guias[k]);
        if (el) el.hidden = k !== via;
      });
    }
    bts.forEach(function (b) {
      b.addEventListener("click", function () { mostrar(b.dataset.via); });
    });
    var daUrl = (location.hash || "").replace("#", "");
    // sem escolha na URL, abre o chat: e a via que roda sem instalar nada
    mostrar(Object.prototype.hasOwnProperty.call(guias, daUrl) ? daUrl : "chat");
  })();

  // o botao do pedido do agente, ao lado do botao do prompt
  (function () {
    var btn = document.getElementById('btn-copiar-agente');
    var ta = document.getElementById('pedido-agente');
    if (!btn || !ta) return;
    btn.addEventListener('click', function () {
      function feito() { btn.textContent = 'Copiado';
        setTimeout(function () { btn.textContent = 'Copiar pedido'; }, 1800); }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(ta.value).then(feito, function () {
          ta.select(); feito(); });
      } else { ta.select();
        try { document.execCommand('copy'); feito(); } catch (e) {} }
    });
  })();
</script>
"""


def main():
    modelo = MODELO.read_text(encoding="utf-8")
    m = re.search(r"<style>.*?</style>", modelo, re.S)
    if not m:
        sys.exit("ERRO: nao achei o <style> no modelo da oficina.")
    estilo = m.group(0).replace("textarea#selma", "textarea#selma")

    pagina = CORPO % {"estilo": estilo, "oficina": OFICINA, "miro": MIRO}
    prompt = PROMPT.read_text(encoding="utf-8").strip()
    if "{{PROMPT_SELMA}}" not in pagina:
        sys.exit("ERRO: o marcador do prompt sumiu do corpo.")
    import html
    pagina = pagina.replace("{{PROMPT_SELMA}}", html.escape(prompt, quote=False))

    abre = len(re.findall(r"<div\b", pagina))
    fecha = len(re.findall(r"</div>", pagina))
    if abre != fecha:
        sys.exit("ERRO: divs desequilibradas (%d abre, %d fecha)." % (abre, fecha))

    SAIDA.write_text(pagina, encoding="utf-8")
    print("%s: %d caracteres (prompt: %d) | divs %d = %d"
          % (SAIDA.name, len(pagina), len(prompt), abre, fecha))


if __name__ == "__main__":
    main()
