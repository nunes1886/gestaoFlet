import flet as ft
from src.database.database import get_session, Empresa, ProdutoServico, Usuario, DATABASE_URL, engine
import shutil
import os
import datetime
import hashlib
from reset_banco import resetar_tudo 

def ViewConfiguracao(page: ft.Page):
    
    # --- HELPER: VERIFICA SE A LOGO EXISTE ---
    def get_logo_widget():
        caminho_arquivo = "assets/logo.png"
        if os.path.exists(caminho_arquivo):
            src_path = f"logo.png?v={datetime.datetime.now().timestamp()}"
            return ft.Image(src=src_path, width=100, height=100, fit=ft.ImageFit.CONTAIN)
        else:
            return ft.Column([
                ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=50, color=ft.Colors.GREY_400),
                ft.Text("Sem logo.png", size=10, color=ft.Colors.GREY_400)
            ], alignment="center", horizontal_alignment="center")

    # --- HELPER: VERIFICA SE O FAVICON EXISTE (NOVO) ---
    def get_favicon_widget():
        caminho_arquivo = "assets/favicon.png"
        if os.path.exists(caminho_arquivo):
            src_path = f"favicon.png?v={datetime.datetime.now().timestamp()}"
            return ft.Image(src=src_path, width=32, height=32, fit=ft.ImageFit.CONTAIN)
        else:
            return ft.Column([
                ft.Icon(ft.Icons.tab, size=30, color=ft.Colors.GREY_400),
                ft.Text("Sem icon", size=10, color=ft.Colors.GREY_400)
            ], alignment="center", horizontal_alignment="center")

    # --- FORMATAÇÃO (MÁSCARAS) ---
    def formatar_telefone_blur(e):
        v = "".join(filter(str.isdigit, e.control.value))
        if not v: e.control.value = ""
        elif len(v) == 11: e.control.value = f"({v[:2]}) {v[2:7]}-{v[7:]}"
        elif len(v) == 10: e.control.value = f"({v[:2]}) {v[2:6]}-{v[6:]}"
        else: e.control.value = v
        e.control.update()

    def formatar_cnpj_blur(e):
        v = "".join(filter(str.isdigit, e.control.value))[:14]
        if not v: e.control.value = ""
        elif len(v) == 14:
            e.control.value = f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:]}"
        else: e.control.value = v
        e.control.update()

    def limpar_formatacao_focus(e):
        e.control.value = "".join(filter(str.isdigit, e.control.value))
        e.control.update()

    # --- TABELA DE PRODUTOS ---
    tabela_produtos = ft.DataTable(
        heading_row_height=40, column_spacing=20,
        columns=[
            ft.DataColumn(ft.Text("Produto")), 
            ft.DataColumn(ft.Text("Venda", color="green"), numeric=True), 
            ft.DataColumn(ft.Text("Revenda", color="blue"), numeric=True), 
            ft.DataColumn(ft.Text("Ações"))
        ], rows=[]
    )
    
    txt_novo_nome = ft.TextField(label="Nome do Produto", expand=True, height=40, bgcolor="white", content_padding=10)
    txt_novo_venda = ft.TextField(label="Venda R$", width=100, height=40, bgcolor="white", keyboard_type=ft.KeyboardType.NUMBER, content_padding=10)
    txt_novo_revenda = ft.TextField(label="Revenda R$", width=100, height=40, bgcolor="white", keyboard_type=ft.KeyboardType.NUMBER, content_padding=10)

    # --- DADOS DA EMPRESA (COM MÁSCARAS) ---
    txt_nome_empresa = ft.TextField(label="Nome Fantasia", bgcolor="white", height=40, content_padding=10)
    
    txt_cnpj = ft.TextField(
        label="CNPJ", bgcolor="white", height=40, content_padding=10,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"),
        max_length=18,
        on_blur=formatar_cnpj_blur,
        on_focus=limpar_formatacao_focus
    )
    
    txt_endereco = ft.TextField(label="Endereço", bgcolor="white", height=40, content_padding=10)
    
    txt_telefone = ft.TextField(
        label="Telefone", bgcolor="white", height=40, content_padding=10,
        input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"),
        max_length=15,
        on_blur=formatar_telefone_blur,
        on_focus=limpar_formatacao_focus
    )
    
    # Widgets de Imagem
    container_logo = ft.Container(content=get_logo_widget(), alignment=ft.alignment.center)
    container_favicon = ft.Container(content=get_favicon_widget(), alignment=ft.alignment.center)

    # --- FUNÇÕES ---
    def carregar_produtos():
        tabela_produtos.rows.clear()
        session = get_session()
        prods = session.query(ProdutoServico).all()
        session.close()
        
        for p in prods:
            tabela_produtos.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(p.nome)), 
                ft.DataCell(ft.Text(f"{p.preco_venda:.2f}")), 
                ft.DataCell(ft.Text(f"{p.preco_revenda:.2f}")),
                ft.DataCell(ft.IconButton(ft.Icons.DELETE, icon_color="red", on_click=lambda e, pid=p.id: deletar_produto(pid)))
            ]))
        try: tabela_produtos.update()
        except: pass

    def adicionar_produto(e):
        if not txt_novo_nome.value: return
        try:
            pv = float(txt_novo_venda.value.replace(",", ".")) if txt_novo_venda.value else 0.0
            pr = float(txt_novo_revenda.value.replace(",", ".")) if txt_novo_revenda.value else 0.0
            
            session = get_session()
            session.add(ProdutoServico(nome=txt_novo_nome.value, preco_venda=pv, preco_revenda=pr))
            session.commit(); session.close()
            
            txt_novo_nome.value = ""; txt_novo_venda.value = ""; txt_novo_revenda.value = ""
            page.update(); carregar_produtos()
        except: pass

    def deletar_produto(pid):
        session = get_session(); session.query(ProdutoServico).filter_by(id=pid).delete(); session.commit(); session.close(); carregar_produtos()

    def salvar_dados_empresa(e):
        session = get_session()
        emp = session.query(Empresa).first()
        if not emp: emp = Empresa(); session.add(emp)
        emp.nome_fantasia = txt_nome_empresa.value
        # Salva apenas números no banco
        emp.cnpj = "".join(filter(str.isdigit, txt_cnpj.value))
        emp.endereco = txt_endereco.value
        emp.telefone = "".join(filter(str.isdigit, txt_telefone.value))
        session.commit(); session.close()
        page.title = f"{txt_nome_empresa.value}"; page.update()
        page.snack_bar = ft.SnackBar(ft.Text("Dados Salvos!"), bgcolor="green"); page.snack_bar.open=True; page.update()

    def carregar_dados_empresa():
        session = get_session(); emp = session.query(Empresa).first(); session.close()
        if emp:
            txt_nome_empresa.value = emp.nome_fantasia
            txt_endereco.value = emp.endereco
            
            # Carrega e formata visualmente
            c_raw = emp.cnpj or ""
            if len(c_raw) == 14: txt_cnpj.value = f"{c_raw[:2]}.{c_raw[2:5]}.{c_raw[5:8]}/{c_raw[8:12]}-{c_raw[12:]}"
            else: txt_cnpj.value = c_raw

            t_raw = emp.telefone or ""
            if len(t_raw) == 11: txt_telefone.value = f"({t_raw[:2]}) {t_raw[2:7]}-{t_raw[7:]}"
            elif len(t_raw) == 10: txt_telefone.value = f"({t_raw[:2]}) {t_raw[2:6]}-{t_raw[6:]}"
            else: txt_telefone.value = t_raw

    # --- BACKUP E RESET ---
    def baixar_backup(e):
        nome_db = DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(nome_db):
            destino = f"backup_{datetime.date.today()}.db"
            shutil.copy(nome_db, destino)
            os.startfile(os.path.abspath(".")) 
            page.snack_bar = ft.SnackBar(ft.Text(f"Backup: {destino}"), bgcolor="green"); page.snack_bar.open=True; page.update()

    def restaurar_backup_pick(e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            arquivo_origem = e.files[0].path
            nome_db_destino = DATABASE_URL.replace("sqlite:///", "")
            engine.dispose()
            try:
                shutil.copy(arquivo_origem, nome_db_destino)
                page.snack_bar = ft.SnackBar(ft.Text("Backup Restaurado! Fechando sistema..."), bgcolor="green"); page.snack_bar.open=True; page.update()
                import time; time.sleep(2); page.window_close()
            except Exception as err:
                 page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {err}"), bgcolor="red"); page.snack_bar.open=True; page.update()

    fp_restore = ft.FilePicker(on_result=restaurar_backup_pick)
    page.overlay.append(fp_restore)
    
    txt_senha_reset = ft.TextField(label="Senha Admin", password=True)
    def confirmar_reset(e):
        if not txt_senha_reset.value: return
        session = get_session(); admin = session.query(Usuario).filter_by(usuario="admin").first()
        hash_s = hashlib.sha256(txt_senha_reset.value.encode()).hexdigest()
        if admin and admin.senha_hash == hash_s:
            session.close(); page.close(dlg_reset); resetar_tudo()
            page.snack_bar = ft.SnackBar(ft.Text("Resetado!"), bgcolor="green"); page.snack_bar.open=True; page.update()
        else: session.close(); page.snack_bar = ft.SnackBar(ft.Text("Senha Errada!"), bgcolor="red"); page.snack_bar.open=True; page.update()
    
    dlg_reset = ft.AlertDialog(title=ft.Text("RESET TOTAL"), content=txt_senha_reset, actions=[ft.TextButton("Cancelar", on_click=lambda e: page.close(dlg_reset)), ft.ElevatedButton("CONFIRMAR", bgcolor="red", color="white", on_click=confirmar_reset)])

    carregar_dados_empresa(); carregar_produtos()

    return ft.Container(padding=20, bgcolor=ft.Colors.GREY_100, expand=True, content=ft.Column([
        ft.Text("Configurações", size=25, weight="bold", color=ft.Colors.BLUE_GREY_900),
        ft.Row([
            # Coluna 1
            ft.Container(bgcolor="white", padding=20, border_radius=10, expand=1, content=ft.Column([
                ft.Text("Identidade & Dados", weight="bold"), ft.Divider(),
                txt_nome_empresa, txt_cnpj, txt_endereco, txt_telefone,
                ft.Divider(),
                ft.Text("Logo do Sistema", weight="bold"),
                ft.Row([
                    container_logo, 
                    ft.Column([
                        ft.Text("Para alterar a logo:", size=12, color="grey"),
                        ft.Text("1. Salve 'logo.png' na pasta assets", size=11, italic=True),
                        ft.Text("2. Reinicie o sistema", size=11, italic=True),
                    ])
                ]),
                ft.Divider(),
                ft.Text("Favicon (Ícone)", weight="bold"),
                ft.Row([
                    container_favicon, 
                    ft.Column([
                        ft.Text("Para alterar o ícone:", size=12, color="grey"),
                        ft.Text("1. Salve 'favicon.png' na pasta assets", size=11, italic=True),
                        ft.Text("2. Reinicie o sistema", size=11, italic=True),
                    ])
                ]),
                ft.Container(height=10), ft.ElevatedButton("Salvar Dados", bgcolor="blue", color="white", width=float('inf'), on_click=salvar_dados_empresa)
            ])),
            # Coluna 2
            ft.Column([
                ft.Container(bgcolor="white", padding=20, border_radius=10, content=ft.Column([
                    ft.Text("Produtos", weight="bold", color="green"),
                    ft.Row([txt_novo_nome, txt_novo_venda, txt_novo_revenda, ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color="green", icon_size=30, on_click=adicionar_produto)]),
                    ft.Container(content=ft.Column([tabela_produtos], scroll=ft.ScrollMode.AUTO), height=250)
                ])),
                ft.Container(bgcolor="white", padding=20, border_radius=10, content=ft.Column([
                    ft.Text("Segurança", weight="bold"),
                    ft.Row([
                        ft.ElevatedButton("Backup", icon=ft.Icons.DOWNLOAD, bgcolor="orange", color="white", on_click=baixar_backup),
                        ft.ElevatedButton("Restaurar", icon=ft.Icons.UPLOAD_FILE, bgcolor=ft.Colors.GREY_700, color="white", on_click=lambda _: fp_restore.pick_files()),
                        ft.ElevatedButton("Reset", icon=ft.Icons.DELETE_FOREVER, bgcolor="red", color="white", on_click=lambda e: page.open(dlg_reset))
                    ], alignment="spaceBetween")
                ]))
            ], expand=1)
        ], vertical_alignment=ft.CrossAxisAlignment.START)
    ], scroll=ft.ScrollMode.AUTO))