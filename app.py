from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from datetime import datetime, timezone
import json
import os
from utils.database import (
    load_services, save_service, update_service, delete_service, 
    save_logs, db, get_pc_sessions, get_service_logs, get_expense_logs,
    update_pc_session, update_service_log, update_expense_log,
    delete_pc_session, delete_service_log, delete_expense_log,
    save_pc_session, save_service_log, save_expense_log
)
from utils.utils import load_data, save_data, calc_totals, cost_to_time

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production

@app.route('/')
def dashboard():
    """Main dashboard showing summary and quick actions"""
    data = load_data()
    services = load_services()
    
    # Calculate totals
    pcs_total, services_total, expenses_total, total_all = calc_totals(data)
    
    # Recent activities (last 5 of each type)
    recent_pcs = data.get('pcs', [])[-5:]
    recent_services = data.get('services', [])[-5:]
    recent_expenses = data.get('expenses', [])[-5:]
    
    return render_template('dashboard.html', 
                         pcs_total=pcs_total,
                         services_total=services_total,
                         expenses_total=expenses_total,
                         total_all=total_all,
                         recent_pcs=recent_pcs,
                         recent_services=recent_services,
                         recent_expenses=recent_expenses,
                         services_count=len(services))

@app.route('/pc-logging')
def pc_logging():
    """PC session logging page"""
    return render_template('pc_logging.html')

@app.route('/log-pc', methods=['POST'])
def log_pc():
    """Handle PC session logging"""
    try:
        pc_number = request.form.get('pc_number')
        cost = int(request.form.get('cost'))
        notes = request.form.get('notes', '')
        staff = request.form.get('staff', 'Web User')
        
        if not pc_number or cost <= 0:
            flash('Please provide valid PC number and cost', 'error')
            return redirect(url_for('pc_logging'))
        
        # Generate unique session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Log the session to JSON only
        data = load_data()
        today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
        
        session_data = {
            "session_id": session_id,
            "pc": f"PC {pc_number}",
            "amount": cost,
            "staff": staff,
            "time": today_full
        }
        
        if notes:
            session_data['notes'] = notes
        
        data["pcs"].append(session_data)
        
        # Update totals
        pcs_total, services_total, expenses_total, total_all = calc_totals(data)
        data["totals"] = {
            "pcs": pcs_total,
            "services": services_total,
            "expenses": expenses_total,
            "all": total_all
        }
        
        save_data(data)
        
        session_time = cost_to_time(cost)
        flash(f'PC {pc_number} session logged successfully! Time equivalent: {session_time}', 'success')
        
    except ValueError:
        flash('Cost must be a valid number', 'error')
    except Exception as e:
        flash(f'Error logging session: {str(e)}', 'error')
    
    return redirect(url_for('pc_logging'))

@app.route('/services')
def services():
    """Services management page"""
    services_list = load_services()
    return render_template('services.html', services=services_list)

@app.route('/add-service', methods=['POST'])
def add_service():
    """Add a new service"""
    try:
        service_name = request.form.get('service_name')
        cost = int(request.form.get('cost'))
        emoji = request.form.get('emoji', '🔧')
        custom_cost = request.form.get('custom_cost') == 'true'
        available = request.form.get('available') == 'true'
        
        if not service_name:
            flash('Service name is required', 'error')
            return redirect(url_for('services'))
        
        # Check if service already exists
        existing_services = load_services()
        for service in existing_services:
            if service['name'].lower() == service_name.lower():
                flash('Service already exists', 'error')
                return redirect(url_for('services'))
        
        service_doc = {
            "name": service_name,
            "cost": cost,
            "emoji": emoji,
            "available": available,
            "custom_cost": custom_cost
        }
        
        save_service(service_doc)
        flash(f'Service "{service_name}" added successfully!', 'success')
        
    except ValueError:
        flash('Cost must be a valid number', 'error')
    except Exception as e:
        flash(f'Error adding service: {str(e)}', 'error')
    
    return redirect(url_for('services'))

