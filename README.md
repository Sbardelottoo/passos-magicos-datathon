# Datathon PosTech · Fase 5 — Associação Passos Mágicos

Análise de dados, storytelling e **modelo preditivo de risco de defasagem** a
partir da Pesquisa Extensiva do Desenvolvimento Educacional (PEDE) de
**2022, 2023 e 2024**.

> A Associação Passos Mágicos usa a educação para transformar a vida de crianças
> e jovens em vulnerabilidade social. Este projeto ajuda a equipe a **enxergar a
> evolução dos alunos** e a **antecipar quem corre risco de defasagem**, para agir
> antes da queda.

---

## 🚀 Acesso rápido

- **▶️ App publicado (Streamlit Community Cloud):** https://paapps-magicos-datathon-mbjdeucxaqr7pkuodmftr6.streamlit.app/

## 🔗 Entregáveis

| Entregável do enunciado | Onde está |
|---|---|
| Código de **limpeza e análise** de dados | [`src/limpeza.py`](src/limpeza.py) · [`src/analise.py`](src/analise.py) |
| **Notebook** do modelo preditivo (feature eng. → split → modelagem → avaliação) | [`notebooks/modelo_preditivo_risco.ipynb`](notebooks/modelo_preditivo_risco.ipynb) |
| **Aplicação Streamlit** (deploy no Community Cloud) | [app publicado](https://paapps-magicos-datathon-mbjdeucxaqr7pkuodmftr6.streamlit.app/) · [`streamlit_app/app.py`](streamlit_app/app.py) |
| Respostas às **11 perguntas** de negócio | [`RESPOSTAS.md`](RESPOSTAS.md) · [`reports/insights.md`](reports/insights.md) |
| Insights e figuras | [`reports/`](reports/) |

> ✅ Mapa completo "pergunta do enunciado → onde está respondida": veja
> [**RESPOSTAS.md**](RESPOSTAS.md).

---

## 📁 Estrutura

```
passos-magicos-datathon/
├── data/
│   ├── raw/               # base original (PEDE_PASSOS_DATASET.xlsx)
│   └── processed/         # dataset unificado gerado pela limpeza
├── src/
│   ├── limpeza.py         # 1. limpeza + unificação (aba-por-ano -> tabela longa)
│   ├── analise.py         # 2. EDA respondendo as 11 perguntas -> figuras + insights
│   ├── modelo.py          # 3. treino/avaliação do modelo -> models/
│   ├── explicador.py      # explicabilidade local + recomendações (usado pelo app)
│   ├── validacao.py       # validação de dados com mensagens amigáveis
│   ├── gera_notebook.py   # gera o .ipynb executado
│   ├── relatorio.py       # exportação de relatório em PDF por aluno
│   └── gera_apresentacao.py
├── notebooks/
│   └── modelo_preditivo_risco.ipynb
├── models/
│   ├── modelo_risco.joblib   # pipeline treinado (pré-proc + modelo)
│   └── modelo_meta.json      # métricas, features e limiar
├── reports/
│   ├── figures/           # gráficos (.png) — inclui pedras e combinações
│   └── insights.md        # respostas às perguntas de negócio
├── tests/test_pipeline.py # testes automatizados (pytest)
├── streamlit_app/
│   ├── app.py
│   └── assets/logo_passos_magicos.png
├── .streamlit/config.toml # tema visual (azul/dourado da Passos Mágicos)
├── apresentacao/storytelling_passos_magicos.pptx
├── docs/
│   ├── roteiro_video.md
│   └── deploy_streamlit.md
├── .python-version / runtime.txt  # versão do Python fixada para o deploy
└── requirements.txt
```

## 🖥️ A aplicação (experiência do usuário)

- **🔮 Predição individual** — probabilidade de risco + medidor, **radar do aluno
  vs média da coorte**, **explicação dos fatores** que mais elevam o risco,
  **ações pedagógicas sugeridas** e **exportação em PDF**.
- **📋 Turma priorizada** — envie a **planilha PEDE crua** (a limpeza roda
  automaticamente) ou um CSV; recebe a lista de alunos **ordenada por risco**,
  com filtros por fase/pedra e exportação.
- **📈 Histórico do aluno** — escolha um RA real e veja a **trajetória dos
  indicadores de 2022–2024**, com o risco calculado a partir do registro mais
  recente e exportação em PDF.
- **📊 Panorama** — evolução dos indicadores, distribuição das pedras e
  correlações (2022–2024).
- Identidade visual da **Associação Passos Mágicos** (logo oficial + paleta
  azul/dourado) na sidebar, favicon e relatórios em PDF.

## ✅ Testes

```bash
pytest -q          # valida limpeza, validação, contrato do modelo e explicador
```

---

## ▶️ Como reproduzir

```bash
# 1. Ambiente
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Pipeline completo
python src/limpeza.py            # gera data/processed/pede_unificado.csv
python src/analise.py            # gera reports/figures/*.png e reports/insights.md
python src/modelo.py             # treina e salva models/modelo_risco.joblib
python src/gera_notebook.py      # (opcional) regera o notebook executado
python src/gera_apresentacao.py  # (opcional) regera o PPTX

# 3. Aplicação
streamlit run streamlit_app/app.py
```

---

## 🧠 O modelo em uma frase

Estima a **probabilidade de a defasagem de um aluno piorar no ano seguinte**
(alvo longitudinal, construído ligando cada aluno pela chave `RA`), usando os
**indicadores atuais** (IAN, IDA, IEG, IAA, IPS, IPP, IPV, INDE), idade, fase e
tempo de casa.

- **Melhor modelo:** Random Forest · **AUC (teste) = 0,88** · **Recall (risco) = 73%**
- **Por que prever a *mudança* e não o *nível*:** a defasagem atual é praticamente
  determinística (deriva de idade × fase); prever o nível seria reproduzir a
  fórmula. Prever a **piora futura** torna o modelo genuinamente preditivo e útil
  para intervenção precoce — exatamente o que o enunciado pede
  (*"antes de queda no desempenho ou aumento da defasagem"*).

---

## ⚠️ Notas sobre os dados

- A base real vem em **uma aba por ano** (2022/2023/2024), com nomes de coluna e
  codificações **diferentes entre anos** — tudo padronizado em `src/limpeza.py`.
- O **dicionário de dados fornecido** descreve o formato antigo (2020/2021) e foi
  usado apenas como **referência conceitual** dos indicadores.
- Tratamentos aplicados: normalização de `Fase` (numérica/texto/`1A` → inteiro),
  correção de encoding (Gênero, pedras, Sim/Não), coerção de `INDE 2024`
  (texto com placeholder `INCLUIR`), unificação de gênero (Menino/Menina) e
  construção do alvo longitudinal.

---

## 👥 Entrega

Datathon PosTech — Fase 5. Ferramenta de **apoio à decisão pedagógica**; não
substitui a avaliação profissional das equipes da Passos Mágicos.
