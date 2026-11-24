"""Agregação semanal (semanas de segunda a domingo)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from .config import Config
from .datas import inicio_da_semana
from .modelos import Intervalo, Treino
from .sono import minutos_por_noite
from .zona2 import minutos_do_treino


@dataclass
class Semana:
    inicio: datetime
    treinos: int = 0
    min_treino: int = 0
    min_com_fc: int = 0
    min_zona2: int = 0
    sono_media_h: float | None = None
    noites: int = 0

    @property
    def cobertura_pct(self) -> float | None:
        if self.min_treino == 0:
            return None
        return 100.0 * self.min_com_fc / self.min_treino


def agregar(
    treinos: list[Treino],
    amostras_fc: list[tuple],
    sono: list[Intervalo],
    cfg: Config,
) -> list[Semana]:
    tempos = [t for t, _ in amostras_fc]
    bpms = [b for _, b in amostras_fc]
    faixa = cfg.faixa_zona2

    semanas: dict[datetime, Semana] = {}

    def da_semana(dt: datetime) -> Semana:
        ini = inicio_da_semana(dt)
        if ini not in semanas:
            semanas[ini] = Semana(inicio=ini)
        return semanas[ini]

    for t in treinos:
        s = da_semana(t.inicio)
        total, cobertos, z2 = minutos_do_treino(t, tempos, bpms, faixa)
        s.treinos += 1
        s.min_treino += total
        s.min_com_fc += cobertos
        s.min_zona2 += z2

    noites = minutos_por_noite(sono)
    por_semana: dict[datetime, list[float]] = defaultdict(list)
    for dia, minutos in noites.items():
        dt = datetime(dia.year, dia.month, dia.day)
        da_semana(dt)
        por_semana[inicio_da_semana(dt)].append(minutos)
    for ini, valores in por_semana.items():
        semanas[ini].noites = len(valores)
        semanas[ini].sono_media_h = sum(valores) / len(valores) / 60.0

    if not semanas:
        return []
    # Semanas sem nenhum dado entram vazias, para o gráfico não esconder buracos.
    primeira, ultima = min(semanas), max(semanas)
    atual = primeira
    while atual <= ultima:
        semanas.setdefault(atual, Semana(inicio=atual))
        atual += timedelta(days=7)
    return [semanas[k] for k in sorted(semanas)]
