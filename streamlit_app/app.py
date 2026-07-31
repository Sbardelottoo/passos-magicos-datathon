"""
Aplicacao Streamlit — Passos Magicos | Preditor de Risco de Defasagem.

Ferramenta de apoio a decisao pedagogica:
  • Predicao individual com EXPLICACAO, recomendacoes de acao e PDF
  • Turma priorizada (upload da planilha PEDE crua OU CSV de features)
  • Historico do aluno (trajetoria real 2022-2024) com PDF
  • Panorama dos indicadores (2022–2024)

Deploy: Streamlit Community Cloud · Main file = streamlit_app/app.py
Local:  streamlit run streamlit_app/app.py
"""
from pathlib import Path
import sys
import json
import numpy as np
import pandas as pd
import joblib
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "src"))
from explicador import baseline_de, explica_aluno, recomendacoes_para, ROTULOS  # noqa: E402
from validacao import valida_features  # noqa: E402
from relatorio import gerar_pdf_aluno  # noqa: E402
import limpeza  # noqa: E402

MODEL_PATH = BASE / "models" / "modelo_risco.joblib"
META_PATH = BASE / "models" / "modelo_meta.json"
DATA_PATH = BASE / "data" / "processed" / "pede_unificado.csv"
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "logo_passos_magicos.png"
FIGURES = BASE / "reports" / "figures"

st.set_page_config(page_title="Passos Mágicos — Risco de Defasagem",
                   page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "🎓",
                   layout="wide")

if LOGO_PATH.exists():
    st.logo(str(LOGO_PATH), size="large")

INDS = ["ian", "ida", "ieg", "iaa", "ips", "ipp", "ipv"]

# Paleta central (identidade Passos Mágicos: azul + dourado)
AZUL = "#0A5FA8"        # primário
DOURADO = "#E9A23B"     # acento
COR_RISCO = "#C0392B"   # vermelho — em risco
COR_OK = "#2E9E5B"      # verde — sem risco
COR_NEUTRO = "#95A5A6"  # cinza — referência/média
# Defasagem: escala sequencial (bom -> ruim)
CORES_DEFASAGEM = ["#2E9E5B", "#8FD19E", DOURADO, COR_RISCO]
# Pedras: cores semânticas da gema (mantidas distintas do vermelho de "risco")
CORES_PEDRAS = {"Quartzo": "#B0BEC5", "Agata": "#7FB3D5",
                "Ametista": "#8E44AD", "Topazio": DOURADO}
ORDEM_PEDRAS = ["Quartzo", "Agata", "Ametista", "Topazio"]


@st.cache_resource
def carrega_modelo():
    return joblib.load(MODEL_PATH), json.loads(META_PATH.read_text(encoding="utf-8"))


@st.cache_data
def carrega_dados():
    return pd.read_csv(DATA_PATH)


@st.cache_data
def limpa_planilha(conteudo: bytes):
    """Roda o pipeline de limpeza sobre uma planilha PEDE crua enviada."""
    import io
    return limpeza.unifica(io.BytesIO(conteudo))


@st.cache_data
def metricas_no_limiar(_modelo, dados, feats, limiar):
    """Recalcula precisão/recall/matriz de confusão no conjunto de teste,
    reconstruindo o mesmo split do treino (sem alterar o modelo salvo)."""
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
    d = dados.sort_values(["RA", "ano"]).copy()
    d["defasagem_prox"] = d.groupby("RA")["defasagem"].shift(-1)
    d = d[d["defasagem_prox"].notna()].copy()
    d["y"] = (d["defasagem_prox"] < d["defasagem"]).astype(int)
    _, X_te, _, y_te = train_test_split(
        d[feats], d["y"], test_size=0.25, stratify=d["y"], random_state=42)
    proba = _modelo.predict_proba(X_te)[:, 1]
    pred = (proba >= limiar).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_te, pred).ravel()
    return {
        "precisao": precision_score(y_te, pred, zero_division=0),
        "recall": recall_score(y_te, pred, zero_division=0),
        "f1": f1_score(y_te, pred, zero_division=0),
        "matriz": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "n_teste": int(len(y_te)),
    }


