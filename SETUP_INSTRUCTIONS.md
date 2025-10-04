# 🚀 Cyber Cafe Management System - Setup Instructions

## 📋 Prerequisites

1. **Python 3.8+** - Download from [python.org](https://www.python.org/downloads/)
2. **MongoDB Database** - You need a MongoDB connection string

## 🛠️ Quick Setup

### Option 1: PowerShell (Recommended)
```powershell
# Run the PowerShell script
.\start.ps1
```

### Option 2: Batch File
```cmd
# Double-click start.bat or run:
start.bat
```

### Option 3: Manual Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your MongoDB connection
# Edit .env file with your MongoDB connection string

# Run the application
python app.py
```

## 🔧 Configuration

### 1. MongoDB Setup
You need to provide your MongoDB connection string in the `.env` file:

```env
# MongoDB Connection String
DB_TOKEN=mongodb+srv://username:password@cluster.mongodb.net/

# Flask Secret Key
SECRET_KEY=cyber-cafe-secret-key-2024

# Flask Environment
FLASK_ENV=development
FLASK_DEBUG=True
```

### 2. MongoDB Connection String Formats

**MongoDB Atlas (Cloud):**
```
DB_TOKEN=mongodb+srv://username:password@cluster.mongodb.net/
```

**Local MongoDB:**
```
DB_TOKEN=mongodb://localhost:27017/
```

**MongoDB with Authentication:**
```
DB_TOKEN=mongodb://username:password@localhost:27017/
```

## 🌐 Running the Application

1. **Start the server:**
   - Run `.\start.ps1` (PowerShell)
   - Or double-click `start.bat`
   - Or run `python app.py`

2. **Open your browser:**
   - Go to `http://localhost:5000`

3. **Start using the system:**
   - Log PC sessions, services, and expenses
   - Edit/delete current day records
   - Save daily logs with PDF generation

## 📱 Features

### ✅ Current Day Management
- **Log Records**: All new records stored in `current_day.json`
- **Edit/Delete**: Modify any current day record
- **Real-time Updates**: Changes reflected immediately

### ✅ Daily Archive
- **Save Logs**: Move records from JSON to MongoDB
- **PDF Generation**: Automatic daily summary reports
- **Historical Data**: View past days' records

### ✅ PDF Reports
- **Daily Summaries**: Complete breakdown of daily activities
- **Download**: PDF reports available in history page
- **Professional Format**: Clean, organized reports

## 🔍 Troubleshooting

### MongoDB Connection Issues
```
❌ MongoDB connection failed: [WinError 10061] No connection could be made
```

**Solutions:**
1. Check your MongoDB connection string in `.env`
2. Ensure MongoDB service is running (if using local MongoDB)
3. Verify network connectivity (if using MongoDB Atlas)
4. Check firewall settings

### Python Issues
```
❌ Python not found
```

**Solutions:**
1. Install Python from [python.org](https://www.python.org/downloads/)
2. Add Python to your system PATH
3. Restart your terminal/command prompt

### Dependencies Issues
```
❌ Module not found
```

**Solutions:**
1. Run `pip install -r requirements.txt`
2. Update pip: `python -m pip install --upgrade pip`
3. Use virtual environment: `python -m venv venv`

## 📁 File Structure

```
Cyber/
├── app.py                 # Main Flask application
├── current_day.json       # Current day records (JSON)
├── .env                   # Environment configuration
├── requirements.txt       # Python dependencies
├── start.ps1             # PowerShell startup script
├── start.bat             # Windows batch startup script
├── utils/
│   ├── database.py       # MongoDB operations
│   └── utils.py         # Utility functions
├── templates/            # HTML templates
├── static/              # CSS/JS files
└── cogs/                # Discord bot cogs
```

## 🎯 Usage Workflow

1. **Start the day**: Open the application
2. **Log activities**: Record PC sessions, services, expenses
3. **Edit if needed**: Modify any current day record
4. **End the day**: Click "Save & Archive" to generate PDF
5. **View history**: Access past days' records and PDFs

## 🆘 Support

If you encounter any issues:

1. Check the console output for error messages
2. Verify your MongoDB connection string
3. Ensure all dependencies are installed
4. Check that Python is properly installed

## 🎉 Success!

Once everything is set up, you'll see:
```
✅ Connected to MongoDB successfully!
🌐 Starting the application...
📱 Open your browser to: http://localhost:5000
```

Your Cyber Cafe Management System is ready to use! 🚀
