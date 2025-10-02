from nextcord.ext import commands
from nextcord import Embed, Interaction, slash_command, SlashOption, Color
from nextcord.ui import Select, View, Modal, TextInput, Button, ButtonStyle
from nextcord import SelectOption, TextInputStyle
import utils.database as db
from datetime import datetime
import nextcord

class EditRecordModal(Modal):
    def __init__(self, record_type, record_id, current_data):
        super().__init__(title=f"Edit {record_type.title()}")
        self.record_type = record_type
        self.record_id = record_id
        self.current_data = current_data
        
        if record_type == "pc_session":
            self.add_item(TextInput(
                label="PC Number", 
                default_value=current_data.get('pc', ''),
                style=TextInputStyle.short, 
                required=True
            ))
            self.add_item(TextInput(
                label="Amount (EGP)", 
                default_value=str(current_data.get('amount', 0)),
                style=TextInputStyle.short, 
                required=True
            ))
            self.add_item(TextInput(
                label="Notes", 
                default_value=current_data.get('notes', ''),
                style=TextInputStyle.paragraph, 
                required=False
            ))
        elif record_type == "service_log":
            self.add_item(TextInput(
                label="Service Name", 
                default_value=current_data.get('service', ''),
                style=TextInputStyle.short, 
                required=True
            ))
            self.add_item(TextInput(
                label="Amount (EGP)", 
                default_value=str(current_data.get('amount', 0)),
                style=TextInputStyle.short, 
                required=True
            ))
        elif record_type == "expense_log":
            self.add_item(TextInput(
                label="Expense Name", 
                default_value=current_data.get('name', ''),
                style=TextInputStyle.short, 
                required=True
            ))
            self.add_item(TextInput(
                label="Amount (EGP)", 
                default_value=str(current_data.get('amount', 0)),
                style=TextInputStyle.short, 
                required=True
            ))
    
    async def callback(self, interaction: Interaction):
        await interaction.response.send_message("Updating record... 🔄", ephemeral=True)
        
        try:
            if self.record_type == "pc_session":
                pc = self.children[0].value
                amount = int(self.children[1].value)
                notes = self.children[2].value
                
                update_data = {
                    "pc": pc,
                    "amount": amount,
                    "notes": notes
                }
                success = db.update_pc_session(self.record_id, update_data)
                
            elif self.record_type == "service_log":
                service = self.children[0].value
                amount = int(self.children[1].value)
                
                update_data = {
                    "service": service,
                    "amount": amount
                }
                success = db.update_service_log(self.record_id, update_data)
                
            elif self.record_type == "expense_log":
                name = self.children[0].value
                amount = int(self.children[1].value)
                
                update_data = {
                    "name": name,
                    "amount": amount
                }
                success = db.update_expense_log(self.record_id, update_data)
            
            if success:
                embed = Embed(
                    title="✅ Record Updated Successfully",
                    description=f"The {self.record_type.replace('_', ' ')} has been updated.",
                    color=Color.green()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = Embed(
                    title="❌ Update Failed",
                    description="Could not update the record. Please try again.",
                    color=Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                
        except ValueError:
            embed = Embed(
                title="❌ Invalid Input",
                description="Amount must be a valid number.",
                color=Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            embed = Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class RecordSelector(Select):
    def __init__(self, records, record_type):
        self.records = records
        self.record_type = record_type
        
        options = []
        for i, record in enumerate(records[:25]):  # Discord limit
            if record_type == "pc_session":
                label = f"PC {record.get('pc', 'Unknown')} - {record.get('amount', 0)} EGP"
                description = f"Staff: {record.get('staff', 'Unknown')} | {record.get('time', 'Unknown')}"
            elif record_type == "service_log":
                label = f"{record.get('service', 'Unknown')} - {record.get('amount', 0)} EGP"
                description = f"Staff: {record.get('staff', 'Unknown')} | {record.get('time', 'Unknown')}"
            elif record_type == "expense_log":
                label = f"{record.get('name', 'Unknown')} - {record.get('amount', 0)} EGP"
                description = f"Staff: {record.get('staff', 'Unknown')} | {record.get('time', 'Unknown')}"
            
            options.append(SelectOption(
                label=label[:100],  # Discord limit
                description=description[:100],
                value=str(i)
            ))
        
        super().__init__(placeholder=f"Select a {record_type.replace('_', ' ')} to edit...", 
                        min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: Interaction):
        try:
            index = int(self.values[0])
            selected_record = self.records[index]
            
            # Get the record ID based on type
            if self.record_type == "pc_session":
                record_id = selected_record.get('session_id')
            elif self.record_type == "service_log":
                record_id = selected_record.get('log_id')
            elif self.record_type == "expense_log":
                record_id = selected_record.get('log_id')
            
            if not record_id:
                await interaction.response.send_message("❌ Record ID not found.", ephemeral=True)
                return
            
            await interaction.response.send_modal(EditRecordModal(self.record_type, record_id, selected_record))
            
        except (ValueError, IndexError) as e:
            await interaction.response.send_message("❌ Invalid selection.", ephemeral=True)

class RecordSelectorView(View):
    def __init__(self, records, record_type):
        super().__init__(timeout=60)
        self.add_item(RecordSelector(records, record_type))

class UniversalEditView(View):
    def __init__(self):
        super().__init__(timeout=60)
    
    @Button(label="💻 PC Sessions", style=ButtonStyle.blue, emoji="💻")
    async def edit_pc_sessions(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        records = db.get_pc_sessions()
        if not records:
            embed = Embed(
                title="No PC Sessions Found",
                description="There are no PC sessions to edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="💻 Edit PC Sessions",
            description=f"**Found {len(records)} PC sessions**\nSelect one to edit:",
            color=Color.blue()
        )
        
        view = RecordSelectorView(records, "pc_session")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @Button(label="🛠️ Service Logs", style=ButtonStyle.orange, emoji="🛠️")
    async def edit_service_logs(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        records = db.get_service_logs()
        if not records:
            embed = Embed(
                title="No Service Logs Found",
                description="There are no service logs to edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="🛠️ Edit Service Logs",
            description=f"**Found {len(records)} service logs**\nSelect one to edit:",
            color=Color.orange()
        )
        
        view = RecordSelectorView(records, "service_log")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @Button(label="🛒 Expense Logs", style=ButtonStyle.red, emoji="🛒")
    async def edit_expense_logs(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        records = db.get_expense_logs()
        if not records:
            embed = Embed(
                title="No Expense Logs Found",
                description="There are no expense logs to edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="🛒 Edit Expense Logs",
            description=f"**Found {len(records)} expense logs**\nSelect one to edit:",
            color=Color.red()
        )
        
        view = RecordSelectorView(records, "expense_log")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class AllRecordsView(View):
    def __init__(self):
        super().__init__(timeout=60)
    
    @Button(label="📝 Edit Records", style=ButtonStyle.primary, emoji="✏️")
    async def edit_records(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get all types of records
        pc_records = db.get_pc_sessions()
        service_records = db.get_service_logs()
        expense_records = db.get_expense_logs()
        
        total_records = len(pc_records) + len(service_records) + len(expense_records)
        
        if total_records == 0:
            embed = Embed(
                title="No Records Found",
                description="There are no records to edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="📝 Edit Any Record",
            description=f"**Total Records Available:** {total_records}\n\n"
                       f"💻 **PC Sessions:** {len(pc_records)}\n"
                       f"🛠️ **Service Logs:** {len(service_records)}\n"
                       f"🛒 **Expense Logs:** {len(expense_records)}\n\n"
                       f"Choose what type of record you want to edit:",
            color=Color.blue()
        )
        
        view = UniversalEditView()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @Button(label="🗑️ Delete Records", style=ButtonStyle.danger, emoji="🗑️")
    async def delete_records(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        embed = Embed(
            title="🗑️ Delete Records",
            description="Choose what type of record you want to delete:",
            color=Color.red()
        )
        
        view = DeleteRecordsView()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @Button(label="📊 View Details", style=ButtonStyle.secondary, emoji="📊")
    async def view_details(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get recent records (last 10 of each type)
        pc_records = db.get_pc_sessions()[:10]
        service_records = db.get_service_logs()[:10]
        expense_records = db.get_expense_logs()[:10]
        
        embed = Embed(
            title="📊 Recent Records Details",
            description="Here are the most recent records:",
            color=Color.blue()
        )
        
        if pc_records:
            pc_text = "\n".join([
                f"• {record.get('pc', 'Unknown')} - {record.get('amount', 0)} EGP ({record.get('time', 'Unknown')})"
                for record in pc_records[:5]
            ])
            embed.add_field(name="💻 Recent PC Sessions", value=pc_text or "None", inline=False)
        
        if service_records:
            service_text = "\n".join([
                f"• {record.get('service', 'Unknown')} - {record.get('amount', 0)} EGP ({record.get('time', 'Unknown')})"
                for record in service_records[:5]
            ])
            embed.add_field(name="🛠️ Recent Service Logs", value=service_text or "None", inline=False)
        
        if expense_records:
            expense_text = "\n".join([
                f"• {record.get('name', 'Unknown')} - {record.get('amount', 0)} EGP ({record.get('time', 'Unknown')})"
                for record in expense_records[:5]
            ])
            embed.add_field(name="🛒 Recent Expense Logs", value=expense_text or "None", inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)

class DeleteRecordsView(View):
    def __init__(self):
        super().__init__(timeout=60)
    
    @Button(label="💻 Delete PC Sessions", style=ButtonStyle.danger, emoji="💻")
    async def delete_pc_sessions(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        records = db.get_pc_sessions()
        if not records:
            embed = Embed(
                title="No PC Sessions Found",
                description="There are no PC sessions to delete.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="🗑️ Delete PC Sessions",
            description=f"**Found {len(records)} PC sessions**\nSelect one to delete:",
            color=Color.red()
        )
        
        view = DeleteRecordSelectorView(records, "pc_session")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @Button(label="🛠️ Delete Service Logs", style=ButtonStyle.danger, emoji="🛠️")
    async def delete_service_logs(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        records = db.get_service_logs()
        if not records:
            embed = Embed(
                title="No Service Logs Found",
                description="There are no service logs to delete.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="🗑️ Delete Service Logs",
            description=f"**Found {len(records)} service logs**\nSelect one to delete:",
            color=Color.red()
        )
        
        view = DeleteRecordSelectorView(records, "service_log")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @Button(label="🛒 Delete Expense Logs", style=ButtonStyle.danger, emoji="🛒")
    async def delete_expense_logs(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        records = db.get_expense_logs()
        if not records:
            embed = Embed(
                title="No Expense Logs Found",
                description="There are no expense logs to delete.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="🗑️ Delete Expense Logs",
            description=f"**Found {len(records)} expense logs**\nSelect one to delete:",
            color=Color.red()
        )
        
        view = DeleteRecordSelectorView(records, "expense_log")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class DeleteRecordSelectorView(View):
    def __init__(self, records, record_type):
        super().__init__(timeout=60)
        self.add_item(DeleteRecordSelector(records, record_type))

class DeleteRecordSelector(Select):
    def __init__(self, records, record_type):
        self.records = records
        self.record_type = record_type
        
        options = []
        for i, record in enumerate(records[:25]):  # Discord limit
            if record_type == "pc_session":
                label = f"PC {record.get('pc', 'Unknown')} - {record.get('amount', 0)} EGP"
                description = f"Staff: {record.get('staff', 'Unknown')} | {record.get('time', 'Unknown')}"
            elif record_type == "service_log":
                label = f"{record.get('service', 'Unknown')} - {record.get('amount', 0)} EGP"
                description = f"Staff: {record.get('staff', 'Unknown')} | {record.get('time', 'Unknown')}"
            elif record_type == "expense_log":
                label = f"{record.get('name', 'Unknown')} - {record.get('amount', 0)} EGP"
                description = f"Staff: {record.get('staff', 'Unknown')} | {record.get('time', 'Unknown')}"
            
            options.append(SelectOption(
                label=label[:100],  # Discord limit
                description=description[:100],
                value=str(i)
            ))
        
        super().__init__(placeholder=f"Select a {record_type.replace('_', ' ')} to delete...", 
                        min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: Interaction):
        try:
            index = int(self.values[0])
            selected_record = self.records[index]
            
            # Get the record ID based on type
            if self.record_type == "pc_session":
                record_id = selected_record.get('session_id')
            elif self.record_type == "service_log":
                record_id = selected_record.get('log_id')
            elif self.record_type == "expense_log":
                record_id = selected_record.get('log_id')
            
            if not record_id:
                await interaction.response.send_message("❌ Record ID not found.", ephemeral=True)
                return
            
            # Delete the record
            success = False
            if self.record_type == "pc_session":
                success = db.delete_pc_session(record_id)
            elif self.record_type == "service_log":
                success = db.delete_service_log(record_id)
            elif self.record_type == "expense_log":
                success = db.delete_expense_log(record_id)
            
            if success:
                embed = Embed(
                    title="✅ Record Deleted Successfully",
                    description=f"The {self.record_type.replace('_', ' ')} has been deleted.",
                    color=Color.green()
                )
            else:
                embed = Embed(
                    title="❌ Delete Failed",
                    description="Could not delete the record. Please try again.",
                    color=Color.red()
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except (ValueError, IndexError) as e:
            await interaction.response.send_message("❌ Invalid selection.", ephemeral=True)

class EditRecords(commands.Cog):
    def __init__(self, client):
        self.client = client

    @slash_command(name="edit_any_record", description="Edit any record (PC sessions, services, or expenses)")
    async def edit_any_record(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get all types of records
        pc_records = db.get_pc_sessions()
        service_records = db.get_service_logs()
        expense_records = db.get_expense_logs()
        
        total_records = len(pc_records) + len(service_records) + len(expense_records)
        
        if total_records == 0:
            embed = Embed(
                title="No Records Found",
                description="There are no records to edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Create a combined view with all record types
        embed = Embed(
            title="📝 Edit Any Record",
            description=f"**Total Records Available:** {total_records}\n\n"
                       f"💻 **PC Sessions:** {len(pc_records)}\n"
                       f"🛠️ **Service Logs:** {len(service_records)}\n"
                       f"🛒 **Expense Logs:** {len(expense_records)}\n\n"
                       f"Choose what type of record you want to edit:",
            color=Color.blue()
        )
        
        view = UniversalEditView()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @slash_command(name="edit_pc_session", description="Edit a PC session record")
    async def edit_pc_session(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get recent PC sessions
        records = db.get_pc_sessions()
        
        if not records:
            embed = Embed(
                title="No PC Sessions Found",
                description="There are no PC sessions to edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="💻 Edit PC Session",
            description=f"**Found {len(records)} PC sessions**\nSelect a PC session to edit from the dropdown below.",
            color=Color.blue()
        )
        
        view = RecordSelectorView(records, "pc_session")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @slash_command(name="edit_service_log", description="Edit a service log record")
    async def edit_service_log(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get recent service logs
        records = db.get_service_logs()
        
        if not records:
            embed = Embed(
                title="No Service Logs Found",
                description="There are no service logs to edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="🛠️ Edit Service Log",
            description=f"**Found {len(records)} service logs**\nSelect a service log to edit from the dropdown below.",
            color=Color.orange()
        )
        
        view = RecordSelectorView(records, "service_log")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @slash_command(name="edit_expense_log", description="Edit an expense log record")
    async def edit_expense_log(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get recent expense logs
        records = db.get_expense_logs()
        
        if not records:
            embed = Embed(
                title="No Expense Logs Found",
                description="There are no expense logs to edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="🛒 Edit Expense Log",
            description=f"**Found {len(records)} expense logs**\nSelect an expense log to edit from the dropdown below.",
            color=Color.red()
        )
        
        view = RecordSelectorView(records, "expense_log")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @slash_command(name="view_all_records", description="View all records with edit options")
    async def view_all_records(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        # Get all records
        pc_records = db.get_pc_sessions()
        service_records = db.get_service_logs()
        expense_records = db.get_expense_logs()
        
        total_records = len(pc_records) + len(service_records) + len(expense_records)
        
        if total_records == 0:
            embed = Embed(
                title="No Records Found",
                description="There are no records to view.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        # Calculate totals
        pc_total = sum(record.get('amount', 0) for record in pc_records)
        service_total = sum(record.get('amount', 0) for record in service_records)
        expense_total = sum(record.get('amount', 0) for record in expense_records)
        net_total = pc_total + service_total - expense_total
        
        embed = Embed(
            title="📊 All Records Summary",
            description=f"**Total Records:** {total_records}\n\n"
                       f"**Financial Summary:**\n"
                       f"💻 PC Sessions: {len(pc_records)} records - {pc_total:,} EGP\n"
                       f"🛠️ Service Logs: {len(service_records)} records - {service_total:,} EGP\n"
                       f"🛒 Expense Logs: {len(expense_records)} records - {expense_total:,} EGP\n"
                       f"💰 **Net Total:** {net_total:,} EGP\n\n"
                       f"Choose what you want to do:",
            color=Color.green()
        )
        
        view = AllRecordsView()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @slash_command(name="delete_record", description="Delete a record by ID")
    async def delete_record(self, interaction: Interaction, 
                          record_type: str = SlashOption(
                              name="type",
                              description="Type of record to delete",
                              choices={
                                  "PC Session": "pc_session",
                                  "Service Log": "service_log", 
                                  "Expense Log": "expense_log"
                              }
                          ),
                          record_id: str = SlashOption(
                              name="id",
                              description="ID of the record to delete"
                          )):
        await interaction.response.defer(ephemeral=True)
        
        try:
            success = False
            if record_type == "pc_session":
                success = db.delete_pc_session(record_id)
            elif record_type == "service_log":
                success = db.delete_service_log(record_id)
            elif record_type == "expense_log":
                success = db.delete_expense_log(record_id)
            
            if success:
                embed = Embed(
                    title="✅ Record Deleted Successfully",
                    description=f"The {record_type.replace('_', ' ')} has been deleted.",
                    color=Color.green()
                )
            else:
                embed = Embed(
                    title="❌ Delete Failed",
                    description="Could not find or delete the record.",
                    color=Color.red()
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            embed = Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)}",
                color=Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @slash_command(name="search_records", description="Search for specific records")
    async def search_records(self, interaction: Interaction,
                           search_term: str = SlashOption(
                               name="term",
                               description="Search term (PC number, service name, expense name, or staff name)"
                           )):
        await interaction.response.defer(ephemeral=True)
        
        # Search in all record types
        pc_records = db.get_pc_sessions()
        service_records = db.get_service_logs()
        expense_records = db.get_expense_logs()
        
        # Filter records based on search term
        search_lower = search_term.lower()
        
        matching_pcs = [r for r in pc_records if 
                       search_lower in r.get('pc', '').lower() or 
                       search_lower in r.get('staff', '').lower() or
                       search_lower in str(r.get('amount', 0))]
        
        matching_services = [r for r in service_records if 
                           search_lower in r.get('service', '').lower() or 
                           search_lower in r.get('staff', '').lower() or
                           search_lower in str(r.get('amount', 0))]
        
        matching_expenses = [r for r in expense_records if 
                           search_lower in r.get('name', '').lower() or 
                           search_lower in r.get('staff', '').lower() or
                           search_lower in str(r.get('amount', 0))]
        
        total_matches = len(matching_pcs) + len(matching_services) + len(matching_expenses)
        
        if total_matches == 0:
            embed = Embed(
                title="No Matching Records Found",
                description=f"No records found matching '{search_term}'",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title=f"🔍 Search Results for '{search_term}'",
            description=f"**Found {total_matches} matching records:**\n\n"
                       f"💻 **PC Sessions:** {len(matching_pcs)}\n"
                       f"🛠️ **Service Logs:** {len(matching_services)}\n"
                       f"🛒 **Expense Logs:** {len(matching_expenses)}\n\n"
                       f"Choose what you want to do with the results:",
            color=Color.blue()
        )
        
        view = SearchResultsView(matching_pcs, matching_services, matching_expenses)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @slash_command(name="bulk_edit", description="Edit multiple records at once")
    async def bulk_edit(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        embed = Embed(
            title="📝 Bulk Edit Records",
            description="Choose what type of records you want to bulk edit:",
            color=Color.purple()
        )
        
        view = BulkEditView()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class SearchResultsView(View):
    def __init__(self, pc_records, service_records, expense_records):
        super().__init__(timeout=60)
        self.pc_records = pc_records
        self.service_records = service_records
        self.expense_records = expense_records
    
    @Button(label="💻 Edit PC Results", style=ButtonStyle.blue, emoji="💻")
    async def edit_pc_results(self, button: Button, interaction: Interaction):
        if not self.pc_records:
            await interaction.response.send_message("No PC sessions in search results.", ephemeral=True)
            return
        
        embed = Embed(
            title="💻 Edit PC Sessions (Search Results)",
            description=f"**Found {len(self.pc_records)} matching PC sessions**\nSelect one to edit:",
            color=Color.blue()
        )
        
        view = RecordSelectorView(self.pc_records, "pc_session")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @Button(label="🛠️ Edit Service Results", style=ButtonStyle.orange, emoji="🛠️")
    async def edit_service_results(self, button: Button, interaction: Interaction):
        if not self.service_records:
            await interaction.response.send_message("No service logs in search results.", ephemeral=True)
            return
        
        embed = Embed(
            title="🛠️ Edit Service Logs (Search Results)",
            description=f"**Found {len(self.service_records)} matching service logs**\nSelect one to edit:",
            color=Color.orange()
        )
        
        view = RecordSelectorView(self.service_records, "service_log")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @Button(label="🛒 Edit Expense Results", style=ButtonStyle.red, emoji="🛒")
    async def edit_expense_results(self, button: Button, interaction: Interaction):
        if not self.expense_records:
            await interaction.response.send_message("No expense logs in search results.", ephemeral=True)
            return
        
        embed = Embed(
            title="🛒 Edit Expense Logs (Search Results)",
            description=f"**Found {len(self.expense_records)} matching expense logs**\nSelect one to edit:",
            color=Color.red()
        )
        
        view = RecordSelectorView(self.expense_records, "expense_log")
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class BulkEditView(View):
    def __init__(self):
        super().__init__(timeout=60)
    
    @Button(label="💻 Bulk Edit PC Sessions", style=ButtonStyle.blue, emoji="💻")
    async def bulk_edit_pcs(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        records = db.get_pc_sessions()
        if not records:
            embed = Embed(
                title="No PC Sessions Found",
                description="There are no PC sessions to bulk edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="💻 Bulk Edit PC Sessions",
            description=f"**Found {len(records)} PC sessions**\n"
                       f"Select multiple PC sessions to edit (up to 10):",
            color=Color.blue()
        )
        
        view = BulkEditSelectorView(records, "pc_session")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @Button(label="🛠️ Bulk Edit Service Logs", style=ButtonStyle.orange, emoji="🛠️")
    async def bulk_edit_services(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        records = db.get_service_logs()
        if not records:
            embed = Embed(
                title="No Service Logs Found",
                description="There are no service logs to bulk edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="🛠️ Bulk Edit Service Logs",
            description=f"**Found {len(records)} service logs**\n"
                       f"Select multiple service logs to edit (up to 10):",
            color=Color.orange()
        )
        
        view = BulkEditSelectorView(records, "service_log")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    
    @Button(label="🛒 Bulk Edit Expense Logs", style=ButtonStyle.red, emoji="🛒")
    async def bulk_edit_expenses(self, button: Button, interaction: Interaction):
        await interaction.response.defer(ephemeral=True)
        
        records = db.get_expense_logs()
        if not records:
            embed = Embed(
                title="No Expense Logs Found",
                description="There are no expense logs to bulk edit.",
                color=Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        embed = Embed(
            title="🛒 Bulk Edit Expense Logs",
            description=f"**Found {len(records)} expense logs**\n"
                       f"Select multiple expense logs to edit (up to 10):",
            color=Color.red()
        )
        
        view = BulkEditSelectorView(records, "expense_log")
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class BulkEditSelectorView(View):
    def __init__(self, records, record_type):
        super().__init__(timeout=60)
        self.add_item(BulkEditSelector(records, record_type))

class BulkEditSelector(Select):
    def __init__(self, records, record_type):
        self.records = records
        self.record_type = record_type
        
        options = []
        for i, record in enumerate(records[:25]):  # Discord limit
            if record_type == "pc_session":
                label = f"PC {record.get('pc', 'Unknown')} - {record.get('amount', 0)} EGP"
                description = f"Staff: {record.get('staff', 'Unknown')} | {record.get('time', 'Unknown')}"
            elif record_type == "service_log":
                label = f"{record.get('service', 'Unknown')} - {record.get('amount', 0)} EGP"
                description = f"Staff: {record.get('staff', 'Unknown')} | {record.get('time', 'Unknown')}"
            elif record_type == "expense_log":
                label = f"{record.get('name', 'Unknown')} - {record.get('amount', 0)} EGP"
                description = f"Staff: {record.get('staff', 'Unknown')} | {record.get('time', 'Unknown')}"
            
            options.append(SelectOption(
                label=label[:100],  # Discord limit
                description=description[:100],
                value=str(i)
            ))
        
        super().__init__(placeholder=f"Select multiple {record_type.replace('_', ' ')}s to edit...", 
                        min_values=1, max_values=min(10, len(records)), options=options)
    
    async def callback(self, interaction: Interaction):
        try:
            selected_indices = [int(i) for i in self.values]
            selected_records = [self.records[i] for i in selected_indices]
            
            embed = Embed(
                title=f"📝 Bulk Edit {self.record_type.replace('_', ' ').title()}s",
                description=f"**Selected {len(selected_records)} records for editing**\n\n"
                           f"**Note:** You'll need to edit each record individually. "
                           f"Use the individual edit commands for each selected record.",
                color=Color.blue()
            )
            
            # Show selected records
            for i, record in enumerate(selected_records[:5]):  # Show first 5
                if self.record_type == "pc_session":
                    embed.add_field(
                        name=f"PC Session {i+1}",
                        value=f"PC: {record.get('pc', 'Unknown')} | Amount: {record.get('amount', 0)} EGP",
                        inline=False
                    )
                elif self.record_type == "service_log":
                    embed.add_field(
                        name=f"Service Log {i+1}",
                        value=f"Service: {record.get('service', 'Unknown')} | Amount: {record.get('amount', 0)} EGP",
                        inline=False
                    )
                elif self.record_type == "expense_log":
                    embed.add_field(
                        name=f"Expense Log {i+1}",
                        value=f"Expense: {record.get('name', 'Unknown')} | Amount: {record.get('amount', 0)} EGP",
                        inline=False
                    )
            
            if len(selected_records) > 5:
                embed.add_field(
                    name="...",
                    value=f"And {len(selected_records) - 5} more records",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except (ValueError, IndexError) as e:
            await interaction.response.send_message("❌ Invalid selection.", ephemeral=True)

def setup(client):
    client.add_cog(EditRecords(client))
