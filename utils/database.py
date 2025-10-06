from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import os
from dotenv import load_dotenv
from pprint import pprint
import json
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
DB_TOKEN = os.getenv('DB_TOKEN')

if not DB_TOKEN:
    raise Exception("DB_TOKEN not found in .env file. Please add your MongoDB connection string.")

try:
    db = MongoClient(DB_TOKEN)
    # Test connection
    db.admin.command('ping')
    print("✅ Connected to MongoDB successfully!")
    try:
        db.cyber.users.create_index("username", unique=True)
    except Exception:
        pass
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    print("Please check your DB_TOKEN in the .env file")
    raise e

def load_services():
    try:
        services = list(db.cyber.services.find({}, {"_id": 0}).sort("name", 1))  
        if not services:
            return []
        return services
        
    except Exception as e:
        print(f"[Services] Error loading file: {e}")
        return []

def save_service(data):
    try:
        db.cyber.services.insert_one(data)
    except Exception as e:
        print(f"Error Saving Document\nError: {e}")

def update_service(update):
    try:
        service_name = update['name']
        # Only set provided fields except 'name'
        fields_to_set = {k: v for k, v in update.items() if k != "name"}
        if not fields_to_set:
            return {"matched": 0, "modified": 0, "error": "no updatable fields provided"}

        result = db.cyber.services.update_one({"name": service_name}, {"$set": fields_to_set})
        return {"matched": result.matched_count, "modified": result.modified_count}
    except Exception as e:
        print(f"Error updating service\nError: {e}")
        return {"matched": 0, "modified": 0, "error": str(e)}

def delete_service(name):
    try:
        db.cyber.services.delete_one({"name": name})
    except Exception as e:
        print(f"Error deleting service\nError: {e}")


def save_logs():
    try:
        with open('current_day.json','r',encoding='utf-8') as f:
            doc = json.load(f)

        now = datetime.now(timezone.utc)
        doc["date"] = now.strftime("%Y-%m-%d")  # e.g. 2025-09-29
        db.cyber.logs.insert_one(doc)
        
        # Generate PDF report
        generate_daily_pdf_report(doc)
        
        default = {
            "pcs": [],
            "services": [],
            "expenses":[],
            "totals": {"pcs": 0, "services": 0,"expenses":0, "all": 0},
            "log_channel_id": None
        }
        with open('current_day.json','w',encoding='utf-8') as f:
            json.dump(default,f,indent=4)
    except Exception as e:
        print(f"Error Saving Logs\nError: {e}")

# MongoDB operations for PC sessions
def save_pc_session(session_data):
    try:
        db.cyber.pc_sessions.insert_one(session_data)
    except Exception as e:
        print(f"Error saving PC session: {e}")

def get_pc_sessions(date=None):
    try:
        query = {}
        if date:
            query["date"] = date
        return list(db.cyber.pc_sessions.find(query, {"_id": 0}).sort("timestamp", -1))
    except Exception as e:
        print(f"Error getting PC sessions: {e}")
        return []

def update_pc_session(session_id, update_data):
    try:
        result = db.cyber.pc_sessions.update_one(
            {"session_id": session_id}, 
            {"$set": update_data},
            upsert=True
        )
        return (result.modified_count > 0) or (result.matched_count > 0) or (getattr(result, 'upserted_id', None) is not None)
    except Exception as e:
        print(f"Error updating PC session: {e}")
        return False

