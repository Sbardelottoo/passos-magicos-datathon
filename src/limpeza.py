"""
Limpeza e unificacao da base PEDE Passos Magicos (2022, 2023, 2024).

A planilha original possui uma aba por ano, com nomes de coluna e codificacoes
diferentes entre anos. Este script:
  1. Le as 3 abas.
  2. Padroniza nomes de indicadores (IAN, IDA, IEG, IAA, IPS, IPP, IPV, INDE).
  3. Normaliza a coluna Fase (numerica em 2022, texto em 2023, fase+turma em 2024).
  4. Corrige encoding de textos (Genero, Pedra, Sim/Nao).
  5. Coage colunas numericas gravadas como texto (ex.: INDE 2024 com 'INCLUIR').
  6. Empilha tudo em um dataset LONGO: uma linha por (RA, ano).
  7. Salva em data/processed/pede_unificado.csv (e .parquet se possivel).

Uso:
    python src/limpeza.py
"""
from pathlib import Path
import re
import unicodedata
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW = BASE_DIR / "data" / "raw" / "PEDE_PASSOS_DATASET.xlsx"
OUT_DIR = BASE_DIR / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Indicadores que existem (com nomes ja padronizados na planilha) nos 3 anos.
INDICADORES = ["IAA", "IEG", "IPS", "IDA", "IPP", "IPV", "IAN"]


def _ascii_key(txt):
    """Chave normalizada (minuscula, sem acento, so alfanumerico) p/ casar nomes."""
    s = "".join(
        c for c in unicodedata.normalize("NFKD", str(txt))
        if not unicodedata.combining(c)
    )
    return re.sub(r"[^a-z0-9]", "", s.lower())


def acha_coluna(df, *nomes):
    """Retorna o nome real da 1a coluna cujo nome normalizado casa com algum alvo."""
    alvo = {_ascii_key(n) for n in nomes}
    for c in df.columns:
        if _ascii_key(c) in alvo:
            return c
    return None


def corrige_texto(valor):
    """Corrige mojibake comum (cp1252 lido como utf-8) e normaliza."""
    if not isinstance(valor, str):
        return valor
    s = valor.strip()
    trocas = {
        "�gata": "Agata", "Ã¡gata": "Agata", "Ãgata": "Agata",
        "Top�zio": "Topazio", "TopÃ¡zio": "Topazio",
        "N�o": "Nao", "NÃ£o": "Nao",
        "Ingl�s": "Ingles",
        "G�nero": "Genero",
    }
    for k, v in trocas.items():
        s = s.replace(k, v)
    # Remove acentuacao remanescente para padronizar categorias
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return s


def normaliza_fase(valor):
    """Converte a Fase para inteiro 0..8. Trata os 3 formatos distintos.

    2022: ja e numerica (0..7).
    2023: 'ALFA', 'FASE 1'..'FASE 8'.
    2024: fase+turma como '1A', '2B', 'ALFA'...
    """
    if pd.isna(valor):
        return np.nan
    s = str(valor).strip().upper()
    if s in ("ALFA", "FASE ALFA", "0"):
        return 0
    # 'FASE 3' -> 3
    m = re.search(r"FASE\s*(\d+)", s)
    if m:
        return int(m.group(1))
    # '1A', '2B' -> primeiro digito
    m = re.match(r"(\d+)", s)
    if m:
        return int(m.group(1))
    return np.nan


def sim_nao_para_bool(serie):
    def conv(v):
        if pd.isna(v):
            return np.nan
        s = corrige_texto(str(v)).strip().lower()
        if s in ("sim", "s", "1", "true", "verdadeiro"):
            return 1
        if s in ("nao", "n", "0", "false", "falso"):
            return 0
        return np.nan
    return serie.apply(conv)


def num(serie):
    """Coage para numerico tratando virgula decimal e placeholders."""
    if serie.dtype.kind in "if":
        return serie
    return pd.to_numeric(
        serie.astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )


def carrega(source=None):
    """Le a planilha PEDE (caminho ou buffer). Detecta as abas por ano.

    Funciona com o arquivo padrao (abas PEDE2022/2023/2024) e tolera pequenas
    variacoes de nome, permitindo que o app receba a planilha crua do usuario.
    """
    xl = pd.ExcelFile(source if source is not None else RAW)
    abas = {}
    for aba in xl.sheet_names:
        for ano in (2022, 2023, 2024):
            if str(ano) in str(aba) or str(ano)[2:] in str(aba):
                abas.setdefault(ano, aba)
    # Fallback posicional se a deteccao por nome falhar
    if len(abas) < 3 and len(xl.sheet_names) >= 3:
        for ano, aba in zip((2022, 2023, 2024), xl.sheet_names[:3]):
            abas.setdefault(ano, aba)
    faltando = [a for a in (2022, 2023, 2024) if a not in abas]
    if faltando:
        raise ValueError(f"Planilha nao contem abas para os anos: {faltando}. "
                         f"Abas encontradas: {xl.sheet_names}")
    return xl.parse(abas[2022]), xl.parse(abas[2023]), xl.parse(abas[2024])


