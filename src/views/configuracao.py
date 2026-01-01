import flet as ft
from src.database.database import get_session, Empresa, ProdutoServico, Usuario, DATABASE_URL, engine
import shutil
import os
import datetime
import hashlib
from reset_banco import resetar_tudo 

def ViewConfiguracao(page: ft.Page):
    
    caminho_logo_temp = ft.Ref[str]()
    caminho_icon_temp = ft.Ref[str]()
    
    # --- HELPER: CORRIGE CAMINHO DA IMAGEM ---
    def resolver_src(caminho):
        if not caminho or not os.path.exists(caminho): return ""
        return os.path.basename(caminho)
    
    # --- PRODUTOS: VARIAVEIS ---
    tabela_produtos = ft.DataTable(
        heading_row_height=40,
        column_spacing=20,
        columns=[
            ft.DataColumn(ft.Text("Produto")),
            ft.DataColumn(ft.Text("Venda", color="green"), numeric=True),
            ft.DataColumn(ft.Text("Revenda", color="blue"), numeric=True),
            ft.DataColumn(ft.Text("Ações")),
        ], rows=[]
    )
    
    txt_novo_nome = ft.TextField(label="Nome do Produto", expand=True, height=40, text_size=13, bgcolor="white")
    txt_novo_venda = ft.TextField(label="Venda R$", width=100, height=40, text_size=13, bgcolor="white", keyboard_type=ft.KeyboardType.NUMBER)
    txt_novo_revenda = ft.TextField(label="Revenda R$", width=100, height=40, text_size=13, bgcolor="white", keyboard_type=ft.KeyboardType.NUMBER)

    # --- EMPRESA: CAMPOS ---
    txt_nome_empresa = ft.TextField(label="Nome Fantasia", bgcolor="white", height=40, text_size=14)
    txt_cnpj = ft.TextField(label="CNPJ", bgcolor="white", height=40, text_size=14)
    txt_endereco = ft.TextField(label="Endereço", bgcolor="white", height=40, text_size=14)
    txt_telefone = ft.TextField(label="Telefone", bgcolor="white", height=40, text_size=14)
    
    img_logo_preview = ft.Image(src="", width=100, height=100, fit=ft.ImageFit.CONTAIN, visible=False)
    img_icon_preview = ft.Image(src="", width=50, height=50, fit=ft.ImageFit.CONTAIN, visible=False)

    # --- LÓGICA DE PRODUTOS ---
    def carregar_produtos():
        tabela_produtos.rows.clear()
        session = get_session()
        prods = session.query(ProdutoServico).all()
        session.close()
        
        for p in prods:
            tabela_produtos.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(p.nome, size=12)),
                ft.DataCell(ft.Text(f"{p.preco_venda:.2f}", size=12, weight="bold")),
                ft.DataCell(ft.Text(f"{p.preco_revenda:.2f}", size=12)),
                ft.DataCell(ft.IconButton(ft.Icons.DELETE, icon_color="red", icon_size=18, on_click=lambda e, pid=p.id: deletar_produto(pid)))
            ]))
        try: tabela_produtos.update()
        except: pass

    def adicionar_produto(e):
        if not txt_novo_nome.value: return
        try:
            pv = float(txt_novo_venda.value.replace(",", ".")) if txt_novo_venda.value else 0.0
            pr = float(txt_novo_revenda.value.replace(",", ".")) if txt_novo_revenda.value else 0.0
            
            session = get_session()
            session.add(ProdutoServico(nome=txt_novo_nome.value, preco_venda=pv, preco_revenda=pr, unidade="Un"))
            session.commit(); session.close()
            
            txt_novo_nome.value = ""; txt_novo_venda.value = ""; txt_novo_revenda.value = ""
            txt_novo_nome.update(); txt_novo_venda.update(); txt_novo_revenda.update()
            carregar_produtos()
            page.snack_bar = ft.SnackBar(ft.Text("Produto Adicionado!"), bgcolor="green"); page.snack_bar.open=True; page.update()
        except: pass

    def deletar_produto(pid):
        session = get_session()
        session.query(ProdutoServico).filter_by(id=pid).delete()
        session.commit(); session.close()
        carregar_produtos()

    # --- LÓGICA DE UPLOAD ---
    def on_logo_picked(e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            if not os.path.exists("assets"): os.makedirs("assets")
            destino = f"assets/logo_custom.png"
            shutil.copy(e.files[0].path, destino)
            caminho_logo_temp.current = destino
            img_logo_preview.src = f"logo_custom.png?v={datetime.datetime.now().timestamp()}"
            img_logo_preview.visible = True; img_logo_preview.update()

    def on_icon_picked(e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            if not os.path.exists("assets"): os.makedirs("assets")
            destino = f"assets/favicon_custom.png"
            shutil.copy(e.files[0].path, destino)
            caminho_icon_temp.current = destino
            img_icon_preview.src = f"favicon_custom.png?v={datetime.datetime.now().timestamp()}"
            img_icon_preview.visible = True; img_icon_preview.update()

    fp_logo = ft.FilePicker(on_result=on_logo_picked)
    fp_icon = ft.FilePicker(on_result=on_icon_picked)
    page.overlay.extend([fp_logo, fp_icon])

    def salvar_dados_empresa(e):
        session = get_session()
        emp = session.query(Empresa).first()
        if not emp: emp = Empresa(); session.add(emp)
        emp.nome_fantasia = txt_nome_empresa.value
        emp.cnpj, emp.endereco, emp.telefone = txt_cnpj.value, txt_endereco.value, txt_telefone.value
        if caminho_logo_temp.current: emp.caminho_logo = caminho_logo_temp.current
        if caminho_icon_temp.current: emp.caminho_icon = caminho_icon_temp.current
        session.commit(); session.close()
        page.title = f"{txt_nome_empresa.value}"
        page.update()
        page.snack_bar = ft.SnackBar(ft.Text("Dados Salvos!"), bgcolor="green"); page.snack_bar.open=True; page.update()

    def carregar_dados_empresa():
        session = get_session()
        emp = session.query(Empresa).first()
        if emp:
            txt_nome_empresa.value = emp.nome_fantasia
            txt_cnpj.value = emp.cnpj
            txt_endereco.value = emp.endereco
            txt_telefone.value = emp.telefone
            if emp.caminho_logo:
                img_logo_preview.src = resolver_src(emp.caminho_logo); img_logo_preview.visible = True
            if emp.caminho_icon:
                img_icon_preview.src = resolver_src(emp.caminho_icon); img_icon_preview.visible = True
        session.close()

    # --- BACKUP E RESTAURAÇÃO ---
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
            
            # Força a desconexão do banco atual para permitir a substituição
            engine.dispose()
            try:
                shutil.copy(arquivo_origem, nome_db_destino)
                page.snack_bar = ft.SnackBar(ft.Text("Backup Restaurado! O sistema será fechado."), bgcolor="green"); page.snack_bar.open=True; page.update()
                import time; time.sleep(2)
                page.window_close() # Fecha a janela para reiniciar
            except Exception as err:
                 page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao restaurar: {err}"), bgcolor="red"); page.snack_bar.open=True; page.update()

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

    carregar_dados_empresa()
    carregar_produtos()

    return ft.Container(padding=20, bgcolor=ft.Colors.GREY_100, expand=True, content=ft.Column([
        ft.Text("Configurações", size=25, weight="bold", color=ft.Colors.BLUE_GREY_900),
        ft.Row([
            # Coluna 1: Dados da Empresa
            ft.Container(bgcolor="white", padding=20, border_radius=10, expand=1, content=ft.Column([
                ft.Text("Identidade Visual", weight="bold"), ft.Divider(),
                txt_nome_empresa, txt_cnpj, txt_endereco, txt_telefone,
                ft.Divider(), ft.Text("Imagens"),
                ft.Row([ft.ElevatedButton("Logo", icon=ft.Icons.UPLOAD, on_click=lambda _: fp_logo.pick_files()), img_logo_preview]),
                ft.Row([ft.ElevatedButton("Ícone", icon=ft.Icons.IMAGE, on_click=lambda _: fp_icon.pick_files()), img_icon_preview]),
                ft.Container(height=10), ft.ElevatedButton("Salvar Dados", bgcolor="blue", color="white", width=float('inf'), on_click=salvar_dados_empresa)
            ])),
            # Coluna 2: Produtos e Backup
            ft.Column([
                # Card Produtos
                ft.Container(bgcolor="white", padding=20, border_radius=10, content=ft.Column([
                    ft.Text("Cadastro de Produtos & Preços", weight="bold", color="green"),
                    ft.Row([txt_novo_nome, txt_novo_venda, txt_novo_revenda, ft.IconButton(ft.Icons.ADD_CIRCLE, icon_color="green", icon_size=30, on_click=adicionar_produto)]),
                    ft.Container(content=ft.Column([tabela_produtos], scroll=ft.ScrollMode.AUTO), height=250)
                ])),
                # Card Backup e Reset
                ft.Container(bgcolor="white", padding=20, border_radius=10, content=ft.Column([
                    ft.Text("Sistema & Segurança", weight="bold"),
                    ft.Row([
                        # BOTÃO BAIXAR
                        ft.ElevatedButton("Backup", icon=ft.Icons.DOWNLOAD, bgcolor="orange", color="white", on_click=baixar_backup),
                        
                        # BOTÃO RESTAURAR (NOVO!)
                        ft.ElevatedButton("Restaurar", icon=ft.Icons.UPLOAD_FILE, bgcolor=ft.Colors.GREY_700, color="white", on_click=lambda _: fp_restore.pick_files()),
                        
                        # BOTÃO RESETAR
                        ft.ElevatedButton("Reset Total", icon=ft.Icons.DELETE_FOREVER, bgcolor="red", color="white", on_click=lambda e: page.open(dlg_reset))
                    ], alignment="spaceBetween")
                ]))
            ], expand=1)
        ], vertical_alignment=ft.CrossAxisAlignment.START)
    ], scroll=ft.ScrollMode.AUTO))