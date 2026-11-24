"""Gráficos SVG simples, gerados por código, sem biblioteca e sem rede."""

from __future__ import annotations

import math
from html import escape

LARGURA, ALTURA = 760, 240
ME, MD, MS, MI = 46, 12, 14, 34  # margens


def formatar(valor: float, casas: int = 0) -> str:
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def maximo_bonito(v: float) -> float:
    if v <= 0:
        return 1.0
    exp = 10 ** math.floor(math.log10(v))
    for m in (1, 2, 2.5, 5, 10):
        if v <= m * exp:
            return m * exp
    return 10 * exp


def _moldura(uid: str, titulo: str, maximo: float, unidade: str, rotulos: list[str]):
    larg = LARGURA - ME - MD
    alt = ALTURA - MS - MI
    partes = [
        f'<svg viewBox="0 0 {LARGURA} {ALTURA}" role="img" aria-label="{escape(titulo)}" '
        f'class="grafico" preserveAspectRatio="xMidYMid meet">',
        f'<defs><pattern id="hach-{uid}" width="6" height="6" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(45)"><rect width="6" height="6" class="hach-fundo"/>'
        f'<line x1="0" y1="0" x2="0" y2="6" class="hach-traco" stroke-width="2.4"/></pattern></defs>',
    ]
    for i in range(5):
        y = MS + alt - alt * i / 4
        valor = maximo * i / 4
        partes.append(f'<line x1="{ME}" y1="{y:.1f}" x2="{LARGURA - MD}" y2="{y:.1f}" class="grade"/>')
        partes.append(
            f'<text x="{ME - 6}" y="{y + 4:.1f}" class="eixo" text-anchor="end">'
            f"{formatar(valor, 1 if maximo <= 10 else 0)}</text>"
        )
    n = len(rotulos)
    passo = max(1, math.ceil(n / 12))
    for i, r in enumerate(rotulos):
        if i % passo:
            continue
        x = ME + larg * (i + 0.5) / n
        partes.append(
            f'<text x="{x:.1f}" y="{ALTURA - MI + 16}" class="eixo" text-anchor="middle">{escape(r)}</text>'
        )
    partes.append(f'<text x="{ME}" y="9" class="eixo">{escape(unidade)}</text>')
    return partes, larg, alt


def barras(
    uid: str,
    titulo: str,
    rotulos: list[str],
    valores: list[float | None],
    unidade: str,
    maximo: float | None = None,
    hachurar: list[bool] | None = None,
) -> str:
    """Barras por semana. Barras marcadas em hachurar usam padrão listrado."""
    topo = maximo if maximo is not None else maximo_bonito(max([v or 0 for v in valores] + [0]))
    partes, larg, alt = _moldura(uid, titulo, topo, unidade, rotulos)
    n = len(valores)
    folga = larg / n
    largura_barra = max(2.0, folga * 0.7)
    for i, v in enumerate(valores):
        if v is None:
            continue
        h = alt * min(v, topo) / topo
        x = ME + folga * i + (folga - largura_barra) / 2
        y = MS + alt - h
        if hachurar and hachurar[i]:
            estilo = f'fill="url(#hach-{uid})" class="barra-hach"'
        else:
            estilo = 'class="barra"'
        partes.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{largura_barra:.1f}" height="{max(h, 0):.1f}" '
            f'{estilo}><title>{escape(rotulos[i])}: {formatar(v, 1)} {escape(unidade)}</title></rect>'
        )
    partes.append("</svg>")
    return "".join(partes)


def linha(
    uid: str,
    titulo: str,
    rotulos: list[str],
    valores: list[float | None],
    unidade: str,
    maximo: float | None = None,
) -> str:
    """Linha com pontos. Semanas sem dado quebram a linha em vez de virar zero."""
    topo = maximo if maximo is not None else maximo_bonito(max([v or 0 for v in valores] + [0]))
    partes, larg, alt = _moldura(uid, titulo, topo, unidade, rotulos)
    n = len(valores)
    pontos = []
    for i, v in enumerate(valores):
        if v is None:
            pontos.append(None)
        else:
            x = ME + larg * (i + 0.5) / n
            y = MS + alt - alt * min(v, topo) / topo
            pontos.append((x, y, i, v))

    trecho: list[tuple] = []

    def descarregar():
        if len(trecho) > 1:
            caminho = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in trecho)
            partes.append(f'<polyline points="{caminho}" class="linha"/>')

    for p in pontos:
        if p is None:
            descarregar()
            trecho = []
        else:
            trecho.append(p)
    descarregar()
    for p in pontos:
        if p is not None:
            partes.append(
                f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="3.4" class="ponto">'
                f"<title>{escape(rotulos[p[2]])}: {formatar(p[3], 1)} {escape(unidade)}</title></circle>"
            )
    partes.append("</svg>")
    return "".join(partes)
