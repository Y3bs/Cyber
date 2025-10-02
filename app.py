from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timezone
import json
import os
from utils.database import (
    load_services, save_service, update_service, delete_service, 
    save_logs, db
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
        
        # Log the session
        data = load_data()
        today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
        
        session_data = {
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
        
        # Log the service
        data = load_data()
        today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
        
        data["services"].append({
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
        
        # Log the expense
        data = load_data()
        today_full = datetime.now().strftime("%d %b %Y %I:%M %p")
        
        data["expenses"].append({
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
        save_logs()
        flash('Daily logs saved and archived successfully!', 'success')
    except Exception as e:
        flash(f'Error saving logs: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
