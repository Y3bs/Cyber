from nextcord.ext import commands
from nextcord import Interaction,Embed, SlashOption,slash_command
import utils.database as db

class DeleteService(commands.Cog):
     def __init__(self,client):
          self.client = client
     
     @slash_command(name='delete_service',description="remove a service from the database")
     async def delete(self,interaction:Interaction,
     service_name: str = SlashOption(
          name='service_name',
          description='choose a service to delete',
          required=True,
          autocomplete=True
     )
     ):
          await interaction.response.defer(ephemeral=True)
          db.delete_service(service_name)
          embed = Embed(
               title="🗑️ Service Deleted",
               description=f"Service **{service_name}** is deleted",
          )
          await interaction.followup.send(embed=embed,ephemeral=True)

     @delete.on_autocomplete("service_name")
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
     client.add_cog(DeleteService(client))