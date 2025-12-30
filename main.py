import flet as ft
from src.database.database import get_session, Usuario, Configuracao, OrdemServico
from src.ui import Sidebar
# Importação das Views (Telas)
from src.views.vendas import ViewNovaVenda 
from src.views.producao import ViewProducao
from src.views.estoque import ViewEstoque
from src.views.financeiro import ViewFinanceiro
from src.views.clientes import ViewClientes
import sys
import os
import warnings

# Silencia avisos de versão para limpar o terminal
warnings.filterwarnings("ignore")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def main(page: ft.Page):
    # --- CONFIGURAÇÃO DA JANELA ---
    page.title = "Gestão Gráfica Pro"
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0
    page.theme_mode = ft.ThemeMode.LIGHT 

    # --- ÁREA DE CONTEÚDO DINÂMICO ---
    # Aqui é onde as telas (Dashboard, Vendas, etc) serão carregadas
    area_conteudo = ft.Container(expand=True, bgcolor=ft.colors.GREY_100)

    # --- FUNÇÃO DE NAVEGAÇÃO CENTRAL ---
    def navegar_para(nome_tela):
        # Limpa o conteúdo atual para carregar o novo
        area_conteudo.content = None
        
        if nome_tela == "Dashboard":
            area_conteudo.content = criar_dashboard_content()
        elif nome_tela == "Nova Venda":
            area_conteudo.content = ViewNovaVenda(page)
        elif nome_tela == "Clientes":        # <--- Adicionado Clientes
            area_conteudo.content = ViewClientes(page)
        elif nome_tela == "Produção":
            area_conteudo.content = ViewProducao(page)
        elif nome_tela == "Estoque":    # <--- Adicionado Estoque
            area_conteudo.content = ViewEstoque(page)
        elif nome_tela == "Financeiro":       # <--- Adicionado Financeiro
            area_conteudo.content = ViewFinanceiro(page)
        elif nome_tela == "Sair":
            tela_login() # Volta para o login
            return

        area_conteudo.update()

    # --- CONTEÚDO DA DASHBOARD (Componente) ---
    def criar_dashboard_content():
        session = get_session()
        # Consultas reais ao banco
        total_os = session.query(OrdemServico).count()
        producao_os = session.query(OrdemServico).filter(OrdemServico.status.in_(['Impressão', 'Acabamento', 'Fila', 'Rodando'])).count()
        concluidas_os = session.query(OrdemServico).filter_by(status='Entregue').count()
        session.close()

        def card_topo(titulo, valor, cor_texto, cor_borda):
            return ft.Container(
                content=ft.Column([
                        ft.Text(titulo, color=ft.colors.GREY_600),
                        ft.Text(str(valor), size=40, weight="bold", color=cor_texto)
                    ], alignment="center", horizontal_alignment="center"),
                width=250, height=120, bgcolor="white",
                border=ft.border.all(1, color=cor_borda), border_radius=10, padding=20, alignment=ft.alignment.center
            )

        return ft.Container(
            padding=30,
            content=ft.Column([
                    ft.Text("Dashboard Gerencial", size=30, weight="bold", color=ft.colors.BLUE_GREY_900),
                    ft.Divider(color="transparent"),
                    ft.Row([
                            card_topo("Total Cadastrado", total_os, ft.colors.BLUE_600, ft.colors.BLUE_200),
                            card_topo("Em Produção", producao_os, ft.colors.ORANGE_600, ft.colors.ORANGE_200),
                            card_topo("Concluídas", concluidas_os, ft.colors.GREEN_600, ft.colors.GREEN_200),
                        ], alignment="spaceBetween"),
                    ft.Divider(color="transparent"),
                    ft.Container(
                        height=300, bgcolor="white", border_radius=10, alignment=ft.alignment.center,
                        content=ft.Text("Gráficos de Faturamento (Em breve)", color=ft.colors.GREY_400)
                    )
                ])
        )

    # --- FUNÇÃO: CARREGAR O SISTEMA PÓS-LOGIN ---
    def carregar_sistema_principal():
        page.clean() # Limpa a tela de login
        
        # Cria o Menu Lateral
        menu = Sidebar(page)
        
        # Carrega a Dashboard como tela inicial
        area_conteudo.content = criar_dashboard_content()
        
        # Monta o Layout Principal (Menu na Esquerda + Conteúdo na Direita)
        page.add(
            ft.Row(
                [
                    menu, 
                    area_conteudo 
                ],
                expand=True,
                spacing=0
            )
        )
        
        # --- VINCULAÇÃO DOS BOTÕES DO MENU ---
        # A estrutura é: menu -> content (Column) -> controls (Lista de botões)
        # Índices baseados na ordem do arquivo ui.py:
        coluna_botoes = menu.content.controls
        
        # [0]=Header, [1]=Divider
        # [2]=Dashboard
        coluna_botoes[2].on_click = lambda e: navegar_para("Dashboard")
        
        # [3]=Nova Venda
        coluna_botoes[3].on_click = lambda e: navegar_para("Nova Venda")
        
        # [4]=Clientes
        coluna_botoes[4].on_click = lambda e: navegar_para("Clientes")
        # [5]=Produção
        coluna_botoes[5].on_click = lambda e: navegar_para("Produção")
        
        # [6]=Estoque
        coluna_botoes[6].on_click = lambda e: navegar_para("Estoque")

        # [7]=Financeiro
        coluna_botoes[7].on_click = lambda e: navegar_para("Financeiro")
        
        # [-1]=Botão Sair (O último da lista)
        coluna_botoes[-1].on_click = lambda e: navegar_para("Sair")
        
        page.update()

    # --- TELA DE LOGIN (Visual Profissional) ---
    def tela_login():
        page.clean()
        page.bgcolor = ft.colors.WHITE
        
        # Carrega dados da empresa (Logo)
        session = get_session()
        nome_empresa = "Carregando..."
        logo_src = ""
        try:
            config = session.query(Configuracao).first()
            if not config:
                config = Configuracao(nome_fantasia="Sua Gráfica Aqui")
                session.add(config)
                session.commit()
            nome_empresa = config.nome_fantasia
            logo_src = config.caminho_logo if config.caminho_logo and os.path.exists(config.caminho_logo) else ""
        except: pass
        finally: session.close()

        # Elementos do Formulário
        txt_usuario = ft.TextField(
            label="Usuário", width=320, height=50, 
            bgcolor="white", border_radius=8, 
            prefix_icon=ft.icons.PERSON, 
            border_color=ft.colors.GREY_400
        )
        
        txt_senha = ft.TextField(
            label="Senha", password=True, width=320, height=50, 
            bgcolor="white", border_radius=8, 
            prefix_icon=ft.icons.LOCK, 
            border_color=ft.colors.GREY_400,
            can_reveal_password=True
        )
        
        lbl_erro = ft.Text("", color=ft.colors.RED_600, size=13, weight="bold")

        def realizar_login(e):
            user = txt_usuario.value
            senha = txt_senha.value
            
            # Validação simples
            if not user or not senha:
                lbl_erro.value = "Preencha todos os campos."
                page.update()
                return

            session = get_session()
            usuario_db = session.query(Usuario).filter_by(usuario=user, senha_hash=senha).first()
            session.close()

            if usuario_db:
                # Login Sucesso -> Vai para o Sistema
                carregar_sistema_principal()
            else:
                lbl_erro.value = "Usuário ou senha incorretos."
                page.update()

        btn_entrar = ft.ElevatedButton(
            text="ACESSAR SISTEMA", width=320, height=50,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE, 
                bgcolor=ft.colors.BLUE_900, 
                shape=ft.RoundedRectangleBorder(radius=8)
            ),
            on_click=realizar_login
        )

        # --- MONTAGEM DO LAYOUT DE LOGIN (DIVIDIDO) ---
        
        # Coluna da Direita (Formulário)
        container_form = ft.Container(
            expand=1.2,
            bgcolor=ft.colors.WHITE,
            padding=40,
            content=ft.Column(
                [
                    ft.Text("Bem-vindo de volta", size=28, weight="bold", color=ft.colors.BLUE_GREY_900),
                    ft.Text("Insira suas credenciais para acessar o painel.", size=14, color=ft.colors.GREY_600),
                    ft.Divider(height=40, color="transparent"),
                    
                    ft.Text("Usuário", size=12, weight="bold", color=ft.colors.GREY_700),
                    txt_usuario,
                    ft.Divider(height=5, color="transparent"),
                    
                    ft.Text("Senha", size=12, weight="bold", color=ft.colors.GREY_700),
                    txt_senha,
                    
                    ft.Divider(height=10, color="transparent"),
                    lbl_erro,
                    ft.Divider(height=20, color="transparent"),
                    
                    btn_entrar,
                    
                    ft.Divider(height=30, color="transparent"),
                    ft.Row([ft.Text(f"Licenciado para: {nome_empresa}", size=11, color=ft.colors.GREY_400)], alignment="center")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START
            )
        )

        # Coluna da Esquerda (Capa Azul)
        container_capa = ft.Container(
            expand=1,
            bgcolor=ft.colors.BLUE_900,
            padding=40,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.Icon(ft.icons.DASHBOARD_CUSTOMIZE, size=100, color="white") if not logo_src else ft.Image(src=logo_src, width=200),
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
    ft.app(target=main, view=ft.WEB_BROWSER)