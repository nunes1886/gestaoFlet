import flet as ft
from src.database.database import get_session, Cliente, OrdemServico

def ViewClientes(page):
    
    id_editar = ft.Ref[int]()
    
    # --- FORMATAÇÃO INTELIGENTE (9 DÍGITOS) ---
    def formatar_telefone_blur(e):
        # Remove tudo que não for número
        valor = "".join(filter(str.isdigit, e.control.value))
        
        if not valor:
            e.control.value = ""
        elif len(valor) == 11: # Celular (XX) XXXXX-XXXX
            e.control.value = f"({valor[:2]}) {valor[2:7]}-{valor[7:]}"
        elif len(valor) == 10: # Fixo (XX) XXXX-XXXX
            e.control.value = f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
        else:
            # Se tiver tamanho estranho, deixa só os números mesmo
            e.control.value = valor
            
        e.control.update()

    def formatar_doc_blur(e):
        v = "".join(filter(str.isdigit, e.control.value))[:14]
        if not v: e.control.value = ""
        elif len(v) <= 11:
            if len(v) == 11: e.control.value = f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:]}"
        else:
            if len(v) == 14: e.control.value = f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"
        e.control.update()

    def limpar_formatacao_focus(e):
        valor_limpo = "".join(filter(str.isdigit, e.control.value))
        e.control.value = valor_limpo
        e.control.update()

    # --- CAMPOS ---
    txt_nome = ft.TextField(label="Nome Completo / Empresa", expand=True)
    
    # InputFilter permite até 11 dígitos (DDD + 9 números)
    txt_telefone = ft.TextField(
        label="Telefone", width=200, 
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"), 
        on_blur=formatar_telefone_blur, on_focus=limpar_formatacao_focus, max_length=11
    )
    txt_doc = ft.TextField(
        label="CPF/CNPJ", width=200, 
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"), 
        on_blur=formatar_doc_blur, on_focus=limpar_formatacao_focus, max_length=14
    )
    txt_email = ft.TextField(label="Email", expand=True, prefix_icon=ft.Icons.EMAIL)
    
    chk_revenda = ft.Checkbox(label="É Parceiro/Revenda? (Ativa tabela de preço diferenciada)", value=False)

    # --- TABELA ---
    tabela = ft.DataTable(
        width=float('inf'), column_spacing=20,
        heading_row_color=ft.Colors.GREY_200,
        columns=[
            ft.DataColumn(ft.Text("Nome", weight="bold")),
            ft.DataColumn(ft.Text("Tipo", weight="bold")), 
            ft.DataColumn(ft.Text("Documento", weight="bold")),
            ft.DataColumn(ft.Text("Telefone", weight="bold")),
            ft.DataColumn(ft.Text("Ações", weight="bold")),
        ], rows=[]
    )

    # --- LÓGICA DO MODAL ---
    def fechar_dialogo(e):
        page.close(dialogo_cliente)

    def abrir_novo(e):
        id_editar.current = None
        txt_nome.value = ""; txt_nome.error_text = None
        txt_telefone.value = ""; txt_email.value = ""; txt_doc.value = ""
        chk_revenda.value = False 
        dialogo_cliente.title = ft.Text("Novo Cliente")
        page.open(dialogo_cliente)

    def abrir_edicao(e, cli):
        id_editar.current = cli.id
        txt_nome.value = cli.nome_empresa
        txt_telefone.value = cli.telefone or ""
        txt_email.value = cli.email or ""
        txt_doc.value = cli.documento or ""
        chk_revenda.value = cli.is_revenda 
        txt_nome.error_text = None
        dialogo_cliente.title = ft.Text(f"Editar: {cli.nome_empresa}")
        page.open(dialogo_cliente)

    def salvar_cliente(e):
        if not txt_nome.value:
            txt_nome.error_text = "Nome Obrigatório"; txt_nome.update(); return

        session = get_session()
        tel_limpo = "".join(filter(str.isdigit, txt_telefone.value))
        doc_limpo = "".join(filter(str.isdigit, txt_doc.value))
        
        try:
            if id_editar.current:
                c = session.query(Cliente).get(id_editar.current)
                if c: 
                    c.nome_empresa = txt_nome.value
                    c.telefone = tel_limpo
                    c.email = txt_email.value
                    c.documento = doc_limpo
                    c.is_revenda = chk_revenda.value
                msg = "Cliente atualizado!"
            else:
                novo = Cliente(nome_empresa=txt_nome.value, telefone=tel_limpo, email=txt_email.value, documento=doc_limpo, is_revenda=chk_revenda.value)
                session.add(novo)
                msg = "Cliente cadastrado!"

            session.commit()
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.GREEN); page.snack_bar.open = True; page.update()
            page.close(dialogo_cliente)
            carregar_dados()

        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {err}"), bgcolor=ft.Colors.RED); page.snack_bar.open = True; page.update()
        finally:
            session.close()

    def excluir_cliente(e, cli_id):
        session = get_session()
        try:
            if session.query(OrdemServico).filter_by(cliente_id=cli_id).count() > 0:
                page.snack_bar = ft.SnackBar(ft.Text("Erro: Cliente possui vendas registradas!"), bgcolor=ft.Colors.RED)
            else:
                c = session.query(Cliente).get(cli_id)
                if c: session.delete(c); session.commit()
                page.snack_bar = ft.SnackBar(ft.Text("Cliente removido."), bgcolor=ft.Colors.ORANGE)
            page.snack_bar.open = True; page.update(); carregar_dados()
        except Exception as err:
            print(err)
        finally: session.close()

    dialogo_cliente = ft.AlertDialog(
        title=ft.Text("Dados do Cliente"),
        content=ft.Container(
            width=600, 
            content=ft.Column([txt_nome, ft.Row([txt_telefone, txt_doc]), txt_email, ft.Divider(), chk_revenda], height=260, spacing=20)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_dialogo),
            ft.ElevatedButton("Salvar", on_click=salvar_cliente, bgcolor=ft.Colors.BLUE_600, color="white"),
        ],
    )

    def carregar_dados():
        tabela.rows.clear()
        session = get_session()
        clientes = session.query(Cliente).order_by(Cliente.id.desc()).all()
        session.close()

        for c in clientes:
            tel_visual = c.telefone
            # Formatação visual na tabela
            if tel_visual:
                if len(tel_visual) == 11:
                    tel_visual = f"({tel_visual[:2]}) {tel_visual[2:7]}-{tel_visual[7:]}"
                elif len(tel_visual) == 10:
                    tel_visual = f"({tel_visual[:2]}) {tel_visual[2:6]}-{tel_visual[6:]}"

            doc_visual = c.documento if c.documento else "-"
            texto_tipo = "REVENDA" if c.is_revenda else "Final"
            cor_tipo = ft.Colors.BLUE_700 if c.is_revenda else ft.Colors.BLACK87
            peso_tipo = "bold" if c.is_revenda else "normal"

            tabela.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(c.nome_empresa, weight="bold")),
                ft.DataCell(ft.Text(texto_tipo, color=cor_tipo, weight=peso_tipo, size=12)),
                ft.DataCell(ft.Text(doc_visual)),
                ft.DataCell(ft.Text(tel_visual if tel_visual else "-")),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE_600, on_click=lambda e, cli=c: abrir_edicao(e, cli)),
                    ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_600, on_click=lambda e, cid=c.id: excluir_cliente(e, cid)),
                ])),
            ]))
        page.update()

    carregar_dados()

    return ft.Container(
        padding=30, expand=True, bgcolor=ft.Colors.GREY_100, 
        content=ft.Column([
            ft.Row([ft.Text("Gestão de Clientes", size=25, weight="bold", color=ft.Colors.BLUE_GREY_900), ft.ElevatedButton("Novo Cliente", icon=ft.Icons.ADD, bgcolor=ft.Colors.BLUE_600, color="white", on_click=abrir_novo)], alignment="spaceBetween"),
            ft.Divider(height=20, color="transparent"),
            ft.Container(bgcolor="white", padding=20, border_radius=10, shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12), content=ft.Column([tabela], scroll=ft.ScrollMode.AUTO))
        ], scroll=ft.ScrollMode.AUTO)
    )