try:
    modelo, meta = carrega_modelo()
    LIMIAR = float(meta.get("limiar_padrao", 0.5))
    NUM_FEATS = meta["features_numericas"]
    CAT_FEATS = meta["features_categoricas"]
    FEATS = NUM_FEATS + CAT_FEATS
except Exception as e:
    st.error(f"Não foi possível carregar o modelo: {e}\n\n"
             "Execute `python src/modelo.py` para gerar `models/modelo_risco.joblib`.")
    st.stop()

df = carrega_dados()
BASELINE = baseline_de(df, NUM_FEATS, CAT_FEATS)
COORTE_MEDIA = df[INDS].mean()

# --------------------------- Sidebar ---------------------------
with st.sidebar:
    st.caption("Preditor de Risco de Defasagem · Datathon PosTech Fase 5")
    auc = meta["metricas"][meta["melhor_modelo"]]["AUC (teste)"]
    st.markdown(
        f"""**Modelo:** {meta['melhor_modelo']}
**AUC (teste):** {auc:.2f}
**Alvo:** {meta['definicao_target']}
**Limiar de alerta:** {LIMIAR:.2f}"""
    )
    st.markdown("**Legenda:** 🔴 em risco · 🟢 sem risco imediato")
    st.divider()
    st.caption("Ferramenta de **apoio** à decisão pedagógica — não substitui a "
               "avaliação profissional das equipes.")

# --------------------------- Header ---------------------------
hcol1, hcol2 = st.columns([1, 8], vertical_alignment="center")
with hcol1:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=90)
with hcol2:
    st.title("Preditor de Risco de Defasagem")
    st.caption("Associação Passos Mágicos · antecipando o risco para agir antes")

with st.expander("ℹ️ Como usar esta ferramenta (clique para abrir)", expanded=True):
    st.markdown(
        """
Esta aplicação estima a **probabilidade de a defasagem de um aluno piorar no
próximo ano**, a partir dos seus indicadores atuais. Ela serve para **priorizar
o acompanhamento** de quem mais precisa.

- **🔮 Simulador (what-if):** teste um perfil de aluno, veja o risco, **por que**
  ele é alto e **quais ações** são sugeridas. Baixe um **relatório em PDF**.
- **📋 Turma priorizada:** envie a **planilha PEDE** (ou um CSV) e receba a lista
  de alunos ordenada por risco, pronta para agir.
- **📈 Histórico do aluno:** escolha um RA real e veja a **trajetória** dos
  indicadores de 2022 a 2024, com o risco calculado a partir dos dados mais
  recentes.
- **📊 Panorama:** a evolução dos indicadores e das pedras de 2022 a 2024.
- **🧠 Sobre o modelo:** desempenho, limitações e como ele foi construído.

> 🔴 acima do limiar = risco · 🟢 abaixo = sem risco imediato.
> **p.p.** = pontos percentuais (ex.: "+8 p.p." = o risco sobe 8 pontos).
        """
    )

with st.expander("📖 Glossário dos indicadores"):
    st.markdown("\n".join(f"- **{ROTULOS[i].split(' ')[0]}** — "
                          f"{ROTULOS[i].split('(')[1].rstrip(')')}" for i in INDS)
                + "\n- **INDE** — índice global (pondera todos os indicadores acima)")

aba_pred, aba_turma, aba_historico, aba_panorama, aba_modelo = st.tabs(
    ["🔮 Simulador", "📋 Turma priorizada", "📈 Histórico do aluno",
     "📊 Panorama", "🧠 Sobre o modelo"])

