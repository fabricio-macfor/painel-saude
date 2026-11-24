"""Leitura de datas dos dois formatos, normalizadas para horário sem fuso."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

_ESPACO_ANTES_DO_FUSO = re.compile(r"\s+([+-]\d{2}:?\d{2})$")


def ler_data(texto: str, fuso_horas: float = 0.0) -> datetime:
    """Converte 'AAAA-MM-DD HH:MM:SS -0300' (ou variações) para horário local sem fuso.

    Datas sem fuso explícito são tratadas como UTC.
    """
    t = _ESPACO_ANTES_DO_FUSO.sub(r"\1", texto.strip())
    dt = datetime.fromisoformat(t)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    alvo = timezone(timedelta(hours=fuso_horas))
    return dt.astimezone(alvo).replace(tzinfo=None)


def inicio_da_semana(dt: datetime) -> datetime:
    """Segunda-feira, 00:00, da semana de dt."""
    dia = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return dia - timedelta(days=dia.weekday())
