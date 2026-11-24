"""Sono: fusão de intervalos sobrepostos antes de somar."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from .modelos import Intervalo


def fundir(intervalos: list[Intervalo]) -> list[Intervalo]:
    """Une intervalos que se sobrepõem ou se tocam."""
    ordenados = sorted(intervalos, key=lambda i: (i.inicio, i.fim))
    saida: list[Intervalo] = []
    for iv in ordenados:
        if saida and iv.inicio <= saida[-1].fim:
            if iv.fim > saida[-1].fim:
                saida[-1] = Intervalo(saida[-1].inicio, iv.fim)
        else:
            saida.append(iv)
    return saida


def chave_da_noite(iv: Intervalo) -> date:
    """Noite identificada pelo dia em que se acorda: início + 6 h cai nesse dia."""
    return (iv.inicio + timedelta(hours=6)).date()


def minutos_por_noite(intervalos: list[Intervalo]) -> dict[date, float]:
    """Agrupa por noite, funde dentro de cada noite e soma os minutos."""
    grupos: dict[date, list[Intervalo]] = defaultdict(list)
    for iv in intervalos:
        grupos[chave_da_noite(iv)].append(iv)
    return {
        noite: sum(i.minutos for i in fundir(ivs)) for noite, ivs in grupos.items()
    }
