import flet as ft
from src.database.database import get_session, Usuario, Empresa, OrdemServico
import hashlib
import sys
import os
import warnings

# --- IMPORTAÇÃO DAS VIEWS ---
from src.views.vendas import ViewNovaVenda 
from src.views.producao import ViewProducao
from src.views.estoque import ViewEstoque
from src.views.financeiro import ViewFinanceiro 
from src.views.clientes import ViewClientes
from src.views.configuracao import ViewConfiguracao

# Silencia avisos de versão
warnings.filterwarnings("ignore")

def main(page: ft.Page):
    
    # --- FUNÇÃO AUXILIAR PARA CORRIGIR CAMINHOS DE IMAGEM ---
    # O Flet se perde se você mandar "assets/logo.png" quando o assets_dir já é "assets"
    # Essa função limpa o caminho para funcionar perfeito.
    def resolver_src(caminho):
        if not caminho or not os.path.exists(caminho):
            return ""
        # Retorna apenas o nome do arquivo (ex: "logo.png")
        return os.path.basename(caminho)

    # --- CONFIGURAÇÃO INICIAL (Load do Banco) ---
    session = get_session()
    empresa = session.query(Empresa).first()
    
    # Define valores padrão caso não tenha configuração
    nome_app = empresa.nome_fantasia if empresa else "GestãoPro"
    path_icon = empresa.caminho_icon if (empresa and empresa.caminho_icon) else ""
    path_logo = empresa.caminho_logo if (empresa and empresa.caminho_logo) else ""
    session.close()

    # Configurações da Janela
    page.title = nome_app
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_100
    page.theme_mode = ft.ThemeMode.LIGHT 
    
    # Tenta carregar o Favicon (Ícone da janela/aba)
    if path_icon and os.path.exists(path_icon):
        page.window_icon = path_icon

    # --- ÁREA DE CONTEÚDO DINÂMICO ---
    area_conteudo = ft.Container(expand=True, padding=20)

    # --- FUNÇÃO DE NAVEGAÇÃO ---
    def navegar_para(e, nome_tela):
        # Atualiza visual do menu (marca o ativo)
        if isinstance(e, ft.ControlEvent):
            for item in menu_coluna.controls:
                if isinstance(item, ft.Container):
                    item.bgcolor = "transparent"
            e.control.bgcolor = ft.Colors.WHITE10
            e.control.update()
            menu_coluna.update()

        # Loading temporário
        area_conteudo.content = ft.Container(alignment=ft.alignment.center, content=ft.ProgressRing())
        page.update()

        # Roteamento
        if nome_tela == "Dashboard":
            area_conteudo.content = criar_dashboard_content()
        elif nome_tela == "Nova Venda":
            area_conteudo.content = ViewNovaVenda(page)
        elif nome_tela == "Clientes":
            area_conteudo.content = ViewClientes(page)
        elif nome_tela == "Produção":
            area_conteudo.content = ViewProducao(page)
        elif nome_tela == "Estoque":
            area_conteudo.content = ViewEstoque(page)
        elif nome_tela == "Financeiro":
            area_conteudo.content = ViewFinanceiro(page)
        elif nome_tela == "Configurações":
            area_conteudo.content = ViewConfiguracao(page)
        elif nome_tela == "Sair":
            tela_login()
            return

        page.update()

    # --- SIDEBAR (MENU LATERAL) ---
    menu_coluna = ft.Column(spacing=5) 

    def CriarSidebar():
        # Busca dados atualizados da empresa para o menu
        session_sb = get_session()
        emp_sb = session_sb.query(Empresa).first()
        nome_menu = emp_sb.nome_fantasia if emp_sb else "GestãoPro"
        logo_menu_path = emp_sb.caminho_logo if (emp_sb and emp_sb.caminho_logo) else ""
        session_sb.close()

        # Decide se mostra Logo (Personalizada) ou Ícone Padrão
        if logo_menu_path and os.path.exists(logo_menu_path):
            # Usa resolver_src para corrigir o caminho
            header_content = ft.Image(src=resolver_src(logo_menu_path), width=50, height=50, fit=ft.ImageFit.CONTAIN)
        else:
            header_content = ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, color=ft.Colors.BLUE_400, size=40)

        def item_menu(icone, texto, destino):
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icone, color=ft.Colors.WHITE70, size=20),
                    ft.Text(texto, color=ft.Colors.WHITE, size=14, weight="w500")
                ], spacing=15),
                padding=ft.padding.symmetric(horizontal=20, vertical=15),
                border_radius=8,
                ink=True,
                on_click=lambda e: navegar_para(e, destino)
            )

        menu_coluna.controls = [
            item_menu(ft.Icons.DASHBOARD, "Dashboard", "Dashboard"),
            item_menu(ft.Icons.SHOPPING_CART, "Nova Venda", "Nova Venda"),
            item_menu(ft.Icons.PEOPLE, "Clientes", "Clientes"),
            item_menu(ft.Icons.PRECISION_MANUFACTURING, "Produção", "Produção"),
            item_menu(ft.Icons.INVENTORY_2, "Estoque", "Estoque"),
            item_menu(ft.Icons.ATTACH_MONEY, "Financeiro", "Financeiro"),
            ft.Divider(color=ft.Colors.WHITE24),
            item_menu(ft.Icons.SETTINGS, "Configurações", "Configurações"),
            item_menu(ft.Icons.EXIT_TO_APP, "Sair", "Sair"),
        ]

        return ft.Container(
            width=260,
            bgcolor="#263238", 
            padding=10,
            content=ft.Column([
                ft.Container(
                    padding=20,
                    content=ft.Row([
                        header_content,
                        # Corta o nome se for muito grande para não quebrar o layout
                        ft.Text(nome_menu[:15], size=18, weight="bold", color=ft.Colors.WHITE)
                    ], alignment="center")
                ),
                ft.Divider(color=ft.Colors.WHITE24, height=1),
                ft.Container(height=20),
                menu_coluna
            ])
        )

    # --- DASHBOARD (LÓGICA COMPLETA) ---
    def criar_dashboard_content():
        session = get_session()
        try:
            total_os = session.query(OrdemServico).count()
            producao_os = session.query(OrdemServico).filter(OrdemServico.status.in_(['Impressão', 'Acabamento', 'Fila'])).count()
            concluidas_os = session.query(OrdemServico).filter_by(status='Entregue').count()
        except:
            total_os, producao_os, concluidas_os = 0, 0, 0
        session.close()

        def card_topo(titulo, valor, cor_texto, cor_bg_icone, icone):
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(icone, color=cor_texto, size=30),
                        bgcolor=cor_bg_icone, padding=15, border_radius=10
                    ),
                    ft.Column([
                        ft.Text(titulo, color=ft.Colors.GREY_600, size=12),
                        ft.Text(str(valor), size=28, weight="bold", color=ft.Colors.BLACK87)
                    ], spacing=2)
                ], alignment="start"),
                width=280, height=100, bgcolor="white",
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
                border_radius=12, padding=20
            )

        return ft.Container(
            padding=10,
            content=ft.Column([
                ft.Text("Visão Geral", size=30, weight="bold", color=ft.Colors.BLUE_GREY_900),
                ft.Divider(color="transparent"),
                ft.Row([
                    card_topo("Total Vendas", total_os, ft.Colors.BLUE_600, ft.Colors.BLUE_50, ft.Icons.RECEIPT_LONG),
                    card_topo("Em Produção", producao_os, ft.Colors.ORANGE_600, ft.Colors.ORANGE_50, ft.Icons.PRECISION_MANUFACTURING),
                    card_topo("Entregues", concluidas_os, ft.Colors.GREEN_600, ft.Colors.GREEN_50, ft.Icons.CHECK_CIRCLE),
                ], wrap=True, alignment="spaceBetween"),
                
                ft.Divider(height=40, color="transparent"),
                
                ft.Container(
                    height=300, bgcolor="white", border_radius=10, alignment=ft.alignment.center,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
                    content=ft.Column([
                        ft.Icon(ft.Icons.BAR_CHART, size=50, color=ft.Colors.GREY_300),
                        ft.Text("Gráficos de Faturamento (Em breve)", color=ft.Colors.GREY_400)
                    ], alignment="center", horizontal_alignment="center")
                )
            ])
        )

    # --- CARREGAMENTO DO SISTEMA ---
    def carregar_sistema_principal():
        page.clean()
        page.bgcolor = ft.Colors.GREY_100
        
        menu = CriarSidebar()
        area_conteudo.content = criar_dashboard_content()
        
        page.add(
            ft.Row(
                [menu, area_conteudo],
                expand=True, # IMPORTANTE: Ocupa toda a tela
                spacing=0
            )
        )
        # Marca Dashboard como ativo
        menu_coluna.controls[0].bgcolor = ft.Colors.WHITE10
        page.update()

    # --- TELA DE LOGIN (LAYOUT CORRIGIDO) ---
    def tela_login():
        page.clean()
        page.bgcolor = ft.Colors.WHITE
        
        # Busca dados atualizados para a tela de login
        session = get_session()
        empresa = session.query(Empresa).first()
        nome_fantasia_login = empresa.nome_fantasia if empresa else "GestãoPro"
        path_logo_login = empresa.caminho_logo if (empresa and empresa.caminho_logo) else ""
        session.close()

        txt_usuario = ft.TextField(label="Usuário", width=320, height=50, bgcolor="white", border_radius=8, prefix_icon=ft.Icons.PERSON, border_color=ft.Colors.GREY_400)
        txt_senha = ft.TextField(label="Senha", password=True, width=320, height=50, bgcolor="white", border_radius=8, prefix_icon=ft.Icons.LOCK, border_color=ft.Colors.GREY_400, can_reveal_password=True, on_submit=lambda e: realizar_login(e))
        lbl_erro = ft.Text("", color=ft.Colors.RED_600, size=13, weight="bold")

        def realizar_login(e):
            user = txt_usuario.value
            senha = txt_senha.value
            
            if not user or not senha:
                lbl_erro.value = "Preencha todos os campos."; page.update(); return

            senha_bytes = senha.encode('utf-8')
            hash_obj = hashlib.sha256(senha_bytes)
            senha_cripto = hash_obj.hexdigest()

            session = get_session()
            usuario_db = session.query(Usuario).filter_by(usuario=user, senha_hash=senha_cripto).first()
            session.close()

            if usuario_db:
                carregar_sistema_principal()
            else:
                lbl_erro.value = "Usuário ou senha incorretos."
                page.update()

        btn_entrar = ft.ElevatedButton(text="ENTRAR", width=320, height=50, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE_900, shape=ft.RoundedRectangleBorder(radius=8)), on_click=realizar_login)

        # Configuração da Logo ou Ícone Padrão
        if path_logo_login and os.path.exists(path_logo_login):
             # Usa resolver_src para corrigir o caminho
             imagem_capa = ft.Image(src=resolver_src(path_logo_login), width=200, fit=ft.ImageFit.CONTAIN)
        else:
             imagem_capa = ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, size=100, color="white")

        # Container Azul (Esquerda) - CORRIGIDO EXPAND E ALIGNMENT
        container_capa = ft.Container(
            expand=1, # Ocupa 50% ou proporcional
            bgcolor=ft.Colors.BLUE_900, 
            padding=40, 
            alignment=ft.alignment.center,
            content=ft.Column([
                imagem_capa,
                ft.Divider(height=20, color="transparent"),
                ft.Text(nome_fantasia_login, size=30, weight="bold", color="white", text_align="center"),
                ft.Text("Sistema de Gestão Integrada", size=16, color="white70", text_align="center"),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

        # Container Branco (Direita)
        container_form = ft.Container(
            expand=1, # Ocupa o restante
            bgcolor=ft.Colors.WHITE, 
            padding=40,
            alignment=ft.alignment.center, # Centraliza verticalmente o formulário
            content=ft.Column([
                ft.Text("Bem-vindo de volta", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900),
                ft.Text("Insira suas credenciais para acessar o painel.", size=14, color=ft.Colors.GREY_600),
                ft.Divider(height=40, color="transparent"),
                txt_usuario, ft.Divider(height=5, color="transparent"),
                txt_senha, ft.Divider(height=10, color="transparent"),
                lbl_erro, ft.Divider(height=20, color="transparent"),
                btn_entrar, ft.Divider(height=30, color="transparent"),
                ft.Row([ft.Text(f"Licenciado para: {nome_fantasia_login}", size=11, color=ft.Colors.GREY_400)], alignment="center")
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.START)
        )

        # Adiciona à página ocupando TUDO (expand=True na Row)
        page.add(ft.Row([container_capa, container_form], expand=True, spacing=0))

    tela_login()

if __name__ == "__main__":
    # assets_dir garante que o Flet ache a pasta 'assets'
    ft.app(target=main, view=ft.WEB_BROWSER, assets_dir="assets")