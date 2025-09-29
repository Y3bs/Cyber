from random import choice
from nextcord.ext import commands
from nextcord import Color, Embed, SlashOption, slash_command, Interaction
import utils.database as db

class EnableService(commands.Cog):
    def __init__(self, client):
        self.client = client

    @slash_command(name="enable_service", description="Enable a service to make it available")
    async def enable_service(self, interaction: Interaction, 
    service_name: str = SlashOption(
        name= "service_name",
        description="Choose a service to edit",
        autocomplete=True,
        required=True
    )):
        await interaction.response.defer(ephemeral=True)
        db.update_service({"name": service_name, "available": True})
        embed = Embed(
            title="✅ Service Enabled",
            description=f"Service **{service_name}** is now available",
            color=Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @enable_service.on_autocomplete("service_name")
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
    client.add_cog(EnableService(client))