@app.route('/edit-service/<service_name>')
def edit_service_form(service_name):
    """Show edit form for a specific service"""
    try:
        services_list = load_services()
        service = None
        for s in services_list:
            if s['name'] == service_name:
                service = s
                break
        
        if not service:
            flash('Service not found', 'error')
            return redirect(url_for('services'))
        
        return render_template('edit_service.html', service=service)
    except Exception as e:
        flash(f'Error loading service: {str(e)}', 'error')
        return redirect(url_for('services'))

@app.route('/update-service/<service_name>', methods=['POST'])
def update_service_route(service_name):
    """Update service availability or details"""
    try:
        action = request.form.get('action')
        
        if action == 'toggle':
            # Toggle availability
            services_list = load_services()
            current_service = None
            for service in services_list:
                if service['name'] == service_name:
                    current_service = service
                    break
            
            if current_service:
                new_availability = not current_service['available']
                result = update_service({"name": service_name, "available": new_availability})
                status = "enabled" if new_availability else "disabled"
                flash(f'Service "{service_name}" {status} successfully!', 'success')
            else:
                flash('Service not found', 'error')
        
        elif action == 'delete':
            delete_service(service_name)
            flash(f'Service "{service_name}" deleted successfully!', 'success')
        
        elif action == 'edit':
            # Handle full service edit
            new_name = request.form.get('service_name')
            cost = int(request.form.get('cost'))
            emoji = request.form.get('emoji', '🔧')
            custom_cost = request.form.get('custom_cost') == 'true'
            available = request.form.get('available') == 'true'
            
            if not new_name:
                flash('Service name is required', 'error')
                return redirect(url_for('edit_service_form', service_name=service_name))
            
            # Check if new name conflicts with existing service (except current one)
            if new_name != service_name:
                existing_services = load_services()
                for service in existing_services:
                    if service['name'].lower() == new_name.lower() and service['name'] != service_name:
                        flash('A service with this name already exists', 'error')
                        return redirect(url_for('edit_service_form', service_name=service_name))
            
            # If name changed, we need to delete old and create new
            if new_name != service_name:
                delete_service(service_name)
                service_doc = {
                    "name": new_name,
                    "cost": cost,
                    "emoji": emoji,
                    "available": available,
                    "custom_cost": custom_cost
                }
                save_service(service_doc)
                flash(f'Service updated successfully! Name changed from "{service_name}" to "{new_name}"', 'success')
            else:
                # Update existing service
                update_data = {
                    "name": service_name,
                    "cost": cost,
                    "emoji": emoji,
                    "available": available,
                    "custom_cost": custom_cost
                }
                result = update_service(update_data)
                flash(f'Service "{service_name}" updated successfully!', 'success')
            
    except ValueError:
        flash('Cost must be a valid number', 'error')
        return redirect(url_for('edit_service_form', service_name=service_name))
    except Exception as e:
        flash(f'Error updating service: {str(e)}', 'error')
        return redirect(url_for('edit_service_form', service_name=service_name))
    
    return redirect(url_for('services'))

@app.route('/service-logging')
def service_logging():
    """Service logging page"""
    services_list = load_services()
    available_services = [s for s in services_list if s['available']]
    return render_template('service_logging.html', services=available_services)

