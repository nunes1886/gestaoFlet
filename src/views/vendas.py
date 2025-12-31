import flet as ft
from src.database.database import get_session, ProdutoServico, Cliente, OrdemServico, ItemOS
from datetime import datetime
from PIL import ImageGrab # Biblioteca para pegar o PrintScreen
import os
import time
import shutil

# --- IMPORTANTE: Importa o gerador de PDF que criamos ---
from src.utils.gerar_pdf import gerar_pdf_venda

def ViewNovaVenda(page):
    carrinho_itens = []
    cliente_selecionado_id = None 
    caminho_imagem_temp = None # Guarda o caminho da imagem temporária

    session = get_session()
    lista_produtos = session.query(ProdutoServico).all()
    todos_clientes = session.query(Cliente).all() 
    session.close()

    # --- LÓGICA DE IMAGEM (CLIPBOARD) ---
    def colar_imagem_clipboard(e):
        nonlocal caminho_imagem_temp
        
        try:
            # Pega o conteúdo da área de transferência
            imagem = ImageGrab.grabclipboard()
            
            if imagem:
                # Cria pasta temporária se não existir
                if not os.path.exists("temp_img"):
                    os.makedirs("temp_img")
                
                # Verifica se é lista de arquivos (copiou arquivo) ou imagem pura (print)
                if isinstance(imagem, list):
                     page.snack_bar = ft.SnackBar(ft.Text("Por favor, tire um PrintScreen (Win+Shift+S) em vez de copiar arquivo."), bgcolor="orange")
                     page.snack_bar.open = True
                     page.update()
                     return

                # Salva imagem temporária
                nome_arq = f"temp_img/temp_{int(time.time())}.png"
                imagem.save(nome_arq)
                
                # Atualiza a interface
                caminho_imagem_temp = nome_arq
                img_preview.src = os.path.abspath(nome_arq)
                img_preview.visible = True
                img_preview.update()
                
                page.snack_bar = ft.SnackBar(ft.Text("Imagem colada!"), bgcolor="green")
                page.snack_bar.open = True
                page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Nada na área de transferência. Tire um PrintScreen primeiro!"), bgcolor="red")
                page.snack_bar.open = True
                page.update()
                
        except Exception as err:
            print(err)
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao colar: {err}"), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    def limpar_imagem(e):
        nonlocal caminho_imagem_temp
        caminho_imagem_temp = None
        img_preview.src = ""
        img_preview.visible = False
        img_preview.update()

    # --- COMPONENTES VISUAIS (BOTOES IMAGEM) ---
    btn_colar = ft.ElevatedButton(
        "Colar Print (Ctrl+V)", 
        icon=ft.icons.PASTE, 
        bgcolor=ft.colors.ORANGE_600, 
        color="white",
        on_click=colar_imagem_clipboard
    )
    
    btn_limpar_img = ft.IconButton(
        icon=ft.icons.DELETE, 
        icon_color="red", 
        tooltip="Remover imagem",
        on_click=limpar_imagem
    )

    img_preview = ft.Image(
        src="",
        width=200,
        height=200,
        fit=ft.ImageFit.CONTAIN,
        visible=False,
        border_radius=10
    )

    # --- FORMATAÇÃO TELEFONE ---
    def formatar_telefone_blur(e):
        valor = "".join(filter(str.isdigit, e.control.value))[:11]
        if not valor: e.control.value = ""
        elif len(valor) <= 10: e.control.value = f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
        else: e.control.value = f"({valor[:2]}) {valor[2:7]}-{valor[7:]}"
        e.control.update()

    def limpar_formatacao_focus(e):
        e.control.value = "".join(filter(str.isdigit, e.control.value))
        e.control.update()

    # --- LÓGICA DE CLIENTE ---
    def selecionar_cliente_lista(e, cli):
        nonlocal cliente_selecionado_id
        txt_cliente.value = cli.nome_empresa
        tel = cli.telefone or ""
        tel_limpo = "".join(filter(str.isdigit, tel))
        if len(tel_limpo) == 11:
            txt_whatsapp.value = f"({tel_limpo[:2]}) {tel_limpo[2:7]}-{tel_limpo[7:]}"
        else:
            txt_whatsapp.value = tel_limpo
        cliente_selecionado_id = cli.id
        lista_sugestoes.visible = False
        page.update()

    def buscar_cliente(e):
        digitado = e.control.value.lower()
        if not digitado:
            lista_sugestoes.visible = False
            page.update()
            return
        matches = [c for c in todos_clientes if digitado in c.nome_empresa.lower()]
        if matches:
            lista_sugestoes.controls.clear()
            for c in matches:
                tel_display = c.telefone
                if tel_display and len(tel_display) == 11:
                     tel_display = f"({tel_display[:2]}) {tel_display[2:7]}-{tel_display[7:]}"
                lista_sugestoes.controls.append(
                    ft.ListTile(title=ft.Text(c.nome_empresa), subtitle=ft.Text(tel_display), on_click=lambda e, cli=c: selecionar_cliente_lista(e, cli), bgcolor="white")
                )
            lista_sugestoes.visible = True
            lista_sugestoes.height = min(len(matches) * 60, 200) 
        else:
            lista_sugestoes.visible = False
        page.update()
    
    # Inputs Cliente
    txt_cliente = ft.TextField(label="Cliente", expand=True, prefix_icon=ft.icons.SEARCH, on_change=buscar_cliente, height=50, bgcolor="white", content_padding=10)
    lista_sugestoes = ft.ListView(visible=False, spacing=0, padding=0)
    container_sugestoes = ft.Container(content=lista_sugestoes, bgcolor="white", border=ft.border.all(1, ft.colors.GREY_300), width=400)
    txt_whatsapp = ft.TextField(label="WhatsApp", expand=True, prefix_icon=ft.icons.PHONE, height=50, bgcolor="white", content_padding=10, input_filter=ft.InputFilter(allow=True, regex_string=r"[0-9]"), max_length=11, on_blur=formatar_telefone_blur, on_focus=limpar_formatacao_focus)
    dt_entrega = ft.TextField(label="Entrega", width=150, value=datetime.now().strftime("%d/%m/%Y"), prefix_icon=ft.icons.CALENDAR_MONTH, height=50, bgcolor="white", content_padding=10)

    # Inputs Produto
    opcoes_produtos = [ft.dropdown.Option(key=str(p.id), text=f"{p.nome} (R$ {p.preco_venda:.2f})") for p in lista_produtos]
    dd_produtos = ft.Dropdown(label="Selecione o Produto", options=opcoes_produtos, expand=True, height=50, bgcolor="white", content_padding=10)
    txt_largura = ft.TextField(label="Larg (m)", expand=True, value="1", height=50, bgcolor="white", content_padding=10)
    txt_altura = ft.TextField(label="Alt (m)", expand=True, value="1", height=50, bgcolor="white", content_padding=10)
    txt_qtd = ft.TextField(label="Qtd", width=80, value="1", height=50, bgcolor="white", content_padding=10)
    
    # Inputs Detalhes e Financeiro
    txt_obs = ft.TextField(label="Obs Produção", multiline=True, min_lines=3, bgcolor="white")
    txt_sinal = ft.TextField(label="Sinal (R$)", value="0.00", width=150, text_align="right", bgcolor="white", on_change=lambda e: atualizar_financeiro(), content_padding=10)
    txt_falta_pagar = ft.Text("Falta: R$ 0.00", size=18, weight="bold", color=ft.colors.RED_600)
    
    tabela_itens = ft.DataTable(width=float('inf'), columns=[ft.DataColumn(ft.Text("Prod")), ft.DataColumn(ft.Text("Medidas")), ft.DataColumn(ft.Text("Total")), ft.DataColumn(ft.Text("Del"))], rows=[])
    txt_total_final = ft.Text("R$ 0.00", size=28, weight="bold", color=ft.colors.GREEN_700)

    # --- LÓGICA FINANCEIRA E ITENS ---
    def atualizar_financeiro():
        try:
            total = sum(item["total"] for item in carrinho_itens)
            sinal = float(txt_sinal.value.replace(",", ".")) if txt_sinal.value else 0.0
            falta = total - sinal
            txt_total_final.value = f"R$ {total:.2f}"
            txt_falta_pagar.value = f"Falta: R$ {falta:.2f}"
            txt_falta_pagar.color = ft.colors.GREEN_600 if falta <= 0.01 else ft.colors.RED_600
            page.update()
        except: pass

    def adicionar_item(e):
        if not dd_produtos.value: return
        session = get_session()
        prod = session.query(ProdutoServico).get(int(dd_produtos.value))
        session.close()
        try:
            larg, alt, qtd = float(txt_largura.value.replace(",", ".")), float(txt_altura.value.replace(",", ".")), int(txt_qtd.value)
        except: return 
        total_item = larg * alt * qtd * prod.preco_venda
        carrinho_itens.append({"id": prod.id, "nome": prod.nome, "l": larg, "a": alt, "q": qtd, "p": prod.preco_venda, "total": total_item})
        reconstruir_tabela()

    def remover_item(e, idx):
        carrinho_itens.pop(idx)
        reconstruir_tabela()

    def reconstruir_tabela():
        tabela_itens.rows.clear()
        for i, item in enumerate(carrinho_itens):
            tabela_itens.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(item["nome"][:15])), 
                ft.DataCell(ft.Text(f"{item['l']}x{item['a']} ({item['q']})")), 
                ft.DataCell(ft.Text(f"{item['total']:.2f}")),
                ft.DataCell(ft.IconButton(ft.icons.DELETE, icon_color="red", on_click=lambda e, idx=i: remover_item(e, idx)))
            ]))
        page.update()
        atualizar_financeiro()

    # --- CONCLUIR VENDA (COM GERAR PDF) ---
    def concluir_venda(e):
        nonlocal cliente_selecionado_id, caminho_imagem_temp
        if not txt_cliente.value or not carrinho_itens:
            page.snack_bar = ft.SnackBar(ft.Text("Preencha dados!"), bgcolor="red"); page.snack_bar.open=True; page.update(); return

        session = get_session()
        cli_id = cliente_selecionado_id
        
        # Cria cliente se não existir
        if not cli_id:
            existente = session.query(Cliente).filter_by(nome_empresa=txt_cliente.value).first()
            if existente: cli_id = existente.id
            else:
                novo = Cliente(nome_empresa=txt_cliente.value, telefone="".join(filter(str.isdigit, txt_whatsapp.value)))
                session.add(novo); session.flush(); cli_id = novo.id
        
        sinal = float(txt_sinal.value.replace(",", ".")) if txt_sinal.value else 0.0
        total = sum(i["total"] for i in carrinho_itens)
        
        # Salva imagem definitiva
        caminho_final = None
        if caminho_imagem_temp:
            if not os.path.exists("os_images"): os.makedirs("os_images")
            nome_final = f"os_images/os_{int(time.time())}.png"
            shutil.copy(caminho_imagem_temp, nome_final)
            caminho_final = nome_final
        
        # Cria a OS no Banco
        nova_os = OrdemServico(
            cliente_id=cli_id, status="Fila", valor_total=total, valor_pago=sinal, 
            observacoes=txt_obs.value, imagem_os=caminho_final, data_criacao=datetime.now()
        )
        session.add(nova_os); session.flush()
        
        # Salva Itens
        for item in carrinho_itens:
            session.add(ItemOS(os_id=nova_os.id, produto_id=item["id"], descricao_item=item["nome"], largura=item["l"], altura=item["a"], quantidade=item["q"], preco_unitario=item["p"], total_item=item["total"]))
        
        session.commit()
        
        # --- GERAÇÃO DO PDF ---
        # Recarrega o objeto OS para garantir que os dados do cliente e itens venham juntos
        session.refresh(nova_os)
        
        try:
            gerar_pdf_venda(nova_os)
            mensagem = f"Venda #{nova_os.id} Salva! PDF Gerado."
            cor_msg = "green"
        except Exception as err:
            mensagem = f"Venda Salva, mas erro no PDF: {err}"
            cor_msg = "orange"
            print(err)

        session.close() # Fecha conexão com banco
        
        # Limpa temporários
        if caminho_imagem_temp and os.path.exists(caminho_imagem_temp):
            try: os.remove(caminho_imagem_temp)
            except: pass

        # Reset da Tela
        carrinho_itens.clear(); reconstruir_tabela()
        txt_cliente.value=""; txt_whatsapp.value=""; txt_sinal.value="0.00"
        cliente_selecionado_id=None
        limpar_imagem(None)
        
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor_msg)
        page.snack_bar.open=True
        page.update()

    # --- LAYOUT ---
    coluna_esquerda = ft.Column([
        ft.Text("Dados do Cliente", weight="bold"), txt_cliente, container_sugestoes, ft.Row([txt_whatsapp, dt_entrega]), 
        ft.Divider(), 
        ft.Text("Produtos", weight="bold"), dd_produtos, ft.Row([txt_largura, txt_altura, txt_qtd]), ft.ElevatedButton("Add Item", on_click=adicionar_item, bgcolor="blue", color="white"), 
        ft.Divider(), 
        ft.Text("Detalhes & Arte", weight="bold"), 
        txt_obs,
        ft.Row([btn_colar, btn_limpar_img]), # Botões de imagem
        img_preview # Preview da imagem
    ], scroll=ft.ScrollMode.AUTO)
    
    coluna_direita = ft.Column([
        ft.Text("Resumo", weight="bold", size=18), 
        ft.Container(content=ft.Column([tabela_itens], scroll="auto"), height=250, border=ft.border.all(1, "grey")), 
        ft.Divider(), 
        ft.Row([ft.Text("Total:"), txt_total_final], alignment="spaceBetween"), 
        ft.Row([txt_sinal, txt_falta_pagar], alignment="spaceBetween"), 
        # AQUI ESTÁ A CORREÇÃO DO BOTÃO RETANGULAR:
        ft.ElevatedButton(
            "CONCLUIR VENDA", 
            on_click=concluir_venda, 
            height=50, 
            bgcolor=ft.colors.GREEN_600, 
            color="white", 
            expand=True,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)) # Força formato retangular
        )
    ])

    return ft.Container(padding=20, bgcolor=ft.colors.GREY_100, expand=True, content=ft.Row([ft.Container(coluna_esquerda, expand=3, bgcolor="white", padding=20, border_radius=10), ft.VerticalDivider(width=20, color="transparent"), ft.Container(coluna_direita, expand=2, bgcolor="white", padding=20, border_radius=10)], vertical_alignment="start"))