from nextcord import Button, ButtonStyle, SelectOption,Interaction,Embed,TextInputStyle
import nextcord
from datetime import datetime
import os, json
import utils.database as db
from nextcord.ui import Select,View,Modal,TextInput

DATA_FILE = "current_day.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "pcs": [],
            "services": [],
            "totals": {"pcs": 0, "services": 0, "all": 0},
            "log_channel_id": None,
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w',encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class LogEdit(Modal):
    def __init__(self,msg,log_index,log_type,cost,edit_type):
        super().__init__(title='Edited Bill')
        self.log_index = log_index
        self.log_type = log_type
        self.msg = msg
        self.cost = cost
        self.edit_type = edit_type
        
        self.add_item(TextInput(label='💷 Cost (EGP)',default_value=self.cost, style=TextInputStyle.short, required=True))
    
    async def callback(self, interaction: Interaction):
        await interaction.response.send_message("Editing ur message... 🔃",ephemeral=True)
        cost = self.children[0].value
        if self.log_type == 'pcs':
            try:
                embed = self.msg.embeds[0]
                embed.set_field_at(0, name="🖥️ PC", value=self.edit_type, inline=True)         
                embed.set_field_at(1, name="💰 Amount Paid", value=f"💷 {cost} EGP", inline=True)
                embed.set_field_at(2, name='⏳ Time Equivalent',value=cost_to_time(int(cost)),inline=True)

                await self.msg.edit(embed=embed)

                data = load_data()
                new_data = data['pcs'][self.log_index]
                new_data['pc'] = self.edit_type
                new_data['amount'] = int(cost)
                data['pcs'][self.log_index] = new_data
                save_data(data)

                data['totals']['pcs'], data['totals']['services'], data['totals']['all'] = calc_totals(data)
                save_data(data)

                await interaction.followup.send('Pc Session Edited ✅',ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Editing ur message has failed \nError: ```{e}```")
                
            
        if self.log_type == 'services':
            try:
                embed = self.msg.embeds[0]
                embed.set_field_at(0, name="📦 Service", value=self.edit_type, inline=True)         
                embed.set_field_at(1, name="💰 Amount Paid", value=f"💷 {cost} EGP", inline=True)

                await self.msg.edit(embed=embed)

                data = load_data()
                new_data = data['services'][self.log_index]
                new_data['service'] = self.edit_type
                new_data['amount'] = int(cost)
                data['services'][self.log_index] = new_data
                save_data(data)

                data['totals']['pcs'], data['totals']['services'], data['totals']['all'] = calc_totals(data)
                save_data(data)

                await interaction.followup.send('Service Edited ✅',ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Editing ur message has failed\nError: ```{e}```")


class PcEdit(Select):
    def __init__(self,msg,log_index,log_type,cost):
        self.log_index = log_index
        self.log_type = log_type
        self.msg = msg
        self.cost = cost
        options = [
            SelectOption(label=f'PC {i}', value=f'PC {i}', emoji='💻')
            for i in range(1, 15)
        ]
        super().__init__(placeholder='Select a PC...', min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: Interaction):
        pc = self.values[0]
        await interaction.response.send_modal(LogEdit(self.msg,self.log_index,self.log_type,self.cost,pc))

class ServiceEdit(Select):
    def __init__(self,msg,log_index,log_type,cost):
        self.msg = msg
        self.log_index = log_index
        self.log_type = log_type
        self.cost = cost
        
        services = db.load_services()
        options = []
        for service in services:
            name = service['name']
            cost = service['cost']
            emoji = service['emoji']
            available = service['available']

            if not available:
                continue  

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
        service = self.values[0]
        await interaction.response.send_modal(LogEdit(self.msg,self.log_index,self.log_type,self.cost,service))    

class Edit(View):
    def __init__(self,log_index,log_type):
        super().__init__(timeout=None)
        self.log_index = log_index
        self.log_type = log_type
    
    @nextcord.ui.button(
        label = 'Edit',
        custom_id='edit',
        style=nextcord.ButtonStyle.gray,
        emoji='✏️'
    )
    async def edit(self,button : Button,interaction: Interaction):
        msg = interaction.message
        cost = msg.embeds[0].fields[1].value
        try:
            cost = int(cost[1:(len(cost)-3)])
        except ValueError as e:
            print(f'Value Error: {e}')

        if self.log_type == 'pcs':
            pc_dropdown = View()
            pc_dropdown.add_item(PcEdit(msg,self.log_index,self.log_type,cost))
            embed = Embed(
                title='Pc Session Edit',
                description='Choose which pc you want to edit the current session',
                color=0x001DA3
            )
            for i in range(1,15):
                embed.add_field(
                    name=f'💻 PC {i}',
                    value = ' '
                )
            await interaction.response.send_message(embed=embed,view = pc_dropdown,ephemeral=True)
        if self.log_type == 'services':
            service_dropdown = View()
            service_dropdown.add_item(ServiceEdit(msg,self.log_index,self.log_type,cost))
            embed = Embed(
                title='Service Edit',
                description='Choose a service to edit for',
                color=0xFFA500
            )
            await interaction.response.send_message(embed=embed,view=service_dropdown,ephemeral=True)

    @nextcord.ui.button(
        label = "Delete",
        style = ButtonStyle.red,
        emoji='🗑️'
    )
    async def delete(self,button: Button, interaction: Interaction):
        await interaction.response.send_message(f"Deleting ur message... 🔃",ephemeral=True)
        data = load_data()
        
        if self.log_type == 'pcs':
            try:
                del data['pcs'][self.log_index]
                await interaction.message.delete()
                save_data(data)
                data['totals']['pcs'], data['totals']['services'], data['totals']['all'] = calc_totals(data)
                save_data(data)
                await interaction.followup.send("Message deleted 🗑️",ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Failed to delete the message\nError: ```{e}```",ephemeral=True)

        if self.log_type == 'services':
            try:
                del data['services'][self.log_index]
                await interaction.message.delete()
                save_data(data)
                data['totals']['pcs'], data['totals']['services'], data['totals']['all'] = calc_totals(data)
                save_data(data)
                await interaction.followup.send("Message deleted 🗑️",ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Failed to delete the message\nError: ```{e}```",ephemeral=True)



async def log_session(guild: nextcord.Guild, amount_paid: int, pc_name: str, staff: str = "Yousef",notes: str = None):
    amount_paid = int(amount_paid)
    today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
    today_channel = datetime.now().strftime("logs-%Y-%m-%d")
    session_time  = cost_to_time(amount_paid)

    # Save to JSON
    data = load_data()
    data["pcs"].append({"pc": pc_name, "amount": amount_paid, "staff": staff, "time": today_full})
    data["totals"]["pcs"] += amount_paid
    data["totals"]["all"] = data["totals"]["pcs"] + data["totals"]["services"]

    # Find or create the log channel
    channel = nextcord.utils.get(guild.text_channels, name=today_channel)
    if channel is None:
        channel = await guild.create_text_channel(today_channel)
    data["log_channel_id"] = channel.id

    save_data(data)

    # Embed
    embed = nextcord.Embed(
        title="💻 PC Session Logged",
        description="A new session has been recorded successfully.",
        color=nextcord.Color.green()
    )
    embed.add_field(name="🖥️ PC", value=pc_name, inline=True)
    embed.add_field(name="💰 Amount Paid", value=f"💷 {amount_paid} EGP", inline=True)
    embed.add_field(name="⏳ Time Equivalent",value=session_time,inline=True)
    embed.add_field(name="📅 Date", value=today_full, inline=True)
    if notes:
        embed.add_field(name="📝 Notes",value=notes,inline=True)
    embed.set_footer(text=f"Logged by: {staff} | Leader")

    await channel.send(embed=embed,view=Edit(len(data['pcs'])-1 ,'pcs'))

async def log_service(guild: nextcord.Guild, amount_paid: int, service_name: str,emoji: str, staff: str = "Yousef"):
    amount_paid = int(amount_paid)
    today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
    today_channel = datetime.now().strftime("logs-%Y-%m-%d")

    # Save to JSON
    data = load_data()
    data["services"].append({"service": service_name, "amount": amount_paid, "staff": staff, "time": today_full})
    data["totals"]["services"] += amount_paid
    data["totals"]["all"] = data["totals"]["pcs"] + data["totals"]["services"]

    # Find or create the log channel
    channel = nextcord.utils.get(guild.text_channels, name=today_channel)
    if channel is None:
        channel = await guild.create_text_channel(today_channel)
    data["log_channel_id"] = channel.id

    save_data(data)

    # Embed
    embed = nextcord.Embed(
        title="🛠️ Service Logged",
        description="A new service has been recorded successfully.",
        color=nextcord.Color.orange()
    )
    embed.add_field(name="📦 Service", value=f'{emoji} {service_name}', inline=True)
    embed.add_field(name="💰 Amount Paid", value=f"💷 {amount_paid} EGP", inline=True)
    embed.add_field(name="📅 Date", value=today_full, inline=True)
    embed.set_footer(text=f"Logged by: {staff} | Leader")

    await channel.send(embed=embed,view=Edit(len(data['services'])-1,'services'))

def get_summary():
    data = load_data()
    return (
        data["totals"]["pcs"],
        data["totals"]["services"],
        data["totals"]["all"]
    )

def cost_to_time(cost: int):
    min = cost * 6
    h = min // 60
    mins = min % 60
    return f'{h}h {mins}m'

# Better way to calculate totals
def calc_totals(data):
    total_pc = 0
    total_service = 0
    for record in data['pcs']:
        total_pc += record['amount']
    for record in data['services']:
        total_service += record['amount']
    return total_pc,total_service,(total_pc + total_service)
