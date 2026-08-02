"""Registro das atividades conduzidas pelo Miro. Para adicionar uma nova
atividade: criar um módulo contextos/<slug>.py com uma AtividadeMiro (ver
modulo_2_planejamento.py como modelo) e registrá-la abaixo.

modulo_2_planejamento.py serve os dois cursos que usam essa atividade
("Metodologia da Pesquisa" e "Ciência de Dados aplicada à Pesquisa
Empírica em Direito") com um único fluxo — não duas variantes separadas."""

from .modulo_2_planejamento import ATIVIDADE as MODULO_2_PLANEJAMENTO

ATIVIDADES = {
    MODULO_2_PLANEJAMENTO.slug: MODULO_2_PLANEJAMENTO,
}
