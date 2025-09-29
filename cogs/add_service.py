import json, os, nextcord
from nextcord.ext import commands
from nextcord import Color, Embed, slash_command, Interaction
from nextcord import SlashOption
import utils.database as db

class AddService(commands.Cog):
    def __init__(self, client):
        self.client = client

    @slash_command(name="add_service", description="Add a new service with cost, availability, and emoji")
    async def add_service(
        self,
        interaction: Interaction,
        service_name: str,
        cost: int = SlashOption(
            name='cost',
            description="Enter the service's cost (could be custom)"
        ),
        availability: str = SlashOption(
            name="availability",
            description="Is this service available?",
            choices={"true": "true", "false": "false"}
        ),
        emoji: str = SlashOption(
            name="emoji",
            description="Emoji for this service",
            required=True
        ),
        is_custom : str = SlashOption(
            name='custom_cost',
            description="Whether the service has a custom price or not",
            choices={'true': 'true','false':'false'},
            required=True
        )
    ):
        services = db.load_services()

        for service in services:
            if service_name == service['name']:
                return await interaction.response.send_message(
                    f"⚠️ Service **{service_name}** already exists.", ephemeral=True
                )
                

        service_doc = {
            "name": service_name,
            "cost": int(cost),
            "emoji": emoji,
            "available": True if availability == "true" else False,
            "custom_cost": True if is_custom == 'true' else False
        }
        db.save_service(service_doc)

        embed = Embed(
            title = "✅ Service added",
            color=Color.green()
        )
        embed.add_field(name="🔨 Service Name",value=service_name)
        embed.add_field(name="💷 Cost",value =f"{cost} EGP")
        embed.add_field(name="🔓 availability",value="available" if availability else "Closed")
        await interaction.response.send_message(
            embed =embed,
            ephemeral=True
        )


def setup(client):
    client.add_cog(AddService(client))
