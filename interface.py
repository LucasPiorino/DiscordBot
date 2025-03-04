import os
import time
import tkinter as tk
import customtkinter as ctk
from tkinter import ttk

# Importa as variáveis e funções do bot_manager
from bot_manager import (
    music_queue, CURRENT_TRACK, PLAYING_SOURCES, loop_single,
    set_interface_app, start_bot, stop_bot
)

import urllib.request
import subprocess

def check_ffmpeg():
    try:
        proc = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        return True, "ffmpeg detectado com sucesso."
    except Exception as e:
        return False, f"AVISO: ffmpeg não foi encontrado no PATH. O bot não conseguirá tocar áudio.\n{e}"

def check_discord_connectivity():
    try:
        with urllib.request.urlopen("https://discord.com", timeout=5) as resp:
            if resp.status == 200:
                return True, "Conectividade OK com discord.com."
            else:
                return False, f"AVISO: Recebido status {resp.status} ao tentar acessar discord.com."
    except Exception as e:
        return False, f"AVISO: Falha ao acessar discord.com. Pode ser firewall ou falta de internet.\n{e}"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")  # Pode escolher "dark-blue", "blue", "green" etc.

class TokenPopup(ctk.CTkToplevel):
    def __init__(self, master, callback):
        super().__init__(master)
        self.callback = callback
        self.title("Configurar Token do Bot")
        self.geometry("400x200")
        self.resizable(False, False)

        self.label = ctk.CTkLabel(self, text="Insira o Token do Bot:")
        self.label.pack(pady=10)

        self.token_entry = ctk.CTkEntry(self, width=300, show="")
        self.token_entry.pack(pady=5)

        self.remember_var = tk.BooleanVar(value=False)
        self.remember_check = ctk.CTkCheckBox(self, text="Salvar Token para uso futuro", variable=self.remember_var)
        self.remember_check.pack(pady=5)

        self.ok_button = ctk.CTkButton(self, text="OK", command=self.on_ok)
        self.ok_button.pack(pady=10)

    def on_ok(self):
        token = self.token_entry.get().strip()
        remember = self.remember_var.get()
        self.callback(token, remember)
        self.destroy()

