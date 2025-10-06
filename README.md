# Cyber Cafe Management Bot

A comprehensive Discord bot for managing PC sessions, services, and expenses at a cyber cafe, with MongoDB integration and PDF reporting.

## Features

- **PC Session Logging**: Track PC usage with time calculations
- **Service Management**: Add, edit, and manage services with custom pricing
- **Expense Tracking**: Log daily expenses
- **MongoDB Integration**: All data stored in MongoDB for scalability
- **PDF Reports**: Automatic daily PDF report generation
- **Edit Functionality**: Edit any record (PC sessions, services, expenses)
- **Web Dashboard**: Flask-based web interface for management
- **Real-time Updates**: Live data synchronization between Discord and web

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file with the following variables:

```env
# Discord Bot Token
TOKEN=your_discord_bot_token_here

# MongoDB Connection String
DB_TOKEN=mongodb://localhost:27017/cyber
# Or for MongoDB Atlas:
# DB_TOKEN=mongodb+srv://username:password@cluster.mongodb.net/cyber?retryWrites=true&w=majority
```

### 3. MongoDB Setup

The bot will automatically create the following collections:
- `cyber.services` - Service definitions
- `cyber.pc_sessions` - PC session logs
- `cyber.service_logs` - Service transaction logs
- `cyber.expense_logs` - Expense logs
- `cyber.logs` - Daily archived logs

### 4. Running the Bot

```bash
python main.py
```

### 5. Running the Web Dashboard

```bash
python app.py
## Authentication (Web UI)

The web dashboard requires authentication for all management pages.

- Sign up: `/signup`
- Login: `/login`
- Logout: `/logout`

Users are stored in MongoDB collection `cyber.users` with salted password hashes. Set a strong `app.secret_key` in `app.py` for production.

<!-- Windows exe packaging removed by request. Use `python app.py` to run the web app. -->

```

## Discord Commands

### PC Management
- `/pc_log` - Create PC logging panel
- `/edit_pc_session` - Edit existing PC sessions

### Service Management
- `/add_service` - Add new service
- `/service_log` - Create service logging panel
- `/edit_service_log` - Edit existing service logs

### Expense Management
- `/expense_panel` - Create expense logging panel
- `/edit_expense_log` - Edit existing expense logs

### General
- `/delete_record` - Delete any record by ID

## Web Dashboard

Access the web dashboard at `http://localhost:5000` for:
- Real-time data visualization
- Historical data viewing
- Service management
- PDF report downloads

## PDF Reports

Daily PDF reports are automatically generated when logs are saved, including:
- Daily summary with totals
- Detailed PC session logs
- Service transaction logs
- Expense logs
- Professional formatting with tables and styling

## Database Schema

### PC Sessions
```json
{
  "session_id": "uuid",
  "pc": "PC 1",
  "amount": 50,
  "staff": "Staff Name",
  "time": "29 Dec 2024 02:30 PM",
  "notes": "Optional notes",
  "date": "2024-12-29",
  "timestamp": "2024-12-29T14:30:00Z",
  "guild_id": 123456789
}
```

### Service Logs
```json
{
  "log_id": "uuid",
  "service": "Service Name",
  "amount": 25,
  "staff": "Staff Name",
  "time": "29 Dec 2024 02:30 PM",
  "emoji": "🔧",
  "date": "2024-12-29",
  "timestamp": "2024-12-29T14:30:00Z",
  "guild_id": 123456789
}
```

### Expense Logs
```json
{
  "log_id": "uuid",
  "name": "Expense Name",
  "amount": 100,
  "staff": "Staff Name",
  "time": "29 Dec 2024 02:30 PM",
  "date": "2024-12-29",
  "timestamp": "2024-12-29T14:30:00Z",
  "guild_id": 123456789
}
```

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**: Check your `DB_TOKEN` in the `.env` file
2. **Discord Bot Not Responding**: Verify the `TOKEN` in the `.env` file
3. **PDF Generation Fails**: Ensure you have write permissions in the bot directory
4. **Services Not Loading**: Check MongoDB connection and service collection

### Logs

The bot creates daily log channels in Discord and stores all data in MongoDB. Check the console output for detailed error messages.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.