import flet as ft
from src.database.database import get_session, OrdemServico
from sqlalchemy.orm import joinedload
from datetime import datetime

def ViewFinanceiro(page):
    
    # --- FUNÇÃO: REGISTRAR PAGAMENTO ---
    def registrar_pagamento(e, os_id):
        try:
            session = get_session()
            os_atual = session.query(OrdemServico).get(os_id)
            
            if os_atual:
                # Quita a dívida (Define valor pago igual ao total)
                os_atual.valor_pago = os_atual.valor_total
                session.commit()
                
                page.snack_bar = ft.SnackBar(ft.Text(f"Pagamento da OS #{os_id} confirmado!"), bgcolor=ft.Colors.GREEN_600)
                page.snack_bar.open = True
                page.update()
                
                # Recarrega a tela para atualizar a tabela e os cards
                carregar_dados()
            
            session.close()
        except Exception as err:
            print(err)

    # --- ELEMENTOS VISUAIS (TABELA E CARDS) ---
    # Criamos as referências para poder atualizar depois sem recarregar a página toda
    linha_cards = ft.Row(wrap=True, alignment="center")
    tabela_financeira = ft.DataTable(
        width=float('inf'),
        heading_row_color=ft.Colors.GREY_200,
        columns=[
            ft.DataColumn(ft.Text("OS")),
            ft.DataColumn(ft.Text("Cliente")),
            ft.DataColumn(ft.Text("Total")),
            ft.DataColumn(ft.Text("Status Pagamento")), # Barra de Progresso
            ft.DataColumn(ft.Text("Falta")),
            ft.DataColumn(ft.Text("Ação")),
        ],
        rows=[]
    )

    def carregar_dados():
        tabela_financeira.rows.clear()
        linha_cards.controls.clear()

        session = get_session()
        # Busca OS com Cliente (JoinedLoad para performance)
        lista_os = session.query(OrdemServico).options(
            joinedload(OrdemServico.cliente)
        ).order_by(OrdemServico.id.desc()).all()
        session.close()

        # Cálculos Gerais
        total_vendido = sum(os.valor_total for os in lista_os)
        total_recebido = sum(os.valor_pago for os in lista_os)
        total_pendente = total_vendido - total_recebido

        # --- PREENCHE OS CARDS ---
        def criar_card(titulo, valor, cor_texto):
            return ft.Container(
                content=ft.Column([
                    ft.Text(titulo, color=ft.Colors.GREY_600),
                    ft.Text(f"R$ {valor:.2f}", size=24, weight="bold", color=cor_texto)
                ]),
                bgcolor="white", padding=20, border_radius=10, width=250,
                border=ft.border.all(1, ft.Colors.GREY_200),
                shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12)
            )

        linha_cards.controls.append(criar_card("Total Vendido", total_vendido, ft.Colors.BLUE_700))
        linha_cards.controls.append(criar_card("Total Recebido", total_recebido, ft.Colors.GREEN_700))
        linha_cards.controls.append(criar_card("A Receber", total_pendente, ft.Colors.RED_700))

        # --- PREENCHE A TABELA ---
        for os_obj in lista_os:
            pendente = os_obj.valor_total - os_obj.valor_pago
            
            # Lógica da Barra de Progresso
            progresso = 0
            if os_obj.valor_total > 0:
                progresso = os_obj.valor_pago / os_obj.valor_total
            
            # Cores e Status
            cor_barra = ft.Colors.RED_400
            if progresso >= 1: cor_barra = ft.Colors.GREEN_400
            elif progresso > 0.5: cor_barra = ft.Colors.ORANGE_400

            # Botão ou Check
            if pendente <= 0.01: # Considera pago se a diferença for centavos
                acao = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_500)
                texto_falta = ft.Text("Quitado", color=ft.Colors.GREEN_600, weight="bold")
            else:
                acao = ft.ElevatedButton(
                    "Receber", 
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color="white"),
                    height=30,
                    on_click=lambda e, oid=os_obj.id: registrar_pagamento(e, oid)
                )
                texto_falta = ft.Text(f"R$ {pendente:.2f}", color=ft.Colors.RED_600, weight="bold")

            tabela_financeira.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"#{os_obj.id}", weight="bold")),
                    ft.DataCell(ft.Text(os_obj.cliente.nome_empresa if os_obj.cliente else "Consumidor")),
                    ft.DataCell(ft.Text(f"R$ {os_obj.valor_total:.2f}")),
                    ft.DataCell(ft.Column([
                        ft.ProgressBar(value=progresso, width=100, color=cor_barra, bgcolor=ft.Colors.GREY_200),
                        ft.Text(f"{int(progresso*100)}% Pago", size=10, color=ft.Colors.GREY_600)
                    ], alignment="center", spacing=2)),
                    ft.DataCell(texto_falta),
                    ft.DataCell(acao),
                ])
            )
        
        # Atualiza a tela
        try:
            tabela_financeira.update()
            linha_cards.update()
        except: pass

    # Inicializa os dados
    carregar_dados()

    # --- LAYOUT FINAL ---
    return ft.Container(
        padding=30, expand=True, bgcolor=ft.Colors.GREY_100,
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.ATTACH_MONEY, size=30, color=ft.Colors.BLUE_GREY_900),
                ft.Text("Fluxo de Caixa", size=25, weight="bold", color=ft.Colors.BLUE_GREY_900),
            ]),
            ft.Divider(color="transparent"),
            linha_cards,
            ft.Divider(height=30, color="transparent"),
            ft.Container(
                bgcolor="white", padding=10, border_radius=10, 
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
                content=ft.Column([tabela_financeira], scroll=ft.ScrollMode.AUTO),
                expand=True
            )
        ])
    )