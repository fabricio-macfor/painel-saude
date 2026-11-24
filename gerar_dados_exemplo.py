#!/usr/bin/env python3
"""Gera exports falsos e realistas (Apple Health e Zepp), com semente fixa.

Tudo aqui é inventado. Saída em dados_exemplo/:
  export.zip        no formato do Apple Health (apple_health_export/export.xml)
  zepp_sport.csv    no formato do Zepp
Use --xml para gravar também o export.xml solto.
"""

from __future__ import annotations

import argparse
import csv
import random
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import quoteattr

SEMENTE = 2026
PRIMEIRA_SEGUNDA = datetime(2026, 6, 1)
SEMANAS = 16
SEM_RELOGIO = {5, 6, 11}  # semanas em que o relógio ficou na gaveta
FC_MAX = 190
FUSO = "-0300"

RELOGIO = "Relógio de Exemplo"
TELEFONE = "Telefone de Exemplo"
TIPOS = ["Running", "Walking", "Cycling"]
TIPOS_ZEPP = {"Running": "Corrida", "Walking": "Caminhada", "Cycling": "Ciclismo"}


def fmt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S ") + FUSO


def registro(tipo, fonte, unidade, ini, fim, valor) -> str:
    return (
        f"<Record type={quoteattr(tipo)} sourceName={quoteattr(fonte)} unit={quoteattr(unidade)} "
        f"creationDate={quoteattr(fmt(fim))} startDate={quoteattr(fmt(ini))} "
        f"endDate={quoteattr(fmt(fim))} value={quoteattr(str(valor))}/>"
    )


def treino_xml(tipo, fonte, ini, fim) -> str:
    dur = round((fim - ini).total_seconds() / 60, 2)
    return (
        f"<Workout workoutActivityType={quoteattr('HKWorkoutActivityType' + tipo)} "
        f"duration={quoteattr(str(dur))} durationUnit=\"min\" sourceName={quoteattr(fonte)} "
        f"creationDate={quoteattr(fmt(fim))} startDate={quoteattr(fmt(ini))} "
        f"endDate={quoteattr(fmt(fim))}/>"
    )


def amostras_fc(rng, ini, fim, alvo_pct):
    """FC com aquecimento, trecho estável com deriva leve e ruído."""
    seg = int((fim - ini).total_seconds())
    saida = []
    alvo = FC_MAX * alvo_pct
    t = 0
    while t < seg:
        subida = min(1.0, t / 420)  # 7 minutos de aquecimento
        base = 90 + (alvo - 90) * subida + 6 * (t / seg)
        valor = round(base + rng.gauss(0, 3))
        saida.append((ini + timedelta(seconds=t), valor))
        t += rng.choice((15, 20, 25))
    return saida


def sono_da_noite(rng, dormir, acordar, relogio_ativo):
    """Lista de (fonte, valor, ini, fim)."""
    itens = []
    if relogio_ativo:
        itens.append((RELOGIO, "InBed", dormir, acordar))
        t = dormir + timedelta(minutes=rng.randint(8, 25))
        estagios = ["Core", "Deep", "Core", "REM"]
        i = 0
        while t < acordar - timedelta(minutes=10):
            est = estagios[i % 4]
            dur = timedelta(minutes=rng.randint(25, 70))
            fim = min(t + dur, acordar)
            itens.append((RELOGIO, "Asleep" + est, t, fim))
            t = fim
            if rng.random() < 0.35 and t < acordar:
                pausa = timedelta(minutes=rng.randint(2, 8))
                itens.append((RELOGIO, "Awake", t, min(t + pausa, acordar)))
                t += pausa
            i += 1
    # O telefone sempre registra a noite inteira, sobrepondo o relógio.
    itens.append((TELEFONE, "InBed", dormir, acordar))
    itens.append((TELEFONE, "AsleepUnspecified", dormir + timedelta(minutes=15), acordar - timedelta(minutes=5)))
    return itens


