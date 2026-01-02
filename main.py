import flet as ft
from src.database.database import get_session, Usuario, Empresa, OrdemServico
import hashlib
import sys
import os
import warnings

# VIEWS
from src.views.vendas import ViewNovaVenda 
from src.views.producao import ViewProducao
from src.views.estoque import ViewEstoque
from src.views.financeiro import ViewFinanceiro 
from src.views.clientes import ViewClientes
from src.views.configuracao import ViewConfiguracao
from src.views.relatorio_dia import ViewRelatorioDia # <--- IMPORTAÇÃO NOVA

warnings.filterwarnings("ignore")

def main(page: ft.Page):
    
    # --- CONFIGURAÇÃO SIMPLIFICADA DE IMAGENS ---
    CAMINHO_LOGO_PADRAO = "logo.png"
    CAMINHO_FAVICON_PADRAO = "favicon.png" 

    def get_logo_path():
        if os.path.exists(f"assets/{CAMINHO_LOGO_PADRAO}"):
            return CAMINHO_LOGO_PADRAO
        return ""

    # --- CARGA INICIAL ---
    session = get_session()
    empresa = session.query(Empresa).first()
    nome_app = empresa.nome_fantasia if empresa else "GestãoPro"
    session.close()

    # Janela
    page.title = nome_app
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_100
    page.theme_mode = ft.ThemeMode.LIGHT 
    
    if os.path.exists(f"assets/{CAMINHO_FAVICON_PADRAO}"):
        page.window_icon = f"assets/{CAMINHO_FAVICON_PADRAO}"

    area_conteudo = ft.Container(expand=True, padding=20)

    # --- NAVEGAÇÃO ---
    def navegar_para(e, nome_tela):
        if isinstance(e, ft.ControlEvent):
            for item in menu_coluna.controls:
                if isinstance(item, ft.Container): item.bgcolor = "transparent"
            e.control.bgcolor = ft.Colors.WHITE10
            e.control.update(); menu_coluna.update()

        area_conteudo.content = ft.Container(alignment=ft.alignment.center, content=ft.ProgressRing())
        page.update()

        if nome_tela == "Dashboard": area_conteudo.content = criar_dashboard_content()
        elif nome_tela == "Nova Venda": area_conteudo.content = ViewNovaVenda(page)
        elif nome_tela == "Clientes": area_conteudo.content = ViewClientes(page)
        elif nome_tela == "Produção": area_conteudo.content = ViewProducao(page)
        elif nome_tela == "Estoque": area_conteudo.content = ViewEstoque(page)
        elif nome_tela == "Financeiro": area_conteudo.content = ViewFinanceiro(page)
        elif nome_tela == "Relatorios": area_conteudo.content = ViewRelatorioDia(page) # <---ROTA NOVA
        elif nome_tela == "Configurações": area_conteudo.content = ViewConfiguracao(page)
        elif nome_tela == "Sair": tela_login(); return

        page.update()

    # --- MENU LATERAL ---
    menu_coluna = ft.Column(spacing=5) 

    def CriarSidebar():
        session_sb = get_session()
        emp_sb = session_sb.query(Empresa).first()
        nome_menu = emp_sb.nome_fantasia if emp_sb else "GestãoPro"
        session_sb.close()

        logo_path = get_logo_path()
        if logo_path:
            header_content = ft.Image(src=logo_path, width=80, height=80, fit=ft.ImageFit.CONTAIN)
        else:
            header_content = ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, color=ft.Colors.BLUE_400, size=40)

        def item_menu(icone, texto, destino):
            return ft.Container(content=ft.Row([ft.Icon(icone, color=ft.Colors.WHITE70, size=20), ft.Text(texto, color=ft.Colors.WHITE, size=14, weight="w500")], spacing=15), padding=ft.padding.symmetric(horizontal=20, vertical=15), border_radius=8, ink=True, on_click=lambda e: navegar_para(e, destino))

        menu_coluna.controls = [
            item_menu(ft.Icons.DASHBOARD, "Dashboard", "Dashboard"),
            item_menu(ft.Icons.SHOPPING_CART, "Nova Venda", "Nova Venda"),
            item_menu(ft.Icons.PEOPLE, "Clientes", "Clientes"),
            item_menu(ft.Icons.PRECISION_MANUFACTURING, "Produção", "Produção"),
            item_menu(ft.Icons.INVENTORY_2, "Estoque", "Estoque"),
            item_menu(ft.Icons.ATTACH_MONEY, "Financeiro", "Financeiro"),
            item_menu(ft.Icons.BAR_CHART, "Relatórios", "Relatorios"), # <--- ITEM NOVO
            ft.Divider(color=ft.Colors.WHITE24),
            item_menu(ft.Icons.SETTINGS, "Configurações", "Configurações"),
            item_menu(ft.Icons.EXIT_TO_APP, "Sair", "Sair"),
        ]

        return ft.Container(
            width=260, bgcolor="#263238", padding=10, 
            content=ft.Column([
                ft.Container(padding=20, content=ft.Column([
                    header_content, ft.Container(height=10),
                    ft.Text(nome_menu[:20], size=18, weight="bold", color=ft.Colors.WHITE, text_align="center")
                ], horizontal_alignment="center")),
                ft.Divider(color=ft.Colors.WHITE24, height=1),
                ft.Container(height=20), menu_coluna
            ], scroll=ft.ScrollMode.AUTO) 
        )

    # --- DASHBOARD ---
    def criar_dashboard_content():
        session = get_session()
        try:
            total_os = session.query(OrdemServico).count()
            producao_os = session.query(OrdemServico).filter(OrdemServico.status.in_(['Impressão', 'Acabamento', 'Fila'])).count()
            concluidas_os = session.query(OrdemServico).filter_by(status='Entregue').count()
        except: total_os, producao_os, concluidas_os = 0, 0, 0
        session.close()

        def card_topo(titulo, valor, cor_texto, cor_bg_icone, icone):
            return ft.Container(content=ft.Row([ft.Container(content=ft.Icon(icone, color=cor_texto, size=30), bgcolor=cor_bg_icone, padding=15, border_radius=10), ft.Column([ft.Text(titulo, color=ft.Colors.GREY_600, size=12), ft.Text(str(valor), size=28, weight="bold", color=ft.Colors.BLACK87)], spacing=2)], alignment="start"), width=280, height=100, bgcolor="white", shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12), border_radius=12, padding=20)

        return ft.Container(padding=10, content=ft.Column([
                ft.Text("Visão Geral", size=30, weight="bold", color=ft.Colors.BLUE_GREY_900),
                ft.Divider(color="transparent"),
                ft.Row([card_topo("Total Vendas", total_os, ft.Colors.BLUE_600, ft.Colors.BLUE_50, ft.Icons.RECEIPT_LONG), card_topo("Em Produção", producao_os, ft.Colors.ORANGE_600, ft.Colors.ORANGE_50, ft.Icons.PRECISION_MANUFACTURING), card_topo("Entregues", concluidas_os, ft.Colors.GREEN_600, ft.Colors.GREEN_50, ft.Icons.CHECK_CIRCLE)], wrap=True, alignment="spaceBetween"),
                ft.Divider(height=40, color="transparent"),
                ft.Container(height=300, bgcolor="white", border_radius=10, alignment=ft.alignment.center, shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12), content=ft.Column([ft.Icon(ft.Icons.BAR_CHART, size=50, color=ft.Colors.GREY_300), ft.Text("Gráficos (Em breve)", color=ft.Colors.GREY_400)], alignment="center", horizontal_alignment="center"))
            ]))

    def carregar_sistema_principal():
        page.clean(); page.bgcolor = ft.Colors.GREY_100
        menu = CriarSidebar()
        area_conteudo.content = criar_dashboard_content()
        page.add(ft.Row([menu, area_conteudo], expand=True, spacing=0))
        menu_coluna.controls[0].bgcolor = ft.Colors.WHITE10; page.update()

    # --- LOGIN ---
    def tela_login():
        page.clean(); page.bgcolor = ft.Colors.WHITE
        session = get_session(); empresa = session.query(Empresa).first()
        nome_login = empresa.nome_fantasia if empresa else "GestãoPro"
        session.close()

        txt_usuario = ft.TextField(label="Usuário", width=320, height=50, bgcolor="white", border_radius=8, prefix_icon=ft.Icons.PERSON)
        txt_senha = ft.TextField(label="Senha", password=True, width=320, height=50, bgcolor="white", border_radius=8, prefix_icon=ft.Icons.LOCK, can_reveal_password=True, on_submit=lambda e: realizar_login(e))
        lbl_erro = ft.Text("", color="red", weight="bold")

        def realizar_login(e):
            if not txt_usuario.value or not txt_senha.value: lbl_erro.value = "Preencha tudo."; page.update(); return
            hash_login = hashlib.sha256(txt_senha.value.encode()).hexdigest()
            session = get_session(); user_db = session.query(Usuario).filter_by(usuario=txt_usuario.value, senha_hash=hash_login).first(); session.close()
            if user_db: carregar_sistema_principal()
            else: lbl_erro.value = "Dados incorretos."; page.update()

        btn_entrar = ft.ElevatedButton(text="ENTRAR", width=320, height=50, style=ft.ButtonStyle(color="white", bgcolor=ft.Colors.BLUE_900, shape=ft.RoundedRectangleBorder(radius=8)), on_click=realizar_login)
        logo_path = get_logo_path()
        if logo_path: img_login = ft.Image(src=logo_path, width=200, fit=ft.ImageFit.CONTAIN)
        else: img_login = ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, size=100, color="white")

        container_capa = ft.Container(expand=1, bgcolor=ft.Colors.BLUE_900, padding=40, alignment=ft.alignment.center, content=ft.Column([img_login, ft.Divider(height=20, color="transparent"), ft.Text(nome_login, size=30, weight="bold", color="white", text_align="center"), ft.Text("Sistema Integrado", size=16, color="white70")], alignment="center", horizontal_alignment="center"))
        container_form = ft.Container(expand=1, bgcolor="white", padding=40, alignment=ft.alignment.center, content=ft.Column([ft.Text("Bem-vindo", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900), ft.Divider(height=40, color="transparent"), txt_usuario, ft.Divider(height=10, color="transparent"), txt_senha, ft.Divider(height=10, color="transparent"), lbl_erro, ft.Divider(height=20, color="transparent"), btn_entrar], alignment="center", horizontal_alignment="center"))
        page.add(ft.Row([container_capa, container_form], expand=True, spacing=0))

    tela_login()

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, assets_dir="assets")