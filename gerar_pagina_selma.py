#!/usr/bin/env python3
"""
Gera pagina_selma.html, a pagina propria da Selma.

    python gerar_pagina_selma.py

POR QUE ELA EXISTE. O Miro e o Nelson tem pagina propria, com o prompt e o
botao de copiar; a Selma so vivia dentro da pagina da Oficina. Agora ela
tem a dela, e a oficina passa a apontar para ca, como aponta para os
outros.

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

CORPO = """<title>Selma — leitura de banca de seleção</title>

%(estilo)s

<div class="wrap">

<header>
  <p class="eyebrow">Universidade de Brasília · Seleção e qualificação ·
  <a href="%(oficina)s">Oficina de Projetos</a></p>
  <h1>Selma</h1>
  <p class="lead"><strong>Selma lê um projeto de pesquisa como uma banca de
  seleção o leria</strong>, e devolve um relatório de uma página, com nota por
  dimensão. Não há conversa: ela lê, classifica e entrega. O
  <a href="%(miro)s">Miro</a> trabalha com quem escreve, e não julga ninguém;
  ela faz a leitura oposta, que é a que decide.</p>
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
    <li><strong>Problema.</strong> Há pergunta, ou só tema? Ela é respondível
    com o que o projeto se propõe? E é circular, isto é, a resposta já está
    escrita na justificativa?</li>
    <li><strong>Metodologia e teoria</strong>, lidas juntas. A fonte, as
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
    página, e o que elas custam.</li>
  </ol>
</div>

<p><strong>Se vier um edital junto com o projeto, são os critérios dele que
valem</strong>, na ordem e com os nomes que ele usa, porque quem avalia
preenche uma ficha e relatório organizado por outros critérios obriga a banca
a traduzir cada achado. O que o edital pontua e ela não lê (currículo,
entrevista, proficiência) fica de fora, sem nota inventada, e ela diz que a
média é só sobre o que pôde avaliar.</p>

<h2 id="nota">A nota sai de uma contagem</h2>

<p>Cada achado se classifica em uma de três classes, com o teste feito
<strong>com o defeito no lugar</strong>, e não depois de imaginá-lo
consertado. <b>Impeditivo:</b> do jeito que está, a dimensão não entrega o que
promete, e nenhum prazo resolve. <b>Bloqueio de partida:</b> a dimensão
entrega, e há coisa a resolver antes de começar, que se resolve fazendo.
<b>Localizado:</b> resolve-se no caminho. Depois a contagem manda na faixa e
no dígito, e o relatório mostra a conta.</p>

<p>Duas regras de subida corrigem o que a contagem sozinha não veria, e as
duas se contam na página: defeito que aparece em <b>mais da metade das
subdivisões</b> de uma seção sobe uma classe, e achado que atinge afirmação
que o projeto repete em <b>três ou mais tópicos</b> também sobe. A subida é de
uma classe só.</p>

<h3>Duas linhas, e elas medem coisas diferentes</h3>
<p><b>A aprovação na seleção está na média 7.</b> Ali a banca ordena
candidatos, e compensar um critério com outro é o que ela de fato faz.
<b>A recomendação de levar à qualificação não sai da média:</b> exige que
nenhuma dimensão esteja abaixo de 7, porque a pergunta ali é se o desenho,
executado como está escrito, produz a resposta, e para isso não há
compensação. A conta mostra por quê: 10, 10, 10, 10 e 2 dá média 8,4, num
projeto com uma dimensão sem material nenhum.</p>

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

<h3>A pergunta do escopo, e o movimento de subtrair</h3>
<p>As três classes são todas sobre <b>falta</b>: apontam o que não está lá.
Excesso não tinha classe, e é o defeito mais comum de projeto ambicioso, além
de ser o que uma banca de qualificação diz com mais frequência. Então ela conta
as frentes, uma a uma: quantas coletas distintas o projeto promete, quantas
exigem acesso de terceiro, quantas exigem campo, comitê ou deslocamento.</p>
<p>E aí faz o movimento que a régua não sabia fazer, que é <strong>nomear a
frente que pode sair sem que a pergunta morra</strong>, dizendo por que aquela
e não outra. Se nenhuma puder sair, isso também é achado, e é pior: quer dizer
que a pergunta, como está formulada, exige mais do que o prazo comporta, e o
que se corta então é a pergunta.</p>

<h2 id="ia">Os indícios de IA se relatam, e não se acusam</h2>

<p>Ela não diz que o projeto foi gerado por inteligência artificial, não
insinua e não pede confissão, e a razão não é delicadeza: <strong>a marca é
probabilística, e um candidato reprovado por ela não teria como se defender de
uma objeção que ninguém enuncia.</strong> O que ela relata está na página e se
conta: a simetria repetida entre seções sem relação entre si, a seção que não
entrega o que o título promete, a subdivisão que sai sem que nada mude, e a
mesma obra com dados diferentes em dois pontos do documento. <b>Obra arrolada
e não citada no texto não entra</b>, quando o projeto tem lista única: ali a
bibliografia indica também o que será integrado ao trabalho, e lista maior que
o uso é o estado esperado. O defeito só existe quando há duas listas, uma
delas apresentando-se como o que foi de fato citado.</p>

<div class="nota">
  <p><strong>Referência não encontrada não é obra inexistente.</strong> Com
  busca, ela confere se as obras existem, porque projeto escrito com IA e sem
  revisão traz referência inventada em ABNT impecável. Mas busca que falha é
  busca que falha, e há obra real fora das bases. Ela escreve que não
  encontrou, com os termos que usou, e manda conferir; nunca que o candidato
  fabricou. Sem busca, diz que não conferiu, e não julga por memória.</p>
</div>

<h2 id="lote">Uso em lote, num processo seletivo</h2>

<p>Para ler vinte projetos, ela roda <b>uma vez por projeto</b>, e nunca os
vinte no mesmo contexto. Isso não é limitação a superar: se um modelo lê vinte
seguidos, o sétimo é lido contra a lembrança dos seis anteriores, e o mesmo
defeito recebe nota diferente conforme o que veio antes.</p>

<p>Cada relatório fecha com um <b>bloco de dados</b>, e é dele que a tabela do
lote se monta, <b>por um programa e não por um modelo</b>: quem copia vinte
linhas de números troca uma. O programa recusa o relatório cujo bloco não
fecha. <b>E a tabela sai em ordem alfabética, não por média</b>, porque tabela
ordenada por média é um ranking, e a média foi feita para dizer de que lado da
linha o projeto caiu, não para ordenar.</p>

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
