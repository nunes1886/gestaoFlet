import flet as ft
from src.database.database import get_session, OrdemServico
from sqlalchemy.orm import joinedload
from datetime import datetime

def ViewFinanceiro(page):
    
    # --- CORES E ESTILOS ---
    COR_VENDIDO = [ft.Colors.BLUE_700, ft.Colors.BLUE_400]
    COR_RECEBIDO = [ft.Colors.GREEN_700, ft.Colors.GREEN_400]
    COR_RECEBER = [ft.Colors.RED_700, ft.Colors.RED_400]

    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # --- FUNÇÃO: REGISTRAR PAGAMENTO ---
    def registrar_pagamento(e, os_id):
        try:
            session = get_session()
            os_atual = session.query(OrdemServico).get(os_id)
            
            if os_atual:
                os_atual.valor_pago = os_atual.valor_total
                session.commit()
                
                page.snack_bar = ft.SnackBar(ft.Text(f"Pagamento da OS #{os_id} confirmado!"), bgcolor=ft.Colors.GREEN_600)
                page.snack_bar.open = True
                page.update()
                
                carregar_dados() # Recarrega
            
            session.close()
        except Exception as err:
            print(err)

    # --- COMPONENTE CARD ---
    def card_financeiro(titulo, valor, icone, cores_gradiente):
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icone, color="white", size=30),
                    padding=10,
                    bgcolor=ft.Colors.WHITE24,
                    border_radius=10
                ),
                ft.Column([
                    ft.Text(titulo, color="white", size=12, weight="w500"),
                    ft.Text(formatar_moeda(valor), size=24, weight="bold", color="white")
                ], spacing=2)
            ], alignment="start", vertical_alignment="center"),
            width=300, 
            height=100,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=cores_gradiente
            ),
            border_radius=15,
            padding=20,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12)
        )

    # --- ELEMENTOS VISUAIS ---
    
    # Dropdown de Filtro (NOVIDADE)
    filtro_status = ft.Dropdown(
        options=[
            ft.dropdown.Option("Todos"),
            ft.dropdown.Option("Pendentes"), # Devedores
            ft.dropdown.Option("Quitados"),
        ],
        value="Todos",
        width=200,
        bgcolor="white",
        border_radius=10,
        content_padding=10,
        on_change=lambda e: carregar_dados() # Recarrega ao mudar
    )

    linha_cards = ft.Row(wrap=True, alignment="spaceBetween", spacing=20)
    
    tabela_financeira = ft.DataTable(
        width=float('inf'),
        heading_row_color=ft.Colors.GREY_50,
        data_row_max_height=60,
        columns=[
            ft.DataColumn(ft.Text("OS", weight="bold")),
            ft.DataColumn(ft.Text("Cliente")),
            ft.DataColumn(ft.Text("Total")),
            ft.DataColumn(ft.Text("Status Pagamento")),
            ft.DataColumn(ft.Text("Falta")),
            ft.DataColumn(ft.Text("Ação")),
        ],
        rows=[]
    )

    def carregar_dados():
        tabela_financeira.rows.clear()
        linha_cards.controls.clear()

        session = get_session()
        # Busca todas para calcular totais corretamente
        lista_os = session.query(OrdemServico).options(
            joinedload(OrdemServico.cliente)
        ).order_by(OrdemServico.id.desc()).all()
        session.close()

        # 1. Totais Gerais (Sempre calculados sobre tudo)
        total_vendido = sum(os.valor_total for os in lista_os if os.valor_total)
        total_recebido = sum(os.valor_pago for os in lista_os if os.valor_pago)
        total_pendente = total_vendido - total_recebido

        linha_cards.controls.append(card_financeiro("Total Vendido", total_vendido, ft.Icons.POINT_OF_SALE, COR_VENDIDO))
        linha_cards.controls.append(card_financeiro("Total Recebido", total_recebido, ft.Icons.SAVINGS, COR_RECEBIDO))
        linha_cards.controls.append(card_financeiro("A Receber", total_pendente, ft.Icons.MONEY_OFF, COR_RECEBER))

        # 2. Preenchimento da Tabela (Com Filtro)
        opcao_filtro = filtro_status.value # Pega o valor do dropdown

        for os_obj in lista_os:
            v_total = os_obj.valor_total or 0.0
            v_pago = os_obj.valor_pago or 0.0
            pendente = v_total - v_pago
            
            eh_quitado = pendente <= 0.01

            # --- LÓGICA DO FILTRO ---
            if opcao_filtro == "Pendentes" and eh_quitado:
                continue # Pula se queremos ver pendentes mas esse já pagou
            if opcao_filtro == "Quitados" and not eh_quitado:
                continue # Pula se queremos ver quitados mas esse deve
            # ------------------------

            # Lógica Visual (Igual ao anterior)
            progresso = 0
            if v_total > 0: progresso = v_pago / v_total
            
            cor_barra = ft.Colors.RED_400
            status_texto = "Pendente"
            
            if progresso >= 0.99: 
                cor_barra = ft.Colors.GREEN_400
                status_texto = "Quitado"
            elif progresso > 0.5: 
                cor_barra = ft.Colors.ORANGE_400
                status_texto = "Parcial"

            if eh_quitado: 
                acao = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_500)
                texto_falta = ft.Text("Quitado", color=ft.Colors.GREEN_600, weight="bold")
            else:
                acao = ft.ElevatedButton(
                    "Receber", 
                    style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color="white"),
                    height=30,
                    on_click=lambda e, oid=os_obj.id: registrar_pagamento(e, oid)
                )
                texto_falta = ft.Text(formatar_moeda(pendente), color=ft.Colors.RED_600, weight="bold")

            tabela_financeira.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(f"#{os_obj.id}", weight="bold")),
                    ft.DataCell(ft.Text(os_obj.cliente.nome_empresa if os_obj.cliente else "Consumidor")),
                    ft.DataCell(ft.Text(formatar_moeda(v_total))),
                    ft.DataCell(ft.Column([
                        ft.ProgressBar(value=progresso, width=100, color=cor_barra, bgcolor=ft.Colors.GREY_200),
                        ft.Text(f"{int(progresso*100)}% ({status_texto})", size=10, color=ft.Colors.GREY_600)
                    ], alignment="center", spacing=2)),
                    ft.DataCell(texto_falta),
                    ft.DataCell(acao),
                ])
            )
        
        try:
            tabela_financeira.update()
            linha_cards.update()
        except: pass

    carregar_dados()

    # --- LAYOUT FINAL ---
    return ft.Container(
        padding=20, expand=True, bgcolor=ft.Colors.GREY_100,
        content=ft.Column([
            # Cabeçalho com Título e Filtro
            ft.Row([
                ft.Row([
                    ft.Icon(ft.Icons.ATTACH_MONEY, size=30, color=ft.Colors.BLUE_GREY_800),
                    ft.Text("Fluxo de Caixa", size=28, weight="bold", color=ft.Colors.BLUE_GREY_800),
                ]),
                # Filtro alinhado à direita
                ft.Row([
                    ft.Icon(ft.Icons.FILTER_LIST, color=ft.Colors.GREY_600),
                    ft.Text("Filtrar:", color=ft.Colors.GREY_700, weight="bold"),
                    filtro_status
                ], alignment="center")
            ], alignment="spaceBetween"), # Espaço entre Título e Filtro
            
            ft.Divider(color="transparent", height=10),
            
            linha_cards,
            
            ft.Divider(height=30, color="transparent"),
            
            ft.Container(
                bgcolor="white", padding=10, border_radius=15, 
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
                content=ft.Column([
                    ft.Text("Lançamentos", size=18, weight="bold", color=ft.Colors.GREY_700),
                    ft.Divider(color="transparent", height=5),
                    tabela_financeira
                ], scroll=ft.ScrollMode.AUTO),
                expand=True
            )
        ], scroll=ft.ScrollMode.AUTO)
    )