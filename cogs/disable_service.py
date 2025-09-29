import json, os, nextcord
from nextcord.ext import commands
from nextcord import Color, Embed, SlashOption, slash_command, Interaction
import utils.database as db

class DisableService(commands.Cog):
    def __init__(self, client):
        self.client = client

    @slash_command(name="disable_service", description="Disable a service to make it unavailable")
    async def disable_service(self, interaction: Interaction, 
    service_name: str = SlashOption(
        name= "service_name",
        description="Choose a service to edit",
        autocomplete=True,
        required=True
    )
    ):
        await interaction.response.defer(ephemeral=True)
        db.update_service({"name": service_name, "available":False})
        embed = Embed(
            title="❌ Service Disabled",
            description=f"Service **{service_name}** is now unavailable",
            color=Color.red()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @disable_service.on_autocomplete("service_name")
    async def service_name_autocomplete(self, interaction: Interaction, string: str):
        try:
            cursor = db.db.cyber.services.find({}, {"_id": 0, "name": 1})
            names = [doc.get("name") for doc in cursor if doc.get("name")]
            query = (string or "").lower()
            filtered = [n for n in names if query in n.lower()][:25]
            await interaction.response.send_autocomplete(filtered)
        except Exception:
            await interaction.response.send_autocomplete([])


def setup(client):
    client.add_cog(DisableService(client))
