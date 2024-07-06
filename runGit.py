import discord
from discord.ext import commands
import yt_dlp
import asyncio
from queue import Queue

# Initialiser botten med intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Kø til at holde video URLs
video_queue = Queue()

# Funktion til at downloade og afspille YouTube videoer
async def play_next_song(ctx):
    if not video_queue.empty():
        url = video_queue.get()
        print(f"Afspiller næste sang: {url}")

        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info['url']
                title = info.get('title', 'Unknown title')
        except Exception as e:
            await ctx.send(f"Kunne ikke hente video information: {e}")
            return
        
        # Tjek om botten allerede er i en kanal
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Du skal være i en stemmekanal for at kunne afspille musik.")
                return

        # Afspil videoen
        source = discord.FFmpegPCMAudio(video_url, **ffmpeg_options)
        ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(play_next_song(ctx), bot.loop))

        await ctx.send(f'Nu spiller: {title}')
    else:
        await ctx.send('Køen er tom.')

# Kommando til at tilføje en sang til køen
@bot.command(name='add')
async def add_to_queue(ctx, url: str):
    video_queue.put(url)
    print(f"Tilføjet til køen: {url}")
    await ctx.send(f'Tilføjet til køen: {url}')
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await play_next_song(ctx)

# Kommando til at starte afspilning af køen
@bot.command(name='play')
async def start_playing(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await play_next_song(ctx)

# Kommando til at stoppe afspilning og rydde køen
@bot.command(name='stop')
async def stop_playing(ctx):
    if ctx.voice_client is_playing():
        ctx.voice_client.stop()
    video_queue.queue.clear()
    await ctx.send('Afspilning stoppet, og køen er ryddet.')

# Kommando til at springe en sang over
@bot.command(name='skip')
async def skip_song(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await play_next_song(ctx)
    else:
        await ctx.send('Der er ingen sang, der spiller.')

# Kommando til at pause en sang
@bot.command(name='pause')
async def pause_song(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send('Sangen er pauset.')
    else:
        await ctx.send('Der er ingen sang, der spiller.')

# Kommando til at genoptage en pauset sang
@bot.command(name='resume')
async def resume_song(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send('Sangen er genoptaget.')
    else:
        await ctx.send('Der er ingen pauset sang.')

# Kommando til at tilføje en hel YouTube-playliste til køen
@bot.command(name='playlist')
async def add_playlist(ctx, playlist_url: str):
    video_urls = extract_playlist_videos(playlist_url)
    if not video_urls:
        await ctx.send('Ingen videoer fundet i playlisten.')
        return

    for url in video_urls:
        video_queue.put(url)
        print(f"Tilføjet til køen: {url}")

    await ctx.send(f'Tilføjet {len(video_urls)} videoer til køen.')
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await play_next_song(ctx)

# Funktion til at hente video URLs fra en YouTube playliste
def extract_playlist_videos(url):
    ydl_opts = {
        'extract_flat': True,
        'dump_single_json': True,
        'quiet': True,
    }

    def get_video_urls(info_dict):
        if 'entries' not in info_dict:
            return []
        return ['https://www.youtube.com/watch?v=' + entry['id'] for entry in info_dict['entries'] if entry and 'id' in entry]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_urls = get_video_urls(info_dict)
            if video_urls:
                return video_urls
            else:
                print("Ingen videoer fundet med første metode, prøver anden metode...")
                # Forsøg anden metode
                ydl_opts['extract_flat'] = False
                info_dict = ydl.extract_info(url, download=False)
                return get_video_urls(info_dict)
    except Exception as e:
        print(f"Fejl ved hentning af playliste: {e}")
        return []

# Event handler for når botten tilslutter sig en server
@bot.event
async def on_ready():
    print(f'{bot.user} har tilsluttet sig!')

# Start botten med din token
bot.run(' Discord token skal være her / token here ')
