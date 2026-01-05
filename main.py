import flet as ft
from src.database.database import get_session, Usuario, Empresa, OrdemServico
from fpdf import FPDF
import hashlib
import sys
import os
import warnings
import datetime
# Não precisamos mais do random

# VIEWS
from src.views.vendas import ViewNovaVenda 
from src.views.producao import ViewProducao
from src.views.estoque import ViewEstoque
from src.views.financeiro import ViewFinanceiro 
from src.views.clientes import ViewClientes
from src.views.configuracao import ViewConfiguracao
from src.views.relatorio_dia import ViewRelatorioDia
from src.views.funcionarios import ViewFuncionarios

warnings.filterwarnings("ignore")

def main(page: ft.Page):
    
    # --- CONFIGURAÇÕES DE ASSETS ---
    CAMINHO_LOGO_PADRAO = "logo.png"
    CAMINHO_FAVICON_PADRAO = "favicon.png" 

    def get_logo_path():
        if os.path.exists(f"assets/{CAMINHO_LOGO_PADRAO}"): return CAMINHO_LOGO_PADRAO
        return ""

    # --- SETUP INICIAL ---
    session = get_session()
    empresa = session.query(Empresa).first()
    nome_app = empresa.nome_fantasia if empresa else "GestãoPro"
    session.close()

    page.title = nome_app
    page.window_width = 1200
    page.window_height = 800
    page.padding = 0
    page.bgcolor = ft.Colors.GREY_100
    page.theme_mode = ft.ThemeMode.LIGHT 
    page.window_prevent_close = False 
    
    if os.path.exists(f"assets/{CAMINHO_FAVICON_PADRAO}"):
        page.window_icon = f"assets/{CAMINHO_FAVICON_PADRAO}"

    area_conteudo = ft.Container(expand=True, padding=20)

    # --- NAVEGAÇÃO SEGURA ---
    def navegar_para(e, nome_tela):
        perms = page.session.get("permissoes") or {}
        
        # Regras de Bloqueio
        if nome_tela in ["Financeiro", "Relatorios", "Dashboard"] and not perms.get("ver_dash"):
            page.snack_bar = ft.SnackBar(ft.Text("Acesso Negado: Financeiro restrito."), bgcolor="red"); page.snack_bar.open=True; page.update(); return
        
        if nome_tela in ["Nova Venda", "Clientes"] and not perms.get("cadastrar"):
             page.snack_bar = ft.SnackBar(ft.Text("Acesso Negado: Você não pode Cadastrar."), bgcolor="red"); page.snack_bar.open=True; page.update(); return

        if nome_tela == "Estoque" and not perms.get("estoque"):
             page.snack_bar = ft.SnackBar(ft.Text("Acesso Negado: Sem permissão de Estoque."), bgcolor="red"); page.snack_bar.open=True; page.update(); return

        if nome_tela in ["Equipe", "Configurações"] and not perms.get("admin"):
             page.snack_bar = ft.SnackBar(ft.Text("Acesso Negado: Apenas Administradores."), bgcolor="red"); page.snack_bar.open=True; page.update(); return

        if nome_tela == "Sair":
            tela_login()
            return

        # Visual do Menu
        if isinstance(e, ft.ControlEvent):
            for item in menu_coluna.controls:
                if isinstance(item, ft.Container): item.bgcolor = "transparent"
            e.control.bgcolor = ft.Colors.WHITE10
            e.control.update(); menu_coluna.update()

        area_conteudo.content = ft.Container(alignment=ft.alignment.center, content=ft.ProgressRing())
        page.update()

        # Roteamento
        if nome_tela == "Dashboard": area_conteudo.content = criar_dashboard_content()
        elif nome_tela == "Nova Venda": area_conteudo.content = ViewNovaVenda(page)
        elif nome_tela == "Clientes": area_conteudo.content = ViewClientes(page)
        elif nome_tela == "Produção": area_conteudo.content = ViewProducao(page)
        elif nome_tela == "Estoque": area_conteudo.content = ViewEstoque(page)
        elif nome_tela == "Financeiro": area_conteudo.content = ViewFinanceiro(page)
        elif nome_tela == "Relatorios": area_conteudo.content = ViewRelatorioDia(page)
        elif nome_tela == "Equipe": area_conteudo.content = ViewFuncionarios(page)
        elif nome_tela == "Configurações": area_conteudo.content = ViewConfiguracao(page)

        page.update()

    menu_coluna = ft.Column(spacing=5) 

    def CriarSidebar():
        session_sb = get_session()
        empresa_sb = session_sb.query(Empresa).first() 
        nome_menu = empresa_sb.nome_fantasia if empresa_sb else "GestãoPro"
        session_sb.close()
        
        perms = page.session.get("permissoes") or {}

        logo_path = get_logo_path()
        if logo_path: header_content = ft.Image(src=logo_path, width=80, height=80, fit=ft.ImageFit.CONTAIN)
        else: header_content = ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, color=ft.Colors.BLUE_400, size=40)

        def item_menu(icone, texto, destino):
            return ft.Container(content=ft.Row([ft.Icon(icone, color=ft.Colors.WHITE70, size=20), ft.Text(texto, color=ft.Colors.WHITE, size=14, weight="w500")], spacing=15), padding=ft.padding.symmetric(horizontal=20, vertical=15), border_radius=8, ink=True, on_click=lambda e: navegar_para(e, destino))

        itens = []
        if perms.get("ver_dash"): itens.append(item_menu(ft.Icons.DASHBOARD, "Dashboard", "Dashboard"))
        if perms.get("cadastrar"):
            itens.append(item_menu(ft.Icons.SHOPPING_CART, "Nova Venda", "Nova Venda"))
            itens.append(item_menu(ft.Icons.PEOPLE, "Clientes", "Clientes"))
        itens.append(item_menu(ft.Icons.PRECISION_MANUFACTURING, "Produção", "Produção"))
        if perms.get("estoque"): itens.append(item_menu(ft.Icons.INVENTORY_2, "Estoque", "Estoque"))
        if perms.get("ver_dash"):
            itens.append(item_menu(ft.Icons.ATTACH_MONEY, "Financeiro", "Financeiro"))
            itens.append(item_menu(ft.Icons.BAR_CHART, "Relatórios", "Relatorios"))
        if perms.get("admin"):
            itens.append(item_menu(ft.Icons.SUPERVISED_USER_CIRCLE, "Equipe", "Equipe"))
            itens.append(ft.Divider(color=ft.Colors.WHITE24))
            itens.append(item_menu(ft.Icons.SETTINGS, "Configurações", "Configurações"))
        itens.append(item_menu(ft.Icons.EXIT_TO_APP, "Sair", "Sair"))

        menu_coluna.controls = itens

        return ft.Container(width=260, bgcolor="#263238", padding=10, content=ft.Column([
                ft.Container(padding=20, content=ft.Column([header_content, ft.Container(height=10), ft.Text(nome_menu[:20], size=18, weight="bold", color=ft.Colors.WHITE, text_align="center")], horizontal_alignment="center")),
                ft.Divider(color=ft.Colors.WHITE24, height=1), ft.Container(height=20), menu_coluna
            ], scroll=ft.ScrollMode.AUTO))

    # --- DASHBOARD REAL ---
    def criar_dashboard_content():
        session = get_session()
        try:
            # 1. Totais Gerais
            total_os = session.query(OrdemServico).count()
            producao_os = session.query(OrdemServico).filter(OrdemServico.status.in_(['Impressão', 'Acabamento', 'Fila'])).count()
            concluidas_os = session.query(OrdemServico).filter_by(status='Entregue').count()
            
            # 2. Lógica do Gráfico Semanal (REAL)
            hoje = datetime.datetime.now()
            # Encontrar a segunda-feira da semana atual (0 = Segunda, 6 = Domingo)
            inicio_semana = hoje - datetime.timedelta(days=hoje.weekday())
            # Zerar as horas para pegar desde o inicio do dia
            inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Buscar OS criadas desta segunda-feira em diante
            vendas_semana = session.query(OrdemServico).filter(OrdemServico.data_criacao >= inicio_semana).all()
            
            # Dicionário para contar: 0:Segunda, 1:Terça ... 4:Sexta
            contagem_dias = {0:0, 1:0, 2:0, 3:0, 4:0} 
            
            for venda in vendas_semana:
                dia_semana = venda.data_criacao.weekday()
                if dia_semana in contagem_dias:
                    contagem_dias[dia_semana] += 1
            
            # Criar as barras do gráfico
            dados_grafico = [
                ft.BarChartGroup(x=0, bar_rods=[ft.BarChartRod(from_y=0, to_y=contagem_dias[0], color=ft.Colors.BLUE_400, width=20, border_radius=5)]),
                ft.BarChartGroup(x=1, bar_rods=[ft.BarChartRod(from_y=0, to_y=contagem_dias[1], color=ft.Colors.BLUE_400, width=20, border_radius=5)]),
                ft.BarChartGroup(x=2, bar_rods=[ft.BarChartRod(from_y=0, to_y=contagem_dias[2], color=ft.Colors.BLUE_400, width=20, border_radius=5)]),
                ft.BarChartGroup(x=3, bar_rods=[ft.BarChartRod(from_y=0, to_y=contagem_dias[3], color=ft.Colors.BLUE_400, width=20, border_radius=5)]),
                ft.BarChartGroup(x=4, bar_rods=[ft.BarChartRod(from_y=0, to_y=contagem_dias[4], color=ft.Colors.BLUE_400, width=20, border_radius=5)]),
            ]
            
            # Definir altura máxima do gráfico (para não ficar achatado se tiver poucos dados)
            max_y = max(contagem_dias.values()) + 5 if contagem_dias else 10
            
        except Exception as e:
            print(f"Erro Dash: {e}")
            total_os, producao_os, concluidas_os = 0, 0, 0
            dados_grafico = []
            max_y = 10
        finally:
            session.close()

        # Função Gerar PDF
        def gerar_pdf(e):
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                
                pdf.set_font("Arial", "B", 16)
                pdf.cell(200, 10, txt="Relatorio de Dashboard - GestaoPro", ln=1, align="C")
                pdf.ln(10)
                
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"Data: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
                pdf.ln(10)
                
                pdf.set_font("Arial", "B", 12)
                pdf.cell(200, 10, txt="Resumo Geral:", ln=1)
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"- Total de Vendas: {total_os}", ln=1)
                pdf.cell(200, 10, txt=f"- Em Producao: {producao_os}", ln=1)
                pdf.cell(200, 10, txt=f"- Entregues: {concluidas_os}", ln=1)
                
                nome_arquivo = f"Relatorio_Dash_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                pdf.output(nome_arquivo)
                
                e.page.snack_bar = ft.SnackBar(ft.Text(f"PDF Gerado: {nome_arquivo}"), bgcolor="green")
                e.page.snack_bar.open = True
                e.page.update()
            except Exception as ex:
                e.page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao gerar PDF: {str(ex)}"), bgcolor="red")
                e.page.snack_bar.open = True
                e.page.update()

        # Componente Card Colorido
        def card_topo_colorido(titulo, valor, icone, cores_gradiente):
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
                        ft.Text(str(valor), size=26, weight="bold", color="white")
                    ], spacing=2)
                ], alignment="start", vertical_alignment="center"),
                width=280,
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

        # Container do Gráfico
        grafico_container = ft.Container(
            height=350,
            bgcolor="white",
            border_radius=15,
            padding=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
            content=ft.Column([
                ft.Text("Vendas desta Semana (Seg-Sex)", size=18, weight="bold", color=ft.Colors.BLUE_GREY_800),
                ft.Divider(color="transparent", height=20),
                ft.BarChart(
                    bar_groups=dados_grafico,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("Qtd", size=10), title_size=20),
                    bottom_axis=ft.ChartAxis(
                        labels=[
                            ft.ChartAxisLabel(value=0, label=ft.Text("Seg")),
                            ft.ChartAxisLabel(value=1, label=ft.Text("Ter")),
                            ft.ChartAxisLabel(value=2, label=ft.Text("Qua")),
                            ft.ChartAxisLabel(value=3, label=ft.Text("Qui")),
                            ft.ChartAxisLabel(value=4, label=ft.Text("Sex")),
                        ],
                        labels_size=30,
                    ),
                    horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.GREY_100, width=1, dash_pattern=[3, 3]),
                    tooltip_bgcolor=ft.Colors.BLUE_GREY_50,
                    max_y=max_y, 
                    interactive=True,
                    expand=True,
                )
            ])
        )

        return ft.Container(
            padding=10,
            content=ft.Column([
                ft.Row([
                    ft.Text("Visão Geral", size=30, weight="bold", color=ft.Colors.BLUE_GREY_900),
                    ft.ElevatedButton("Imprimir Relatório", icon=ft.Icons.PRINT, bgcolor=ft.Colors.BLUE_GREY_700, color="white", on_click=gerar_pdf)
                ], alignment="spaceBetween"),
                
                ft.Divider(color="transparent", height=10),
                
                ft.Row([
                    card_topo_colorido("Total Vendas", total_os, ft.Icons.RECEIPT_LONG, [ft.Colors.BLUE_700, ft.Colors.BLUE_400]),
                    card_topo_colorido("Em Produção", producao_os, ft.Icons.PRECISION_MANUFACTURING, [ft.Colors.ORANGE_700, ft.Colors.ORANGE_400]),
                    card_topo_colorido("Entregues", concluidas_os, ft.Icons.CHECK_CIRCLE, [ft.Colors.GREEN_700, ft.Colors.GREEN_400]),
                ], wrap=True, alignment="spaceBetween"),
                
                ft.Divider(height=30, color="transparent"),
                grafico_container
            ], scroll=ft.ScrollMode.AUTO)
        )

    def carregar_sistema_principal():
        page.clean(); page.bgcolor = ft.Colors.GREY_100
        
        perms = page.session.get("permissoes") or {}
        menu = CriarSidebar()
        
        if perms.get("ver_dash"):
            area_conteudo.content = criar_dashboard_content()
            if len(menu_coluna.controls) > 0: menu_coluna.controls[0].bgcolor = ft.Colors.WHITE10
        else:
            area_conteudo.content = ViewProducao(page)

        page.add(ft.Row([menu, area_conteudo], expand=True, spacing=0))
        page.update()

    def tela_login():
        page.overlay.clear() 
        page.dialog = None   
        page.clean()         
        page.update()        
        
        page.bgcolor = ft.Colors.WHITE
        
        session = get_session(); empresa = session.query(Empresa).first()
        nome_login = empresa.nome_fantasia if empresa else "GestãoPro"
        session.close()

        txt_usuario = ft.TextField(label="Usuário", width=320, height=50, bgcolor="white", border_radius=8, prefix_icon=ft.Icons.PERSON)
        txt_senha = ft.TextField(label="Senha", password=True, width=320, height=50, bgcolor="white", border_radius=8, prefix_icon=ft.Icons.LOCK, can_reveal_password=True, on_submit=lambda e: realizar_login(e))
        lbl_erro = ft.Text("", color="red", weight="bold")

        def realizar_login(e):
            if not txt_usuario.value or not txt_senha.value: lbl_erro.value = "Preencha tudo."; page.update(); return
            hash_login = hashlib.sha256(txt_senha.value.encode()).hexdigest()
            session = get_session()
            user_db = session.query(Usuario).filter_by(usuario=txt_usuario.value, senha_hash=hash_login).first()
            
            if user_db:
                page.session.set("user_id", user_db.id)
                page.session.set("permissoes", {
                    "admin": user_db.is_admin,
                    "cadastrar": user_db.can_register,
                    "ver_dash": user_db.view_dashboard,
                    "designer": user_db.is_designer,
                    "excluir": user_db.can_delete,
                    "estoque": user_db.manage_stock
                })
                session.close()
                carregar_sistema_principal()
            else:
                session.close()
                lbl_erro.value = "Dados incorretos."; page.update()

        btn_entrar = ft.ElevatedButton(text="ENTRAR", width=320, height=50, style=ft.ButtonStyle(color="white", bgcolor=ft.Colors.BLUE_900, shape=ft.RoundedRectangleBorder(radius=8)), on_click=realizar_login)
        logo_path = get_logo_path()
        if logo_path: img_login = ft.Image(src=logo_path, width=200, fit=ft.ImageFit.CONTAIN)
        else: img_login = ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, size=100, color="white")

        container_capa = ft.Container(expand=1, bgcolor=ft.Colors.BLUE_900, padding=40, alignment=ft.alignment.center, content=ft.Column([img_login, ft.Divider(height=20, color="transparent"), ft.Text(nome_login, size=30, weight="bold", color="white", text_align="center"), ft.Text("Sistema Integrado", size=16, color="white70")], alignment="center", horizontal_alignment="center"))
        container_form = ft.Container(expand=1, bgcolor="white", padding=40, alignment=ft.alignment.center, content=ft.Column([ft.Text("Bem-vindo", size=28, weight="bold", color=ft.Colors.BLUE_GREY_900), ft.Divider(height=40, color="transparent"), txt_usuario, ft.Divider(height=10, color="transparent"), txt_senha, ft.Divider(height=10, color="transparent"), lbl_erro, ft.Divider(height=20, color="transparent"), btn_entrar], alignment="center", horizontal_alignment="center"))
        page.add(ft.Row([container_capa, container_form], expand=True, spacing=0))

    tela_login()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets", view=ft.WEB_BROWSER)