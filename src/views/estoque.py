import flet as ft
from src.database.database import get_session, Material, MovimentacaoEstoque
from sqlalchemy.orm import joinedload
from datetime import datetime
from fpdf import FPDF
import os

def ViewEstoque(page):
    
    # --- VARIÁVEIS DE CONTROLE ---
    selecionados_para_imprimir = set()
    id_movimentando = ft.Ref[int]() # ID do material selecionado para Add/Remover/Editar
    id_editando = ft.Ref[int]()

    # --- FUNÇÃO DE IMPRESSÃO (PDF) ---
    def imprimir_relatorio(e):
        session = get_session()
        query = session.query(Material)
        if selecionados_para_imprimir:
            query = query.filter(Material.id.in_(selecionados_para_imprimir))
        materiais = query.all()
        session.close()

        if not materiais:
            page.snack_bar = ft.SnackBar(ft.Text("Nenhum item para imprimir!"), bgcolor=ft.Colors.RED)
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
            
            page.snack_bar = ft.SnackBar(ft.Text("PDF Gerado!"), bgcolor=ft.Colors.GREEN)
            page.snack_bar.open = True
            page.update()
        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao gerar PDF: {err}"), bgcolor=ft.Colors.RED)
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
            page.snack_bar = ft.SnackBar(ft.Text("Valor inválido!"), bgcolor=ft.Colors.RED); page.snack_bar.open=True; page.update()

    # --- SAÍDA DE ESTOQUE (-) ---
    def salvar_saida_estoque(e):
        try:
            qtd_sai = float(txt_qtd_sai.value)
            if qtd_sai <= 0: raise ValueError
            
            session = get_session()
            mat = session.query(Material).get(id_movimentando.current)
            
            if mat:
                if mat.quantidade < qtd_sai:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Estoque insuficiente! Disponível: {mat.quantidade}"), bgcolor=ft.Colors.RED)
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
             page.snack_bar = ft.SnackBar(ft.Text("Valor inválido!"), bgcolor=ft.Colors.RED); page.snack_bar.open=True; page.update()


    def excluir_insumo(e, mat_id):
        session = get_session()
        mat = session.query(Material).get(mat_id)
        if mat:
            session.query(MovimentacaoEstoque).filter_by(material_id=mat_id).delete()
            session.delete(mat); session.commit()
        session.close(); carregar_dados()

    # --- MODAIS ---
    # Novo
    txt_nome = ft.TextField(label="Nome do Insumo")
    dd_unidade = ft.Dropdown(label="Unidade", options=[ft.dropdown.Option("Unid"), ft.dropdown.Option("m²"), ft.dropdown.Option("Rolo"), ft.dropdown.Option("Litro")], value="Unid")
    txt_qtd = ft.TextField(label="Qtd Inicial", value="0", keyboard_type=ft.KeyboardType.NUMBER)
    txt_min = ft.TextField(label="Mínimo", value="5", keyboard_type=ft.KeyboardType.NUMBER)
    dlg_novo = ft.AlertDialog(title=ft.Text("Novo Insumo"), content=ft.Column([txt_nome, dd_unidade, txt_qtd, txt_min], height=250), actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_novo)), ft.ElevatedButton("Salvar", on_click=salvar_novo_insumo)])

    # Editar
    txt_nome_edit = ft.TextField(label="Nome")
    txt_min_edit = ft.TextField(label="Estoque Mínimo", keyboard_type=ft.KeyboardType.NUMBER)
    dlg_editar = ft.AlertDialog(title=ft.Text("Editar Insumo"), content=ft.Column([txt_nome_edit, txt_min_edit], height=150), actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_editar)), ft.ElevatedButton("Salvar", on_click=salvar_edicao)])

    # Adicionar (+)
    txt_qtd_add = ft.TextField(label="Qtd Entrada (+)", autofocus=True, keyboard_type=ft.KeyboardType.NUMBER)
    dlg_add = ft.AlertDialog(title=ft.Text("Adicionar ao Estoque"), content=txt_qtd_add, actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_add)), ft.ElevatedButton("Confirmar Entrada", on_click=salvar_entrada_estoque)])

    # Retirar (-)
    txt_qtd_sai = ft.TextField(label="Qtd Saída (-)", autofocus=True, keyboard_type=ft.KeyboardType.NUMBER)
    dlg_saida = ft.AlertDialog(title=ft.Text("Baixa no Estoque"), content=txt_qtd_sai, actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_saida)), ft.ElevatedButton("Confirmar Saída", bgcolor=ft.Colors.RED, color="white", on_click=salvar_saida_estoque)])

    # --- TABELA ---
    def toggle_selecao(e, mat_id):
        if e.control.value: selecionados_para_imprimir.add(mat_id)
        else: selecionados_para_imprimir.discard(mat_id)

    tabela_estoque = ft.DataTable(
        heading_row_color=ft.Colors.GREY_200,
        columns=[
            ft.DataColumn(ft.Text("Imp")),
            ft.DataColumn(ft.Text("Insumo")), 
            ft.DataColumn(ft.Text("Qtd")), 
            ft.DataColumn(ft.Text("Status")), 
            ft.DataColumn(ft.Text("Ações"))
        ], 
        rows=[]
    )

    dd_filtro_hist = ft.Dropdown(label="Filtrar Histórico", width=300, options=[], on_change=lambda e: carregar_historico())
    tabela_historico = ft.DataTable(
        heading_row_color=ft.Colors.GREY_200,
        columns=[ft.DataColumn(ft.Text("Data")), ft.DataColumn(ft.Text("Produto")), ft.DataColumn(ft.Text("Movimento")), ft.DataColumn(ft.Text("Qtd"))], 
        rows=[]
    )

    def carregar_dados():
        tabela_estoque.rows.clear()
        selecionados_para_imprimir.clear() 
        
        session = get_session()
        materiais = session.query(Material).all()
        
        opcoes = [ft.dropdown.Option("Todos")] + [ft.dropdown.Option(key=str(m.id), text=m.nome) for m in materiais]
        dd_filtro_hist.options = opcoes
        if not dd_filtro_hist.value: dd_filtro_hist.value = "Todos"
        
        for m in materiais:
            cor_status = ft.Colors.GREEN
            txt_status = "OK"
            if m.quantidade <= 0: cor_status, txt_status = ft.Colors.RED, "ZERADO"
            elif m.quantidade <= m.estoque_minimo: cor_status, txt_status = ft.Colors.ORANGE, "BAIXO"

            tabela_estoque.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Checkbox(on_change=lambda e, mid=m.id: toggle_selecao(e, mid))),
                ft.DataCell(ft.Text(m.nome)),
                ft.DataCell(ft.Text(f"{m.quantidade} {m.unidade}")),
                ft.DataCell(ft.Container(ft.Text(txt_status, color="white", size=10), bgcolor=cor_status, padding=5, border_radius=5)),
                ft.DataCell(ft.Row([
                    # Botão ADICIONAR (+)
                    ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.GREEN, tooltip="Entrada (+)", on_click=lambda e, mid=m.id: abrir_add(mid)),
                    # Botão RETIRAR (-)
                    ft.IconButton(ft.Icons.REMOVE_CIRCLE, icon_color=ft.Colors.RED, tooltip="Saída / Baixa (-)", on_click=lambda e, mid=m.id: abrir_saida(mid)),
                    
                    ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE, tooltip="Editar", on_click=lambda e, obj=m: abrir_editar(obj)),
                    ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.GREY, tooltip="Excluir", on_click=lambda e, mid=m.id: excluir_insumo(e, mid))
                ]))
            ]))
        session.close()
        
        try:
            tabela_estoque.update()
            dd_filtro_hist.update()
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
            cor = ft.Colors.GREEN if h.tipo == "Entrada" else ft.Colors.RED
            tabela_historico.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(h.data.strftime("%d/%m %H:%M"))),
                ft.DataCell(ft.Text(h.material.nome if h.material else "-")),
                ft.DataCell(ft.Text(h.tipo, color=cor, weight="bold")),
                ft.DataCell(ft.Text(str(h.quantidade))),
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

    return ft.Container(padding=20, bgcolor=ft.Colors.GREY_100, expand=True, content=ft.Column([
        ft.Row([
            ft.Text("Estoque", size=25, weight="bold", color=ft.Colors.BLUE_GREY_900),
            ft.Row([
                ft.ElevatedButton("Imprimir Selecionados", icon=ft.Icons.PRINT, bgcolor=ft.Colors.GREY_700, color="white", on_click=imprimir_relatorio),
                ft.ElevatedButton("Novo Insumo", icon=ft.Icons.ADD, bgcolor=ft.Colors.BLUE_600, color="white", on_click=lambda e: page.open(dlg_novo))
            ])
        ], alignment="spaceBetween"),
        ft.Divider(height=10, color="transparent"),
        ft.Container(bgcolor="white", padding=10, border_radius=10, content=ft.Column([tabela_estoque], scroll=ft.ScrollMode.AUTO), height=300),
        ft.Divider(height=20, color="transparent"),
        ft.Row([ft.Icon(ft.Icons.HISTORY), ft.Text("Histórico de Movimentações", size=20, weight="bold"), dd_filtro_hist]),
        ft.Container(bgcolor="white", padding=10, border_radius=10, content=ft.Column([tabela_historico], scroll=ft.ScrollMode.AUTO), expand=True),
    ], scroll=ft.ScrollMode.AUTO))