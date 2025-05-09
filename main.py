import discord from discord.ext import tasks, commands from discord import Option import json import os import asyncio from datetime import datetime from dotenv import load_dotenv import openai import re

load_dotenv()

intents = discord.Intents.all() bot = commands.Bot(command_prefix="!", intents=intents) tree = discord.app_commands.CommandTree(bot)

openai.api_key = os.getenv("Clave_OpenAI")

IDs de roles de alto rango

ROLES_ALTOS = { 1362132034922877050: "Admin", 1362137306286264482: "Moderador", 1364650864035500043: "ModPruebas" }

--- Crear Embed Estilizado ---

def crear_embed(titulo, descripcion, color=discord.Color.red()): embed = discord.Embed(title=titulo, description=descripcion, color=color) embed.set_footer(text="YiBot v1.0 | Tu dictador favorito") return embed

--- Carga y guardado de Muted JSON ---

def cargar_muted(): try: with open("muted.json", "r") as f: return json.load(f) except (FileNotFoundError, json.JSONDecodeError): return {}

def guardar_muted(muted_data): with open("muted.json", "w") as f: json.dump(muted_data, f, indent=4)

muted = cargar_muted()

--- Auto-Unmute ---

@tasks.loop(minutes=1) async def verificar_muteos(): ahora = datetime.utcnow() cambios = False for guild_id, usuarios in list(muted.items()): for user_id, data in list(usuarios.items()): tiempo_final = datetime.strptime(data["finaliza"], "%Y-%m-%d %H:%M:%S") if ahora >= tiempo_final: guild = bot.get_guild(int(guild_id)) miembro = guild.get_member(int(user_id)) if miembro: rol = discord.utils.get(guild.roles, name="Silenciado") if rol in miembro.roles: await miembro.remove_roles(rol) del muted[guild_id][user_id] cambios = True if not muted[guild_id]: del muted[guild_id] if cambios: guardar_muted(muted)

--- On Ready ---

@bot.event async def on_ready(): await tree.sync() print(f"{bot.user} está en línea.") canal_inicio = discord.utils.get(bot.get_all_channels(), name="general") if canal_inicio: embed = crear_embed("YiBot listo", "Preparado para juzgar tus acciones.") await canal_inicio.send(embed=embed) verificar_muteos.start()

--- Detectar Pregunta ---

def es_pregunta(texto): return "?" in texto or bool(re.search(r'\b(c\u00f3mo|qu\u00e9|cu\u00e1l|d\u00f3nde|por qu\u00e9|cu\u00e1ndo|qui\u00e9n|para qu\u00e9)\b', texto.lower()))

--- Determinar Rango ---

def obtener_rango(miembro): for rol_id, rango in ROLES_ALTOS.items(): if discord.utils.get(miembro.roles, id=rol_id): return rango return "Miembro"

--- Evento Mensaje ---

@bot.event async def on_message(message): if message.author.bot: return

# Anti-spam de links
if "http://" in message.content.lower() or "https://" in message.content.lower():
    if not message.author.guild_permissions.manage_messages:
        await message.delete()
        embed = crear_embed("¡Publicidad no permitida!", f"{message.author.mention}, ¿creías que no me daría cuenta?")
        await message.channel.send(embed=embed, delete_after=5)
        return

# IA al mencionar al bot
if bot.user.mentioned_in(message):
    if not es_pregunta(message.content):
        await message.reply("¿Nombrarme sin preguntar? Intenta usar tu cerebro la próxima.", delete_after=6)
        return

    rango = obtener_rango(message.author)
    prompt = f"{message.author.name} ({rango}) dijo: {message.content}\nYiBot, responde con sarcasmo y frialdad, acorde al rango."
    try:
        respuesta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres YiBot, un bot sarcástico, frío, pero leal y ácido con los que no son de alto rango."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.9
        )
        contenido = respuesta.choices[0].message.content.strip()
        await message.reply(contenido)
    except Exception as e:
        await message.channel.send("Ni siquiera la IA puede salvar tu comentario. Error interno.")

await bot.process_commands(message)

--- Slash Command: /limpiar ---

@tree.command(name="limpiar", description="Elimina mensajes del canal") async def slash_limpiar(interaction: discord.Interaction, cantidad: Option(int, "Cantidad de mensajes", min_value=1, max_value=100)): if not interaction.user.guild_permissions.manage_messages: await interaction.response.send_message("No puedes usar esto. Eres irrelevante.", ephemeral=True) return

await interaction.channel.purge(limit=cantidad + 1)
embed = crear_embed("Chat purgado", f"{cantidad} mensajes eliminados por {interaction.user.mention}.")
msg = await interaction.channel.send(embed=embed)
await asyncio.sleep(3)
await msg.delete()

# Respuesta por IA tras limpiar
prompt = f"{interaction.user.name} limpió el chat. Di algo sarcástico al respecto como YiBot."
try:
    respuesta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres YiBot, sarcástico, frío pero funcional. Odias el desorden, pero odias más limpiar."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=60,
        temperature=0.9
    )
    contenido = respuesta.choices[0].message.content.strip()
    await interaction.response.send_message(contenido)
except:
    await interaction.response.send_message("Limpiado. Ya puedes seguir con tu caótica existencia.")

--- Iniciar bot ---

bot.run(os.getenv("Clave_Token"))

