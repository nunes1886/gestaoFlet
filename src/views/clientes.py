import flet as ft
from src.database.database import get_session, Cliente, OrdemServico

def ViewClientes(page):
    
    id_editar = ft.Ref[int]()
    
    # --- FORMATAÇÃO DE CAMPOS ---
    def formatar_telefone_blur(e):
        valor = "".join(filter(str.isdigit, e.control.value))[:11]
        if not valor: e.control.value = ""
        elif len(valor) <= 10: e.control.value = f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
        else: e.control.value = f"({valor[:2]}) {valor[2:7]}-{valor[7:]}"
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

    # --- CAMPOS DO FORMULÁRIO ---
    txt_nome = ft.TextField(label="Nome Completo / Empresa", expand=True)
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

    # --- TABELA DE DADOS ---
    tabela = ft.DataTable(
        width=float('inf'), column_spacing=20,
        heading_row_color=ft.Colors.GREY_200,
        columns=[
            ft.DataColumn(ft.Text("Nome", weight="bold")),
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
        # Limpa campos
        txt_nome.value = ""
        txt_nome.error_text = None
        txt_telefone.value = ""
        txt_email.value = ""
        txt_doc.value = ""
        
        dialogo_cliente.title = ft.Text("Novo Cliente")
        # CORREÇÃO: Usar page.open para evitar travamento
        page.open(dialogo_cliente)

    def abrir_edicao(e, cli):
        id_editar.current = cli.id
        txt_nome.value = cli.nome_empresa
        txt_telefone.value = cli.telefone or ""
        txt_email.value = cli.email or ""
        txt_doc.value = cli.documento or ""
        txt_nome.error_text = None
        
        dialogo_cliente.title = ft.Text(f"Editar: {cli.nome_empresa}")
        page.open(dialogo_cliente)

    def salvar_cliente(e):
        if not txt_nome.value:
            txt_nome.error_text = "Nome Obrigatório"
            txt_nome.update()
            return

        session = get_session()
        tel_limpo = "".join(filter(str.isdigit, txt_telefone.value))
        doc_limpo = "".join(filter(str.isdigit, txt_doc.value))
        
        try:
            if id_editar.current:
                # Atualizar
                c = session.query(Cliente).get(id_editar.current)
                if c: 
                    c.nome_empresa = txt_nome.value
                    c.telefone = tel_limpo
                    c.email = txt_email.value
                    c.documento = doc_limpo
                msg = "Cliente atualizado!"
            else:
                # Criar Novo
                novo = Cliente(
                    nome_empresa=txt_nome.value, 
                    telefone=tel_limpo, 
                    email=txt_email.value, 
                    documento=doc_limpo
                )
                session.add(novo)
                msg = "Cliente cadastrado!"

            session.commit()
            
            # Feedback e Fechamento
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.Colors.GREEN)
            page.snack_bar.open = True
            page.update()
            
            page.close(dialogo_cliente)
            carregar_dados()

        except Exception as err:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {err}"), bgcolor=ft.Colors.RED)
            page.snack_bar.open = True
            page.update()
        finally:
            session.close()

    def excluir_cliente(e, cli_id):
        session = get_session()
        try:
            # Verifica se tem vendas antes de excluir
            if session.query(OrdemServico).filter_by(cliente_id=cli_id).count() > 0:
                page.snack_bar = ft.SnackBar(ft.Text("Erro: Cliente possui vendas registradas!"), bgcolor=ft.Colors.RED)
            else:
                c = session.query(Cliente).get(cli_id)
                if c:
                    session.delete(c)
                    session.commit()
                    page.snack_bar = ft.SnackBar(ft.Text("Cliente removido."), bgcolor=ft.Colors.ORANGE)
            
            page.snack_bar.open = True
            page.update()
            carregar_dados()
        except Exception as err:
            print(err)
        finally:
            session.close()

    # --- DEFINIÇÃO DO MODAL ---
    dialogo_cliente = ft.AlertDialog(
        title=ft.Text("Dados do Cliente"),
        content=ft.Container(
            width=600, 
            content=ft.Column([
                txt_nome, 
                ft.Row([txt_telefone, txt_doc]), 
                txt_email
            ], height=220, spacing=20)
        ),
        actions=[
            ft.TextButton("Cancelar", on_click=fechar_dialogo),
            ft.ElevatedButton("Salvar", on_click=salvar_cliente, bgcolor=ft.Colors.BLUE_600, color="white"),
        ],
    )

    # --- CARREGAMENTO DE DADOS ---
    def carregar_dados():
        tabela.rows.clear()
        session = get_session()
        clientes = session.query(Cliente).order_by(Cliente.id.desc()).all()
        session.close()

        for c in clientes:
            # Formatação Visual para a Tabela
            tel_visual = c.telefone
            if tel_visual and len(tel_visual) == 11:
                tel_visual = f"({tel_visual[:2]}) {tel_visual[2:7]}-{tel_visual[7:]}"
            
            doc_visual = c.documento if c.documento else "-"
            numeros_doc = "".join(filter(str.isdigit, doc_visual))
            if len(numeros_doc) == 11: 
                doc_visual = f"{numeros_doc[:3]}.{numeros_doc[3:6]}.{numeros_doc[6:9]}-{numeros_doc[9:]}"
            elif len(numeros_doc) == 14: 
                doc_visual = f"{numeros_doc[:2]}.{numeros_doc[2:5]}.{numeros_doc[5:8]}/{numeros_doc[8:12]}-{numeros_doc[12:]}"

            tabela.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(c.nome_empresa, weight="bold")),
                ft.DataCell(ft.Text(doc_visual)),
                ft.DataCell(ft.Text(tel_visual if tel_visual else "-")),
                ft.DataCell(ft.Row([
                    ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.BLUE_600, tooltip="Editar", on_click=lambda e, cli=c: abrir_edicao(e, cli)),
                    ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_600, tooltip="Excluir", on_click=lambda e, cid=c.id: excluir_cliente(e, cid)),
                ])),
            ]))
        
        try: tabela.update()
        except AssertionError: pass 
        page.update()

    carregar_dados()

    # --- LAYOUT PRINCIPAL ---
    return ft.Container(
        padding=30, expand=True, bgcolor=ft.Colors.GREY_100, 
        content=ft.Column([
            ft.Row([
                ft.Text("Gestão de Clientes", size=25, weight="bold", color=ft.Colors.BLUE_GREY_900), 
                ft.ElevatedButton("Novo Cliente", icon=ft.Icons.ADD, bgcolor=ft.Colors.BLUE_600, color="white", on_click=abrir_novo)
            ], alignment="spaceBetween"),
            
            ft.Divider(height=20, color="transparent"),
            
            ft.Container(
                bgcolor="white", padding=20, border_radius=10, 
                shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12), 
                content=ft.Column([tabela], scroll=ft.ScrollMode.AUTO)
            )
        ], scroll=ft.ScrollMode.AUTO)
    )