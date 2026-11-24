# Painel de saúde

Um painel de saúde que você roda no seu computador, com os seus próprios dados do Apple Health e, se quiser, do Zepp. A saída é um único arquivo HTML, sem CDN e sem chamada de rede, com gráficos SVG feitos por código e uma tabela semanal. Só biblioteca padrão do Python.

O exemplo pronto, gerado com dados falsos, está em [`exemplo/painel.html`](exemplo/painel.html).

## As duas armadilhas que ele resolve

**1. A zona que não vem no export.** O export do Apple Health traz os treinos e as amostras brutas de frequência cardíaca (FC), mas não diz em que zona cada minuto foi. O painel calcula isso: divide cada treino em minutos, tira a média das leituras de FC de cada minuto e conta como zona 2 o minuto cuja média cai dentro da faixa. A faixa vem da sua FC máxima (porcentagens configuráveis) ou de bpm que você informa direto. Nenhuma faixa vem embutida no código além de um padrão genérico que você deve ajustar.

**2. A cobertura.** Semana sem relógio no pulso não tem amostra de FC, e isso faz uma semana com treino parecer semana sem treino. Por isso os minutos de zona 2 aparecem sempre ao lado da cobertura: quantos minutos de treino têm ao menos uma amostra de FC e que porcentagem isso representa. Semanas com cobertura abaixo do limite (50% por padrão) ficam listradas no gráfico e marcadas na tabela. O número de zona 2 dessas semanas é um piso, não uma medida.

Também cuida de dois problemas comuns:

- **Treinos duplicados.** Quando o relógio e um aparelho secundário (telefone, Zepp) registram o mesmo período, vale o relógio. Treino específico de aparelho secundário só entra se não se sobrepõe a um já mantido. Atividade genérica de aparelho secundário só conta se não se sobrepõe e dura pelo menos N minutos (padrão 20, configurável).
- **Sono sobreposto.** Relógio, telefone e estágios de sono gravam intervalos que se cruzam. Os intervalos de cada noite são fundidos antes da soma. "Na cama" e "acordado" não contam como sono.

## Como exportar

**Apple Health (iPhone):** abra o app Saúde, toque na foto do perfil (canto superior direito), role até o fim e toque em "Exportar todos os dados de saúde". Aguarde, escolha onde salvar e leve o `export.zip` para o computador. Pode usar o zip direto, sem descompactar.

**Zepp (opcional, experimental):** o painel lê um CSV de atividades com as colunas `type`, `startTime` e `sportTime(s)`; você pode passar o zip inteiro, uma pasta ou só o CSV. O caminho e o formato da exportação mudam entre versões do app: confira no seu e, se as colunas vierem com outros nomes, ajuste em `painel_saude/zepp.py`. Se o seu aparelho já sincroniza com o Apple Health, os dados dele chegam pelo export da Apple e o CSV é dispensável.

## Como rodar

Requer Python 3.11 ou mais novo. Com [uv](https://docs.astral.sh/uv/):

```bash
make demo
```

Isso gera dados falsos em `dados_exemplo/` e o painel em `exemplo/painel.html`. Sem make:

```bash
uv run python gerar_dados_exemplo.py
uv run python -m painel_saude --apple dados_exemplo/export.zip \
  --zepp dados_exemplo/zepp_sport.csv --fc-max 190 --fuso -3 --saida exemplo/painel.html
```

Com os seus dados (coloque os exports numa pasta fora do repositório ou em `meus_dados/`, que o Git ignora):

```bash
uv run python -m painel_saude --apple meus_dados/export.zip --zepp meus_dados/zepp \
  --fc-max 185 --fuso -3 --saida painel.html
```

Opções principais: `--fc-max`, `--zona2 BAIXO-ALTO` (bpm), `--min-generica` (minutos), `--cobertura-baixa` (%), `--fuso` (horas em relação ao UTC, porque o Zepp exporta em UTC) e `--config` para um arquivo TOML (veja `config.exemplo.toml`). O comando `python -m painel_saude --help` lista tudo.

Testes:

```bash
make test
```

## Privacidade

Tudo roda no seu computador. O programa só lê os arquivos que você aponta e só escreve o HTML de saída. Não há chamada de rede, telemetria, CDN nem fonte externa, e o HTML gerado também não carrega nada de fora. O `.gitignore` bloqueia `*.zip`, `*.csv`, `export.xml` e `config.toml`, exceto os dados falsos de `dados_exemplo/`. Mesmo assim, o HTML gerado com os seus dados é pessoal: pense antes de compartilhar.

## Limites

- Datas são alinhadas a um fuso fixo informado em `--fuso`; horário de verão não é tratado.
- A zona é calculada por média de FC por minuto, não por zona oficial do relógio.
- Os formatos do Apple Health e do Zepp mudam com o tempo; ajustes podem ser necessários.

## Não é orientação médica

Este projeto organiza números que o seu relógio já registrou. Ele não interpreta, não diagnostica e não recomenda nada. Para qualquer decisão sobre saúde, converse com um profissional.

## Licença

MIT. Veja [LICENSE](LICENSE).
