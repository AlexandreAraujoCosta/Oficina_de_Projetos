"""
Biblioteca de leituras do curso — grounding compartilhado entre atividades
do Miro. Cada atividade (em contextos/) referencia leituras daqui por id ou
por tema, em vez de duplicar prosa em cada arquivo de contexto.

Textos de autoria/coautoria do professor (arcos.org.br, dsd.arcos.org.br)
têm resumo completo, já que o uso é livre (autorizado pelo autor). O livro
de Epstein & Martin, "An Introduction to Empirical Legal Research" (não é do
professor), entra só como paráfrase leve da abordagem geral do capítulo,
nunca um resumo detalhado — o objetivo é indicar a leitura, não substituí-la.
Os resumos dos capítulos de Epstein & Martin usados aqui se baseiam na
estrutura e nos temas de cada capítulo, já públicos no próprio programa do
curso (títulos de capítulo e perguntas norteadoras cadastrados no Canvas),
não numa leitura do livro em si.
"""


class Leitura:
    def __init__(self, titulo, autores, modulo, tipo, url, temas, resumo):
        self.titulo = titulo
        self.autores = autores
        self.modulo = modulo  # módulo de origem no curso (onde é indicada)
        self.tipo = tipo  # "obrigatoria" | "sugerida" | "complementar"
        self.url = url
        self.temas = temas  # tags para busca por tema (ver por_tema)
        self.resumo = resumo

    def __str__(self):
        return f'{self.autores}, "{self.titulo}" (M{self.modulo}, {self.tipo}, {self.url}): {self.resumo}'


