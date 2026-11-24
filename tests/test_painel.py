from datetime import datetime, timedelta

from painel_saude.apple import dormindo
from painel_saude.config import Config
from painel_saude.duplicidade import deduplicar
from painel_saude.modelos import Intervalo, Treino
from painel_saude.semanas import agregar
from painel_saude.sono import fundir, minutos_por_noite
from painel_saude.zona2 import minutos_do_treino

BASE = datetime(2026, 3, 2, 7, 0)  # uma segunda-feira


def treino(inicio_min, dur, principal=False, generico=False, tipo="Running"):
    ini = BASE + timedelta(minutes=inicio_min)
    return Treino(ini, ini + timedelta(minutes=dur), tipo,
                  "relogio" if principal else "outro", principal, generico)


def amostras(minuto_inicial, minutos, bpm, por_minuto=4):
    saida = []
    for m in range(minutos):
        for k in range(por_minuto):
            saida.append((BASE + timedelta(minutes=minuto_inicial + m, seconds=k * 12), bpm))
    return saida


# duplicidade

def test_relogio_vence_secundario_sobreposto():
    relogio = treino(0, 40, principal=True)
    outro = treino(2, 38)
    mantidos, c = deduplicar([outro, relogio], Config())
    assert mantidos == [relogio]
    assert c["duplicados"] == 1


def test_secundario_especifico_sem_sobreposicao_fica_mesmo_curto():
    mantidos, _ = deduplicar([treino(0, 40, principal=True), treino(300, 10)], Config())
    assert len(mantidos) == 2


def test_generico_curto_sem_sobreposicao_e_descartado():
    mantidos, c = deduplicar([treino(0, 10, generico=True)], Config(min_generica_min=20))
    assert mantidos == []
    assert c["genericos_curtos"] == 1


def test_generico_longo_sem_sobreposicao_fica():
    mantidos, _ = deduplicar([treino(0, 25, generico=True)], Config(min_generica_min=20))
    assert len(mantidos) == 1


def test_generico_longo_sobreposto_ao_relogio_e_descartado():
    mantidos, _ = deduplicar([treino(0, 40, principal=True), treino(10, 60, generico=True)], Config())
    assert len(mantidos) == 1 and mantidos[0].principal


def test_limite_de_generico_e_configuravel():
    t = treino(0, 15, generico=True)
    assert deduplicar([t], Config(min_generica_min=15))[0] == [t]
    assert deduplicar([t], Config(min_generica_min=16))[0] == []


def test_dois_secundarios_sobrepostos_mantem_um():
    mantidos, _ = deduplicar([treino(0, 30), treino(5, 30)], Config())
    assert len(mantidos) == 1


# zona 2

def test_zona2_conta_so_minutos_dentro_da_faixa():
    t = treino(0, 10, principal=True)
    am = amostras(0, 4, 100) + amostras(4, 6, 130)
    tempos, bpms = [a[0] for a in am], [a[1] for a in am]
    total, cob, z2 = minutos_do_treino(t, tempos, bpms, (114, 133))
    assert (total, cob, z2) == (10, 10, 6)


def test_faixa_e_inclusiva_nas_pontas():
    t = treino(0, 2, principal=True)
    am = amostras(0, 1, 114) + amostras(1, 1, 133)
    total, cob, z2 = minutos_do_treino(t, [a[0] for a in am], [a[1] for a in am], (114, 133))
    assert z2 == 2


def test_faixa_vem_da_fc_max_informada():
    cfg = Config(fc_max=200, zona2_pct_min=60, zona2_pct_max=70)
    assert cfg.faixa_zona2 == (120.0, 140.0)
    assert Config(zona2_bpm=(100, 110)).faixa_zona2 == (100, 110)


# cobertura

def test_cobertura_conta_minutos_com_amostra():
    t = treino(0, 10, principal=True)
    am = amostras(0, 3, 120)  # só os três primeiros minutos têm leitura
    total, cob, z2 = minutos_do_treino(t, [a[0] for a in am], [a[1] for a in am], (114, 133))
    assert (total, cob, z2) == (10, 3, 3)


def test_semana_sem_relogio_tem_cobertura_zero_e_zona2_zero():
    cfg = Config()
    semanas = agregar([treino(0, 45)], [], [], cfg)
    assert semanas[0].treinos == 1
    assert semanas[0].min_treino == 45
    assert semanas[0].min_zona2 == 0
    assert semanas[0].cobertura_pct == 0.0


def test_cobertura_parcial_na_semana():
    cfg = Config(zona2_bpm=(100, 140))
    am = amostras(0, 30, 120)
    semanas = agregar([treino(0, 60, principal=True)], am, [], cfg)
    assert semanas[0].cobertura_pct == 50.0
    assert semanas[0].min_zona2 == 30


def test_semana_sem_treino_nao_tem_cobertura():
    semanas = agregar([], [], [Intervalo(BASE - timedelta(hours=8), BASE)], Config())
    assert semanas[0].cobertura_pct is None


# sono

def iv(h0, h1):
    d = datetime(2026, 3, 1)
    return Intervalo(d + timedelta(hours=h0), d + timedelta(hours=h1))


def test_fundir_une_sobrepostos_e_que_se_tocam():
    r = fundir([iv(23, 26), iv(24, 28), iv(28, 30), iv(40, 41)])
    assert [(i.inicio, i.fim) for i in r] == [
        (iv(23, 30).inicio, iv(23, 30).fim),
        (iv(40, 41).inicio, iv(40, 41).fim),
    ]


def test_sono_nao_soma_duas_fontes_sobrepostas():
    noite = minutos_por_noite([iv(23, 31), iv(23.5, 30.5), iv(24, 25)])
    assert list(noite.values()) == [8 * 60]


def test_sono_com_lacuna_soma_so_o_que_dormiu():
    noite = minutos_por_noite([iv(23, 26), iv(27, 31)])
    assert list(noite.values()) == [7 * 60]


def test_duas_noites_ficam_separadas():
    noites = minutos_por_noite([iv(23, 31), iv(47, 55)])
    assert len(noites) == 2 and all(v == 480 for v in noites.values())


def test_na_cama_e_acordado_nao_contam_como_sono():
    assert not dormindo("HKCategoryValueSleepAnalysisInBed")
    assert not dormindo("HKCategoryValueSleepAnalysisAwake")
    assert dormindo("HKCategoryValueSleepAnalysisAsleepCore")
    assert dormindo("HKCategoryValueSleepAnalysisAsleep")