# ===================== ABA 1 — Simulador (what-if) =====================
with aba_pred:
    st.subheader("Simulador de risco (what-if)")
    st.caption("Ajuste um **perfil hipotético** de aluno e veja o risco estimado. "
               "Os valores iniciais são apenas um exemplo — não é um aluno real.")
    c1, c2, c3 = st.columns(3)
    with c1:
        ian = st.slider("IAN — Adequação ao nível", 0.0, 10.0, 5.0, 0.5)
        ida = st.slider("IDA — Aprendizagem", 0.0, 10.0, 6.0, 0.1)
        ieg = st.slider("IEG — Engajamento", 0.0, 10.0, 7.0, 0.1)
    with c2:
        iaa = st.slider("IAA — Autoavaliação", 0.0, 10.0, 8.0, 0.1)
        ips = st.slider("IPS — Psicossocial", 0.0, 10.0, 6.5, 0.1)
        ipp = st.slider("IPP — Psicopedagógico", 0.0, 10.0, 6.0, 0.1)
    with c3:
        ipv = st.slider("IPV — Ponto de virada", 0.0, 10.0, 6.5, 0.1)
        defas = st.select_slider("Defasagem atual (0 = adequado)",
                                 options=[-4, -3, -2, -1, 0, 1, 2], value=-1)
        # INDE é uma ponderação dos demais indicadores; por padrão o estimamos
        # (média dos 7) para evitar combinações impossíveis. Avançado: sobrescrever.
        inde_auto = float(np.mean([ian, ida, ieg, iaa, ips, ipp, ipv]))
        override_inde = st.checkbox("Definir INDE manualmente (avançado)", value=False)
        if override_inde:
            inde = st.slider("INDE — Índice global", 0.0, 10.0, round(inde_auto, 1), 0.1)
        else:
            inde = inde_auto
            st.caption(f"INDE estimado a partir dos indicadores: **{inde:.1f}**")
    c4, c5, c6, c7 = st.columns(4)
    idade = c4.number_input("Idade", 6, 25, 14)
    fase = c5.number_input("Fase", 0, 9, 3)
    anos_pm = c6.number_input("Anos na PM", 0, 15, 2)
    genero = c7.radio("Gênero", ["Feminino", "Masculino"], horizontal=True)

    entrada = pd.DataFrame([{
        "inde": inde, "ida": ida, "ieg": ieg, "iaa": iaa, "ips": ips, "ipp": ipp,
        "ipv": ipv, "ian": ian, "idade": idade, "fase": fase, "defasagem": defas,
        "anos_na_pm": anos_pm, "genero": genero,
    }])

    if st.button("Calcular risco", type="primary"):
        with st.spinner("Calculando..."):
            res = explica_aluno(modelo, entrada, BASELINE, NUM_FEATS, CAT_FEATS)
            prob = float(res["prob_original"].iloc[0])
            em_risco = prob >= LIMIAR

        k1, k2 = st.columns([1, 1])
        with k1:
            st.metric("Probabilidade de piora no próximo ano", f"{prob*100:.1f}%")
            if em_risco:
                st.error("🔴 **ALUNO EM RISCO** — acompanhamento prioritário.")
            else:
                st.success("🟢 **Sem risco imediato** — manter acompanhamento regular.")
            gauge = go.Figure(go.Indicator(
                mode="gauge+number", value=prob * 100,
                number={"suffix": "%"},
                gauge={"axis": {"range": [0, 100]},
                       "bar": {"color": AZUL},
                       "threshold": {"line": {"color": "red", "width": 3},
                                     "value": LIMIAR * 100}}))
            gauge.update_layout(height=220, margin=dict(l=20, r=20, t=10, b=10))
            st.plotly_chart(gauge, width="stretch")
        with k2:
            # Radar do aluno vs media da coorte
            categorias = [ROTULOS[i].split(" ")[0] for i in INDS]
            radar = go.Figure()
            radar.add_trace(go.Scatterpolar(
                r=[entrada[i].iloc[0] for i in INDS], theta=categorias,
                fill="toself", name="Aluno", line_color=AZUL))
            radar.add_trace(go.Scatterpolar(
                r=[COORTE_MEDIA[i] for i in INDS], theta=categorias,
                fill="toself", name="Média da coorte", line_color=COR_NEUTRO, opacity=0.6))
            radar.update_layout(polar=dict(radialaxis=dict(range=[0, 10])),
                                height=340, margin=dict(l=30, r=30, t=30, b=30),
                                title="Perfil do aluno vs média")
            st.plotly_chart(radar, width="stretch")

        st.markdown("#### Por que este risco? Fatores que mais pesam")
        st.caption("Como lemos: para cada indicador, simulamos trocar o valor do "
                   "aluno por um valor típico e medimos quanto o risco cai. Quanto "
                   "maior a barra, mais aquele indicador está elevando o risco.")
        expl = res[res["contribuicao"] > 0].head(5).copy()
        if len(expl):
            expl["impacto"] = (expl["contribuicao"] * 100).round(1)
            figb = px.bar(expl.sort_values("impacto"), x="impacto", y="rotulo",
                          orientation="h", color_discrete_sequence=[AZUL],
                          labels={"impacto": "Aumento no risco (p.p.)", "rotulo": ""})
            figb.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(figb, width="stretch")

            st.markdown("#### Ações sugeridas")
            recs = recomendacoes_para(res, top=3)
            if recs:
                for rot, acao in recs:
                    st.markdown(f"- **{rot}** — {acao}")
            else:
                st.info("Nenhum fator pedagógico crítico isolado; manter acompanhamento.")
        else:
            recs = []
            st.info("O perfil do aluno está acima da média — sem fatores de risco relevantes.")

        pdf_bytes = gerar_pdf_aluno(
            identificacao={"Simulação": "aluno hipotético", "Idade": idade,
                          "Fase": fase, "Gênero": genero},
            indicadores={k.upper(): entrada[k].iloc[0] for k in NUM_FEATS if k in entrada.columns},
            prob=prob, limiar=LIMIAR,
            fatores=[(r["rotulo"], r["contribuicao"] * 100) for _, r in expl.iterrows()] if len(expl) else [],
            recomendacoes=recs,
            logo_path=LOGO_PATH if LOGO_PATH.exists() else None,
        )
        st.download_button("📄 Baixar relatório em PDF (perfil simulado)", pdf_bytes,
                           "relatorio_risco_simulado.pdf", "application/pdf")
        st.caption("⚠️ Este relatório refere-se ao **perfil hipotético** simulado "
                   "acima. Para um aluno real, use a aba *Histórico do aluno*.")

