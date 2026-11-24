"""Minutos de zona 2 e cobertura de frequência cardíaca, a partir de amostras brutas.

O export do Apple Health não traz zona. Aqui cada treino é dividido em minutos
inteiros; um minuto "tem amostra" se houver ao menos uma leitura de FC nele, e conta
como zona 2 se a média das leituras do minuto cair dentro da faixa.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from datetime import timedelta

from .modelos import Treino


def minutos_do_treino(
    treino: Treino,
    tempos: list,
    bpms: list[float],
    faixa: tuple[float, float],
) -> tuple[int, int, int]:
    """Devolve (minutos_totais, minutos_com_amostra, minutos_em_zona2).

    tempos deve estar ordenado e alinhado a bpms. Faixa inclusiva nas duas pontas.
    """
    baixo, alto = faixa
    total = max(1, math.ceil((treino.fim - treino.inicio).total_seconds() / 60.0))
    cobertos = 0
    zona2 = 0
    for i in range(total):
        ini = treino.inicio + timedelta(minutes=i)
        fim = min(ini + timedelta(minutes=1), treino.fim)
        a = bisect_left(tempos, ini)
        b = bisect_left(tempos, fim)
        if b > a:
            cobertos += 1
            media = sum(bpms[a:b]) / (b - a)
            if baixo <= media <= alto:
                zona2 += 1
    return total, cobertos, zona2
