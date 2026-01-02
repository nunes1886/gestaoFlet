from fpdf import FPDF
import os
from datetime import datetime
from src.database.database import get_session, Empresa

class PDFRelatorio(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Relatorio Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'C')

def gerar_pdf_relatorio_dia(data_str, vendas, total_recebido):
    session = get_session()
    empresa = session.query(Empresa).first()
    nome_empresa = empresa.nome_fantasia if empresa else "Minha Gráfica"
    session.close()

    pdf = PDFRelatorio()
    pdf.add_page()
    
    # --- CABEÇALHO ---
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"RELATÓRIO DE MOVIMENTAÇÃO", 0, 1, 'C')
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"{nome_empresa} - Data: {data_str}", 0, 1, 'C')
    pdf.ln(5)

    # --- RESUMO ---
    pdf.set_fill_color(200, 255, 200) # Verde claro
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 12, f"TOTAL ENTRADAS (CAIXA): R$ {total_recebido:.2f}", 1, 1, 'C', fill=True)
    pdf.ln(5)

    # --- TABELA ---
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(20, 8, "OS #", 1, 0, 'C', fill=True)
    pdf.cell(70, 8, "Cliente", 1, 0, 'L', fill=True)
    pdf.cell(60, 8, "Detalhes", 1, 0, 'L', fill=True)
    pdf.cell(40, 8, "Valor Pago", 1, 1, 'R', fill=True)

    pdf.set_font("Arial", "", 10)
    for v in vendas:
        # Pega o primeiro item como resumo
        detalhe = v.itens[0].descricao_item[:25] if v.itens else "Sem itens"
        if len(v.itens) > 1: detalhe += "..."
        
        pdf.cell(20, 8, str(v.id), 1, 0, 'C')
        pdf.cell(70, 8, v.cliente.nome_empresa[:30], 1, 0, 'L')
        pdf.cell(60, 8, detalhe, 1, 0, 'L')
        
        # Destaca valor pago
        pdf.cell(40, 8, f"R$ {v.valor_pago:.2f}", 1, 1, 'R')

    # --- SALVAR ---
    if not os.path.exists("relatorios"): os.makedirs("relatorios")
    nome_arq = f"relatorios/Fechamento_{data_str.replace('/','-')}.pdf"
    pdf.output(nome_arq)
    try: os.startfile(os.path.abspath(nome_arq))
    except: pass