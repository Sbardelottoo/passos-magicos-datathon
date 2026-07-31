"""Gera a apresentacao gerencial (storytelling) em PPTX a partir das figuras."""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

BASE = Path(__file__).resolve().parents[1]
FIG = BASE / "reports" / "figures"
OUT = BASE / "apresentacao" / "storytelling_passos_magicos.pptx"
OUT.parent.mkdir(exist_ok=True)

AZUL = RGBColor(0x1F, 0x3A, 0x5F)
ROXO = RGBColor(0x8E, 0x44, 0xAD)
CINZA = RGBColor(0x40, 0x40, 0x40)
BRANCO = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def cx_texto(slide, x, y, w, h, texto, tam=18, cor=CINZA, bold=False, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = texto
    r.font.size = Pt(tam); r.font.bold = bold; r.font.color.rgb = cor
    return tb


def bullets(slide, x, y, w, h, itens, tam=16):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, (txt, destaque) in enumerate(itens):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(8)
        r = p.add_run(); r.text = "• " + txt
        r.font.size = Pt(tam); r.font.color.rgb = ROXO if destaque else CINZA
        r.font.bold = destaque
    return tb


def faixa(slide, cor=AZUL, altura=1.1):
    from pptx.enum.shapes import MSO_SHAPE
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(altura))
    s.fill.solid(); s.fill.fore_color.rgb = cor; s.line.fill.background()
    return s


def slide_titulo_secao(titulo, subtitulo=""):
    s = prs.slides.add_slide(BLANK)
    faixa(s, AZUL, 7.5)
    cx_texto(s, 0.8, 2.6, 11.7, 1.5, titulo, 40, BRANCO, True)
    if subtitulo:
        cx_texto(s, 0.8, 4.0, 11.7, 1.0, subtitulo, 20, RGBColor(0xD0, 0xD8, 0xE8))
    return s


def slide_conteudo(titulo, itens, imagem=None, tam_bullet=16):
    s = prs.slides.add_slide(BLANK)
    faixa(s)
    cx_texto(s, 0.5, 0.22, 12.3, 0.8, titulo, 26, BRANCO, True)
    if imagem and (FIG / imagem).exists():
        bullets(s, 0.5, 1.4, 5.2, 5.6, itens, tam_bullet)
        s.shapes.add_picture(str(FIG / imagem), Inches(6.0), Inches(1.4), height=Inches(5.3))
    else:
        bullets(s, 0.7, 1.5, 12.0, 5.4, itens, tam_bullet)
    return s


# ---------- 1. Capa ----------
s = prs.slides.add_slide(BLANK)
faixa(s, AZUL, 7.5)
cx_texto(s, 0.8, 2.2, 11.7, 1.4, "Educação que transforma", 44, BRANCO, True)
cx_texto(s, 0.8, 3.5, 11.7, 1.2,
         "Análise de dados e modelo preditivo de risco de defasagem\nAssociação Passos Mágicos · PEDE 2022–2024",
         22, RGBColor(0xD0, 0xD8, 0xE8))
cx_texto(s, 0.8, 6.6, 11.7, 0.5, "Datathon PosTech — Fase 5", 16, RGBColor(0x9F, 0xB0, 0xC8))

# ---------- 2. Contexto ----------
slide_conteudo("O desafio", [
    ("A Passos Mágicos usa a educação para transformar a vida de crianças e jovens em vulnerabilidade social.", False),
    ("A PEDE mede o desenvolvimento por 7 indicadores: IAN, IDA, IEG, IAA, IPS, IPP e IPV, sintetizados no INDE.", False),
    ("Objetivo: contar a história dos dados de 2022 a 2024 e antecipar quem corre risco de defasagem.", True),
    ("Base analisada: 3.030 registros aluno-ano · 1.661 alunos únicos · chave RA liga a evolução no tempo.", False),
    ("Nota metodológica: usamos a base real (abas 2022/2023/2024). O dicionário fornecido descreve um formato antigo (2020/2021) e foi tratado como referência conceitual.", False),
])

# ---------- 3. Q1 defasagem ----------
slide_conteudo("Adequação ao nível (IAN): a defasagem está caindo", [
    ("Defasagem moderada/severa caiu de 22,2% (2022) para 8,0% (2024).", True),
    ("Alunos adequados ou adiantados subiram de 30,1% para 53,8%.", True),
    ("Ainda há 93 alunos (2024) em defasagem moderada/severa — foco de atenção.", False),
], "q1_defasagem_por_ano.png")

# ---------- 4. Q2 IDA + Q10 efetividade ----------
slide_conteudo("Desempenho e efetividade do programa", [
    ("IDA médio subiu de 6,09 (2022) para 6,35 (2024).", False),
    ("INDE médio: 7,04 → 7,34 → 7,40 — tendência de melhora.", True),
    ("Fases iniciais têm IDA mais alto; há queda nas fases de transição.", False),
    ("Coorte fixa (468 alunos nos 3 anos): melhora se mantém controlando entrada/saída — impacto real.", True),
], "q10_evolucao_indicadores.png")

# ---------- 4b. Q10 efetividade por PEDRA ----------
slide_conteudo("Impacto por pedra: os alunos sobem de nível (Q10)", [
    ("Pedras superiores (Ametista + Topázio) passaram de 55,6% (2022) para 68,0% (2024).", True),
    ("Na coorte fixa, 130 alunos SUBIRAM de pedra entre 2022 e 2024 (29% de ascensão).", True),
    ("A matriz de transição confirma mobilidade ascendente na classificação — evidência de impacto real.", False),
], "q10_transicao_pedras.png")

