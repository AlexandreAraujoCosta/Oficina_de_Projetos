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

CORPO = """<title>Selma — leitura de projeto de pesquisa</title>

%(estilo)s

<nav class="indice" aria-label="Índice da página">
  <details class="indice-caixa" id="indice">
    <summary>Índice</summary>
    <div class="indice-lista">
      <a href="#dimensoes">As cinco dimensões</a>
      <a href="#nota">A nota sai de uma contagem</a>
      <a href="#ia">Os indícios de IA</a>
      <a href="#descricao">Dois parágrafos por dimensão</a>
      <a class="grupo" href="#lote">Uso em lote</a>
      <a href="#prompt">O prompt, para colar</a>
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
  <p class="eyebrow"><span class="eb-linha"><a href="https://direito.unb.br/">Faculdade de Direito</a> · <a href="https://www.unb.br/">UnB</a> · <a href="https://pmpd.unb.br/">PMPD</a> · <a href="https://claude.ai/code/artifact/4fe98c90-3461-4d03-8c83-7ba2fe0c1c72">Oficinas</a>: <a href="https://claude.ai/code/artifact/1d29d917-d73f-48b3-9f89-1eaab12cfffd">Projetos</a> · <a href="https://claude.ai/code/artifact/57a0317d-5d0d-48fd-b571-4d7dfb1fe916">Orientação</a> · Formatação</span><span class="eb-linha eb-baixo"><a href="https://claude.ai/code/artifact/6912df2d-dc98-40b3-beb8-172219b077bb">Miro</a> · <span class="eb-atual" aria-current="page">Selma</span></span></p>
  <h1>Selma</h1>
  <p class="lead"><strong>Selma lê um projeto de pesquisa como uma banca o
  leria</strong>, e devolve um relatório curto: o que o projeto traz em cada
  parte, o que cada parte vale, e <strong>que condições ele precisa cumprir
  para ser apresentável a uma banca de qualificação</strong>. Não há conversa:
  ela lê, classifica e entrega. O <a href="%(miro)s">Miro</a> trabalha com quem
  escreve, e não julga ninguém; ela faz a leitura oposta, que é a que
  decide.</p>
</header>

<div class="nota">
  <p><strong>O relatório é escrito para a banca, sempre.</strong> Quem o usa
  para ver o próprio projeto está vendo o que a banca veria, e é só isso que
  ele tem a oferecer: relatório que amacia porque o autor está lendo deixa de
  mostrar o que ele precisa ver.</p>
</div>

<h2 id="dimensoes">As cinco dimensões</h2>

<p class="deck">Sempre as mesmas, sempre na mesma ordem, e todas aparecem no
relatório mesmo quando não há o que apontar, porque dimensão omitida se lê
como dimensão aprovada.</p>

<div class="fluxo">
  <ol>
    <li><strong>Problema e justificativa</strong>, lidos juntos, porque
    pergunta clara e irrelevante não sustenta projeto. Há pergunta, ou só tema?
    Ela é respondível? É circular? E, do outro lado, <b>de que modo enfrentá-la
    justifica o trabalho</b> — que não é a mesma coisa que a importância do
    tema, porque um tema importante justifica qualquer pesquisa sobre ele, e
    portanto nenhuma.</li>
    <li><strong>Metodologia e teoria</strong>, lidas juntas, e a primeira coisa
    é se <b>o método responde à pergunta</b>: método suficiente é método
    articulado à pergunta, e não método bem descrito. A fonte, as
    categorias, a operação (contar, classificar, qualificar, comparar,
    interpretar) e a forma do resultado. A proporção entre as duas: método
    rarefeito demais faz a teoria deixar de restringir qualquer conclusão.
    E <b>o escopo</b>: o que o projeto promete cabe no prazo e nas mãos de uma
    pessoa?</li>
    <li><strong>Contribuições e impacto.</strong> O que muda no conhecimento,
    e o que muda na prática, com alguém concreto que decidiria diferente.
    Categoria profissional não é destinatário.</li>
    <li><strong>Bibliografia.</strong> A lista contra o texto, a composição da
    lista, e a existência das obras quando há busca.</li>
    <li><strong>Indícios de uso de IA.</strong> As marcas que se conferem na
    página, e o que elas custam. <b>Esta não tem nota:</b> é graduada em
    quatro níveis, e viaja ao lado das outras.</li>
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

<h3>A terceira pergunta: dá para aprovar com alterações?</h3>
<p>É a que mais rende, e a resposta já está na contagem, sem conta nova:
<strong>as três classes são uma escala de custo de conserto.</strong> Sem
nenhum grave, o projeto é apto, e um projeto com cinco achados leves está
mais perto de ser aprovado do que um com um achado grave só, ainda que as notas
digam o contrário. Com um achado grave, ela diz para cada um o que teria de mudar e
de que tamanho é a mudança: reescrever uma seção é uma coisa, refazer a
pergunta é outra, e só essa última é não apto.</p>
<p>E o relatório fecha com <strong>o que a arguição pode ganhar</strong>: até
três achados que se resolvem com uma resposta boa na banca, cada um com a
dimensão que sobe de faixa se ele responder bem. Só entra o que sobe de faixa;
o resto é pendência e já está no lugar dele.</p>

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
  <p>No lugar da nota, quatro níveis: <b>fortes (uso abusivo)</b>, quando as
  marcas mostram na página que o texto não foi controlado por quem o assina;
  <b>fortes (uso indeterminado)</b>, quando são fortes e ainda compatíveis com
  pressa ou revisão mal feita; <b>leves</b>; e <b>ausentes</b>. O nível não
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
<p><b>Duas marcas saíram nos testes de hoje, e o registro fica.</b> A
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

<h2 id="prompt">O prompt, para colar</h2>

<p>Cabe numa colagem só. Cole o texto, <strong>não o anexe como arquivo</strong>,
e abra uma janela nova: o que já foi dito numa conversa em andamento entra na
leitura sem avisar.</p>

<div class="caixa-prompt">
  <div class="barra">
    <span id="tamanho"></span>
    <button class="copiar" id="btn-copiar" type="button">Copiar prompt</button>
  </div>
  <textarea id="selma" readonly spellcheck="false">{{PROMPT_SELMA}}</textarea>
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
