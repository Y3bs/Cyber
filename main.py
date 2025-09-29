import nextcord
from nextcord.ext import commands
from nextcord import Intents
from dotenv import load_dotenv
import os
from utils.database import db

intents = Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix='!',intents=intents)
load_dotenv()

TOKEN = os.getenv('TOKEN')

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    print("🗄️  Database State:")
    print("=" * 50)
    try:
        db.admin.command('ping')
        print("✅ Database Connection: Connected")
    except Exception as e:
        print(f"❌ Database Connection: Failed - {str(e)}")
        print("=" * 50)

client.run(TOKEN)