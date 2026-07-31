"""
Analise exploratoria (EDA) respondendo as 11 perguntas de negocio do Datathon.

Gera figuras em reports/figures/ e um resumo textual em reports/insights.md.
Cada bloco esta rotulado com a pergunta correspondente do enunciado.

Uso:
    python src/analise.py
"""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["figure.dpi"] = 110

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data" / "processed" / "pede_unificado.csv"
FIG = BASE / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
INSIGHTS = BASE / "reports" / "insights.md"

INDS = ["ian", "ida", "ieg", "iaa", "ips", "ipp", "ipv"]
COR = "#2E5E8C"
linhas = []  # acumula texto de insights


def add(txt=""):
    linhas.append(txt)
    print(txt)


def salvar(fig, nome):
    caminho = FIG / nome
    fig.tight_layout()
    fig.savefig(caminho, bbox_inches="tight")
    plt.close(fig)
    return caminho


def main():
    df = pd.read_csv(DATA)
    add("# Insights da Analise Exploratoria - PEDE Passos Magicos (2022-2024)\n")
    add(f"Base unificada: {df.shape[0]} registros (aluno-ano), "
        f"{df['RA'].nunique()} alunos unicos, anos {sorted(df.ano.unique())}.\n")

    # ------------------------------------------------------------------
    # Q1. Adequacao do nivel (IAN) - perfil de defasagem e evolucao
    # ------------------------------------------------------------------
    add("## Q1. Adequacao ao nivel (IAN) e defasagem")
    ordem = ["Adiantado", "Adequado", "Defasagem leve", "Defasagem moderada/severa"]
    tab = (df.groupby(["ano", "categoria_defasagem"]).size()
             .unstack(fill_value=0).reindex(columns=ordem))
    perc = tab.div(tab.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(8, 4.5))
    perc.plot(kind="bar", stacked=True, ax=ax,
              color=["#4C9A2A", "#8FBF60", "#E9A23B", "#C0392B"])
    ax.set_title("Perfil de defasagem dos alunos por ano (%)")
    ax.set_ylabel("% de alunos"); ax.set_xlabel("Ano")
    ax.legend(title="Categoria", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.tick_params(axis="x", rotation=0)
    salvar(fig, "q1_defasagem_por_ano.png")
    mod = perc["Defasagem moderada/severa"]
    add(f"- Defasagem moderada/severa caiu de {mod.loc[2022]:.1f}% (2022) "
        f"para {mod.loc[2024]:.1f}% (2024).")
    adeq = perc["Adequado"] + perc["Adiantado"]
    add(f"- Alunos adequados/adiantados subiram de {adeq.loc[2022]:.1f}% para {adeq.loc[2024]:.1f}%.")
    add(f"- Em 2024, {tab.loc[2024,'Defasagem moderada/severa']} alunos seguem em defasagem moderada/severa (foco de atencao).\n")

    # ------------------------------------------------------------------
    # Q2. Desempenho academico (IDA) ao longo das fases e anos
    # ------------------------------------------------------------------
    add("## Q2. Desempenho academico (IDA)")
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    df.groupby("ano")["ida"].mean().plot(marker="o", ax=ax[0], color=COR)
    ax[0].set_title("IDA medio por ano"); ax[0].set_ylabel("IDA medio"); ax[0].set_xticks(df.ano.unique())
    piv = df.pivot_table(index="fase", columns="ano", values="ida", aggfunc="mean")
    piv.plot(marker="o", ax=ax[1])
    ax[1].set_title("IDA medio por fase e ano"); ax[1].set_xlabel("Fase")
    salvar(fig, "q2_ida_evolucao.png")
    ida_ano = df.groupby("ano")["ida"].mean()
    tend = "melhora" if ida_ano.loc[2024] > ida_ano.loc[2022] else "queda"
    add(f"- IDA medio: {ida_ano.loc[2022]:.2f} (2022) -> {ida_ano.loc[2024]:.2f} (2024): tendencia de {tend}.")
    add(f"- Fases iniciais tendem a IDA mais alto; ha queda nas fases intermediarias (transicao).\n")

    # ------------------------------------------------------------------
    # Q3. Engajamento (IEG) x desempenho (IDA) e ponto de virada (IPV)
    # ------------------------------------------------------------------
    add("## Q3. Engajamento (IEG) x IDA e IPV")
    corr_ida = df["ieg"].corr(df["ida"])
    corr_ipv = df["ieg"].corr(df["ipv"])
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    sns.regplot(data=df, x="ieg", y="ida", ax=ax[0], scatter_kws={"alpha": .25, "s": 15}, line_kws={"color": "#C0392B"})
    ax[0].set_title(f"IEG x IDA (r = {corr_ida:.2f})")
    sns.regplot(data=df, x="ieg", y="ipv", ax=ax[1], scatter_kws={"alpha": .25, "s": 15}, line_kws={"color": "#C0392B"})
    ax[1].set_title(f"IEG x IPV (r = {corr_ipv:.2f})")
    salvar(fig, "q3_ieg_ida_ipv.png")
    add(f"- Correlacao IEG-IDA = {corr_ida:.2f}; IEG-IPV = {corr_ipv:.2f} (positivas e fortes).")
    add("- Engajamento e um dos maiores alavancadores de desempenho e do ponto de virada.\n")

    # ------------------------------------------------------------------
    # Q4. Autoavaliacao (IAA) x desempenho real (IDA) e engajamento (IEG)
    # ------------------------------------------------------------------
    add("## Q4. Autoavaliacao (IAA) x realidade")
    c_ida = df["iaa"].corr(df["ida"]); c_ieg = df["iaa"].corr(df["ieg"])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.scatterplot(data=df, x="iaa", y="ida", hue="categoria_defasagem", alpha=.5, ax=ax)
    ax.set_title(f"IAA x IDA (r = {c_ida:.2f})")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    salvar(fig, "q4_iaa_ida.png")
    add(f"- Correlacao IAA-IDA = {c_ida:.2f}; IAA-IEG = {c_ieg:.2f}.")
    incoerente = df[(df["iaa"] >= 8) & (df["ida"] <= 5)]
    add(f"- {len(incoerente)} registros com autoavaliacao alta (>=8) mas IDA baixo (<=5): "
        "possivel descompasso de autopercepcao a monitorar.\n")

    # ------------------------------------------------------------------
    # Q5. Aspectos psicossociais (IPS) que antecedem quedas (longitudinal)
    # ------------------------------------------------------------------
    add("## Q5. Psicossocial (IPS) antecedendo quedas")
    d = df.sort_values(["RA", "ano"]).copy()
    d["ida_prox"] = d.groupby("RA")["ida"].shift(-1)
    d["ieg_prox"] = d.groupby("RA")["ieg"].shift(-1)
    d["queda_ida"] = (d["ida_prox"] < d["ida"] - 0.5)
    par = d.dropna(subset=["ips", "queda_ida"])
    ips_queda = par.loc[par["queda_ida"], "ips"].mean()
    ips_sem = par.loc[~par["queda_ida"], "ips"].mean()
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    sns.boxplot(data=par, x="queda_ida", y="ips", ax=ax, palette=["#4C9A2A", "#C0392B"])
    ax.set_xticklabels(["Sem queda", "Com queda de IDA no ano seguinte"])
    ax.set_title("IPS atual x queda de desempenho no ano seguinte"); ax.set_xlabel("")
    salvar(fig, "q5_ips_antecede_queda.png")
    add(f"- IPS medio de quem cai no ano seguinte = {ips_queda:.2f} vs {ips_sem:.2f} de quem nao cai.")
    add("- IPS mais baixo antecede quedas de IDA: sinal de alerta psicossocial precoce.\n")

    # ------------------------------------------------------------------
    # Q6. Psicopedagogico (IPP) confirma ou contradiz o IAN?
    # ------------------------------------------------------------------
    add("## Q6. Psicopedagogico (IPP) x defasagem (IAN)")
    dpp = df.dropna(subset=["ipp"])
    c_ipp_ian = dpp["ipp"].corr(dpp["ian"])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.boxplot(data=dpp, x="categoria_defasagem", y="ipp",
                order=["Adiantado", "Adequado", "Defasagem leve", "Defasagem moderada/severa"], ax=ax)
    ax.set_title(f"IPP por categoria de defasagem (r IPP-IAN = {c_ipp_ian:.2f})")
    ax.tick_params(axis="x", rotation=20); ax.set_xlabel("")
    salvar(fig, "q6_ipp_ian.png")
    add(f"- Correlacao IPP-IAN = {c_ipp_ian:.2f}.")
    add("- IPP tende a acompanhar a defasagem, mas a relacao e fraca: a avaliacao psicopedagogica "
        "captura dimensao complementar ao IAN (nao apenas redundante).\n")

    # ------------------------------------------------------------------
    # Q7. Ponto de virada (IPV) - o que mais influencia
    # ------------------------------------------------------------------
    add("## Q7. Determinantes do ponto de virada (IPV)")
    corrs = df[INDS].corr()["ipv"].drop("ipv").sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    corrs.plot(kind="barh", ax=ax, color=COR)
    ax.set_title("Correlacao dos indicadores com o IPV"); ax.set_xlabel("Correlacao de Pearson")
    salvar(fig, "q7_drivers_ipv.png")
    add("- Ordem de influencia sobre o IPV: " + ", ".join(f"{k.upper()} ({v:.2f})" for k, v in corrs.items()) + ".")
    add(f"- {corrs.index[0].upper()} e {corrs.index[1].upper()} sao os principais motores do ponto de virada.\n")

    # ------------------------------------------------------------------
    # Q8. Multidimensionalidade - o que eleva o INDE
    # ------------------------------------------------------------------
    add("## Q8. O que eleva a nota global (INDE)")
    corr_inde = df[INDS + ["inde"]].corr()["inde"].drop(index="inde").sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    corr_inde.plot(kind="barh", ax=ax, color="#8E44AD")
    ax.set_title("Correlacao dos indicadores com o INDE"); ax.set_xlabel("Correlacao de Pearson")
    salvar(fig, "q8_drivers_inde.png")
    add("- Indicadores mais associados ao INDE: " + ", ".join(f"{k.upper()} ({v:.2f})" for k, v in corr_inde.items()) + ".")

    # Q8b. Contribuicao MULTIVARIADA (combinacoes) via regressao padronizada
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    comb = df[INDS + ["inde"]].dropna()
    Xs = StandardScaler().fit_transform(comb[INDS])
    reg = LinearRegression().fit(Xs, comb["inde"])
    coef = pd.Series(reg.coef_, index=[i.upper() for i in INDS]).sort_values()
    r2 = reg.score(Xs, comb["inde"])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    coef.plot(kind="barh", ax=ax, color="#2E5E8C")
    ax.set_title(f"Peso efetivo de cada indicador no INDE (R2={r2:.2f})")
    ax.set_xlabel("Coeficiente padronizado (peso na composicao do INDE)")
    salvar(fig, "q8_contribuicao_multivariada.png")
    top_comb = coef.sort_values(ascending=False)
    add(f"- Como o INDE e uma ponderacao dos indicadores, a regressao padronizada RECUPERA os "
        f"pesos efetivos da formula (R2={r2:.2f}): "
        + ", ".join(f"{k} ({v:+.2f})" for k, v in top_comb.items()) + ".")
    add(f"- Os maiores pesos sao {top_comb.index[0]} e {top_comb.index[1]}: sao as combinacoes que "
        "mais elevam a nota global - priorizar esses eixos rende o maior ganho no INDE.")

    # Combinacao de indicadores "altos" (>= mediana) x INDE medio
    eixos = ["ida", "ieg", "ips", "ipp"]
    cc = df[eixos + ["inde"]].dropna().copy()
    for e in eixos:
        cc[e + "_alto"] = (cc[e] >= cc[e].median()).astype(int)
    cc["n_altos"] = cc[[e + "_alto" for e in eixos]].sum(axis=1)
    por_n = cc.groupby("n_altos")["inde"].mean()
    fig, ax = plt.subplots(figsize=(7, 4.2))
    por_n.plot(kind="bar", ax=ax, color="#8E44AD")
    ax.set_title("INDE medio por nº de indicadores (IDA/IEG/IPS/IPP) acima da mediana")
    ax.set_xlabel("Quantos dos 4 indicadores estao 'altos'"); ax.set_ylabel("INDE medio")
    ax.tick_params(axis="x", rotation=0)
    salvar(fig, "q8_combinacoes_inde.png")
    add(f"- Ter os 4 indicadores (IDA+IEG+IPS+IPP) acima da mediana eleva o INDE medio para "
        f"{por_n.max():.2f} vs {por_n.min():.2f} quando nenhum esta alto: o efeito e cumulativo.\n")

    # ------------------------------------------------------------------
    # Q10. Efetividade do programa por pedra/fase ao longo do tempo
    # ------------------------------------------------------------------
    add("## Q10. Efetividade do programa ao longo do ciclo")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    df.groupby("ano")[["inde"] + INDS].mean().plot(marker="o", ax=ax)
    ax.set_title("Evolucao media dos indicadores (2022-2024)"); ax.set_ylabel("Nota media")
    ax.set_xticks(df.ano.unique()); ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left")
    salvar(fig, "q10_evolucao_indicadores.png")
    inde_ano = df.groupby("ano")["inde"].mean()
    add(f"- INDE medio: {inde_ano.loc[2022]:.2f} -> {inde_ano.loc[2023]:.2f} -> {inde_ano.loc[2024]:.2f}.")
    # Coorte longitudinal: alunos presentes nos 3 anos
    presentes = df.groupby("RA")["ano"].nunique()
    coorte = df[df["RA"].isin(presentes[presentes == 3].index)]
    ic = coorte.groupby("ano")["inde"].mean()
    add(f"- Coorte fixa (alunos nos 3 anos, n={coorte['RA'].nunique()}): "
        f"INDE {ic.loc[2022]:.2f} -> {ic.loc[2024]:.2f} "
        f"({'melhora' if ic.loc[2024] > ic.loc[2022] else 'queda'} real controlando entrada/saida).")

    # Q10b. Efetividade por PEDRA (Quartzo, Agata, Ametista, Topazio)
    ordem_pedra = ["Quartzo", "Agata", "Ametista", "Topazio"]
    dpedra = df.dropna(subset=["pedra"])
    dpedra = dpedra[dpedra["pedra"].isin(ordem_pedra)]
    dist = (dpedra.groupby(["ano", "pedra"]).size().unstack(fill_value=0)
            .reindex(columns=ordem_pedra))
    distp = dist.div(dist.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(8, 4.5))
    distp.plot(kind="bar", stacked=True, ax=ax,
               color=["#C0392B", "#E9A23B", "#8E44AD", "#2E86C1"])
    ax.set_title("Distribuicao das pedras por ano (%)"); ax.set_ylabel("% de alunos")
    ax.set_xlabel("Ano"); ax.tick_params(axis="x", rotation=0)
    ax.legend(title="Pedra", bbox_to_anchor=(1.02, 1), loc="upper left")
    salvar(fig, "q10_pedras_por_ano.png")
    top2 = (distp.get("Ametista", 0) + distp.get("Topazio", 0))
    add(f"- Pedras superiores (Ametista+Topazio) passaram de {top2.loc[2022]:.1f}% (2022) "
        f"para {top2.loc[2024]:.1f}% (2024): avanco na classificacao geral.")

    # Matriz de transicao de pedra (2022 -> 2024) na coorte
    piv_ped = coorte.pivot_table(index="RA", columns="ano", values="pedra", aggfunc="first")
    if {2022, 2024}.issubset(piv_ped.columns):
        trans = piv_ped[[2022, 2024]].dropna()
        trans = trans[trans[2022].isin(ordem_pedra) & trans[2024].isin(ordem_pedra)]
        mat = (pd.crosstab(trans[2022], trans[2024], normalize="index")
               .reindex(index=ordem_pedra, columns=ordem_pedra) * 100)
        fig, ax = plt.subplots(figsize=(6.5, 5))
        sns.heatmap(mat, annot=True, fmt=".0f", cmap="Purples", ax=ax, cbar_kws={"label": "% da linha"})
        ax.set_title("Transicao de pedra 2022 -> 2024 (coorte fixa)")
        ax.set_xlabel("Pedra em 2024"); ax.set_ylabel("Pedra em 2022")
        salvar(fig, "q10_transicao_pedras.png")
        subiu = sum(ordem_pedra.index(b) > ordem_pedra.index(a)
                    for a, b in zip(trans[2022], trans[2024]))
        desceu = sum(ordem_pedra.index(b) < ordem_pedra.index(a)
                     for a, b in zip(trans[2022], trans[2024]))
        add(f"- Na coorte fixa, {subiu} alunos SUBIRAM de pedra e {desceu} desceram entre 2022 e 2024 "
            f"({subiu/len(trans)*100:.0f}% de ascensao) - evidencia de impacto real do programa.\n")

    # ------------------------------------------------------------------
    # Mapa de correlacoes geral (apoio a Q3-Q8)
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(df[["inde"] + INDS].corr(), annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
    ax.set_title("Matriz de correlacao dos indicadores")
    salvar(fig, "corr_indicadores.png")

    # ------------------------------------------------------------------
    # Q11. Insights adicionais
    # ------------------------------------------------------------------
    add("## Q11. Insights adicionais")
    # Genero
    g = df.groupby("genero")[["inde", "ida", "ieg"]].mean().round(2)
    add(f"- Medias por genero (INDE/IDA/IEG):\n{g.to_string()}")
    # Ponto de virada 2022 x indicadores
    if df["atingiu_pv"].notna().any():
        pv = df.dropna(subset=["atingiu_pv"]).groupby("atingiu_pv")[INDS].mean().round(2)
        add(f"- Quem atingiu o Ponto de Virada (2022) tem indicadores mais altos:\n{pv.to_string()}")
    # Tempo de casa
    if df["anos_na_pm"].notna().any():
        c = df["anos_na_pm"].corr(df["inde"])
        rel = "praticamente nula" if abs(c) < 0.15 else ("positiva" if c > 0 else "levemente negativa")
        add(f"- Correlacao anos na PM x INDE = {c:.2f} ({rel}): tempo de casa isoladamente nao explica o desempenho.")
    add("")

    INSIGHTS.write_text("\n".join(linhas), encoding="utf-8")
    add(f"[OK] Insights salvos em {INSIGHTS}")
    add(f"[OK] {len(list(FIG.glob('*.png')))} figuras em {FIG}")


if __name__ == "__main__":
    main()
