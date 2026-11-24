"""Leitura do export do Apple Health (export.zip ou export.xml), em fluxo."""

from __future__ import annotations

import io
import zipfile
from contextlib import contextmanager
from pathlib import Path
from xml.etree import ElementTree as ET

from .config import Config
from .datas import ler_data
from .modelos import Intervalo, Treino

TIPO_FC = "HKQuantityTypeIdentifierHeartRate"
TIPO_SONO = "HKCategoryTypeIdentifierSleepAnalysis"
TIPO_GENERICO = "HKWorkoutActivityTypeOther"
VALORES_FORA_DO_SONO = ("InBed", "Awake")


@contextmanager
def abrir_export(caminho: str | Path):
    caminho = Path(caminho)
    if caminho.suffix.lower() == ".zip":
        with zipfile.ZipFile(caminho) as z:
            nomes = [n for n in z.namelist() if Path(n).name == "export.xml"]
            if not nomes:
                raise FileNotFoundError("export.xml não encontrado dentro do zip")
            with z.open(nomes[0]) as f:
                yield io.BufferedReader(f)
    else:
        with open(caminho, "rb") as f:
            yield f


def dormindo(valor: str) -> bool:
    """True para qualquer estágio de sono. Ficar na cama e acordado não contam."""
    resto = valor.replace("HKCategoryValueSleepAnalysis", "")
    return resto != "" and resto not in VALORES_FORA_DO_SONO


def eh_relogio(nome_fonte: str, cfg: Config) -> bool:
    nome = nome_fonte.lower()
    return any(p in nome for p in cfg.palavras_relogio)


def ler_apple(caminho: str | Path, cfg: Config):
    """Devolve (treinos, amostras_fc, sono).

    amostras_fc: lista de (datetime, bpm). sono: lista de Intervalo.
    """
    treinos: list[Treino] = []
    fc: list[tuple] = []
    sono: list[Intervalo] = []
    with abrir_export(caminho) as f:
        for _, elem in ET.iterparse(f, events=("end",)):
            tag = elem.tag
            if tag == "Record":
                tipo = elem.get("type")
                if tipo == TIPO_FC:
                    try:
                        bpm = float(elem.get("value"))
                    except (TypeError, ValueError):
                        bpm = None
                    if bpm:
                        fc.append((ler_data(elem.get("startDate"), cfg.fuso_horas), bpm))
                elif tipo == TIPO_SONO and dormindo(elem.get("value", "")):
                    ini = ler_data(elem.get("startDate"), cfg.fuso_horas)
                    fim = ler_data(elem.get("endDate"), cfg.fuso_horas)
                    if fim > ini:
                        sono.append(Intervalo(ini, fim))
            elif tag == "Workout":
                ini = ler_data(elem.get("startDate"), cfg.fuso_horas)
                fim = ler_data(elem.get("endDate"), cfg.fuso_horas)
                tipo = elem.get("workoutActivityType", TIPO_GENERICO)
                fonte = elem.get("sourceName", "")
                if fim > ini:
                    treinos.append(
                        Treino(
                            inicio=ini,
                            fim=fim,
                            tipo=tipo.replace("HKWorkoutActivityType", ""),
                            origem=fonte,
                            principal=eh_relogio(fonte, cfg),
                            generico=(tipo == TIPO_GENERICO),
                        )
                    )
            if tag in ("Record", "Workout", "Correlation"):
                elem.clear()
    fc.sort(key=lambda x: x[0])
    return treinos, fc, sono
