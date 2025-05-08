import discord
from discord.ext import tasks, commands
from discord import Option
import json
import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import openai

load_dotenv()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = discord.app_commands.CommandTree(bot)

openai.api_key = os.getenv("Clave_OpenAI")  # Asegúrar de tener esta clave en mi archivo .env

# --- Crear Embed Estilizado ---
def crear_embed(titulo, descripcion, color=discord.Color.red()):
    embed = discord.Embed(title=titulo, description=descripcion, color=color)
    embed.set_footer(text="YiBot v1.0 | Tu dictador favorito")
    return embed

# --- Carga de Muted JSON ---
def cargar_muted():
    try:
        with open("muted.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def guardar_muted(muted_data):
    with open("muted.json", "w") as f:
        json.dump(muted_data, f, indent=4)

muted = cargar_muted()

# --- Auto-Unmute Task ---
@tasks.loop(minutes=1)
async def verificar_muteos():
    ahora = datetime.utcnow()
    cambios = False

    for guild_id, usuarios in list(muted.items()):
        for user_id, data in list(usuarios.items()):
            tiempo_final = datetime.strptime(data["finaliza"], "%Y-%m-%d %H:%M:%S")
            if ahora >= tiempo_final:
                guild = bot.get_guild(int(guild_id))
                miembro = guild.get_member(int(user_id))
                if miembro:
                    rol = discord.utils.get(guild.roles, name="Silenciado")
                    if rol in miembro.roles:
                        await miembro.remove_roles(rol)
                        print(f"Auto-desmuteado: {miembro}")
                del muted[guild_id][user_id]
                cambios = True

        if not muted[guild_id]:
            del muted[guild_id]

    if cambios:
        guardar_muted(muted)

# --- Evento On Ready ---
@bot.event
async def on_ready():
    await tree.sync()
    print(f"{bot.user} está en línea.")
    canal_inicio = discord.utils.get(bot.get_all_channels(), name="general")
    if canal_inicio:
        embed = crear_embed("YiBot listo", "Preparado para juzgar tus acciones.")
        await canal_inicio.send(embed=embed)
    verificar_muteos.start()

# --- Anti-Spam + Mención a YiBot (IA) ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Anti-Spam
    if "http://" in message.content.lower() or "https://" in message.content.lower():
        if not message.author.guild_permissions.manage_messages:
            await message.delete()
            embed = crear_embed("¡Publicidad no permitida!", f"{message.author.mention}, ¿creías que no me daría cuenta?")
            await message.channel.send(embed=embed, delete_after=5)
            return

    # Respuesta con IA si se menciona al bot
    if bot.user.mentioned_in(message):
        prompt = f"{message.author.name} dijo: {message.content}\nYiBot, responde con sarcasmo:"
        try:
            respuesta = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres YiBot, un bot sarcástico, frío pero útil."},
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

# --- Slash Command: /info ---
@tree.command(name="info", description="Muestra información sobre YiBot")
async def slash_info(interaction: discord.Interaction):
    embed = crear_embed("Información del Bot", "Soy YiBot, moderador, sarcástico y absolutamente necesario.")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    await interaction.response.send_message(embed=embed)

# --- Slash Command: /regla ---
@tree.command(name="regla", description="Muestra una regla o todas las reglas del servidor")
async def slash_regla(interaction: discord.Interaction, numero: Option(int, "Número de la regla", required=False)):
    reglas = {
        1: "No hacer spam. Me aburres.",
        2: "Nada de contenido NSFW. Este no es ese tipo de lugar.",
        3: "Respeta a los demás... aunque tú no te respetes.",
        4: "Prohibido hacer publicidad sin permiso. Este no es tu patio."
    }
    if numero is None:
        embed = crear_embed("Lista de Reglas", "\n".join([f"{n}. {r}" for n, r in reglas.items()]))
    else:
        regla = reglas.get(numero, "Esa regla no existe. ¿Intentas crear caos?")
        embed = crear_embed(f"Regla {numero}", regla)
    await interaction.response.send_message(embed=embed)

# --- Slash Command: /limpiar ---
@tree.command(name="limpiar", description="Elimina mensajes del canal")
async def slash_limpiar(interaction: discord.Interaction, cantidad: Option(int, "Cantidad de mensajes", min_value=1, max_value=100)):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("No puedes usar esto. Eres irrelevante.", ephemeral=True)
        return
    await interaction.channel.purge(limit=cantidad + 1)
    embed = crear_embed("Chat purgado", f"{cantidad} mensajes eliminados por {interaction.user.mention}.")
    msg = await interaction.channel.send(embed=embed)
    await asyncio.sleep(3)
    await msg.delete()
    await interaction.response.send_message("Mensajes eliminados.", ephemeral=True)

# --- Iniciar bot ---
bot.run(os.getenv("Clave_Token"))
