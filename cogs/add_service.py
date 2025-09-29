import json, os, nextcord
from nextcord.ext import commands
from nextcord import slash_command, Interaction
from nextcord import SlashOption

SERVICES_FILE = "./data/services.json"

def load_services():
    if not os.path.exists(SERVICES_FILE):
        return {}
    with open(SERVICES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_services(data):
    with open(SERVICES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


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
        services = load_services()

        if service_name in services:
            await interaction.response.send_message(
                f"⚠️ Service **{service_name}** already exists.", ephemeral=True
            )
            return

        services[service_name] = {
            "cost": int(cost),
            "emoji": emoji,
            "available": True if availability == "true" else False,
            "custom_cost": True if is_custom == 'true' else False
        }
        save_services(services)

        await interaction.response.send_message(
            f"✅ Added service {emoji} **{service_name}** with cost **{cost} EGP**, availability: **{availability}**",
            ephemeral=True
        )


def setup(client):
    client.add_cog(AddService(client))
