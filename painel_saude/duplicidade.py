"""Remoção de treinos duplicados entre o relógio e aparelhos secundários."""

from __future__ import annotations

from .config import Config
from .modelos import Treino


def sobrepoe(a: Treino, b: Treino) -> bool:
    return a.inicio < b.fim and b.inicio < a.fim


def deduplicar(treinos: list[Treino], cfg: Config) -> tuple[list[Treino], dict]:
    """Aplica as regras e devolve (treinos_mantidos, contagens).

    1. Todo treino do relógio fica.
    2. Treino específico de aparelho secundário fica se não se sobrepõe a nenhum já mantido.
    3. Atividade genérica de aparelho secundário só fica se não se sobrepõe a nenhum
       já mantido e dura pelo menos cfg.min_generica_min minutos.
    """
    principais = sorted((t for t in treinos if t.principal), key=lambda t: t.inicio)
    secundarios = [t for t in treinos if not t.principal]
    # Específicos primeiro, para que um genérico nunca tire o lugar de um específico.
    secundarios.sort(key=lambda t: (t.generico, t.inicio, -t.minutos))

    mantidos = list(principais)
    contagem = {"lidos": len(treinos), "duplicados": 0, "genericos_curtos": 0}
    for t in secundarios:
        if any(sobrepoe(t, m) for m in mantidos):
            contagem["duplicados"] += 1
            continue
        if t.generico and t.minutos < cfg.min_generica_min:
            contagem["genericos_curtos"] += 1
            continue
        mantidos.append(t)
    mantidos.sort(key=lambda t: t.inicio)
    contagem["mantidos"] = len(mantidos)
    return mantidos, contagem
