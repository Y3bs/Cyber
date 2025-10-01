from tkinter import Button
from nextcord.ext import commands
from nextcord import ButtonStyle, Color, Interaction,Embed, TextInputStyle,slash_command
from nextcord.ui import Modal, TextInput,Button, button,View
import utils.utils as use

class ExpenseModal(Modal):
    def __init__(self):
        super().__init__(title="Bill")
        self.add_item(TextInput(label="🛍 Expense Name",style=TextInputStyle.short,required=True))
        self.add_item(TextInput(label="💷 Cost",style=TextInputStyle.short,required=True))
    
    async def callback(self, interaction: Interaction):
        data = use.load_data()
        expense = self.children[0].value
        cost = self.children[1].value

        if not cost.isdigit():
            return await interaction.response.send_message('❌ Cost must be an integer 🔢', ephemeral=True)
        guild = interaction.guild
        await use.log_expense(guild,cost,expense,interaction.user.display_name)

        embed = Embed(
            title = "Expense Logged Successfully ✅",
            color = Color.green()
        )
        embed.add_field(name='🛍 Expense Name',value=expense)
        embed.add_field(name='💷 Cost',value=f'{cost} EGP')

        await interaction.response.send_message(embed=embed,ephemeral=True)

class Expense(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @button(
        label = "Log Expense",
        style=ButtonStyle.red,
        emoji="🛒"
    )

    async def log_expense(self,button:Button,interaction: Interaction):
        await interaction.response.send_modal(ExpenseModal())

class Expenses(commands.Cog):
    def __init__(self,client):
        self.client = client
    
    @slash_command(name='expense_panel',description="sends the panel to log expenses")
    async def expense_panel(self,interaction:Interaction):
        await interaction.response.defer(ephemeral=True)
        bot = interaction.client.user

        embed = Embed(
            title = "🛍 Expenses Logging Panel",
            description="All your expenses in one place just press the button below to log",
            color=Color.red()
         )
        embed.set_footer(text=f'{bot.name} | Daily logs')
        embed.set_thumbnail(url=bot.display_avatar.url)

        await interaction.followup.send("Panel Created")
        await interaction.channel.send(embed=embed,view=Expense())

def setup(client):
    client.add_cog(Expenses(client))