"""Leitura opcional do export do Zepp (CSV de atividades, arquivo, pasta ou zip)."""

from __future__ import annotations

import csv
import io
import zipfile
from datetime import timedelta
from pathlib import Path

from .config import Config
from .datas import ler_data
from .modelos import Treino

COLUNAS_INICIO = ("startTime", "start_time", "inicio")
COLUNAS_DURACAO = ("sportTime(s)", "sportTime", "duration", "duracao")
COLUNAS_TIPO = ("type", "tipo", "sport")
TIPOS_GENERICOS = ("", "0", "other", "outro", "generic", "generico", "genérico")


def _coluna(linha: dict, candidatas) -> str | None:
    for c in candidatas:
        if c in linha:
            return linha[c]
    return None


def _linhas_csv(texto: str):
    leitor = csv.DictReader(io.StringIO(texto))
    if not leitor.fieldnames:
        return
    campos = [c.strip() for c in leitor.fieldnames]
    if not any(c in campos for c in COLUNAS_INICIO):
        return  # CSV de outro assunto (sono, passos etc.)
    leitor.fieldnames = campos
    yield from leitor


def _textos(caminho: Path):
    if caminho.is_dir():
        for p in sorted(caminho.rglob("*.csv")):
            yield p.read_text(encoding="utf-8-sig")
    elif caminho.suffix.lower() == ".zip":
        with zipfile.ZipFile(caminho) as z:
            for n in sorted(z.namelist()):
                if n.lower().endswith(".csv"):
                    yield z.read(n).decode("utf-8-sig")
    else:
        yield caminho.read_text(encoding="utf-8-sig")


def ler_zepp(caminho: str | Path, cfg: Config) -> list[Treino]:
    treinos: list[Treino] = []
    for texto in _textos(Path(caminho)):
        for linha in _linhas_csv(texto):
            inicio_txt = _coluna(linha, COLUNAS_INICIO)
            dur_txt = _coluna(linha, COLUNAS_DURACAO)
            if not inicio_txt or not dur_txt:
                continue
            try:
                inicio = ler_data(inicio_txt, cfg.fuso_horas)
                segundos = float(dur_txt)
            except ValueError:
                continue
            if segundos <= 0:
                continue
            tipo = (_coluna(linha, COLUNAS_TIPO) or "").strip()
            treinos.append(
                Treino(
                    inicio=inicio,
                    fim=inicio + timedelta(seconds=segundos),
                    tipo=tipo or "Outro",
                    origem="Zepp",
                    principal=False,
                    generico=tipo.lower() in TIPOS_GENERICOS,
                )
            )
    return treinos
