import time
import asyncio
import threading
from collections import deque

import discord
from discord.ext import commands
import yt_dlp as youtube_dl

# Se você usar voz no Discord, instale PyNaCl (pip install PyNaCl) e inclua:
# import nacl

# --------------- Variáveis e Fila ---------------
music_queue = deque()  # Cada item: {"title": ..., "url": ..., "duration": ...}
loop_single = False
PLAYING_SOURCES = {}
CURRENT_TRACK = {}

# Referência para a interface (para .log(...))
APP = None

# --------------- Configuração do Bot ---------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# yt-dlp config
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
import yt_dlp as real_yt_dlp
ytdl = real_yt_dlp.YoutubeDL(ytdl_format_options)

def set_interface_app(app):
    """Permite ao bot_manager acessar a interface para logar mensagens."""
    global APP
    APP = app

def format_time(sec):
    m, s = divmod(int(sec), 60)
    return f"{m:02d}:{s:02d}"

# --------------- Classe para tocar música ---------------
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# --------------- Comandos do Bot ---------------
@bot.event
async def on_ready():
    if APP:
        APP.log("Bot está online (on_ready).")

@bot.command(name='join', help='Conecta o bot a um canal de voz')
async def join(ctx):
    if APP: APP.log(f"Comando join por {ctx.author}")
    if not ctx.author.voice:
        await ctx.send("Você não está em um canal de voz.")
        return
    channel = ctx.author.voice.channel
    try:
        await channel.connect()
        if APP:
            APP.log(f"Conectado ao canal de voz: {channel.name}")
    except Exception as e:
        await ctx.send(f"Falha ao conectar no canal de voz: {e}")
        if APP:
            APP.log(f"Erro ao conectar no canal de voz: {e}")

@bot.command(name='leave', help='Desconecta o bot do canal de voz')
async def leave(ctx):
    if APP: APP.log(f"Comando leave por {ctx.author}")
    vc = ctx.guild.voice_client
    if vc and vc.is_connected():
        await vc.disconnect()
    else:
        await ctx.send("O bot não está conectado a um canal de voz.")

@bot.command(name='play', help='Toca uma música do YouTube')
async def play(ctx, url):
    if APP: APP.log(f"Comando play por {ctx.author} - URL: {url}")
    if not ctx.author.voice:
        await ctx.send("Você não está em um canal de voz.")
        return
    vc = ctx.guild.voice_client
    if not vc:
        try:
            vc = await ctx.author.voice.channel.connect()
            if APP:
                APP.log(f"Conectado ao canal de voz (play): {vc.channel.name}")
        except Exception as e:
            await ctx.send(f"Falha ao conectar no canal de voz: {e}")
            if APP:
                APP.log(f"Erro ao conectar no canal de voz (play): {e}")
            return

    loop_ = bot.loop or asyncio.get_event_loop()
    info = await loop_.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
    if 'entries' in info:
        info = info['entries'][0]
    title = info.get('title', 'Sem título')
    webpage_url = info.get('webpage_url', url)
    duration = info.get('duration', 0)

    music_queue.append({"title": title, "url": webpage_url, "duration": duration})
    await ctx.send(f"Música adicionada: **{title}** (pos: {len(music_queue)})")
    if APP:
        APP.log(f"Música adicionada à fila: {title}")

    if not vc.is_playing():
        await play_next(ctx)

@bot.command(name='skip', help='Pula para a próxima música da fila')
async def skip(ctx):
    if APP: APP.log(f"Comando skip por {ctx.author}")
    vc = ctx.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("Música pulada.")
    else:
        await ctx.send("Não há música tocando.")

@bot.command(name='stop', help='Para a música e limpa a fila')
async def stop(ctx):
    if APP: APP.log(f"Comando stop por {ctx.author}")
    vc = ctx.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        music_queue.clear()
        await ctx.send("Música parada e fila limpa.")
        if APP:
            APP.log("Stop & Clear via comando.")
    else:
        await ctx.send("Não há música tocando.")

@bot.command(name='loop', help='Ativa/Desativa loop da música atual')
async def loop_cmd(ctx):
    global loop_single
    loop_single = not loop_single
    if APP:
        APP.log(f"Loop Single: {loop_single}")
    await ctx.send(f"Loop: {loop_single}")

@bot.command(name='ping', help='Testa a latência do bot')
async def ping(ctx):
    if APP:
        APP.log(f"Comando ping por {ctx.author}")
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

async def play_next(ctx):
    global loop_single
    if len(music_queue) > 0:
        if loop_single:
            song_info = music_queue[0]
        else:
            song_info = music_queue.popleft()

        player = await YTDLSource.from_url(song_info["url"], loop=bot.loop, stream=True)
        player.volume = 0.5
        voice_client = ctx.guild.voice_client
        PLAYING_SOURCES[ctx.guild.id] = player

        CURRENT_TRACK[ctx.guild.id] = {
            "start_time": time.time(),
            "duration": song_info.get("duration", 0),
            "title": player.title
        }
        if APP:
            APP.log(f"Tocando agora: {player.title}")

        def after_play(err):
            if ctx.guild.id in PLAYING_SOURCES:
                del PLAYING_SOURCES[ctx.guild.id]
            if ctx.guild.id in CURRENT_TRACK:
                del CURRENT_TRACK[ctx.guild.id]
            coro = play_next(ctx)
            fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
            try:
                fut.result()
            except Exception as e:
                print(f"Erro no after_play: {e}")

        voice_client.play(player, after=after_play)
    else:
        await ctx.guild.voice_client.disconnect()
        if APP:
            APP.log("Fila vazia. Desconectando...")

# --------------- Start/Stop do Bot com Novo Event Loop ---------------
_loop_thread = None

def start_bot(token):
    """Cria um novo event loop a cada vez que iniciar, permitindo start/stop múltiplas vezes."""
    def run_in_loop():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            new_loop.run_until_complete(bot.start(token))
        except Exception as e:
            if APP:
                APP.log(f"Erro ao iniciar bot: {e}")
        finally:
            new_loop.close()

    global _loop_thread
    if _loop_thread and _loop_thread.is_alive():
        if APP:
            APP.log("O bot já está em execução.")
        return

    _loop_thread = threading.Thread(target=run_in_loop, daemon=True)
    _loop_thread.start()

def stop_bot():
    """Para o bot de forma segura em uma thread separada para não travar a interface."""
    def _stop():
        if bot.is_closed():
            if APP:
                APP.log("O bot já está parado.")
        else:
            future = asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
            future.result()
            if APP:
                APP.log("Bot parado.")

    threading.Thread(target=_stop, daemon=True).start()
