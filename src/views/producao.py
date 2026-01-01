import flet as ft
from src.database.database import get_session, OrdemServico, ItemOS
from sqlalchemy.orm import joinedload 
import os
import urllib.parse 

def ViewProducao(page):
    
    filtro_atual = ft.Ref[str]()
    filtro_atual.current = "producao"

    def mudar_status(e, os_id):
        novo_status = e.control.value
        try:
            session = get_session()
            os_atual = session.query(OrdemServico).get(os_id)
            if os_atual:
                os_atual.status = novo_status
                session.commit()
                e.control.bgcolor = obter_cor_status(novo_status)
                e.control.update()
                page.snack_bar = ft.SnackBar(ft.Text(f"OS #{os_id} -> {novo_status}"), bgcolor=ft.Colors.GREEN)
                page.snack_bar.open = True
                page.update()
                if novo_status == "Entregue" and filtro_atual.current == "producao":
                    carregar_dados()
            session.close()
        except Exception as err:
            print(f"Erro: {err}")

    def obter_cor_status(status):
        cores = {
            "Fila": ft.Colors.GREY_700,
            "Impressão": ft.Colors.BLUE_600,
            "Acabamento": ft.Colors.ORANGE_600,
            "Expedição": ft.Colors.PURPLE_600,
            "Entregue": ft.Colors.GREEN_600
        }
        return cores.get(status, ft.Colors.GREY_500)

    def abrir_detalhes(e, os_obj):
        img_arte = ft.Container()
        if os_obj.imagem_os and os.path.exists(os_obj.imagem_os):
            src_flet = os_obj.imagem_os.replace("\\", "/")
            if src_flet.startswith("assets/"): src_flet = src_flet.replace("assets/", "")
            img_arte = ft.Image(src=src_flet, width=400, height=300, fit=ft.ImageFit.CONTAIN, border_radius=10)
        else:
            img_arte = ft.Container(content=ft.Column([ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=50, color="grey"), ft.Text("Sem imagem", color="grey")], alignment="center"), width=400, height=200, bgcolor=ft.Colors.GREY_200, border_radius=10, alignment=ft.alignment.center)

        lista_itens_detalhe = ft.Column(spacing=5)
        for item in os_obj.itens:
            lista_itens_detalhe.controls.append(ft.Container(padding=10, bgcolor=ft.Colors.GREY_100, border_radius=5, content=ft.Row([ft.Text(f"{item.quantidade}x", weight="bold", size=16), ft.Column([ft.Text(item.descricao_item, weight="bold"), ft.Text(f"Medidas: {item.largura}m x {item.altura}m")])])))

        conteudo = ft.Column([
            ft.Text(f"Cliente: {os_obj.cliente.nome_empresa}", size=16, weight="bold"),
            ft.Text(f"Motivo/Ref: {os_obj.motivo or '---'}", size=14, color=ft.Colors.BLUE_GREY_700), # Mostra o motivo no modal
            ft.Divider(),
            ft.Text("Itens:", weight="bold"), lista_itens_detalhe,
            ft.Divider(),
            ft.Text("Observações:", weight="bold", color=ft.Colors.RED_400),
            ft.Container(padding=10, bgcolor=ft.Colors.YELLOW_100, border_radius=5, width=float('inf'), content=ft.Text(os_obj.observacoes if os_obj.observacoes else "Nenhuma observação.")),
            ft.Divider(),
            ft.Text("Arte:", weight="bold"),
            ft.Container(content=img_arte, alignment=ft.alignment.center)
        ], scroll=ft.ScrollMode.AUTO, height=400)

        dlg = ft.AlertDialog(title=ft.Text(f"Detalhes OS #{os_obj.id}"), content=conteudo, actions=[ft.TextButton("Fechar", on_click=lambda e: page.close(dlg))])
        page.open(dlg)

    tabela = ft.DataTable(
        width=float('inf'), heading_row_color=ft.Colors.BLUE_GREY_50, column_spacing=10,
        columns=[
            ft.DataColumn(ft.Text("OS", weight="bold")),
            ft.DataColumn(ft.Text("Data", weight="bold")),
            ft.DataColumn(ft.Text("Cliente", weight="bold")),
            ft.DataColumn(ft.Text("Motivo / Resumo", weight="bold")), # Mudança no título
            ft.DataColumn(ft.Text("Status", weight="bold")),
            ft.DataColumn(ft.Text("Ações", weight="bold")), 
        ], rows=[]
    )

    def carregar_dados():
        tabela.rows.clear()
        session = get_session()
        query = session.query(OrdemServico).options(joinedload(OrdemServico.itens).joinedload(ItemOS.produto), joinedload(OrdemServico.cliente)).order_by(OrdemServico.id.desc())
        todos = query.all()
        session.close()

        lista_filtrada = [os for os in todos if os.status in ["Fila", "Impressão", "Acabamento"]] if filtro_atual.current == "producao" else [os for os in todos if os.status in ["Expedição", "Entregue"]]

        for os_obj in lista_filtrada:
            # Resumo Inteligente: Mostra o MOTIVO se tiver, senão mostra os itens
            if os_obj.motivo:
                txt_resumo = f"{os_obj.motivo[:30]}"
                cor_resumo = ft.Colors.BLACK87
                peso_resumo = "bold"
            else:
                txt_resumo = ", ".join([f"{i.quantidade}x {i.descricao_item[:20]}" for i in os_obj.itens])
                if len(txt_resumo) > 30: txt_resumo = txt_resumo[:27] + "..."
                cor_resumo = "grey"
                peso_resumo = "normal"

            dd_status = ft.Dropdown(
                value=os_obj.status, width=120, height=35, text_size=12, content_padding=5,
                bgcolor=obter_cor_status(os_obj.status), color="white", border_radius=5, border_width=0,
                options=[ft.dropdown.Option("Fila"), ft.dropdown.Option("Impressão"), ft.dropdown.Option("Acabamento"), ft.dropdown.Option("Expedição"), ft.dropdown.Option("Entregue")],
                on_change=lambda e, oid=os_obj.id: mudar_status(e, oid)
            )

            btn_zap = ft.Container() 
            if os_obj.cliente.telefone:
                nums = "".join(filter(str.isdigit, os_obj.cliente.telefone))
                if nums:
                    lista_itens_msg = ""
                    for item in os_obj.itens:
                        lista_itens_msg += f"\n- {item.quantidade}x {item.descricao_item}"
                        if item.largura > 0 and item.altura > 0: lista_itens_msg += f" ({item.largura}x{item.altura}m)"

                    saudacao = f"Olá *{os_obj.cliente.nome_empresa}*!"
                    
                    # Mensagem personalizada
                    status_msg = f"pedido *#{os_obj.id}*"
                    if os_obj.motivo:
                        status_msg += f" (*{os_obj.motivo}*)" # Adiciona o motivo na mensagem
                    
                    if os_obj.status == "Expedição": corpo = f"Seu {status_msg} está pronto e aguardando retirada/envio. 📦"
                    elif os_obj.status == "Entregue": corpo = f"Obrigado por retirar o {status_msg}. ✅"
                    else: corpo = f"Atualização sobre o {status_msg}: Fase de *{os_obj.status}*."

                    msg_completa = f"{saudacao}\n\n{corpo}\n\n*Resumo:*{lista_itens_msg}"
                    link_zap = f"https://wa.me/55{nums}?text={urllib.parse.quote(msg_completa)}"
                    btn_zap = ft.IconButton(icon=ft.Icons.MESSAGE, icon_color=ft.Colors.GREEN, tooltip="Enviar WhatsApp", url=link_zap)

            tabela.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(f"#{os_obj.id}", weight="bold")),
                ft.DataCell(ft.Text(os_obj.data_criacao.strftime("%d/%m %H:%M"))),
                ft.DataCell(ft.Text(os_obj.cliente.nome_empresa[:20])),
                ft.DataCell(ft.Text(txt_resumo, size=12, color=cor_resumo, weight=peso_resumo)), # Mostra o motivo aqui
                ft.DataCell(dd_status),
                ft.DataCell(ft.Row([ft.IconButton(icon=ft.Icons.VISIBILITY, icon_color=ft.Colors.BLUE, tooltip="Detalhes", on_click=lambda e, obj=os_obj: abrir_detalhes(e, obj)), btn_zap], spacing=0)),
            ]))
        try: tabela.update()
        except: pass

    def mudar_aba(e):
        idx = e.control.selected_index
        filtro_atual.current = "producao" if idx == 0 else "historico"
        carregar_dados()

    abas = ft.Tabs(selected_index=0, animation_duration=300, tabs=[ft.Tab(text="Fila / Produção", icon=ft.Icons.FORMAT_LIST_BULLETED), ft.Tab(text="Expedição / Entregues", icon=ft.Icons.CHECK_CIRCLE)], on_change=mudar_aba)

    carregar_dados()
    return ft.Container(padding=20, bgcolor=ft.Colors.GREY_100, expand=True, content=ft.Column([ft.Row([ft.Text("Painel de Produção", size=25, weight="bold", color=ft.Colors.BLUE_GREY_900), ft.IconButton(icon=ft.Icons.REFRESH, tooltip="Atualizar", on_click=lambda e: carregar_dados())], alignment="spaceBetween"), abas, ft.Container(bgcolor="white", padding=10, border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12), content=ft.Column([tabela], scroll=ft.ScrollMode.AUTO), expand=True)]))