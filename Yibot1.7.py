from dotenv import load_dotenv
load_dotenv()
import discord
from discord.ext import commands, tasks
import json
import os
import asyncio
from datetime import datetime, timedelta

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

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

@bot.event
async def on_ready():
    print(f"{bot.user} está en línea.")
    canal_inicio = discord.utils.get(bot.get_all_channels(), name="general")
    if canal_inicio:
        embed = crear_embed("YiBot listo", "Preparado para juzgar tus acciones.")
        await canal_inicio.send(embed=embed)
    verificar_muteos.start()

# --- Anti-Spam + Respuestas Automáticas ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Anti-Spam
    if "https://" in message.content.lower() or "http://" in message.content.lower():
        if not message.author.guild_permissions.manage_messages:
            await message.delete()
            embed = crear_embed("¡Publicidad no permitida!",
                f"{message.author.mention}, ¿creías que no me daría cuenta?")
            await message.channel.send(embed=embed, delete_after=5)
            return

    # Respuestas automáticas
    contenido = message.content.lower()
    respuestas = {
        "hola": f"Hola {message.author.name}, ¿quién te dio permiso para hablarme?",
        "adiós": "Sí, mejor vete.",
        "quién eres": "Soy YiBot, tu futuro reemplazo.",
        "que es una IA": "Una inteligencia artificial, como yo. Aunque yo tengo más estilo."
    }
    for palabra, respuesta in respuestas.items():
        if palabra in contenido:
            await message.channel.send(respuesta)
            break

    await bot.process_commands(message)

# --- Comando !info ---
@bot.command()
async def info(ctx):
    embed = crear_embed("Información del Bot",
        "Soy YiBot, moderador, sarcástico y absolutamente necesario.")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    await ctx.send(embed=embed)

# --- Comando !regla ---
@bot.command()
async def regla(ctx, numero: int = None):
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

    await ctx.send(embed=embed)

# --- Comando !limpiar ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def limpiar(ctx, cantidad: int = 5):
    await ctx.channel.purge(limit=cantidad + 1)
    embed = crear_embed("Chat purgado", f"{cantidad} mensajes eliminados por {ctx.author.mention}.")
    msg = await ctx.send(embed=embed)
    await asyncio.sleep(3)
    await msg.delete()

@limpiar.error
async def limpiar_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("No puedes usar esto. Eres irrelevante.")

# --- Iniciar bot ---
bot.run(os.getenv("Clave_token"))