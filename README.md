# Cyber Cafe Management System

A comprehensive web-based management system for cyber cafes, converted from a Discord bot to a modern Flask web application. This system helps track PC sessions, services, expenses, and provides detailed analytics and reporting.

![Cyber Cafe Management System](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Latest-brightgreen.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3.0-purple.svg)

## Features

### 📊 Dashboard
- Real-time summary of daily activities
- Quick action buttons for common tasks
- Recent activity feeds
- System status monitoring
- Auto-refreshing data

### 💻 PC Session Management
- Log PC sessions with time calculation
- Visual PC selection grid (PC 1-14)
- Automatic time equivalent calculation (1 EGP = 6 minutes)
- Staff tracking
- Notes support

### 🛠️ Service Management
- Add, edit, delete, enable/disable services
- Custom pricing options
- Emoji support for visual identification
- Service availability tracking
- Service logging with staff attribution

### 💰 Expense Tracking
- Log business expenses
- Category-based quick selection
- Real-time total calculations
- Staff attribution
- Expense analytics

### 📈 Historical Analytics
- Archive daily logs to MongoDB
- Historical data viewing
- Business insights and statistics
- Profit/loss tracking
- Export capabilities

### 🎨 Modern UI
- Responsive Bootstrap 5 design
- Mobile-friendly interface
- Dark mode support
- Keyboard shortcuts
- Real-time notifications
- Print-friendly layouts

## Requirements

- Python 3.8 or higher
- MongoDB database
- Modern web browser

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd cyber-discord-bot
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the root directory:
```env
DB_TOKEN=mongodb://your-mongodb-connection-string
SECRET_KEY=your-secret-key-here
```

**Required Environment Variables:**
- `DB_TOKEN`: MongoDB connection string
- `SECRET_KEY`: Flask secret key for session management

### 5. Database Setup
The application uses the existing MongoDB structure:
- Database: `cyber`
- Collections: `services`, `logs`
- The application will create necessary collections automatically

### 6. Run the Application
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### First Time Setup
1. Access the web application at `http://localhost:5000`
2. Navigate to Services management to add your services
3. Start logging PC sessions and activities
4. Use the dashboard to monitor daily activities

### Daily Operations
1. **Log PC Sessions**: Go to PC Logging, select PC, enter cost and details
2. **Log Services**: Use Service Logging to record service activities
3. **Track Expenses**: Record business expenses in the Expenses section
4. **Monitor Progress**: Use the Dashboard for real-time overview
5. **Save Daily Logs**: Use "Save & Archive" to store daily data permanently

### Keyboard Shortcuts
- `Ctrl+1`: Dashboard
- `Ctrl+2`: PC Logging
- `Ctrl+3`: Service Logging
- `Ctrl+4`: Expenses
- `Ctrl+5`: Service Management
- `Ctrl+6`: History
- `Esc`: Close modals/forms

## API Endpoints

### Web Routes
- `GET /` - Dashboard
- `GET /pc-logging` - PC session logging page
- `POST /log-pc` - Log PC session
- `GET /services` - Service management page
- `POST /add-service` - Add new service
- `POST /update-service/<name>` - Update service
- `GET /service-logging` - Service logging page
- `POST /log-service` - Log service
- `GET /expenses` - Expense management page
- `POST /log-expense` - Log expense
- `GET /history` - Historical logs
- `POST /save-logs` - Archive daily logs

### API Routes
- `GET /api/summary` - Get current day summary data

## File Structure

```
cyber-discord-bot/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Documentation
├── .env                  # Environment variables (create this)
├── current_day.json      # Current day data storage
├── utils/
│   ├── database.py       # Database operations
│   └── utils.py          # Utility functions
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── dashboard.html    # Dashboard page
│   ├── pc_logging.html   # PC logging page
│   ├── services.html     # Service management
│   ├── service_logging.html # Service logging page
│   ├── expenses.html     # Expense management
│   └── history.html      # Historical logs
├── static/               # Static files
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── main.js       # JavaScript functionality
└── cogs/                 # Original Discord bot cogs (reference)
```

## Database Schema

### Services Collection
```json
{
  "name": "string",
  "cost": "number",
  "emoji": "string",
  "available": "boolean",
  "custom_cost": "boolean"
}
```

### Logs Collection
```json
{
  "date": "YYYY-MM-DD",
  "pcs": [
    {
      "pc": "PC X",
      "amount": "number",
      "staff": "string",
      "time": "string"
    }
  ],
  "services": [
    {
      "service": "string",
      "amount": "number",
      "staff": "string",
      "time": "string"
    }
  ],
  "expenses": [
    {
      "name": "string",
      "amount": "number",
      "staff": "string",
      "time": "string"
    }
  ],
  "totals": {
    "pcs": "number",
    "services": "number",
    "expenses": "number",
    "all": "number"
  }
}
```

## Features Migration from Discord Bot

The web application includes all features from the original Discord bot:

### Discord Bot Features → Web Features
- **PC Logging Commands** → PC Logging Interface
- **Service Management Commands** → Service Management Page
- **Expense Tracking** → Expense Management Interface
- **Discord Embeds** → Web Cards and Tables
- **Slash Commands** → Web Forms
- **Button Interactions** → Click Handlers
- **Modal Dialogs** → Web Forms with Validation
- **Role Permissions** → Open Access (can be extended)
- **Channel Logging** → Database Logging
- **Daily Summaries** → Dashboard and History

## Customization

### Adding New Features
1. Create new routes in `app.py`
2. Add corresponding HTML templates
3. Update navigation in `base.html`
4. Add CSS styling if needed
5. Update database functions in `utils/database.py`

### Styling Customization
- Modify `static/css/style.css` for custom styles
- Update Bootstrap classes in templates
- Add custom JavaScript in `static/js/main.js`

### Database Customization
- Extend collections in MongoDB
- Update database functions in `utils/database.py`
- Modify data models in templates

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check MongoDB service is running
   - Verify connection string in `.env`
   - Ensure database permissions are correct

2. **Port Already in Use**
   - Change port in `app.py`: `app.run(debug=True, port=5001)`
   - Or kill the process using the port

3. **Template Not Found**
   - Ensure templates are in the `templates/` directory
   - Check file names match route functions

4. **Static Files Not Loading**
   - Verify files are in `static/` directory
   - Check Flask is serving static files correctly
   - Clear browser cache

### Debug Mode
The application runs in debug mode by default. For production:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

## Security Considerations

### For Production Deployment
1. Change `SECRET_KEY` to a strong, random value
2. Set `debug=False`
3. Use environment variables for sensitive data
4. Implement user authentication if needed
5. Use HTTPS
6. Set up proper database access controls
7. Implement input validation and sanitization

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is provided as-is for educational and commercial use.

## Support

For support and questions:
1. Check the troubleshooting section
2. Review the code documentation
3. Open an issue on the repository

---

**Note**: This web application maintains compatibility with the existing MongoDB structure from the original Discord bot, allowing for seamless transition and data preservation.