def gerar(destino: Path, gravar_xml: bool) -> None:
    rng = random.Random(SEMENTE)
    registros: list[str] = []
    treinos_xml: list[str] = []
    zepp_linhas: list[list] = []

    for w in range(SEMANAS):
        segunda = PRIMEIRA_SEGUNDA + timedelta(days=7 * w)
        relogio_ativo = w not in SEM_RELOGIO

        # Sono: 7 noites, algumas sem registro do relógio mesmo em semana ativa.
        for d in range(7):
            dia = segunda + timedelta(days=d)
            dormir = dia - timedelta(hours=1, minutes=rng.randint(0, 80))
            acordar = dia + timedelta(hours=6, minutes=rng.randint(0, 90))
            ativo = relogio_ativo and rng.random() > 0.1
            for fonte, valor, ini, fim in sono_da_noite(rng, dormir, acordar, ativo):
                registros.append(
                    registro("HKCategoryTypeIdentifierSleepAnalysis", fonte, "",
                             ini, fim, "HKCategoryValueSleepAnalysis" + valor)
                )

        # FC de repouso esparsa ao longo do dia, só com relógio.
        if relogio_ativo:
            for d in range(7):
                for hora in range(8, 22, 2):
                    t = segunda + timedelta(days=d, hours=hora, minutes=rng.randint(0, 50))
                    registros.append(registro("HKQuantityTypeIdentifierHeartRate", RELOGIO,
                                              "count/min", t, t, round(rng.gauss(68, 7))))

        # Treinos da semana.
        for d in sorted(rng.sample(range(7), rng.choice((3, 4)))):
            tipo = rng.choice(TIPOS)
            ini = segunda + timedelta(days=d, hours=rng.randint(6, 18), minutes=rng.choice((0, 15, 30, 45)))
            fim = ini + timedelta(minutes=rng.randint(30, 70))
            if relogio_ativo:
                treinos_xml.append(treino_xml(tipo, RELOGIO, ini, fim))
                for t, v in amostras_fc(rng, ini, fim, rng.uniform(0.58, 0.74)):
                    registros.append(registro("HKQuantityTypeIdentifierHeartRate", RELOGIO,
                                              "count/min", t, t, v))
                # O telefone grava o mesmo treino, e o Zepp também (início ligeiramente deslocado).
                treinos_xml.append(treino_xml(tipo, TELEFONE, ini + timedelta(minutes=1), fim))
                zepp_linhas.append([TIPOS_ZEPP[tipo], ini + timedelta(minutes=2), (fim - ini).total_seconds() - 150])
            else:
                # Sem relógio: só o Zepp registrou, e não há amostra de FC no Apple Health.
                zepp_linhas.append([TIPOS_ZEPP[tipo], ini, (fim - ini).total_seconds()])

        # Atividades genéricas do aparelho secundário: uma curta (descartada) e,
        # em algumas semanas, uma longa fora de qualquer treino (mantida).
        dia_g = segunda + timedelta(days=rng.randint(0, 6), hours=20)
        zepp_linhas.append(["", dia_g, 9 * 60])
        if w % 3 == 0:
            ini_g = segunda + timedelta(days=rng.randint(0, 6), hours=4, minutes=30)
            treinos_xml.append(treino_xml("Other", TELEFONE, ini_g, ini_g + timedelta(minutes=35)))

    corpo = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<HealthData locale="pt_BR">',
        "<!-- Dados falsos gerados por gerar_dados_exemplo.py -->",
        *treinos_xml,
        *registros,
        "</HealthData>",
    ]
    xml = "\n".join(corpo) + "\n"

    destino.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino / "export.zip", "w", zipfile.ZIP_DEFLATED) as z:
        info = zipfile.ZipInfo("apple_health_export/export.xml", date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(info, xml.encode("utf-8"))
    if gravar_xml:
        (destino / "export.xml").write_text(xml, encoding="utf-8")

    with open(destino / "zepp_sport.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["type", "startTime", "sportTime(s)", "distance(meter)", "calories(kcal)"])
        for tipo, ini, seg in sorted(zepp_linhas, key=lambda x: x[1]):
            # O Zepp exporta em UTC: o horário local de exemplo é -03:00.
            utc = ini + timedelta(hours=3)
            w.writerow([tipo, utc.strftime("%Y-%m-%d %H:%M:%S") + "+0000", int(seg),
                        int(seg * rng.uniform(2.0, 3.2)), int(seg / 60 * rng.uniform(6, 11))])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--saida", default="dados_exemplo", type=Path)
    p.add_argument("--xml", action="store_true", help="grava também export.xml solto")
    args = p.parse_args()
    gerar(args.saida, args.xml)
    print(f"Dados de exemplo em {args.saida}/")


if __name__ == "__main__":
    main()