@app.route('/log-service', methods=['POST'])
def log_service():
    """Handle service logging"""
    try:
        service_name = request.form.get('service_name')
        staff = request.form.get('staff', 'Web User')
        custom_cost = request.form.get('custom_cost')
        
        if not service_name:
            flash('Please select a service', 'error')
            return redirect(url_for('service_logging'))
        
        # Get service details
        services_list = load_services()
        selected_service = None
        for service in services_list:
            if service['name'] == service_name:
                selected_service = service
                break
        
        if not selected_service:
            flash('Service not found', 'error')
            return redirect(url_for('service_logging'))
        
        # Determine cost
        if selected_service['custom_cost'] and custom_cost:
            cost = int(custom_cost)
        else:
            cost = selected_service['cost']
        
        # Generate unique log ID
        import uuid
        log_id = str(uuid.uuid4())
        
        # Log the service to JSON only
        data = load_data()
        today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
        
        data["services"].append({
            "log_id": log_id,
            "service": service_name,
            "amount": cost,
            "staff": staff,
            "time": today_full
        })
        
        # Update totals
        pcs_total, services_total, expenses_total, total_all = calc_totals(data)
        data["totals"] = {
            "pcs": pcs_total,
            "services": services_total,
            "expenses": expenses_total,
            "all": total_all
        }
        
        save_data(data)
        
        flash(f'Service "{service_name}" logged successfully! Cost: {cost} EGP', 'success')
        
    except ValueError:
        flash('Custom cost must be a valid number', 'error')
    except Exception as e:
        flash(f'Error logging service: {str(e)}', 'error')
    
    return redirect(url_for('service_logging'))

@app.route('/expenses')
def expenses():
    """Expenses logging page"""
    data = load_data()
    expenses_list = data.get('expenses', [])
    return render_template('expenses.html', expenses=expenses_list)

@app.route('/log-expense', methods=['POST'])
def log_expense():
    """Handle expense logging"""
    try:
        expense_name = request.form.get('expense_name')
        cost = int(request.form.get('cost'))
        staff = request.form.get('staff', 'Web User')
        
        if not expense_name or cost <= 0:
            flash('Please provide valid expense name and cost', 'error')
            return redirect(url_for('expenses'))
        
        # Generate unique log ID
        import uuid
        log_id = str(uuid.uuid4())
        
        # Log the expense to JSON only
        data = load_data()
        today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
        
        data["expenses"].append({
            "log_id": log_id,
            "name": expense_name,
            "amount": cost,
            "staff": staff,
            "time": today_full
        })
        
        # Update totals
        pcs_total, services_total, expenses_total, total_all = calc_totals(data)
        data["totals"] = {
            "pcs": pcs_total,
            "services": services_total,
            "expenses": expenses_total,
            "all": total_all
        }
        
        save_data(data)
        
        flash(f'Expense "{expense_name}" logged successfully! Cost: {cost} EGP', 'success')
        
    except ValueError:
        flash('Cost must be a valid number', 'error')
    except Exception as e:
        flash(f'Error logging expense: {str(e)}', 'error')
    
    return redirect(url_for('expenses'))

@app.route('/history')
def history():
    """View historical logs from database"""
    try:
        # Get logs from database
        logs = list(db.cyber.logs.find({}, {"_id": 0}).sort("date", -1))
        
        # Ensure all logs have required fields with defaults
        for log in logs:
            # Ensure expenses field exists
            if 'expenses' not in log:
                log['expenses'] = []
            
            # Ensure totals has all required fields
            if 'totals' not in log:
                log['totals'] = {}
            
            # Set default values for missing totals
            if 'expenses' not in log['totals']:
                log['totals']['expenses'] = 0
            if 'pcs' not in log['totals']:
                log['totals']['pcs'] = 0
            if 'services' not in log['totals']:
                log['totals']['services'] = 0
            if 'all' not in log['totals']:
                log['totals']['all'] = log['totals']['pcs'] + log['totals']['services'] - log['totals']['expenses']
        
        return render_template('history.html', logs=logs)
    except Exception as e:
        flash(f'Error loading history: {str(e)}', 'error')
        return render_template('history.html', logs=[])

