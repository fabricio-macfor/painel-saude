"""Tipos simples usados em todo o projeto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Treino:
    inicio: datetime
    fim: datetime
    tipo: str
    origem: str
    principal: bool  # True quando veio do relógio
    generico: bool  # True para atividade sem tipo definido

    @property
    def minutos(self) -> float:
        return (self.fim - self.inicio).total_seconds() / 60.0


@dataclass(frozen=True)
class Intervalo:
    inicio: datetime
    fim: datetime

    @property
    def minutos(self) -> float:
        return (self.fim - self.inicio).total_seconds() / 60.0
