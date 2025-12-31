from fpdf import FPDF
from datetime import datetime
import os

class PDF_OS(FPDF):
    def header(self):
        # Cabeçalho Simples
        self.set_font('Helvetica', 'B', 15)
        self.cell(0, 8, 'GestãoPro - Comunicação Visual', ln=True, align='C')
        self.set_font('Helvetica', '', 9)
        self.cell(0, 5, 'Rua da Gráfica, 123 - Centro | (79) 99999-9999', ln=True, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def gerar_conteudo_pagina(pdf, os_obj, modo_producao=False):
    # --- FAIXA TÍTULO ---
    titulo = "ORDEM DE SERVIÇO (PRODUÇÃO)" if modo_producao else f"ORDEM DE SERVIÇO {os_obj.id:06d}"
    
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, titulo, ln=True, align='L', fill=True)
    pdf.ln(3)
    
    # --- DADOS DO CLIENTE ---
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(25, 5, "Cliente:", align='L')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(100, 5, os_obj.cliente.nome_empresa[:45], align='L')
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(15, 5, "Data:", align='L')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, os_obj.data_criacao.strftime("%d/%m/%Y %H:%M"), ln=True, align='L')
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(25, 5, "Telefone:", align='L')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, os_obj.cliente.telefone or "-", ln=True, align='L')
    pdf.ln(3)

    # --- TABELA DE ITENS ---
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Helvetica', 'B', 9)
    
    # Define larguras baseadas no modo (se tem preço ou não)
    if modo_producao:
        # Sem colunas de preço -> Aumenta descrição e medidas
        w_desc = 100
        w_med = 30
        w_qtd = 30
        w_unit = 0 # Oculto
        w_total = 0 # Oculto
    else:
        w_desc = 70
        w_med = 25
        w_qtd = 15
        w_unit = 35
        w_total = 35

    pdf.cell(w_desc, 6, "Descrição", border=1, fill=True)
    pdf.cell(w_med, 6, "Medidas", border=1, align='C', fill=True)
    pdf.cell(w_med, 6, "Qtd", border=1, align='C', fill=True) # Usando w_med para produção ficar grande
    
    if not modo_producao:
        pdf.cell(w_unit, 6, "Unit (R$)", border=1, align='C', fill=True)
        pdf.cell(w_total, 6, "Total (R$)", border=1, align='C', fill=True)
    
    pdf.ln()

    # --- ITENS LOOP ---
    pdf.set_font('Helvetica', '', 10) # Fonte maior na produção
    
    for item in os_obj.itens:
        # Altura da linha dinâmica
        h_line = 8 
        
        pdf.cell(w_desc, h_line, item.descricao_item[:40], border=1)
        pdf.cell(w_med, h_line, f"{item.largura:.2f}x{item.altura:.2f}", border=1, align='C')
        pdf.cell(w_med, h_line, str(item.quantidade), border=1, align='C') # Reusa largura
        
        if not modo_producao:
            pdf.cell(w_unit, h_line, f"{item.preco_unitario:.2f}", border=1, align='R')
            pdf.cell(w_total, h_line, f"{item.total_item:.2f}", border=1, align='R')
        
        pdf.ln()

    pdf.ln(5)

    # --- FINANCEIRO (SÓ APARECE NA VIA ADMINISTRATIVA) ---
    if not modo_producao:
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(145, 6, "TOTAL GERAL:", border=0, align='R')
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(45, 6, f"R$ {os_obj.valor_total:.2f}", border=1, align='R', ln=True)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(145, 6, "Sinal Pago:", border=0, align='R')
        pdf.cell(45, 6, f"R$ {os_obj.valor_pago:.2f}", border=1, align='R', ln=True)
        
        falta = os_obj.valor_total - os_obj.valor_pago
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(145, 6, "RESTANTE:", border=0, align='R')
        pdf.cell(45, 6, f"R$ {falta:.2f}", border=1, align='R', ln=True)
        pdf.ln(5)

    # --- OBSERVAÇÕES E ARTE ---
    if os_obj.observacoes:
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, "OBSERVAÇÕES / ACABAMENTO:", ln=True, fill=True)
        pdf.set_font('Helvetica', '', 11) # Fonte maior para produção ler bem
        pdf.multi_cell(0, 6, os_obj.observacoes, border=1)
        pdf.ln(5)

    # --- IMAGEM ---
    if os_obj.imagem_os and os.path.exists(os_obj.imagem_os):
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(0, 6, "LAYOUT / ARTE:", ln=True)
        try:
            # Centraliza a imagem e define tamanho máximo
            # Largura máx 120mm
            pdf.image(os_obj.imagem_os, x=45, w=120) 
        except:
            pdf.cell(0, 10, "[Erro ao carregar imagem]", ln=True)
            
    pdf.ln(10)
    
    # --- ASSINATURA ---
    if not modo_producao:
        pdf.line(20, pdf.get_y(), 100, pdf.get_y())
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(0, 4, "Assinatura do Cliente / Responsável", ln=True)


def gerar_pdf_venda(os_obj):
    pdf = PDF_OS()
    
    # PÁGINA 1: VIA ADMINISTRATIVA (COM VALORES)
    pdf.add_page()
    gerar_conteudo_pagina(pdf, os_obj, modo_producao=False)
    
    # PÁGINA 2: VIA PRODUÇÃO (SEM VALORES)
    pdf.add_page()
    gerar_conteudo_pagina(pdf, os_obj, modo_producao=True)

    # Salva e Abre
    nome_arq = f"OS_{os_obj.id}.pdf"
    pdf.output(nome_arq)
    try:
        os.startfile(nome_arq)
    except:
        pass # Linux/Mac usam comandos diferentes, mas focaremos no Windows