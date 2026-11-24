"""Linha de comando: python -m painel_saude --apple export.zip [--zepp sport.csv]."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .apple import ler_apple
from .config import Config, carregar_toml
from .duplicidade import deduplicar
from .relatorio import montar_html
from .semanas import agregar
from .zepp import ler_zepp


def _faixa(texto: str) -> tuple[float, float]:
    a, b = texto.replace(",", ".").split("-")
    return float(a), float(b)


def criar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="painel_saude",
        description="Gera um painel HTML local a partir do Apple Health e, opcionalmente, do Zepp.",
    )
    p.add_argument("--apple", required=True, help="export.zip ou export.xml do Apple Health")
    p.add_argument("--zepp", help="CSV, pasta ou zip do export do Zepp (opcional)")
    p.add_argument("--saida", default="painel.html", help="arquivo HTML de saída")
    p.add_argument("--config", help="arquivo TOML com os parâmetros")
    p.add_argument("--fc-max", type=float, help="frequência cardíaca máxima, em bpm")
    p.add_argument("--zona2", type=_faixa, metavar="BAIXO-ALTO",
                   help="faixa de zona 2 em bpm, no lugar da calculada pela FC máxima")
    p.add_argument("--min-generica", type=float,
                   help="minutos mínimos para uma atividade genérica secundária contar")
    p.add_argument("--cobertura-baixa", type=float, help="limite de cobertura baixa, em %%")
    p.add_argument("--fuso", type=float, help="fuso em horas relativo ao UTC, ex.: -3")
    p.add_argument("--titulo", help="título do painel")
    return p


def main(argv: list[str] | None = None) -> int:
    args = criar_parser().parse_args(argv)
    cfg = carregar_toml(args.config) if args.config else Config()
    cfg = cfg.com(
        fc_max=args.fc_max,
        zona2_bpm=args.zona2,
        min_generica_min=args.min_generica,
        cobertura_baixa_pct=args.cobertura_baixa,
        fuso_horas=args.fuso,
        titulo=args.titulo,
    )

    treinos, fc, sono = ler_apple(args.apple, cfg)
    if args.zepp:
        treinos += ler_zepp(args.zepp, cfg)
    mantidos, contagem = deduplicar(treinos, cfg)
    semanas = agregar(mantidos, fc, sono, cfg)

    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(montar_html(semanas, contagem, cfg), encoding="utf-8")
    print(
        f"{contagem['lidos']} treinos lidos, {contagem['mantidos']} mantidos; "
        f"{len(fc)} amostras de FC; {len(semanas)} semanas. Gerado: {saida}",
        file=sys.stderr,
    )
    return 0
