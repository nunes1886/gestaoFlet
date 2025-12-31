import flet as ft
from src.database.database import get_session, Estoque, MovimentacaoEstoque
from sqlalchemy.orm import joinedload
from datetime import datetime
from fpdf import FPDF
import os

def ViewEstoque(page):

    # --- VARIÁVEIS DE ESTADO ---
    txt_nome = ft.TextField(label="Nome do Insumo (Ex: Rolo Lona 440g)")
    dd_unidade = ft.Dropdown(
        label="Unidade",
        options=[
            ft.dropdown.Option("Rolo"),
            ft.dropdown.Option("Unidade"),
            ft.dropdown.Option("Caixa"),
            ft.dropdown.Option("Litro"),
            ft.dropdown.Option("Pacote"),
            ft.dropdown.Option("Metro"),
        ]
    )
    txt_qtd = ft.TextField(label="Quantidade Inicial", value="0", keyboard_type=ft.KeyboardType.NUMBER)
    txt_minimo = ft.TextField(label="Estoque Mínimo (Alerta)", value="2", keyboard_type=ft.KeyboardType.NUMBER)

    id_baixa = ft.Ref[int]()
    txt_qtd_baixa = ft.TextField(label="Qtd Retirada", value="1", text_align="center")

    dd_filtro = ft.Dropdown(
        label="Filtrar Histórico por Material",
        options=[ft.dropdown.Option("Todos")],
        value="Todos",
        expand=True,
        on_change=lambda e: carregar_historico()
    )

    # --- FUNÇÃO: GERAR PDF (IMPRIMIR) ---
    def gerar_relatorio_pdf(e):
        try:
            session = get_session()
            insumos = session.query(Estoque).all()
            session.close()

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=16)
            
            # Título
            pdf.cell(0, 10, text="Relatório de Estoque - GestãoPro", new_x="LMARGIN", new_y="NEXT", align='C')
            pdf.set_font("Helvetica", size=10)
            pdf.cell(0, 10, text=f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", new_x="LMARGIN", new_y="NEXT", align='C')
            pdf.ln(10) # Espaço

            # Cabeçalho da Tabela
            pdf.set_font("Helvetica", style='B', size=12)
            pdf.cell(80, 10, text="Material", border=1)
            pdf.cell(30, 10, text="Unidade", border=1, align='C')
            pdf.cell(40, 10, text="Saldo Atual", border=1, align='C')
            pdf.cell(40, 10, text="Status", border=1, align='C')
            pdf.ln()

            # Dados
            pdf.set_font("Helvetica", size=12)
            for item in insumos:
                status = "OK"
                if item.quantidade_atual <= 0: status = "ZERADO"
                elif item.quantidade_atual <= item.minimo_alerta: status = "BAIXO"
                
                # Tratamento simples para caracteres (FPDF básico pode ter problema com acentos)
                # O ideal é usar fontes TTF, mas para simplificar vamos usar padrão
                nome_item = item.nome[:35] # Corta se for muito longo
                
                pdf.cell(80, 10, text=nome_item, border=1)
                pdf.cell(30, 10, text=item.unidade, border=1, align='C')
                pdf.cell(40, 10, text=str(item.quantidade_atual), border=1, align='C')
                pdf.cell(40, 10, text=status, border=1, align='C')
                pdf.ln()

            # Salvar e Abrir
            nome_arquivo = "relatorio_estoque.pdf"
            pdf.output(nome_arquivo)
            
            # Abre o arquivo automaticamente no Windows
            os.startfile(nome_arquivo)
            
            page.snack_bar = ft.SnackBar(ft.Text("Relatório gerado com sucesso!"), bgcolor="green")
            page.snack_bar.open = True
            page.update()

        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao gerar PDF: {err}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    # --- FUNÇÕES DE CRUD (Igual anterior) ---
    def fechar_dialogos(e):
        dialogo_novo.open = False
        dialogo_baixa.open = False
        page.update()

    def salvar_novo_insumo(e):
        if not txt_nome.value: return
        try:
            session = get_session()
            novo = Estoque(nome=txt_nome.value, unidade=dd_unidade.value, quantidade_atual=float(txt_qtd.value), minimo_alerta=float(txt_minimo.value))
            session.add(novo); session.commit()
            mov = MovimentacaoEstoque(estoque_id=novo.id, tipo="Entrada Inicial", quantidade=float(txt_qtd.value), data=datetime.now())
            session.add(mov); session.commit(); session.close()
            page.snack_bar = ft.SnackBar(ft.Text("Insumo cadastrado!"), bgcolor="green"); page.snack_bar.open = True
            dialogo_novo.open = False; carregar_dados_gerais()
        except: pass

    def confirmar_baixa(e):
        if not id_baixa.current: return
        try:
            qtd = float(txt_qtd_baixa.value)
            session = get_session()
            insumo = session.query(Estoque).get(id_baixa.current)
            if insumo:
                insumo.quantidade_atual -= qtd
                mov = MovimentacaoEstoque(estoque_id=insumo.id, tipo="Baixa Produção", quantidade=qtd, data=datetime.now())
                session.add(mov); session.commit()
                page.snack_bar = ft.SnackBar(ft.Text(f"Baixa registrada!"), bgcolor="orange"); page.snack_bar.open = True
            session.close(); dialogo_baixa.open = False; carregar_dados_gerais()
        except: pass

    # --- MODAIS ---
    dialogo_novo = ft.AlertDialog(title=ft.Text("Novo Insumo"), content=ft.Column([txt_nome, dd_unidade, txt_qtd, txt_minimo], height=250), actions=[ft.TextButton("Cancelar", on_click=fechar_dialogos), ft.ElevatedButton("Salvar", on_click=salvar_novo_insumo, bgcolor="blue", color="white")])
    dialogo_baixa = ft.AlertDialog(title=ft.Text("Retirar Material"), content=ft.Column([ft.Text("Quanto saiu do estoque?"), txt_qtd_baixa], height=100), actions=[ft.TextButton("Cancelar", on_click=fechar_dialogos), ft.ElevatedButton("CONFIRMAR", on_click=confirmar_baixa, bgcolor="red", color="white")])

    def abrir_novo(e): txt_nome.value = ""; txt_qtd.value = "0"; page.dialog = dialogo_novo; dialogo_novo.open = True; page.update()
    def abrir_baixa(e, insumo_id): id_baixa.current = insumo_id; txt_qtd_baixa.value = "1"; page.dialog = dialogo_baixa; dialogo_baixa.open = True; page.update()

    # --- TABELAS ---
    tabela_estoque = ft.DataTable(
        width=float('inf'),
        columns=[ft.DataColumn(ft.Text("Insumo")), ft.DataColumn(ft.Text("Saldo")), ft.DataColumn(ft.Text("Status")), ft.DataColumn(ft.Text("Ação"))], rows=[]
    )
    tabela_historico = ft.DataTable(
        width=float('inf'),
        columns=[ft.DataColumn(ft.Text("Data/Hora")), ft.DataColumn(ft.Text("Material")), ft.DataColumn(ft.Text("Movimento")), ft.DataColumn(ft.Text("Qtd"))], rows=[]
    )

    # --- CARREGAR DADOS ---
    def carregar_dados_gerais():
        tabela_estoque.rows.clear()
        session = get_session()
        insumos = session.query(Estoque).all()
        
        opcoes = [ft.dropdown.Option("Todos")]
        for i in insumos: opcoes.append(ft.dropdown.Option(key=str(i.id), text=i.nome))
        dd_filtro.options = opcoes

        for i in insumos:
            cor_status, texto_status = (ft.colors.RED_600, "ZERADO") if i.quantidade_atual <= 0 else (ft.colors.ORANGE_600, "BAIXO") if i.quantidade_atual <= i.minimo_alerta else (ft.colors.GREEN_600, "OK")
            tabela_estoque.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(i.nome, weight="bold")),
                ft.DataCell(ft.Text(f"{i.quantidade_atual} {i.unidade}")),
                ft.DataCell(ft.Container(ft.Text(texto_status, color="white", size=10), bgcolor=cor_status, padding=5, border_radius=5)),
                ft.DataCell(ft.ElevatedButton("- Retirar", style=ft.ButtonStyle(bgcolor=ft.colors.RED_400, color="white"), height=30, on_click=lambda e, id=i.id: abrir_baixa(e, id))),
            ]))
        session.close()
        carregar_historico()
        page.update()

    def carregar_historico():
        tabela_historico.rows.clear()
        session = get_session()
        query = session.query(MovimentacaoEstoque).options(joinedload(MovimentacaoEstoque.estoque))
        if dd_filtro.value and dd_filtro.value != "Todos": query = query.filter(MovimentacaoEstoque.estoque_id == int(dd_filtro.value))
        movs = query.order_by(MovimentacaoEstoque.data.desc()).all()
        session.close()

        for m in movs:
            cor_tipo = ft.colors.GREEN_700 if "Entrada" in m.tipo else ft.colors.RED_700
            tabela_historico.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(m.data.strftime("%d/%m %H:%M"), size=12)),
                ft.DataCell(ft.Text(m.estoque.nome if m.estoque else "-", weight="bold")),
                ft.DataCell(ft.Text(m.tipo, color=cor_tipo)),
                ft.DataCell(ft.Text(f"{m.quantidade}")),
            ]))
        page.update()

    carregar_dados_gerais()

    # --- LAYOUT FINAL ---
    return ft.Container(
        padding=30, expand=True, bgcolor=ft.colors.GREY_100,
        content=ft.Column([
            ft.Row([
                ft.Row([
                    ft.Text("Controle de Estoque", size=25, weight="bold", color=ft.colors.BLUE_GREY_900),
                    # BOTÃO DE IMPRIMIR AQUI
                    ft.IconButton(icon=ft.icons.PRINT, icon_color=ft.colors.BLUE_GREY_700, tooltip="Imprimir Relatório", on_click=gerar_relatorio_pdf)
                ]),
                ft.ElevatedButton("Novo Insumo", icon=ft.icons.ADD, bgcolor="blue", color="white", on_click=abrir_novo)
            ], alignment="spaceBetween"),
            
            ft.Container(bgcolor="white", padding=10, border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK12), content=tabela_estoque),
            ft.Divider(height=40, color="grey"),
            ft.Row([ft.Icon(ft.icons.HISTORY, color=ft.colors.BLUE_GREY_700), ft.Text("Histórico", size=20, weight="bold", color=ft.colors.BLUE_GREY_700)]),
            ft.Container(bgcolor="white", padding=10, border_radius=5, width=400, content=dd_filtro),
            ft.Container(bgcolor="white", padding=10, border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK12), content=tabela_historico),
        ], scroll="auto")
    )