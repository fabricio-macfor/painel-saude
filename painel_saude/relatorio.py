"""Monta o HTML único e autocontido: CSS e SVG embutidos, sem CDN e sem chamada de rede."""

from __future__ import annotations

from html import escape

from . import svg
from .config import Config
from .semanas import Semana

CSS = """
:root{--fundo:#f6f7f9;--cartao:#fff;--texto:#1d2733;--suave:#5b6773;--linha:#d9dee4;
--barra:#2f6f9f;--hach:#2f6f9f;--hachfundo:#e8eef3;--destaque:#b5532b;--ponto:#2f6f9f}
@media (prefers-color-scheme:dark){:root{--fundo:#12171c;--cartao:#1a2127;--texto:#e6eaee;
--suave:#9aa6b2;--linha:#2b343c;--barra:#6aa9d6;--hach:#6aa9d6;--hachfundo:#232c34;
--destaque:#e08a5f;--ponto:#6aa9d6}}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--texto);
font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:1.6rem;margin:0 0 4px}h2{font-size:1.15rem;margin:0 0 8px}
.sub{color:var(--suave);margin:0 0 20px}
.cartoes{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:20px}
.cartao,section{background:var(--cartao);border:1px solid var(--linha);border-radius:10px;padding:14px 16px}
section{margin-bottom:16px}
.num{font-size:1.7rem;font-weight:650;line-height:1.2}.rot{color:var(--suave);font-size:.85rem}
.grafico{width:100%;height:auto;display:block}
.grade{stroke:var(--linha);stroke-width:1}.eixo{fill:var(--suave);font-size:11px}
.barra{fill:var(--barra)}.hach-fundo{fill:var(--hachfundo)}.hach-traco{stroke:var(--hach)}
.barra-hach{stroke:var(--hach);stroke-width:1}
.linha{fill:none;stroke:var(--ponto);stroke-width:2}.ponto{fill:var(--ponto)}
.nota{color:var(--suave);font-size:.88rem;margin:6px 0 0}
.tabela{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.9rem;
font-variant-numeric:tabular-nums}
th,td{padding:6px 10px;border-bottom:1px solid var(--linha);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}th{color:var(--suave);font-weight:600}
td.baixa{color:var(--destaque);font-weight:600}
footer{color:var(--suave);font-size:.85rem;margin-top:24px}
"""


def _rotulo(s: Semana) -> str:
    return s.inicio.strftime("%d/%m")


def _num(v, casas=0, vazio="sem dado"):
    return vazio if v is None else svg.formatar(v, casas)


def _cartoes(semanas: list[Semana]) -> str:
    treinos = sum(s.treinos for s in semanas)
    z2 = sum(s.min_zona2 for s in semanas)
    tot = sum(s.min_treino for s in semanas)
    cob = sum(s.min_com_fc for s in semanas)
    pct = 100.0 * cob / tot if tot else None
    noites = sum(s.noites for s in semanas)
    horas = sum((s.sono_media_h or 0) * s.noites for s in semanas)
    sono = horas / noites if noites else None
    itens = [
        (_num(treinos), "treinos no período"),
        (_num(z2), "minutos em zona 2 (somente com amostra)"),
        (_num(pct, 0) + ("%" if pct is not None else ""), "cobertura de FC nos treinos"),
        (_num(sono, 1) + (" h" if sono is not None else ""), "sono médio por noite"),
    ]
    return '<div class="cartoes">' + "".join(
        f'<div class="cartao"><div class="num">{escape(n)}</div><div class="rot">{escape(r)}</div></div>'
        for n, r in itens
    ) + "</div>"


