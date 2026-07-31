"""
Testes automatizados do pipeline (limpeza, validacao, modelo e explicador).

Executar:  pytest -q
"""
from pathlib import Path
import sys
import io
import json
import joblib
import numpy as np
import pandas as pd
import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "src"))

import limpeza  # noqa: E402
from validacao import valida_features  # noqa: E402
from explicador import baseline_de, explica_aluno, recomendacoes_para  # noqa: E402

RAW = BASE / "data" / "raw" / "PEDE_PASSOS_DATASET.xlsx"
PROC = BASE / "data" / "processed" / "pede_unificado.csv"
MODEL = BASE / "models" / "modelo_risco.joblib"
META = BASE / "models" / "modelo_meta.json"


@pytest.fixture(scope="module")
def long():
    return limpeza.unifica(RAW)


@pytest.fixture(scope="module")
def meta():
    return json.loads(META.read_text(encoding="utf-8"))


# ----------------------------- Limpeza -----------------------------
def test_limpeza_shape_e_anos(long):
    assert long.shape[0] > 2500
    assert set(long["ano"].unique()) == {2022, 2023, 2024}


def test_limpeza_genero_normalizado(long):
    # Nao pode sobrar Menino/Menina apos unificacao
    assert set(long["genero"].dropna().unique()) <= {"Feminino", "Masculino"}


def test_limpeza_fase_inteira(long):
    fases = long["fase"].dropna()
    assert fases.between(0, 12).all()


def test_limpeza_pedras_validas(long):
    validas = {"Quartzo", "Agata", "Ametista", "Topazio"}
    assert set(long["pedra"].dropna().unique()) <= validas


def test_limpeza_indicadores_na_faixa(long):
    for c in ["ian", "ida", "ieg", "iaa", "ips", "ipv"]:
        serie = long[c].dropna()
        assert serie.between(0, 10).mean() > 0.98  # quase tudo em [0,10]


def test_limpeza_via_buffer_igual_ao_arquivo(long):
    data = RAW.read_bytes()
    outra = limpeza.unifica(io.BytesIO(data))
    assert outra.shape == long.shape


# ----------------------------- Validacao ---------------------------
def test_validacao_detecta_colunas_faltando():
    df = pd.DataFrame({"ida": [5.0]})
    ok, problemas, _ = valida_features(df, ["ida", "ieg"], ["genero"])
    assert not ok and any("ausentes" in p for p in problemas)


def test_validacao_aceita_dados_bons(meta):
    df = pd.read_csv(PROC).head(10)
    ok, problemas, _ = valida_features(df, meta["features_numericas"], meta["features_categoricas"])
    assert ok and problemas == []


# ------------------------- Modelo / contrato -----------------------
def test_modelo_preve_probabilidade(meta):
    modelo = joblib.load(MODEL)
    feats = meta["features_numericas"] + meta["features_categoricas"]
    df = pd.read_csv(PROC).head(50)
    proba = modelo.predict_proba(df[feats])[:, 1]
    assert proba.shape == (50,)
    assert ((proba >= 0) & (proba <= 1)).all()


def test_modelo_auc_minima(meta):
    # Contrato de qualidade: AUC de teste registrada nao pode regredir muito
    auc = meta["metricas"][meta["melhor_modelo"]]["AUC (teste)"]
    assert auc >= 0.80


# ----------------------------- Explicador --------------------------
def test_explicador_ranqueia_fatores(meta):
    modelo = joblib.load(MODEL)
    df = pd.read_csv(PROC)
    num, cat = meta["features_numericas"], meta["features_categoricas"]
    base = baseline_de(df, num, cat)
    aluno = df[num + cat].dropna().head(1)
    res = explica_aluno(modelo, aluno, base, num, cat)
    assert len(res) == len(num + cat)
    assert "contribuicao" in res.columns
    # recomendacoes devem ser uma lista (possivelmente vazia)
    assert isinstance(recomendacoes_para(res), list)
