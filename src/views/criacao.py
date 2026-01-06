import flet as ft
from src.database.database import get_session, OrdemServico
from sqlalchemy.orm import joinedload
import os
import shutil
import urllib.parse

def ViewCriacao(page):
    
    # --- VARIÁVEIS ---
    caminho_arquivo_selecionado = ft.Ref[str]()
    id_os_anexo = ft.Ref[int]()

    # --- FUNÇÃO: PICKER DE ARQUIVO (UPLOAD) ---
    def salvar_caminho_arquivo(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            caminho_origem = e.files[0].path
            os_id = id_os_anexo.current
            
            # Cria pasta se não existir
            pasta_destino = "assets/artes_finais"
            if not os.path.exists(pasta_destino):
                os.makedirs(pasta_destino)
            
            # Copia o arquivo para a pasta do sistema (para garantir acesso)
            nome_arquivo = f"OS_{os_id}_{e.files[0].name}"
            caminho_destino = os.path.join(pasta_destino, nome_arquivo)
            
            try:
                shutil.copy(caminho_origem, caminho_destino)
                
                # Salva no Banco
                session = get_session()
                os_atual = session.query(OrdemServico).get(os_id)
                if os_atual:
                    os_atual.imagem_os = caminho_destino
                    session.commit()
                session.close()
                
                page.snack_bar = ft.SnackBar(ft.Text(f"Arte anexada: {nome_arquivo}"), bgcolor=ft.colors.GREEN)
                page.snack_bar.open = True
                page.update()
                carregar_dados() # Atualiza para mostrar que tem arquivo
                
            except Exception as err:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao salvar arquivo: {err}"), bgcolor=ft.colors.RED)
                page.snack_bar.open = True
                page.update()

    file_picker = ft.FilePicker(on_result=salvar_caminho_arquivo)
    page.overlay.append(file_picker)

    def abrir_seletor_arquivo(os_id):
        id_os_anexo.current = os_id
        file_picker.pick_files(allow_multiple=False)

    # --- FUNÇÕES DE STATUS ---
    def mover_status(os_id, novo_status):
        try:
            session = get_session()
            os_atual = session.query(OrdemServico).get(os_id)
            if os_atual:
                os_atual.status = novo_status
                session.commit()
            session.close()
            
            msg = f"OS #{os_id} movida para: {novo_status}"
            cor = ft.colors.BLUE
            
            # Se for para produção, avisa diferente
            if novo_status == "Fila": # "Fila" é o início da Produção
                msg = f"OS #{os_id} enviada para IMPRESSÃO!"
                cor = ft.colors.GREEN_700
            
            page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=cor)
            page.snack_bar.open = True
            page.update()
            carregar_dados()
        except Exception as e:
            print(e)

    # --- UI: CARD DE TAREFA ---
    def card_criacao(os_obj, coluna):
        # Cores e Ícones baseados na urgência
        borda_cor = ft.colors.RED_400 if os_obj.is_urgente else ft.colors.GREY_300
        bg_card = ft.colors.RED_50 if os_obj.is_urgente else "white"
        icone_urgente = ft.Icon(ft.Icons.WARNING, color=ft.colors.RED, size=16) if os_obj.is_urgente else ft.Container()
        
        # Resumo dos itens
        txt_itens = ", ".join([f"{i.quantidade}x {i.descricao_item}" for i in os_obj.itens])
        
        # Botões de Ação
        botoes = []
        
        # COLUNA 1: FILA DE ARTE (Novos) -> Mover para Aprovação
        if coluna == 1:
            btn_zap = ft.IconButton(ft.Icons.MESSAGE, tooltip="Contatar Cliente", icon_color=ft.colors.GREEN, on_click=lambda e: enviar_zap(os_obj))
            btn_mover = ft.ElevatedButton("Pedir Aprovação", icon=ft.Icons.ARROW_FORWARD, style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_600, color="white", padding=5), height=30, on_click=lambda e, oid=os_obj.id: mover_status(oid, "Aprovação"))
            botoes = [btn_zap, btn_mover]

        # COLUNA 2: AGUARDANDO APROVAÇÃO -> Voltar ou Finalizar
        elif coluna == 2:
            btn_voltar = ft.IconButton(ft.Icons.ARROW_BACK, tooltip="Voltar (Alteração)", icon_color=ft.colors.ORANGE, on_click=lambda e, oid=os_obj.id: mover_status(oid, "Criando Arte"))
            btn_ok = ft.ElevatedButton("Aprovado", icon=ft.Icons.CHECK, style=ft.ButtonStyle(bgcolor=ft.colors.GREEN_600, color="white", padding=5), height=30, on_click=lambda e, oid=os_obj.id: mover_status(oid, "Arte Finalizada"))
            botoes = [btn_voltar, btn_ok]

        # COLUNA 3: ARTE FINALIZADA -> Anexar e Mandar p/ Produção
        elif coluna == 3:
            # Verifica se já tem arquivo
            tem_arquivo = os_obj.imagem_os and os.path.exists(os_obj.imagem_os)
            cor_anexo = ft.colors.GREEN if tem_arquivo else ft.colors.GREY
            icon_anexo = ft.Icons.ATTACH_FILE if not tem_arquivo else ft.Icons.CHECK_CIRCLE
            
            btn_anexo = ft.IconButton(icon_anexo, tooltip="Anexar Arte Final", icon_color=cor_anexo, on_click=lambda e, oid=os_obj.id: abrir_seletor_arquivo(oid))
            
            # Só libera enviar para produção se tiver arquivo (opcional, mas recomendado)
            btn_producao = ft.ElevatedButton("Imprimir", icon=ft.Icons.PRINT, style=ft.ButtonStyle(bgcolor=ft.colors.BLUE_GREY_800, color="white", padding=5), height=30, on_click=lambda e, oid=os_obj.id: mover_status(oid, "Fila")) # Manda para o painel de Produção
            
            botoes = [btn_anexo, btn_producao]

        return ft.Container(
            padding=10,
            bgcolor=bg_card,
            border=ft.border.all(1, borda_cor),
            border_radius=8,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK12),
            content=ft.Column([
                ft.Row([
                    ft.Text(f"#{os_obj.id}", weight="bold", color=ft.colors.GREY_700),
                    icone_urgente,
                    ft.Text(os_obj.data_criacao.strftime("%d/%m"), size=10, color=ft.colors.GREY_500)
                ], alignment="spaceBetween"),
                ft.Text(os_obj.cliente.nome_empresa, weight="bold", size=14, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(txt_itens, size=12, color=ft.colors.GREY_700, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Divider(height=5, color="transparent"),
                ft.Row(botoes, alignment="spaceBetween")
            ], spacing=2)
        )

    def enviar_zap(os_obj):
        if os_obj.cliente.telefone:
            nums = "".join(filter(str.isdigit, os_obj.cliente.telefone))
            msg = f"Olá {os_obj.cliente.nome_empresa}, segue a prova da arte do pedido #{os_obj.id} para aprovação."
            link = f"https://wa.me/55{nums}?text={urllib.parse.quote(msg)}"
            page.launch_url(link)

    # --- COLUNAS DO KANBAN ---
    col_fila = ft.Column(spacing=10, scroll=ft.ScrollMode.HIDDEN)
    col_aprovacao = ft.Column(spacing=10, scroll=ft.ScrollMode.HIDDEN)
    col_finalizada = ft.Column(spacing=10, scroll=ft.ScrollMode.HIDDEN)

    def criar_coluna_kanban(titulo, cor_topo, conteudo):
        return ft.Container(
            width=300,
            bgcolor="white",
            border_radius=10,
            padding=10,
            content=ft.Column([
                ft.Container(
                    content=ft.Text(titulo, color="white", weight="bold"),
                    bgcolor=cor_topo,
                    padding=10,
                    border_radius=8,
                    alignment=ft.alignment.center
                ),
                ft.Container(content=conteudo, expand=True) # Área rolável
            ], spacing=10),
            shadow=ft.BoxShadow(blur_radius=10, color=ft.colors.BLACK12)
        )

    def carregar_dados():
        col_fila.controls.clear()
        col_aprovacao.controls.clear()
        col_finalizada.controls.clear()

        session = get_session()
        # Busca todas as OS que NÃO estão entregues/canceladas
        # E que estão nos status pertinentes a criação
        # Vamos definir os status de criação: 'Pendente', 'Criando Arte', 'Aprovação', 'Arte Finalizada'
        # Se você usar outros nomes no banco, ajuste aqui
        
        lista_os = session.query(OrdemServico).options(joinedload(OrdemServico.cliente), joinedload(OrdemServico.itens)).order_by(OrdemServico.is_urgente.desc(), OrdemServico.id.asc()).all()
        session.close()

        count_fila = 0
        count_aprov = 0
        count_final = 0

        for os_obj in lista_os:
            st = os_obj.status
            
            # Lógica de distribuição nas colunas
            # Coluna 1: Chegou agora ou está fazendo
            if st in ["Pendente", "Criando Arte", "Aguardando Arte", "Fila"]: 
                col_fila.controls.append(card_criacao(os_obj, 1))
                count_fila += 1
            
            # Coluna 2: Enviou pro cliente
            elif st in ["Aprovação", "Aguardando Aprovação", "Aguardando Cliente"]:
                col_aprovacao.controls.append(card_criacao(os_obj, 2))
                count_aprov += 1
            
            # Coluna 3: Aprovou, falta mandar pra produção
            elif st in ["Arte Finalizada", "Arte Aprovada"]:
                col_finalizada.controls.append(card_criacao(os_obj, 3))
                count_final += 1

        try:
            # Atualiza contadores nos títulos (opcional, requer refatorar o título para ser Ref)
            col_fila.update()
            col_aprovacao.update()
            col_finalizada.update()
        except: pass

    carregar_dados()

    return ft.Container(
        expand=True,
        padding=20,
        bgcolor="#f0f2f5", # Fundo cinza suave
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.BRUSH, color=ft.colors.PURPLE_600, size=30),
                ft.Text("Estúdio de Criação", size=28, weight="bold", color=ft.colors.BLUE_GREY_900),
                ft.Container(expand=True),
                ft.IconButton(ft.Icons.REFRESH, icon_color=ft.colors.BLUE_GREY_600, on_click=lambda e: carregar_dados())
            ]),
            ft.Divider(height=20, color="transparent"),
            
            # ÁREA DO KANBAN (LINHA COM 3 COLUNAS)
            ft.Row([
                criar_coluna_kanban("🎨 Fila de Arte", ft.colors.BLUE_500, col_fila),
                criar_coluna_kanban("⏳ Aguardando Aprovação", ft.colors.ORANGE_500, col_aprovacao),
                criar_coluna_kanban("✅ Prontos p/ Produção", ft.colors.GREEN_600, col_finalizada),
            ], alignment="start", vertical_alignment="start", expand=True, scroll=ft.ScrollMode.AUTO)
        ])
    )