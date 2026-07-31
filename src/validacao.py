"""
Camada de validacao de dados — mensagens amigaveis para o app e testes.

Valida um DataFrame de features antes da predicao: colunas obrigatorias,
tipos e faixas plausiveis dos indicadores (0–10).
"""
import numpy as np
import pandas as pd

FAIXA_INDICADORES = {c: (0, 10) for c in ["inde", "ida", "ieg", "iaa", "ips", "ipp", "ipv", "ian"]}


def valida_features(df, num_feats, cat_feats):
    """Retorna (ok: bool, problemas: list[str], avisos: list[str])."""
    problemas, avisos = [], []
    feats = num_feats + cat_feats

    faltando = [c for c in feats if c not in df.columns]
    if faltando:
        problemas.append("Colunas obrigatórias ausentes: " + ", ".join(faltando))
        return False, problemas, avisos  # sem colunas nao da pra seguir

    if len(df) == 0:
        problemas.append("O arquivo não contém linhas de dados.")
        return False, problemas, avisos

    # Numericas: coercao e faixa
    for c in num_feats:
        serie = pd.to_numeric(df[c], errors="coerce")
        n_nao_num = int(serie.isna().sum() - df[c].isna().sum())
        if n_nao_num > 0:
            avisos.append(f"'{c}': {n_nao_num} valor(es) não numérico(s) serão tratados como ausentes.")
        if c in FAIXA_INDICADORES:
            lo, hi = FAIXA_INDICADORES[c]
            fora = int(((serie < lo) | (serie > hi)).sum())
            if fora > 0:
                avisos.append(f"'{c}': {fora} valor(es) fora da faixa [{lo}, {hi}].")

    # Ausencia total em coluna critica
    for c in num_feats:
        if pd.to_numeric(df[c], errors="coerce").notna().sum() == 0:
            avisos.append(f"'{c}': coluna totalmente vazia (será imputada pela mediana do treino).")

    return True, problemas, avisos
