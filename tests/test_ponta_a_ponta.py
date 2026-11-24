import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from gerar_dados_exemplo import gerar  # noqa: E402
from painel_saude.cli import main  # noqa: E402


def test_demo_gera_html_autocontido(tmp_path):
    gerar(tmp_path / "d", False)
    saida = tmp_path / "p.html"
    assert main(["--apple", str(tmp_path / "d/export.zip"), "--zepp",
                 str(tmp_path / "d/zepp_sport.csv"), "--fuso", "-3", "--saida", str(saida)]) == 0
    html = saida.read_text(encoding="utf-8")
    assert "<svg" in html and "Cobertura de FC" in html
    assert "src=" not in html and "href=" not in html and "@import" not in html
    assert "https://" not in html and "http://" not in html.replace("http://www.w3.org/2000/svg", "")


def test_dados_de_exemplo_sao_deterministicos(tmp_path):
    gerar(tmp_path / "a", True)
    gerar(tmp_path / "b", True)
    assert (tmp_path / "a/export.xml").read_bytes() == (tmp_path / "b/export.xml").read_bytes()
