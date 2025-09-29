from nextcord.ext import commands
from nextcord import Embed, Interaction, TextInputStyle, slash_command, SelectOption, ButtonStyle
from nextcord.ui import Select, View, Modal, button, TextInput
import utils.utils as use
from datetime import datetime
import utils.database as db
import nextcord

class PCLog(Modal):
    def __init__(self, pc):
        super().__init__(title='Bill')
        self.pc = pc
        self.add_item(TextInput(label='💷 Cost (EGP)', style=TextInputStyle.short, required=True))
        self.add_item(TextInput(label="📝 Notes",style=TextInputStyle.paragraph,required=False))

    async def callback(self, interaction: Interaction):
        cost = self.children[0].value
        notes = self.children[1].value
        if not cost.isdigit():
            return await interaction.response.send_message('❌ Cost must be an integer 🔢', ephemeral=True)
        guild = interaction.guild
        await use.log_session(guild, int(cost), self.pc,interaction.user.display_name,notes)

class PCsDropDown(Select):
    def __init__(self):
        options = [
            SelectOption(label=f'PC {i}', value=f'PC {i}', emoji='💻')
            for i in range(1, 15)
        ]
        super().__init__(placeholder='Select a PC...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        pc = self.values[0]
        await interaction.response.send_modal(PCLog(pc))

class PCv(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PCsDropDown())

    @button(label="View Summary", style=ButtonStyle.blurple,emoji='📊')
    async def summary(self, button, interaction: Interaction):
        pcs, services, total = use.get_summary()
        bot_user = interaction.client.user

        embed = Embed(title="⚡ Quick Summary", color=0x7289DA)
        embed.add_field(name="💻 PCs", value=f"💷 {pcs} EGP", inline=True)
        embed.add_field(name="🛠️ Services", value=f"💷 {services} EGP", inline=True)
        embed.add_field(name="💰 Total", value=f"💷 {total} EGP", inline=False)

        embed.set_author(name=bot_user.name, icon_url=bot_user.display_avatar.url)
        embed.set_thumbnail(url=bot_user.display_avatar.url)
        embed.set_footer(text=f"{bot_user.name} | Quick overview")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @button(label="Save Logs", style=ButtonStyle.green,emoji='💾')
    async def reset(self, button, interaction: Interaction):
        data = use.load_data()
        pcs_total = data["totals"]["pcs"]
        services_total = data["totals"]["services"]
        total = data["totals"]["all"]
        date_str = datetime.now().strftime("%d %b %Y")
        bot_user = interaction.client.user

        embed = Embed(title="📊 Daily Summary", color=0x2ecc71)
        embed.add_field(name="💻 PC Sessions", value=f"💷 {pcs_total} EGP", inline=False)
        embed.add_field(name="🛠️ Services", value=f"💷 {services_total} EGP", inline=False)
        embed.add_field(name="💰 Total Income", value=f"💷 {total} EGP", inline=False)
        embed.add_field(name="📅 Date", value=date_str, inline=False)

        embed.set_author(name=bot_user.name, icon_url=bot_user.display_avatar.url)
        embed.set_thumbnail(url=bot_user.display_avatar.url)
        embed.set_footer(text=f"Day has been closed and archived | {bot_user.name}")

        # Send to the correct log channel
        log_channel_id = data.get("log_channel_id")
        if log_channel_id:
            channel = interaction.client.get_channel(log_channel_id)
            if channel:
                await channel.send(embed=embed)

        db.save_logs()
        await interaction.response.send_message("✅ Logs have been reset and archived.", ephemeral=True)

class PC(commands.Cog):
    def __init__(self, client):
        self.client = client

    @slash_command(name='pc_log', description='sends a panel to log all pc sessions')
    async def pc_log(self, interaction: Interaction):
        bot = interaction.client.user
        embed = Embed(
            title='💻 Session Logging Panel',
            description="> Use this panel to log any PC session.\n> Select the PC below and enter session details when prompted.",
            color=0x001DA3
        )
        embed.add_field(name='PC Selection', value='Choose from the dropdown list below.')
        embed.set_footer(text=f'{bot.name} | Daily logs')
        embed.set_thumbnail(url=bot.display_avatar.url)
        await interaction.channel.send(embed=embed, view=PCv())
        await interaction.response.send_message('Panel Created', ephemeral=True)

def setup(client):
    client.add_cog(PC(client))
