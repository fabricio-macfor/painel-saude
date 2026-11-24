"""Configuração com padrões neutros. Tudo pode ser trocado por TOML ou pela linha de comando."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, replace
from pathlib import Path


@dataclass(frozen=True)
class Config:
    # Frequência cardíaca máxima informada por quem usa. O padrão é só um ponto de partida.
    fc_max: float = 190.0
    # Faixa de zona 2 como porcentagem da FC máxima (padrão genérico, ajustável).
    zona2_pct_min: float = 60.0
    zona2_pct_max: float = 70.0
    # Se informada, a faixa em bpm substitui a calculada pela FC máxima.
    zona2_bpm: tuple[float, float] | None = None
    # Atividade genérica de aparelho secundário só conta se durar pelo menos isto.
    min_generica_min: float = 20.0
    # Abaixo desta cobertura de FC a semana é marcada como "cobertura baixa".
    cobertura_baixa_pct: float = 50.0
    # Trechos do nome da fonte que identificam o relógio principal.
    palavras_relogio: tuple[str, ...] = ("watch", "relógio", "relogio")
    # Fuso (em horas, relativo ao UTC) usado para alinhar todas as datas.
    fuso_horas: float = 0.0
    titulo: str = "Painel de saúde"

    @property
    def faixa_zona2(self) -> tuple[float, float]:
        if self.zona2_bpm is not None:
            return self.zona2_bpm
        return (
            self.fc_max * self.zona2_pct_min / 100.0,
            self.fc_max * self.zona2_pct_max / 100.0,
        )

    def com(self, **mudancas) -> "Config":
        return replace(self, **{k: v for k, v in mudancas.items() if v is not None})


def carregar_toml(caminho: str | Path) -> Config:
    with open(caminho, "rb") as f:
        dados = tomllib.load(f)
    campos = {}
    for chave, valor in dados.items():
        if chave == "zona2_bpm":
            campos[chave] = (float(valor[0]), float(valor[1]))
        elif chave == "palavras_relogio":
            campos[chave] = tuple(str(v).lower() for v in valor)
        elif chave == "titulo":
            campos[chave] = str(valor)
        elif chave in Config.__dataclass_fields__:
            campos[chave] = float(valor)
        else:
            raise ValueError(f"Chave desconhecida na configuração: {chave}")
    return Config(**campos)
