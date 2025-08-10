# Superset Post Monitor

A comprehensive GUI-based application to monitor new posts on the Superset platform (https://app.joinsuperset.com/students) with advanced desktop notifications, system integration, and professional user interface.

## ✨ Key Features

🔐 **Modern Login Management**
- Beautiful, modern GUI with card-based design
- Secure credential storage with encryption
- Real-time login testing and validation
- Placeholder text and focus effects
- Auto-save credentials option

📡 **Intelligent Monitoring System**
- Automatic post checking every 5 minutes (configurable)
- Smart scrolling that stops when known posts are found
- Efficient new post detection with duplicate prevention
- Robust session management with automatic recovery
- Real-time status indicators and progress tracking

🔔 **Advanced Interactive Notifications**
- **Custom Toast Notifications**: Modern, interactive notifications with action buttons
- **Windows Native Notifications**: System-integrated toast notifications
- **Global Auto-Close**: Close all notifications with a single timer
- **Action Buttons**: Mark as Read, Open Link, Apply Now (job profiles)
- **Link Information**: Shows available links in expanded details
- **Chrome Installation Alerts**: Automatic notifications if Chrome is missing

📋 **Comprehensive Post Management**
- View all discovered posts with full details and metadata
- Extract post content including embedded links
- Expandable post details with "Read More" functionality
- Clear post history and manual file reload
- Newest posts displayed first with timestamps
- Post statistics and file modification tracking

⚙️ **Professional System Integration**
- **System Tray**: Full-featured tray icon with context menu
- **Auto-Start**: Windows startup integration with EXE support
- **Minimize to Tray**: Clean desktop experience
- **Custom Icons**: Professional notification bell icon
- **Silent Mode**: Hidden window with automatic monitoring
- **Portable**: Self-contained EXE with proper file handling

🎨 **Modern User Interface**
- **Material Design**: Clean, modern interface with cards and shadows
- **Responsive Layout**: Tabbed interface with organized sections
- **Visual Feedback**: Hover effects, animations, and status indicators
- **Professional Styling**: Consistent color scheme and typography
- **Activity Logging**: Real-time activity log with clear formatting

🛠️ **Developer & Power User Features**
- Detailed logging to multiple files
- Debug file access from system tray
- Configurable settings with validation
- Manual monitoring controls
- Close all notifications button
- Chrome browser detection and setup

## 🚀 Installation & Setup

### Method 1: Compiled EXE (Recommended)
1. Download the compiled `superset_gui_monitor.exe`
2. Place it in a dedicated folder
3. Double-click to run - no Python installation required!
4. The application will automatically:
   - Create necessary data files
   - Set up Chrome browser integration
   - Show Chrome installation prompts if needed

### Method 2: Quick Start (Windows - Python)
1. Download all files to a folder
2. Double-click `run_monitor.bat`
3. The script will automatically:
   - Check for Python installation
   - Install required packages
   - Create application icon
   - Start the application

### Method 3: Manual Installation
1. Install Python 3.8+ from https://python.org
2. Install Google Chrome browser
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python superset_gui_monitor.py
   ```

### Method 4: Compile Your Own EXE
```bash
# Install PyInstaller
pip install pyinstaller

# Compile to EXE
pyinstaller --name superset_notification --onefile --noconsole --icon="notification-bell.ico" "superset_gui_monitor.py"
```

## 📖 Usage Guide

### 🔧 First Time Setup
1. **🔐 Login Tab**: Enter your Superset credentials
   - **Username/Email**: Your login email with modern placeholder text
   - **Password**: Your password with secure input
   - **💾 Remember Credentials**: Check to store them securely
   - **🔍 Test Connection**: Verify credentials work before saving
   - **💾 Save Credentials**: Store for automatic login

2. **⚙️ Settings Tab**: Configure monitoring behavior
   - **⏰ Check Interval**: Set monitoring frequency (default: 5 minutes)
   - **🔔 Notifications**: Enable/disable desktop notifications
   - **🌐 Browser Mode**: Choose headless or visible mode
   - **🔔 Test Notification**: Preview notification system

### 🚀 Starting Monitoring
1. Go to **📡 Monitor Tab**
2. Click **"▶️ Start Monitoring"**
3. The application will:
   - Login to Superset automatically using saved credentials
   - Build initial database by scrolling through all posts
   - Monitor for new posts every 5 minutes
   - Send interactive notifications for new posts
   - Log all activity in real-time

### 📊 Monitoring Dashboard
- **🔄 Status Card**: Real-time monitoring status with visual indicators
- **📊 Statistics Card**: Post count and file modification times
- **🎮 Control Panel**: Start/stop monitoring, manual checks, close all notifications
- **📋 Activity Log**: Live activity feed with timestamps and status messages

### 🔔 Interactive Notifications
When new posts are found, you'll receive:
- **Modern Toast Notifications**: Slide-in from the right side
- **Action Buttons**: 
  - **✓ Mark as Read**: Mark post as seen
  - **🔗 Open Link**: Open post links in browser
  - **🚀 Apply Now**: Quick access to job profiles
- **Auto-Close Options**: Global timer to close all notifications
- **Expandable Details**: Click "Read More" to see full content and link count

### 📋 Post Management
- **📋 Posts Tab**: View all discovered posts with full details
- **🔄 Refresh**: Update post display
- **📁 Reload from File**: Refresh from saved data
- **🗑️ Clear All**: Reset post database
- **📊 Statistics**: View post counts and timestamps

### 🎯 System Tray Features
Right-click the system tray icon for:
- **👁️ Show/Hide**: Toggle window visibility
- **▶️ Start/Stop Monitoring**: Quick monitoring control
- **🔍 Check Now**: Manual post check
- **🚀 Auto Start**: Enable/disable Windows startup
- **📁 Open Data Folder**: Access log files
- **🔧 Developer Tools**: Debug and log access

## How It Works

### Post Detection
The monitor looks for posts using the specific HTML structure:
```html
<div class="feedHeader">
  <p class="text-base font-bold text-dark">Post Title</p>
  <div class="flex mt-1 flex-wrap">
    <span class="text-gray-500 text-xs">Author Name</span>
    <span class="text-gray-500 text-xs">Time Posted</span>
  </div>
</div>
```

### Smart Scrolling
- **First Run**: Scrolls to bottom to discover all existing posts
- **Subsequent Runs**: Only scrolls until known posts are found (saves time)
- **Manual Check**: Always performs full scroll

### File Structure
- `credentials.json` - Encrypted login credentials (if saved)
- `known_posts.json` - Database of discovered posts
- `posts_log.txt` - Activity log
- `new_posts_detailed.log` - Detailed log of new posts found

## 🔧 Troubleshooting

### 🚨 Common Issues & Solutions

**🔐 "Login failed" or Authentication Issues**
- ✅ Verify credentials are correct in the Login tab
- ✅ Test connection using the "🔍 Test Connection" button
- ✅ Check if Superset website is accessible in your browser
- ✅ Try disabling headless mode to see browser interaction
- ✅ Clear saved credentials and re-enter them

**🌐 "Browser setup failed" or Chrome Issues**
- ✅ **Automatic Solution**: The app will show Chrome installation notifications
- ✅ Install Google Chrome from https://www.google.com/chrome/
- ✅ Restart the application after Chrome installation
- ✅ Check internet connection for ChromeDriver download
- ✅ Try running as administrator if permission issues occur
- ✅ Ensure Chrome is updated to the latest version

**📋 "No posts found" or Detection Issues**
- ✅ Website structure may have changed - check manually first
- ✅ Enable visible browser mode in Settings to debug
- ✅ Try manual "🔍 Check Now" to test detection
- ✅ Clear known posts and rebuild database
- ✅ Check if you can access the dashboard manually

**🔔 Notifications Not Working**
- ✅ Enable notifications in Settings tab
- ✅ Test using "🔔 Test Notification" button
- ✅ Check Windows notification settings
- ✅ Some antivirus software blocks notifications
- ✅ Try different notification types (system/toast/custom)

**🚀 Auto-Start Issues**
- ✅ Run application as administrator to set registry entries
- ✅ Check Windows startup programs in Task Manager
- ✅ Ensure EXE file path hasn't changed
- ✅ Verify saved credentials for automatic login

**📁 File and Data Issues**
- ✅ Application creates files in the same directory as the EXE
- ✅ Check file permissions in the application folder
- ✅ Use "📁 Open Data Folder" from system tray to locate files
- ✅ Backup important data files before clearing

### ⚡ Performance Optimization

**🚀 Speed Improvements**
- ✅ Use headless mode for better performance
- ✅ Increase check interval if frequent updates aren't needed
- ✅ Clear old posts periodically to keep database small
- ✅ Close unnecessary browser tabs and applications
- ✅ Use compiled EXE version for faster startup

**💾 Memory Management**
- ✅ Restart monitoring session if memory usage is high
- ✅ Use "🗑️ Close All" to close notification windows
- ✅ Monitor system resources during long monitoring sessions

**🔄 Reliability Tips**
- ✅ Save credentials to avoid repeated login prompts
- ✅ Enable auto-start for continuous monitoring
- ✅ Check activity logs regularly for any issues
- ✅ Keep Chrome browser updated for compatibility

## Security Notes

- Credentials are stored in plain text JSON (if you choose to save them)
- Consider using environment variables for production use
- The application runs a real browser instance - ensure your system is secure

## 📋 System Requirements

### 🖥️ Operating System
- **Windows 10/11** (fully tested and optimized)
- **Windows 7/8.1** (should work with minor limitations)
- **Linux/Mac** (requires minor modifications for system tray)

### 🌐 Browser Requirements
- **Google Chrome** (recommended, latest version)
- **Chromium** (alternative, may require manual setup)
- **Internet Connection** (for ChromeDriver and website access)

### 🐍 Python Requirements (if not using EXE)
- **Python 3.8+** (3.9+ recommended)
- **pip** package manager
- **Required packages** (auto-installed via requirements.txt):
  - `selenium>=4.15.0`
  - `webdriver-manager>=4.0.0`
  - `plyer` (for notifications)
  - `win10toast` (Windows toast notifications)
  - `pystray` (system tray integration)
  - `Pillow` (image processing)

### 💾 Storage Requirements
- **50MB** minimum free space
- **Additional space** for log files and post database
- **Write permissions** in application directory

## 🆘 Support & Debugging

### 📊 Built-in Diagnostics
1. **📋 Activity Log**: Real-time monitoring in the GUI
2. **📁 Log Files**: Detailed logs saved automatically
3. **🔍 Test Functions**: Built-in connection and notification testing
4. **🌐 Visible Mode**: Debug browser interactions visually

### 🔍 Debug Steps
1. **Check Activity Log** in the Monitor tab
2. **Review Log Files** via system tray → "📁 Open Data Folder"
3. **Test Components**:
   - Use "🔍 Test Connection" for login issues
   - Use "🔔 Test Notification" for notification problems
   - Use "🔍 Check Now" for detection issues
4. **Enable Visible Mode** in Settings to watch browser behavior
5. **Check File Permissions** in the application directory

### 📞 Getting Help
- **Activity Logs**: Include relevant log entries when reporting issues
- **System Info**: Mention Windows version, Chrome version, and Python version
- **Error Messages**: Copy exact error messages from logs
- **Steps to Reproduce**: Describe what you were doing when the issue occurred

## 🔒 Security & Privacy

### 🛡️ Data Security
- **Local Storage**: All data stored locally on your computer
- **Credential Encryption**: Passwords stored in JSON format (consider using environment variables for production)
- **No Data Transmission**: No data sent to external servers except Superset login
- **Browser Security**: Uses standard Chrome security features

### 🔐 Privacy Considerations
- **Browser Instance**: Runs a real Chrome browser instance
- **Login Credentials**: Stored locally if you choose to save them
- **Activity Logging**: All monitoring activity logged locally
- **Network Access**: Only accesses Superset website and ChromeDriver downloads

### ⚠️ Important Notes
- **Educational Use**: This tool is for educational and personal use only
- **Terms of Service**: Respect Superset platform's terms of service
- **Responsible Use**: Don't overload the website with excessive requests
- **System Security**: Ensure your system is secure when running browser automation

## 📄 License

This tool is provided for **educational and personal use only**. Users are responsible for complying with the terms of service of the Superset platform and using the tool responsibly.

---

## 🎉 Recent Updates

### ✨ Latest Features
- **🎨 Modern UI**: Complete interface redesign with material design
- **🔔 Enhanced Notifications**: Interactive toast notifications with action buttons
- **🚀 Apply Now Button**: Quick access to job profiles
- **🌐 Chrome Detection**: Automatic Chrome installation prompts
- **📊 Global Auto-Close**: Close all notifications with single timer
- **💾 EXE Support**: Compiled executable with proper file handling
- **🎯 System Integration**: Full Windows startup and tray integration

### 🐛 Bug Fixes
- **📍 Notification Positioning**: Fixed random window positioning
- **📁 File Paths**: Resolved PyInstaller temp directory issues
- **🔄 Auto-Start**: Improved EXE detection and startup reliability
- **🎨 UI Polish**: Enhanced spacing, colors, and visual feedback