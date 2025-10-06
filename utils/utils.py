from nextcord import Button, ButtonStyle, SelectOption,Interaction,Embed,TextInputStyle
import nextcord
from datetime import datetime, time
import os, json
import utils.database as db
from nextcord.ui import Select,View,Modal,TextInput
import uuid

DATA_FILE = "current_day.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "pcs": [],
            "services": [],
            "expenses":[],
            "totals": {"pcs": 0, "services": 0,"expenses":0, "all": 0},
            "log_channel_id": None,
        }
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w',encoding='utf-8') as f:
        json.dump(data, f, indent=4)

class LogEdit(Modal):
    def __init__(self,msg,log_id,log_type,cost,edit_type):
        super().__init__(title='Edited Bill')
        self.log_id = log_id
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

                # Update MongoDB
                update_data = {
                    "pc": self.edit_type,
                    "amount": int(cost)
                }
                db.update_pc_session(self.log_id, update_data)

                # Update JSON
                data = load_data()
                for i, pc in enumerate(data['pcs']):
                    if pc.get('session_id') == self.log_id:
                        data['pcs'][i]['pc'] = self.edit_type
                        data['pcs'][i]['amount'] = int(cost)
                        break
                save_data(data)

                data['totals']['pcs'], data['totals']['services'],data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
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

                # Update MongoDB
                update_data = {
                    "service": self.edit_type,
                    "amount": int(cost)
                }
                db.update_service_log(self.log_id, update_data)

                # Update JSON
                data = load_data()
                for i, service in enumerate(data['services']):
                    if service.get('log_id') == self.log_id:
                        data['services'][i]['service'] = self.edit_type
                        data['services'][i]['amount'] = int(cost)
                        break
                save_data(data)

                data['totals']['pcs'], data['totals']['services'],data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
                save_data(data)

                await interaction.followup.send('Service Edited ✅',ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Editing ur message has failed\nError: ```{e}```")


class PcEdit(Select):
    def __init__(self,msg,log_id,log_type,cost):
        self.log_id = log_id
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
        await interaction.response.send_modal(LogEdit(self.msg,self.log_id,self.log_type,self.cost,pc))

class ServiceEdit(Select):
    def __init__(self,msg,log_id,log_type,cost):
        self.msg = msg
        self.log_id = log_id
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
        await interaction.response.send_modal(LogEdit(self.msg,self.log_id,self.log_type,self.cost,service))    

class ExpenseEdit(Modal):
    def __init__(self,msg,log_id,log_type):
        super().__init__(title="Detail Edit")
        self.add_item(TextInput(label="🛍 Expense Name",style=TextInputStyle.short,required=True))
        self.add_item(TextInput(label="💷 Cost",style=TextInputStyle.short,required=True))
        self.msg = msg
        self.log_id = log_id
        self.log_type = log_type
    
    async def callback(self,interaction: Interaction):
        await interaction.response.send_message("Editing ur message... 🔃",ephemeral=True)
        try:
            expense = self.children[0].value
            cost = self.children[1].value

            embed = self.msg.embeds[0]
            embed.set_field_at(0, name="🛍️ Expense", value=expense, inline=True)         
            embed.set_field_at(1, name="💰 Amount Paid", value=f"💷 {cost} EGP", inline=True)

            await self.msg.edit(embed=embed)

            # Update MongoDB
            update_data = {
                "name": expense,
                "amount": int(cost)
            }
            db.update_expense_log(self.log_id, update_data)

            # Update JSON
            data = load_data()
            for i, exp in enumerate(data['expenses']):
                if exp.get('log_id') == self.log_id:
                    data['expenses'][i]['name'] = expense
                    data['expenses'][i]['amount'] = int(cost)
                    break
            save_data(data)

            data['totals']['pcs'], data['totals']['services'],data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
            save_data(data)
            await interaction.followup.send('Expense Edited ✅',ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Editing ur message has failed\nError: ```{e}```")
        
class Edit(View):
    def __init__(self,log_id,log_type):
        super().__init__(timeout=None)
        self.log_id = log_id
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
            pc_dropdown.add_item(PcEdit(msg,self.log_id,self.log_type,cost))
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
            service_dropdown.add_item(ServiceEdit(msg,self.log_id,self.log_type,cost))
            embed = Embed(
                title='Service Edit',
                description='Choose a service to edit for',
                color=0xFFA500
            )
            await interaction.response.send_message(embed=embed,view=service_dropdown,ephemeral=True)

        if self.log_type == 'expenses':
            await interaction.response.send_modal(ExpenseEdit(msg,self.log_id,self.log_type))


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
                # Delete from MongoDB
                db.delete_pc_session(self.log_id)
                
                # Remove from JSON and update totals
                data['pcs'] = [pc for pc in data['pcs'] if pc.get('session_id') != self.log_id]
                data['totals']['pcs'], data['totals']['services'],data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
                save_data(data)
                
                await interaction.message.delete()
                await interaction.followup.send("Message deleted 🗑️",ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Failed to delete the message\nError: ```{e}```",ephemeral=True)

        if self.log_type == 'services':
            try:
                # Delete from MongoDB
                db.delete_service_log(self.log_id)
                
                # Remove from JSON and update totals
                data['services'] = [s for s in data['services'] if s.get('log_id') != self.log_id]
                data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
                save_data(data)
                
                await interaction.message.delete()
                await interaction.followup.send("Message deleted 🗑️",ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Failed to delete the message\nError: ```{e}```",ephemeral=True)
        
        if self.log_type == 'expenses':
            try:
                # Delete from MongoDB
                db.delete_expense_log(self.log_id)
                
                # Remove from JSON and update totals
                data['expenses'] = [e for e in data['expenses'] if e.get('log_id') != self.log_id]
                data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
                save_data(data)
                
                await interaction.message.delete()
                await interaction.followup.send("Message deleted 🗑️",ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Failed to delete the message\nError: ```{e}```",ephemeral=True)

async def log_session(guild: nextcord.Guild, amount_paid: int, pc_name: str, staff: str = "Yousef",notes: str = None):
    amount_paid = int(amount_paid)
    today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
    today_channel = datetime.now().strftime("logs-%Y-%m-%d")
    session_time  = cost_to_time(amount_paid)
    session_id = str(uuid.uuid4())

    # Save to JSON (for current day)
    data = load_data()
    session_data = {
        "pc": pc_name, 
        "amount": amount_paid, 
        "staff": staff, 
        "time": today_full,
        "notes": notes,
        "session_id": session_id
    }
    data["pcs"].append(session_data)
    data["totals"]["pcs"] += amount_paid
    data["totals"]["all"] = data["totals"]["pcs"] + data["totals"]["services"] - data['totals']['expenses']

    # Save to MongoDB
    mongo_data = {
        "session_id": session_id,
        "pc": pc_name,
        "amount": amount_paid,
        "staff": staff,
        "time": today_full,
        "notes": notes,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now(),
        "guild_id": guild.id
    }
    db.save_pc_session(mongo_data)

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

    await channel.send(embed=embed,view=Edit(session_id, 'pcs'))

async def log_service(guild: nextcord.Guild, amount_paid: int, service_name: str,emoji: str, staff: str = "Yousef"):
    amount_paid = int(amount_paid)
    today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
    today_channel = datetime.now().strftime("logs-%Y-%m-%d")
    log_id = str(uuid.uuid4())

    # Save to JSON (for current day)
    data = load_data()
    service_data = {
        "service": service_name, 
        "amount": amount_paid, 
        "staff": staff, 
        "time": today_full,
        "log_id": log_id
    }
    data["services"].append(service_data)
    data["totals"]["services"] += amount_paid
    data["totals"]["all"] = data["totals"]["pcs"] + data["totals"]["services"] - data['totals']['expenses']

    # Save to MongoDB
    mongo_data = {
        "log_id": log_id,
        "service": service_name,
        "amount": amount_paid,
        "staff": staff,
        "time": today_full,
        "emoji": emoji,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now(),
        "guild_id": guild.id
    }
    db.save_service_log(mongo_data)

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

    await channel.send(embed=embed,view=Edit(log_id,'services'))

async def log_expense(guild: nextcord.Guild, amount: int, expense_name: str,staff: str = "Yousef"):
    amount = int(amount)
    today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
    today_channel = datetime.now().strftime("logs-%Y-%m-%d")
    log_id = str(uuid.uuid4())
    
    # Save to JSON (for current day)
    data = load_data()
    expense_data = {
        "name": expense_name,
        "amount": amount,
        "staff": staff,
        "time": today_full,
        "log_id": log_id
    }
    data['expenses'].append(expense_data)
    data['totals']['expenses'] += amount
    data['totals']['all'] = data['totals']['pcs'] + data['totals']['services'] - data['totals']['expenses']

    # Save to MongoDB
    mongo_data = {
        "log_id": log_id,
        "name": expense_name,
        "amount": amount,
        "staff": staff,
        "time": today_full,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now(),
        "guild_id": guild.id
    }
    db.save_expense_log(mongo_data)

    # Find or create the log channel
    channel = nextcord.utils.get(guild.text_channels, name=today_channel)
    if channel is None:
        channel = await guild.create_text_channel(today_channel)
    data["log_channel_id"] = channel.id

    save_data(data)

    # Embed
    embed = nextcord.Embed(
        title="🛒 Expense Logged",
        description="A new expense has been recorded successfully.",
        color=nextcord.Color.red()
    )
    embed.add_field(name="🛍️ Expense", value=f'{expense_name}', inline=True)
    embed.add_field(name="💰 Amount Paid", value=f"💷 {amount} EGP", inline=True)
    embed.add_field(name="📅 Date", value=today_full, inline=True)
    embed.set_footer(text=f"Logged by: {staff} | Leader")

    await channel.send(embed=embed,view=Edit(log_id,'expenses'))
    
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
    total_expense = 0
    for record in data['pcs']:
        total_pc += record['amount']
    for record in data['services']:
        total_service += record['amount']
    for record in data['expenses']:
        total_expense += record['amount']
    return total_pc,total_service,total_expense,(total_pc + total_service - total_expense)

def get_current_period():
    now = datetime.now().time()
    morning_start = time(8, 0)
    evening_start = time(16, 0)
    midnight = time(0, 0)
    # Morning: 08:00 <= now < 16:00
    if morning_start <= now < evening_start:
        return 'morning'
    # Evening: 16:00 <= now <= 23:59:59
    return 'evening'
