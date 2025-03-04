# Bot Discord 

Este projeto implementa um **bot de música para Discord**, usando [yt-dlp](https://github.com/yt-dlp/yt-dlp) para tocar músicas do YouTube e uma **interface gráfica** em [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter). A lógica do bot e a interface são separadas em arquivos, facilitando a manutenção e empacotamento (por exemplo, via [cx_Freeze](https://github.com/marcelotduarte/cx_Freeze)).

## Recursos

- **Interface CustomTkinter**:
  - Abas (Principal, Log, Voice Info).
  - Exibição de fila de músicas em `Treeview` (clique duplo para pular diretamente).
  - Popup para inserir e salvar token do bot em `bot_token.txt`.
  - Barra de progresso, controle de volume e logs detalhados.
- **Comandos do Bot** (ex.: `!play`, `!skip`, `!stop`, `!loop`, etc.).
- **Novo Event Loop** a cada “Iniciar Bot”, permitindo **start/stop** múltiplas vezes sem erro de loop fechado.
- **Verificações** de ffmpeg e conectividade com `discord.com`.

## Pré-requisitos

- **Python 3.8+**  
- **Bibliotecas**:  
  - `discord.py` ou equivalente  
  - `yt-dlp`  
  - `customtkinter`  
  - `PyNaCl` (para voz)  
- **ffmpeg** instalado ou incluso no empacotamento.

## Uso

1. **Clonar** o repositório e instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. **Executar**:
   ```bash
   python main.py
   ```
   - Ao iniciar, uma popup solicitará o **token** do seu bot.  
   - Se quiser salvar o token, marque a opção.
3. **Iniciar Bot** na interface.  
4. **No Discord**, use comandos como:
   - `!play <URL>`: Toca música do YouTube.
   - `!skip`: Pula música.
   - `!stop`: Para e limpa fila.
   - `!join`: Entra no canal de voz atual.
   - `!leave`: Sai do canal de voz.
   - `!loop`: Ativa/Desativa loop.

## Empacotando (Exemplo cx_Freeze)

1. **Crie** um `setup.py`:
   ```python
   from cx_Freeze import setup, Executable

   build_options = {
       'packages': ['discord', 'customtkinter', 'yt_dlp', 'tkinter', 'asyncio'],
       'includes': ['tkinter.ttk']
   }

   setup(
       name="MeuBot",
       version="1.0",
       options={'build_exe': build_options},
       executables=[Executable("main.py")]
   )
   ```
2. **Gere** o executável:
   ```bash
   python setup.py build
   ```
3. A pasta `build` conterá o executável e dependências. Se quiser **incluir** ffmpeg, coloque-o em `include_files` e ajuste o caminho no seu código.

## Observações

- **Se dois computadores usarem o mesmo token** simultaneamente, o Discord só permite um bot conectado; o segundo expulsa o primeiro.  
- **PyNaCl** é necessário para tocar áudio no Discord.  
- **ffmpeg** precisa estar no PATH ou incluso no empacotamento.  
- Permissões de firewall podem ser necessárias se o bot não conectar.

---

**Qualquer dúvida**, abra uma *issue* ou envie PRs com sugestões!
