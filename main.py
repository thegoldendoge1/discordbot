import requests
from bs4 import BeautifulSoup
import utils
import discord
from discord.ext import commands
import os
import settings
import random
from yt_dlp import YoutubeDL
import asyncio
import csv
import json

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix='>', intents=intents)


@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    utils.log(f'Successfully logged in as {bot.user}')
    utils.log(f'synced {len(synced)} command(s)')


@bot.event
async def on_member_join(member):
    # TODO добавить отправление рандомной картинки в приветствии
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


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.tree.command(name='lastfm', description='Информация о скробблах пользователя last.fm')
async def get_scrobbles(interaction: discord.Interaction, user: str):
    await interaction.response.defer()
    url = f'https://www.last.fm/user/{user}'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, features='html.parser')

    # Попытка получения информации и обработка возможных исключений
    try:
        # Получение количества скробблов
        try:
            scrobbles_element = soup.find('div', class_='header-metadata-display').find('a')
            scrobbles = scrobbles_element.text if scrobbles_element else 'Не удалось получить информацию о прослушиваниях'
        except AttributeError:
            scrobbles = 'Не удалось получить информацию о прослушиваниях'

        # Получение информации о треках
        try:
            tracks = soup.find_all('tr', class_='chartlist-row')
            if not tracks:
                raise AttributeError
        except AttributeError:
            tracks = 'Не удалось получить информацию о треках'

        try:
            avatar_url = soup.find('div', class_='header-avatar').find('img')['src']
        except AttributeError:
            avatar_url = None

        try:
            current_top_track = soup.find('a', 'featured-item-name').text
        except AttributeError:
            current_top_track = 'Не удалось получить информацию'

        try:
            current_top_executor = soup.find('a', 'featured-item-artist').text
        except AttributeError:
            current_top_executor = 'Не удалось получить информацию'

        # Получение последних скробблов
        recent_scrobbles = []
        for track in tracks[:5]:  # Получить только последние 5 скробблов
            try:
                track_info = track.find('td', class_='chartlist-name').get_text(strip=True)
                artist = track.find('td', class_='chartlist-artist').get_text(strip=True)
                time = track.find('td', class_='chartlist-timestamp').get_text(strip=True)
                recent_scrobbles.append(f'**{artist}** - {track_info} ({time})')
            except AttributeError:
                continue

        # Создание встроенного сообщения (embed)
        embed = discord.Embed(title=f'Информация о скробблах пользователя {user}',
                              color=discord.Color.blue())

        if current_top_track != 'Не удалось получить информацию' and current_top_executor != 'Не удалось получить информацию':
            embed.description = f'Количество прослушиваний на Last.fm: **{scrobbles}**\nТоп композиция: **{current_top_executor}** - {current_top_track}'
        elif current_top_track == 'Не удалось получить информацию' and current_top_executor != 'Не удалось получить информацию':
            embed.description = f'Количество прослушиваний на Last.fm: **{scrobbles}**\nТоп исполнитель: **{current_top_executor}**'
        elif current_top_track != 'Не удалось получить информацию' and current_top_executor == 'Не удалось получить информацию':
            embed.description = f'Количество прослушиваний на Last.fm: **{scrobbles}**\nТоп композиция: **{current_top_track}**'
        else:
            embed.description = f'Количество прослушиваний на Last.fm: **{scrobbles}**\nНе удалось получить информацию о топ композиции'

        if avatar_url:
            embed.set_thumbnail(url=avatar_url)

        embed.add_field(name='Последние скробблы:',
                        value='\n'.join(recent_scrobbles) if recent_scrobbles else 'Нет данных', inline=False)

        # Отправка встроенного сообщения (embed)
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(f'Произошла ошибка: {e}')


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


voice_client = None


@bot.tree.command(name='play', description='Проиграть трек по ссылке')
async def connect_to_voice_channel(interaction: discord.Interaction, url: str):
    global voice_client
    if interaction.user.voice:
        await interaction.response.defer()
        track_info = await get_audio_from_link(url)
        # Присваивание значений из url
        if track_info:
            track_url = track_info.get('url')
            track_title = track_info.get('fulltitle')
            track_thumbnail = track_info.get('thumbnail')
            track_duration = utils.format_duration(track_info.get('duration'))

        # Подключение к голосовому каналу
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client:
            await interaction.followup.send('Бот уже подключен к голосовому каналу на этом сервере')
        else:
            voice_client = await channel.connect(reconnect=True)

        # Воспроизведение трека
        ffmpeg_options = {
            'options': '-vn',
            'before_options': '-reconnect 5 -reconnect_streamed 5 -reconnect_delay_max 5',
            'format': 'mp3',
            'ar': 48000,
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


@bot.tree.command(name='pause', description='Поставить на паузу текущий трек (Чтобы убрать паузу, пропишите команду '
                                            'повторно')
async def pause_current_track(interaction: discord.Interaction):
    global voice_client
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message('Трек поставлен на паузу')
        await asyncio.sleep(10)
        await interaction.delete_original_response()
    elif voice_client and voice_client.is_paused:
        voice_client.resume()
        await interaction.response.send_message('Трек снят с паузы')
        await asyncio.sleep(10)
        await interaction.delete_original_response()
    else:
        await interaction.response.send_message('Сейчас ничего не играет')


@bot.event
async def on_message(message):
    server_id = message.guild.id
    user_id = f'{message.author.id}'
    filename = f"./ranks/{server_id}.json"
    try:
        file = open(filename, 'r+')
    except IOError:
        file = open(filename, 'w+')
    with open(filename, "r+", encoding="utf-8") as file:
        try:
            user_data = json.load(file)
        except:
            user_data = {}
    if user_id in user_data:
        user_data[user_id] += 1
        utils.log(f"XP user {user_id} + 1!")
    else:
        utils.log(f"New user {user_id} added!")
        user_data[user_id] = 1

    with open(filename, "w+", encoding="utf-8") as file:
        json.dump(user_data, file)

    await bot.process_commands(message)


@bot.tree.command(name='leaderboard', description='Лидерборд активных участников')
async def leaderboard(interaction: discord.Interaction):
    # TODO: починить сортировку
    server_id = interaction.guild.id
    filename = f"./ranks/{server_id}.json"
    leaderboard_data = []
    try:
        file = open(filename, 'r+')
    except IOError:
        file = open(filename, 'w+')
    with open(filename, "r+", encoding="utf-8") as file:
        try:
            user_data = json.load(file)
            for user in user_data:
                user_id = bot.get_user(int(user))
                xp = user_data[user]
                leaderboard_data.append(f"**{user_id.name}** - {xp} xp")
            leaderboard_data.sort()
            embed = discord.Embed(title='Лидерборд активных участников',
                                  description='\n'.join(leaderboard_data),
                                  colour=discord.Color.blue())
            await interaction.response.send_message(embed=embed)
        except:
            embed = discord.Embed(title='Лидерборд активных участников',
                                  description='Лидерборд пока пуст :(',
                                  colour=discord.Color.blue())
            await interaction.response.send_message(embed=embed)


bot.run(os.getenv('TOKEN'))
