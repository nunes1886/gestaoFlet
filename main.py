import flet as ft
from src.database.database import get_session, Usuario, Configuracao, OrdemServico
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

# Silencia avisos de versão
warnings.filterwarnings("ignore")

def main(page: ft.Page):
    # --- CONFIGURAÇÃO DA JANELA ---
    page.title = "Gestão Gráfica Pro"
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_100
    page.theme_mode = ft.ThemeMode.LIGHT 

    # --- ÁREA DE CONTEÚDO DINÂMICO ---
    area_conteudo = ft.Container(expand=True, padding=20)

    # --- FUNÇÃO DE NAVEGAÇÃO ---
    def navegar_para(e, nome_tela):
        # Limpa visual dos botões do menu (remove destaque)
        if isinstance(e, ft.ControlEvent):
            for item in menu_coluna.controls:
                if isinstance(item, ft.Container):
                    item.bgcolor = "transparent"
            # Destaca o clicado
            e.control.bgcolor = ft.Colors.WHITE10
            e.control.update()
            menu_coluna.update()

        # Troca o conteúdo
        area_conteudo.content = ft.Container(alignment=ft.alignment.center, content=ft.ProgressRing())
        page.update()

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
            area_conteudo.content = ViewFinanceiro(page) # Descomente quando criar o arquivo
            # area_conteudo.content = ft.Text("Módulo Financeiro em Desenvolvimento...", size=20)
        elif nome_tela == "Sair":
            tela_login()
            return

        page.update()

    # --- COMPONENTE MENU LATERAL (SIDEBAR) ---
    menu_coluna = ft.Column(spacing=5) # Referência para atualizar os botões

    def CriarSidebar():
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

        # Popula a coluna de botões
        menu_coluna.controls = [
            item_menu(ft.Icons.DASHBOARD, "Dashboard", "Dashboard"),
            item_menu(ft.Icons.SHOPPING_CART, "Nova Venda", "Nova Venda"),
            item_menu(ft.Icons.PEOPLE, "Clientes", "Clientes"),
            item_menu(ft.Icons.PRECISION_MANUFACTURING, "Produção", "Produção"),
            item_menu(ft.Icons.INVENTORY_2, "Estoque", "Estoque"),
            item_menu(ft.Icons.ATTACH_MONEY, "Financeiro", "Financeiro"),
            ft.Divider(color=ft.Colors.WHITE24),
            item_menu(ft.Icons.EXIT_TO_APP, "Sair", "Sair"),
        ]

        return ft.Container(
            width=260,
            bgcolor="#263238", # Cor escura do menu
            padding=10,
            content=ft.Column([
                # Cabeçalho do Menu
                ft.Container(
                    padding=20,
                    content=ft.Row([
                        ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, color=ft.Colors.BLUE_400),
                        ft.Text("GestãoPro", size=22, weight="bold", color=ft.Colors.WHITE)
                    ])
                ),
                ft.Divider(color=ft.Colors.WHITE24, height=1),
                ft.Container(height=20),
                menu_coluna
            ])
        )

    # --- CONTEÚDO DA DASHBOARD ---
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
                    content=ft.Text("Gráficos de Faturamento (Em breve)", color=ft.Colors.GREY_400)
                )
            ])
        )

    # --- FUNÇÃO: CARREGAR O SISTEMA PÓS-LOGIN ---
    def carregar_sistema_principal():
        page.clean()
        page.bgcolor = ft.Colors.GREY_100
        
        menu = CriarSidebar()
        
        # Carrega Dashboard Inicialmente
        area_conteudo.content = criar_dashboard_content()
        
        page.add(
            ft.Row(
                [menu, area_conteudo],
                expand=True,
                spacing=0
            )
        )
        
        # Simula clique visual no primeiro botão
        menu_coluna.controls[0].bgcolor = ft.Colors.WHITE10
        page.update()

    # --- TELA DE LOGIN (LAYOUT SPLIT - Azul/Branco) ---
    def tela_login():
        page.clean()
        page.bgcolor = ft.Colors.WHITE
        
        # Elementos do Formulário
        txt_usuario = ft.TextField(
            label="Usuário", width=320, height=50, 
            bgcolor="white", border_radius=8, 
            prefix_icon=ft.Icons.PERSON, 
            border_color=ft.Colors.GREY_400
        )
        
        txt_senha = ft.TextField(
            label="Senha", password=True, width=320, height=50, 
            bgcolor="white", border_radius=8, 
            prefix_icon=ft.Icons.LOCK, 
            border_color=ft.Colors.GREY_400,
            can_reveal_password=True,
            on_submit=lambda e: realizar_login(e)
        )
        
        lbl_erro = ft.Text("", color=ft.Colors.RED_600, size=13, weight="bold")

        def realizar_login(e):
            user = txt_usuario.value
            senha = txt_senha.value
            
            if not user or not senha:
                lbl_erro.value = "Preencha todos os campos."
                page.update()
                return

            # Criptografia para conferir com o banco
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

        btn_entrar = ft.ElevatedButton(
            text="ACESSAR SISTEMA", width=320, height=50,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE, 
                bgcolor=ft.Colors.BLUE_900, 
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=realizar_login
        )

        # Coluna da Direita (Formulário)
        container_form = ft.Container(
            expand=1.2,
            bgcolor=ft.Colors.WHITE,
            padding=40,
            content=ft.Column(
                [
                    ft.Text("Bem-vindo de volta", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900),
                    ft.Text("Insira suas credenciais para acessar o painel.", size=14, color=ft.Colors.GREY_600),
                    ft.Divider(height=40, color="transparent"),
                    
                    ft.Text("Usuário", size=12, weight="bold", color=ft.Colors.GREY_700),
                    txt_usuario,
                    ft.Divider(height=5, color="transparent"),
                    
                    ft.Text("Senha", size=12, weight="bold", color=ft.Colors.GREY_700),
                    txt_senha,
                    
                    ft.Divider(height=10, color="transparent"),
                    lbl_erro,
                    ft.Divider(height=20, color="transparent"),
                    
                    btn_entrar,
                    
                    ft.Divider(height=30, color="transparent"),
                    ft.Row([ft.Text("TechSolutions © 2026", size=11, color=ft.Colors.GREY_400)], alignment="center")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START
            )
        )

        # Coluna da Esquerda (Capa Azul)
        container_capa = ft.Container(
            expand=1,
            bgcolor=ft.Colors.BLUE_900,
            padding=40,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, size=100, color="white"),
                    ft.Divider(height=20, color="transparent"),
                    ft.Text("GestãoPro", size=30, weight="bold", color="white"),
                    ft.Text("Controle total para Comunicação Visual", size=16, color="white70", text_align="center"),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        page.add(
            ft.Row(
                [container_capa, container_form],
                expand=True,
                spacing=0
            )
        )

    # Inicia na tela de login
    tela_login()

if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER, assets_dir="assets")