def _linha_base(df, ano):
    """Extrai as colunas comuns e devolve um DataFrame padronizado."""
    a = str(ano)
    col_inde_cands = [f"INDE {a}", f"INDE {a[2:]}", "INDE"]
    col_pedra_cands = [f"Pedra {a}", f"Pedra {a[2:]}", "Pedra"]
    out = pd.DataFrame()
    col_ra = acha_coluna(df, "RA")
    col_fase = acha_coluna(df, "Fase")
    out["RA"] = df[col_ra].astype(str).str.strip()
    out["ano"] = ano
    out["fase"] = df[col_fase].apply(normaliza_fase)

    col_idade = acha_coluna(df, "Idade", "Idade 22", "Idade 2022")
    out["idade"] = num(df[col_idade]) if col_idade else np.nan
    col_gen = acha_coluna(df, "Genero")
    out["genero"] = df[col_gen].apply(corrige_texto) if col_gen else np.nan
    col_ing = acha_coluna(df, "Ano ingresso", "Ano de ingresso")
    out["ano_ingresso"] = num(df[col_ing]) if col_ing else np.nan

    ci = acha_coluna(df, *col_inde_cands)
    out["inde"] = num(df[ci]) if ci else np.nan
    cp = acha_coluna(df, *col_pedra_cands)
    out["pedra"] = df[cp].apply(corrige_texto) if cp else np.nan

    for ind in INDICADORES:
        c = acha_coluna(df, ind)
        out[ind.lower()] = num(df[c]) if c else np.nan

    # Notas por disciplina (nomes variam por ano)
    for k, nomes in {"mat": ("Matem", "Mat"), "port": ("Portug", "Por"), "ing": ("Ingles", "Ing")}.items():
        c = acha_coluna(df, *nomes)
        out["nota_" + k] = num(df[c]) if c else np.nan

    # Defasagem (nome varia: 'Defas' em 2022, 'Defasagem' nos demais)
    col_def = acha_coluna(df, "Defas", "Defasagem")
    out["defasagem"] = num(df[col_def]) if col_def else np.nan
    # Ponto de virada booleano (so 2022 tem preenchido)
    col_pv = acha_coluna(df, "Atingiu PV")
    out["atingiu_pv"] = sim_nao_para_bool(df[col_pv]) if col_pv else np.nan
    # Bolsa / indicado
    col_bolsa = acha_coluna(df, "Indicado")
    out["indicado_bolsa"] = sim_nao_para_bool(df[col_bolsa]) if col_bolsa else np.nan
    return out


def unifica(source=None):
    d22, d23, d24 = carrega(source)
    p22 = _linha_base(d22, 2022)
    p23 = _linha_base(d23, 2023)
    p24 = _linha_base(d24, 2024)
    long = pd.concat([p22, p23, p24], ignore_index=True)

    # Clipa indicadores para a faixa valida [0, 10] (ha ruido tipo 10.002 em 2024)
    for c in ["inde", "ian", "ida", "ieg", "iaa", "ips", "ipp", "ipv"]:
        long[c] = long[c].clip(lower=0, upper=10)

    # Unifica genero (algumas abas usam Menino/Menina)
    long["genero"] = long["genero"].replace({
        "Menina": "Feminino", "Menino": "Masculino",
        "F": "Feminino", "M": "Masculino",
    })

    # Limpa pedras invalidas (placeholder 'INCLUIR')
    long.loc[long["pedra"].isin(["INCLUIR", "nan", "None", ""]), "pedra"] = np.nan
    long["pedra"] = long["pedra"].replace({"Agata": "Agata"})

    # Feature: em risco de defasagem (moderada/severa: defasagem <= -2)
    long["em_risco_defasagem"] = (long["defasagem"] <= -2).astype("Int64")
    long.loc[long["defasagem"].isna(), "em_risco_defasagem"] = pd.NA

    # Categoria de defasagem legivel
    def cat_def(d):
        if pd.isna(d):
            return np.nan
        if d >= 1:
            return "Adiantado"
        if d == 0:
            return "Adequado"
        if d == -1:
            return "Defasagem leve"
        return "Defasagem moderada/severa"
    long["categoria_defasagem"] = long["defasagem"].apply(cat_def)

    # Anos na PM (derivado do ano de ingresso)
    long["anos_na_pm"] = long["ano"] - long["ano_ingresso"]
    long.loc[(long["anos_na_pm"] < 0) | (long["anos_na_pm"] > 30), "anos_na_pm"] = np.nan

    long = long.sort_values(["RA", "ano"]).reset_index(drop=True)
    return long


def main():
    long = unifica()
    csv_path = OUT_DIR / "pede_unificado.csv"
    long.to_csv(csv_path, index=False, encoding="utf-8-sig")
    try:
        long.to_parquet(OUT_DIR / "pede_unificado.parquet", index=False)
    except Exception as e:  # pyarrow pode nao estar disponivel
        print("(parquet ignorado:", e, ")")

    print("Dataset unificado salvo em:", csv_path)
    print("Shape:", long.shape)
    print("Registros por ano:\n", long["ano"].value_counts().sort_index())
    print("\nAlunos unicos (RA):", long["RA"].nunique())
    print("\nDistribuicao do alvo (em_risco_defasagem):")
    print(long["em_risco_defasagem"].value_counts(dropna=False))
    print("\nCompletude por coluna (%):")
    print((long.notna().mean() * 100).round(1).sort_values())


if __name__ == "__main__":
    main()
