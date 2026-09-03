# Miro

Assistente-orientador conversacional que ajuda estudantes a equilibrar os quatro elementos iniciais de um projeto de pesquisa (tema, lacuna, problema, esboço de metodologia e referencial teórico). Usado em três disciplinas da UnB: Metodologia de Pesquisa, Ciência de Dados Aplicada à Pesquisa Empírica em Direito (curso 7 no Canvas) e Ciência de Dados Aplicada à Regulação e Políticas Públicas (curso 4).

Miro não entrega um projeto pronto: conduz uma conversa maiêutica até o estudante formular e sustentar as próprias posições, aponta tensões e lacunas em vez de resolvê-las, e reconhece quando o esboço já está sólido o bastante para seguir adiante.

## Estrutura

- `core.py` — motor genérico: `SYSTEM_PROMPT_BASE` (comportamento do Miro em qualquer atividade), saída estruturada, persistência de conversa e de perfil.
- `contextos/` — uma instância `AtividadeMiro` por atividade (hoje só `modulo_2_planejamento.py`), com as instruções e critérios específicos.
- `leituras.py` — biblioteca de resumos das leituras do curso.
- `app.py` — servidor Flask (rotas HTML para o iframe do Canvas e JSON para testes automatizados).
- `teste_aluno_simulado.py` — personas adversariais para testar o Miro por HTTP.
- `gerar_prompt_portatil.py` + `atualizar_portatil.py` — geram a versão portátil (o texto que se cola em qualquer IA gratuita) a partir do mesmo código-fonte de `core.py`/`contextos/`, para as duas versões nunca divergirem. **Nunca editar `prompt_portatil_modulo_2_planejamento.md` ou `pagina_prompt_portatil.html` diretamente** — rodar `atualizar_portatil.py` depois de qualquer mudança em `core.py` ou `contextos/`.
- `fechamentos.py` — as peças de fechamento comuns aos contextos (entrega em bloco de código, nota sobre a conversa, molde do veredito, regras do esboço), compostas por `montar()`. Evita que os dois prompts divirjam.
- `comentar_projeto.py` / `comentar_pdf.py` — põem as sugestões do assistente dentro do arquivo do autor, como comentários, sem tocar numa palavra. O assistente escreve `P014 > texto da sugestão`; quem escreve no arquivo é o programa. **No PDF prefira `comentar_pdf.py`**, que anota o PDF como ele está: converter para `.docx` reconstrói o documento, e reconstrução tem defeito medido (num projeto real, o texto das notas de rodapé saiu como parágrafo do corpo). `--provar` mostra o conferidor reprovando de propósito.
- `relatorio_pdf.py` — para projeto que chega em PDF: monta o relatório do assistente **em PDF**, com o trecho de cada item copiado do projeto pelo programa e conferido palavra a palavra contra a origem. O Miro trabalha com `.docx` e `.md`; o PDF recebe relatório ou comentários, e não conversão.
- `pdf_para_docx.py` — só para quem precisa mesmo do `.docx`. Preserva o texto palavra por palavra e confere isso; perde a formatação fina, as imagens e as tabelas.
- `pagina_prompt_portatil.html` — a página publicada com a versão portátil e botão de copiar (a mesma fonte também vive como [Claude Artifact](https://claude.ai/code/artifact/6912df2d-dc98-40b3-beb8-172219b077bb)).

`conversas_miro/`, `conversas_miro_teste/` e `perfis_projeto/` guardam dados de sessões de alunos reais e ficam fora do controle de versão (`.gitignore`) — nunca sobem para o GitHub.

## Uso portátil

Para quem não vai rodar o servidor Flask: copie o conteúdo de `prompt_portatil_modulo_2_planejamento.md` (ou acesse a [página publicada](https://claude.ai/code/artifact/6912df2d-dc98-40b3-beb8-172219b077bb)) e cole como primeira mensagem em qualquer assistente de IA gratuito.

## Autoria

Concepção, critérios e prompts: Prof. Alexandre Araújo Costa, Universidade de Brasília. Desenvolvido com apoio de modelos Claude (Anthropic) no Claude Code.

Abordagem experimental, em fase de testes.
