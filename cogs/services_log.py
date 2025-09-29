import json
import os
import nextcord
from nextcord.ext import commands
from nextcord import Embed, Interaction, slash_command, SelectOption,TextInputStyle,Color
from nextcord.ui import View, Select,Modal,TextInput
import utils.utils as use
import utils.database as db

class CustomServiceCost(Modal):
    def __init__(self, service,emoji):
        super().__init__(title='Bill')
        self.service = service
        self.emoji = emoji
        self.add_item(TextInput(label='💷 Cost (EGP)', style=TextInputStyle.short, required=True))

    async def callback(self, interaction: Interaction):
        cost = self.children[0].value
        if not cost.isdigit():
            return await interaction.response.send_message('❌ Cost must be an integer 🔢', ephemeral=True)
        guild = interaction.guild
        await use.log_service(guild,cost,self.service,self.emoji,staff=interaction.user.display_name)

       # Confirmation Message
        embed = Embed(
            title='Serivce Logged Successfully ✅',
            color=Color.green()
        )
        embed.add_field(name='Service Name',value=f'{self.emoji} {self.service}',inline=True)
        embed.add_field(name='Cost',value=f'💷 {cost} EGP')

        # ✅ Always respond to the dropdown interaction
        await interaction.response.send_message(embed=embed,ephemeral=True)

class ServiceDropdown(Select):
    def __init__(self):
        services = db.load_services()
        options = []
        for service in services:
            name = service['name']
            cost = service['cost']
            emoji = service['emoji']
            available = service['available']

            if not available:
                continue  # skip unavailable services

            options.append(
                SelectOption(
                    label=name,
                    description=f"💷 {cost} EGP",
                    value=name,
                    emoji=emoji
                )
            )

        if not options:
            options = [SelectOption(label="No services available", value="none")]

        super().__init__(placeholder="Select a service...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        services = db.load_services()
        service_name = self.values[0]

        if service_name == "none":
            await interaction.response.send_message("⚠️ No services available.", ephemeral=True)
            return

        service_info = services[service_name]
        cost = service_info.get("cost", 0)
        emoji = service_info.get("emoji", "🛠️")
        is_custom = service_info.get("custom_cost")

        # for custom cost services
        if is_custom:
            await interaction.response.send_modal(CustomServiceCost(service_name,emoji))
            return

        # ✅ Log the service in utils.py
        await use.log_service(
            interaction.guild,
            cost,
            service_name,
            emoji,
            staff=interaction.user.display_name
        )

        # Confirmation Message
        embed = Embed(
            title='Serivce Logged Successfully ✅',
            color=Color.green()
        )
        embed.add_field(name='Service Name',value=f'{emoji} {service_name}',inline=True)
        embed.add_field(name='Cost',value=f'💷 {cost} EGP')

        # ✅ Always respond to the dropdown interaction
        await interaction.response.send_message(embed=embed,ephemeral=True)


class ServicePanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ServiceDropdown())


class ServiceCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @slash_command(name="service_log", description="Send a panel to log services")
    async def service_log(self, interaction: Interaction):
        bot = interaction.client.user
        embed = Embed(
            title="🛠️ Service Logging Panel",
            description="Select a service from the dropdown below to log it.",
            color=0xFFA500
        )
        embed.set_footer(text=f"{bot.name} | Daily logs")
        await interaction.channel.send(embed=embed, view=ServicePanel())
        await interaction.response.send_message("✅ Service panel created", ephemeral=True)


def setup(client):
    client.add_cog(ServiceCog(client))