class BotInterface(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Toby")
        self.geometry("1000x600")
        self.resizable(True, True)

        self.bot_token = None
        self.bot_status = tk.StringVar(value="Bot Offline")

        self.load_token()
        self.create_layout()
        self.update_status()

        self.check_requirements()

        # Registra a interface no bot_manager
        set_interface_app(self)

        # Se não tiver token, abre popup
        if not self.bot_token:
            self.show_token_popup()

        # Barra superior sem animação
        self.top_bar = ctk.CTkFrame(self, corner_radius=0, fg_color="#3f2aff")
        self.top_bar.pack(side="top", fill="x")

        self.title_label = ctk.CTkLabel(
            self.top_bar,
            text="Toby",
            font=("Helvetica", 20, "bold"),
        )
        self.title_label.pack(pady=10)

    def load_token(self):
        if os.path.isfile("bot_token.txt"):
            with open("bot_token.txt", "r", encoding="utf-8") as f:
                token = f.read().strip()
                if token:
                    self.bot_token = token

    def show_token_popup(self):
        def on_token_entered(token, remember):
            self.bot_token = token
            if remember and token:
                with open("bot_token.txt", "w", encoding="utf-8") as f:
                    f.write(token)
        TokenPopup(self, callback=on_token_entered)

    def check_requirements(self):
        self.log("Verificando se ffmpeg está instalado...")
        ffmpeg_ok, msg_ffmpeg = check_ffmpeg()
        self.log(msg_ffmpeg)

        self.log("Verificando conectividade com discord.com...")
        net_ok, msg_net = check_discord_connectivity()
        self.log(msg_net)

    # ---------------------- Layout com Barra Superior e Tabs ----------------------
    def create_layout(self):
        # Barra superior
        self.top_bar = ctk.CTkFrame(self, corner_radius=0)
        self.top_bar.pack(side="top", fill="x")

        self.title_label = ctk.CTkLabel(self.top_bar, text="Discord Bot - Interface Animada", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=10)

        # Área principal
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(side="bottom", fill="both", expand=True)

        self.tabview = ctk.CTkTabview(main_frame, width=900, height=500)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)

        self.tabview.add("Principal")
        self.tabview.add("Log")
        self.tabview.add("Voice Info")

        # Aba Principal
        principal_tab = self.tabview.tab("Principal")
        self.create_principal_tab(principal_tab)

        # Aba Log
        log_tab = self.tabview.tab("Log")
        self.log_textbox = ctk.CTkTextbox(log_tab, width=850, height=450)
        self.log_textbox.pack(padx=10, pady=10, fill="both", expand=True)
        self.log_textbox.configure(state="disabled")

        # Aba Voice Info
        voice_tab = self.tabview.tab("Voice Info")
        self.voice_label = ctk.CTkLabel(voice_tab, text="Canal de voz: Nenhum")
        self.voice_label.pack(anchor="w", padx=10, pady=5)

        self.voice_users_textbox = ctk.CTkTextbox(voice_tab, width=850, height=400)
        self.voice_users_textbox.pack(padx=10, pady=10, fill="both", expand=True)
        self.voice_users_textbox.configure(state="disabled")

        # Barra de status
        self.status_label = ctk.CTkLabel(self, textvariable=self.bot_status, fg_color=("#333333", "#333333"), corner_radius=0)
        self.status_label.pack(fill="x", side="bottom")

    def create_principal_tab(self, parent):
        controls_frame = ctk.CTkFrame(parent)
        controls_frame.pack(fill="x", padx=10, pady=10)

        self.start_button = ctk.CTkButton(controls_frame, text="Iniciar Bot", command=self.start_bot)
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        self.stop_button = ctk.CTkButton(controls_frame, text="Parar Bot", command=self.stop_bot, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)

        music_frame = ctk.CTkFrame(parent)
        music_frame.pack(fill="x", padx=10, pady=5)

        pause_btn = ctk.CTkButton(music_frame, text="Pausar", command=self.ui_pause_music)
        pause_btn.grid(row=0, column=0, padx=5, pady=5)

        resume_btn = ctk.CTkButton(music_frame, text="Retomar", command=self.ui_resume_music)
        resume_btn.grid(row=0, column=1, padx=5, pady=5)

        loop_btn = ctk.CTkButton(music_frame, text="Loop", command=self.ui_toggle_loop)
        loop_btn.grid(row=0, column=2, padx=5, pady=5)

        stop_music_btn = ctk.CTkButton(music_frame, text="Stop & Clear", command=self.ui_stop_music)
        stop_music_btn.grid(row=0, column=3, padx=5, pady=5)

        skip_music_btn = ctk.CTkButton(music_frame, text="Próxima Música", command=self.ui_skip_music)
        skip_music_btn.grid(row=0, column=4, padx=5, pady=5)

        vol_frame = ctk.CTkFrame(parent)
        vol_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(vol_frame, text="Volume:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.volume_slider = ctk.CTkSlider(vol_frame, from_=0, to=100, number_of_steps=100)
        self.volume_slider.set(50)
        self.volume_slider.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        volume_btn = ctk.CTkButton(vol_frame, text="Aplicar", command=self.ui_set_volume)
        volume_btn.grid(row=0, column=2, padx=5, pady=5)

        self.progress_bar = ctk.CTkProgressBar(vol_frame, orientation="horizontal", width=300)
        self.progress_bar.grid(row=1, column=0, padx=5, pady=5, columnspan=2, sticky="e")
        self.progress_bar.set(0)

        self.time_label = ctk.CTkLabel(vol_frame, text="00:00 / 00:00")
        self.time_label.grid(row=1, column=2, padx=5, pady=5, sticky="w")

        queue_frame = ctk.CTkFrame(parent)
        queue_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(queue_frame, text="Fila de Músicas (clique duas vezes):").pack(anchor="w")

        self.queue_tree = ttk.Treeview(queue_frame, columns=("Title", "URL"), show="headings", height=8)
        self.queue_tree.heading("Title", text="Título")
        self.queue_tree.heading("URL", text="URL")
        self.queue_tree.column("Title", width=300, anchor="w")
        self.queue_tree.column("URL", width=600, anchor="w")
        self.queue_tree.pack(side="left", fill="both", expand=True)

        self.queue_tree.bind("<Double-1>", self.on_treeview_double_click)

        scrollbar = ttk.Scrollbar(queue_frame, orient="vertical", command=self.queue_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.queue_tree.configure(yscrollcommand=scrollbar.set)

    # ---------------------- Animação do Top Bar (transição de cores) ----------------------
    def animate_top_bar(self):
        color = self.color_list[self.color_index]
        self.top_bar.configure(fg_color=color)

        self.color_index = (self.color_index + 1) % len(self.color_list)
        # Chama novamente em 300 ms
        self.after(300, self.animate_top_bar)

    # ---------------------- LOG e Mensagens ----------------------
    def log(self, msg):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", msg + "\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    # ---------------------- Botões Principais ----------------------
    def start_bot(self):
        if not self.bot_token:
            self.log("Token não definido. Abra a popup para inserir o token.")
            self.show_token_popup()
            return
        start_bot(self.bot_token)
        self.log("Iniciando o bot...")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.bot_status.set("Bot Online")

    def stop_bot(self):
        stop_bot()
        self.log("Solicitada parada do bot.")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.bot_status.set("Bot Offline")

    # ---------------------- Controles de Música (UI) ----------------------
    def ui_pause_music(self):
        from bot_manager import bot
        vc = self.get_voice_client()
        if vc and vc.is_playing() and not vc.is_paused():
            vc.pause()
            self.log("Música pausada via UI.")
        else:
            self.log("Nenhuma música tocando ou já está pausada.")

    def ui_resume_music(self):
        from bot_manager import bot
        vc = self.get_voice_client()
        if vc and vc.is_paused():
            vc.resume()
            self.log("Música retomada via UI.")
        else:
            self.log("Nenhuma música pausada.")

    def ui_toggle_loop(self):
        from bot_manager import loop_single
        loop_single = not loop_single
        self.log(f"Loop Single: {loop_single}")

    def ui_stop_music(self):
        from bot_manager import bot, music_queue
        vc = self.get_voice_client()
        if vc and vc.is_playing():
            vc.stop()
            music_queue.clear()
            self.log("Stop & Clear via UI.")
        else:
            self.log("Nenhuma música tocando ou bot não conectado.")

    def ui_skip_music(self):
        from bot_manager import bot
        vc = self.get_voice_client()
        if vc and vc.is_playing():
            vc.stop()
            self.log("Música pulada via UI.")
        else:
            self.log("Nenhuma música tocando.")

    def ui_set_volume(self):
        from bot_manager import bot, PLAYING_SOURCES
        volume = self.volume_slider.get() / 100.0
        vc = self.get_voice_client()
        if vc and vc.guild.id in PLAYING_SOURCES:
            source = PLAYING_SOURCES[vc.guild.id]
            source.volume = volume
            self.log(f"Volume: {volume*100:.0f}%")
        else:
            self.log("Nenhuma música tocando ou bot não conectado.")

    # ---------------------- Fila Clicável ----------------------
    def on_treeview_double_click(self, event):
        from bot_manager import music_queue
        item_id = self.queue_tree.focus()
        if not item_id:
            return
        row_values = self.queue_tree.item(item_id, "values")
        if len(row_values) < 2:
            return
        title_clicked, url_clicked = row_values

        index_found = None
        for idx, item in enumerate(music_queue):
            if item["title"] == title_clicked and item["url"] == url_clicked:
                index_found = idx
                break
        if index_found is not None:
            clicked_item = music_queue[index_found]
            del music_queue[index_found]
            music_queue.appendleft(clicked_item)
            self.log(f"Mudando para a música: {clicked_item['title']}")
            self.ui_skip_music()

    # ---------------------- Voice Client ----------------------
    def get_voice_client(self):
        from bot_manager import bot
        for g in bot.guilds:
            if g.voice_client:
                return g.voice_client
        return None

    # ---------------------- Loop de Atualização ----------------------
    def update_status(self):
        from bot_manager import music_queue, CURRENT_TRACK
        queue_len = len(music_queue)
        self.status_label.configure(text=f"{self.bot_status.get()} | Fila: {queue_len}")

        # Atualiza Treeview
        self.queue_tree.delete(*self.queue_tree.get_children())
        for item in music_queue:
            title = item["title"]
            url = item["url"]
            self.queue_tree.insert("", "end", values=(title, url))

        # Voice info
        vc = self.get_voice_client()
        if vc and vc.channel:
            self.voice_label.configure(text=f"Canal de voz: {vc.channel.name}")
            self.voice_users_textbox.configure(state="normal")
            self.voice_users_textbox.delete("1.0", "end")
            for member in vc.channel.members:
                self.voice_users_textbox.insert("end", member.name + "\n")
            self.voice_users_textbox.see("end")
            self.voice_users_textbox.configure(state="disabled")
        else:
            self.voice_label.configure(text="Canal de voz: Nenhum")
            self.voice_users_textbox.configure(state="normal")
            self.voice_users_textbox.delete("1.0", "end")
            self.voice_users_textbox.configure(state="disabled")

        # Progresso
        if vc and vc.guild.id in CURRENT_TRACK and vc.is_playing():
            track_info = CURRENT_TRACK[vc.guild.id]
            elapsed = time.time() - track_info["start_time"]
            duration = track_info["duration"]
            if elapsed < 0: 
                elapsed = 0
            if elapsed > duration:
                elapsed = duration

            if duration > 0:
                progress_val = elapsed / duration
            else:
                progress_val = 0
            self.progress_bar.set(progress_val)

            def _fmt(sec):
                m, s = divmod(int(sec), 60)
                return f"{m:02d}:{s:02d}"

            self.time_label.configure(text=f"{_fmt(elapsed)} / {_fmt(duration)}")
        else:
            self.progress_bar.set(0)
            self.time_label.configure(text="00:00 / 00:00")

        self.after(1000, self.update_status)

    # ---------------------- Animação do Top Bar (transição de cores) ----------------------
    color_index = 0
    color_list = [
        "#3f2aff", "#5a2aff", "#762aff", "#9b2aff", "#c72aff", "#f32aff",
        "#f32a7c", "#f32ab2", "#d82af3", "#a42af3", "#762aff"
    ]
    def animate_top_bar(self):
        color = self.color_list[self.color_index]
        self.top_bar.configure(fg_color=color)
        self.color_index = (self.color_index + 1) % len(self.color_list)
        self.after(300, self.animate_top_bar)