@app.route('/save-logs', methods=['POST'])
def save_logs_route():
    """Save current day logs to database and reset"""
    try:
        # Get current day data
        data = load_data()
        
        # Move records from JSON to MongoDB
        for pc_record in data.get('pcs', []):
            mongo_data = {
                "session_id": pc_record.get('session_id'),
                "pc": pc_record.get('pc'),
                "amount": pc_record.get('amount'),
                "staff": pc_record.get('staff'),
                "time": pc_record.get('time'),
                "notes": pc_record.get('notes'),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now()
            }
            save_pc_session(mongo_data)
        
        for service_record in data.get('services', []):
            mongo_data = {
                "log_id": service_record.get('log_id'),
                "service": service_record.get('service'),
                "amount": service_record.get('amount'),
                "staff": service_record.get('staff'),
                "time": service_record.get('time'),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now()
            }
            save_service_log(mongo_data)
        
        for expense_record in data.get('expenses', []):
            mongo_data = {
                "log_id": expense_record.get('log_id'),
                "name": expense_record.get('name'),
                "amount": expense_record.get('amount'),
                "staff": expense_record.get('staff'),
                "time": expense_record.get('time'),
                "date": datetime.now().strftime("%Y-%m-%d"),
                "timestamp": datetime.now()
            }
            save_expense_log(mongo_data)
        
        # Save to logs collection and generate PDF
        save_logs()
        
        flash('Daily logs saved and archived successfully! PDF report generated.', 'success')
    except Exception as e:
        flash(f'Error saving logs: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/download-pdf/<date>')
def download_pdf(date):
    """Download PDF report for a specific date"""
    try:
        filename = f"daily_report_{date}.pdf"
        if os.path.exists(filename):
            return send_file(filename, as_attachment=True)
        else:
            flash('PDF report not found for this date', 'error')
            return redirect(url_for('history'))
    except Exception as e:
        flash(f'Error downloading PDF: {str(e)}', 'error')
        return redirect(url_for('history'))

@app.route('/api/summary')
def api_summary():
    """API endpoint for summary data (for dynamic updates)"""
    data = load_data()
    pcs_total, services_total, expenses_total, total_all = calc_totals(data)
    
    return jsonify({
        'pcs_total': pcs_total,
        'services_total': services_total,
        'expenses_total': expenses_total,
        'total_all': total_all,
        'pcs_count': len(data.get('pcs', [])),
        'services_count': len(data.get('services', [])),
        'expenses_count': len(data.get('expenses', []))
    })

# ==================== EDIT CURRENT DAY RECORDS ====================

@app.route('/edit-current-pc/<session_id>')
def edit_current_pc_form(session_id):
    """Edit current day PC session form"""
    try:
        data = load_data()
        session = None
        for s in data.get('pcs', []):
            if s.get('session_id') == session_id:
                session = s
                break
        
        if not session:
            flash('PC session not found', 'error')
            return redirect(url_for('edit_records'))
        
        return render_template('edit_pc_session.html', session=session)
    except Exception as e:
        flash(f'Error loading PC session: {str(e)}', 'error')
        return redirect(url_for('edit_records'))

