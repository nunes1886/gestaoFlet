import flet as ft
from src.database.database import get_session, Usuario, Empresa, OrdemServico
from fpdf import FPDF
import hashlib
import sys
import os
import warnings
import datetime
from datetime import date, timedelta # Imports essenciais para datas

# VIEWS
from src.views.criacao import ViewCriacao
from src.views.vendas import ViewNovaVenda 
from src.views.producao import ViewProducao
from src.views.estoque import ViewEstoque
from src.views.financeiro import ViewFinanceiro 
from src.views.clientes import ViewClientes
from src.views.configuracao import ViewConfiguracao
from src.views.relatorio_dia import ViewRelatorioDia
from src.views.funcionarios import ViewFuncionarios
from src.views.arquivo_morto import ViewArquivoMorto

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
        elif nome_tela == "Criação": area_conteudo.content = ViewCriacao(page)
        elif nome_tela == "Produção": area_conteudo.content = ViewProducao(page)
        elif nome_tela == "Estoque": area_conteudo.content = ViewEstoque(page)
        elif nome_tela == "Financeiro": area_conteudo.content = ViewFinanceiro(page)
        elif nome_tela == "Relatorios": area_conteudo.content = ViewRelatorioDia(page)
        elif nome_tela == "Equipe": area_conteudo.content = ViewFuncionarios(page)
        elif nome_tela == "Configurações": area_conteudo.content = ViewConfiguracao(page)
        elif nome_tela == "Arquivo": area_conteudo.content = ViewArquivoMorto(page)

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
        if perms.get("designer") or perms.get("admin"):
            itens.append(item_menu(ft.Icons.BRUSH, "Criação", "Criação"))
        itens.append(item_menu(ft.Icons.PRECISION_MANUFACTURING, "Produção", "Produção"))
        
        if perms.get("estoque"): itens.append(item_menu(ft.Icons.INVENTORY_2, "Estoque", "Estoque"))
        if perms.get("ver_dash"):
            itens.append(item_menu(ft.Icons.ATTACH_MONEY, "Financeiro", "Financeiro"))
            itens.append(item_menu(ft.Icons.BAR_CHART, "Relatórios", "Relatorios"))
        if perms.get("admin"):
            itens.append(item_menu(ft.Icons.SUPERVISED_USER_CIRCLE, "Equipe", "Equipe"))
            itens.append(ft.Divider(color=ft.Colors.WHITE24))
            itens.append(item_menu(ft.Icons.ARCHIVE, "Arquivo Geral", "Arquivo"))
            itens.append(item_menu(ft.Icons.SETTINGS, "Configurações", "Configurações"))
        itens.append(item_menu(ft.Icons.EXIT_TO_APP, "Sair", "Sair"))

        menu_coluna.controls = itens

        return ft.Container(width=260, bgcolor="#263238", padding=10, content=ft.Column([
                ft.Container(padding=20, content=ft.Column([header_content, ft.Container(height=10), ft.Text(nome_menu[:20], size=18, weight="bold", color=ft.Colors.WHITE, text_align="center")], horizontal_alignment="center")),
                ft.Divider(color=ft.Colors.WHITE24, height=1), ft.Container(height=20), menu_coluna
            ], scroll=ft.ScrollMode.AUTO))

    # --- DASHBOARD REAL (COM CALENDÁRIO) ---
    def criar_dashboard_content():
        # Limpa o overlay para não acumular datepickers antigos
        page.overlay.clear()
        
        # Datas Iniciais (Padrão: Começo do mês até hoje)
        hoje = datetime.date.today()
        primeiro_dia_mes = datetime.date(hoje.year, hoje.month, 1)
        
        # Variáveis para guardar a seleção (começam com o padrão)
        data_ini_selecionada = ft.Ref[datetime.date]()
        data_fim_selecionada = ft.Ref[datetime.date]()
        data_ini_selecionada.current = primeiro_dia_mes
        data_fim_selecionada.current = hoje

        # Referencias visuais
        ref_total_vendas = ft.Text("0", size=26, weight="bold", color="white")
        ref_producao = ft.Text("0", size=26, weight="bold", color="white")
        ref_entregues = ft.Text("0", size=26, weight="bold", color="white")
        
        # Definição do Gráfico
        ref_grafico = ft.BarChart(
            bar_groups=[],
            border=ft.border.all(1, ft.Colors.GREY_200),
            left_axis=ft.ChartAxis(labels_size=40, title=ft.Text("Qtd", size=10), title_size=20),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(value=0, label=ft.Text("Seg")),
                    ft.ChartAxisLabel(value=1, label=ft.Text("Ter")),
                    ft.ChartAxisLabel(value=2, label=ft.Text("Qua")),
                    ft.ChartAxisLabel(value=3, label=ft.Text("Qui")),
                    ft.ChartAxisLabel(value=4, label=ft.Text("Sex")),
                    ft.ChartAxisLabel(value=5, label=ft.Text("Sab")),
                ],
                labels_size=30,
            ),
            horizontal_grid_lines=ft.ChartGridLines(color=ft.Colors.GREY_100, width=1, dash_pattern=[3, 3]),
            tooltip_bgcolor=ft.Colors.BLUE_GREY_50,
            max_y=10, 
            interactive=True,
            expand=True,
        )

        def atualizar_dashboard(e=None):
            try:
                d_ini = data_ini_selecionada.current
                d_fim = data_fim_selecionada.current
                
                dt_ini = datetime.datetime.combine(d_ini, datetime.time.min)
                dt_fim = datetime.datetime.combine(d_fim, datetime.time.max)

                session = get_session()
                
                # Query Base filtrada
                query_base = session.query(OrdemServico).filter(OrdemServico.data_criacao >= dt_ini, OrdemServico.data_criacao <= dt_fim)
                
                # 1. Totais
                total = query_base.count()
                prod = query_base.filter(OrdemServico.status.in_(['Impressão', 'Acabamento', 'Fila'])).count()
                entregues = query_base.filter_by(status='Entregue').count()
                
                ref_total_vendas.value = str(total)
                ref_producao.value = str(prod)
                ref_entregues.value = str(entregues)

                # 2. Gráfico
                vendas_periodo = query_base.all()
                contagem_dias = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
                
                for v in vendas_periodo:
                    wd = v.data_criacao.weekday()
                    if wd in contagem_dias:
                        contagem_dias[wd] += 1
                
                novos_grupos = []
                cores = [ft.Colors.BLUE_400, ft.Colors.BLUE_400, ft.Colors.BLUE_400, ft.Colors.BLUE_400, ft.Colors.BLUE_400, ft.Colors.ORANGE_400]
                
                for i in range(6):
                    val = contagem_dias.get(i, 0)
                    novos_grupos.append(
                        ft.BarChartGroup(x=i, bar_rods=[ft.BarChartRod(from_y=0, to_y=val, color=cores[i], width=20, border_radius=5)])
                    )
                
                ref_grafico.bar_groups = novos_grupos
                ref_grafico.max_y = max(contagem_dias.values()) + 5 if contagem_dias else 10
                
                session.close()
                page.update()

            except Exception as ex:
                print(f"Erro Dash: {ex}")

        # --- LÓGICA DO DATEPICKER (CALENDÁRIO) ---
        def ao_mudar_data_inicio(e):
            if e.control.value:
                data_ini_selecionada.current = e.control.value.date()
                btn_data_inicio.text = e.control.value.strftime("%d/%m/%Y")
                btn_data_inicio.update()

        def ao_mudar_data_final(e):
            if e.control.value:
                data_fim_selecionada.current = e.control.value.date()
                btn_data_final.text = e.control.value.strftime("%d/%m/%Y")
                btn_data_final.update()
        
        # Componentes DatePicker
        date_picker_inicio = ft.DatePicker(
            first_date=datetime.datetime(2023, 1, 1),
            last_date=datetime.datetime(2030, 12, 31),
            on_change=ao_mudar_data_inicio,
            confirm_text="Confirmar",
            cancel_text="Cancelar",
            help_text="Selecione data inicial"
        )

        date_picker_final = ft.DatePicker(
            first_date=datetime.datetime(2023, 1, 1),
            last_date=datetime.datetime(2030, 12, 31),
            on_change=ao_mudar_data_final,
            confirm_text="Confirmar",
            cancel_text="Cancelar",
            help_text="Selecione data final"
        )
        
        page.overlay.append(date_picker_inicio)
        page.overlay.append(date_picker_final)

        # Botões que abrem o calendário
        btn_data_inicio = ft.ElevatedButton(
            text=primeiro_dia_mes.strftime("%d/%m/%Y"),
            icon=ft.Icons.CALENDAR_MONTH,
            style=ft.ButtonStyle(bgcolor="white", color="black"),
            on_click=lambda _: date_picker_inicio.pick_date()
        )

        btn_data_final = ft.ElevatedButton(
            text=hoje.strftime("%d/%m/%Y"),
            icon=ft.Icons.CALENDAR_MONTH,
            style=ft.ButtonStyle(bgcolor="white", color="black"),
            on_click=lambda _: date_picker_final.pick_date()
        )
        # ------------------------------------------

        # Componente Card
        def card_topo_colorido_ref(titulo, ref_valor, icone, cores_gradiente):
            return ft.Container(
                content=ft.Row([
                    ft.Container(content=ft.Icon(icone, color="white", size=30), padding=10, bgcolor=ft.Colors.WHITE24, border_radius=10),
                    ft.Column([
                        ft.Text(titulo, color="white", size=12, weight="w500"),
                        ref_valor
                    ], spacing=2)
                ], alignment="start", vertical_alignment="center"),
                width=280, height=100,
                gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=cores_gradiente),
                border_radius=15, padding=20, shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12)
            )

        grafico_container = ft.Container(
            height=350, bgcolor="white", border_radius=15, padding=20, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
            content=ft.Column([
                ft.Text("Vendas por Dia da Semana (No Período)", size=18, weight="bold", color=ft.Colors.BLUE_GREY_800),
                ft.Divider(color="transparent", height=20),
                ref_grafico
            ])
        )

        btn_filtrar = ft.ElevatedButton("Aplicar Filtro", icon=ft.Icons.FILTER_LIST, on_click=atualizar_dashboard, bgcolor=ft.Colors.BLUE_800, color="white", height=40)

        # Função Gerar PDF
        def gerar_pdf(e):
            atualizar_dashboard()
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                
                pdf.set_font("Arial", "B", 16)
                pdf.cell(200, 10, txt="Relatorio de Dashboard - GestaoPro", ln=1, align="C")
                pdf.ln(5)
                
                d_ini_str = data_ini_selecionada.current.strftime("%d/%m/%Y")
                d_fim_str = data_fim_selecionada.current.strftime("%d/%m/%Y")
                
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"Periodo: {d_ini_str} ate {d_fim_str}", ln=1, align="C")
                pdf.ln(10)
                
                pdf.set_font("Arial", "B", 12)
                pdf.cell(200, 10, txt="Resumo Geral:", ln=1)
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"- Total de Vendas: {ref_total_vendas.value}", ln=1)
                pdf.cell(200, 10, txt=f"- Em Producao: {ref_producao.value}", ln=1)
                pdf.cell(200, 10, txt=f"- Entregues: {ref_entregues.value}", ln=1)
                
                nome_arquivo = f"Relatorio_Dash_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                pdf.output(nome_arquivo)
                
                e.page.snack_bar = ft.SnackBar(ft.Text(f"PDF Gerado: {nome_arquivo}"), bgcolor="green")
                e.page.snack_bar.open = True
                e.page.update()
            except Exception as ex:
                e.page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao gerar PDF: {str(ex)}"), bgcolor="red")
                e.page.snack_bar.open = True
                e.page.update()

        layout = ft.Container(
            padding=10,
            content=ft.Column([
                ft.Row([
                    ft.Text("Visão Geral", size=30, weight="bold", color=ft.Colors.BLUE_GREY_900),
                    ft.Row([
                        ft.Text("De:", weight="bold"), btn_data_inicio,
                        ft.Text("Até:", weight="bold"), btn_data_final,
                        btn_filtrar,
                        ft.IconButton(icon=ft.Icons.PRINT, tooltip="Imprimir PDF", on_click=gerar_pdf, icon_color=ft.Colors.BLUE_GREY_700)
                    ], vertical_alignment="center")
                ], alignment="spaceBetween"),
                
                ft.Divider(color="transparent", height=10),
                
                ft.Row([
                    card_topo_colorido_ref("Total Vendas", ref_total_vendas, ft.Icons.RECEIPT_LONG, [ft.Colors.BLUE_700, ft.Colors.BLUE_400]),
                    card_topo_colorido_ref("Em Produção", ref_producao, ft.Icons.PRECISION_MANUFACTURING, [ft.Colors.ORANGE_700, ft.Colors.ORANGE_400]),
                    card_topo_colorido_ref("Entregues", ref_entregues, ft.Icons.CHECK_CIRCLE, [ft.Colors.GREEN_700, ft.Colors.GREEN_400]),
                ], wrap=True, alignment="spaceBetween"),
                
                ft.Divider(height=30, color="transparent"),
                grafico_container
            ], scroll=ft.ScrollMode.AUTO)
        )
        
        atualizar_dashboard()
        return layout

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