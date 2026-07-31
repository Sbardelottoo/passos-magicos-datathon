"""
Explicabilidade local do modelo de risco + recomendacoes de acao.

Metodo: ablacao local (model-agnostic). Para cada variavel, medimos quanto a
probabilidade de risco CAI se aquele valor do aluno fosse substituido por um
valor "tipico" (baseline). Quanto maior a queda, mais aquela variavel esta
elevando o risco DESTE aluno -> vira prioridade de acao.

Nao depende de bibliotecas extras (SHAP etc.), roda rapido e produz uma
explicacao intuitiva para a equipe pedagogica.
"""
import numpy as np
import pandas as pd

# Rotulos amigaveis
ROTULOS = {
    "inde": "INDE (índice global)", "ida": "IDA (aprendizagem)",
    "ieg": "IEG (engajamento)", "iaa": "IAA (autoavaliação)",
    "ips": "IPS (psicossocial)", "ipp": "IPP (psicopedagógico)",
    "ipv": "IPV (ponto de virada)", "ian": "IAN (adequação ao nível)",
    "idade": "Idade", "fase": "Fase", "defasagem": "Defasagem atual",
    "anos_na_pm": "Anos na Passos Mágicos", "genero": "Gênero",
}

# Acoes sugeridas por fator de risco (linguagem pedagogica)
RECOMENDACOES = {
    "ipv": "Fortalecer o protagonismo e as metas do aluno (mentoria voltada ao ponto de virada).",
    "ida": "Reforço acadêmico e acompanhamento de aprendizagem (tutoria/monitoria).",
    "ieg": "Ações de engajamento: presença, participação e vínculo com as atividades.",
    "ips": "Atenção psicossocial — apoio emocional e leitura do contexto familiar.",
    "ipp": "Avaliação psicopedagógica e plano individualizado.",
    "iaa": "Rodas de autoconhecimento para alinhar autopercepção e desempenho real.",
    "ian": "Plano de nivelamento para reduzir a defasagem série-idade.",
    "defasagem": "Priorizar o nivelamento — a defasagem atual já eleva o risco.",
    "inde": "Monitoramento geral do índice de desenvolvimento.",
    "idade": "Fator etário — atenção redobrada a alunos mais velhos para a fase.",
    "fase": "Acompanhar de perto a transição de fase/nível.",
    "anos_na_pm": "Reforçar o vínculo do aluno com o programa.",
    "genero": "—",
}


def baseline_de(df, num_feats, cat_feats):
    """Valor 'tipico' por variavel: mediana (numericas) / moda (categoricas)."""
    base = {}
    for c in num_feats:
        base[c] = float(pd.to_numeric(df[c], errors="coerce").median())
    for c in cat_feats:
        base[c] = df[c].mode(dropna=True)
        base[c] = base[c].iloc[0] if len(base[c]) else None
    return base


def explica_aluno(modelo, entrada, baseline, num_feats, cat_feats):
    """Retorna DataFrame ranqueado: contribuicao de cada variavel ao risco.

    contribuicao = prob_original - prob_com_variavel_no_baseline
    (positiva => a variavel esta ELEVANDO o risco deste aluno).
    """
    feats = num_feats + cat_feats
    entrada = entrada[feats].copy().reset_index(drop=True)
    prob0 = float(modelo.predict_proba(entrada)[0, 1])

    linhas = []
    for c in feats:
        alt = entrada.copy()
        alt.loc[0, c] = baseline.get(c)
        prob_alt = float(modelo.predict_proba(alt)[0, 1])
        contrib = prob0 - prob_alt  # >0: variavel eleva o risco
        linhas.append({
            "variavel": c,
            "rotulo": ROTULOS.get(c, c),
            "valor_aluno": entrada.loc[0, c],
            "valor_tipico": baseline.get(c),
            "contribuicao": contrib,
        })
    res = pd.DataFrame(linhas).sort_values("contribuicao", ascending=False)
    res["prob_original"] = prob0
    return res


def recomendacoes_para(res, top=3, apenas_positivas=True):
    """Lista de (rotulo, acao) para os principais fatores de risco."""
    r = res.copy()
    if apenas_positivas:
        r = r[r["contribuicao"] > 0]
    out = []
    for _, row in r.head(top).iterrows():
        acao = RECOMENDACOES.get(row["variavel"], "—")
        if acao and acao != "—":
            out.append((row["rotulo"], acao))
    return out
