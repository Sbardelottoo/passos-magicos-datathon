# Roteiro do vídeo (até 5 minutos)

Objetivo: apresentar o storytelling da análise e os resultados do modelo
preditivo. Pelo menos uma pessoa do grupo deve aparecer. Sugestão: compartilhar a
tela alternando entre a **apresentação (PPTX)** e a **aplicação Streamlit**.

| Tempo | Bloco | O que dizer / mostrar |
|---|---|---|
| **0:00–0:30** | **Abertura** | Apresente-se. "Somos o grupo X, do Datathon Fase 5. Analisamos os dados da Associação Passos Mágicos — que usa a educação para transformar a vida de crianças e jovens — para responder às perguntas de negócio e prever risco de defasagem." (Slide 1) |
| **0:30–1:10** | **Contexto e dados** | Base PEDE 2022–2024: 3.030 registros, 1.661 alunos, ligados pela chave RA. Indicadores IAN, IDA, IEG, IAA, IPS, IPP, IPV e o INDE. Cite a nota metodológica: usamos a base real; o dicionário descrevia formato antigo. (Slide 2) |
| **1:10–2:00** | **A defasagem está caindo** | Slide da Q1: defasagem moderada/severa caiu de 22% (2022) para 8% (2024); adequados/adiantados subiram de 30% para 54%. Some ao slide de efetividade (Q10): INDE 7,04 → 7,40 e a coorte fixa de 468 alunos confirma melhora real. **Mensagem: o programa funciona.** |
| **2:00–2:45** | **O que move os resultados** | Correlações: engajamento (IEG) puxa aprendizagem (IDA) e ponto de virada (IPV); IDA+IEG+IPV são as maiores alavancas do INDE. Sinais de alerta: IPS baixo antecede quedas; autoavaliação (IAA) descolada do desempenho real em 444 casos. |
| **2:45–3:45** | **O modelo preditivo** | Explique o alvo: "probabilidade de a defasagem **piorar no ano seguinte**". Por que prever a mudança e não o nível (evitar vazamento). Resultados: **AUC 0,88** e **recall 73%** (captura 3 em cada 4 alunos que piorariam). Preditor pedagógico mais forte: IPV. |
| **3:45–4:40** | **Demonstração do app** | Mostre a aplicação Streamlit ao vivo: (1) aba de **predição individual** — ajuste os sliders e mostre a probabilidade e o alerta; (2) aba de **predição em lote** — subir um CSV de turma e baixar os alunos priorizados; (3) aba de **panorama**. |
| **4:40–5:00** | **Recomendações e fecho** | Triagem anual com o modelo, monitorar IPS como termômetro precoce, investir em engajamento, atenção às fases de transição. Agradeça e cite que código, notebook e app estão no GitHub. (Slide final) |

## Checklist de gravação
- [ ] Rosto de ao menos 1 integrante aparece.
- [ ] Duração ≤ 5:00.
- [ ] Áudio limpo; tela legível (fonte grande).
- [ ] App aberto e testado antes de gravar (evitar "cold start").
- [ ] Link do vídeo (YouTube não listado / Drive) adicionado ao README.
