import json, os, nextcord
from nextcord.ext import commands
from nextcord import slash_command, Interaction

SERVICES_FILE = "./data/services.json"

def load_services():
    if not os.path.exists(SERVICES_FILE):
        return {}
    with open(SERVICES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_services(data):
    with open(SERVICES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class DisableService(commands.Cog):
    def __init__(self, client):
        self.client = client

    @slash_command(name="disable_service", description="Disable a service to make it unavailable")
    async def disable_service(self, interaction: Interaction, service_name: str):
        services = load_services()
        if service_name not in services:
            await interaction.response.send_message(f"⚠️ Service **{service_name}** not found.", ephemeral=True)
            return

        services[service_name]["available"] = False
        save_services(services)
        await interaction.response.send_message(f"🚫 Service **{service_name}** is now unavailable.", ephemeral=True)

    @disable_service.on_autocomplete("service_name")
    async def service_autocomplete(self, interaction: Interaction, current: str):
        services = load_services()
        choices = [s for s in services.keys() if current.lower() in s.lower()]
        await interaction.response.send_autocomplete(choices[:25])  # Discord limit


def setup(client):
    client.add_cog(DisableService(client))