def delete_pc_session(session_id):
    try:
        result = db.cyber.pc_sessions.delete_one({"session_id": session_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting PC session: {e}")
        return False

# MongoDB operations for service logs
def save_service_log(service_data):
    try:
        db.cyber.service_logs.insert_one(service_data)
    except Exception as e:
        print(f"Error saving service log: {e}")

def get_service_logs(date=None):
    try:
        query = {}
        if date:
            query["date"] = date
        return list(db.cyber.service_logs.find(query, {"_id": 0}).sort("timestamp", -1))
    except Exception as e:
        print(f"Error getting service logs: {e}")
        return []

def update_service_log(log_id, update_data):
    try:
        result = db.cyber.service_logs.update_one(
            {"log_id": log_id}, 
            {"$set": update_data},
            upsert=True
        )
        return (result.modified_count > 0) or (result.matched_count > 0) or (getattr(result, 'upserted_id', None) is not None)
    except Exception as e:
        print(f"Error updating service log: {e}")
        return False

def delete_service_log(log_id):
    try:
        result = db.cyber.service_logs.delete_one({"log_id": log_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting service log: {e}")
        return False

# MongoDB operations for expense logs
def save_expense_log(expense_data):
    try:
        db.cyber.expense_logs.insert_one(expense_data)
    except Exception as e:
        print(f"Error saving expense log: {e}")

def get_expense_logs(date=None):
    try:
        query = {}
        if date:
            query["date"] = date
        return list(db.cyber.expense_logs.find(query, {"_id": 0}).sort("timestamp", -1))
    except Exception as e:
        print(f"Error getting expense logs: {e}")
        return []

def update_expense_log(log_id, update_data):
    try:
        result = db.cyber.expense_logs.update_one(
            {"log_id": log_id}, 
            {"$set": update_data},
            upsert=True
        )
        return (result.modified_count > 0) or (result.matched_count > 0) or (getattr(result, 'upserted_id', None) is not None)
    except Exception as e:
        print(f"Error updating expense log: {e}")
        return False

def delete_expense_log(log_id):
    try:
        result = db.cyber.expense_logs.delete_one({"log_id": log_id})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting expense log: {e}")
        return False

# ==================== USER AUTH HELPERS ====================
def create_user(username: str, password: str):
    try:
        if not username or not password:
            return False, "Username and password are required"
        password_hash = generate_password_hash(password)
        user_doc = {
            "username": username,
            "password_hash": password_hash,
            "created_at": datetime.now(),
            "role": "worker",
        }
        db.cyber.users.insert_one(user_doc)
        return True, None
    except DuplicateKeyError:
        return False, "Username already exists"
    except Exception as e:
        print(f"Error creating user: {e}")
        return False, "Internal error"

def get_user_by_username(username: str):
    try:
        return db.cyber.users.find_one({"username": username}, {"_id": 0})
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def verify_user_credentials(username: str, password: str):
    try:
        user = db.cyber.users.find_one({"username": username})
        if not user:
            return False
        return check_password_hash(user.get("password_hash", ""), password)
    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return False

def users_count():
    try:
        return db.cyber.users.estimated_document_count()
    except Exception:
        return 0

def reset_all_users():
    try:
        # Drop users collection entirely
        db.cyber.users.drop()
        # Recreate unique index on username
        try:
            db.cyber.users.create_index("username", unique=True)
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"Error resetting users: {e}")
        return False

def set_user_role(username: str, role: str):
    try:
        result = db.cyber.users.update_one({"username": username}, {"$set": {"role": role}})
        return result.modified_count > 0
    except Exception as e:
        print(f"Error setting user role: {e}")
        return False

def update_user_password(username: str, new_password: str):
    try:
        if not new_password:
            return False
        password_hash = generate_password_hash(new_password)
        result = db.cyber.users.update_one({"username": username}, {"$set": {"password_hash": password_hash}})
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating user password: {e}")
        return False

def update_user_fields(username: str, role: str | None = None, new_password: str | None = None):
    try:
        update_doc = {}
        if role:
            update_doc["role"] = role
        if new_password:
            update_doc["password_hash"] = generate_password_hash(new_password)
        if not update_doc:
            return False
        result = db.cyber.users.update_one({"username": username}, {"$set": update_doc})
        return result.modified_count > 0
    except Exception as e:
        print(f"Error updating user fields: {e}")
        return False

def rename_user(old_username: str, new_username: str):
    try:
        if not new_username:
            return False, "New username required"
        # Ensure unique
        if db.cyber.users.find_one({"username": new_username}):
            return False, "Username already exists"
        result = db.cyber.users.update_one({"username": old_username}, {"$set": {"username": new_username}})
        return result.modified_count > 0, None
    except Exception as e:
        print(f"Error renaming user: {e}")
        return False, "Internal error"

def delete_user(username: str):
    try:
        result = db.cyber.users.delete_one({"username": username})
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False

# PDF Report Generation
def generate_daily_pdf_report(data):
    try:
        date_str = data.get("date", datetime.now().strftime("%Y-%m-%d"))
        filename = f"daily_report_{date_str}.pdf"
        
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        )
        story.append(Paragraph(f"Daily Report - {date_str}", title_style))
        story.append(Spacer(1, 20))
        
        # Summary section
        totals = data.get("totals", {})
        summary_data = [
            ['Category', 'Amount (EGP)'],
            ['PC Sessions', f"{totals.get('pcs', 0):,}"],
            ['Services', f"{totals.get('services', 0):,}"],
            ['Expenses', f"{totals.get('expenses', 0):,}"],
            ['Total Income', f"{totals.get('all', 0):,}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Daily Summary", styles['Heading2']))
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # PC Sessions details
        pcs = data.get("pcs", [])
        if pcs:
            story.append(Paragraph("PC Sessions", styles['Heading2']))
            pc_data = [['PC', 'Amount', 'Staff', 'Time']]
            for pc in pcs:
                pc_data.append([
                    pc.get('pc', 'N/A'),
                    f"{pc.get('amount', 0):,} EGP",
                    pc.get('staff', 'N/A'),
                    pc.get('time', 'N/A')
                ])
            
            pc_table = Table(pc_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            pc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(pc_table)
            story.append(Spacer(1, 20))
        
        # Services details
        services = data.get("services", [])
        if services:
            story.append(Paragraph("Services", styles['Heading2']))
            service_data = [['Service', 'Amount', 'Staff', 'Time']]
            for service in services:
                service_data.append([
                    service.get('service', 'N/A'),
                    f"{service.get('amount', 0):,} EGP",
                    service.get('staff', 'N/A'),
                    service.get('time', 'N/A')
                ])
            
            service_table = Table(service_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            service_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.orange),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(service_table)
            story.append(Spacer(1, 20))
        
        # Expenses details
        expenses = data.get("expenses", [])
        if expenses:
            story.append(Paragraph("Expenses", styles['Heading2']))
            expense_data = [['Expense', 'Amount', 'Staff', 'Time']]
            for expense in expenses:
                expense_data.append([
                    expense.get('name', 'N/A'),
                    f"{expense.get('amount', 0):,} EGP",
                    expense.get('staff', 'N/A'),
                    expense.get('time', 'N/A')
                ])
            
            expense_table = Table(expense_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.red),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(expense_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,
            textColor=colors.grey
        )
        story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
        
        doc.build(story)
        print(f"PDF report generated: {filename}")
        return filename
        
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        return None
