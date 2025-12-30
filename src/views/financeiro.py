import flet as ft
from src.database.database import get_session, OrdemServico
from sqlalchemy.orm import joinedload # <--- Importante para corrigir o erro
from datetime import datetime

def ViewFinanceiro(page):
    
    # --- FUNÇÃO: REGISTRAR PAGAMENTO ---
    def registrar_pagamento(e, os_id, valor_restante):
        try:
            session = get_session()
            os_atual = session.query(OrdemServico).get(os_id)
            
            if os_atual:
                # Quita a dívida
                os_atual.valor_pago = os_atual.valor_total
                session.commit()
                
                page.snack_bar = ft.SnackBar(ft.Text(f"Pagamento da OS #{os_id} registrado!"), bgcolor=ft.colors.GREEN_600)
                page.snack_bar.open = True
                page.update()
            
            session.close()
            # Idealmente recarregaríamos a view aqui. 
            # Por enquanto, o usuário clica no menu de novo para atualizar.
            
        except Exception as err:
            print(err)

    # --- DADOS ---
    session = get_session()
    
    # --- CORREÇÃO AQUI ---
    # Usamos .options(joinedload(OrdemServico.cliente)) para trazer o cliente junto
    lista_os = session.query(OrdemServico).options(
        joinedload(OrdemServico.cliente)
    ).order_by(OrdemServico.id.desc()).all()
    
    session.close()

    # Cálculos Gerais
    total_vendido = sum(os.valor_total for os in lista_os)
    total_recebido = sum(os.valor_pago for os in lista_os)
    total_pendente = total_vendido - total_recebido

    # --- TABELA ---
    linhas = []
    
    for os in lista_os:
        pendente = os.valor_total - os.valor_pago
        status_pgto = "Pendente"
        cor_status = ft.colors.RED_600
        
        # Define se mostra botão ou check de pago
        if os.valor_pago >= os.valor_total:
            botao_acao = ft.Icon(ft.icons.CHECK_CIRCLE, color=ft.colors.GREEN_400)
            cor_status = ft.colors.GREEN_600
        else:
            botao_acao = ft.ElevatedButton(
                "Receber", 
                height=30, 
                style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_600, color="white"),
                on_click=lambda e, oid=os.id, rest=pendente: registrar_pagamento(e, oid, rest)
            )

        # Cálculo da barra de progresso (evita divisão por zero)
        progresso = 0
        if os.valor_total > 0:
            progresso = os.valor_pago / os.valor_total

        linhas.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(f"#{os.id}", weight="bold")),
                    ft.DataCell(ft.Text(os.cliente.nome_empresa)), # Agora isso funciona!
                    ft.DataCell(ft.Text(f"R$ {os.valor_total:.2f}")),
                    ft.DataCell(ft.Column([
                        ft.Text(f"Recebido: R$ {os.valor_pago:.2f}", size=10),
                        ft.ProgressBar(value=progresso, width=100, color=cor_status, bgcolor=ft.colors.GREY_200)
                    ], alignment="center")),
                    ft.DataCell(ft.Text(f"R$ {pendente:.2f}", color=ft.colors.RED_600 if pendente > 0 else ft.colors.GREY_400, weight="bold")),
                    ft.DataCell(botao_acao),
                ]
            )
        )

    # --- CARDS DO TOPO ---
    def card_fin(titulo, valor, cor):
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, color=ft.colors.GREY_600),
                ft.Text(f"R$ {valor:.2f}", size=24, weight="bold", color=cor)
            ]),
            bgcolor="white", padding=20, border_radius=10, width=250,
            border=ft.border.all(1, ft.colors.GREY_200)
        )

    # --- LAYOUT FINAL ---
    return ft.Container(
        padding=30, expand=True, bgcolor=ft.colors.GREY_100,
        content=ft.Column([
            ft.Text("Fluxo de Caixa (Vendas)", size=25, weight="bold", color=ft.colors.BLUE_GREY_900),
            ft.Divider(color="transparent"),
            ft.Row([
                card_fin("Total Vendido", total_vendido, ft.colors.BLUE_700),
                card_fin("Total Recebido", total_recebido, ft.colors.GREEN_700),
                card_fin("A Receber", total_pendente, ft.colors.RED_700),
            ], wrap=True),
            ft.Divider(height=30, color="transparent"),
            ft.Container(
                bgcolor="white", padding=20, border_radius=10, shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
                content=ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("OS")),
                        ft.DataColumn(ft.Text("Cliente")),
                        ft.DataColumn(ft.Text("Total")),
                        ft.DataColumn(ft.Text("Progresso")),
                        ft.DataColumn(ft.Text("Falta")),
                        ft.DataColumn(ft.Text("Ação")),
                    ],
                    rows=linhas
                )
            )
        ], scroll=ft.ScrollMode.AUTO)
    )