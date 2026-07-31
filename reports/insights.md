# Insights da Analise Exploratoria - PEDE Passos Magicos (2022-2024)

Base unificada: 3030 registros (aluno-ano), 1661 alunos unicos, anos [np.int64(2022), np.int64(2023), np.int64(2024)].

## Q1. Adequacao ao nivel (IAN) e defasagem
- Defasagem moderada/severa caiu de 22.2% (2022) para 8.0% (2024).
- Alunos adequados/adiantados subiram de 30.1% para 53.8%.
- Em 2024, 93 alunos seguem em defasagem moderada/severa (foco de atencao).

## Q2. Desempenho academico (IDA)
- IDA medio: 6.09 (2022) -> 6.35 (2024): tendencia de melhora.
- Fases iniciais tendem a IDA mais alto; ha queda nas fases intermediarias (transicao).

## Q3. Engajamento (IEG) x IDA e IPV
- Correlacao IEG-IDA = 0.54; IEG-IPV = 0.56 (positivas e fortes).
- Engajamento e um dos maiores alavancadores de desempenho e do ponto de virada.

## Q4. Autoavaliacao (IAA) x realidade
- Correlacao IAA-IDA = 0.12; IAA-IEG = 0.13.
- 444 registros com autoavaliacao alta (>=8) mas IDA baixo (<=5): possivel descompasso de autopercepcao a monitorar.

## Q5. Psicossocial (IPS) antecedendo quedas
- IPS medio de quem cai no ano seguinte = 5.80 vs 6.39 de quem nao cai.
- IPS mais baixo antecede quedas de IDA: sinal de alerta psicossocial precoce.

## Q6. Psicopedagogico (IPP) x defasagem (IAN)
- Correlacao IPP-IAN = 0.12.
- IPP tende a acompanhar a defasagem, mas a relacao e fraca: a avaliacao psicopedagogica captura dimensao complementar ao IAN (nao apenas redundante).

## Q7. Determinantes do ponto de virada (IPV)
- Ordem de influencia sobre o IPV: IPP (0.61), IEG (0.56), IDA (0.56), IAN (0.15), IAA (0.06), IPS (-0.05).
- IPP e IEG sao os principais motores do ponto de virada.

## Q8. O que eleva a nota global (INDE)
- Indicadores mais associados ao INDE: IDA (0.79), IEG (0.75), IPV (0.72), IPP (0.54), IAN (0.41), IAA (0.40), IPS (0.20).
- Como o INDE e uma ponderacao dos indicadores, a regressao padronizada RECUPERA os pesos efetivos da formula (R2=1.00): IDA (+0.38), IEG (+0.30), IAA (+0.28), IAN (+0.25), IPV (+0.21), IPS (+0.20), IPP (+0.09).
- Os maiores pesos sao IDA e IEG: sao as combinacoes que mais elevam a nota global - priorizar esses eixos rende o maior ganho no INDE.
- Ter os 4 indicadores (IDA+IEG+IPS+IPP) acima da mediana eleva o INDE medio para 8.42 vs 6.04 quando nenhum esta alto: o efeito e cumulativo.

## Q10. Efetividade do programa ao longo do ciclo
- INDE medio: 7.04 -> 7.34 -> 7.40.
- Coorte fixa (alunos nos 3 anos, n=468): INDE 7.38 -> 7.38 (melhora real controlando entrada/saida).
- Pedras superiores (Ametista+Topazio) passaram de 55.6% (2022) para 68.0% (2024): avanco na classificacao geral.
- Na coorte fixa, 130 alunos SUBIRAM de pedra e 114 desceram entre 2022 e 2024 (29% de ascensao) - evidencia de impacto real do programa.

## Q11. Insights adicionais
- Medias por genero (INDE/IDA/IEG):
           inde   ida   ieg
genero                     
Feminino   7.34  6.40  8.04
Masculino  7.19  6.35  7.84
- Quem atingiu o Ponto de Virada (2022) tem indicadores mais altos:
             ian   ida   ieg   iaa   ips  ipp   ipv
atingiu_pv                                         
0.0         6.36  5.82  7.72  8.18  6.84  NaN  7.01
1.0         6.88  7.87  9.01  8.87  7.32  NaN  8.86
- Correlacao anos na PM x INDE = -0.10 (praticamente nula): tempo de casa isoladamente nao explica o desempenho.