# ===================== ABA 2 — Turma priorizada =====================
with aba_turma:
    st.subheader("Pontuar e priorizar uma turma")
    modo = st.radio("Fonte dos dados",
                    ["Planilha PEDE (mesmo formato do Datathon)", "CSV já no formato de features"],
                    horizontal=False)

    entrada_lote = None
    if modo.startswith("Planilha"):
        st.caption("Envie a planilha `.xlsx` da PEDE (abas por ano). "
                   "A limpeza é feita automaticamente.")
        up = st.file_uploader("Planilha PEDE (.xlsx)", type=["xlsx"])
        if up is not None:
            try:
                with st.spinner("Limpando e unificando a planilha..."):
                    long = limpa_planilha(up.getvalue())
                ano_sel = st.selectbox("Ano de referência",
                                       sorted(long["ano"].unique(), reverse=True))
                entrada_lote = long[long["ano"] == ano_sel].copy()
                st.success(f"{len(entrada_lote)} alunos carregados para {ano_sel}.")
            except Exception as e:
                st.error(f"Não foi possível processar a planilha: {e}")
    else:
        st.caption("CSV com as colunas: " + ", ".join(FEATS) +
                   ". Colunas extras (RA, Nome) são preservadas.")
        exemplo = df.head(20)[[c for c in ["RA"] + FEATS if c in df.columns]]
        st.download_button("Baixar CSV de exemplo", exemplo.to_csv(index=False).encode("utf-8"),
                           "exemplo_alunos.csv", "text/csv")
        upc = st.file_uploader("Arquivo CSV", type=["csv"])
        if upc is not None:
            try:
                entrada_lote = pd.read_csv(upc)
            except Exception as e:
                st.error(f"Não foi possível ler o CSV: {e}")

    if entrada_lote is not None:
        ok, problemas, avisos = valida_features(entrada_lote, NUM_FEATS, CAT_FEATS)
        for a in avisos:
            st.warning(a)
        if not ok:
            for p in problemas:
                st.error(p)
        else:
            # Limiar ajustável: dá controle à equipe (mais sensível = pega mais alunos)
            limiar_turma = st.slider(
                "Sensibilidade do alerta (limiar)", 0.10, 0.90, float(LIMIAR), 0.01,
                help="Menor = sinaliza mais alunos (mais sensível, mais falsos alarmes). "
                     f"Padrão do modelo: {LIMIAR:.2f}.")
            proba = modelo.predict_proba(entrada_lote[FEATS])[:, 1]
            res = entrada_lote.copy()
            res["prob_risco_%"] = (proba * 100).round(1)
            res["risco"] = np.where(proba >= limiar_turma, "🔴 Em risco", "🟢 Sem risco")
            n_risco = int((proba >= limiar_turma).sum())

            m1, m2, m3 = st.columns(3)
            m1.metric("Alunos avaliados", len(res))
            m2.metric("Em risco", n_risco)
            m3.metric("% em risco", f"{n_risco/len(res)*100:.0f}%")

            # Resumo visual: distribuição das probabilidades + corte do limiar
            hist = px.histogram(res, x="prob_risco_%", nbins=20,
                                color_discrete_sequence=[AZUL],
                                labels={"prob_risco_%": "Probabilidade de risco (%)"},
                                title="Distribuição do risco na turma")
            hist.add_vline(x=limiar_turma * 100, line_dash="dash", line_color=COR_RISCO,
                           annotation_text="limiar", annotation_position="top")
            hist.update_layout(height=260, showlegend=False, margin=dict(t=40, b=10))
            st.plotly_chart(hist, width="stretch")

            # Filtros
            f1, f2 = st.columns(2)
            if "fase" in res.columns:
                fases = sorted(res["fase"].dropna().unique())
                sel_f = f1.multiselect("Filtrar por fase", fases, default=fases)
                res = res[res["fase"].isin(sel_f)]
            if "pedra" in res.columns and res["pedra"].notna().any():
                pedras = sorted(res["pedra"].dropna().unique())
                sel_p = f2.multiselect("Filtrar por pedra", pedras, default=pedras)
                res = res[res["pedra"].isin(sel_p) | res["pedra"].isna()]

            res_ord = res.sort_values("prob_risco_%", ascending=False)
            cols_show = [c for c in ["RA", "fase", "pedra", "genero", "defasagem",
                                     "prob_risco_%", "risco"] if c in res.columns]

            # Recorte acionável: Top N em risco
            em_risco_df = res_ord[res_ord["prob_risco_%"] >= limiar_turma * 100]
            if len(em_risco_df):
                topn = min(10, len(em_risco_df))
                st.markdown(f"#### 🎯 Top {topn} para acompanhar primeiro")
                st.dataframe(em_risco_df.head(topn)[cols_show], width="stretch")

            st.markdown("#### Turma completa (ordenada por risco)")
            st.dataframe(res_ord[cols_show], width="stretch", height=340)
            st.download_button("⬇️ Baixar turma priorizada",
                               res_ord.to_csv(index=False).encode("utf-8"),
                               "turma_priorizada.csv", "text/csv", type="primary")

