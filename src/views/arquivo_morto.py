import flet as ft
from src.database.database import get_session, OrdemServico, Empresa
from sqlalchemy.orm import joinedload
from datetime import datetime
from fpdf import FPDF
import os

# --- CLASSE PDF PADRÃO ---
class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'GestãoPro - {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 0, 'C')

def ViewArquivoMorto(page):
    
    # --- VARIÁVEIS DE ESTADO ---
    id_editando = ft.Ref[int]()

    # --- CAMPOS DE EDIÇÃO (Dialog) ---
    txt_edit_cliente = ft.TextField(label="Cliente", read_only=True, bgcolor=ft.colors.GREY_100)
    txt_edit_total = ft.TextField(label="Valor Total (R$)", keyboard_type=ft.KeyboardType.NUMBER)
    txt_edit_pago = ft.TextField(label="Valor Já Pago (R$)", keyboard_type=ft.KeyboardType.NUMBER)
    
    dd_edit_status = ft.Dropdown(
        label="Status Atual",
        options=[
            ft.dropdown.Option("Aguardando Pagamento"),
            ft.dropdown.Option("Fila"),
            ft.dropdown.Option("Impressão"),
            ft.dropdown.Option("Acabamento"),
            ft.dropdown.Option("Entregue"),
            ft.dropdown.Option("Cancelado"),
        ]
    )

    # --- FUNÇÃO: IMPRIMIR O.S. (MODELO COMPLETO) ---
    def imprimir_os_individual(os_obj):
        try:
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

            # --- FUNÇÃO INTERNA PARA DESENHAR PÁGINA ---
            def desenhar_pagina(tipo="CLIENTE"):
                pdf.add_page()
                
                # 1. CABEÇALHO
                # Logo
                if os.path.exists("assets/logo.png"):
                    try:
                        pdf.image("assets/logo.png", 10, 10, 22) 
                    except: pass

                # Dados Empresa
                pdf.set_xy(40, 10) 
                pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 8, dados_empresa["nome"], 0, 1, 'R')
                
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
                pdf.cell(0, 10, titulo, 0, 1, 'C', fill=True)
                pdf.ln(5)

                # 3. DADOS DO CLIENTE
                pdf.set_font("Arial", "B", 10)
                pdf.cell(100, 5, f"Cliente: {os_obj.cliente.nome_empresa}", 0, 0)
                
                # Tratamento seguro para data de entrega (caso não exista no banco)
                data_entrega = getattr(os_obj, 'data_entrega', 'A Combinar')
                pdf.cell(0, 5, f"Previsão: {data_entrega}", 0, 1, 'R')
                
                pdf.set_font("Arial", "", 10)
                pdf.cell(100, 5, f"Tel: {os_obj.cliente.telefone}", 0, 0)
                pdf.cell(0, 5, f"Entrada: {os_obj.data_criacao.strftime('%d/%m/%Y')}", 0, 1, 'R')

                if os_obj.motivo:
                    pdf.ln(2)
                    pdf.set_font("Arial", "I", 9)
                    pdf.multi_cell(0, 5, f"Ref: {os_obj.motivo}")

                pdf.ln(3)

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
                        pdf.cell(15, 8, str(item.quantidade), 1, 0, 'C')
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
                        espaco_restante = 270 - pdf.get_y()
                        if espaco_restante > 60:
                            pdf.image(os_obj.imagem_os, x=70, w=70)
                            pdf.ln(2)
                    except: pass

                # 6. TOTAIS (Só Cliente)
                if tipo == "CLIENTE":
                    if pdf.get_y() > 250: pdf.add_page()
                    
                    pdf.set_x(130)
                    pdf.set_font("Arial", "B", 10)
                    pdf.cell(30, 6, "Total:", 0, 0, 'R')
                    pdf.cell(30, 6, f"R$ {os_obj.valor_total:.2f}", 0, 1, 'R')
                    
                    restante = os_obj.valor_total - os_obj.valor_pago
                    if restante > 0.01:
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

                # 7. ASSINATURA
                if pdf.get_y() > 260: pdf.add_page()
                
                posicao_assinatura = 270
                if pdf.get_y() + 15 > posicao_assinatura:
                     posicao_assinatura = pdf.get_y() + 10

                pdf.set_y(posicao_assinatura)
                pdf.line(60, pdf.get_y(), 150, pdf.get_y())
                pdf.set_font("Arial", "", 8)
                pdf.cell(0, 4, "Assinatura / Responsável", 0, 1, 'C')

            # --- GERAÇÃO DAS DUAS VIAS ---
            desenhar_pagina("CLIENTE")
            desenhar_pagina("PRODUCAO")

            # --- SALVAR E ABRIR ---
            if not os.path.exists("os_pdfs"): os.makedirs("os_pdfs")
            caminho_arquivo = f"os_pdfs/OS_{os_obj.id}_Completa.pdf"
            pdf.output(caminho_arquivo)
            
            try: os.startfile(os.path.abspath(caminho_arquivo))
            except: pass
            
            page.snack_bar = ft.SnackBar(ft.Text(f"PDF Gerado: {caminho_arquivo}"), bgcolor=ft.colors.GREEN)
            page.snack_bar.open = True
            page.update()

        except Exception as e:
            print(f"Erro PDF: {e}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao imprimir: {e}"), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()

    # --- FUNÇÃO: SALVAR CORREÇÃO ---
    def salvar_correcao(e):
        try:
            v_total = float(txt_edit_total.value.replace(",", ".")) if txt_edit_total.value else 0.0
            v_pago = float(txt_edit_pago.value.replace(",", ".")) if txt_edit_pago.value else 0.0
            
            session = get_session()
            os_atual = session.query(OrdemServico).get(id_editando.current)
            
            if os_atual:
                os_atual.valor_total = v_total
                os_atual.valor_pago = v_pago
                os_atual.status = dd_edit_status.value
                session.commit()
                
                page.snack_bar = ft.SnackBar(ft.Text(f"OS #{os_atual.id} corrigida com sucesso!"), bgcolor=ft.colors.GREEN)
                page.snack_bar.open = True
                page.update()
            
            session.close()
            
            if page.dialog:
                page.dialog.open = False
                page.update()
            
            carregar_dados()

        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Erro: Verifique os valores numéricos."), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
        except Exception as err:
            print(err)

    # --- MODAL DE EDIÇÃO ---
    dlg_editar = ft.AlertDialog(
        title=ft.Text("Corrigir O.S. (Administrativo)"),
        content=ft.Column([
            ft.Text("Use com cuidado. Isso altera o financeiro.", color=ft.colors.RED, size=12),
            txt_edit_cliente,
            txt_edit_total,
            txt_edit_pago,
            dd_edit_status
        ], height=300, tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: fechar_dialog(e)),
            ft.ElevatedButton("Salvar Correção", bgcolor=ft.colors.BLUE_800, color="white", on_click=salvar_correcao)
        ]
    )

    def abrir_edicao(os_obj):
        id_editando.current = os_obj.id
        txt_edit_cliente.value = os_obj.cliente.nome_empresa if os_obj.cliente else "Consumidor"
        valor_total = os_obj.valor_total or 0.0
        valor_pago = os_obj.valor_pago or 0.0
        
        txt_edit_total.value = f"{valor_total:.2f}" # Mostra apenas 2 casas
        txt_edit_pago.value = f"{valor_pago:.2f}"   # Mostra apenas 2 casas
        dd_edit_status.value = os_obj.status
        
        page.dialog = dlg_editar
        dlg_editar.open = True
        page.update()

    def fechar_dialog(e):
        if page.dialog:
            page.dialog.open = False
            page.update()

    # --- TABELA E BUSCA ---
    txt_busca = ft.TextField(
        label="Buscar por Cliente ou ID...",
        prefix_icon=ft.Icons.SEARCH,
        width=400,
        bgcolor="white",
        border_radius=20,
        on_submit=lambda e: carregar_dados() 
    )

    tabela_geral = ft.DataTable(
        width=float('inf'),
        heading_row_color=ft.colors.GREY_200,
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Data")),
            ft.DataColumn(ft.Text("Cliente")),
            ft.DataColumn(ft.Text("Total (R$)")),
            ft.DataColumn(ft.Text("Pago (R$)")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Ações")), # Coluna unificada
        ],
        rows=[]
    )

    def carregar_dados():
        tabela_geral.rows.clear()
        termo = txt_busca.value
        
        session = get_session()
        query = session.query(OrdemServico).options(joinedload(OrdemServico.cliente)).options(joinedload(OrdemServico.itens)).order_by(OrdemServico.id.desc())
        
        if termo:
            if termo.isdigit():
                query = query.filter(OrdemServico.id == int(termo))
            else:
                # Busca simples por nome (para produção ideal, use join)
                pass 
        
        lista_os = query.limit(50).all() 
        session.close()

        for os_obj in lista_os:
            nome_cli = os_obj.cliente.nome_empresa if os_obj.cliente else "Consumidor"
            if termo and not termo.isdigit() and termo.lower() not in nome_cli.lower():
                continue

            v_total = f"R$ {os_obj.valor_total:.2f}" if os_obj.valor_total else "R$ 0.00"
            v_pago = f"R$ {os_obj.valor_pago:.2f}" if os_obj.valor_pago else "R$ 0.00"
            
            cor_st = ft.colors.BLUE
            if os_obj.status == "Entregue": cor_st = ft.colors.GREEN
            elif os_obj.status == "Cancelado": cor_st = ft.colors.RED
            elif os_obj.status == "Aguardando Pagamento": cor_st = ft.colors.ORANGE

            tabela_geral.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(os_obj.id), weight="bold")),
                    ft.DataCell(ft.Text(os_obj.data_criacao.strftime("%d/%m/%Y"))),
                    ft.DataCell(ft.Text(nome_cli)),
                    ft.DataCell(ft.Text(v_total)),
                    ft.DataCell(ft.Text(v_pago)),
                    ft.DataCell(ft.Container(
                        content=ft.Text(os_obj.status, color="white", size=10, weight="bold"),
                        bgcolor=cor_st, padding=5, border_radius=5
                    )),
                    ft.DataCell(
                        ft.Row([
                            # Botão de Impressão
                            ft.IconButton(
                                icon=ft.Icons.PRINT, 
                                icon_color=ft.colors.BLUE_600, 
                                tooltip="Imprimir O.S.",
                                on_click=lambda e, obj=os_obj: imprimir_os_individual(obj)
                            ),
                            # Botão de Edição
                            ft.IconButton(
                                icon=ft.Icons.EDIT_DOCUMENT, 
                                icon_color=ft.colors.GREY_700, 
                                tooltip="Corrigir Valores",
                                on_click=lambda e, obj=os_obj: abrir_edicao(obj)
                            )
                        ], spacing=0)
                    ),
                ])
            )
        
        try: tabela_geral.update()
        except: pass

    carregar_dados()

    # --- LAYOUT ---
    return ft.Container(
        padding=20,
        bgcolor=ft.colors.GREY_100,
        expand=True,
        content=ft.Column([
            ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.ARCHIVE, size=30, color=ft.colors.BLUE_GREY_800),
                    ft.Text("Arquivo Geral & Auditoria", size=24, weight="bold", color=ft.colors.BLUE_GREY_800),
                ]),
                txt_busca
            ], alignment="spaceBetween"),
            
            ft.Divider(color="transparent", height=10),
            
            ft.Container(
                bgcolor="white",
                padding=10,
                border_radius=10,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
                content=ft.Column([
                    ft.Text("Histórico Completo de Pedidos", weight="bold", color=ft.colors.GREY_700),
                    ft.Divider(),
                    ft.Column([tabela_geral], scroll=ft.ScrollMode.AUTO, expand=True)
                ], expand=True),
                expand=True
            )
        ])
    )