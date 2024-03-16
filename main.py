import requests
from bs4 import BeautifulSoup
import func
import discord
from discord.ext import commands
import os
import settings
import random
from yt_dlp import YoutubeDL
from time import sleep
import aiohttp

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='>', intents=intents)


@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    func.log(f'Successfully logged in as {bot.user}')
    func.log(f'synced {len(synced)} command(s)')


@bot.event
async def on_member_join(member):
    welcome_channel_id = 888701342447718420
    welcome_channel = bot.get_channel(welcome_channel_id)
    embed = discord.Embed(title=f'Добро пожаловать, {member}',
                          description=f'Мы рады видеть вас на сервере {member.guild}',
                          colour=8811470)
    embed.set_image(url='https://i.pinimg.com/564x/f3/3a/b6/f33ab6078d8a72c1b2ce6db1e07ff2e0.jpg')
    embed.set_footer(text=member, icon_url=member.avatar)
    if welcome_channel:
        await welcome_channel.send(embed=embed)

# Тестирование присоединения участника к серверу
# @bot.command()
# async def test_join(ctx):
#     guild_id = 858605598856577065
#     member_id = 325551692592709632
#     guild = bot.get_guild(guild_id)
#     member = guild.get_member(member_id)
#     await on_member_join(member)

# TODO: сделать проверку на каждый реквест (если например у пользователя нет топ трека то будет ошибка)


@bot.tree.command(name='lastfm', description='Информация о скробблах пользователя last.fm')
async def get_scrobbles(interaction: discord.Interaction, user: str):
    await interaction.response.defer()
    url = f'https://www.last.fm/user/{user}'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, features='html.parser')

    try:
        # Получение количества скробблов
        scrobbles_element = soup.find('div', class_='header-metadata-display').find('a')
        if scrobbles_element.text:
            scrobbles = scrobbles_element.text
        else:
            scrobbles = 'Неудалось получить информацию о прослушиваниях'
        # Получение информации с last.fm
        tracks = soup.find_all('tr', class_='chartlist-row')
        avatar_url = soup.find('div', class_='header-avatar').find('img')['src']
        current_top_track = soup.find('a', 'featured-item-name')
        current_top_executor = soup.find('a', 'featured-item-artist')
        recent_scrobbles = []
        for track in tracks[:5]:  # Получить только последние 5 скробблов
            track_info = track.find('td', class_='chartlist-name').get_text(strip=True)
            artist = track.find('td', class_='chartlist-artist').get_text(strip=True)
            time = track.find('td', class_='chartlist-timestamp').get_text(strip=True)
            recent_scrobbles.append(f'**{artist}** - {track_info} ({time})')

        # Создание встроенного сообщения (embed)
        embed = discord.Embed(title=f'Информация о скробблах пользователя {user}',
                      description=f'Количество прослушиваний на Last.fm: **{scrobbles}**\n'
                                  f'Топ композиция: **{current_top_executor.text}** - {current_top_track.text}',
                      color=discord.Color.blue())
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name='Последние скробблы:', value='\n'.join(recent_scrobbles), inline=False)

        # Отправка встроенного сообщения (embed)
        await interaction.followup.send(embed=embed)

    except AttributeError:
        await interaction.followup.send('Error: AttrubuteError')




@bot.tree.command(name='roll',
                  description='Сгенерировать рандомное число в указанном промежутке. Пример использования: /roll 0-100')
async def random_digit(interaction: discord.Interaction, range: str):
    try:
        list_of_range = range.split('-')
        if len(list_of_range) == 2:
            random_choise = random.randint(int(list_of_range[0]), int(list_of_range[1]))
            await interaction.response.send_message(f'Рандомное число из диапозона {range}: **{random_choise}**')
        else:
            await interaction.response.send_message(
                "Неправильный синтаксис команды. Введите диапазон в формате **['Число'-'Число']**\n"
                "Например: **0-100**\n")

    except Exception as e:
        await interaction.response.send_message(
            "Неправильный синтаксис команды. Введите диапазон в формате **['Число'-'Число']**\n"
            "Например: **0-100**\n"
            "\n"
            f"Ошибка: {e}")


@bot.tree.command(name='random_choice', description='Перечислите через запятую список элементов для выбора')
async def random_choice_from_list(interaction: discord.Interaction, list: str):
    string_without_spaces = list.replace(' ', '')
    converted_list = string_without_spaces.split(',')
    await interaction.response.send_message(f'Рандомный элемент из списка: **{random.choice(converted_list)}**')


async def get_audio_from_link(url: str):
    ydl_options = {
        'format': 'bestaudio/best',
    }

    with YoutubeDL(ydl_options) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'url' in info:
            return info
        else:
            return None

# TODO: сделать проверку на уже подключенного бота к серверу


@bot.tree.command(name='play', description='Проиграть трек по ссылке')
async def connect_to_voice_channel(interaction: discord.Interaction, url: str):
    voice_client = None
    if interaction.user.voice:
        await interaction.response.defer()
        track_info = await get_audio_from_link(url)
        # Присваивание значений из url
        if track_info:
            track_url = track_info.get('url')
            track_title = track_info.get('fulltitle')
            track_thumbnail = track_info.get('thumbnail')
            track_duration = func.format_duration(track_info.get('duration'))

        # Подключение к голосовому каналу
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client:
            await interaction.followup.send('Бот уже подключен к голосовому каналу на этом сервере')
        else:
            voice_client = await channel.connect(reconnect=True)

        # Воспроизведение трека
        ffmpeg_options = {
            'options': '-vn',
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'format': 'flac',  # Использование формата без потерь
            'ar': 48000,  # Увеличение частоты дискретизации
            'ac': 2
        }

        if voice_client and voice_client.is_playing():
            await interaction.followup.send('Трек уже играет')
        else:
            ffmpeg_class = discord.FFmpegPCMAudio(source=track_url, executable='./ffmpeg/bin/ffmpeg.exe',
                                                  options=ffmpeg_options)
            voice_client.play(ffmpeg_class)
            is_playing_now = True

            embed = discord.Embed(description=f'**{track_title}**\n'
                                          f'Длительность: {track_duration}')
            embed.set_author(name='Сейчас играет:')
            embed.set_thumbnail(url=track_thumbnail)
            await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(description='**Вы не находитесь в голосовом канале**')
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name='pause', description='Поставить на паузу воспроизведение текущего трека')
async def pause_current_track(interaction: discord.Interaction):
    pass


bot.run(os.getenv('TOKEN'))