# ===================== ABA 3 — Histórico do aluno =====================
with aba_historico:
    st.subheader("Trajetória real do aluno (2022–2024)")
    st.caption("Escolha um RA da base histórica para ver a evolução dos indicadores "
               "e o risco calculado a partir do ano mais recente disponível.")

    ras_disponiveis = sorted(df["RA"].dropna().unique(), key=str)
    ra_sel = st.selectbox("RA do aluno", ras_disponiveis)

    hist = df[df["RA"] == ra_sel].sort_values("ano").copy()
    if hist.empty:
        st.warning("Nenhum registro encontrado para esse RA.")
    else:
        anos_aluno = hist["ano"].tolist()
        st.caption(f"Registros encontrados em: {', '.join(str(a) for a in anos_aluno)}")

        h1, h2 = st.columns(2)
        with h1:
            eh = hist.melt(id_vars="ano", value_vars=["inde"] + INDS,
                           var_name="indicador", value_name="valor")
            fig = px.line(eh, x="ano", y="valor", color="indicador", markers=True,
                          title="Evolução dos indicadores do aluno")
            fig.update_layout(xaxis=dict(tickmode="array", tickvals=anos_aluno),
                              yaxis=dict(range=[0, 10]))
            st.plotly_chart(fig, width="stretch")
        with h2:
            cols_hist = [c for c in ["ano", "fase", "pedra", "defasagem",
                                     "categoria_defasagem"] + INDS if c in hist.columns]
            st.dataframe(hist[cols_hist], width="stretch", height=280)

        # Risco calculado a partir do registro mais recente do aluno. Valores
        # ausentes (ex.: IPP nao existia em 2022) sao imputados pelo proprio
        # pipeline do modelo — não é preciso exigir todos os indicadores.
        ultimo = hist.dropna(subset=["defasagem"]).tail(1)
        if ultimo.empty:
            st.info("Não há dados suficientes para calcular o risco deste aluno.")
        else:
            linha = ultimo.iloc[0]
            entrada_h = pd.DataFrame([{c: linha.get(c) for c in FEATS}])
            res_h = explica_aluno(modelo, entrada_h, BASELINE, NUM_FEATS, CAT_FEATS)
            prob_h = float(res_h["prob_original"].iloc[0])
            em_risco_h = prob_h >= LIMIAR

            st.markdown(f"#### Risco calculado com os dados de {int(linha['ano'])}")
            k1, k2 = st.columns([1, 1.4])
            with k1:
                st.metric("Probabilidade de piora no próximo ano", f"{prob_h*100:.1f}%")
                if em_risco_h:
                    st.error("🔴 **ALUNO EM RISCO** — acompanhamento prioritário.")
                else:
                    st.success("🟢 **Sem risco imediato** — manter acompanhamento regular.")
            with k2:
                expl_h = res_h[res_h["contribuicao"] > 0].head(5).copy()
                if len(expl_h):
                    expl_h["impacto"] = (expl_h["contribuicao"] * 100).round(1)
                    figb = px.bar(expl_h.sort_values("impacto"), x="impacto", y="rotulo",
                                  orientation="h", color_discrete_sequence=[AZUL],
                                  labels={"impacto": "Aumento no risco (p.p.)", "rotulo": ""},
                                  title="Fatores que mais pesam")
                    figb.update_layout(height=220, margin=dict(l=10, r=10, t=30, b=10))
                    st.plotly_chart(figb, width="stretch")

            recs_h = recomendacoes_para(res_h, top=3)
            if recs_h:
                st.markdown("#### Ações sugeridas")
                for rot, acao in recs_h:
                    st.markdown(f"- **{rot}** — {acao}")

            pdf_bytes_h = gerar_pdf_aluno(
                identificacao={"RA": ra_sel, "Ano de referência": int(linha["ano"]),
                              "Fase": linha.get("fase"), "Pedra": linha.get("pedra"),
                              "Gênero": linha.get("genero")},
                indicadores={k.upper(): linha.get(k) for k in NUM_FEATS if k in hist.columns},
                prob=prob_h, limiar=LIMIAR,
                fatores=[(r["rotulo"], r["contribuicao"] * 100) for _, r in expl_h.iterrows()] if len(expl_h) else [],
                recomendacoes=recs_h,
                logo_path=LOGO_PATH if LOGO_PATH.exists() else None,
            )
            st.download_button("📄 Baixar relatório em PDF", pdf_bytes_h,
                               f"relatorio_risco_RA{ra_sel}.pdf", "application/pdf")

