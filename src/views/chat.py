import flet as ft
from src.database.database import get_session, ChatMensagem, Usuario
from sqlalchemy.orm import joinedload
from datetime import datetime
import threading
import time

def ViewChat(page):
    
    # --- VARIÁVEIS DE CONTROLE ---
    usuario_logado_id = page.session.get("user_id")
    
    id_ultimo_msg = ft.Ref[int]()
    id_ultimo_msg.current = 0
    rodando = ft.Ref[bool]()
    rodando.current = True
    
    # Elementos Visuais
    lista_mensagens = ft.ListView(expand=True, spacing=10, auto_scroll=True)
    txt_msg = ft.TextField(
        hint_text="Digite sua mensagem...", 
        expand=True, 
        border_radius=20, 
        bgcolor="white", 
        on_submit=lambda e: enviar_mensagem(e)
    )
    
    # --- FUNÇÃO: ENVIAR MENSAGEM ---
    def enviar_mensagem(e):
        texto = txt_msg.value
        if not texto: return
        
        try:
            session = get_session()
            nova_msg = ChatMensagem(
                remetente_id=usuario_logado_id,
                destinatario_id=None, # None = Chat Geral
                mensagem=texto,
                data_envio=datetime.now()
            )
            session.add(nova_msg)
            session.commit()
            session.close()
            
            txt_msg.value = ""
            txt_msg.focus()
            page.update()
            
            # Força atualização imediata
            carregar_novas()
            
        except Exception as err:
            print(f"Erro envio: {err}")

    # --- FUNÇÃO: CARREGAR MENSAGENS (LOOP) ---
    def loop_atualizacao():
        while rodando.current:
            try:
                carregar_novas()
            except Exception as e:
                print(f"Erro no Loop: {e}")
            time.sleep(2) # Atualiza a cada 2 segundos

    def carregar_novas():
        session = get_session()
        
        msgs = session.query(ChatMensagem).options(joinedload(ChatMensagem.remetente))\
            .filter(ChatMensagem.destinatario_id == None)\
            .filter(ChatMensagem.id > id_ultimo_msg.current)\
            .order_by(ChatMensagem.id).all()
            
        session.close()

        if msgs:
            novos_baloes = []
            for m in msgs:
                id_ultimo_msg.current = m.id
                eh_minha = (m.remetente_id == usuario_logado_id)
                
                # Visual do Balão
                cor_fundo = ft.colors.BLUE_100 if eh_minha else "white"
                alinhamento = ft.MainAxisAlignment.END if eh_minha else ft.MainAxisAlignment.START
                
                # Tratamento seguro do nome
                nome_remetente = "Desconhecido"
                if eh_minha:
                    nome_remetente = "Eu"
                elif m.remetente:
                    nome_remetente = m.remetente.nome
                
                hora_formatada = m.data_envio.strftime("%H:%M")
                
                balao = ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(nome_remetente, size=11, weight="bold", color=ft.colors.BLUE_GREY_900),
                            ft.Text(m.mensagem, size=14, color="black"),
                            ft.Text(hora_formatada, size=9, color="grey", text_align="right")
                        ], spacing=2, tight=True),
                        bgcolor=cor_fundo,
                        padding=10,
                        border_radius=ft.border_radius.only(
                            top_left=10, top_right=10, 
                            bottom_left=0 if not eh_minha else 10, 
                            bottom_right=0 if eh_minha else 10
                        ),
                        shadow=ft.BoxShadow(blur_radius=2, color=ft.colors.BLACK12),
                        # REMOVI A LINHA 'constraints' QUE DAVA ERRO
                    )
                ], alignment=alinhamento)
                
                novos_baloes.append(balao)

            lista_mensagens.controls.extend(novos_baloes)
            
            try:
                lista_mensagens.update()
            except: pass

    # Inicia a thread
    t = threading.Thread(target=loop_atualizacao, daemon=True)
    t.start()
    
    def ao_sair(e):
        rodando.current = False

    return ft.Container(
        expand=True,
        padding=20,
        bgcolor="#E5DDD5", 
        content=ft.Column([
            ft.Container(
                bgcolor="white", padding=10, border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.BLACK12),
                content=ft.Row([
                    ft.Icon(ft.Icons.FORUM, color=ft.colors.TEAL),
                    ft.Text("Chat Geral da Equipe", weight="bold", size=16, color=ft.colors.TEAL_800),
                    ft.Container(expand=True),
                    ft.IconButton(ft.Icons.REFRESH, icon_color=ft.colors.GREY, tooltip="Forçar Atualização", on_click=lambda e: carregar_novas())
                ])
            ),
            ft.Container(
                content=lista_mensagens,
                expand=True, 
                border_radius=10
            ),
            ft.Row([
                txt_msg,
                ft.IconButton(ft.Icons.SEND, icon_color=ft.colors.TEAL, on_click=enviar_mensagem)
            ])
        ])
    )