def _tabela(semanas: list[Semana], cfg: Config) -> str:
    cab = (
        "Semana (segunda)", "Treinos", "Min. de treino", "Zona 2 (min)",
        "Min. com FC", "Cobertura de FC", "Sono médio (h)", "Noites com dado",
    )
    linhas = ["<tr>" + "".join(f"<th>{c}</th>" for c in cab) + "</tr>"]
    for s in semanas:
        pct = s.cobertura_pct
        baixa = pct is not None and pct < cfg.cobertura_baixa_pct
        if pct is None:
            cel_cob = "<td>sem treino</td>"
        else:
            texto = f"{svg.formatar(pct, 0)}%" + (" (baixa)" if baixa else "")
            cel_cob = f'<td class="{"baixa" if baixa else ""}">{texto}</td>'
        linhas.append(
            "<tr>"
            f"<td>{s.inicio.strftime('%d/%m/%Y')}</td><td>{s.treinos}</td>"
            f"<td>{svg.formatar(s.min_treino)}</td><td>{svg.formatar(s.min_zona2)}</td>"
            f"<td>{svg.formatar(s.min_com_fc)}</td>{cel_cob}"
            f"<td>{_num(s.sono_media_h, 1, '-')}</td><td>{s.noites}</td></tr>"
        )
    return '<div class="tabela"><table>' + "".join(linhas) + "</table></div>"


def montar_html(semanas: list[Semana], contagem: dict, cfg: Config) -> str:
    rot = [_rotulo(s) for s in semanas]
    baixo, alto = cfg.faixa_zona2
    hach = [
        s.cobertura_pct is not None and s.cobertura_pct < cfg.cobertura_baixa_pct
        for s in semanas
    ]
    g_z2 = svg.barras(
        "z2", "Minutos de zona 2 por semana", rot,
        [float(s.min_zona2) for s in semanas], "min", hachurar=hach,
    )
    g_cob = svg.barras(
        "cob", "Cobertura de frequência cardíaca por semana", rot,
        [s.cobertura_pct for s in semanas], "% dos minutos de treino com amostra",
        maximo=100.0,
    )
    g_trn = svg.barras(
        "trn", "Minutos de treino por semana", rot,
        [float(s.min_treino) for s in semanas], "min",
    )
    g_sono = svg.linha(
        "sono", "Sono médio por noite, por semana", rot,
        [s.sono_media_h for s in semanas], "horas por noite",
    )
    periodo = (
        f"{semanas[0].inicio.strftime('%d/%m/%Y')} a "
        f"{semanas[-1].inicio.strftime('%d/%m/%Y')} (semanas iniciadas)"
        if semanas else "sem dados"
    )
    corpo = f"""
<h1>{escape(cfg.titulo)}</h1>
<p class="sub">Período: {escape(periodo)}. Gerado no seu computador, sem enviar nada para fora.</p>
{_cartoes(semanas)}
<section><h2>Zona 2 por semana</h2>
{g_z2}
<p class="nota">Barras listradas são semanas com cobertura de FC abaixo de {svg.formatar(cfg.cobertura_baixa_pct, 0)}%:
o número é um piso, porque faltou leitura de frequência cardíaca, e não necessariamente faltou treino.
Faixa usada: {svg.formatar(baixo, 0)} a {svg.formatar(alto, 0)} bpm.</p></section>
<section><h2>Cobertura de frequência cardíaca</h2>
{g_cob}
<p class="nota">Porcentagem dos minutos de treino em que existe ao menos uma amostra de FC.</p></section>
<section><h2>Minutos de treino</h2>
{g_trn}
<p class="nota">Treinos lidos: {contagem.get('lidos', 0)}. Duplicados descartados: {contagem.get('duplicados', 0)}.
Atividades genéricas curtas descartadas: {contagem.get('genericos_curtos', 0)}
(mínimo de {svg.formatar(cfg.min_generica_min, 0)} min). Mantidos: {contagem.get('mantidos', 0)}.</p></section>
<section><h2>Sono</h2>
{g_sono}
<p class="nota">Intervalos sobrepostos de cada noite são fundidos antes da soma. Semanas sem registro ficam em branco.</p></section>
<section><h2>Tabela semanal</h2>
{_tabela(semanas, cfg)}</section>
<footer>Painel informativo para acompanhamento pessoal. Não é orientação médica.</footer>
"""
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(cfg.titulo)}</title><style>{CSS}</style></head>"
        f"<body><main>{corpo}</main></body></html>"
    )
