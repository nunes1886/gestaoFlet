import flet as ft
from src.database.database import get_session, OrdemServico, ItemOS, Setor, StatusOS
from sqlalchemy.orm import joinedload 
import os
import urllib.parse 

def ViewProducao(page):
    
    filtro_atual = ft.Ref[str]()
    filtro_atual.current = "producao"

    # --- MAPA DE CORES (DB String -> Flet Colors) ---
    MAPA_CORES_FLET = {
        "blue":   (ft.colors.BLUE_50,    ft.colors.BLUE_700,    ft.colors.BLUE_900),
        "orange": (ft.colors.ORANGE_50,  ft.colors.ORANGE_700,  ft.colors.BROWN_900),
        "amber":  (ft.colors.AMBER_50,   ft.colors.AMBER_700,   ft.colors.BROWN_900),
        "green":  (ft.colors.GREEN_50,   ft.colors.GREEN_700,   ft.colors.GREEN_900),
        "purple": (ft.colors.PURPLE_50,  ft.colors.PURPLE_700,  ft.colors.PURPLE_900),
        "red":    (ft.colors.RED_50,     ft.colors.RED_700,     ft.colors.RED_900),
        "grey":   (ft.colors.GREY_50,    ft.colors.GREY_500,    ft.colors.BLACK),
    }

    # --- VARIÁVEIS DE CACHE ---
    cache_opcoes_status = []
    cache_mapa_status_cor = {}

    def recarregar_caches():
        nonlocal cache_opcoes_status, cache_mapa_status_cor
        session = get_session()
        statuses = session.query(StatusOS).order_by(StatusOS.ordem).all()
        cache_opcoes_status = [ft.dropdown.Option(s.nome) for s in statuses]
        cache_mapa_status_cor = {s.nome: s.cor for s in statuses}
        session.close()

    def obter_estilo_dinamico(status_nome):
        cor_nome = cache_mapa_status_cor.get(status_nome, "grey")
        return MAPA_CORES_FLET.get(cor_nome, MAPA_CORES_FLET["grey"])

    def mudar_setor(e, os_id):
        novo_setor = e.control.value
        try:
            session = get_session()
            os_atual = session.query(OrdemServico).get(os_id)
            if os_atual:
                os_atual.setor_atual = novo_setor
                session.commit()
                page.snack_bar = ft.SnackBar(ft.Text(f"Setor alterado para: {novo_setor}"), bgcolor="teal")
                page.snack_bar.open = True
                page.update()
            session.close()
        except Exception as err:
            print(f"Erro ao mudar setor: {err}")

    def mudar_status(e, os_id):
        novo_status = e.control.value
        try:
            session = get_session()
            os_atual = session.query(OrdemServico).get(os_id)
            if os_atual:
                os_atual.status = novo_status
                session.commit()
                page.snack_bar = ft.SnackBar(ft.Text(f"Status alterado: {novo_status}"), bgcolor="green")
                page.snack_bar.open = True
                page.update()
                carregar_dados()
            session.close()
        except Exception as err:
            print(f"Erro: {err}")

    def get_opcoes_setor():
        session = get_session()
        setores = session.query(Setor).all()
        session.close()
        return [ft.dropdown.Option(s.nome) for s in setores]

    def abrir_detalhes(e, os_obj):
        img_arte = ft.Container()
        if os_obj.imagem_os and os.path.exists(os_obj.imagem_os):
            src_flet = os_obj.imagem_os.replace("\\", "/")
            if src_flet.startswith("assets/"): src_flet = src_flet.replace("assets/", "")
            img_arte = ft.Image(src=src_flet, width=400, height=300, fit=ft.ImageFit.CONTAIN, border_radius=10)
        else:
            img_arte = ft.Container(content=ft.Column([ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=50, color="grey"), ft.Text("Sem imagem", color="grey")], alignment="center"), width=400, height=200, bgcolor=ft.colors.GREY_200, border_radius=10, alignment=ft.alignment.center)

        lista_itens_detalhe = ft.Column(spacing=5)
        for item in os_obj.itens:
            lista_itens_detalhe.controls.append(ft.Container(padding=10, bgcolor=ft.colors.GREY_100, border_radius=5, content=ft.Row([ft.Text(f"{item.quantidade}x", weight="bold", size=16, color=ft.colors.BLUE_800), ft.Column([ft.Text(item.descricao_item, weight="bold"), ft.Text(f"Medidas: {item.largura}m x {item.altura}m", size=12, color="grey")])])))

        conteudo = ft.Column([
            ft.Text(f"Cliente: {os_obj.cliente.nome_empresa}", size=18, weight="bold", color=ft.colors.BLUE_GREY_900),
            ft.Text(f"Motivo: {os_obj.motivo or '---'}", size=14, color=ft.colors.BLUE_GREY_600),
            ft.Divider(),
            ft.Text("Itens do Pedido:", weight="bold"), lista_itens_detalhe,
            ft.Divider(),
            ft.Text("Observações:", weight="bold", color=ft.colors.RED_400),
            ft.Container(padding=10, bgcolor=ft.colors.YELLOW_100, border_radius=5, width=float('inf'), content=ft.Text(os_obj.observacoes if os_obj.observacoes else "Nenhuma observação.")),
            ft.Divider(),
            ft.Text("Arte Anexada:", weight="bold"),
            ft.Container(content=img_arte, alignment=ft.alignment.center)
        ], scroll=ft.ScrollMode.AUTO, height=400)

        dlg = ft.AlertDialog(title=ft.Text(f"Detalhes OS #{os_obj.id}"), content=conteudo, actions=[ft.TextButton("Fechar", on_click=lambda e: page.close(dlg))])
        page.open(dlg)

    lista_cards = ft.ListView(expand=True, spacing=10, padding=10)
    opcoes_setores_cache = []

    def criar_card_os(os_obj):
        cor_fundo, cor_borda, cor_texto = obter_estilo_dinamico(os_obj.status)
        txt_resumo = os_obj.motivo if os_obj.motivo else ", ".join([f"{i.quantidade}x {i.descricao_item}" for i in os_obj.itens])

        badge_urgente = ft.Container()
        if os_obj.is_urgente:
            badge_urgente = ft.Container(content=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color="white", size=14), ft.Text("URGENTE", color="white", size=10, weight="bold")], spacing=2), bgcolor=ft.colors.RED_600, padding=ft.padding.symmetric(horizontal=8, vertical=2), border_radius=20)

        dd_status = ft.Dropdown(
            value=os_obj.status, width=130, height=35, text_size=12, content_padding=5,
            bgcolor="white", border_color=cor_borda, border_radius=8,
            options=cache_opcoes_status,
            on_change=lambda e, oid=os_obj.id: mudar_status(e, oid),
            hint_text="Status"
        )

        dd_setor = ft.Dropdown(
            value=os_obj.setor_atual, width=130, height=35, text_size=12, content_padding=5,
            bgcolor="white", border_color=cor_borda, border_radius=8,
            options=opcoes_setores_cache, 
            on_change=lambda e, oid=os_obj.id: mudar_setor(e, oid),
            hint_text="Setor"
        )

        btn_zap = ft.IconButton(icon=ft.Icons.MESSAGE, icon_color=ft.colors.GREY_400, tooltip="Sem telefone")
        if os_obj.cliente.telefone:
            nums = "".join(filter(str.isdigit, os_obj.cliente.telefone))
            if nums:
                lista_itens_msg = "".join([f"\n- {i.quantidade}x {i.descricao_item} ({i.largura}x{i.altura}m)" for i in os_obj.itens])
                saudacao = f"Olá *{os_obj.cliente.nome_empresa}*!"
                status_msg = f"pedido *#{os_obj.id}*" + (f" (*{os_obj.motivo}*)" if os_obj.motivo else "")
                link_zap = f"https://wa.me/55{nums}?text={urllib.parse.quote(f'{saudacao}\n\nAtualização sobre {status_msg}: Status *{os_obj.status}*.\n\n*Resumo:*{lista_itens_msg}')}"
                btn_zap = ft.IconButton(icon=ft.Icons.MESSAGE, icon_color=ft.colors.GREEN_600, tooltip="Enviar WhatsApp", url=link_zap)

        return ft.Container(
            bgcolor=cor_fundo, border_radius=10, padding=0, clip_behavior=ft.ClipBehavior.HARD_EDGE, 
            shadow=ft.BoxShadow(blur_radius=4, color=ft.colors.BLACK12, offset=ft.Offset(0, 2)),
            content=ft.Row([
                ft.Container(width=10, bgcolor=cor_borda, height=130),
                ft.Container(padding=10, expand=True, content=ft.Column([
                    ft.Row([
                        ft.Row([ft.Icon(ft.Icons.TAG, size=14, color=cor_texto), ft.Text(f"OS #{os_obj.id}", weight="bold", size=14, color=cor_texto), ft.Text(f"• {os_obj.data_criacao.strftime('%d/%m %H:%M')}", size=12, color=ft.colors.GREY_600)]),
                        badge_urgente
                    ], alignment="spaceBetween"),
                    ft.Text(os_obj.cliente.nome_empresa, weight="bold", size=16, color=ft.colors.BLACK87, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(txt_resumo, size=13, color=ft.colors.BLACK54, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Divider(height=5, color="transparent"),
                    
                    # --- AQUI ESTÁ A INVERSÃO SOLICITADA ---
                    ft.Row([
                        ft.Row([dd_setor, dd_status], spacing=5), # Setor PRIMEIRO, Status DEPOIS
                        ft.Row([ft.IconButton(icon=ft.Icons.VISIBILITY, icon_color=ft.colors.BLUE_600, tooltip="Ver Detalhes", on_click=lambda e, obj=os_obj: abrir_detalhes(e, obj)), btn_zap], spacing=0)
                    ], alignment="spaceBetween", vertical_alignment="center")
                    # ---------------------------------------

                ], spacing=2))
            ], spacing=0)
        )

    def carregar_dados():
        recarregar_caches()
        nonlocal opcoes_setores_cache
        opcoes_setores_cache = get_opcoes_setor() 

        lista_cards.controls.clear()
        session = get_session()
        query = session.query(OrdemServico).options(joinedload(OrdemServico.itens).joinedload(ItemOS.produto), joinedload(OrdemServico.cliente)).order_by(OrdemServico.id.desc())
        todos = query.all()
        session.close()

        lista_filtrada = []
        if filtro_atual.current == "producao":
            lista_filtrada = [os for os in todos if os.status not in ["Entregue", "Cancelado"]]
        else:
            lista_filtrada = [os for os in todos if os.status in ["Entregue", "Cancelado"]]

        if not lista_filtrada:
            lista_cards.controls.append(ft.Container(content=ft.Text("Nenhuma OS encontrada.", color="grey", size=16), alignment=ft.alignment.center, padding=20))
        else:
            for os_obj in lista_filtrada:
                lista_cards.controls.append(criar_card_os(os_obj))
        
        try: lista_cards.update()
        except: pass

    def mudar_aba(e):
        idx = e.control.selected_index
        filtro_atual.current = "producao" if idx == 0 else "historico"
        carregar_dados()

    abas = ft.Tabs(
        selected_index=0, animation_duration=300, indicator_color=ft.colors.BLUE_600, label_color=ft.colors.BLUE_800, unselected_label_color=ft.colors.GREY_500,
        tabs=[ft.Tab(text="Fila & Produção", icon=ft.Icons.PRECISION_MANUFACTURING), ft.Tab(text="Histórico & Entregues", icon=ft.Icons.CHECK_CIRCLE)],
        on_change=mudar_aba
    )

    carregar_dados()
    
    return ft.Container(
        padding=0, bgcolor=ft.colors.GREY_100, expand=True, 
        content=ft.Column([
            ft.Container(padding=20, bgcolor="white", shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK12),
                content=ft.Column([
                    ft.Row([ft.Row([ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, color=ft.colors.BLUE_800, size=30), ft.Text("Painel de Produção", size=24, weight="bold", color=ft.colors.BLUE_GREY_900)]), ft.IconButton(icon=ft.Icons.REFRESH, icon_color=ft.colors.BLUE_800, tooltip="Atualizar Lista", on_click=lambda e: carregar_dados())], alignment="spaceBetween"),
                    abas
                ])
            ),
            ft.Container(padding=15, content=lista_cards, expand=True)
        ], spacing=0)
    )