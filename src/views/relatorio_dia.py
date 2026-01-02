import flet as ft
from src.database.database import get_session, OrdemServico, Cliente
from datetime import datetime
from sqlalchemy import func
from src.utils.gerar_relatorio import gerar_pdf_relatorio_dia # Importa o gerador que criamos acima
from src.utils.gerar_pdf import gerar_pdf_venda # Para reimprimir recibos individuais

def ViewRelatorioDia(page: ft.Page):
    
    vendas_hoje = []
    
    # Campo de Data (Inicia com hoje)
    txt_data = ft.TextField(value=datetime.now().strftime("%d/%m/%Y"), width=120, height=40, content_padding=10, bgcolor="white", text_align="center", read_only=True)
    
    # DatePicker
    def mudar_data(e):
        if date_picker.value:
            txt_data.value = date_picker.value.strftime("%d/%m/%Y")
            page.update()
            carregar_dados() # Recarrega ao mudar data

    date_picker = ft.DatePicker(on_change=mudar_data, first_date=datetime(2023,1,1), last_date=datetime(2030,12,31))
    page.overlay.append(date_picker)

    # Tabela
    tabela = ft.DataTable(
        heading_row_height=40, column_spacing=20,
        columns=[
            ft.DataColumn(ft.Text("OS")),
            ft.DataColumn(ft.Text("Cliente")),
            ft.DataColumn(ft.Text("Detalhes")),
            ft.DataColumn(ft.Text("Total OS", weight="bold")),
            ft.DataColumn(ft.Text("Entrada (Hoje)", color="green", weight="bold")),
            ft.DataColumn(ft.Text("Ações")),
        ], rows=[]
    )

    txt_total_caixa = ft.Text("R$ 0.00", size=25, weight="bold", color="white")
    
    def carregar_dados():
        nonlocal vendas_hoje
        tabela.rows.clear()
        
        data_formatada = datetime.strptime(txt_data.value, "%d/%m/%Y").date()
        
        session = get_session()
        # Filtra vendas criadas nesta data (Simples)
        # Obs: Num sistema contábil complexo, fariamos uma tabela de 'MovimentacaoCaixa', 
        # mas aqui vamos filtrar pela data da OS para simplificar conforme pedido.
        vendas = session.query(OrdemServico).filter(func.date(OrdemServico.data_criacao) == data_formatada).all()
        vendas_hoje = vendas # Guarda para usar na impressão
        
        total_dia = 0.0
        
        for v in vendas:
            total_dia += v.valor_pago
            
            # Resumo dos itens
            detalhe_texto = v.itens[0].descricao_item if v.itens else "-"
            if len(v.itens) > 1: detalhe_texto += f" (+{len(v.itens)-1})"

            tabela.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(f"#{v.id}")),
                ft.DataCell(ft.Text(v.cliente.nome_empresa[:20])),
                ft.DataCell(ft.Text(detalhe_texto[:30])),
                ft.DataCell(ft.Text(f"R$ {v.valor_total:.2f}")),
                ft.DataCell(ft.Text(f"R$ {v.valor_pago:.2f}", color="green", weight="bold")),
                ft.DataCell(ft.ElevatedButton("Recibo", icon=ft.Icons.PRINT, height=30, style=ft.ButtonStyle(padding=5), on_click=lambda e, os_obj=v: gerar_pdf_venda(os_obj)))
            ]))
        
        txt_total_caixa.value = f"R$ {total_dia:.2f}"
        session.close()
        page.update()

    def imprimir_relatorio_geral(e):
        if not vendas_hoje:
            page.snack_bar = ft.SnackBar(ft.Text("Sem movimentação para imprimir!"), bgcolor="red"); page.snack_bar.open=True; page.update(); return
        
        total = sum(v.valor_pago for v in vendas_hoje)
        gerar_pdf_relatorio_dia(txt_data.value, vendas_hoje, total)

    carregar_dados()

    # --- LAYOUT ---
    return ft.Container(
        padding=20, expand=True, bgcolor=ft.Colors.GREY_100,
        content=ft.Column([
            # TOPO: Título e Filtros
            ft.Container(
                bgcolor="#263238", padding=15, border_radius=10,
                content=ft.Row([
                    ft.Icon(ft.Icons.BAR_CHART, color="white"),
                    ft.Text("Relatório de Movimentação", size=20, weight="bold", color="white"),
                    ft.Container(expand=True), # Espaçador
                    ft.Text("Data:", color="white"),
                    ft.Row([
                        txt_data,
                        ft.IconButton(ft.Icons.CALENDAR_MONTH, icon_color="white", on_click=lambda _: date_picker.pick_date()),
                    ]),
                    ft.ElevatedButton("Filtrar", bgcolor="blue", color="white", on_click=lambda _: carregar_dados()),
                    ft.ElevatedButton("Imprimir Relatório", icon=ft.Icons.PRINT, bgcolor="green", color="white", on_click=imprimir_relatorio_geral),
                ], alignment="spaceBetween")
            ),
            
            ft.Divider(color="transparent", height=10),

            # CAIXA DIÁRIO (Card Verde)
            ft.Container(
                bgcolor="green", padding=20, border_radius=10,
                content=ft.Row([
                    ft.Column([
                        ft.Text("Caixa Diário", color="white", size=14),
                        ft.Text("Entradas de Hoje", color=ft.Colors.WHITE70, size=12),
                    ]),
                    txt_total_caixa
                ], alignment="spaceBetween")
            ),

            ft.Divider(color="transparent", height=10),

            # TABELA
            ft.Container(
                bgcolor="white", padding=10, border_radius=10, expand=True,
                content=ft.Column([tabela], scroll=ft.ScrollMode.AUTO)
            )
        ])
    )