# Respostas às 11 perguntas de negócio

Mapa direto: cada pergunta do enunciado → resposta resumida → onde ela está
comprovada (código/figura, aba do app publicado e slide da apresentação).

- **App:** https://paapps-magicos-datathon-mbjdeucxaqr7pkuodmftr6.streamlit.app/
- **Análise completa:** [`reports/insights.md`](reports/insights.md) (gerado por [`src/analise.py`](src/analise.py))
- **Base unificada:** 3.030 registros aluno-ano · 1.661 alunos · 2022–2024.

---

### 1. Adequação do nível (IAN) — perfil de defasagem e evolução
**Resposta:** a defasagem moderada/severa caiu de **22,2% (2022) para 8,0% (2024)**;
alunos adequados/adiantados subiram de 30,1% para 53,8%. Em 2024 restam 93 alunos
em defasagem moderada/severa (foco de atenção).
📊 `reports/figures/q1_defasagem_por_ano.png` · App: aba **Panorama** (KPI + gráfico) · Slide 2.

### 2. Desempenho acadêmico (IDA) — melhora, estagnação ou queda?
**Resposta:** **melhora** — IDA médio de 6,09 (2022) → 6,35 (2024). Fases iniciais
têm IDA mais alto; há queda nas fases de transição.
📊 `q2_ida_evolucao.png` · App: **Panorama** (evolução dos indicadores) · Slide 3.

### 3. Engajamento (IEG) × desempenho (IDA) e ponto de virada (IPV)
**Resposta:** relação direta e forte — **IEG↔IDA r=0,54** e **IEG↔IPV r=0,56**.
Engajamento é uma das maiores alavancas.
📊 `q3_ieg_ida_ipv.png` · App: **Panorama** (correlações) · Slide 5.

### 4. Autoavaliação (IAA) — coerente com desempenho e engajamento?
**Resposta:** baixa coerência — **IAA↔IDA r=0,12**; 444 registros com IAA≥8 e IDA≤5
(descompasso de autopercepção a monitorar).
📊 `q4_iaa_ida.png` · App: **Sobre o modelo**/**Panorama** · Slide 7.

### 5. Aspectos psicossociais (IPS) — antecedem quedas?
**Resposta:** sim — quem cai de desempenho no ano seguinte tinha **IPS 5,80 vs 6,39**
de quem não cai. IPS baixo é alerta precoce.
📊 `q5_ips_antecede_queda.png` · App: **Panorama** ("O que os dados mostram") · Slide 7.

### 6. Aspectos psicopedagógicos (IPP) — confirmam ou contradizem o IAN?
**Resposta:** relação fraca (**IPP↔IAN r=0,12**) — o IPP captura uma dimensão
**complementar** à defasagem, não redundante.
📊 `q6_ipp_ian.png` · Slide 7.

### 7. Ponto de virada (IPV) — o que mais influencia?
**Resposta:** os maiores motores são **IPP (0,61), IEG (0,56) e IDA (0,56)** —
engajamento e aprendizagem puxam o ponto de virada.
📊 `q7_drivers_ipv.png` · App: **Sobre o modelo** (importâncias) · Slide 5.

### 8. Multidimensionalidade — combinações que elevam o INDE
**Resposta:** a regressão recupera os pesos do INDE (R²=1,0): **IDA e IEG** têm o
maior peso. Efeito **cumulativo**: com IDA+IEG+IPS+IPP acima da mediana o INDE
médio salta para **8,42 vs 6,04** quando nenhum está alto.
📊 `q8_combinacoes_inde.png`, `q8_contribuicao_multivariada.png` · App: **Panorama** · Slide 6.

### 9. Previsão de risco com Machine Learning
**Resposta:** modelo **Random Forest** que estima a probabilidade de a defasagem
**piorar no ano seguinte** (alvo longitudinal via chave RA). **AUC 0,88 · recall 73%**
no limiar 0,56. Etapas no notebook: feature engineering → split → modelagem → avaliação.
📓 [`notebooks/modelo_preditivo_risco.ipynb`](notebooks/modelo_preditivo_risco.ipynb) ·
🤖 [`src/modelo.py`](src/modelo.py) · App: **Simulador**, **Turma priorizada**,
**Sobre o modelo** · Slides 8–10, 12.

### 10. Efetividade do programa (Quartzo, Ágata, Ametista, Topázio)
**Resposta:** sim, há melhora consistente — pedras superiores (Ametista+Topázio)
passaram de **55,6% para 68,0%**; na coorte fixa (468 alunos nos 3 anos), **130
subiram de pedra (29% de ascensão)**, controlando entrada/saída → impacto real.
📊 `q10_pedras_por_ano.png`, `q10_transicao_pedras.png` · App: **Panorama** · Slides 3–4.

### 11. Insights e criatividade
**Resposta:** entre os insights adicionais — desempenho equilibrado por gênero;
quem atinge o Ponto de Virada tem todos os indicadores mais altos; tempo de casa
isolado não explica o desempenho. Além disso, a própria **plataforma** (explicação
por aluno, recomendações de ação, turma priorizada com limiar ajustável, relatório
em PDF) é a entrega criativa que transforma a análise em ação.
📊 `reports/insights.md` (seção Q11) · App: todas as abas · Slides 11, 13.

---

_Gerado para facilitar a avaliação. Números conferem com `reports/insights.md`._
