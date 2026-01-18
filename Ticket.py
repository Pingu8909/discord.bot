import discord
from discord.ext import commands

# ========== INTENTS ==========
intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ========== CONFIG ==========
TOKEN = "TOKEN_BOT"

FOUNDER_ROLE_ID = 1422244306743328768
STAFF_ROLE_ID = 1431350167814275082

CATEGORY_ASSISTENZA = 1450802434556297328
CATEGORY_SEGNALAZIONE = 1450804077482213378
CATEGORY_VERTICI = 1450802747199721524
CATEGORY_TRASFERIMENTO = 1450803146355118153

LOG_CHANNEL_ID = 1450802298593738894
LOGO_URL = "https://link-logo.png"

# ========== READY ==========
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online come {bot.user}")

# ========== BOTTONI TICKET PUBBLICI ==========
class ConfirmCloseTicket(discord.ui.View):
    def __init__(self, ticket_user: discord.Member):
        super().__init__(timeout=60)
        self.ticket_user = ticket_user

    @discord.ui.button(label="✅ Accetta", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        embed_log = discord.Embed(
            title="📄 Ticket Chiuso",
            color=0xe74c3c
        )
        embed_log.add_field(name="👤 Chiuso da", value=interaction.user.mention, inline=False)
        embed_log.add_field(name="📁 Canale", value=interaction.channel.name, inline=False)
        embed_log.set_footer(text="Sistema Ticket • Rimini RP")
        if log_channel:
            await log_channel.send(embed=embed_log)

        embed_public = discord.Embed(
            title="🔒 Ticket Chiuso",
            description=f"Il ticket è stato chiuso da {interaction.user.mention}",
            color=0xe74c3c
        )
        await interaction.channel.send(embed=embed_public)

        try:
            await self.ticket_user.send(f"📌 Il tuo ticket `{interaction.channel.name}` è stato chiuso.")
        except:
            pass

        await interaction.channel.delete()

    @discord.ui.button(label="❌ Annulla", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
        await interaction.channel.send("❌ Chiusura annullata, il ticket rimane aperto.")

class TicketButtons(discord.ui.View):
    def __init__(self, ticket_user: discord.Member):
        super().__init__(timeout=None)
        self.ticket_user = ticket_user
        self.ping_count = 0  # limite ping staff per ticket

    @discord.ui.button(label=" Prendi in carico", style=discord.ButtonStyle.primary, emoji="✅")
    async def take_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔹 Ticket in gestione",
            description=f"{interaction.user.mention} sta gestendo questo ticket.",
            color=0x2ecc71
        )
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label=" Trasferisci", style=discord.ButtonStyle.secondary, emoji="🔁")
    async def transfer_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        gestionale_category = interaction.guild.get_channel(CATEGORY_TRASFERIMENTO)
        await interaction.channel.edit(category=gestionale_category)
        embed = discord.Embed(
            title="🔁 Ticket Trasferito",
            description=f"{interaction.user.mention} ha trasferito il ticket nella categoria gestionale.",
            color=0xf1c40f
        )
        await interaction.channel.send(embed=embed)

    @discord.ui.button(label=" Ping Staff", style=discord.ButtonStyle.secondary, emoji="📣")
    
    async def ping_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ping_count >= 2:
            await interaction.response.send_message("❌ Limite di ping allo staff raggiunto (2 per ticket).", ephemeral=True)
            return
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        await interaction.channel.send(f"{staff_role.mention} 📣 Assistenza richiesta!")
        self.ping_count += 1
        await interaction.response.send_message(f"✅ Ping inviato ({self.ping_count}/2)", ephemeral=True)

    @discord.ui.button(label=" Chiudi Ticket", style=discord.ButtonStyle.danger, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_confirm = discord.Embed(
            title="⚠️ Conferma Chiusura Ticket",
            description="Clicca ✅ per confermare la chiusura del ticket.",
            color=0xe74c3c
        )
        await interaction.response.send_message(embed=embed_confirm, view=ConfirmCloseTicket(self.ticket_user), ephemeral=False)

# ========== MENU TICKET ==========
class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Assistenza Generale", value="assistenza", emoji="🛠", description="Problemi di gioco, comandi, cittadinanza"),
            discord.SelectOption(label="Segnalazione", value="segnalazione", emoji="🚫", description="Segnalazioni con prove"),
            discord.SelectOption(label="Amministrazione", value="amministrazione", emoji="⚠️", description="Solo per questioni serie"),
            discord.SelectOption(label="Richiesta Partner", value="partnership", emoji="🤝", description="Richiesta partnership"),
        ]
        super().__init__(placeholder="📂 Seleziona una categoria", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        mapping = {
            "assistenza": (CATEGORY_ASSISTENZA, "assistenza"),
            "segnalazione": (CATEGORY_SEGNALAZIONE, "segnalazione"),
            "amministrazione": (CATEGORY_VERTICI, "amministrazione"),
            "partnership": (CATEGORY_TRASFERIMENTO, "partnership")
        }

        category_id, prefix = mapping[self.values[0]]
        category = guild.get_channel(category_id)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(
            name=f"{prefix}-{user.name}",
            category=category,
            overwrites=overwrites
        )

        embed_ticket = discord.Embed(
            title="🎫 Ticket Aperto",
            description=(
                f"Benvenuto {user.mention}!\n"
                "Il tuo ticket è stato aperto correttamente.\n\n"
                "🕐 Uno membro dello staff ti assisterà al più presto.\n"
                "❗ Non pingare lo staff inutilmente."
            ),
            color=0x2ecc71
        )
        embed_ticket.set_thumbnail(url=LOGO_URL)
        embed_ticket.set_footer(text="Rimini Roleplay • Sistema Ticket")

        staff_role = guild.get_role(STAFF_ROLE_ID)
        await channel.send(content=f"{user.mention} {staff_role.mention}", embed=embed_ticket, view=TicketButtons(user))

        await interaction.response.send_message(f"✅ Ticket creato correttamente: {channel.mention}", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ========== PANEL COMMAND ==========
@bot.tree.command(name="ticketpanel", description="Pannello Ticket (Founder only)")
async def ticketpanel(interaction: discord.Interaction):
    founder_role = interaction.guild.get_role(FOUNDER_ROLE_ID)
    if founder_role not in interaction.user.roles:
        await interaction.response.send_message("❌ Non hai il permesso di usare questo comando.", ephemeral=True)
        return

    embed = discord.Embed(
        title="<:emoji_1:1438927533382045706> __Rimini Ticket__",
        description=(
            " **Benvenuto nel sistema ticket di Rimini Roleplay**\n"
            "Tutti i membri di Rimini possono aprire un ticket utilizzando questo pannello.\n\n"

            "\n\n"
            " **Assistenza Generale**\n"
            "• Comandi non funzionanti\n"
            "• Come iniziare a giocare\n"
            "• Richiesta cittadinanza\n"
            "• Problemi tecnici o di gioco\n\n"

            "\n\n"
            " **Richiesta Partnership**\n"
            "Sezione dedicata a chi desidera avviare una\n"
            "**partnership** con Rimini.\n"
            "*Leggi i requisiti prima di aprire il ticket.*\n\n"

            "\n\n"
            " **Richiesta Segnalazione**\n"
            "Usa questa categoria per segnalare **BOT o membri**.\n"
            "**Le prove sono obbligatorie**\n"
            "senza di esse non sarà possibile intervenire.\n\n"

            "\n\n"
            " **Richiesta Amministrazione**\n"
            "Categoria riservata a **situazioni serie e importanti**.\n"
            "L’abuso comporterà **sanzioni severe**.\n\n"

            "\n\n"
            "   **Avviso**\n"
            "L’abuso del sistema ticket verrà punito ."
        ),
        color=0x5865F2
    )
    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text="Rimini Roleplay • Sistema Ticket")

    await interaction.response.send_message(
        content="👇 **Usa il menu qui sotto per aprire un ticket**",
        embed=embed,
        view=TicketView()
    )

# ========== RUN ==========
bot.run("MTQ1NDg4Mjg1Mzk0NjAwMzYyMQ.GLrmOO.d1wdMr_kEiaWOl9mLqGo-BD0halHKz4Ywt1NzM")
