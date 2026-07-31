"""
Aplicacao Streamlit — Passos Magicos | Preditor de Risco de Defasagem.

Ferramenta de apoio a decisao pedagogica:
  • Predicao individual com EXPLICACAO e recomendacoes de acao
  • Turma priorizada (upload da planilha PEDE crua OU CSV de features)
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
import limpeza  # noqa: E402

MODEL_PATH = BASE / "models" / "modelo_risco.joblib"
META_PATH = BASE / "models" / "modelo_meta.json"
DATA_PATH = BASE / "data" / "processed" / "pede_unificado.csv"

st.set_page_config(page_title="Passos Mágicos — Risco de Defasagem",
                   page_icon="🎓", layout="wide")

INDS = ["ian", "ida", "ieg", "iaa", "ips", "ipp", "ipv"]
ROXO = "#8E44AD"


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
    st.markdown(f"## 🎓 Passos Mágicos")
    st.caption("Preditor de Risco de Defasagem · Datathon PosTech Fase 5")
    auc = meta["metricas"][meta["melhor_modelo"]]["AUC (teste)"]
    st.markdown(
        f"""**Modelo:** {meta['melhor_modelo']}
**AUC (teste):** {auc:.2f}
**Alvo:** {meta['definicao_target']}
**Limiar de alerta:** {LIMIAR:.2f}"""
    )
    st.divider()
    st.caption("Ferramenta de **apoio** à decisão pedagógica — não substitui a "
               "avaliação profissional das equipes.")

st.title("Preditor de Risco de Defasagem")

with st.expander("ℹ️ Como usar esta ferramenta (clique para abrir)", expanded=False):
    st.markdown(
        """
Esta aplicação estima a **probabilidade de a defasagem de um aluno piorar no
próximo ano**, a partir dos seus indicadores atuais. Ela serve para **priorizar
o acompanhamento** de quem mais precisa.

- **🔮 Predição individual:** simule um aluno, veja o risco, **por que** ele é
  alto e **quais ações** são sugeridas.
- **📋 Turma priorizada:** envie a **planilha PEDE** (ou um CSV) e receba a lista
  de alunos ordenada por risco, pronta para agir.
- **📊 Panorama:** a evolução dos indicadores e das pedras de 2022 a 2024.

> 🔴 acima do limiar = risco · 🟢 abaixo = sem risco imediato.
        """
    )

aba_pred, aba_turma, aba_panorama = st.tabs(
    ["🔮 Predição individual", "📋 Turma priorizada", "📊 Panorama"])

# ===================== ABA 1 — Predição individual =====================
with aba_pred:
    st.subheader("Simular um aluno")
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
        inde = st.slider("INDE — Índice global", 0.0, 10.0, 6.8, 0.1)
        defas = st.select_slider("Defasagem atual (0 = adequado)",
                                 options=[-4, -3, -2, -1, 0, 1, 2], value=-1)
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
                       "bar": {"color": ROXO},
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
                fill="toself", name="Aluno", line_color=ROXO))
            radar.add_trace(go.Scatterpolar(
                r=[COORTE_MEDIA[i] for i in INDS], theta=categorias,
                fill="toself", name="Média da coorte", line_color="#95A5A6", opacity=0.6))
            radar.update_layout(polar=dict(radialaxis=dict(range=[0, 10])),
                                height=340, margin=dict(l=30, r=30, t=30, b=30),
                                title="Perfil do aluno vs média")
            st.plotly_chart(radar, width="stretch")

        st.markdown("#### Por que este risco? Fatores que mais pesam")
        expl = res[res["contribuicao"] > 0].head(5).copy()
        if len(expl):
            expl["impacto"] = (expl["contribuicao"] * 100).round(1)
            figb = px.bar(expl.sort_values("impacto"), x="impacto", y="rotulo",
                          orientation="h", color_discrete_sequence=[ROXO],
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
            st.info("O perfil do aluno está acima da média — sem fatores de risco relevantes.")

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
            entrada_lote = pd.read_csv(upc)

    if entrada_lote is not None:
        ok, problemas, avisos = valida_features(entrada_lote, NUM_FEATS, CAT_FEATS)
        for a in avisos:
            st.warning(a)
        if not ok:
            for p in problemas:
                st.error(p)
        else:
            proba = modelo.predict_proba(entrada_lote[FEATS])[:, 1]
            res = entrada_lote.copy()
            res["prob_risco_%"] = (proba * 100).round(1)
            res["risco"] = np.where(proba >= LIMIAR, "🔴 Em risco", "🟢 Sem risco")
            n_risco = int((proba >= LIMIAR).sum())

            m1, m2, m3 = st.columns(3)
            m1.metric("Alunos avaliados", len(res))
            m2.metric("Em risco", n_risco)
            m3.metric("% em risco", f"{n_risco/len(res)*100:.0f}%")

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

            cols_show = [c for c in ["RA", "fase", "pedra", "genero", "defasagem",
                                     "prob_risco_%", "risco"] if c in res.columns]
            st.dataframe(res.sort_values("prob_risco_%", ascending=False)[cols_show],
                         width="stretch", height=380)
            st.download_button("⬇️ Baixar turma priorizada",
                               res.sort_values("prob_risco_%", ascending=False).to_csv(index=False).encode("utf-8"),
                               "turma_priorizada.csv", "text/csv", type="primary")

# ===================== ABA 3 — Panorama =====================
with aba_panorama:
    st.subheader("Panorama dos indicadores (2022–2024)")
    col1, col2 = st.columns(2)
    with col1:
        ordem = ["Adiantado", "Adequado", "Defasagem leve", "Defasagem moderada/severa"]
        tab = df.groupby(["ano", "categoria_defasagem"]).size().reset_index(name="n")
        fig = px.bar(tab, x="ano", y="n", color="categoria_defasagem",
                     category_orders={"categoria_defasagem": ordem},
                     color_discrete_sequence=["#4C9A2A", "#8FBF60", "#E9A23B", "#C0392B"],
                     title="Perfil de defasagem por ano", labels={"n": "nº de alunos"})
        st.plotly_chart(fig, width="stretch")
    with col2:
        ordem_p = ["Quartzo", "Agata", "Ametista", "Topazio"]
        dp = df[df["pedra"].isin(ordem_p)]
        tp = dp.groupby(["ano", "pedra"]).size().reset_index(name="n")
        fig = px.bar(tp, x="ano", y="n", color="pedra",
                     category_orders={"pedra": ordem_p},
                     color_discrete_sequence=["#C0392B", "#E9A23B", "#8E44AD", "#2E86C1"],
                     title="Distribuição das pedras por ano", labels={"n": "nº de alunos"})
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

st.divider()
st.caption("Datathon PosTech · Fase 5 — Associação Passos Mágicos.")
