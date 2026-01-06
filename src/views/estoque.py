import flet as ft
from src.database.database import get_session, Material, MovimentacaoEstoque
from sqlalchemy.orm import joinedload
from datetime import datetime
from fpdf import FPDF
import os

def ViewEstoque(page):
    
    # --- VARIÁVEIS DE CONTROLE ---
    selecionados_para_imprimir = set()
    id_movimentando = ft.Ref[int]()
    id_editando = ft.Ref[int]()
    id_para_excluir = ft.Ref[int]() # Variável para guardar quem será excluído

    # --- REFIRÊNCIAS VISUAIS ---
    ref_qtd_total = ft.Text("0", size=24, weight="bold", color="white")
    ref_qtd_baixo = ft.Text("0", size=24, weight="bold", color="white")
    ref_qtd_zerado = ft.Text("0", size=24, weight="bold", color="white")

    # Campo de Busca (Filtro)
    txt_busca = ft.TextField(
        label="Buscar material...", 
        prefix_icon=ft.Icons.SEARCH,
        height=40,
        text_size=12,
        content_padding=10,
        border_radius=20,
        width=250,
        bgcolor="white",
        on_change=lambda e: carregar_dados()
    )

    # --- FUNÇÃO DE IMPRESSÃO ---
    def imprimir_relatorio(e):
        session = get_session()
        query = session.query(Material)
        if selecionados_para_imprimir:
            query = query.filter(Material.id.in_(selecionados_para_imprimir))
        
        if txt_busca.value:
            query = query.filter(Material.nome.ilike(f"%{txt_busca.value}%"))
            
        materiais = query.all()
        session.close()

        if not materiais:
            page.snack_bar = ft.SnackBar(ft.Text("Nenhum item para imprimir!"), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Relatorio de Estoque", ln=True, align="C")
            pdf.ln(10)
            
            pdf.set_font("Arial", "B", 12)
            pdf.cell(80, 10, "Produto", 1)
            pdf.cell(30, 10, "Qtd", 1)
            pdf.cell(30, 10, "Unid", 1)
            pdf.cell(40, 10, "Status", 1)
            pdf.ln()
            
            pdf.set_font("Arial", "", 12)
            for m in materiais:
                status = "OK"
                if m.quantidade <= 0: status = "ZERADO"
                elif m.quantidade <= m.estoque_minimo: status = "BAIXO"
                
                pdf.cell(80, 10, m.nome[:30], 1)
                pdf.cell(30, 10, str(m.quantidade), 1)
                pdf.cell(30, 10, m.unidade, 1)
                pdf.cell(40, 10, status, 1)
                pdf.ln()

            if not os.path.exists("relatorios"): os.makedirs("relatorios")
            nome_arq = f"relatorios/estoque_{int(datetime.now().timestamp())}.pdf"
            pdf.output(nome_arq)
            
            try: os.startfile(os.path.abspath(nome_arq))
            except: pass 
            
            page.snack_bar = ft.SnackBar(ft.Text("PDF Gerado!"), bgcolor=ft.colors.GREEN)
            page.snack_bar.open = True
            page.update()
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao gerar PDF: {err}"), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()

    # --- FUNÇÕES DE CRUD ---
    def salvar_novo_insumo(e):
        if not txt_nome.value:
            txt_nome.error_text = "Nome obrigatório"; txt_nome.update(); return
        
        try:
            qtd = float(txt_qtd.value) if txt_qtd.value else 0.0
            minimo = float(txt_min.value) if txt_min.value else 0.0
        except: return

        session = get_session()
        novo = Material(nome=txt_nome.value, unidade=dd_unidade.value, quantidade=qtd, estoque_minimo=minimo)
        session.add(novo); session.flush()
        
        if qtd > 0:
            session.add(MovimentacaoEstoque(material_id=novo.id, tipo="Entrada", quantidade=qtd, data=datetime.now(), observacao="Inicial"))
            
        session.commit(); session.close()
        page.close(dlg_novo); carregar_dados()

    def salvar_edicao(e):
        try:
            session = get_session()
            mat = session.query(Material).get(id_editando.current)
            if mat:
                mat.nome = txt_nome_edit.value
                mat.estoque_minimo = float(txt_min_edit.value)
                session.commit()
            session.close()
            page.close(dlg_editar); carregar_dados()
        except: pass

    # --- ENTRADA DE ESTOQUE (+) ---
    def salvar_entrada_estoque(e):
        try:
            qtd_add = float(txt_qtd_add.value)
            if qtd_add <= 0: raise ValueError
            
            session = get_session()
            mat = session.query(Material).get(id_movimentando.current)
            if mat:
                mat.quantidade += qtd_add
                session.add(MovimentacaoEstoque(material_id=mat.id, tipo="Entrada", quantidade=qtd_add, data=datetime.now(), observacao="Renovação Estoque"))
                session.commit()
            session.close()
            page.close(dlg_add); carregar_dados()
        except: 
            page.snack_bar = ft.SnackBar(ft.Text("Valor inválido!"), bgcolor=ft.colors.RED); page.snack_bar.open=True; page.update()

    # --- SAÍDA DE ESTOQUE (-) ---
    def salvar_saida_estoque(e):
        try:
            qtd_sai = float(txt_qtd_sai.value)
            if qtd_sai <= 0: raise ValueError
            
            session = get_session()
            mat = session.query(Material).get(id_movimentando.current)
            
            if mat:
                if mat.quantidade < qtd_sai:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Estoque insuficiente! Disponível: {mat.quantidade}"), bgcolor=ft.colors.RED)
                    page.snack_bar.open = True
                    page.update()
                    session.close()
                    return

                mat.quantidade -= qtd_sai
                session.add(MovimentacaoEstoque(material_id=mat.id, tipo="Saída", quantidade=qtd_sai, data=datetime.now(), observacao="Baixa / Uso"))
                session.commit()
                
            session.close()
            page.close(dlg_saida); carregar_dados()
        except:
             page.snack_bar = ft.SnackBar(ft.Text("Valor inválido!"), bgcolor=ft.colors.RED); page.snack_bar.open=True; page.update()

    # --- LÓGICA DE EXCLUSÃO SEGURA ---
    def confirmar_exclusao(mat_id):
        # 1. Guarda o ID na variável de referência
        id_para_excluir.current = mat_id
        # 2. Abre a janela de confirmação
        page.open(dlg_confirmar_exclusao)

    def efetivar_exclusao(e):
        try:
            mat_id = id_para_excluir.current
            if not mat_id: return

            session = get_session()
            mat = session.query(Material).get(mat_id)
            if mat:
                # Remove histórico primeiro (se não tiver cascade no banco)
                session.query(MovimentacaoEstoque).filter_by(material_id=mat_id).delete()
                # Remove o material
                session.delete(mat)
                session.commit()
            
            session.close()
            
            page.close(dlg_confirmar_exclusao) # Fecha o alerta
            
            page.snack_bar = ft.SnackBar(ft.Text("Insumo excluído com sucesso!"), bgcolor=ft.colors.GREEN)
            page.snack_bar.open = True
            page.update()
            
            carregar_dados() # Atualiza a tabela
            
        except Exception as err:
            print(err)
            page.snack_bar = ft.SnackBar(ft.Text("Erro ao excluir."), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()

    # --- MODAIS ---
    txt_nome = ft.TextField(label="Nome do Insumo", border_radius=8)
    dd_unidade = ft.Dropdown(label="Unidade", options=[ft.dropdown.Option("Unid"), ft.dropdown.Option("m²"), ft.dropdown.Option("Rolo"), ft.dropdown.Option("Litro")], value="Unid", border_radius=8)
    txt_qtd = ft.TextField(label="Qtd Inicial", value="0", keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
    txt_min = ft.TextField(label="Mínimo", value="5", keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
    dlg_novo = ft.AlertDialog(title=ft.Text("Novo Insumo"), content=ft.Column([txt_nome, dd_unidade, txt_qtd, txt_min], height=250), actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_novo)), ft.ElevatedButton("Salvar", on_click=salvar_novo_insumo)])

    txt_nome_edit = ft.TextField(label="Nome", border_radius=8)
    txt_min_edit = ft.TextField(label="Estoque Mínimo", keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
    dlg_editar = ft.AlertDialog(title=ft.Text("Editar Insumo"), content=ft.Column([txt_nome_edit, txt_min_edit], height=150), actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_editar)), ft.ElevatedButton("Salvar", on_click=salvar_edicao)])

    txt_qtd_add = ft.TextField(label="Qtd Entrada (+)", autofocus=True, keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
    dlg_add = ft.AlertDialog(title=ft.Text("Adicionar ao Estoque"), content=txt_qtd_add, actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_add)), ft.ElevatedButton("Confirmar Entrada", on_click=salvar_entrada_estoque)])

    txt_qtd_sai = ft.TextField(label="Qtd Saída (-)", autofocus=True, keyboard_type=ft.KeyboardType.NUMBER, border_radius=8)
    dlg_saida = ft.AlertDialog(title=ft.Text("Baixa no Estoque"), content=txt_qtd_sai, actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_saida)), ft.ElevatedButton("Confirmar Saída", bgcolor=ft.colors.RED, color="white", on_click=salvar_saida_estoque)])

    # Novo Modal de Confirmação de Exclusão
    dlg_confirmar_exclusao = ft.AlertDialog(
        title=ft.Text("Excluir Item?"),
        content=ft.Text("Tem certeza que deseja excluir este insumo?\nTodo o histórico de movimentação dele será perdido."),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_confirmar_exclusao)),
            ft.ElevatedButton("SIM, EXCLUIR", bgcolor="red", color="white", on_click=efetivar_exclusao)
        ],
        actions_alignment="end"
    )

    # --- TABELAS ---
    def toggle_selecao(e, mat_id):
        if e.control.value: selecionados_para_imprimir.add(mat_id)
        else: selecionados_para_imprimir.discard(mat_id)

    tabela_estoque = ft.DataTable(
        width=float('inf'),
        heading_row_color=ft.colors.GREY_100,
        heading_row_height=40,
        data_row_min_height=50,
        column_spacing=20,
        columns=[
            ft.DataColumn(ft.Text("Imp", weight="bold")),
            ft.DataColumn(ft.Text("Insumo / Material", weight="bold")), 
            ft.DataColumn(ft.Text("Quantidade", weight="bold")), 
            ft.DataColumn(ft.Text("Status", weight="bold")), 
            ft.DataColumn(ft.Text("Ações Rápidas", weight="bold"), numeric=True)
        ], 
        rows=[]
    )

    dd_filtro_hist = ft.Dropdown(label="Filtrar por Produto", width=250, text_size=12, height=40, content_padding=10, border_radius=8, options=[], on_change=lambda e: carregar_historico())
    
    tabela_historico = ft.DataTable(
        width=float('inf'),
        heading_row_color=ft.colors.GREY_100,
        heading_row_height=40,
        columns=[
            ft.DataColumn(ft.Text("Data/Hora", weight="bold")), 
            ft.DataColumn(ft.Text("Produto", weight="bold")), 
            ft.DataColumn(ft.Text("Movimento", weight="bold")), 
            ft.DataColumn(ft.Text("Qtd", weight="bold"))
        ], 
        rows=[]
    )

    def carregar_dados():
        tabela_estoque.rows.clear()
        selecionados_para_imprimir.clear() 
        
        session = get_session()
        
        query = session.query(Material)
        termo_busca = txt_busca.value
        if termo_busca:
            query = query.filter(Material.nome.ilike(f"%{termo_busca}%"))
            
        materiais = query.order_by(Material.nome).all()
        
        total_itens = len(materiais)
        total_baixo = 0
        total_zerado = 0

        opcoes = [ft.dropdown.Option("Todos")] + [ft.dropdown.Option(key=str(m.id), text=m.nome) for m in materiais]
        dd_filtro_hist.options = opcoes
        if not dd_filtro_hist.value: dd_filtro_hist.value = "Todos"
        
        for m in materiais:
            cor_status = ft.colors.GREEN_600
            bg_status = ft.colors.GREEN_50
            txt_status = "Estoque OK"
            
            if m.quantidade <= 0: 
                cor_status, bg_status, txt_status = ft.colors.RED_700, ft.colors.RED_50, "ZERADO"
                total_zerado += 1
            elif m.quantidade <= m.estoque_minimo: 
                cor_status, bg_status, txt_status = ft.colors.ORANGE_700, ft.colors.ORANGE_50, "BAIXO"
                total_baixo += 1

            badge_status = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CIRCLE, size=8, color=cor_status),
                    ft.Text(txt_status, color=cor_status, size=11, weight="bold")
                ], spacing=5, alignment="center"),
                bgcolor=bg_status, 
                padding=ft.padding.symmetric(horizontal=10, vertical=5), 
                border_radius=20,
                border=ft.border.all(1, cor_status),
                width=110,
                alignment=ft.alignment.center
            )

            tabela_estoque.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Checkbox(active_color=ft.colors.BLUE_600, on_change=lambda e, mid=m.id: toggle_selecao(e, mid))),
                ft.DataCell(ft.Text(m.nome, weight="w500", size=14, color=ft.colors.BLACK87)),
                ft.DataCell(ft.Text(f"{m.quantidade} {m.unidade}", size=13)),
                ft.DataCell(badge_status),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=ft.colors.GREEN_600, tooltip="Entrada", on_click=lambda e, mid=m.id: abrir_add(mid)),
                    ft.IconButton(ft.Icons.REMOVE_CIRCLE, icon_color=ft.colors.RED_600, tooltip="Saída", on_click=lambda e, mid=m.id: abrir_saida(mid)),
                    ft.Container(width=10),
                    ft.IconButton(ft.Icons.EDIT, icon_color=ft.colors.BLUE_GREY_400, tooltip="Editar", icon_size=20, on_click=lambda e, obj=m: abrir_editar(obj)),
                    
                    # --- AQUI ESTÁ O BOTÃO DE EXCLUIR QUE CHAMA O ALERT ---
                    ft.IconButton(ft.Icons.DELETE, icon_color=ft.colors.GREY_400, tooltip="Excluir", icon_size=20, on_click=lambda e, mid=m.id: confirmar_exclusao(mid))
                    # ------------------------------------------------------
                    
                ], alignment="end"))
            ]))
        
        session.close()
        
        ref_qtd_total.value = str(total_itens)
        ref_qtd_baixo.value = str(total_baixo)
        ref_qtd_zerado.value = str(total_zerado)

        try:
            tabela_estoque.update()
            dd_filtro_hist.update()
            ref_qtd_total.update()
            ref_qtd_baixo.update()
            ref_qtd_zerado.update()
        except AssertionError: pass
        
        carregar_historico()

    def carregar_historico():
        tabela_historico.rows.clear()
        session = get_session()
        query = session.query(MovimentacaoEstoque).options(joinedload(MovimentacaoEstoque.material)).order_by(MovimentacaoEstoque.id.desc())
        
        if dd_filtro_hist.value and dd_filtro_hist.value != "Todos":
            query = query.filter(MovimentacaoEstoque.material_id == int(dd_filtro_hist.value))
            
        historico = query.limit(50).all()
        session.close()

        for h in historico:
            cor = ft.colors.GREEN_700 if h.tipo == "Entrada" else ft.colors.RED_700
            icone = ft.Icons.ARROW_UPWARD if h.tipo == "Entrada" else ft.Icons.ARROW_DOWNWARD
            
            tabela_historico.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(h.data.strftime("%d/%m %H:%M"), size=12)),
                ft.DataCell(ft.Text(h.material.nome if h.material else "-", weight="bold", size=12)),
                ft.DataCell(ft.Row([
                    ft.Icon(icone, size=14, color=cor),
                    ft.Text(h.tipo, color=cor, weight="bold", size=12)
                ], spacing=5)),
                ft.DataCell(ft.Text(str(h.quantidade), size=12)),
            ]))
        try: tabela_historico.update()
        except AssertionError: pass

    def abrir_editar(mat):
        id_editando.current = mat.id
        txt_nome_edit.value = mat.nome
        txt_min_edit.value = str(mat.estoque_minimo)
        page.open(dlg_editar)

    def abrir_add(mat_id):
        id_movimentando.current = mat_id
        txt_qtd_add.value = ""
        page.open(dlg_add)

    def abrir_saida(mat_id):
        id_movimentando.current = mat_id
        txt_qtd_sai.value = ""
        page.open(dlg_saida)

    carregar_dados()

    # --- CARD DE RESUMO COM DEGRADÊ ---
    def card_resumo_gradiente(titulo, ref_valor, icone, cores_gradiente):
        return ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=cores_gradiente
            ),
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icone, color="white", size=30), 
                    padding=10, 
                    bgcolor=ft.colors.WHITE24, 
                    border_radius=50
                ),
                ft.Column([
                    ft.Text(titulo, size=12, color="white", weight="w500"),
                    ref_valor
                ], spacing=2)
            ], alignment="center"),
            padding=15,
            border_radius=12,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
            width=220
        )

    # --- LAYOUT PRINCIPAL ---
    return ft.Container(
        padding=30, 
        bgcolor="#f8f9fa",
        expand=True, 
        content=ft.Column([
            
            # CABEÇALHO E CARDS
            ft.Row([
                ft.Column([
                    ft.Text("Controle de Estoque", size=28, weight="bold", color=ft.colors.BLUE_GREY_900),
                    ft.Text("Gerencie seus materiais e insumos", size=14, color=ft.colors.GREY_500),
                ]),
                ft.Row([
                    card_resumo_gradiente("Total de Itens", ref_qtd_total, ft.Icons.INVENTORY_2, [ft.colors.BLUE_700, ft.colors.BLUE_400]),
                    card_resumo_gradiente("Estoque Baixo", ref_qtd_baixo, ft.Icons.WARNING_ROUNDED, [ft.colors.ORANGE_700, ft.colors.ORANGE_400]),
                    card_resumo_gradiente("Itens Zerados", ref_qtd_zerado, ft.Icons.BLOCK, [ft.colors.RED_700, ft.colors.RED_400]),
                ], spacing=15)
            ], alignment="spaceBetween"),

            ft.Divider(height=20, color="transparent"),

            # ÁREA DE AÇÕES + FILTRO
            ft.Row([
                ft.Row([
                    txt_busca,
                    ft.ElevatedButton("Novo Insumo", icon=ft.Icons.ADD, bgcolor=ft.colors.BLUE_600, color="white", height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=lambda e: page.open(dlg_novo)),
                    ft.OutlinedButton("Imprimir Seleção", icon=ft.Icons.PRINT, height=40, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)), on_click=imprimir_relatorio),
                ], spacing=10),
            ]),

            ft.Divider(height=10, color="transparent"),

            # CARD TABELA PRINCIPAL
            ft.Container(
                bgcolor="white",
                padding=10,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.BLACK12),
                content=ft.Column([
                    tabela_estoque
                ], scroll=ft.ScrollMode.AUTO),
                height=400 
            ),

            ft.Divider(height=30, color="transparent"),

            # ÁREA DO HISTÓRICO
            ft.Container(
                bgcolor="white",
                padding=20,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12),
                content=ft.Column([
                    ft.Row([
                        ft.Row([
                            ft.Icon(ft.Icons.HISTORY, color=ft.colors.BLUE_GREY_700),
                            ft.Text("Histórico de Movimentações", size=18, weight="bold", color=ft.colors.BLUE_GREY_800),
                        ]),
                        dd_filtro_hist
                    ], alignment="spaceBetween"),
                    ft.Divider(),
                    ft.Container(content=tabela_historico, height=250)
                ])
            ),
        ], scroll=ft.ScrollMode.AUTO)
    )