# ---------- 5. Q3/Q7/Q8 correlacoes ----------
slide_conteudo("O que move o desempenho, o ponto de virada e o INDE", [
    ("Engajamento (IEG) x Aprendizagem (IDA): r = 0,54; IEG x Ponto de Virada (IPV): r = 0,56.", False),
    ("Principais motores do IPV: IPP (0,61), IEG (0,56) e IDA (0,56).", True),
    ("Maiores alavancas do INDE: IDA (0,79), IEG (0,75) e IPV (0,72).", True),
    ("Mensagem: engajar o aluno puxa aprendizagem, ponto de virada e nota global juntos.", False),
], "q8_drivers_inde.png")

# ---------- 5b. Q8 combinacoes multivariadas ----------
slide_conteudo("Combinações que mais elevam o INDE (Q8)", [
    ("Regressão multivariada recupera os pesos efetivos da fórmula do INDE (R²=1,0): IDA e IEG têm o maior peso.", True),
    ("Efeito é CUMULATIVO: ter IDA+IEG+IPS+IPP acima da mediana eleva o INDE médio para 8,42 vs 6,04 quando nenhum está alto.", True),
    ("Recomendação: agir simultaneamente nesses eixos rende o maior ganho na nota global.", False),
], "q8_combinacoes_inde.png")

# ---------- 6. Q4/Q5/Q6 psicossocial ----------
slide_conteudo("Sinais de alerta: autoavaliação e psicossocial", [
    ("Autoavaliação (IAA) tem baixa correlação com o desempenho real (r≈0,12): 444 casos de alunos que se avaliam bem, mas têm IDA baixo.", False),
    ("Psicossocial (IPS) mais baixo ANTECEDE quedas: quem cai no ano seguinte tinha IPS 5,80 vs 6,39 dos demais.", True),
    ("IPP capta dimensão complementar ao IAN (r≈0,12): avaliação psicopedagógica não é redundante com a defasagem.", False),
], "q5_ips_antecede_queda.png")

# ---------- 7. Modelo — abordagem ----------
slide_titulo_secao("Modelo preditivo de risco",
                   "Antecipar a piora da defasagem para agir antes")
slide_conteudo("Como o modelo funciona", [
    ("Alvo preditivo: probabilidade de a defasagem PIORAR no ano seguinte (early-warning).", True),
    ("Usa os indicadores ATUAIS do aluno + idade, fase e tempo de casa.", False),
    ("Feature engineering longitudinal via RA · split estratificado 75/25 · imputação + padronização.", False),
    ("Comparados 3 algoritmos; vencedor: Random Forest.", False),
    ("Cuidado com vazamento: prever a defasagem atual seria trivial (ela deriva de idade/fase); por isso prevemos a MUDANÇA futura.", False),
])

# ---------- 8. Modelo — resultados ----------
slide_conteudo("Resultados do modelo", [
    ("AUC no teste = 0,88 — boa capacidade de separar quem vai piorar.", True),
    ("Recall da classe de risco = 73%: captura ~3 de cada 4 alunos que piorariam.", True),
    ("Principais preditores: defasagem atual, IAN, idade/fase e — entre os pedagógicos — IPV e IDA.", False),
    ("Entregue como aplicação Streamlit: risco individual com explicação e ações, turma priorizada e painel.", False),
], "modelo_roc.png")

# ---------- 8b. App como ferramenta ----------
slide_conteudo("Da predição à ação: a ferramenta para a equipe", [
    ("Predição individual: além da probabilidade, mostra POR QUE o risco é alto (fatores) e AÇÕES sugeridas.", True),
    ("Turma priorizada: basta enviar a planilha PEDE — a limpeza roda automaticamente e devolve a lista ordenada por risco.", True),
    ("Radar do aluno vs média da coorte para leitura rápida do perfil.", False),
    ("Objetivo de UX: transformar o modelo em uma lista de trabalho acionável, não uma caixa-preta.", False),
])

# ---------- 9. Importancias ----------
slide_conteudo("O que mais antecipa a piora", [
    ("Além da posição no ciclo (defasagem/idade/fase), o IPV (ponto de virada) é o indicador pedagógico mais preditivo.", True),
    ("Leitura de negócio: manter o aluno engajado rumo ao ponto de virada tem efeito protetor contra a defasagem.", False),
    ("Baixo IDA reforça o alerta — reforço de aprendizagem deve acompanhar o suporte socioemocional.", False),
], "modelo_importancias.png")

# ---------- 10. Recomendacoes ----------
slide_conteudo("Recomendações à Passos Mágicos", [
    ("1. Triagem anual com o modelo: priorizar acompanhamento dos alunos sinalizados em risco.", True),
    ("2. Monitorar IPS como termômetro precoce — quedas psicossociais antecedem quedas acadêmicas.", False),
    ("3. Investir em engajamento (IEG/IPV): é a alavanca de maior retorno sobre o INDE.", False),
    ("4. Atenção às fases de transição, onde o IDA cai.", False),
    ("5. Trabalhar a autopercepção dos alunos com IAA alto e IDA baixo.", False),
    ("6. Padronizar a coleta (fase, gênero, IPP) para fortalecer análises futuras.", False),
])

# ---------- 11. Encerramento ----------
s = slide_titulo_secao("Obrigado!",
                       "Aplicação, código e notebook disponíveis no repositório do projeto.")

prs.save(OUT)
print("Apresentacao salva em:", OUT, "| slides:", len(prs.slides._sldIdLst))
