import flet as ft
from src.database.database import get_session, ProdutoServico

def ViewEstoque(page):
    
    # --- FUNÇÃO: DAR ENTRADA NO ESTOQUE ---
    def adicionar_estoque(e, prod_id, qtd_input):
        try:
            qtd = int(qtd_input.value)
            if qtd <= 0: return

            session = get_session()
            prod = session.query(ProdutoServico).get(prod_id)
            prod.estoque_atual += qtd
            session.commit()
            
            # Feedback e Atualização Visual
            page.snack_bar = ft.SnackBar(ft.Text(f"+{qtd} adicionados ao {prod.nome}"), bgcolor=ft.colors.GREEN_600)
            page.snack_bar.open = True
            
            # Limpa o input
            qtd_input.value = ""
            
            # Atualiza a tela inteira (Jeito preguiçoso mas funcional para MVP)
            # Idealmente atualizaríamos só a célula, mas vamos recarregar a view no futuro
            # Por enquanto, apenas atualizamos a página para refletir (simples)
            page.update()
            
            session.close()
            # Dica: Para ver a mudança na hora, o ideal é recarregar a view, 
            # mas vamos manter simples: o usuário clica em "Estoque" de novo para atualizar visualmente a tabela
            
        except ValueError:
            pass # Ignora se não for número

    # --- CARREGAR DADOS ---
    session = get_session()
    lista_produtos = session.query(ProdutoServico).all()
    session.close()

    # --- LINHAS DA TABELA ---
    linhas = []
    
    for prod in lista_produtos:
        # Lógica de Cores (Semáforo de Estoque)
        cor_estoque = ft.colors.GREEN_600
        bg_status = ft.colors.GREEN_50
        
        if prod.estoque_atual <= 5: # Crítico
            cor_estoque = ft.colors.RED_600
            bg_status = ft.colors.RED_50
        elif prod.estoque_atual <= prod.estoque_minimo: # Alerta
            cor_estoque = ft.colors.ORANGE_600
            bg_status = ft.colors.ORANGE_50

        # Inputzinho para adicionar rápido
        txt_qtd_add = ft.TextField(width=60, height=35, text_size=12, content_padding=5, hint_text="Qtd")
        
        btn_add = ft.IconButton(
            icon=ft.icons.ADD_CIRCLE, 
            icon_color=ft.colors.BLUE_600,
            tooltip="Dar Entrada",
            on_click=lambda e, pid=prod.id, input_box=txt_qtd_add: adicionar_estoque(e, pid, input_box)
        )

        linhas.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(prod.nome, weight="bold")),
                    ft.DataCell(ft.Text(prod.categoria)),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(f"{prod.estoque_atual} unid", color=cor_estoque, weight="bold"),
                            bgcolor=bg_status,
                            padding=5, border_radius=5
                        )
                    ),
                    ft.DataCell(ft.Row([txt_qtd_add, btn_add], spacing=0)),
                ]
            )
        )

    # --- LAYOUT ---
    tabela = ft.DataTable(
        width=float('inf'),
        heading_row_color=ft.colors.BLUE_GREY_50,
        columns=[
            ft.DataColumn(ft.Text("Produto")),
            ft.DataColumn(ft.Text("Categoria")),
            ft.DataColumn(ft.Text("Estoque Atual")),
            ft.DataColumn(ft.Text("Repor Estoque")),
        ],
        rows=linhas
    )

    card = ft.Container(
        bgcolor=ft.colors.WHITE,
        padding=20,
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
        content=ft.Column([
            ft.Text("Controle de Estoque", size=22, weight="bold", color=ft.colors.BLUE_GREY_800),
            ft.Divider(),
            tabela
        ], scroll=ft.ScrollMode.AUTO)
    )

    return ft.Container(padding=30, expand=True, bgcolor=ft.colors.GREY_100, content=card)