# ===================== ABA 4 — Panorama =====================
with aba_panorama:
    st.subheader("Panorama dos indicadores (2022–2024)")

    # --- KPIs-âncora (calculados ao vivo) ---
    def pct_cat(ano, cats):
        d = df[df["ano"] == ano]
        return d["categoria_defasagem"].isin(cats).mean() * 100

    def pct_pedra(ano, pedras):
        d = df[(df["ano"] == ano) & df["pedra"].notna()]
        return d["pedra"].isin(pedras).mean() * 100

    sev22, sev24 = pct_cat(2022, ["Defasagem moderada/severa"]), pct_cat(2024, ["Defasagem moderada/severa"])
    inde22, inde24 = df[df.ano == 2022]["inde"].mean(), df[df.ano == 2024]["inde"].mean()
    top22, top24 = pct_pedra(2022, ["Ametista", "Topazio"]), pct_pedra(2024, ["Ametista", "Topazio"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Alunos únicos", f"{df['RA'].nunique():,}".replace(",", "."))
    k2.metric("Defasagem mod./severa", f"{sev24:.1f}%", f"{sev24 - sev22:+.1f} p.p. vs 2022",
              delta_color="inverse")
    k3.metric("INDE médio", f"{inde24:.2f}", f"{inde24 - inde22:+.2f} vs 2022")
    k4.metric("Pedras superiores", f"{top24:.0f}%", f"{top24 - top22:+.1f} p.p. vs 2022")
    st.caption("Pedras superiores = Ametista + Topázio. "
               "Verde nos KPIs indica evolução positiva para o aluno.")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        ordem = ["Adiantado", "Adequado", "Defasagem leve", "Defasagem moderada/severa"]
        tab = df.groupby(["ano", "categoria_defasagem"]).size().reset_index(name="n")
        fig = px.bar(tab, x="ano", y="n", color="categoria_defasagem",
                     category_orders={"categoria_defasagem": ordem},
                     color_discrete_sequence=CORES_DEFASAGEM,
                     title="Perfil de defasagem por ano", labels={"n": "nº de alunos"})
        fig.update_layout(xaxis=dict(tickmode="array", tickvals=[2022, 2023, 2024]))
        st.plotly_chart(fig, width="stretch")
    with col2:
        dp = df[df["pedra"].isin(ORDEM_PEDRAS)]
        tp = dp.groupby(["ano", "pedra"]).size().reset_index(name="n")
        fig = px.bar(tp, x="ano", y="n", color="pedra",
                     category_orders={"pedra": ORDEM_PEDRAS},
                     color_discrete_map=CORES_PEDRAS,
                     title="Distribuição das pedras por ano", labels={"n": "nº de alunos"})
        fig.update_layout(xaxis=dict(tickmode="array", tickvals=[2022, 2023, 2024]))
        st.plotly_chart(fig, width="stretch")

    col3, col4 = st.columns(2)
    with col3:
        ev = df.groupby("ano")[["inde"] + INDS].mean().reset_index().melt(
            id_vars="ano", var_name="indicador", value_name="media")
        fig = px.line(ev, x="ano", y="media", color="indicador", markers=True,
                      title="Evolução média dos indicadores")
        fig.update_layout(xaxis=dict(tickmode="array", tickvals=[2022, 2023, 2024]))
        st.plotly_chart(fig, width="stretch")
    with col4:
        corr = df[["inde"] + INDS].corr()
        fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                        zmin=-1, zmax=1, title="Correlação entre indicadores")
        st.plotly_chart(fig, width="stretch")

    # --- Insights da análise trazidos para o app ---
    st.divider()
    st.markdown("### 🔎 O que os dados mostram")
    i1, i2 = st.columns(2)
    with i1:
        if (FIGURES / "q10_transicao_pedras.png").exists():
            st.image(str(FIGURES / "q10_transicao_pedras.png"),
                     caption="Mobilidade entre pedras (coorte fixa 2022→2024): "
                             "130 alunos subiram de nível — 29% de ascensão.")
    with i2:
        if (FIGURES / "q8_combinacoes_inde.png").exists():
            st.image(str(FIGURES / "q8_combinacoes_inde.png"),
                     caption="Efeito cumulativo: com IDA+IEG+IPS+IPP acima da mediana, "
                             "o INDE médio salta para 8,4 (vs 6,0 quando nenhum está alto).")
    i3, i4 = st.columns(2)
    with i3:
        if (FIGURES / "q5_ips_antecede_queda.png").exists():
            st.image(str(FIGURES / "q5_ips_antecede_queda.png"),
                     caption="Alerta precoce: quem cai de desempenho no ano seguinte tinha "
                             "IPS mais baixo (5,8 vs 6,4) — o psicossocial antecede a queda.")
    with i4:
        st.markdown(
            "**Efetividade do programa (coorte fixa)**\n\n"
            "Considerando apenas os 468 alunos presentes nos 3 anos (controlando "
            "entrada e saída), o INDE médio se mantém em ~7,4 e a maioria sobe de "
            "pedra — evidência de **impacto real**, não apenas troca de alunos.")

# ===================== ABA 5 — Sobre o modelo =====================
with aba_modelo:
    st.subheader("Sobre o modelo preditivo")
    st.markdown(
        f"""**O que ele prevê:** a probabilidade de a **defasagem de um aluno piorar
no ano seguinte** — um alerta precoce para priorizar acompanhamento.

**Como foi construído:** ligamos cada aluno entre anos (chave RA) e treinamos com
os indicadores do ano atual para prever a piora no ano seguinte. Modelo escolhido:
**{meta['melhor_modelo']}**.""")

    met = metricas_no_limiar(modelo, df, FEATS, LIMIAR)
    prev = meta.get("prevalencia_risco", 0.17)
    m = met["matriz"]

    st.markdown("#### Desempenho (conjunto de teste)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AUC (teste)", f"{meta['metricas'][meta['melhor_modelo']]['AUC (teste)']:.2f}")
    c2.metric("Recall (sensibilidade)", f"{met['recall']*100:.0f}%",
              help="Dos alunos que realmente pioram, quantos o modelo captura.")
    c3.metric("Precisão", f"{met['precisao']*100:.0f}%",
              help="Dos alunos sinalizados, quantos realmente pioram.")
    c4.metric("Prevalência do risco", f"{prev*100:.0f}%",
              help="Proporção de alunos que de fato pioram — a base é desbalanceada.")

    st.info(
        f"**Como ler com honestidade:** no limiar de alerta ({LIMIAR:.2f}), o modelo "
        f"**captura ~{met['recall']*100:.0f}%** dos alunos que vão piorar (bom para "
        f"não deixar ninguém para trás), mas **~{(1-met['precisao'])*100:.0f}% dos "
        "sinalizados** podem ser falsos alarmes. Por isso a ferramenta é de **triagem/"
        "priorização** — a decisão final é sempre da equipe.")

    st.markdown("#### Comparativo dos modelos testados")
    comp = pd.DataFrame(meta["metricas"]).T[["AUC (CV)", "AUC (teste)", "PR-AUC (teste)"]].round(3)
    st.dataframe(comp, width="stretch")

    g1, g2, g3 = st.columns(3)
    for col, arq, leg in [
        (g1, "modelo_roc.png", "Curva ROC — separa quem piora de quem não piora."),
        (g2, "modelo_matriz_confusao.png",
         f"Matriz de confusão — acertos e erros no limiar {LIMIAR:.2f}."),
        (g3, "modelo_importancias.png", "Variáveis que mais influenciam a previsão."),
    ]:
        if (FIGURES / arq).exists():
            col.image(str(FIGURES / arq), caption=leg)

    with st.expander("⚠️ Limitações e uso responsável"):
        st.markdown(
            f"""
- **Não é diagnóstico.** É uma ferramenta de **apoio à priorização**; a avaliação
  final é sempre das equipes pedagógica, psicológica e psicopedagógica.
- **Falsos alarmes existem** (precisão ~{met['precisao']*100:.0f}%): um aluno
  sinalizado pode não piorar. Melhor investigar a mais do que a menos.
- **INDE entre as variáveis:** o INDE é uma ponderação dos demais indicadores
  (R²≈1,0). Como o modelo prevê a **mudança futura** (e não o nível atual), isso
  não gera vazamento — usamos o estado atual do aluno para antecipar a trajetória.
- **Base limitada** a 2022–2024 e ao público da Passos Mágicos; reavaliar o modelo
  a cada novo ciclo da PEDE.
""")

st.divider()
st.caption("Datathon PosTech · Fase 5 — Associação Passos Mágicos.")