LEITURAS = {
    "m1_data_science_direito": Leitura(
        titulo="Data Science e Direito: uma introdução",
        autores="Costa, Costa (2020)",
        modulo=1,
        tipo="obrigatoria",
        url="https://arcos.org.br/datascience_e_direito/",
        temas=["descritivo_explicativo_preditivo_prescritivo", "problema"],
        resumo=(
            "Introduz que problemas jurídicos comportam abordagem de dados e "
            "que tipos de decisão podem ser aprimorados por evidência "
            "empírica. Distingue quatro usos de dados em pesquisa jurídica: "
            "descritivo (mapear o que ocorre), explicativo (por que ocorre), "
            "preditivo (o que tende a ocorrer) e prescritivo (o que fazer a "
            "respeito) — útil para o aluno situar que tipo de pergunta seu "
            "problema de pesquisa está fazendo."
        ),
    ),
    "m1_direito_e_pesquisa_cap2": Leitura(
        titulo='"Direito e Pesquisa", Cap. II: Direito e Pesquisa',
        autores="Costa, Fulgêncio, Horta (2024)",
        modulo=1,
        tipo="obrigatoria",
        url="https://arcos.org.br/direito-ciencia/#2-direito-e-pesquisa",
        temas=["dogmatica_vs_empirica", "problema"],
        resumo=(
            "Distingue dogmática jurídica (produção de conhecimento "
            "normativo, tipo parecer) de pesquisa empírica (produção de "
            "conhecimento sobre o que de fato ocorre), e discute em que "
            "condições evidência empírica se torna decisiva para entender "
            "padrões de decisão no Direito. Chave para separar um problema "
            "de pesquisa investigável de uma pergunta normativa pura."
        ),
    ),
    "m1_epstein_cap1": Leitura(
        titulo="An Introduction to Empirical Legal Research — Cap. 1: Some preliminaries",
        autores="Epstein & Martin (2014)",
        modulo=1,
        tipo="sugerida",
        url="https://books.google.com.br/books?id=fPo5BAAAQBAJ",
        temas=["metodologia", "inferencia_causal"],
        resumo=(
            "Capítulo introdutório sobre desenho de pesquisa empírica: "
            "por que a aleatorização fortalece a inferência causal, e que "
            "limitações surgem ao trabalhar com dados observacionais (o "
            "caso mais comum em pesquisa jurídica, em que raramente há "
            "experimento controlado). Leitura recomendada para quem quiser "
            "aprofundar o desenho da metodologia além do esboço geral desta "
            "atividade."
        ),
    ),
    "m2_pesquisa_empirica_direito": Leitura(
        titulo="Pesquisa empírica em direito",
        autores="Costa, Fulgêncio, Horta (2021)",
        modulo=2,
        tipo="obrigatoria",
        url="https://arcos.org.br/pesquisa-empirica-em-direito/",
        temas=["metodologia", "quali_quanti", "generalizacao_amostral"],
        resumo=(
            "Distingue pesquisa experimental de observacional, abordagens "
            "quantitativas e qualitativas (e a possibilidade de combiná-"
            "las), e discute as condições para generalizar conclusões a "
            "partir de amostras."
        ),
    ),
    "m2_projeto_de_pesquisa": Leitura(
        titulo="O projeto de pesquisa",
        autores="Costa, Horta (2021)",
        modulo=2,
        tipo="obrigatoria",
        url="https://arcos.org.br/o-planejamento-da-pesquisa-em-direito/",
        temas=["tema_vs_problema", "referencial_teorico"],
        resumo=(
            "Diferencia TEMA (área ampla de interesse) de PROBLEMA DE "
            "PESQUISA (pergunta específica e investigável), trata de que "
            "tipos de pergunta não podem ser respondidos por uma pesquisa "
            "empírica (perguntas normativas puras, sem dimensão "
            "observável), e define o que é referencial teórico."
        ),
    ),
    "m2_epstein_cap2": Leitura(
        titulo="An Introduction to Empirical Legal Research — Cap. 2: Questions, Theories, Observable Implications",
        autores="Epstein & Martin (2014)",
        modulo=2,
        tipo="sugerida",
        url="https://books.google.com.br/books?id=fPo5BAAAQBAJ",
        temas=["problema", "referencial_teorico"],
        resumo=(
            "Trata de como transformar um problema jurídico amplo numa "
            "pergunta de pesquisa específica e empiricamente investigável, "
            "e de como derivar implicações observáveis de uma teoria para "
            "que ela possa ser confrontada com dados. Leitura recomendada "
            "para quem quiser aprofundar a formulação do problema e do "
            "referencial teórico além do esboço geral desta atividade."
        ),
    ),
    "m3_analise_de_dados": Leitura(
        titulo="Análise de dados",
        autores="Costa, Alexandre (2020)",
        modulo=3,
        tipo="obrigatoria",
        url="https://dsd.arcos.org.br/analise-de-dados/",
        temas=["dado_metadado", "unidade_de_analise", "abordagem_descritiva_inferencial", "metodologia"],
        resumo=(
            "Diferencia dado (informação bruta sobre um objeto específico) "
            "de metadado (classificação/interpretação desse dado); a "
            "escolha da unidade de análise (processo, decisão, tribunal "
            "etc.) depende do fenômeno que se quer investigar. Sobre "
            "abordagens: a estatística descritiva é mais flexível e serve "
            "bem a amostras pequenas (comuns no judiciário brasileiro), "
            "combinando quantitativo com interpretação qualitativa; a "
            "estatística inferencial é mais robusta mas exige amostras "
            "maiores, nem sempre disponíveis. Ambas buscam padrões de "
            "variação, não casos isolados."
        ),
    ),
    "m3_yeung_jurimetria": Leitura(
        titulo="Jurimetria ou Análise Quantitativa de Decisões Judiciais",
        autores="Yeung, Luciana",
        modulo=3,
        tipo="obrigatoria",
        url="http://reedpesquisa.org/wp-content/uploads/2019/04/MACHADO-Mai%CC%81ra-org.-Pesquisar-empiricamente-o-direito.pdf",
        temas=["abordagem_jurimetrica", "problema", "metodologia"],
        resumo=(
            "Caracteriza a abordagem jurimétrica (análise quantitativa de "
            "decisões judiciais) em contraste com leituras dogmáticas "
            "tradicionais, discutindo como transformar uma questão "
            "jurídica ampla em hipóteses empiricamente testáveis, com "
            "variáveis observáveis, sem confundir correlação com "
            "causalidade."
        ),
    ),
    "m3_epstein_cap3": Leitura(
        titulo="An Introduction to Empirical Legal Research — Cap. 3: Measurement",
        autores="Epstein & Martin (2014)",
        modulo=3,
        tipo="sugerida",
        url="https://books.google.com.br/books?id=fPo5BAAAQBAJ",
        temas=["metodologia"],
        resumo=(
            "Trata de como transformar conceitos jurídicos abstratos em "
            "variáveis observáveis sem perder validade substantiva, e que "
            "critérios avaliam se uma medida capta de fato o fenômeno "
            "pretendido (e não um proxy distorcido). Leitura recomendada "
            "para quem for além do esboço geral da metodologia nesta "
            "atividade."
        ),
    ),
    "m4_coleta_de_dados_judiciais": Leitura(
        titulo="Coleta de dados judiciais",
        autores="Costa, Alexandre (2021)",
        modulo=4,
        tipo="obrigatoria",
        url="https://arcos.org.br/coleta-de-dados-judiciais/",
        temas=["geracao_vs_localizacao_de_dados", "vies_de_selecao", "metodologia"],
        resumo=(
            "Diferencia gerar dados novos (observação direta, entrevistas) "
            "de localizar dados já coletados em bancos existentes — a "
            "prioridade prática costuma ser explorar bem os acervos "
            "disponíveis. Define viés de seleção (quando o critério de "
            "escolha dos dados distorce a conclusão, ex.: só analisar casos "
            "emblemáticos) e propõe mitigações: amostragem aleatória, "
            "pesquisa censitária, ampliar/diversificar a amostra, e ajustar "
            "o universo pesquisado aos dados realmente disponíveis — "
            "reconhecendo que pesquisa jurídica raramente elimina o viés "
            "por completo, dado o número reduzido de decisões disponíveis."
        ),
    ),
    "m4_epstein_collecting_data": Leitura(
        titulo="An Introduction to Empirical Legal Research — Part II.4: Collecting Data",
        autores="Epstein & Martin (2014)",
        modulo=4,
        tipo="sugerida",
        url="https://books.google.com.br/books?id=fPo5BAAAQBAJ",
        temas=["vies_de_selecao", "metodologia"],
        resumo=(
            "Aprofunda as questões de viés de seleção e dimensionamento de "
            "amostra tratadas de forma resumida na leitura obrigatória do "
            "Módulo 4. Leitura recomendada para quem quiser ir além do "
            "esboço geral da metodologia nesta atividade."
        ),
    ),
    "m5_labirintos_da_linguagem": Leitura(
        titulo='"Filosofia, Direito e Linguagem" — Cap. 2: Os labirintos da linguagem',
        autores="Costa, Alexandre",
        modulo=5,
        tipo="obrigatoria",
        url="https://arcos.org.br/filosofia-direito-linguagem/#2-os-labirintos-da-linguagem",
        temas=["referencial_teorico", "classificacao"],
        resumo=(
            "Discute como nossa capacidade de categorizar molda a própria "
            "compreensão do mundo: a linguagem não dá acesso direto à "
            "realidade, mas oferece mapas conceituais que simplificam a "
            "complexidade por meio de agrupamentos abstratos, contingentes "
            "e revisáveis. Base filosófica para entender por que a escolha "
            "das categorias de um referencial teórico não é neutra nem "
            "óbvia."
        ),
    ),
    "m5_modelo_de_dados": Leitura(
        titulo="Modelo de Dados",
        autores="Costa, Costa (2021)",
        modulo=5,
        tipo="obrigatoria",
        url="https://arcos.org.br/modelos-de-dados/",
        temas=["referencial_teorico", "metodologia", "classificacao"],
        resumo=(
            "Um modelo de dados organiza informações sobre fenômenos "
            "jurídicos em categorias estruturadas (classes, atributos, "
            "relações), traduzindo conceitos abstratos em estruturas "
            "mensuráveis — tradução que envolve escolhas (o que contar) com "
            "efeito real sobre as conclusões. Alerta que pesquisadores "
            "tendem a herdar categorias 'naturalizadas' da dogmática/"
            "administração judiciária sem questioná-las, o que introduz "
            "distorções; modelos eficazes exigem trabalho conceitual "
            "próprio para equilibrar precisão descritiva e operacionalidade."
        ),
    ),
    "m5_marco_teorico": Leitura(
        titulo="O Marco Teórico das pesquisas em direito",
        autores="Costa, Fulgêncio (2020)",
        modulo=5,
        tipo="complementar",
        url="https://arcos.org.br/o-marco-teorico-das-pesquisas-em-direito/",
        temas=["referencial_teorico"],
        resumo=(
            "Define marco/referencial teórico como o conjunto de "
            "conceitos, classificações e abordagens que orienta a "
            "investigação, permitindo compreender o objeto de forma "
            "estruturada em vez de depender de conhecimento implícito. Não "
            "é sinônimo de revisão bibliográfica (emerge dela); sua "
            "importância varia por tipo de pesquisa (mais central e "
            "elaborado em pesquisas quantitativas explicativas, mais "
            "flexível em estudos qualitativos exploratórios); qualidade "
            "depende de seletividade, profundidade e coerência entre os "
            "conceitos escolhidos, não da quantidade de referências."
        ),
    ),
    "m5_epstein_coding": Leitura(
        titulo="An Introduction to Empirical Legal Research — Part II.5: Coding Data",
        autores="Epstein & Martin (2014)",
        modulo=5,
        tipo="sugerida",
        url="https://books.google.com.br/books?id=fPo5BAAAQBAJ",
        temas=["referencial_teorico", "metodologia", "classificacao"],
        resumo=(
            "Trata de como a codificação transforma conceitos teóricos em "
            "variáveis observáveis, e como decisões de codificação podem "
            "introduzir vieses nos resultados e na inferência. Leitura "
            "recomendada para quem quiser aprofundar a ligação entre "
            "referencial teórico e metodologia além do esboço geral desta "
            "atividade."
        ),
    ),
}


def por_tema(tema):
    return {k: v for k, v in LEITURAS.items() if tema in v.temas}


def formatar_bloco(ids):
    """Monta o bloco de texto (autor, título, resumo) para um conjunto de
    leituras, na ordem dada, pronto para entrar no system prompt de uma
    atividade."""
    linhas = []
    for id_ in ids:
        l = LEITURAS[id_]
        linhas.append(
            f"- [M{l.modulo}, {l.tipo}] {l.autores}, \"{l.titulo}\" ({l.url}): "
            f"{l.resumo}"
        )
    return "\n".join(linhas)
