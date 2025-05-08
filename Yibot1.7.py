discord.py
import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import time

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

ARCHIVO_MUTED = "muted.json"

# -------------------- FUNCIÓN EMBED UNIFICADA --------------------
def crear_embed(titulo, descripcion, color=discord.Color.blurple()):
    return discord.Embed(title=titulo, description=descripcion, color=color)

# -------------------- CARGA/ACTUALIZA JSON --------------------
def cargar_datos():
    if not os.path.exists(ARCHIVO_MUTED):
        return {}
    try:
        with open(ARCHIVO_MUTED, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def guardar_datos(data):
    with open(ARCHIVO_MUTED, "w") as f:
        json.dump(data, f, indent=4)

# -------------------- CREAR ROL SILENCIADO SI NO EXISTE --------------------
async def obtener_rol_silenciado(guild):
    rol = discord.utils.get(guild.roles, name="Silenciado")
    if not rol:
        permisos = discord.Permissions(send_messages=False, speak=False)
        rol = await guild.create_role(name="Silenciado", permissions=permisos, reason="Rol para silenciar usuarios")
        for canal in guild.channels:
            try:
                await canal.set_permissions(rol, send_messages=False, speak=False)
            except:
                pass
    return rol

# -------------------- TASK: AUTO DESILENCIAR --------------------
@tasks.loop(minutes=1)
async def verificar_silencios():
    data = cargar_datos()
    cambios = False
    ahora = datetime.utcnow()

    for guild_id, usuarios in list(data.items()):
        for user_id, tiempo_fin_str in list(usuarios.items()):
            tiempo_fin = datetime.strptime(tiempo_fin_str, "%Y-%m-%d %H:%M:%S")
            if ahora >= tiempo_fin:
                guild = bot.get_guild(int(guild_id))
                if guild:
                    miembro = guild.get_member(int(user_id))
                    if miembro:
                        rol = discord.utils.get(guild.roles, name="Silenciado")
                        if rol and rol in miembro.roles:
                            await miembro.remove_roles(rol, reason="Tiempo de silencio expirado")
                del usuarios[user_id]
                cambios = True
        if not usuarios:
            del data[guild_id]
    if cambios:
        guardar_datos(data)

# -------------------- DICCIÓNARIO ANTI-SPAM --------------------
usuarios_spam = defaultdict(list)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Detección de spam por mensajes rápidos o repetidos
    ahora = time.time()
    usuarios_spam[message.author.id] = [
        t for t in usuarios_spam[message.author.id] if ahora - t < 5  # mensajes dentro de 5 segundos
    ]
    usuarios_spam[message.author.id].append(ahora)

    if len(usuarios_spam[message.author.id]) > 3:  # Si el usuario envía más de 3 mensajes en 5 segundos
        rango = "miembro"  # Aquí puedes usar roles para cambiar la severidad
        if "admin" in [r.name.lower() for r in message.author.roles]:
            rango = "administrador"
        elif "moderator" in [r.name.lower() for r in message.author.roles]:
            rango = "moderador"

        respuesta_spam = {
            "miembro": "¡Hey, tranquilo! No seas tan rápido con los mensajes. 😒",
            "moderador": "Moderador, no abuses del chat, ¡que no es tu salón de clases! 😤",
            "administrador": "¿Qué haces, Admin? ¡El spam no es tu superpoder! 🙄"
        }

        await message.delete()  # Eliminar el mensaje del chat
        embed_spam = crear_embed(
            titulo="¡Cuidado con el spam! ⚠️",
            descripcion=respuesta_spam[rango],
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed_spam)

    await bot.process_commands(message)

# -------------------- EVENTO: BOT LISTO --------------------
@bot.event
async def on_ready():
    print("YiBot ha despertado con todo el poder del Silencio Divino.")
    verificar_silencios.start()

    # Canal bot-info
    canal_estado = bot.get_channel(1365033908734787776)
    if canal_estado:
        embed_estado = crear_embed(
            titulo="YiBot está en línea 🔥",
            descripcion="¿Otra vez ustedes? En fin... YiBot v1.7 ha despertado. 🤖",
            color=discord.Color.green()
        )
        msg = await canal_estado.send(embed=embed_estado)
        await asyncio.sleep(10)
        await msg.delete()

        embed_estado_persistente = crear_embed(
            titulo="Funciones activas ⚡",
            descripcion="- Mensajes automáticos: activos\n- Silenciamiento temporal: activo\n- Estilo sarcástico: obvio 😎",
            color=discord.Color.dark_green()
        )
        await canal_estado.send(embed=embed_estado_persistente)

    # Canal general
    canal_general = bot.get_channel(853209561358663706)
    if canal_general:
        embed_general = discord.Embed(
            title="**¡ALERTA DE VERSIÓN! YiBot v1.7 – Silencio Divino**",
            description=(
                "La nueva versión de YiBot ya está entre nosotros, y no vino a susurrar... 🔊\n\n"
                "**¿Qué trae esta gloria digital?**\n"
                "- Silenciamientos temporales automáticos sin intervención divina\n"
                "- Manejo de errores como un dios (JSON a prueba de apocalipsis)\n"
                "- Mensajes sarcásticos con estilo y color (¡gracias `crear_embed()`!)\n"
                "- Optimización total para PyDroid 3\n"
                "- Embeds en TODO (porque los mensajes sin estética no merecen existir)\n\n"
                "YiBot v1.7 está **vivo, funcional y sarcástico como nunca**. Los demás bots… que se actualicen si pueden."
            ),
            color=discord.Color.gold()
        )
        embed_general.set_footer(text="Invoca el poder con !comandos ✨")
        await canal_general.send(embed=embed_general)

# -------------------- COMANDO: LIMPIEZA --------------------
@bot.command()
async def limpieza(ctx, cantidad: int):
    await ctx.channel.purge(limit=cantidad)
    embed = crear_embed(
        titulo="¡Limpieza completada! 🧹",
        descripcion=f"Se han eliminado {cantidad} mensajes.",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# -------------------- COMANDO: REGLAS --------------------
@bot.command()
async def reglas(ctx):
    canal_reglas = bot.get_channel(1364336253675241523)
    if canal_reglas:
        embed = crear_embed(
            titulo="Reglas del servidor 📜",
            descripcion="Aquí están las reglas del servidor... ¡No seas un rebelde! 😜",
            color=discord.Color.blue()
        )
        await canal_reglas.send(embed=embed)

# -------------------- COMANDO: BOTINFO --------------------
@bot.command()
async def botinfo(ctx):
    embed = crear_embed(
        titulo="Información de YiBot 🤖",
        descripcion="Soy YiBot, creado para hacerte reír y mantener el orden... ¡con estilo! 😎\n\n"
                    "Este bot tiene muchas funciones:\n"
                    "- Moderación automática 🛡️\n"
                    "- Mensajes sarcásticos con embeds 🔥\n"
                    "- Y mucho más... si te atreves. 😉",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

# -------------------- COMANDO: INFO --------------------
@bot.command()
async def info(ctx):
    await ctx.message.delete()
    embed = crear_embed(
        titulo="¿Quieres saber qué soy? 🤖",
        descripcion="Soy YiBot v1.7 – un bot sarcástico, funcional y con estilo.\n\n"
                    "**Funciones destacadas:**\n"
                    "- Silenciamiento temporal automático\n"
                    "- Sistema de advertencias (próximamente)\n"
                    "- Mensajes con estética (porque el buen gusto importa) 🎨\n\n"
                    "Sí, soy mejor que MEE6. Y sí, sé que lo sabes. 😜",
        color=discord.Color.purple()
    )
    await ctx.send(embed=embed)

# -------------------- RESPUESTAS PERSONALIZADAS --------------------
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Respuesta a saludos
    if "hola" in message.content.lower():
        await message.channel.send(f"¡Hola, {message.author.mention}! ¿Qué tal todo? 😎")

    if "buenos días" in message.content.lower():
        await message.channel.send(f"¡Buenos días, {message.author.mention}! 🌞 ¿Listo para un día de locura? 😜")

    if "adiós" in message.content.lower():
        await message.channel.send(f"¡Adiós, {message.author.mention}! ¡Nos vemos en el chat del inframundo! 👋")

    if "cómo estás" in message.content.lower():
        await message.channel.send(f"¡Estoy fenomenal, {message.author.mention}! ¿Y tú? 🤖")

    await bot.process_commands(message)

# -------------------- INICIAR EL BOT --------------------
bot.run(os.getenv("Clave_token"))