@app.route('/update-current-pc/<session_id>', methods=['POST'])
def update_current_pc_route(session_id):
    """Update current day PC session"""
    try:
        pc = request.form.get('pc')
        amount = int(request.form.get('amount'))
        notes = request.form.get('notes', '')
        staff = request.form.get('staff', 'Web User')
        
        if not pc or amount <= 0:
            flash('Please provide valid PC number and amount', 'error')
            return redirect(url_for('edit_current_pc_form', session_id=session_id))
        
        # Update in JSON file
        data = load_data()
        for i, session in enumerate(data.get('pcs', [])):
            if session.get('session_id') == session_id:
                data['pcs'][i].update({
                    "pc": pc,
                    "amount": amount,
                    "notes": notes,
                    "staff": staff
                })
                break
        
        # Recalculate totals
        data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
        save_data(data)
        
        flash(f'PC session updated successfully!', 'success')
        
    except ValueError:
        flash('Amount must be a valid number', 'error')
    except Exception as e:
        flash(f'Error updating PC session: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

@app.route('/edit-current-service/<log_id>')
def edit_current_service_form(log_id):
    """Edit current day service log form"""
    try:
        data = load_data()
        log = None
        for l in data.get('services', []):
            if l.get('log_id') == log_id:
                log = l
                break
        
        if not log:
            flash('Service log not found', 'error')
            return redirect(url_for('edit_records'))
        
        return render_template('edit_service_log.html', log=log)
    except Exception as e:
        flash(f'Error loading service log: {str(e)}', 'error')
        return redirect(url_for('edit_records'))

@app.route('/update-current-service/<log_id>', methods=['POST'])
def update_current_service_route(log_id):
    """Update current day service log"""
    try:
        service = request.form.get('service')
        amount = int(request.form.get('amount'))
        staff = request.form.get('staff', 'Web User')
        
        if not service or amount <= 0:
            flash('Please provide valid service name and amount', 'error')
            return redirect(url_for('edit_current_service_form', log_id=log_id))
        
        # Update in JSON file
        data = load_data()
        for i, log in enumerate(data.get('services', [])):
            if log.get('log_id') == log_id:
                data['services'][i].update({
                    "service": service,
                    "amount": amount,
                    "staff": staff
                })
                break
        
        # Recalculate totals
        data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
        save_data(data)
        
        flash(f'Service log updated successfully!', 'success')
        
    except ValueError:
        flash('Amount must be a valid number', 'error')
    except Exception as e:
        flash(f'Error updating service log: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

@app.route('/edit-current-expense/<log_id>')
def edit_current_expense_form(log_id):
    """Edit current day expense log form"""
    try:
        data = load_data()
        log = None
        for l in data.get('expenses', []):
            if l.get('log_id') == log_id:
                log = l
                break
        
        if not log:
            flash('Expense log not found', 'error')
            return redirect(url_for('edit_records'))
        
        return render_template('edit_expense_log.html', log=log)
    except Exception as e:
        flash(f'Error loading expense log: {str(e)}', 'error')
        return redirect(url_for('edit_records'))

@app.route('/update-current-expense/<log_id>', methods=['POST'])
def update_current_expense_route(log_id):
    """Update current day expense log"""
    try:
        name = request.form.get('name')
        amount = int(request.form.get('amount'))
        staff = request.form.get('staff', 'Web User')
        
        if not name or amount <= 0:
            flash('Please provide valid expense name and amount', 'error')
            return redirect(url_for('edit_current_expense_form', log_id=log_id))
        
        # Update in JSON file
        data = load_data()
        for i, log in enumerate(data.get('expenses', [])):
            if log.get('log_id') == log_id:
                data['expenses'][i].update({
                    "name": name,
                    "amount": amount,
                    "staff": staff
                })
                break
        
        # Recalculate totals
        data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
        save_data(data)
        
        flash(f'Expense log updated successfully!', 'success')
        
    except ValueError:
        flash('Amount must be a valid number', 'error')
    except Exception as e:
        flash(f'Error updating expense log: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

# ==================== DELETE CURRENT DAY RECORDS ====================

@app.route('/delete-current-pc/<session_id>')
def delete_current_pc_route(session_id):
    """Delete current day PC session"""
    try:
        data = load_data()
        data['pcs'] = [s for s in data.get('pcs', []) if s.get('session_id') != session_id]
        
        # Recalculate totals
        data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
        save_data(data)
        
        flash('PC session deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting PC session: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

@app.route('/delete-current-service/<log_id>')
def delete_current_service_route(log_id):
    """Delete current day service log"""
    try:
        data = load_data()
        data['services'] = [s for s in data.get('services', []) if s.get('log_id') != log_id]
        
        # Recalculate totals
        data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
        save_data(data)
        
        flash('Service log deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting service log: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

@app.route('/delete-current-expense/<log_id>')
def delete_current_expense_route(log_id):
    """Delete current day expense log"""
    try:
        data = load_data()
        data['expenses'] = [e for e in data.get('expenses', []) if e.get('log_id') != log_id]
        
        # Recalculate totals
        data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
        save_data(data)
        
        flash('Expense log deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting expense log: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

# ==================== EDIT FUNCTIONALITY ====================

@app.route('/edit-records')
def edit_records():
    """Main edit records page"""
    # Get current day data from JSON file (for today's records)
    data = load_data()
    current_pcs = data.get('pcs', [])
    current_services = data.get('services', [])
    current_expenses = data.get('expenses', [])
    
    # Get all records from MongoDB (for historical records)
    mongo_pc_records = get_pc_sessions()
    mongo_service_records = get_service_logs()
    mongo_expense_records = get_expense_logs()
    
    # Combine current day records with MongoDB records, avoiding duplicates
    pc_records = current_pcs.copy()
    service_records = current_services.copy()
    expense_records = current_expenses.copy()
    
    # Add MongoDB records that aren't already in current day
    current_pc_ids = {record.get('session_id') for record in current_pcs if record.get('session_id')}
    current_service_ids = {record.get('log_id') for record in current_services if record.get('log_id')}
    current_expense_ids = {record.get('log_id') for record in current_expenses if record.get('log_id')}
    
    for record in mongo_pc_records:
        if record.get('session_id') not in current_pc_ids:
            pc_records.append(record)
    
    for record in mongo_service_records:
        if record.get('log_id') not in current_service_ids:
            service_records.append(record)
    
    for record in mongo_expense_records:
        if record.get('log_id') not in current_expense_ids:
            expense_records.append(record)
    
    # Calculate totals
    pc_total = sum(record.get('amount', 0) for record in pc_records)
    service_total = sum(record.get('amount', 0) for record in service_records)
    expense_total = sum(record.get('amount', 0) for record in expense_records)
    net_total = pc_total + service_total - expense_total
    
    return render_template('edit_records.html',
                         pc_records=pc_records,
                         service_records=service_records,
                         expense_records=expense_records,
                         pc_total=pc_total,
                         service_total=service_total,
                         expense_total=expense_total,
                         net_total=net_total,
                         current_pcs=current_pcs,
                         current_services=current_services,
                         current_expenses=current_expenses)

@app.route('/edit-pc-session/<session_id>')
def edit_pc_session_form(session_id):
    """Edit PC session form"""
    try:
        # Get the specific PC session
        pc_sessions = get_pc_sessions()
        session = None
        for s in pc_sessions:
            if s.get('session_id') == session_id:
                session = s
                break
        
        if not session:
            flash('PC session not found', 'error')
            return redirect(url_for('edit_records'))
        
        return render_template('edit_pc_session.html', session=session)
    except Exception as e:
        flash(f'Error loading PC session: {str(e)}', 'error')
        return redirect(url_for('edit_records'))

@app.route('/update-pc-session/<session_id>', methods=['POST'])
def update_pc_session_route(session_id):
    """Update PC session"""
    try:
        pc = request.form.get('pc')
        amount = int(request.form.get('amount'))
        notes = request.form.get('notes', '')
        staff = request.form.get('staff', 'Web User')
        
        if not pc or amount <= 0:
            flash('Please provide valid PC number and amount', 'error')
            return redirect(url_for('edit_pc_session_form', session_id=session_id))
        
        # Update in MongoDB
        update_data = {
            "pc": pc,
            "amount": amount,
            "notes": notes,
            "staff": staff
        }
        success = update_pc_session(session_id, update_data)
        
        if success:
            # Update in JSON file
            data = load_data()
            for i, session in enumerate(data.get('pcs', [])):
                if session.get('session_id') == session_id:
                    data['pcs'][i].update(update_data)
                    break
            
            # Recalculate totals
            data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
            save_data(data)
            
            flash(f'PC session updated successfully!', 'success')
        else:
            flash('Failed to update PC session', 'error')
        
    except ValueError:
        flash('Amount must be a valid number', 'error')
    except Exception as e:
        flash(f'Error updating PC session: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

@app.route('/edit-service-log/<log_id>')
def edit_service_log_form(log_id):
    """Edit service log form"""
    try:
        # Get the specific service log
        service_logs = get_service_logs()
        log = None
        for l in service_logs:
            if l.get('log_id') == log_id:
                log = l
                break
        
        if not log:
            flash('Service log not found', 'error')
            return redirect(url_for('edit_records'))
        
        return render_template('edit_service_log.html', log=log)
    except Exception as e:
        flash(f'Error loading service log: {str(e)}', 'error')
        return redirect(url_for('edit_records'))

@app.route('/update-service-log/<log_id>', methods=['POST'])
def update_service_log_route(log_id):
    """Update service log"""
    try:
        service = request.form.get('service')
        amount = int(request.form.get('amount'))
        staff = request.form.get('staff', 'Web User')
        
        if not service or amount <= 0:
            flash('Please provide valid service name and amount', 'error')
            return redirect(url_for('edit_service_log_form', log_id=log_id))
        
        # Update in MongoDB
        update_data = {
            "service": service,
            "amount": amount,
            "staff": staff
        }
        success = update_service_log(log_id, update_data)
        
        if success:
            # Update in JSON file
            data = load_data()
            for i, log in enumerate(data.get('services', [])):
                if log.get('log_id') == log_id:
                    data['services'][i].update(update_data)
                    break
            
            # Recalculate totals
            data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
            save_data(data)
            
            flash(f'Service log updated successfully!', 'success')
        else:
            flash('Failed to update service log', 'error')
        
    except ValueError:
        flash('Amount must be a valid number', 'error')
    except Exception as e:
        flash(f'Error updating service log: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

@app.route('/edit-expense-log/<log_id>')
def edit_expense_log_form(log_id):
    """Edit expense log form"""
    try:
        # Get the specific expense log
        expense_logs = get_expense_logs()
        log = None
        for l in expense_logs:
            if l.get('log_id') == log_id:
                log = l
                break
        
        if not log:
            flash('Expense log not found', 'error')
            return redirect(url_for('edit_records'))
        
        return render_template('edit_expense_log.html', log=log)
    except Exception as e:
        flash(f'Error loading expense log: {str(e)}', 'error')
        return redirect(url_for('edit_records'))

@app.route('/update-expense-log/<log_id>', methods=['POST'])
def update_expense_log_route(log_id):
    """Update expense log"""
    try:
        name = request.form.get('name')
        amount = int(request.form.get('amount'))
        staff = request.form.get('staff', 'Web User')
        
        if not name or amount <= 0:
            flash('Please provide valid expense name and amount', 'error')
            return redirect(url_for('edit_expense_log_form', log_id=log_id))
        
        # Update in MongoDB
        update_data = {
            "name": name,
            "amount": amount,
            "staff": staff
        }
        success = update_expense_log(log_id, update_data)
        
        if success:
            # Update in JSON file
            data = load_data()
            for i, log in enumerate(data.get('expenses', [])):
                if log.get('log_id') == log_id:
                    data['expenses'][i].update(update_data)
                    break
            
            # Recalculate totals
            data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
            save_data(data)
            
            flash(f'Expense log updated successfully!', 'success')
        else:
            flash('Failed to update expense log', 'error')
        
    except ValueError:
        flash('Amount must be a valid number', 'error')
    except Exception as e:
        flash(f'Error updating expense log: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

# ==================== DELETE FUNCTIONALITY ====================

@app.route('/delete-pc-session/<session_id>')
def delete_pc_session_route(session_id):
    """Delete PC session"""
    try:
        success = delete_pc_session(session_id)
        
        if success:
            # Remove from JSON file
            data = load_data()
            data['pcs'] = [s for s in data.get('pcs', []) if s.get('session_id') != session_id]
            
            # Recalculate totals
            data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
            save_data(data)
            
            flash('PC session deleted successfully!', 'success')
        else:
            flash('Failed to delete PC session', 'error')
        
    except Exception as e:
        flash(f'Error deleting PC session: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

@app.route('/delete-service-log/<log_id>')
def delete_service_log_route(log_id):
    """Delete service log"""
    try:
        success = delete_service_log(log_id)
        
        if success:
            # Remove from JSON file
            data = load_data()
            data['services'] = [s for s in data.get('services', []) if s.get('log_id') != log_id]
            
            # Recalculate totals
            data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
            save_data(data)
            
            flash('Service log deleted successfully!', 'success')
        else:
            flash('Failed to delete service log', 'error')
        
    except Exception as e:
        flash(f'Error deleting service log: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

@app.route('/delete-expense-log/<log_id>')
def delete_expense_log_route(log_id):
    """Delete expense log"""
    try:
        success = delete_expense_log(log_id)
        
        if success:
            # Remove from JSON file
            data = load_data()
            data['expenses'] = [e for e in data.get('expenses', []) if e.get('log_id') != log_id]
            
            # Recalculate totals
            data['totals']['pcs'], data['totals']['services'], data['totals']['expenses'], data['totals']['all'] = calc_totals(data)
            save_data(data)
            
            flash('Expense log deleted successfully!', 'success')
        else:
            flash('Failed to delete expense log', 'error')
        
    except Exception as e:
        flash(f'Error deleting expense log: {str(e)}', 'error')
    
    return redirect(url_for('edit_records'))

# ==================== SEARCH FUNCTIONALITY ====================

@app.route('/search-records')
def search_records():
    """Search records page"""
    query = request.args.get('q', '')
    results = {'pcs': [], 'services': [], 'expenses': []}
    
    if query:
        # Get current day data from JSON file
        data = load_data()
        current_pcs = data.get('pcs', [])
        current_services = data.get('services', [])
        current_expenses = data.get('expenses', [])
        
        # Get all records from MongoDB
        mongo_pc_records = get_pc_sessions()
        mongo_service_records = get_service_logs()
        mongo_expense_records = get_expense_logs()
        
        # Combine current day records with MongoDB records, avoiding duplicates
        pc_records = current_pcs.copy()
        service_records = current_services.copy()
        expense_records = current_expenses.copy()
        
        # Add MongoDB records that aren't already in current day
        current_pc_ids = {record.get('session_id') for record in current_pcs if record.get('session_id')}
        current_service_ids = {record.get('log_id') for record in current_services if record.get('log_id')}
        current_expense_ids = {record.get('log_id') for record in current_expenses if record.get('log_id')}
        
        for record in mongo_pc_records:
            if record.get('session_id') not in current_pc_ids:
                pc_records.append(record)
        
        for record in mongo_service_records:
            if record.get('log_id') not in current_service_ids:
                service_records.append(record)
        
        for record in mongo_expense_records:
            if record.get('log_id') not in current_expense_ids:
                expense_records.append(record)
        
        search_lower = query.lower()
        
        results['pcs'] = [r for r in pc_records if 
                         search_lower in r.get('pc', '').lower() or 
                         search_lower in r.get('staff', '').lower() or
                         search_lower in str(r.get('amount', 0))]
        
        results['services'] = [r for r in service_records if 
                             search_lower in r.get('service', '').lower() or 
                             search_lower in r.get('staff', '').lower() or
                             search_lower in str(r.get('amount', 0))]
        
        results['expenses'] = [r for r in expense_records if 
                             search_lower in r.get('name', '').lower() or 
                             search_lower in r.get('staff', '').lower() or
                             search_lower in str(r.get('amount', 0))]
    
    return render_template('search_records.html', query=query, results=results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
