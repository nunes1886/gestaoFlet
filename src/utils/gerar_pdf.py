from fpdf import FPDF
import os
from src.database.database import get_session, Empresa

def gerar_pdf_venda(os_obj):
    # Busca dados da empresa
    session = get_session()
    empresa = session.query(Empresa).first()
    nome_empresa = empresa.nome_fantasia if empresa else "Minha Gráfica"
    endereco_empresa = empresa.endereco if empresa else ""
    telefone_empresa = empresa.telefone if empresa else ""
    caminho_logo = empresa.caminho_logo if empresa and empresa.caminho_logo else ""
    session.close()

    pdf = FPDF()
    pdf.add_page()
    
    # --- LOGO E CABEÇALHO ---
    if caminho_logo and os.path.exists(caminho_logo):
        try:
            pdf.image(caminho_logo, x=10, y=8, w=30)
            pdf.set_xy(45, 10)
        except: pass
            
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Ordem de Servico #{os_obj.id}", ln=True, align="R")
    
    x_inicial = 45 if caminho_logo and os.path.exists(caminho_logo) else 10
    pdf.set_x(x_inicial)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, nome_empresa, ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.set_x(x_inicial)
    pdf.cell(0, 5, f"{endereco_empresa} | {telefone_empresa}", ln=True)
    pdf.ln(15)

    # --- DADOS DO CLIENTE ---
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Dados do Cliente", 1, 1, 'L', fill=True)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Cliente: {os_obj.cliente.nome_empresa}", 1, 1)
    if os_obj.motivo:
        pdf.cell(0, 8, f"Ref/Evento: {os_obj.motivo}", 1, 1)
        
    pdf.ln(5)

    # --- ITENS ---
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 8, "Produto", 1, 0, 'C', fill=True)
    pdf.cell(30, 8, "Medidas", 1, 0, 'C', fill=True)
    pdf.cell(20, 8, "Qtd", 1, 0, 'C', fill=True)
    pdf.cell(30, 8, "Unit", 1, 0, 'C', fill=True)
    pdf.cell(30, 8, "Total", 1, 1, 'C', fill=True)
    
    pdf.set_font("Arial", "", 10)
    for item in os_obj.itens:
        medidas = f"{item.largura}x{item.altura}" if item.largura > 0 else "-"
        pdf.cell(80, 8, item.descricao_item[:35], 1)
        pdf.cell(30, 8, medidas, 1, 0, 'C')
        pdf.cell(20, 8, str(item.quantidade), 1, 0, 'C')
        pdf.cell(30, 8, f"R$ {item.preco_unitario:.2f}", 1, 0, 'R')
        pdf.cell(30, 8, f"R$ {item.total_item:.2f}", 1, 1, 'R')
        
    pdf.ln(5)
    
    # --- TOTAIS ---
    pdf.set_font("Arial", "B", 12)
    pdf.cell(130, 10, "", 0)
    pdf.cell(30, 10, "Total:", 0)
    pdf.cell(30, 10, f"R$ {os_obj.valor_total:.2f}", 0, 1, 'R')
    
    if os_obj.valor_pago > 0:
        pdf.cell(130, 10, "", 0)
        pdf.cell(30, 10, "Pago:", 0)
        pdf.cell(30, 10, f"R$ {os_obj.valor_pago:.2f}", 0, 1, 'R')
        
        pdf.set_text_color(200, 0, 0)
        pdf.cell(130, 10, "", 0)
        pdf.cell(30, 10, "Restante:", 0)
        pdf.cell(30, 10, f"R$ {os_obj.valor_total - os_obj.valor_pago:.2f}", 0, 1, 'R')
        pdf.set_text_color(0, 0, 0)

    # --- SALVAR E ABRIR ---
    if not os.path.exists("os_pdfs"): os.makedirs("os_pdfs")
    caminho_arquivo = f"os_pdfs/OS_{os_obj.id}.pdf"
    pdf.output(caminho_arquivo)
    
    # Tenta abrir o arquivo automaticamente (Windows)
    try:
        os.startfile(os.path.abspath(caminho_arquivo))
    except Exception as e:
        print(f"Erro ao abrir PDF automaticamente: {e}")