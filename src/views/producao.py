import flet as ft
from src.database.database import get_session, OrdemServico, ItemOS
# Importamos joinedload para carregar dados vinculados (itens e cliente)
from sqlalchemy.orm import joinedload 
from datetime import datetime

def ViewProducao(page):
    
    # --- FUNÇÃO PARA ATUALIZAR STATUS NO BANCO ---
    def mudar_status(e, os_id):
        novo_status = e.control.value
        print(f"Mudando OS #{os_id} para {novo_status}")
        
        try:
            session = get_session()
            os_atual = session.query(OrdemServico).get(os_id)
            if os_atual:
                os_atual.status = novo_status
                session.commit()
                
                # Feedback visual
                e.control.bgcolor = obter_cor_status(novo_status)
                e.control.update()
                
                page.snack_bar = ft.SnackBar(ft.Text(f"OS #{os_id} atualizada para {novo_status}"), bgcolor=ft.colors.GREEN_600)
                page.snack_bar.open = True
                page.update()
            session.close()
            
        except Exception as err:
            print(f"Erro ao mudar status: {err}")

    # --- HELPERS VISUAIS ---
    def obter_cor_status(status):
        cores = {
            "Fila": ft.colors.BLACK87,
            "Impressão": ft.colors.BLUE_600,
            "Acabamento": ft.colors.ORANGE_600,
            "Expedição": ft.colors.PURPLE_600,
            "Entregue": ft.colors.GREEN_600
        }
        return cores.get(status, ft.colors.GREY_500)

    # --- CARREGAR DADOS DO BANCO (CORRIGIDO COM JOINEDLOAD) ---
    session = get_session()
    
    # AQUI ESTÁ A CORREÇÃO MÁGICA:
    # O .options(joinedload(...)) força o banco a trazer os Itens e o Cliente junto com a OS.
    # Assim, quando fechamos a sessão, os dados já estão na memória.
    lista_os = session.query(OrdemServico).options(
        joinedload(OrdemServico.itens).joinedload(ItemOS.produto), # Traz itens e seus produtos
        joinedload(OrdemServico.cliente) # Traz o cliente
    ).order_by(OrdemServico.id.desc()).all()
    
    session.close()

    # --- MONTAGEM DAS LINHAS DA TABELA ---
    linhas_tabela = []
    
    for os in lista_os:
        # Resumo dos itens (Agora funciona porque os dados foram carregados antes)
        lista_nomes = [f"{item.quantidade}x {item.produto.nome}" for item in os.itens]
        resumo_itens = ", ".join(lista_nomes)
        
        if len(resumo_itens) > 50: resumo_itens = resumo_itens[:47] + "..."

        # Dropdown de Status
        dd_status = ft.Dropdown(
            value=os.status,
            width=140,
            height=35,
            text_size=12,
            content_padding=5,
            bgcolor=obter_cor_status(os.status),
            color=ft.colors.WHITE,
            border_width=0,
            border_radius=5,
            options=[
                ft.dropdown.Option("Fila"),
                ft.dropdown.Option("Impressão"),
                ft.dropdown.Option("Acabamento"),
                ft.dropdown.Option("Expedição"),
                ft.dropdown.Option("Entregue"),
            ],
            on_change=lambda e, os_id=os.id: mudar_status(e, os_id)
        )

        nova_linha = ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(f"#{os.id}", weight="bold")),
                ft.DataCell(ft.Text(os.data_criacao.strftime("%d/%m %H:%M"))),
                ft.DataCell(ft.Text(os.cliente.nome_empresa, weight="bold")), # Cliente já carregado
                ft.DataCell(ft.Text(resumo_itens, size=12, color=ft.colors.GREY_700)),
                ft.DataCell(dd_status),
                ft.DataCell(
                    ft.IconButton(
                        icon=ft.icons.VISIBILITY, 
                        icon_color=ft.colors.BLUE_600,
                        tooltip="Ver Detalhes"
                    )
                ),
            ]
        )
        linhas_tabela.append(nova_linha)

    # --- ESTRUTURA DA TELA ---
    
    header = ft.Row(
        [
            ft.Text("Painel de Produção", size=25, weight="bold", color=ft.colors.BLUE_GREY_900),
            ft.Container(
                content=ft.Row([
                    ft.Icon(ft.icons.SEARCH, color=ft.colors.GREY_400),
                    ft.Text("Buscar OS...", color=ft.colors.GREY_400)
                ]),
                bgcolor=ft.colors.WHITE,
                padding=10,
                border_radius=20,
                width=300,
                border=ft.border.all(1, ft.colors.GREY_300)
            )
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    tabela = ft.DataTable(
        width=float('inf'),
        heading_row_color=ft.colors.BLUE_GREY_50,
        heading_row_height=50,
        data_row_min_height=60,
        column_spacing=20,
        columns=[
            ft.DataColumn(ft.Text("OS", weight="bold")),
            ft.DataColumn(ft.Text("Data", weight="bold")),
            ft.DataColumn(ft.Text("Cliente", weight="bold")),
            ft.DataColumn(ft.Text("Itens / Detalhes", weight="bold")),
            ft.DataColumn(ft.Text("Status", weight="bold")),
            ft.DataColumn(ft.Text("Ações", weight="bold")),
        ],
        rows=linhas_tabela
    )

    card_tabela = ft.Container(
        bgcolor=ft.colors.WHITE,
        border_radius=15,
        padding=20,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
        content=ft.Column(
            [
                tabela
            ],
            scroll=ft.ScrollMode.AUTO
        ),
        expand=True
    )

    return ft.Container(
        padding=30,
        bgcolor=ft.colors.GREY_100,
        expand=True,
        content=ft.Column(
            [
                header,
                ft.Divider(color="transparent", height=20),
                card_tabela
            ]
        )
    )