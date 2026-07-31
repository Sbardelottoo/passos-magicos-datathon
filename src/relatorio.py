"""
Geracao de relatorio em PDF por aluno (predicao + explicacao + recomendacoes).

Usa fpdf2 (puro Python, sem dependencias de sistema) para funcionar tanto local
quanto no Streamlit Community Cloud sem binarios extras.
"""
from pathlib import Path
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos

AZUL = (10, 95, 168)
CINZA_ESCURO = (26, 43, 60)
VERMELHO = (192, 57, 43)
VERDE = (76, 154, 42)


class RelatorioAluno(FPDF):
    def __init__(self, logo_path=None):
        super().__init__(format="A4")
        self.logo_path = logo_path
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        if self.logo_path and Path(self.logo_path).exists():
            self.image(str(self.logo_path), x=10, y=8, h=14)
            self.set_xy(28, 10)
        else:
            self.set_xy(10, 10)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*AZUL)
        self.cell(0, 8, "Preditor de Risco de Defasagem", ln=1)
        self.set_x(28 if self.logo_path else 10)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*CINZA_ESCURO)
        self.cell(0, 5, "Associacao Passos Magicos - Datathon PosTech Fase 5", ln=1)
        self.ln(4)
        self.set_draw_color(*AZUL)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Gerado em {datetime.now():%d/%m/%Y %H:%M} - "
                         "Ferramenta de apoio a decisao pedagogica", align="C")


def _sanitiza(txt):
    """fpdf2 core fonts (Helvetica) sao latin-1; troca acentos problematicos."""
    if txt is None:
        return ""
    return (str(txt).encode("latin-1", errors="replace").decode("latin-1"))


def gerar_pdf_aluno(identificacao: dict, indicadores: dict, prob: float, limiar: float,
                    fatores: list, recomendacoes: list, logo_path=None) -> bytes:
    """Monta o PDF e retorna os bytes prontos para download.

    identificacao: dict com campos livres (ex.: RA, ano, fase, pedra)
    indicadores: dict {nome_indicador: valor}
    prob: probabilidade de risco (0-1)
    fatores: lista de (rotulo, contribuicao_pontos_percentuais)
    recomendacoes: lista de (rotulo, acao)
    """
    pdf = RelatorioAluno(logo_path=logo_path)
    pdf.add_page()

    # --- Identificacao ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*CINZA_ESCURO)
    pdf.cell(0, 7, _sanitiza("Identificacao do aluno"), ln=1)
    pdf.set_font("Helvetica", "", 10)
    for k, v in identificacao.items():
        pdf.cell(0, 6, _sanitiza(f"{k}: {v}"), ln=1)
    pdf.ln(3)

    # --- Resultado da predicao ---
    em_risco = prob >= limiar
    cor = VERMELHO if em_risco else VERDE
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*cor)
    status = "EM RISCO" if em_risco else "SEM RISCO IMEDIATO"
    pdf.cell(0, 8, _sanitiza(f"Probabilidade de piora no proximo ano: {prob*100:.1f}%  ({status})"), ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*CINZA_ESCURO)
    pdf.cell(0, 5, _sanitiza(f"Limiar de alerta do modelo: {limiar*100:.0f}%"), ln=1)
    pdf.ln(3)

    # --- Indicadores ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, _sanitiza("Indicadores"), ln=1)
    pdf.set_font("Helvetica", "", 10)
    col_w = 63
    i = 0
    for k, v in indicadores.items():
        if i % 3 == 0:
            pdf.ln(0)
        pdf.cell(col_w, 6, _sanitiza(f"{k}: {v}"), ln=(i % 3 == 2))
        i += 1
    if i % 3 != 0:
        pdf.ln(6)
    pdf.ln(3)

    # --- Fatores de risco ---
    if fatores:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _sanitiza("Fatores que mais elevam o risco"), ln=1)
        pdf.set_font("Helvetica", "", 10)
        for rot, pontos in fatores:
            pdf.cell(0, 6, _sanitiza(f"- {rot}: +{pontos:.1f} p.p."), ln=1)
        pdf.ln(3)

    # --- Recomendacoes ---
    if recomendacoes:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _sanitiza("Acoes sugeridas"), ln=1)
        pdf.set_font("Helvetica", "", 10)
        for rot, acao in recomendacoes:
            pdf.multi_cell(0, 6, _sanitiza(f"- {rot}: {acao}"),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, _sanitiza(
        "Este relatorio e gerado por um modelo estatistico de apoio a decisao. "
        "Nao substitui a avaliacao profissional das equipes pedagogica, psicologica e psicopedagogica."),
        new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return bytes(pdf.output())
