PY ?= uv run python

.PHONY: demo dados test

dados:
	$(PY) gerar_dados_exemplo.py

demo: dados
	$(PY) -m painel_saude --apple dados_exemplo/export.zip --zepp dados_exemplo/zepp_sport.csv \
		--fc-max 190 --fuso -3 --titulo "Painel de saúde (dados de exemplo)" --saida exemplo/painel.html

test:
	uv run --with pytest python -m pytest
