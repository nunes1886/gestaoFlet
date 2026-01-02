from fpdf import FPDF
import os
from datetime import datetime
from src.database.database import get_session, Empresa

class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'GestãoPro - {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'C')

def gerar_pdf_venda(os_obj):
    # --- DADOS DA EMPRESA ---
    session = get_session()
    empresa = session.query(Empresa).first()
    dados_empresa = {
        "nome": empresa.nome_fantasia if empresa else "Minha Gráfica",
        "cnpj": empresa.cnpj if empresa else "",
        "tel": empresa.telefone if empresa else "",
        "end": empresa.endereco if empresa else ""
    }
    session.close()

    # Cria o objeto PDF UMA VEZ SÓ
    pdf = PDF()

    # --- FUNÇÃO PARA DESENHAR O CONTEÚDO DA PÁGINA ---
    def desenhar_pagina(tipo="CLIENTE"):
        pdf.add_page()
        
        # 1. CABEÇALHO (Baseado na sua imagem)
        # Logo à Esquerda (Menor e centralizada)
        if os.path.exists("assets/logo.png"):
            try:
                # x=10, y=10, w=22 (Diminuí para não brigar com o texto)
                pdf.image("assets/logo.png", 10, 10, 22) 
            except: pass

        # Texto da Empresa à Direita (Alinhamento 'R')
        pdf.set_xy(40, 10) 
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, dados_empresa["nome"], 0, 1, 'R') # Alinhado à Direita
        
        pdf.set_font("Arial", "", 9)
        pdf.cell(0, 5, f"CNPJ: {dados_empresa['cnpj']}", 0, 1, 'R')
        pdf.cell(0, 5, dados_empresa["end"], 0, 1, 'R')
        pdf.cell(0, 5, f"Tel: {dados_empresa['tel']}", 0, 1, 'R')

        # 2. TÍTULO
        pdf.ln(10)
        cor_fundo = (255, 200, 200) if os_obj.is_urgente else (240, 240, 240)
        pdf.set_fill_color(*cor_fundo)
        
        titulo = f"RECIBO #{os_obj.id} ({tipo})"
        if os_obj.is_urgente: titulo += " - URGENTE !!!"
        
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, titulo, 0, 1, 'C', fill=True) # Reduzi altura de 12 para 10
        pdf.ln(5)

        # 3. DADOS DO CLIENTE
        pdf.set_font("Arial", "B", 10)
        pdf.cell(100, 5, f"Cliente: {os_obj.cliente.nome_empresa}", 0, 0)
        pdf.cell(0, 5, f"Previsão: {os_obj.data_entrega}", 0, 1, 'R')
        
        pdf.set_font("Arial", "", 10)
        pdf.cell(100, 5, f"Tel: {os_obj.cliente.telefone}", 0, 0)
        pdf.cell(0, 5, f"Entrada: {os_obj.data_criacao.strftime('%d/%m/%Y')}", 0, 1, 'R')

        if os_obj.motivo:
            pdf.ln(2)
            pdf.set_font("Arial", "I", 9)
            pdf.multi_cell(0, 5, f"Ref: {os_obj.motivo}")

        pdf.ln(3) # Reduzi espaço

        # 4. TABELA DE ITENS
        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(220, 220, 220)
        
        if tipo == "CLIENTE":
            pdf.cell(15, 6, "Qtd", 1, 0, 'C', fill=True)
            pdf.cell(95, 6, "Produto", 1, 0, 'L', fill=True)
            pdf.cell(30, 6, "Medidas", 1, 0, 'C', fill=True)
            pdf.cell(25, 6, "Unit", 1, 0, 'R', fill=True)
            pdf.cell(25, 6, "Total", 1, 1, 'R', fill=True)
        else: # PRODUÇÃO
            pdf.cell(15, 6, "Qtd", 1, 0, 'C', fill=True)
            pdf.cell(115, 6, "Produto / Detalhes", 1, 0, 'L', fill=True)
            pdf.cell(40, 6, "Medidas", 1, 0, 'C', fill=True)
            pdf.cell(20, 6, "OK", 1, 1, 'C', fill=True)

        pdf.set_font("Arial", "", 9)
        for item in os_obj.itens:
            medidas = f"{item.largura}x{item.altura}"
            if tipo == "CLIENTE":
                pdf.cell(15, 6, str(item.quantidade), 1, 0, 'C')
                pdf.cell(95, 6, item.descricao_item[:50], 1, 0, 'L')
                pdf.cell(30, 6, medidas, 1, 0, 'C')
                pdf.cell(25, 6, f"{item.preco_unitario:.2f}", 1, 0, 'R')
                pdf.cell(25, 6, f"{item.total_item:.2f}", 1, 1, 'R')
            else:
                pdf.cell(15, 8, str(item.quantidade), 1, 0, 'C') # Altura maior na produção pra ler melhor
                pdf.cell(115, 8, item.descricao_item[:65], 1, 0, 'L')
                pdf.cell(40, 8, medidas, 1, 0, 'C')
                pdf.cell(20, 8, "[ ]", 1, 1, 'C')

        pdf.ln(3)

        # 5. OBSERVAÇÕES E IMAGEM
        if os_obj.observacoes:
            pdf.set_font("Arial", "B", 8)
            pdf.cell(0, 4, "Observações:", 0, 1)
            pdf.set_font("Arial", "", 8)
            pdf.multi_cell(0, 4, os_obj.observacoes, border=1)
            pdf.ln(2)

        # Imagem (Centralizada)
        if os_obj.imagem_os and os.path.exists(os_obj.imagem_os):
            try:
                # Verifica espaço restante
                espaco_restante = 270 - pdf.get_y()
                if espaco_restante > 60: # Só desenha se tiver espaço
                    # Centraliza imagem: (LarguraPagina - LarguraImg) / 2 = (210 - 70) / 2 = 70
                    pdf.image(os_obj.imagem_os, x=70, w=70)
                    pdf.ln(2)
            except: pass

        # 6. TOTAIS (Só Cliente)
        if tipo == "CLIENTE":
            # Se estiver muito embaixo, força nova página
            if pdf.get_y() > 250: pdf.add_page()
            
            pdf.set_x(130)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(30, 6, "Total:", 0, 0, 'R')
            pdf.cell(30, 6, f"R$ {os_obj.valor_total:.2f}", 0, 1, 'R')
            
            restante = os_obj.valor_total - os_obj.valor_pago
            if restante > 0:
                pdf.set_x(130)
                pdf.set_text_color(200, 0, 0)
                pdf.cell(30, 6, "Falta:", 0, 0, 'R')
                pdf.cell(30, 6, f"R$ {restante:.2f}", 0, 1, 'R')
                pdf.set_text_color(0, 0, 0)
            else:
                pdf.set_x(130)
                pdf.set_text_color(0, 150, 0)
                pdf.cell(60, 6, "PAGO TOTALMENTE", 0, 1, 'R')
                pdf.set_text_color(0, 0, 0)

        # 7. ASSINATURA COMPACTA
        # Verifica se cabe na página, senão adiciona
        if pdf.get_y() > 260: pdf.add_page()
        
        # Posiciona no final da página, mas com margem
        posicao_assinatura = 270
        # Se o conteúdo atual for maior que a posição fixa, usa o dinâmico + margem
        if pdf.get_y() + 15 > posicao_assinatura:
             posicao_assinatura = pdf.get_y() + 10

        pdf.set_y(posicao_assinatura)
        
        pdf.line(60, pdf.get_y(), 150, pdf.get_y()) # Linha centralizada
        pdf.set_font("Arial", "", 8)
        pdf.cell(0, 4, "Assinatura / Responsável", 0, 1, 'C')

    # --- GERA AS DUAS PÁGINAS NO MESMO ARQUIVO ---
    desenhar_pagina("CLIENTE")   # Página 1
    desenhar_pagina("PRODUCAO")  # Página 2 (Sem valores)

    # --- SALVAR ---
    if not os.path.exists("os_pdfs"): os.makedirs("os_pdfs")
    caminho_arquivo = f"os_pdfs/OS_{os_obj.id}_Completa.pdf"
    pdf.output(caminho_arquivo)
    
    try: os.startfile(os.path.abspath(caminho_arquivo))
    except: pass