#!/usr/bin/env python3
"""
Superset Post Monitor with GUI
A complete GUI application for monitoring new posts on Superset platform
"""

import os
import time
import json
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import webbrowser
import subprocess
import sys

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

# Notification imports
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    print("⚠️ plyer not available - basic notifications disabled")

# Windows-specific toast notifications
try:
    import platform
    if platform.system() == "Windows":
        from win10toast import ToastNotifier
        WINDOWS_TOAST_AVAILABLE = True
    else:
        WINDOWS_TOAST_AVAILABLE = False
except ImportError:
    WINDOWS_TOAST_AVAILABLE = False

# System tray imports
try:
    import pystray
    from PIL import Image
    SYSTEM_TRAY_AVAILABLE = True
except ImportError:
    SYSTEM_TRAY_AVAILABLE = False
    print("⚠️ pystray/PIL not available - system tray disabled")

class SupersetGUIMonitor:
    def get_application_directory(self):
        """Get the actual application directory, handling both Python script and compiled EXE"""
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled EXE
                # Use the directory where the EXE is located
                return os.path.dirname(sys.executable)
            else:
                # Running as Python script
                return os.path.dirname(os.path.abspath(__file__))
        except:
            # Fallback to current working directory
            return os.getcwd()

    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("955x860")
        self.root.configure(bg='#f0f0f0')
        
        # Set title after checking auto-start mode (will be updated later)
        self.root.title("Superset Post Monitor")
        
        # Configuration - initialize first
        self.login_url = "https://app.joinsuperset.com/students/login"
        self.dashboard_url = "https://app.joinsuperset.com/students"
        self.check_interval = 300  # 5 minutes
        
        # Data storage - use application directory for all files
        app_dir = self.get_application_directory()
        self.credentials_file = os.path.join(app_dir, "credentials.json")
        self.known_posts_file = os.path.join(app_dir, "known_posts.json")
        self.log_file = os.path.join(app_dir, "posts_log.txt")
        
        # Runtime variables - initialize before system tray
        self.driver = None
        self.known_posts = {}
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Notification tracking
        self.open_notifications = []  # Track all open toast notifications
        self.global_auto_close_timer = None  # Global timer for auto-close
        
        # System tray variables
        self.tray_icon = None
        self.tray_thread = None
        self.window_visible = True  # Track window visibility state
        
        # Check if launched from auto-start
        self.is_auto_start = self.check_auto_start_mode()
        
        # Setup GUI first
        self.setup_gui()
        
        # Load existing data after GUI is ready (quiet during initialization)
        self.load_known_posts(verbose=False)
        
        # Update GUI with loaded data
        self.posts_count_label.config(text=f"{len(self.known_posts)} posts")
        self.file_modified_label.config(text=self.get_file_modified_time())
        
        # Add initialization message to log
        self.log_message("📱 Superset Post Monitor initialized")
        self.log_message(f"📊 Loaded {len(self.known_posts)} known posts")
        self.log_message(f"🎯 Target URL: {self.dashboard_url}")
        self.log_message(f"⏰ Check interval: {self.check_interval // 60} minutes")
        
        if self.is_auto_start:
            self.log_message("🚀 Launched in auto-start mode")
            self.root.title("Superset Post Monitor - Auto-Start Mode")
        
        # Setup system tray and icon after everything else is ready
        self.setup_app_icon()
        self.setup_system_tray()
        
        # Load saved credentials if available
        self.load_credentials()
        
        # Bind window state change events
        self.setup_window_events()
        
        # Handle auto-start mode
        if self.is_auto_start:
            self.handle_auto_start_mode()
    
    def setup_gui(self):
        """Setup the main GUI interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Login Tab
        self.setup_login_tab()
        
        # Monitor Tab
        self.setup_monitor_tab()
        
        # Posts Tab
        self.setup_posts_tab()
        
        # Settings Tab
        self.setup_settings_tab()
    
    def setup_login_tab(self):
        """Setup login credentials tab with modern UI"""
        login_frame = ttk.Frame(self.notebook)
        self.notebook.add(login_frame, text="🔐 Login")
        
        # Main container with gradient-like background
        main_container = tk.Frame(login_frame, bg='#f8f9fa')
        main_container.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Header section - reduced height
        header_frame = tk.Frame(main_container, bg='#ffffff', height=80)
        header_frame.pack(fill='x', padx=20, pady=(15, 0))
        header_frame.pack_propagate(False)
        
        # Title with modern styling
        title_container = tk.Frame(header_frame, bg='#ffffff')
        title_container.pack(expand=True, fill='both')
        
        # Superset logo/icon (using emoji as placeholder) - smaller
        logo_label = tk.Label(title_container, text="🔐", font=('Segoe UI', 24), bg='#ffffff', fg='#3498db')
        logo_label.pack(pady=(5, 2))
        
        title_label = tk.Label(title_container, text="Superset Login", 
                              font=('Segoe UI', 18, 'bold'), bg='#ffffff', fg='#2c3e50')
        title_label.pack()
        
        subtitle_label = tk.Label(title_container, text="Enter your credentials to access the monitoring system", 
                                 font=('Segoe UI', 9), bg='#ffffff', fg='#7f8c8d')
        subtitle_label.pack()
        
        # Login card container - more space
        card_container = tk.Frame(main_container, bg='#f8f9fa')
        card_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Login card - no expand to prevent stretching
        login_card = self.create_login_card(card_container)
        login_card.pack(anchor='center', padx=40, pady=10)
        
        # Status section at bottom - smaller
        status_frame = tk.Frame(main_container, bg='#f8f9fa', height=40)
        status_frame.pack(fill='x', padx=20, pady=(0, 15))
        status_frame.pack_propagate(False)
        
        # Status label with modern styling
        self.login_status_label = tk.Label(status_frame, text="👋 Welcome! Please enter your credentials to get started", 
                                          font=('Segoe UI', 9), bg='#f8f9fa', fg='#7f8c8d')
        self.login_status_label.pack(expand=True)
    
    def create_login_card(self, parent):
        """Create modern login card"""
        card = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(card, bg='#e9ecef', height=3)
        shadow_frame.pack(side='bottom', fill='x')
        
        content_frame = tk.Frame(card, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=30, pady=25)
        
        # Card header - smaller
        header = tk.Label(content_frame, text="🌐 Account Credentials", 
                         font=('Segoe UI', 14, 'bold'), bg='#ffffff', fg='#2c3e50')
        header.pack(pady=(0, 20))
        
        # Username/Email field - more compact
        username_frame = tk.Frame(content_frame, bg='#ffffff')
        username_frame.pack(fill='x', pady=(0, 15))
        
        username_label = tk.Label(username_frame, text="📧 Username/Email", 
                                 font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e')
        username_label.pack(anchor='w', pady=(0, 6))
        
        # Modern input field with border
        username_container = tk.Frame(username_frame, bg='#ffffff', relief='solid', bd=1)
        username_container.pack(fill='x')
        
        self.username_entry = tk.Entry(username_container, font=('Segoe UI', 11), 
                                      relief='flat', bd=0, bg='#f8f9fa', fg='#2c3e50',
                                      insertbackground='#3498db')
        self.username_entry.pack(fill='x', padx=12, pady=10)
        
        # Add placeholder text effect
        self.add_placeholder(self.username_entry, "Enter your email address")
        
        # Password field - more compact
        password_frame = tk.Frame(content_frame, bg='#ffffff')
        password_frame.pack(fill='x', pady=(0, 15))
        
        password_label = tk.Label(password_frame, text="🔒 Password", 
                                 font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e')
        password_label.pack(anchor='w', pady=(0, 6))
        
        # Modern password field with border
        password_container = tk.Frame(password_frame, bg='#ffffff', relief='solid', bd=1)
        password_container.pack(fill='x')
        
        self.password_entry = tk.Entry(password_container, font=('Segoe UI', 11), 
                                      relief='flat', bd=0, bg='#f8f9fa', fg='#2c3e50',
                                      show='*', insertbackground='#3498db')
        self.password_entry.pack(fill='x', padx=12, pady=10)
        
        # Add placeholder text effect
        self.add_placeholder(self.password_entry, "Enter your password", is_password=True)
        
        # Options section - more compact
        options_frame = tk.Frame(content_frame, bg='#ffffff')
        options_frame.pack(fill='x', pady=(0, 20))
        
        # Save credentials checkbox with modern styling - more compact
        checkbox_frame = tk.Frame(options_frame, bg='#ffffff')
        checkbox_frame.pack(anchor='w')
        
        self.save_creds_var = tk.BooleanVar(value=True)
        save_check = tk.Checkbutton(checkbox_frame, text="💾 Remember my credentials", 
                                   variable=self.save_creds_var, bg='#ffffff', 
                                   font=('Segoe UI', 9), fg='#34495e',
                                   activebackground='#ffffff', relief='flat')
        save_check.pack(side='left')
        
        # Help text - smaller
        help_label = tk.Label(options_frame, text="Your credentials will be stored securely on this device", 
                             font=('Segoe UI', 7), bg='#ffffff', fg='#95a5a6')
        help_label.pack(anchor='w', pady=(3, 0))
        
        # Action buttons - more compact
        buttons_frame = tk.Frame(content_frame, bg='#ffffff')
        buttons_frame.pack(fill='x')
        
        # Test login button - smaller
        test_btn = tk.Button(buttons_frame, text="🔍 Test Connection", command=self.test_login,
                            bg='#3498db', fg='white', font=('Segoe UI', 10, 'bold'),
                            relief='flat', bd=0, padx=20, pady=10,
                            cursor='hand2', width=14)
        test_btn.pack(side='left', padx=(0, 12))
        
        # Save credentials button - smaller
        save_btn = tk.Button(buttons_frame, text="💾 Save Credentials", command=self.save_credentials,
                            bg='#27ae60', fg='white', font=('Segoe UI', 10, 'bold'),
                            relief='flat', bd=0, padx=20, pady=10,
                            cursor='hand2', width=14)
        save_btn.pack(side='left')
        
        # Add hover effects
        self.add_button_hover_effects(test_btn, '#3498db', '#5dade2')
        self.add_button_hover_effects(save_btn, '#27ae60', '#2ecc71')
        
        # Add focus effects to input fields
        self.add_input_focus_effects(username_container, self.username_entry)
        self.add_input_focus_effects(password_container, self.password_entry)
        
        return card
    
    def add_placeholder(self, entry, placeholder_text, is_password=False):
        """Add placeholder text effect to entry fields"""
        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, tk.END)
                entry.config(fg='#2c3e50')
                if is_password:
                    entry.config(show='*')
        
        def on_focus_out(event):
            if entry.get() == '':
                entry.insert(0, placeholder_text)
                entry.config(fg='#bdc3c7')
                if is_password:
                    entry.config(show='')
        
        # Set initial placeholder
        entry.insert(0, placeholder_text)
        entry.config(fg='#bdc3c7')
        if is_password:
            entry.config(show='')
        
        # Bind events
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
    
    def add_input_focus_effects(self, container, entry):
        """Add focus effects to input containers"""
        def on_focus_in(event):
            container.config(relief='solid', bd=2, bg='#3498db')
        
        def on_focus_out(event):
            container.config(relief='solid', bd=1, bg='#ffffff')
        
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
    
    def setup_monitor_tab(self):
        """Setup monitoring control tab with modern UI"""
        monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(monitor_frame, text="📡 Monitor")
        
        # Main container with gradient-like background
        main_container = tk.Frame(monitor_frame, bg='#f8f9fa')
        main_container.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Header section
        header_frame = tk.Frame(main_container, bg='#ffffff', height=80)
        header_frame.pack(fill='x', padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        # Title with modern styling
        title_container = tk.Frame(header_frame, bg='#ffffff')
        title_container.pack(expand=True, fill='both')
        
        title_label = tk.Label(title_container, text="📡 Post Monitoring Dashboard", 
                              font=('Segoe UI', 20, 'bold'), bg='#ffffff', fg='#2c3e50')
        title_label.pack(expand=True)
        
        subtitle_label = tk.Label(title_container, text="Monitor Superset posts in real-time", 
                                 font=('Segoe UI', 10), bg='#ffffff', fg='#7f8c8d')
        subtitle_label.pack()
        
        # Status cards container
        cards_container = tk.Frame(main_container, bg='#f8f9fa')
        cards_container.pack(fill='x', padx=20, pady=20)
        
        # Status card
        status_card = self.create_status_card(cards_container)
        status_card.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Statistics card
        stats_card = self.create_stats_card(cards_container)
        stats_card.pack(side='left', fill='both', expand=True, padx=(10, 0))
        
        # Control panel
        control_panel = self.create_control_panel(main_container)
        control_panel.pack(fill='x', padx=20, pady=(0, 20))
        
        # Activity log section
        log_section = self.create_log_section(main_container)
        log_section.pack(fill='both', expand=True, padx=20, pady=(0, 20))
    
    def create_status_card(self, parent):
        """Create modern status card"""
        card = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        
        # Add subtle shadow effect with border
        shadow_frame = tk.Frame(card, bg='#e9ecef', height=2)
        shadow_frame.pack(side='bottom', fill='x')
        
        content_frame = tk.Frame(card, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Card header
        header = tk.Label(content_frame, text="🔄 Monitor Status", 
                         font=('Segoe UI', 14, 'bold'), bg='#ffffff', fg='#2c3e50')
        header.pack(anchor='w', pady=(0, 15))
        
        # Status indicator with icon
        status_container = tk.Frame(content_frame, bg='#ffffff')
        status_container.pack(fill='x', pady=(0, 10))
        
        self.status_indicator = tk.Label(status_container, text="⏹", 
                                        font=('Segoe UI', 24), bg='#ffffff', fg='#e74c3c')
        self.status_indicator.pack(side='left', padx=(0, 10))
        
        status_text_frame = tk.Frame(status_container, bg='#ffffff')
        status_text_frame.pack(side='left', fill='x', expand=True)
        
        self.monitor_status_label = tk.Label(status_text_frame, text="Stopped", 
                                           font=('Segoe UI', 16, 'bold'), bg='#ffffff', fg='#e74c3c')
        self.monitor_status_label.pack(anchor='w')
        
        self.status_description = tk.Label(status_text_frame, text="Monitoring is currently inactive", 
                                          font=('Segoe UI', 9), bg='#ffffff', fg='#7f8c8d')
        self.status_description.pack(anchor='w')
        
        # Last check info
        separator = tk.Frame(content_frame, bg='#ecf0f1', height=1)
        separator.pack(fill='x', pady=(15, 15))
        
        last_check_frame = tk.Frame(content_frame, bg='#ffffff')
        last_check_frame.pack(fill='x')
        
        tk.Label(last_check_frame, text="🕐 Last Check:", 
                font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w')
        
        self.last_check_label = tk.Label(last_check_frame, text="Never", 
                                        font=('Segoe UI', 10), bg='#ffffff', fg='#7f8c8d')
        self.last_check_label.pack(anchor='w', pady=(2, 0))
        
        return card
    
    def create_stats_card(self, parent):
        """Create modern statistics card"""
        card = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(card, bg='#e9ecef', height=2)
        shadow_frame.pack(side='bottom', fill='x')
        
        content_frame = tk.Frame(card, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Card header
        header = tk.Label(content_frame, text="📊 Statistics", 
                         font=('Segoe UI', 14, 'bold'), bg='#ffffff', fg='#2c3e50')
        header.pack(anchor='w', pady=(0, 15))
        
        # Posts count with large number display
        posts_container = tk.Frame(content_frame, bg='#ffffff')
        posts_container.pack(fill='x', pady=(0, 10))
        
        posts_icon = tk.Label(posts_container, text="📝", 
                             font=('Segoe UI', 20), bg='#ffffff')
        posts_icon.pack(side='left', padx=(0, 10))
        
        posts_info_frame = tk.Frame(posts_container, bg='#ffffff')
        posts_info_frame.pack(side='left', fill='x', expand=True)
        
        self.posts_count_label = tk.Label(posts_info_frame, text=f"{len(self.known_posts)}", 
                                         font=('Segoe UI', 20, 'bold'), bg='#ffffff', fg='#27ae60')
        self.posts_count_label.pack(anchor='w')
        
        tk.Label(posts_info_frame, text="Known Posts", 
                font=('Segoe UI', 9), bg='#ffffff', fg='#7f8c8d').pack(anchor='w')
        
        # File info
        separator = tk.Frame(content_frame, bg='#ecf0f1', height=1)
        separator.pack(fill='x', pady=(15, 15))
        
        file_frame = tk.Frame(content_frame, bg='#ffffff')
        file_frame.pack(fill='x')
        
        tk.Label(file_frame, text="📁 File Updated:", 
                font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w')
        
        self.file_modified_label = tk.Label(file_frame, text=self.get_file_modified_time(), 
                                           font=('Segoe UI', 10), bg='#ffffff', fg='#7f8c8d')
        self.file_modified_label.pack(anchor='w', pady=(2, 0))
        
        return card
    
    def create_control_panel(self, parent):
        """Create modern control panel"""
        panel = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(panel, bg='#e9ecef', height=2)
        shadow_frame.pack(side='bottom', fill='x')
        
        content_frame = tk.Frame(panel, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Panel header
        header = tk.Label(content_frame, text="🎮 Control Panel", 
                         font=('Segoe UI', 14, 'bold'), bg='#ffffff', fg='#2c3e50')
        header.pack(anchor='w', pady=(0, 20))
        
        # Buttons container
        buttons_frame = tk.Frame(content_frame, bg='#ffffff')
        buttons_frame.pack(fill='x')
        
        # Toggle monitoring button with modern styling
        self.toggle_monitoring_btn = tk.Button(buttons_frame, text="▶ Start Monitoring", 
                                             command=self.toggle_monitoring,
                                             bg='#27ae60', fg='white', 
                                             font=('Segoe UI', 11, 'bold'),
                                             relief='flat', bd=0, padx=30, pady=12,
                                             cursor='hand2', width=16)
        self.toggle_monitoring_btn.pack(side='left', padx=(0, 15))
        
        # Check now button
        check_btn = tk.Button(buttons_frame, text="🔍 Check Now", command=self.check_now,
                             bg='#3498db', fg='white', font=('Segoe UI', 11, 'bold'),
                             relief='flat', bd=0, padx=30, pady=12,
                             cursor='hand2', width=12)
        check_btn.pack(side='left', padx=(0, 15))
        
        # Close all notifications button
        close_all_btn = tk.Button(buttons_frame, text="🗑️ Close All", command=self.close_all_notifications,
                                 bg='#ef4444', fg='white', font=('Segoe UI', 11, 'bold'),
                                 relief='flat', bd=0, padx=30, pady=12,
                                 cursor='hand2', width=12)
        close_all_btn.pack(side='left', padx=(0, 15))
        
        # Store reference for tray button
        self.tray_btn_placeholder = buttons_frame
        
        # Add hover effects
        self.add_button_hover_effects(self.toggle_monitoring_btn, '#27ae60', '#2ecc71')
        self.add_button_hover_effects(check_btn, '#3498db', '#5dade2')
        self.add_button_hover_effects(close_all_btn, '#ef4444', '#f87171')
        
        return panel
    
    def create_log_section(self, parent):
        """Create modern activity log section"""
        section = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(section, bg='#e9ecef', height=2)
        shadow_frame.pack(side='bottom', fill='x')
        
        content_frame = tk.Frame(section, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Section header
        header_frame = tk.Frame(content_frame, bg='#ffffff')
        header_frame.pack(fill='x', pady=(0, 15))
        
        header = tk.Label(header_frame, text="📋 Activity Log", 
                         font=('Segoe UI', 14, 'bold'), bg='#ffffff', fg='#2c3e50')
        header.pack(side='left')
        
        # Clear log button
        clear_btn = tk.Button(header_frame, text="🗑 Clear", command=self.clear_log,
                             bg='#95a5a6', fg='white', font=('Segoe UI', 9, 'bold'),
                             relief='flat', bd=0, padx=15, pady=6, cursor='hand2')
        clear_btn.pack(side='right')
        
        # Log text area with modern styling
        log_container = tk.Frame(content_frame, bg='#f8f9fa', relief='flat', bd=1)
        log_container.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_container, 
                                                 font=('Consolas', 9),
                                                 bg='#f8f9fa', fg='#2c3e50',
                                                 relief='flat', bd=0,
                                                 padx=10, pady=10,
                                                 wrap='word',
                                                 selectbackground='#3498db',
                                                 selectforeground='white')
        self.log_text.pack(fill='both', expand=True, padx=2, pady=2)
        
        return section
    
    def add_button_hover_effects(self, button, normal_color, hover_color):
        """Add hover effects to buttons"""
        def on_enter(e):
            button.config(bg=hover_color)
        
        def on_leave(e):
            button.config(bg=normal_color)
        
        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)
    
    def clear_log(self):
        """Clear the activity log"""
        if messagebox.askyesno("Clear Log", "Are you sure you want to clear the activity log?"):
            self.log_text.delete(1.0, tk.END)
            self.log_message("🗑️ Activity log cleared")
    
    def setup_posts_tab(self):
        """Setup posts display tab"""
        posts_frame = ttk.Frame(self.notebook)
        self.notebook.add(posts_frame, text="📋 Posts")
        
        # Title and controls
        header_frame = tk.Frame(posts_frame, bg='white')
        header_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(header_frame, text="Known Posts", font=('Arial', 16, 'bold'), bg='white').pack(side='left')
        
        # Refresh button
        refresh_btn = tk.Button(header_frame, text="🔄 Refresh", command=self.refresh_posts_display,
                               bg='#2196F3', fg='white', font=('Arial', 10, 'bold'))
        refresh_btn.pack(side='right')
        
        # Reload from file button
        reload_btn = tk.Button(header_frame, text="📁 Reload from File", command=self.reload_posts_from_file,
                              bg='#9C27B0', fg='white', font=('Arial', 10, 'bold'))
        reload_btn.pack(side='right', padx=(0, 10))
        
        # Clear all button
        clear_btn = tk.Button(header_frame, text="🗑️ Clear All", command=self.clear_all_posts,
                             bg='#f44336', fg='white', font=('Arial', 10, 'bold'))
        clear_btn.pack(side='right', padx=(0, 10))
        
        # Posts display
        self.posts_text = scrolledtext.ScrolledText(posts_frame, font=('Arial', 10))
        self.posts_text.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Update posts display
        self.refresh_posts_display()
    
    def setup_settings_tab(self):
        """Setup settings tab with modern UI"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="⚙️ Settings")
        
        # Main container with gradient-like background
        main_container = tk.Frame(settings_frame, bg='#f8f9fa')
        main_container.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Header section
        header_frame = tk.Frame(main_container, bg='#ffffff', height=80)
        header_frame.pack(fill='x', padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        # Title with modern styling
        title_container = tk.Frame(header_frame, bg='#ffffff')
        title_container.pack(expand=True, fill='both')
        
        title_label = tk.Label(title_container, text="⚙️ Monitor Settings", 
                              font=('Segoe UI', 20, 'bold'), bg='#ffffff', fg='#2c3e50')
        title_label.pack(expand=True)
        
        subtitle_label = tk.Label(title_container, text="Configure monitoring behavior and preferences", 
                                 font=('Segoe UI', 10), bg='#ffffff', fg='#7f8c8d')
        subtitle_label.pack()
        
        # Settings cards container
        cards_container = tk.Frame(main_container, bg='#f8f9fa')
        cards_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left column
        left_column = tk.Frame(cards_container, bg='#f8f9fa')
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Right column
        right_column = tk.Frame(cards_container, bg='#f8f9fa')
        right_column.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Monitoring settings card (left column)
        monitoring_card = self.create_monitoring_settings_card(left_column)
        monitoring_card.pack(fill='x', pady=(0, 20))
        
        # File locations card (left column - moved here to fill empty space)
        files_card = self.create_file_locations_card(left_column)
        files_card.pack(fill='x')
        
        # Notification settings card (right column)
        notification_card = self.create_notification_settings_card(right_column)
        notification_card.pack(fill='x', pady=(0, 20))
        
        # Actions card (right column)
        actions_card = self.create_actions_card(right_column)
        actions_card.pack(fill='x')
    
    def create_monitoring_settings_card(self, parent):
        """Create monitoring settings card"""
        card = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(card, bg='#e9ecef', height=2)
        shadow_frame.pack(side='bottom', fill='x')
        
        content_frame = tk.Frame(card, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Card header
        header = tk.Label(content_frame, text="🔄 Monitoring Settings", 
                         font=('Segoe UI', 14, 'bold'), bg='#ffffff', fg='#2c3e50')
        header.pack(anchor='w', pady=(0, 20))
        
        # Check interval setting
        interval_frame = tk.Frame(content_frame, bg='#ffffff')
        interval_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(interval_frame, text="⏰ Check Interval", 
                font=('Segoe UI', 11, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w')
        
        tk.Label(interval_frame, text="How often to check for new posts", 
                font=('Segoe UI', 9), bg='#ffffff', fg='#7f8c8d').pack(anchor='w', pady=(2, 8))
        
        interval_input_frame = tk.Frame(interval_frame, bg='#ffffff')
        interval_input_frame.pack(anchor='w')
        
        self.interval_var = tk.StringVar(value=str(self.check_interval // 60))
        interval_entry = tk.Entry(interval_input_frame, textvariable=self.interval_var, 
                                 font=('Segoe UI', 10), width=8, relief='solid', bd=1,
                                 bg='#f8f9fa', fg='#2c3e50')
        interval_entry.pack(side='left', padx=(0, 8))
        
        tk.Label(interval_input_frame, text="minutes", 
                font=('Segoe UI', 10), bg='#ffffff', fg='#7f8c8d').pack(side='left')
        
        # Smart scrolling setting
        scroll_frame = tk.Frame(content_frame, bg='#ffffff')
        scroll_frame.pack(fill='x', pady=(0, 15))
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        scroll_check = tk.Checkbutton(scroll_frame, text="📜 Smart Scrolling", 
                                     variable=self.auto_scroll_var, bg='#ffffff', 
                                     font=('Segoe UI', 11, 'bold'), fg='#34495e',
                                     activebackground='#ffffff', relief='flat')
        scroll_check.pack(anchor='w')
        
        tk.Label(scroll_frame, text="Stop scrolling when known posts are found (saves time)", 
                font=('Segoe UI', 9), bg='#ffffff', fg='#7f8c8d').pack(anchor='w', padx=(25, 0), pady=(2, 0))
        
        # Headless mode setting
        headless_frame = tk.Frame(content_frame, bg='#ffffff')
        headless_frame.pack(fill='x')
        
        self.headless_var = tk.BooleanVar(value=True)
        headless_check = tk.Checkbutton(headless_frame, text="👻 Headless Mode", 
                                       variable=self.headless_var, bg='#ffffff', 
                                       font=('Segoe UI', 11, 'bold'), fg='#34495e',
                                       activebackground='#ffffff', relief='flat')
        headless_check.pack(anchor='w')
        
        tk.Label(headless_frame, text="Run browser in background (recommended for better performance)", 
                font=('Segoe UI', 9), bg='#ffffff', fg='#7f8c8d').pack(anchor='w', padx=(25, 0), pady=(2, 0))
        
        return card
    
    def create_notification_settings_card(self, parent):
        """Create notification settings card"""
        card = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(card, bg='#e9ecef', height=2)
        shadow_frame.pack(side='bottom', fill='x')
        
        content_frame = tk.Frame(card, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Card header
        header = tk.Label(content_frame, text="🔔 Notification Settings", 
                         font=('Segoe UI', 14, 'bold'), bg='#ffffff', fg='#2c3e50')
        header.pack(anchor='w', pady=(0, 20))
        
        # Enable notifications
        notif_frame = tk.Frame(content_frame, bg='#ffffff')
        notif_frame.pack(fill='x', pady=(0, 15))
        
        self.notifications_var = tk.BooleanVar(value=True)
        notif_check = tk.Checkbutton(notif_frame, text="🔔 Enable Desktop Notifications", 
                                    variable=self.notifications_var, bg='#ffffff', 
                                    font=('Segoe UI', 11, 'bold'), fg='#34495e',
                                    activebackground='#ffffff', relief='flat')
        notif_check.pack(anchor='w')
        
        tk.Label(notif_frame, text="Show notifications when new posts are found", 
                font=('Segoe UI', 9), bg='#ffffff', fg='#7f8c8d').pack(anchor='w', padx=(25, 0), pady=(2, 0))
        
        # Notification type selection
        type_frame = tk.Frame(content_frame, bg='#ffffff')
        type_frame.pack(fill='x', pady=(10, 0))
        
        tk.Label(type_frame, text="Notification Type:", 
                font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w', pady=(0, 8))
        
        self.notification_type_var = tk.StringVar(value="custom")
        
        # Custom toast option
        custom_frame = tk.Frame(type_frame, bg='#ffffff')
        custom_frame.pack(fill='x', pady=2)
        
        tk.Radiobutton(custom_frame, text="🎨 Custom Toast", 
                      variable=self.notification_type_var, value="custom",
                      bg='#ffffff', font=('Segoe UI', 10), fg='#34495e',
                      activebackground='#ffffff', relief='flat').pack(side='left')
        
        tk.Label(custom_frame, text="(Recommended - Interactive with action buttons)", 
                font=('Segoe UI', 8), bg='#ffffff', fg='#27ae60').pack(side='left', padx=(5, 0))
        
        # Windows native option
        if WINDOWS_TOAST_AVAILABLE:
            windows_frame = tk.Frame(type_frame, bg='#ffffff')
            windows_frame.pack(fill='x', pady=2)
            
            tk.Radiobutton(windows_frame, text="🪟 Windows Native", 
                          variable=self.notification_type_var, value="windows",
                          bg='#ffffff', font=('Segoe UI', 10), fg='#34495e',
                          activebackground='#ffffff', relief='flat').pack(side='left')
            
            tk.Label(windows_frame, text="(System integrated)", 
                    font=('Segoe UI', 8), bg='#ffffff', fg='#3498db').pack(side='left', padx=(5, 0))
        
        # Basic notification option
        if NOTIFICATIONS_AVAILABLE:
            basic_frame = tk.Frame(type_frame, bg='#ffffff')
            basic_frame.pack(fill='x', pady=2)
            
            tk.Radiobutton(basic_frame, text="📱 Basic Notification", 
                          variable=self.notification_type_var, value="basic",
                          bg='#ffffff', font=('Segoe UI', 10), fg='#34495e',
                          activebackground='#ffffff', relief='flat').pack(side='left')
            
            tk.Label(basic_frame, text="(Simple popup)", 
                    font=('Segoe UI', 8), bg='#ffffff', fg='#95a5a6').pack(side='left', padx=(5, 0))
        
        return card
    

    
    def create_file_locations_card(self, parent):
        """Create file locations and system info card"""
        card = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(card, bg='#e9ecef', height=2)
        shadow_frame.pack(side='bottom', fill='x')
        
        content_frame = tk.Frame(card, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Card header
        header_frame = tk.Frame(content_frame, bg='#ffffff')
        header_frame.pack(fill='x', pady=(0, 20))
        
        header = tk.Label(header_frame, text="📁 Files & System", 
                         font=('Segoe UI', 14, 'bold'), bg='#ffffff', fg='#2c3e50')
        header.pack(side='left')
        
        # Open folder button
        folder_btn = tk.Button(header_frame, text="📂 Open Folder", command=self.open_data_folder,
                              bg='#95a5a6', fg='white', font=('Segoe UI', 9, 'bold'),
                              relief='flat', bd=0, padx=15, pady=6, cursor='hand2')
        folder_btn.pack(side='right')
        
        # File list
        files_info = [
            ("🔐 Credentials", self.credentials_file, "Login credentials storage"),
            ("📋 Known Posts", self.known_posts_file, "Database of discovered posts"),
            ("📝 Activity Log", self.log_file, "Application activity log")
        ]
        
        for icon_name, filename, description in files_info:
            file_frame = tk.Frame(content_frame, bg='#ffffff')
            file_frame.pack(fill='x', pady=(0, 10))
            
            # File icon and name
            name_frame = tk.Frame(file_frame, bg='#ffffff')
            name_frame.pack(fill='x')
            
            tk.Label(name_frame, text=f"{icon_name}: {filename}", 
                    font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w')
            
            tk.Label(name_frame, text=description, 
                    font=('Segoe UI', 8), bg='#ffffff', fg='#7f8c8d').pack(anchor='w', padx=(20, 0))
        
        # # System info section
        # separator = tk.Frame(content_frame, bg='#ecf0f1', height=1)
        # separator.pack(fill='x', pady=(15, 15))
        
        # # System tray status
        # system_frame = tk.Frame(content_frame, bg='#ffffff')
        # system_frame.pack(fill='x', pady=(0, 8))
        
        # tk.Label(system_frame, text="📱 System Tray", 
        #         font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w')
        
        # tray_status = "Available ✅" if hasattr(self, 'tray_icon') and self.tray_icon else "Not Available ❌"
        # tk.Label(system_frame, text=f"Status: {tray_status}", 
        #         font=('Segoe UI', 8), bg='#ffffff', fg='#7f8c8d').pack(anchor='w', padx=(20, 0))
        
        # # Auto-start info
        # autostart_frame = tk.Frame(content_frame, bg='#ffffff')
        # autostart_frame.pack(fill='x')
        
        # tk.Label(autostart_frame, text="🚀 Auto-start", 
        #         font=('Segoe UI', 10, 'bold'), bg='#ffffff', fg='#34495e').pack(anchor='w')
        
        # autostart_command = self.get_autostart_command_preview()
        # tk.Label(autostart_frame, text=f"Command: {autostart_command}", 
        #         font=('Segoe UI', 8), bg='#ffffff', fg='#7f8c8d', 
        #         wraplength=280, justify='left').pack(anchor='w', padx=(20, 0))
        
        return card
    
    def create_actions_card(self, parent):
        """Create actions card"""
        card = tk.Frame(parent, bg='#ffffff', relief='flat', bd=0)
        
        # Add subtle shadow effect
        shadow_frame = tk.Frame(card, bg='#e9ecef', height=2)
        shadow_frame.pack(side='bottom', fill='x')
        
        content_frame = tk.Frame(card, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Card header
        header = tk.Label(content_frame, text="💾 Actions", 
                         font=('Segoe UI', 14, 'bold'), bg='#ffffff', fg='#2c3e50')
        header.pack(anchor='w', pady=(0, 20))
        
        # Save settings button
        save_btn = tk.Button(content_frame, text="💾 Save Settings", command=self.save_settings,
                            bg='#27ae60', fg='white', font=('Segoe UI', 10, 'bold'),
                            relief='flat', bd=0, padx=20, pady=10,
                            cursor='hand2')
        save_btn.pack(fill='x', pady=(0, 10))
        
        # Test notification button
        test_btn = tk.Button(content_frame, text="🔔 Test Notification", command=self.test_notification,
                            bg='#f39c12', fg='white', font=('Segoe UI', 10, 'bold'),
                            relief='flat', bd=0, padx=20, pady=10,
                            cursor='hand2')
        test_btn.pack(fill='x', pady=(0, 10))
        
        # Open log file button
        log_btn = tk.Button(content_frame, text="📄 Open Log", command=self.open_log_file,
                           bg='#3498db', fg='white', font=('Segoe UI', 10, 'bold'),
                           relief='flat', bd=0, padx=20, pady=10,
                           cursor='hand2')
        log_btn.pack(fill='x')
        
        # Add hover effects
        self.add_button_hover_effects(save_btn, '#27ae60', '#2ecc71')
        self.add_button_hover_effects(test_btn, '#f39c12', '#f7dc6f')
        self.add_button_hover_effects(log_btn, '#3498db', '#5dade2')
        
        return card 
   
    def log_message(self, message):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Add to GUI log if it exists
        if hasattr(self, 'log_text') and self.log_text:
            try:
                self.log_text.insert(tk.END, log_entry)
                self.log_text.see(tk.END)
            except:
                # If GUI log fails, print to console
                print(log_entry.strip())
        else:
            # If GUI not ready, print to console
            print(log_entry.strip())
        
        # Also save to file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().isoformat()}] {message}\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def load_credentials(self):
        """Load saved credentials if available"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    creds = json.load(f)
                    username = creds.get('username', '')
                    password = creds.get('password', '')
                    
                    if username:
                        # Clear placeholder and set actual value
                        self.username_entry.delete(0, tk.END)
                        self.username_entry.insert(0, username)
                        self.username_entry.config(fg='#2c3e50')
                    
                    if password:
                        # Clear placeholder and set actual value
                        self.password_entry.delete(0, tk.END)
                        self.password_entry.insert(0, password)
                        self.password_entry.config(fg='#2c3e50', show='*')
                    
                    self.log_message("✅ Loaded saved credentials")
        except Exception as e:
            self.log_message(f"⚠️ Error loading credentials: {e}")
    
    def get_username(self):
        """Get username, handling placeholder text"""
        username = self.username_entry.get().strip()
        return '' if username == 'Enter your email address' else username
    
    def get_password(self):
        """Get password, handling placeholder text"""
        password = self.password_entry.get().strip()
        return '' if password == 'Enter your password' else password
    
    def save_credentials(self):
        """Save credentials to file"""
        if not self.save_creds_var.get():
            self.log_message("💾 Credentials not saved (checkbox unchecked)")
            return
        
        username = self.get_username()
        password = self.get_password()
        
        if not username or not password:
            messagebox.showwarning("Warning", "Please enter both username and password")
            return
        
        try:
            creds = {
                'username': username,
                'password': password,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(creds, f, indent=2)
            
            self.log_message("✅ Credentials saved successfully")
            self.login_status_label.config(text="✅ Credentials saved", fg='green')
            
        except Exception as e:
            self.log_message(f"❌ Error saving credentials: {e}")
            messagebox.showerror("Error", f"Failed to save credentials: {e}")
    
    def test_login(self):
        """Test login credentials"""
        username = self.get_username()
        password = self.get_password()
        
        if not username or not password:
            messagebox.showwarning("Warning", "Please enter both username and password")
            return
        
        self.login_status_label.config(text="🔄 Testing login...", fg='orange')
        self.log_message("🔍 Testing login credentials...")
        
        # Run test in separate thread to avoid blocking GUI
        def test_thread():
            try:
                # Setup driver
                driver = self.setup_driver(headless=True)
                
                # Attempt login
                success = self.perform_login(driver, username, password)
                
                # Update GUI in main thread
                self.root.after(0, lambda: self.update_login_status(success))
                
                # Cleanup
                if driver:
                    driver.quit()
                    
            except Exception as e:
                self.root.after(0, lambda: self.update_login_status(False, str(e)))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def update_login_status(self, success, error_msg=None):
        """Update login status in GUI"""
        if success:
            self.login_status_label.config(text="✅ Login successful!", fg='green')
            self.log_message("✅ Login test successful")
            
            # Auto-save credentials if checkbox is checked
            if self.save_creds_var.get():
                self.save_credentials()
        else:
            error_text = f"❌ Login failed"
            if error_msg:
                error_text += f": {error_msg}"
            self.login_status_label.config(text=error_text, fg='red')
            self.log_message(f"❌ Login test failed: {error_msg or 'Unknown error'}")
    
    def setup_driver(self, headless=True):
        """Setup Chrome WebDriver with enhanced stability options"""
        try:
            self.log_message("🔧 Setting up new browser session...")
            
            options = webdriver.ChromeOptions()
            
            # Headless mode options
            if headless:
                options.add_argument('--headless=new')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-software-rasterizer')
            
            # Stability and performance options
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')  # Faster loading
            options.add_argument('--disable-javascript')  # We'll enable it selectively
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            
            # Memory and process management
            options.add_argument('--memory-pressure-off')
            options.add_argument('--max_old_space_size=4096')
            
            # Network and timeout settings
            options.add_argument('--aggressive-cache-discard')
            options.add_argument('--disable-background-networking')
            
            # Anti-detection options
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # User agent
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Enhanced Chrome and ChromeDriver detection for compiled EXE
            service = None
            driver = None
            
            # Try multiple methods to find Chrome and ChromeDriver
            try:
                # Method 1: Try ChromeDriverManager (works in most cases, but may fail in auto-start)
                self.log_message("🔍 Attempting to use ChromeDriverManager...")
                
                # Set a shorter timeout for ChromeDriverManager in auto-start mode
                import socket
                socket.setdefaulttimeout(10)  # 10 second timeout
                
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                self.log_message("✅ Successfully created driver with ChromeDriverManager")
                
            except Exception as e1:
                self.log_message(f"⚠️ ChromeDriverManager failed: {str(e1)[:100]}...")
                
                try:
                    # Method 2: Try to find Chrome binary manually and use system chromedriver
                    self.log_message("🔍 Attempting to find Chrome binary manually...")
                    
                    # Enhanced Chrome installation paths for compiled EXE environments
                    username = os.getenv('USERNAME', os.getenv('USER', ''))
                    userprofile = os.getenv('USERPROFILE', f'C:\\Users\\{username}')
                    
                    chrome_paths = [
                        # Standard installation paths
                        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                        f"{userprofile}\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe",
                        
                        # Alternative user paths
                        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(username),
                        
                        # Beta and Dev versions
                        r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe",
                        r"C:\Program Files (x86)\Google\Chrome Beta\Application\chrome.exe",
                        f"{userprofile}\\AppData\\Local\\Google\\Chrome Beta\\Application\\chrome.exe",
                        
                        # Portable Chrome installations
                        r"C:\PortableApps\GoogleChromePortable\App\Chrome-bin\chrome.exe",
                        
                        # Check in application directory (bundled Chrome)
                        os.path.join(self.get_application_directory(), "chrome.exe"),
                        os.path.join(self.get_application_directory(), "Chrome", "chrome.exe")
                    ]
                    
                    chrome_binary = None
                    self.log_message(f"🔍 Checking {len(chrome_paths)} potential Chrome locations...")
                    
                    for i, path in enumerate(chrome_paths, 1):
                        self.log_message(f"   {i}. Checking: {path}")
                        if os.path.exists(path):
                            chrome_binary = path
                            self.log_message(f"✅ Found Chrome at: {path}")
                            break
                        else:
                            self.log_message(f"   ❌ Not found")
                    
                    if not chrome_binary:
                        self.log_message("⚠️ No Chrome installation found in standard locations")
                        # Try to find Chrome via registry (Windows)
                        try:
                            import winreg
                            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")
                            chrome_binary = winreg.QueryValue(key, "")
                            winreg.CloseKey(key)
                            if os.path.exists(chrome_binary):
                                self.log_message(f"✅ Found Chrome via registry: {chrome_binary}")
                            else:
                                chrome_binary = None
                        except:
                            pass
                    
                    if chrome_binary:
                        options.binary_location = chrome_binary
                        
                        # Try to use system chromedriver or bundled one
                        app_dir = self.get_application_directory()
                        chromedriver_paths = [
                            os.path.join(app_dir, "chromedriver.exe"),  # Bundled with EXE
                            "chromedriver.exe",  # In PATH
                            "chromedriver"  # In PATH (no extension)
                        ]
                        
                        chromedriver_path = None
                        for path in chromedriver_paths:
                            try:
                                if os.path.exists(path) or path in ["chromedriver.exe", "chromedriver"]:
                                    service = Service(path)
                                    driver = webdriver.Chrome(service=service, options=options)
                                    chromedriver_path = path
                                    self.log_message(f"✅ Successfully created driver with chromedriver at: {path}")
                                    break
                            except:
                                continue
                        
                        if not driver:
                            # Try without specifying service (use default)
                            driver = webdriver.Chrome(options=options)
                            self.log_message("✅ Successfully created driver with default service")
                    
                except Exception as e2:
                    self.log_message(f"⚠️ Manual Chrome detection failed: {str(e2)[:100]}...")
                    
                    try:
                        # Method 3: Last resort - try default Chrome without any service specification
                        self.log_message("🔍 Attempting default Chrome setup...")
                        driver = webdriver.Chrome(options=options)
                        self.log_message("✅ Successfully created driver with default setup")
                        
                    except Exception as e3:
                        self.log_message(f"❌ All Chrome setup methods failed:")
                        self.log_message(f"   Method 1 (ChromeDriverManager): {str(e1)[:100]}...")
                        self.log_message(f"   Method 2 (Manual detection): {str(e2)[:100]}...")
                        self.log_message(f"   Method 3 (Default): {str(e3)[:100]}...")
                        
                        # Show Chrome installation notification
                        self.show_chrome_installation_notification()
                        
                        raise Exception("Unable to initialize Chrome browser. Please ensure Chrome is installed and accessible.")
            
            # Set timeouts
            driver.set_page_load_timeout(30)  # 30 seconds page load timeout
            driver.implicitly_wait(10)  # 10 seconds implicit wait
            
            # Anti-detection script
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set window size for headless mode
            if headless:
                driver.set_window_size(1920, 1080)
            
            self.log_message("✅ Browser session created successfully")
            return driver
            
        except Exception as e:
            error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
            self.log_message(f"❌ Error setting up browser: {error_msg}")
            raise
    
    def perform_login(self, driver, username, password):
        """Perform login to Superset with enhanced error handling"""
        try:
            # Check if the provided driver is valid
            if not self.is_driver_valid(driver):
                raise Exception("Driver session is invalid")
            
            self.log_message(f"🔐 Navigating to login page...")
            
            # Navigate with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    driver.get(self.login_url)
                    break
                except Exception as nav_error:
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to navigate to login page: {nav_error}")
                    self.log_message(f"⚠️ Navigation attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)
            
            # Wait for page to load completely
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)  # Additional wait for dynamic content
            
            # Find username field with multiple strategies
            username_field = None
            selectors = [
                (By.NAME, "email"),
                (By.NAME, "username"), 
                (By.ID, "email"),
                (By.ID, "username"),
                (By.XPATH, "//input[@type='email']"),
                (By.XPATH, "//input[@placeholder*='email' or @placeholder*='Email']"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[name*='email']"),
                (By.CSS_SELECTOR, "input[name*='username']")
            ]
            
            for selector_type, selector_value in selectors:
                try:
                    username_field = WebDriverWait(driver, 8).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    self.log_message(f"✅ Found username field with: {selector_value}")
                    break
                except:
                    continue
            
            if not username_field:
                # Save page source for debugging
                try:
                    with open('login_page_debug.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    self.log_message("💾 Saved login page source for debugging")
                except:
                    pass
                raise Exception("Could not find username/email field after trying all selectors")
            
            # Find password field
            password_field = None
            password_selectors = [
                (By.NAME, "password"),
                (By.ID, "password"),
                (By.XPATH, "//input[@type='password']"),
                (By.CSS_SELECTOR, "input[type='password']")
            ]
            
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((selector_type, selector_value))
                    )
                    self.log_message(f"✅ Found password field")
                    break
                except:
                    continue
            
            if not password_field:
                raise Exception("Could not find password field")
            
            # Clear and enter credentials with retry
            for attempt in range(3):
                try:
                    username_field.clear()
                    username_field.send_keys(username)
                    
                    password_field.clear()
                    password_field.send_keys(password)
                    break
                except Exception as input_error:
                    if attempt == 2:
                        raise Exception(f"Failed to enter credentials: {input_error}")
                    time.sleep(1)
            
            self.log_message("✅ Credentials entered, submitting form...")
            
            # Submit form with multiple strategies
            submitted = False
            submit_strategies = [
                lambda: driver.find_element(By.XPATH, "//button[@type='submit']").click(),
                lambda: driver.find_element(By.XPATH, "//button[contains(text(), 'Log') or contains(text(), 'Sign')]").click(),
                lambda: driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click(),
                lambda: password_field.send_keys(Keys.RETURN),
                lambda: username_field.send_keys(Keys.RETURN)
            ]
            
            for i, strategy in enumerate(submit_strategies):
                try:
                    strategy()
                    self.log_message(f"✅ Form submitted using strategy {i + 1}")
                    submitted = True
                    break
                except Exception as submit_error:
                    self.log_message(f"⚠️ Submit strategy {i + 1} failed: {str(submit_error)[:50]}...")
                    continue
            
            if not submitted:
                raise Exception("Could not submit login form with any strategy")
            
            # Wait for successful login with extended timeout
            self.log_message("⏳ Waiting for login redirect...")
            
            try:
                # Wait for redirect to dashboard
                WebDriverWait(driver, 20).until(
                    lambda d: self.dashboard_url in d.current_url or "dashboard" in d.current_url.lower() or "students" in d.current_url.lower()
                )
                self.log_message(f"✅ Login successful - redirected to: {driver.current_url}")
                return True
                
            except Exception as redirect_error:
                self.log_message(f"⚠️ Auto-redirect failed: {redirect_error}")
                
                # Manual navigation as fallback
                self.log_message("🔄 Attempting manual navigation to dashboard...")
                try:
                    driver.get(self.dashboard_url)
                    time.sleep(5)
                    
                    current_url = driver.current_url
                    if self.dashboard_url in current_url or "students" in current_url:
                        self.log_message(f"✅ Manual navigation successful: {current_url}")
                        return True
                    else:
                        self.log_message(f"❌ Manual navigation failed - still at: {current_url}")
                        return False
                        
                except Exception as manual_nav_error:
                    self.log_message(f"❌ Manual navigation error: {manual_nav_error}")
                    return False
                
        except Exception as e:
            error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
            self.log_message(f"❌ Login error: {error_msg}")
            return False
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        if self.monitoring_active:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start the monitoring process"""
        username = self.get_username()
        password = self.get_password()
        
        if not username or not password:
            messagebox.showwarning("Warning", "Please enter login credentials first")
            self.notebook.select(0)  # Switch to login tab
            return
        
        if self.monitoring_active:
            self.log_message("⚠️ Monitoring is already active")
            return
        
        self.monitoring_active = True
        self.update_monitoring_button()
        self.monitor_status_label.config(text="▶️ Running", fg='green')
        
        self.log_message("🚀 Starting post monitoring...")
        
        # Update tray menu
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.update_menu()
        
        # Start monitoring in separate thread
        self.monitor_thread = threading.Thread(target=self.monitor_loop, args=(username, password), daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.monitoring_active = False
        
        # Update GUI
        self.update_monitoring_button()
        
        if hasattr(self, 'monitor_status_label'):
            self.monitor_status_label.config(text="⏹️ Stopped", fg='red')
        
        self.log_message("⏹️ Stopping monitoring...")
        
        # Cleanup driver
        self.cleanup_driver()
        
        # Update tray menu
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.update_menu()
        
        self.log_message("✅ Monitoring stopped successfully")
    
    def update_monitoring_button(self):
        """Update the monitoring toggle button and status indicators based on current state"""
        if hasattr(self, 'toggle_monitoring_btn'):
            if self.monitoring_active:
                # Update button for stop action
                self.toggle_monitoring_btn.config(
                    text="⏹ Stop Monitoring",
                    bg='#e74c3c',  # Modern red
                    fg='white'
                )
                # Update hover effects
                self.add_button_hover_effects(self.toggle_monitoring_btn, '#e74c3c', '#ec7063')
                
                # Update status indicators
                if hasattr(self, 'status_indicator'):
                    self.status_indicator.config(text="▶", fg='#27ae60')
                if hasattr(self, 'monitor_status_label'):
                    self.monitor_status_label.config(text="Running", fg='#27ae60')
                if hasattr(self, 'status_description'):
                    self.status_description.config(text="Actively monitoring for new posts")
            else:
                # Update button for start action
                self.toggle_monitoring_btn.config(
                    text="▶ Start Monitoring",
                    bg='#27ae60',  # Modern green
                    fg='white'
                )
                # Update hover effects
                self.add_button_hover_effects(self.toggle_monitoring_btn, '#27ae60', '#2ecc71')
                
                # Update status indicators
                if hasattr(self, 'status_indicator'):
                    self.status_indicator.config(text="⏹", fg='#e74c3c')
                if hasattr(self, 'monitor_status_label'):
                    self.monitor_status_label.config(text="Stopped", fg='#e74c3c')
                if hasattr(self, 'status_description'):
                    self.status_description.config(text="Monitoring is currently inactive")
    
    def check_now(self):
        """Perform immediate check for new posts"""
        username = self.get_username()
        password = self.get_password()
        
        if not username or not password:
            messagebox.showwarning("Warning", "Please enter login credentials first")
            self.notebook.select(0)  # Switch to login tab
            return
        
        self.log_message("🔍 Performing immediate check...")
        
        # Run check in separate thread
        def check_thread():
            try:
                driver = self.setup_driver(headless=self.headless_var.get())
                
                if self.perform_login(driver, username, password):
                    new_posts = self.check_for_posts(driver, force_full_scroll=True)
                    
                    # Update GUI in main thread
                    self.root.after(0, lambda: self.handle_check_results(new_posts))
                else:
                    self.root.after(0, lambda: self.log_message("❌ Login failed during manual check"))
                
                if driver:
                    driver.quit()
                    
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"❌ Check failed: {e}"))
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def monitor_loop(self, username, password):
        """Main monitoring loop with robust session management"""
        consecutive_failures = 0
        max_failures = 3
        
        while self.monitoring_active:
            try:
                self.log_message("🔄 Starting check cycle...")
                
                # Check if driver is still valid
                driver_valid = self.is_driver_valid(self.driver)
                
                if not driver_valid:
                    self.log_message("🔧 Driver invalid or missing, creating new session...")
                    self.cleanup_driver()
                    self.driver = self.setup_driver(headless=self.headless_var.get())
                
                # Attempt login and post check
                login_success = False
                try:
                    login_success = self.perform_login(self.driver, username, password)
                except Exception as login_error:
                    self.log_message(f"❌ Login attempt failed: {str(login_error)[:100]}...")
                    # Force driver recreation on login failure
                    self.cleanup_driver()
                    login_success = False
                
                if login_success:
                    try:
                        # Check for posts
                        new_posts = self.check_for_posts(self.driver)
                        
                        # Update GUI in main thread
                        self.root.after(0, lambda: self.handle_check_results(new_posts))
                        
                        # Update last check time
                        self.root.after(0, lambda: self.last_check_label.config(
                            text=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                        
                        # Reset failure counter on success
                        consecutive_failures = 0
                        self.log_message("✅ Check cycle completed successfully")
                        
                    except Exception as check_error:
                        self.log_message(f"❌ Post check failed: {str(check_error)[:100]}...")
                        consecutive_failures += 1
                        self.cleanup_driver()  # Force fresh start next time
                else:
                    self.log_message("❌ Login failed during monitoring")
                    consecutive_failures += 1
                    self.cleanup_driver()  # Force fresh start next time
                
                # Handle consecutive failures
                if consecutive_failures >= max_failures:
                    self.log_message(f"⚠️ {consecutive_failures} consecutive failures. Taking longer break...")
                    failure_wait = min(300, 60 * consecutive_failures)  # Max 5 minutes
                    self.log_message(f"⏰ Waiting {failure_wait // 60} minutes before retry...")
                    
                    for _ in range(failure_wait):
                        if not self.monitoring_active:
                            break
                        time.sleep(1)
                    
                    consecutive_failures = 0  # Reset after longer wait
                    continue
                
                # Normal wait for next check
                if self.monitoring_active:
                    wait_minutes = self.check_interval // 60
                    self.log_message(f"⏰ Waiting {wait_minutes} minutes until next check...")
                    
                    # Sleep in small intervals to allow for quick stop
                    for _ in range(self.check_interval):
                        if not self.monitoring_active:
                            break
                        time.sleep(1)
                
            except Exception as e:
                error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
                self.root.after(0, lambda: self.log_message(f"❌ Monitor error: {error_msg}"))
                consecutive_failures += 1
                
                # Cleanup on any error
                self.cleanup_driver()
                
                # Progressive backoff on errors
                wait_time = min(120, 30 * consecutive_failures)  # Max 2 minutes
                self.log_message(f"⏰ Error recovery wait: {wait_time} seconds...")
                time.sleep(wait_time)
        
        # Final cleanup
        self.cleanup_driver()
        self.log_message("🛑 Monitoring loop ended")
    
    def is_driver_valid(self, driver=None):
        """Check if the specified driver session is still valid"""
        test_driver = driver if driver is not None else self.driver
        
        if not test_driver:
            return False
        
        try:
            # Try a simple operation to test if driver is responsive
            test_driver.current_url
            return True
        except Exception as e:
            if driver is None:  # Only log for instance driver
                self.log_message(f"🔧 Driver validation failed: {str(e)[:100]}...")
            return False
    
    def cleanup_driver(self):
        """Safely cleanup the current driver"""
        if self.driver:
            try:
                self.driver.quit()
                self.log_message("🧹 Driver cleaned up successfully")
            except Exception as e:
                self.log_message(f"⚠️ Driver cleanup warning: {str(e)[:50]}...")
            finally:
                self.driver = None
    
    def check_for_posts(self, driver, force_full_scroll=False):
        """Check for new posts on the dashboard"""
        try:
            # Navigate to dashboard
            if self.dashboard_url not in driver.current_url:
                driver.get(self.dashboard_url)
                time.sleep(5)
            
            # Wait for content to load
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(3)
            
            # Smart scrolling if enabled
            if self.auto_scroll_var.get() or force_full_scroll:
                self.scroll_to_load_posts(driver, force_full_scroll)
            
            # Extract posts
            current_posts = self.extract_posts(driver)
            
            # Reload known posts from file to get latest changes (in case user manually edited)
            self.log_message("🔄 Reloading known posts from file...")
            old_count = len(self.known_posts)
            self.load_known_posts(verbose=True)
            new_count = len(self.known_posts)
            
            if new_count != old_count:
                self.log_message(f"📊 Known posts updated: {old_count} → {new_count} posts")
            else:
                self.log_message(f"📊 Known posts: {new_count} posts loaded")
            
            # Compare with known posts
            new_posts = []
            for post in current_posts:
                if post['title'] not in self.known_posts:
                    new_posts.append(post)
                    self.known_posts[post['title']] = {
                        'title': post['title'],
                        'author': post.get('author', ''),
                        'time': post.get('time', ''),
                        'details': post.get('details', ''),
                        'links': post.get('links', []),
                        'found_at': datetime.now().isoformat()
                    }
                    self.log_message(f"🆕 NEW POST DETECTED: {post['title']}")
                else:
                    self.log_message(f"✅ Known post: {post['title'][:50]}...")
            
            if new_posts:
                self.save_known_posts()
                self.save_posts_to_log(new_posts)
                
                # Send notifications
                if self.notifications_var.get() and NOTIFICATIONS_AVAILABLE:
                    self.send_notifications(new_posts)
            
            return new_posts
            
        except Exception as e:
            self.log_message(f"❌ Error checking posts: {e}")
            return []
    
    def scroll_to_load_posts(self, driver, force_full=False):
        """Scroll to load all posts"""
        try:
            # Find scrollable container
            container_selectors = [
                'div.flex-grow.overflow-scroll.sm\\:mb-0',
                'div[class*="flex-grow"][class*="overflow-scroll"]',
                'div.overflow-scroll',
                '[class*="overflow-scroll"]'
            ]
            
            scroll_container = None
            for selector in container_selectors:
                try:
                    scroll_container = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not scroll_container:
                # Fallback to page scroll
                self.scroll_page(driver)
                return
            
            # Smart scrolling
            last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
            scroll_attempts = 0
            max_attempts = 20 if force_full else 10
            consecutive_no_change = 0
            
            while scroll_attempts < max_attempts:
                # Scroll down
                current_scroll = driver.execute_script("return arguments[0].scrollTop", scroll_container)
                driver.execute_script("arguments[0].scrollTop = arguments[1] + 1000", scroll_container, current_scroll)
                
                time.sleep(2)
                
                # Check if content loaded
                new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
                
                if new_height == last_height:
                    consecutive_no_change += 1
                    if consecutive_no_change >= 3:
                        break
                else:
                    consecutive_no_change = 0
                    
                    # If not forcing full scroll, check for known posts
                    if not force_full and self.should_stop_scrolling(driver):
                        self.log_message("🛑 Found known posts, stopping scroll early")
                        break
                
                last_height = new_height
                scroll_attempts += 1
            
            # Scroll back to top
            driver.execute_script("arguments[0].scrollTop = 0", scroll_container)
            time.sleep(1)
            
        except Exception as e:
            self.log_message(f"⚠️ Scroll error: {e}")
    
    def scroll_page(self, driver):
        """Fallback page scrolling"""
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_attempts = 10
        
        while scroll_attempts < max_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            
            last_height = new_height
            scroll_attempts += 1
        
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
    
    def should_stop_scrolling(self, driver):
        """Check if we should stop scrolling (found known posts)"""
        try:
            feed_headers = driver.find_elements(By.CLASS_NAME, "feedHeader")
            if not feed_headers:
                return False
            
            # Check last 5 posts
            recent_headers = feed_headers[-5:] if len(feed_headers) > 5 else feed_headers
            known_count = 0
            
            for header in recent_headers:
                try:
                    title_element = header.find_element(By.CSS_SELECTOR, "p.text-base.font-bold.text-dark")
                    post_title = title_element.text.strip()
                    
                    if post_title in self.known_posts:
                        known_count += 1
                except:
                    continue
            
            # Stop if most recent posts are known
            return known_count >= len(recent_headers) * 0.8
            
        except:
            return False
    
    def extract_posts(self, driver):
        """Extract posts from the page including detailed content"""
        posts = []
        
        try:
            feed_headers = driver.find_elements(By.CLASS_NAME, "feedHeader")
            self.log_message(f"📋 Found {len(feed_headers)} feedHeader elements")
            
            for i, header in enumerate(feed_headers):
                try:
                    # Extract title
                    title_element = header.find_element(By.CSS_SELECTOR, "p.text-base.font-bold.text-dark")
                    post_title = title_element.text.strip()
                    
                    # Extract author and time
                    flex_div = header.find_element(By.CSS_SELECTOR, "div.flex.mt-1.flex-wrap")
                    spans = flex_div.find_elements(By.CSS_SELECTOR, "span.text-gray-500.text-xs")
                    
                    author = ""
                    post_time = ""
                    
                    if len(spans) >= 2:
                        author = spans[0].text.strip()
                        post_time = spans[1].text.strip()
                    elif len(spans) == 1:
                        post_time = spans[0].text.strip()
                    
                    # Extract detailed post content from prose div
                    post_details = ""
                    post_links = []
                    
                    try:
                        # Look for the prose div in the parent container
                        parent_container = header.find_element(By.XPATH, "../..")  # Go up two levels
                        
                        # Try to find the prose div with the specific structure
                        prose_selectors = [
                            'div.prose',
                            'div[class*="prose"]',
                            'div.prose p.text-sm.text-gray-600',
                            'div p.text-sm.text-gray-600'
                        ]
                        
                        prose_element = None
                        for selector in prose_selectors:
                            try:
                                prose_element = parent_container.find_element(By.CSS_SELECTOR, selector)
                                break
                            except:
                                continue
                        
                        if prose_element:
                            # Extract the full text content
                            post_details = prose_element.text.strip()
                            
                            # Extract all links from the prose content
                            try:
                                link_elements = prose_element.find_elements(By.TAG_NAME, "a")
                                for link_elem in link_elements:
                                    href = link_elem.get_attribute("href")
                                    text = link_elem.text.strip()
                                    if href:
                                        post_links.append({
                                            'url': href,
                                            'text': text
                                        })
                            except:
                                pass
                            
                            self.log_message(f"📄 Extracted details for post {i+1}: {len(post_details)} characters")
                        else:
                            self.log_message(f"⚠️ No prose content found for post {i+1}")
                            
                    except Exception as detail_error:
                        self.log_message(f"⚠️ Error extracting details for post {i+1}: {str(detail_error)}")
                    
                    post_data = {
                        'title': post_title,
                        'author': author,
                        'time': post_time,
                        'details': post_details,
                        'links': post_links,
                        'found_at': datetime.now().isoformat()
                    }
                    
                    posts.append(post_data)
                    
                except Exception as e:
                    self.log_message(f"⚠️ Error parsing post {i}: {str(e)}")
                    continue
            
        except Exception as e:
            self.log_message(f"⚠️ Error extracting posts: {e}")
        
        return posts
    
    def handle_check_results(self, new_posts):
        """Handle results from post check"""
        if new_posts:
            self.log_message(f"🎉 Found {len(new_posts)} new posts!")
            for post in new_posts:
                self.log_message(f"📝 New: {post['title'][:60]}...")
        else:
            self.log_message("✅ No new posts found")
        
        # Update posts count and file modified time
        self.posts_count_label.config(text=f"{len(self.known_posts)} posts")
        self.file_modified_label.config(text=self.get_file_modified_time())
        
        # Update tray tooltip
        self.update_tray_tooltip()
        
        # Refresh posts display if on that tab
        self.refresh_posts_display()
    
    def send_notifications(self, new_posts):
        """Send desktop notifications for new posts based on user preference"""
        if not self.notifications_var.get():
            return
            
        notification_type = self.notification_type_var.get()
        
        try:
            if notification_type == "custom":
                self.send_custom_toast_notifications(new_posts)
            elif notification_type == "windows" and WINDOWS_TOAST_AVAILABLE:
                self.send_windows_toast_notifications(new_posts)
            elif notification_type == "basic" and NOTIFICATIONS_AVAILABLE:
                self.send_basic_notifications(new_posts)
            else:
                # Fallback to custom toast
                self.send_custom_toast_notifications(new_posts)
                
        except Exception as e:
            self.log_message(f"⚠️ Notification error: {e}")
            # Ultimate fallback
            try:
                self.send_custom_toast_notifications(new_posts)
            except:
                self.log_message("❌ All notification methods failed")
    
    def send_custom_toast_notifications(self, new_posts):
        """Send custom interactive toast notifications"""
        for post in new_posts:
            self.create_toast_notification(post)
            time.sleep(0.5)
    
    def send_windows_toast_notifications(self, new_posts):
        """Send Windows native toast notifications with action buttons"""
        if not WINDOWS_TOAST_AVAILABLE:
            return
            
        try:
            toaster = ToastNotifier()
            
            for post in new_posts:
                title = "🔔 New Superset Post!"
                message = post['title'][:100]
                if post.get('author'):
                    message += f"\nBy: {post['author']}"
                if post.get('time'):
                    message += f" • {post['time']}"
                
                # Windows toast with callback
                def on_click():
                    webbrowser.open(self.dashboard_url)
                    self.log_message(f"🔗 Opened link from notification: {post['title'][:30]}...")
                
                toaster.show_toast(
                    title=title,
                    msg=message,
                    duration=15,
                    callback_on_click=on_click,
                    threaded=True
                )
                time.sleep(1)
                
        except Exception as e:
            self.log_message(f"⚠️ Windows toast error: {e}")
            self.send_custom_toast_notifications(new_posts)
    
    def send_basic_notifications(self, new_posts):
        """Fallback basic notifications"""
        if not NOTIFICATIONS_AVAILABLE:
            return
            
        try:
            for post in new_posts:
                title = "🔔 New Superset Post!"
                message = post['title'][:100]
                if post.get('author'):
                    message += f"\nBy: {post['author']}"
                if post.get('time'):
                    message += f" • {post['time']}"
                
                notification.notify(
                    title=title,
                    message=message,
                    timeout=10
                )
                time.sleep(1)
                
        except Exception as e:
            self.log_message(f"⚠️ Basic notification error: {e}")
    
    def show_chrome_installation_notification(self):
        """Show notification to install Chrome browser"""
        try:
            self.log_message("🌐 Showing Chrome installation notification...")
            
            # Show system notification if available
            if NOTIFICATIONS_AVAILABLE:
                try:
                    notification.notify(
                        title="Chrome Browser Required",
                        message="Chrome browser is not installed or not accessible. Please install Chrome to use the monitoring system.",
                        timeout=15
                    )
                except:
                    pass
            
            # Show Windows toast notification if available
            if WINDOWS_TOAST_AVAILABLE:
                try:
                    toaster = ToastNotifier()
                    toaster.show_toast(
                        "Chrome Browser Required",
                        "Chrome browser is not installed or not accessible. Please install Chrome to use the monitoring system.",
                        duration=15,
                        threaded=True
                    )
                except:
                    pass
            
            # Show GUI message box as fallback
            try:
                messagebox.showerror(
                    "Chrome Browser Required",
                    "Chrome browser is not installed or not accessible.\n\n"
                    "Please install Google Chrome from:\n"
                    "https://www.google.com/chrome/\n\n"
                    "After installation, restart the application to continue monitoring."
                )
            except:
                pass
            
            # Also show a custom toast notification with download link
            self.show_chrome_install_toast()
            
        except Exception as e:
            self.log_message(f"⚠️ Error showing Chrome installation notification: {e}")
    
    def show_chrome_install_toast(self):
        """Show custom toast notification with Chrome download link"""
        try:
            def show_toast():
                # Create the toast window
                toast = tk.Toplevel()
                toast.title("Chrome Required")
                toast.configure(bg='#000000')
                
                # Hide window initially to prevent flashing
                toast.withdraw()
                
                # Calculate position first
                window_width = 420
                window_height = 300
                screen_width = toast.winfo_screenwidth()
                screen_height = toast.winfo_screenheight()
                x = screen_width - window_width - 30
                y = 60
                
                # Set geometry before showing
                toast.geometry(f"{window_width}x{window_height}+{x}+{y}")
                
                # Window properties
                toast.attributes('-topmost', True)
                toast.attributes('-toolwindow', True)
                toast.overrideredirect(True)
                
                try:
                    toast.attributes('-alpha', 0.98)
                except:
                    pass
                
                # Main frame
                main_frame = tk.Frame(toast, bg='#ffffff', relief='flat', bd=0)
                main_frame.pack(fill='both', expand=True, padx=3, pady=3)
                
                # Header
                header_frame = tk.Frame(main_frame, bg='#ef4444', height=60)
                header_frame.pack(fill='x')
                header_frame.pack_propagate(False)
                
                header_content = tk.Frame(header_frame, bg='#ef4444')
                header_content.pack(fill='both', expand=True, padx=15, pady=8)
                
                # Icon and title
                icon_container = tk.Frame(header_content, bg='#ef4444')
                icon_container.pack(side='left')
                
                icon_label = tk.Label(icon_container, text="🌐", font=('Segoe UI Emoji', 14), 
                                    bg='#ef4444', fg='#ffffff')
                icon_label.pack(expand=True)
                
                title_container = tk.Frame(header_content, bg='#ef4444')
                title_container.pack(side='left', fill='x', expand=True, padx=(12, 0))
                
                title_label = tk.Label(title_container, text="Chrome Browser Required", 
                                     font=('Segoe UI', 13, 'bold'), bg='#ef4444', fg='#ffffff')
                title_label.pack(anchor='w')
                
                subtitle_label = tk.Label(title_container, text="Installation needed", 
                                        font=('Segoe UI', 9), bg='#ef4444', fg='#fecaca')
                subtitle_label.pack(anchor='w')
                
                # Close button
                close_btn = tk.Button(header_content, text="✕", font=('Segoe UI', 12, 'bold'),
                                    bg='#dc2626', fg='white', relief='flat', width=3, height=1,
                                    command=toast.destroy, cursor='hand2', bd=0)
                close_btn.pack(side='right')
                
                # Content
                content_frame = tk.Frame(main_frame, bg='#ffffff')
                content_frame.pack(fill='both', expand=True, padx=20, pady=20)
                
                # Message
                message_label = tk.Label(content_frame, 
                                       text="Chrome browser is not installed or accessible.\n\n"
                                            "The monitoring system requires Google Chrome to function properly.\n\n"
                                            "Please install Chrome and restart the application.",
                                       font=('Segoe UI', 10), bg='#ffffff', fg='#374151',
                                       justify='left', wraplength=350)
                message_label.pack(anchor='w', pady=(0, 20))
                
                # Buttons
                buttons_frame = tk.Frame(content_frame, bg='#ffffff')
                buttons_frame.pack(fill='x')
                
                def download_chrome():
                    try:
                        webbrowser.open('https://www.google.com/chrome/')
                        self.log_message("🌐 Opened Chrome download page")
                        toast.destroy()
                    except Exception as e:
                        self.log_message(f"❌ Error opening Chrome download page: {e}")
                
                download_btn = tk.Button(buttons_frame, text="🌐 Download Chrome", 
                                       command=download_chrome, bg='#3b82f6', fg='white', 
                                       font=('Segoe UI', 10, 'bold'), relief='flat', 
                                       padx=20, pady=8, cursor='hand2', bd=0)
                download_btn.pack(side='left', padx=(0, 10))
                
                close_btn2 = tk.Button(buttons_frame, text="✕ Close", 
                                     command=toast.destroy, bg='#6b7280', fg='white', 
                                     font=('Segoe UI', 10, 'bold'), relief='flat', 
                                     padx=20, pady=8, cursor='hand2', bd=0)
                close_btn2.pack(side='left')
                
                # Show the window after all content is created
                toast.deiconify()
                
                # Auto-close after 30 seconds
                toast.after(30000, toast.destroy)
            
            # Run in thread to avoid blocking
            import threading
            toast_thread = threading.Thread(target=show_toast, daemon=True)
            toast_thread.start()
            
        except Exception as e:
            self.log_message(f"⚠️ Error showing Chrome install toast: {e}")

    def create_toast_notification(self, post):
        """Create a modern custom toast notification window with enhanced styling and animations"""
        def show_toast():
            # Create the toast window
            toast = tk.Toplevel()
            toast.title("New Superset Post")
            toast.configure(bg='#000000')  # Black background for transparency effect
            
            # Hide window initially to prevent flashing
            toast.withdraw()
            
            # Add to tracking list
            self.open_notifications.append(toast)
            
            # Calculate position first (top-right corner with better spacing)
            window_width = 420
            window_height = 450  # Optimized height
            expanded_height = 580  # Height when expanded
            screen_width = toast.winfo_screenwidth()
            screen_height = toast.winfo_screenheight()
            x = screen_width - window_width - 30  # More margin from edge
            y = 60  # Better top margin
            
            # Set geometry before configuring window properties
            toast.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # Window properties for modern appearance
            toast.attributes('-topmost', True)
            toast.attributes('-toolwindow', True)  # Hide from taskbar
            toast.overrideredirect(True)  # Remove window decorations
            
            # Try to make window semi-transparent (Windows only)
            try:
                toast.attributes('-alpha', 0.98)  # Slight transparency for modern look
            except:
                pass
            
            # Variables for state management
            auto_close_timer = None
            auto_close_enabled = tk.BooleanVar(value=False)
            is_details_expanded = tk.BooleanVar(value=False)
            
            # Outer container for shadow effect
            shadow_frame = tk.Frame(toast, bg='#1a1a1a', relief='flat', bd=0)
            shadow_frame.pack(fill='both', expand=True, padx=3, pady=3)
            
            # Main container with modern gradient-like appearance
            main_frame = tk.Frame(shadow_frame, bg='#ffffff', relief='flat', bd=0)
            main_frame.pack(fill='both', expand=True)
            
            # Modern header with gradient-like styling
            header_frame = tk.Frame(main_frame, bg='#4f46e5', height=60)  # Modern purple - increased height
            header_frame.pack(fill='x')
            header_frame.pack_propagate(False)
            
            # Header gradient effect (top border)
            header_top = tk.Frame(header_frame, bg='#6366f1', height=2)
            header_top.pack(fill='x')
            
            # Notification icon and title container
            header_content = tk.Frame(header_frame, bg='#4f46e5')
            header_content.pack(fill='both', expand=True, padx=15, pady=8)
            
            # Modern notification icon with better styling
            icon_container = tk.Frame(header_content, bg='#4f46e5')
            icon_container.pack(side='left')
            
            icon_bg = tk.Frame(icon_container, bg='#4f46e5', width=32, height=32)
            icon_bg.pack()
            icon_bg.pack_propagate(False)
            
            icon_label = tk.Label(icon_bg, text="🔔", font=('Segoe UI Emoji', 14), 
                                bg='#4f46e5', fg='#ffffff')
            icon_label.pack(expand=True)
            
            # Title with modern typography
            title_container = tk.Frame(header_content, bg='#4f46e5')
            title_container.pack(side='left', fill='x', expand=True, padx=(12, 0))
            
            title_label = tk.Label(title_container, text="New Superset Post", 
                                 font=('Segoe UI', 13, 'bold'), bg='#4f46e5', fg='#ffffff')
            title_label.pack(anchor='w')
            
            subtitle_label = tk.Label(title_container, text="Just now", 
                                    font=('Segoe UI', 9), bg='#4f46e5', fg='#e0e7ff')
            subtitle_label.pack(anchor='w')
            
            # Modern close button
            close_btn = tk.Button(header_content, text="✕", font=('Segoe UI', 12, 'bold'),
                                bg='#ef4444', fg='white', relief='flat', width=3, height=1,
                                command=lambda: self.close_toast_with_animation(toast),
                                cursor='hand2', bd=0)
            close_btn.pack(side='right')
            
            # Add hover effect to close button
            def on_close_hover(e):
                close_btn.config(bg='#dc2626')
            def on_close_leave(e):
                close_btn.config(bg='#ef4444')
            
            close_btn.bind('<Enter>', on_close_hover)
            close_btn.bind('<Leave>', on_close_leave)
            
            # Modern content area with card-like styling
            content_frame = tk.Frame(main_frame, bg='#ffffff')
            content_frame.pack(fill='both', expand=True, padx=0, pady=0)
            
            # Post title card
            title_card = tk.Frame(content_frame, bg='#f8fafc')
            title_card.pack(fill='x', padx=15, pady=(15, 2))
            
            # Title with modern styling
            title_text = tk.Text(title_card, height=2, wrap='word', 
                               font=('Segoe UI', 12, 'bold'), bg='#f8fafc', 
                               relief='flat', cursor='arrow', bd=0,
                               selectbackground='#4f46e5', selectforeground='white')
            title_text.pack(fill='x', padx=12, pady=4)
            title_text.insert('1.0', post['title'])
            title_text.config(state='disabled')
            
            # Modern metadata section
            meta_card = tk.Frame(content_frame, bg='#ffffff')
            meta_card.pack(fill='x', padx=15, pady=(0, 4))
            
            if post.get('author') or post.get('time'):
                meta_container = tk.Frame(meta_card, bg='#f1f5f9')
                meta_container.pack(fill='x', padx=0, pady=0)
                
                meta_content = tk.Frame(meta_container, bg='#f1f5f9')
                meta_content.pack(fill='x', padx=12, pady=8)
                
                if post.get('author'):
                    author_frame = tk.Frame(meta_content, bg='#f1f5f9')
                    author_frame.pack(fill='x', pady=(0, 2))
                    
                    author_icon = tk.Label(author_frame, text="👤", font=('Segoe UI Emoji', 10), 
                                         bg='#f1f5f9', fg='#64748b')
                    author_icon.pack(side='left')
                    
                    author_label = tk.Label(author_frame, text=post['author'], 
                                          font=('Segoe UI', 10, 'bold'), bg='#f1f5f9', fg='#334155')
                    author_label.pack(side='left', padx=(6, 0))
                
                if post.get('time'):
                    time_frame = tk.Frame(meta_content, bg='#f1f5f9')
                    time_frame.pack(fill='x')
                    
                    time_icon = tk.Label(time_frame, text="⏰", font=('Segoe UI Emoji', 10), 
                                       bg='#f1f5f9', fg='#64748b')
                    time_icon.pack(side='left')
                    
                    time_label = tk.Label(time_frame, text=post['time'], 
                                        font=('Segoe UI', 10), bg='#f1f5f9', fg='#64748b')
                    time_label.pack(side='left', padx=(6, 0))
            
            # Modern post details section
            details_container = tk.Frame(content_frame, bg='#ffffff')
            details_container.pack(fill='both', expand=True, padx=15, pady=(0, 10))
            
            # Details card with modern styling
            details_card = tk.Frame(details_container, bg='#ffffff', relief='solid', bd=1)
            details_card.configure(highlightbackground='#e2e8f0', highlightthickness=1)
            details_card.pack(fill='both', expand=True)
            
            # Details text widget with modern scrollbar
            text_frame = tk.Frame(details_card, bg='#ffffff')
            text_frame.pack(fill='both', expand=True, padx=1, pady=1)
            
            details_text = tk.Text(text_frame, wrap='word', font=('Segoe UI', 10), 
                                 bg='#ffffff', relief='flat', cursor='arrow',
                                 height=4, bd=0, padx=12, pady=10,
                                 selectbackground='#4f46e5', selectforeground='white')
            
            # Modern scrollbar styling
            text_scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=details_text.yview,
                                        bg='#f1f5f9', troughcolor='#f8fafc', 
                                        activebackground='#cbd5e1', width=12)
            details_text.configure(yscrollcommand=text_scrollbar.set)
            
            details_text.pack(side="left", fill="both", expand=True)
            text_scrollbar.pack(side="right", fill="y")
            
            # Show post details with read more functionality
            post_details = post.get('details', '')
            has_details = bool(post_details and len(post_details.strip()) > 0)
            
            def update_details_display():
                details_text.config(state='normal')
                details_text.delete('1.0', 'end')
                
                if has_details:
                    if is_details_expanded.get():
                        # Show full details
                        content = post_details
                        
                        # Add link count information if links are available
                        if post.get('links'):
                            link_count = len(post['links'])
                            link_info = f"\n\n🔗 {link_count} link(s) available in this post"
                            content += link_info
                        
                        details_text.insert('1.0', content)
                        details_text.config(height=8)  # Expand height
                        read_more_btn.config(text="📖 Show Less")
                        
                        # Expand window height - ensure buttons remain visible
                        toast.geometry(f"{window_width}x{expanded_height}+{x}+{y}")
                    else:
                        # Show preview (first 150 characters)
                        if len(post_details) > 150:
                            preview = post_details[:150] + "..."
                            details_text.insert('1.0', preview)
                            read_more_btn.config(text="📖 Read More")
                        else:
                            details_text.insert('1.0', post_details)
                            read_more_btn.config(text="📖 Full Text")
                        
                        details_text.config(height=4)  # Compact height
                        toast.geometry(f"{window_width}x{window_height}+{x}+{y}")
                else:
                    details_text.insert('1.0', "No additional details available for this post.")
                    read_more_btn.config(state='disabled')
                
                details_text.config(state='disabled')
                
                # Force window to update and ensure buttons are visible
                toast.update_idletasks()
            
            def toggle_details():
                is_details_expanded.set(not is_details_expanded.get())
                update_details_display()
            
            # Modern Read More button
            read_more_btn = tk.Button(details_container, text="📖 Read More", 
                                    command=toggle_details, bg='#6366f1', fg='white', 
                                    font=('Segoe UI', 9, 'bold'), relief='flat', 
                                    padx=12, pady=6, cursor='hand2', bd=0)
            read_more_btn.pack(side='bottom', anchor='e', pady=(8, 0))
            
            # Add hover effect to read more button
            def on_read_more_hover(e):
                read_more_btn.config(bg='#4f46e5')
            def on_read_more_leave(e):
                read_more_btn.config(bg='#6366f1')
            
            read_more_btn.bind('<Enter>', on_read_more_hover)
            read_more_btn.bind('<Leave>', on_read_more_leave)
            
            # Initialize details display
            update_details_display()
            
            # Modern control section with clean separation
            control_frame = tk.Frame(main_frame, bg='#f8fafc')
            control_frame.pack(side='bottom', fill='x')
            
            # Subtle separator line
            separator = tk.Frame(control_frame, bg='#e2e8f0', height=1)
            separator.pack(fill='x')
            
            # Auto-close section with modern styling
            auto_close_frame = tk.Frame(control_frame, bg='#f8fafc')
            auto_close_frame.pack(fill='x', padx=15, pady=(10, 8))
            
            auto_close_check = tk.Checkbutton(auto_close_frame, 
                                            text="⏰ Auto-close in 30 seconds", 
                                            variable=auto_close_enabled,
                                            bg='#f8fafc', font=('Segoe UI', 9),
                                            fg='#64748b', activebackground='#f8fafc',
                                            selectcolor='#ffffff', relief='flat')
            auto_close_check.pack(side='left')
            
            timer_label = tk.Label(auto_close_frame, text="", 
                                 font=('Segoe UI', 9, 'bold'), bg='#f8fafc', fg='#ef4444')
            timer_label.pack(side='right')
            
            # Modern button functions with better feedback
            def mark_as_read():
                self.log_message(f"✅ Marked as read: {post['title'][:30]}...")
                # Animate button feedback
                read_btn.config(text="✓ Marked!", bg='#059669', state='disabled')
                # Pulse effect
                def pulse_effect(count=0):
                    if count < 3:
                        bg_color = '#10b981' if count % 2 == 0 else '#059669'
                        read_btn.config(bg=bg_color)
                        toast.after(150, lambda: pulse_effect(count + 1))
                    else:
                        toast.after(1000, lambda: self.close_toast_with_animation(toast))
                pulse_effect()
            
            def open_link():
                self.log_message(f"🔗 Opening link for: {post['title'][:30]}...")
                webbrowser.open(self.dashboard_url)
                # Animate button feedback
                link_btn.config(text="🔗 Opened!", bg='#2563eb', state='disabled')
                # Pulse effect
                def pulse_effect(count=0):
                    if count < 3:
                        bg_color = '#3b82f6' if count % 2 == 0 else '#2563eb'
                        link_btn.config(bg=bg_color)
                        toast.after(150, lambda: pulse_effect(count + 1))
                    else:
                        toast.after(1000, lambda: self.close_toast_with_animation(toast))
                pulse_effect()
            
            # Modern action buttons with better spacing
            buttons_container = tk.Frame(control_frame, bg='#f8fafc')
            buttons_container.pack(fill='x', padx=15, pady=(0, 15))
            
            # Mark as Read button with modern styling
            read_btn = tk.Button(buttons_container, text="✓ Mark as Read", 
                               command=mark_as_read, bg='#10b981', fg='white', 
                               font=('Segoe UI', 10, 'bold'), relief='flat', 
                               padx=18, pady=8, cursor='hand2', bd=0)
            read_btn.pack(side='left', padx=(0, 8))
            
            # Open Link button with modern styling
            link_btn = tk.Button(buttons_container, text="🔗 Open Link", 
                               command=open_link, bg='#3b82f6', fg='white', 
                               font=('Segoe UI', 10, 'bold'), relief='flat', 
                               padx=18, pady=8, cursor='hand2', bd=0)
            link_btn.pack(side='left', padx=4)
            
            # Apply Now button with modern styling
            def apply_now():
                try:
                    webbrowser.open('https://app.joinsuperset.com/students/jobprofiles')
                    self.log_message("🚀 Opened job profiles page")
                except Exception as e:
                    self.log_message(f"❌ Error opening job profiles: {e}")
            
            apply_btn = tk.Button(buttons_container, text="🚀 Apply It", 
                                command=apply_now, bg='#f59e0b', fg='white', 
                                font=('Segoe UI', 10, 'bold'), relief='flat', 
                                padx=18, pady=8, cursor='hand2', bd=0)
            apply_btn.pack(side='left', padx=(8, 0))
            
            # Auto-close functionality - now global for all notifications
            def on_auto_close_toggle():
                if auto_close_enabled.get():
                    self.start_global_auto_close()
                else:
                    self.stop_global_auto_close()
            
            auto_close_check.config(command=on_auto_close_toggle)
            
            # Update timer display for this notification
            def update_local_timer_display():
                if hasattr(self, 'global_remaining_time') and self.global_remaining_time > 0:
                    timer_label.config(text=f"({self.global_remaining_time}s)")
                else:
                    timer_label.config(text="")
                # Schedule next update
                toast.after(1000, update_local_timer_display)
            
            # Start the local timer display
            update_local_timer_display()
            
            # Add hover effects to buttons
            def on_button_enter(btn, color):
                btn.config(bg=color)
            
            def on_button_leave(btn, original_color):
                btn.config(bg=original_color)
            
            # Modern button hover effects
            def on_read_btn_hover(e):
                read_btn.config(bg='#059669')
            def on_read_btn_leave(e):
                read_btn.config(bg='#10b981')
            
            def on_link_btn_hover(e):
                link_btn.config(bg='#2563eb')
            def on_link_btn_leave(e):
                link_btn.config(bg='#3b82f6')
            
            read_btn.bind('<Enter>', on_read_btn_hover)
            read_btn.bind('<Leave>', on_read_btn_leave)
            
            link_btn.bind('<Enter>', on_link_btn_hover)
            link_btn.bind('<Leave>', on_link_btn_leave)
            
            # Modern slide-in animation with easing
            def slide_in():
                start_x = screen_width + 50  # Start further off-screen
                target_x = x
                steps = 25  # More steps for smoother animation
                
                def ease_out_cubic(t):
                    """Cubic ease-out function for smooth animation"""
                    return 1 - pow(1 - t, 3)
                
                def animate_step(step):
                    if step <= steps:
                        # Calculate position with easing
                        progress = step / steps
                        eased_progress = ease_out_cubic(progress)
                        current_x = start_x - (start_x - target_x) * eased_progress
                        
                        # Also animate opacity for fade-in effect
                        try:
                            opacity = 0.3 + (0.68 * eased_progress)  # From 0.3 to 0.98
                            toast.attributes('-alpha', opacity)
                        except:
                            pass
                        
                        toast.geometry(f"{window_width}x{window_height}+{int(current_x)}+{y}")
                        toast.after(15, lambda: animate_step(step + 1))
                    else:
                        # Final position and opacity
                        toast.geometry(f"{window_width}x{window_height}+{target_x}+{y}")
                        try:
                            toast.attributes('-alpha', 0.98)
                        except:
                            pass
                
                animate_step(0)
            
            # Show the window before starting animation
            toast.deiconify()
            
            # Start animation after window is created
            toast.after(50, slide_in)
            
            # Make sure window appears on top
            toast.lift()
            toast.focus_force()
        
        # Run toast in separate thread to avoid blocking
        toast_thread = threading.Thread(target=show_toast, daemon=True)
        toast_thread.start()
    
    def start_global_auto_close(self):
        """Start global auto-close timer for all notifications"""
        self.stop_global_auto_close()  # Stop any existing timer
        self.global_remaining_time = 30
        self.log_message("⏰ Global auto-close enabled - all notifications will close in 30 seconds")
        self.update_global_timer()
    
    def stop_global_auto_close(self):
        """Stop global auto-close timer"""
        if self.global_auto_close_timer:
            self.root.after_cancel(self.global_auto_close_timer)
            self.global_auto_close_timer = None
        if hasattr(self, 'global_remaining_time'):
            self.global_remaining_time = 0
        self.log_message("⏰ Global auto-close disabled")
    
    def update_global_timer(self):
        """Update global auto-close timer"""
        if self.global_remaining_time > 0:
            self.global_remaining_time -= 1
            self.global_auto_close_timer = self.root.after(1000, self.update_global_timer)
        else:
            # Time's up - close all notifications
            self.close_all_notifications()
    
    def close_all_notifications(self):
        """Close all open notifications"""
        notifications_to_close = self.open_notifications.copy()  # Create a copy to avoid modification during iteration
        self.log_message(f"🔄 Closing {len(notifications_to_close)} notification(s)")
        
        for toast in notifications_to_close:
            try:
                if toast.winfo_exists():  # Check if window still exists
                    self.close_toast_with_animation(toast)
            except:
                pass  # Window might already be closed
        
        # Clear the list
        self.open_notifications.clear()
        self.stop_global_auto_close()

    def close_toast_with_animation(self, toast_window):
        """Close toast notification with smooth slide-out animation"""
        try:
            # Get current position
            geometry = toast_window.geometry()
            parts = geometry.split('+')
            if len(parts) >= 3:
                size_part = parts[0]
                current_x = int(parts[1])
                current_y = int(parts[2])
                
                # Animation parameters
                target_x = toast_window.winfo_screenwidth() + 50
                steps = 20
                
                def ease_in_cubic(t):
                    """Cubic ease-in function for smooth exit animation"""
                    return t * t * t
                
                def animate_close(step):
                    if step <= steps:
                        # Calculate position with easing
                        progress = step / steps
                        eased_progress = ease_in_cubic(progress)
                        new_x = current_x + (target_x - current_x) * eased_progress
                        
                        # Also animate opacity for fade-out effect
                        try:
                            opacity = 0.98 * (1 - eased_progress)
                            toast_window.attributes('-alpha', max(0.1, opacity))
                        except:
                            pass
                        
                        toast_window.geometry(f"{size_part}+{int(new_x)}+{current_y}")
                        toast_window.after(12, lambda: animate_close(step + 1))
                    else:
                        # Animation complete, destroy window and remove from tracking
                        if toast_window in self.open_notifications:
                            self.open_notifications.remove(toast_window)
                        toast_window.destroy()
                
                animate_close(0)
            else:
                # Fallback: destroy immediately if geometry parsing fails
                if toast_window in self.open_notifications:
                    self.open_notifications.remove(toast_window)
                toast_window.destroy()
                
        except Exception as e:
            # Fallback: destroy immediately on any error
            if toast_window in self.open_notifications:
                self.open_notifications.remove(toast_window)
            toast_window.destroy()
    
    def save_posts_to_log(self, new_posts):
        """Save new posts to detailed log file"""
        try:
            log_content = f"\n{'='*80}\n"
            log_content += f"NEW POSTS FOUND: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            log_content += f"{'='*80}\n"
            
            for i, post in enumerate(new_posts, 1):
                log_content += f"\n{i}. {post['title']}\n"
                if post.get('author'):
                    log_content += f"   Author: {post['author']}\n"
                if post.get('time'):
                    log_content += f"   Posted: {post['time']}\n"
                if post.get('details'):
                    log_content += f"   Details: {post['details']}\n"
                if post.get('links'):
                    log_content += f"   Links ({len(post['links'])}):\n"
                    for j, link in enumerate(post['links'], 1):
                        log_content += f"      {j}. {link.get('text', 'Link')}: {link.get('url', '')}\n"
                log_content += f"   Found at: {post['found_at']}\n"
                log_content += "-" * 60 + "\n"
            
            # Read existing content
            existing_content = ""
            if os.path.exists('new_posts_detailed.log'):
                with open('new_posts_detailed.log', 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            
            # Write new content at top
            with open('new_posts_detailed.log', 'w', encoding='utf-8') as f:
                f.write(log_content)
                if existing_content:
                    f.write(existing_content)
                    
        except Exception as e:
            self.log_message(f"⚠️ Error saving detailed log: {e}")
    
    def load_known_posts(self, verbose=True):
        """Load known posts from file with enhanced error handling"""
        try:
            if os.path.exists(self.known_posts_file):
                with open(self.known_posts_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    
                    if isinstance(loaded_data, dict):
                        self.known_posts = loaded_data
                        if verbose:
                            self.log_message(f"📁 Loaded {len(self.known_posts)} known posts from file")
                    else:
                        # Handle old format or corrupted data
                        if verbose:
                            self.log_message("⚠️ Invalid format in known_posts.json, resetting...")
                        self.known_posts = {}
            else:
                self.known_posts = {}
                if verbose:
                    self.log_message("📁 No existing known_posts.json file found, starting fresh")
                
        except json.JSONDecodeError as e:
            if verbose:
                self.log_message(f"❌ JSON decode error in known_posts.json: {e}")
                self.log_message("🔄 Creating backup and starting fresh...")
            
            # Create backup of corrupted file
            try:
                import shutil
                backup_name = f"known_posts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                shutil.copy2(self.known_posts_file, backup_name)
                if verbose:
                    self.log_message(f"💾 Corrupted file backed up as: {backup_name}")
            except:
                pass
            
            self.known_posts = {}
            
        except Exception as e:
            if verbose:
                self.log_message(f"❌ Error loading known posts: {e}")
            else:
                print(f"Error loading known posts: {e}")
            self.known_posts = {}
    
    def save_known_posts(self):
        """Save known posts to file with newest posts at the top"""
        try:
            # Sort posts by found_at timestamp (newest first)
            sorted_posts = dict(sorted(
                self.known_posts.items(),
                key=lambda x: x[1].get('found_at', ''),
                reverse=True  # Newest first
            ))
            
            with open(self.known_posts_file, 'w', encoding='utf-8') as f:
                json.dump(sorted_posts, f, indent=2, ensure_ascii=False)
            self.log_message(f"💾 Saved {len(self.known_posts)} known posts to file (newest first)")
        except Exception as e:
            self.log_message(f"⚠️ Error saving known posts: {e}")
    
    def refresh_posts_display(self):
        """Refresh the posts display"""
        self.posts_text.delete(1.0, tk.END)
        
        if not self.known_posts:
            self.posts_text.insert(tk.END, "No posts found yet. Start monitoring to discover posts!")
            return
        
        content = f"Total Known Posts: {len(self.known_posts)}\n"
        content += "=" * 60 + "\n\n"
        
        # Sort posts by found_at timestamp (newest first)
        sorted_posts = sorted(
            self.known_posts.items(),
            key=lambda x: x[1].get('found_at', ''),
            reverse=True
        )
        
        for i, (title, data) in enumerate(sorted_posts, 1):
            content += f"{i}. {title}\n"
            if data.get('author'):
                content += f"   👤 Author: {data['author']}\n"
            if data.get('time'):
                content += f"   ⏰ Posted: {data['time']}\n"
            if data.get('details'):
                details_preview = data['details'][:200] + "..." if len(data['details']) > 200 else data['details']
                content += f"   📄 Details: {details_preview}\n"
            if data.get('links'):
                content += f"   🔗 Links: {len(data['links'])} found\n"
                for j, link in enumerate(data['links'][:3], 1):  # Show first 3 links
                    content += f"      {j}. {link.get('text', 'Link')}: {link.get('url', '')}\n"
                if len(data['links']) > 3:
                    content += f"      ... and {len(data['links']) - 3} more links\n"
            if data.get('found_at'):
                found_time = datetime.fromisoformat(data['found_at']).strftime('%Y-%m-%d %H:%M:%S')
                content += f"   🔍 Discovered: {found_time}\n"
            content += "\n" + "-" * 60 + "\n\n"
        
        self.posts_text.insert(tk.END, content)
    
    def reload_posts_from_file(self):
        """Reload known posts from file (useful after manual edits)"""
        old_count = len(self.known_posts)
        self.load_known_posts(verbose=True)
        new_count = len(self.known_posts)
        
        self.refresh_posts_display()
        self.posts_count_label.config(text=f"{new_count} posts")
        self.file_modified_label.config(text=self.get_file_modified_time())
        
        if new_count != old_count:
            self.log_message(f"📁 Reloaded from file: {old_count} → {new_count} posts")
            messagebox.showinfo("Reload Complete", f"Posts reloaded from file.\nBefore: {old_count} posts\nAfter: {new_count} posts")
        else:
            self.log_message(f"📁 Reloaded from file: {new_count} posts (no change)")
            messagebox.showinfo("Reload Complete", f"Posts reloaded from file.\nTotal: {new_count} posts")
    
    def clear_all_posts(self):
        """Clear all known posts"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all known posts?\nThis will make all posts appear as 'new' on the next check."):
            self.known_posts = {}
            self.save_known_posts()
            self.refresh_posts_display()
            self.posts_count_label.config(text="0 posts")
            self.log_message("🗑️ All known posts cleared")
    
    def save_settings(self):
        """Save current settings"""
        try:
            # Update check interval
            new_interval = int(self.interval_var.get()) * 60
            if new_interval < 60:
                messagebox.showwarning("Warning", "Check interval must be at least 1 minute")
                return
            
            self.check_interval = new_interval
            self.log_message(f"⚙️ Settings saved - Check interval: {new_interval // 60} minutes")
            self.log_message(f"⚙️ Notification type: {self.notification_type_var.get()}")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for check interval")
    
    def test_notification(self):
        """Test the selected notification type"""
        self.log_message("🔔 Testing notification...")
        
        # Create a sample post for testing
        test_post = {
            'title': 'Test Notification - Superset Post Monitor',
            'author': 'System Test',
            'time': 'Just now',
            'details': 'This is a test notification to verify that your notification system is working correctly. The post details feature allows you to see the full content of each post, including any links or formatted text that may be included. Click "Read More" to see the full details, and use the action buttons to interact with the notification.',
            'links': [
                {'text': 'Test Link 1', 'url': 'https://example.com/test1'},
                {'text': 'Test Link 2', 'url': 'https://example.com/test2'}
            ],
            'found_at': datetime.now().isoformat()
        }
        
        # Send test notification
        self.send_notifications([test_post])
    
    def open_log_file(self):
        """Open the log file"""
        try:
            if os.path.exists(self.log_file):
                os.startfile(self.log_file)  # Windows
            else:
                messagebox.showinfo("Info", "Log file doesn't exist yet")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open log file: {e}")
    
    def open_posts_file(self):
        """Open the posts file"""
        try:
            if os.path.exists(self.known_posts_file):
                os.startfile(self.known_posts_file)  # Windows
            else:
                messagebox.showinfo("Info", "Posts file doesn't exist yet")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open posts file: {e}")
    
    def run(self):
        """Start the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def get_file_modified_time(self):
        """Get the last modified time of the known_posts.json file"""
        try:
            if os.path.exists(self.known_posts_file):
                mod_time = os.path.getmtime(self.known_posts_file)
                return datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            else:
                return "File not found"
        except Exception as e:
            return f"Error: {e}"
    
    def setup_app_icon(self):
        """Setup application icon for taskbar and window"""
        try:
            # Get the application directory and icon path
            app_dir = self.get_application_directory()
            icon_path = os.path.join(app_dir, 'notification-bell.png')
            
            # Try to set the icon if the file exists
            if os.path.exists(icon_path):
                # For Windows, convert PNG to ICO format in memory
                try:
                    from PIL import Image
                    import io
                    
                    # Load and convert PNG to ICO format
                    img = Image.open(icon_path)
                    # Resize to standard icon sizes
                    icon_sizes = [(16, 16), (32, 32), (48, 48)]
                    
                    # Create ICO file in memory
                    ico_buffer = io.BytesIO()
                    img.save(ico_buffer, format='ICO', sizes=icon_sizes)
                    ico_buffer.seek(0)
                    
                    # Save temporary ICO file in app directory
                    temp_ico_path = os.path.join(app_dir, 'temp_icon.ico')
                    with open(temp_ico_path, 'wb') as f:
                        f.write(ico_buffer.getvalue())
                    
                    # Set the icon
                    self.root.iconbitmap(temp_ico_path)
                    self.log_message("✅ Application icon set successfully")
                    
                except ImportError:
                    # Fallback: try to use PNG directly (may not work on all systems)
                    try:
                        icon_photo = tk.PhotoImage(file=icon_path)
                        self.root.iconphoto(True, icon_photo)
                        self.log_message("✅ Application icon set (PNG fallback)")
                    except:
                        self.log_message("⚠️ Could not set PNG icon - install Pillow for better icon support")
                except Exception as e:
                    self.log_message(f"⚠️ Icon setup error: {e}")
            else:
                self.log_message("⚠️ notification-bell.png not found - using default icon")
                
        except Exception as e:
            self.log_message(f"⚠️ Error setting up application icon: {e}")
    
    def setup_system_tray(self):
        """Setup system tray functionality"""
        try:
            # Check if system tray is available
            if not SYSTEM_TRAY_AVAILABLE:
                self.log_message("⚠️ System tray not available - install pystray and Pillow for tray functionality")
                self.tray_icon = None
                return
            
            # Try to import pystray for system tray
            import pystray
            from PIL import Image
            
            # Load the icon image
            app_dir = self.get_application_directory()
            icon_path = os.path.join(app_dir, 'notification-bell.png')
            
            if os.path.exists(icon_path):
                try:
                    icon_image = Image.open(icon_path)
                    self.log_message("✅ Loaded notification-bell.png for system tray")
                except Exception as e:
                    self.log_message(f"⚠️ Error loading icon file: {e}")
                    # Create a simple default icon if file loading fails
                    icon_image = Image.new('RGB', (64, 64), color=(52, 152, 219))  # Blue color
            else:
                self.log_message("⚠️ notification-bell.png not found, creating default icon")
                # Create a simple default icon if file doesn't exist
                icon_image = Image.new('RGB', (64, 64), color=(52, 152, 219))  # Blue color
            
            # Create system tray menu with dynamic visibility
            menu_items = [
                pystray.MenuItem("Show Window", self.show_window, 
                               visible=lambda item: not self.is_window_visible()),
                pystray.MenuItem("Hide Window", self.hide_window, 
                               visible=lambda item: self.is_window_visible()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Start Monitoring", self.tray_start_monitoring, 
                               visible=lambda item: not self.monitoring_active),
                pystray.MenuItem("Stop Monitoring", self.tray_stop_monitoring, 
                               visible=lambda item: self.monitoring_active),
                pystray.MenuItem("Check Now", self.tray_check_now),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Auto Start", self.toggle_auto_start, 
                               checked=lambda item: self.is_auto_start_enabled()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Developer", pystray.Menu(
                    pystray.MenuItem("Open Log File", self.open_log_file),
                    pystray.MenuItem("Open Posts File", self.open_posts_file),
                    pystray.MenuItem("Open Data Folder", self.open_data_folder),
                    pystray.MenuItem("GitHub Repository", self.open_github)
                )),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", self.quit_application)
            ]
            
            # Create system tray icon with double-click handler
            self.tray_icon = pystray.Icon(
                "SupersetMonitor",
                icon_image,
                self.get_tray_tooltip(),
                menu=pystray.Menu(*menu_items)
            )
            
            # Set default action for double-click
            self.tray_icon.default_action = self.toggle_window_visibility
            
            # Start system tray in separate thread
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
            
            self.log_message("✅ System tray icon created successfully")
            
            # Add minimize to tray button to GUI now that tray is available
            self.add_tray_button()
            
        except ImportError as e:
            self.log_message(f"⚠️ System tray import error: {e}")
            self.tray_icon = None
        except Exception as e:
            self.log_message(f"⚠️ System tray setup error: {e}")
            self.tray_icon = None
    
    def add_tray_button(self):
        """Add the minimize to tray button to the modern GUI"""
        try:
            if hasattr(self, 'tray_btn_placeholder') and self.tray_icon:
                tray_btn = tk.Button(self.tray_btn_placeholder, text="📱 Minimize to Tray", 
                                   command=self.hide_window,
                                   bg='#9b59b6', fg='white', font=('Segoe UI', 11, 'bold'),
                                   relief='flat', bd=0, padx=30, pady=12,
                                   cursor='hand2', width=14)
                tray_btn.pack(side='left', padx=(0, 15))
                
                # Add hover effects
                self.add_button_hover_effects(tray_btn, '#9b59b6', '#af7ac5')
                
                self.log_message("✅ Added minimize to tray button")
        except Exception as e:
            self.log_message(f"⚠️ Error adding tray button: {e}")
    
    def setup_window_events(self):
        """Setup window event handlers to track visibility"""
        try:
            # Bind to window state change events
            self.root.bind('<Map>', self.on_window_map)
            self.root.bind('<Unmap>', self.on_window_unmap)
            self.root.bind('<FocusIn>', self.on_window_focus_in)
            
        except Exception as e:
            self.log_message(f"⚠️ Error setting up window events: {e}")
    
    def on_window_map(self, event=None):
        """Handle window map event (window becomes visible)"""
        if event and event.widget == self.root:
            self.window_visible = True
            self.update_tray_menu()
    
    def on_window_unmap(self, event=None):
        """Handle window unmap event (window becomes hidden)"""
        if event and event.widget == self.root:
            self.window_visible = False
            self.update_tray_menu()
    
    def on_window_focus_in(self, event=None):
        """Handle window focus in event"""
        if event and event.widget == self.root:
            self.window_visible = True
            self.update_tray_menu()
    
    def update_tray_menu(self):
        """Update the system tray menu"""
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon:
                # Small delay to ensure state is properly updated
                self.root.after(100, lambda: self.tray_icon.update_menu() if self.tray_icon else None)
        except Exception as e:
            # Silently handle menu update errors
            pass
    
    def toggle_window_visibility(self, icon=None, item=None):
        """Toggle window visibility (for double-click on tray icon)"""
        try:
            if self.is_window_visible():
                self.hide_window()
            else:
                self.show_window()
        except Exception as e:
            self.log_message(f"⚠️ Error toggling window visibility: {e}")
    
    def check_auto_start_mode(self):
        """Check if the application was launched from auto-start"""
        try:
            # Check command line arguments
            import sys
            return '--auto-start' in sys.argv
        except:
            return False
    
    def handle_auto_start_mode(self):
        """Handle auto-start mode - hide window and start monitoring"""
        try:
            self.log_message("🚀 Auto-start mode detected")
            
            # Hide the window after a short delay to ensure GUI is ready
            self.root.after(1000, self.auto_start_sequence)
            
        except Exception as e:
            self.log_message(f"⚠️ Error handling auto-start mode: {e}")
    
    def auto_start_sequence(self):
        """Execute the auto-start sequence"""
        try:
            # Hide the window first
            if self.tray_icon:
                self.hide_window()
                self.log_message("📱 Window hidden for auto-start")
            else:
                self.root.iconify()  # Minimize if no tray
                self.log_message("📱 Window minimized for auto-start")
            
            # Check if we have saved credentials
            username = ""
            password = ""
            
            # Try to get credentials from GUI fields
            if hasattr(self, 'username_entry') and hasattr(self, 'password_entry'):
                username = self.get_username()
                password = self.get_password()
            
            # If no credentials in GUI, try to load from file
            if not username or not password:
                try:
                    if os.path.exists(self.credentials_file):
                        with open(self.credentials_file, 'r', encoding='utf-8') as f:
                            creds = json.load(f)
                            username = creds.get('username', '')
                            password = creds.get('password', '')
                            
                            # Update GUI fields with loaded credentials
                            if username and hasattr(self, 'username_entry'):
                                self.username_entry.delete(0, tk.END)
                                self.username_entry.insert(0, username)
                            if password and hasattr(self, 'password_entry'):
                                self.password_entry.delete(0, tk.END)
                                self.password_entry.insert(0, password)
                                
                except Exception as e:
                    self.log_message(f"⚠️ Error loading credentials for auto-start: {e}")
            
            # Start monitoring if we have credentials
            if username and password:
                self.log_message("🚀 Starting monitoring automatically...")
                
                # Start monitoring
                self.monitoring_active = True
                
                # Update GUI
                self.update_monitoring_button()
                
                if hasattr(self, 'monitor_status_label'):
                    self.monitor_status_label.config(text="▶️ Running", fg='green')
                
                # Update tray menu
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.update_menu()
                
                # Start monitoring in separate thread
                self.monitor_thread = threading.Thread(target=self.monitor_loop, args=(username, password), daemon=True)
                self.monitor_thread.start()
                
                self.log_message("✅ Auto-start monitoring initiated successfully")
                
                # Show tray notification
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.notify(
                        "Superset Monitor Started",
                        "Monitoring started automatically from system startup"
                    )
            else:
                self.log_message("⚠️ Auto-start failed: No credentials available")
                self.log_message("💡 Please configure credentials and save them for auto-start to work")
                
                # Show tray notification about missing credentials
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.notify(
                        "Credentials Required",
                        "Please configure login credentials for auto-start monitoring"
                    )
                
        except Exception as e:
            self.log_message(f"❌ Auto-start sequence failed: {e}")
    
    def get_tray_tooltip(self):
        """Get the tooltip text for the system tray icon"""
        try:
            status = "Running" if getattr(self, 'monitoring_active', False) else "Stopped"
            posts_count = len(getattr(self, 'known_posts', {}))
            window_state = "Visible" if self.is_window_visible() else "Hidden"
            return f"Superset Post Monitor\nStatus: {status}\nWindow: {window_state}\nKnown Posts: {posts_count}"
        except Exception as e:
            return "Superset Post Monitor"
    
    def update_tray_tooltip(self):
        """Update the system tray tooltip"""
        try:
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.title = self.get_tray_tooltip()
        except Exception as e:
            # Silently handle tooltip update errors
            pass
    
    def is_window_visible(self):
        """Check if the main window is currently visible"""
        try:
            # Check if window is withdrawn (hidden) or iconified (minimized)
            state = self.root.state()
            return state == 'normal'
        except:
            return self.window_visible  # Fallback to tracked state
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.window_visible = True
            
            # Update tray menu to reflect new state
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.update_menu()
            
            self.log_message("🪟 Window shown")
        except Exception as e:
            self.log_message(f"⚠️ Error showing window: {e}")
    
    def hide_window(self, icon=None, item=None):
        """Hide the main window to system tray"""
        try:
            if self.tray_icon:
                self.root.withdraw()
                self.window_visible = False
                self.log_message("📱 Application minimized to system tray")
            else:
                self.root.iconify()  # Regular minimize if no tray
                self.window_visible = False
                self.log_message("📱 Application minimized")
            
            # Update tray menu to reflect new state
            if hasattr(self, 'tray_icon') and self.tray_icon:
                self.tray_icon.update_menu()
                
        except Exception as e:
            self.log_message(f"⚠️ Error hiding window: {e}")
    
    def toggle_auto_start(self, icon=None, item=None):
        """Toggle auto-start functionality"""
        try:
            if self.is_auto_start_enabled():
                self.disable_auto_start()
                self.log_message("🔄 Auto-start disabled")
            else:
                self.enable_auto_start()
                self.log_message("🔄 Auto-start enabled")
        except Exception as e:
            self.log_message(f"⚠️ Auto-start toggle error: {e}")
    
    def is_auto_start_enabled(self):
        """Check if auto-start is enabled"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_READ)
            try:
                winreg.QueryValueEx(key, "SupersetPostMonitor")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except:
            return False
    
    def enable_auto_start(self):
        """Enable auto-start on Windows startup"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_SET_VALUE)
            
            # Get the application directory (handles both Python script and compiled EXE)
            current_dir = self.get_application_directory()
            
            # Priority order: EXE file > startup batch file > regular batch file > Python script
            exe_file = os.path.join(current_dir, "superset_gui_monitor.exe")
            startup_batch = os.path.join(current_dir, "startup_monitor.bat")
            regular_batch = os.path.join(current_dir, "run_monitor.bat")
            
            if os.path.exists(exe_file):
                # Use the compiled EXE file (best option for compiled version)
                command = f'"{exe_file}" --auto-start'
                self.log_message("✅ Auto-start will use superset_gui_monitor.exe (compiled version)")
            elif os.path.exists(startup_batch):
                # Use the dedicated startup batch file
                command = f'"{startup_batch}"'
                self.log_message("✅ Auto-start will use startup_monitor.bat (optimized)")
            elif os.path.exists(regular_batch):
                # Use the regular batch file with auto-start flag
                command = f'"{regular_batch}" --auto-start'
                self.log_message("✅ Auto-start will use run_monitor.bat")
            else:
                # Fallback to Python script directly
                script_path = os.path.abspath(__file__)
                python_path = sys.executable
                command = f'"{python_path}" "{script_path}" --auto-start'
                self.log_message("✅ Auto-start will use Python script directly")
            
            winreg.SetValueEx(key, "SupersetPostMonitor", 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)
            
        except Exception as e:
            raise Exception(f"Failed to enable auto-start: {e}")
    
    def disable_auto_start(self):
        """Disable auto-start on Windows startup"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_SET_VALUE)
            
            winreg.DeleteValue(key, "SupersetPostMonitor")
            winreg.CloseKey(key)
            
        except Exception as e:
            raise Exception(f"Failed to disable auto-start: {e}")
    
    def get_autostart_command_preview(self):
        """Get a preview of what command will be used for auto-start"""
        try:
            current_dir = self.get_application_directory()
            startup_batch = os.path.join(current_dir, "startup_monitor.bat")
            regular_batch = os.path.join(current_dir, "run_monitor.bat")
            
            if os.path.exists(startup_batch):
                return "startup_monitor.bat (optimized for startup)"
            elif os.path.exists(regular_batch):
                return "run_monitor.bat --auto-start"
            else:
                return "python superset_gui_monitor.py (direct)"
        except:
            return "Unable to determine"
    
    def open_data_folder(self, icon=None, item=None):
        """Open the data folder in file explorer"""
        try:
            current_dir = self.get_application_directory()
            subprocess.run(['explorer', current_dir], check=True)
        except Exception as e:
            self.log_message(f"⚠️ Error opening data folder: {e}")
    
    def open_github(self, icon=None, item=None):
        """Open GitHub repository (placeholder)"""
        try:
            # Replace with actual GitHub URL when available
            webbrowser.open("https://github.com/bibekchandsah/")
        except Exception as e:
            self.log_message(f"⚠️ Error opening GitHub: {e}")
    
    def tray_start_monitoring(self, icon=None, item=None):
        """Start monitoring from system tray"""
        try:
            # Check if credentials are available
            username = ""
            password = ""
            
            # Try to get credentials from GUI fields if available
            if hasattr(self, 'username_entry') and hasattr(self, 'password_entry'):
                username = self.get_username()
                password = self.get_password()
            
            # If no credentials in GUI, try to load from file
            if not username or not password:
                try:
                    if os.path.exists(self.credentials_file):
                        with open(self.credentials_file, 'r', encoding='utf-8') as f:
                            creds = json.load(f)
                            username = creds.get('username', '')
                            password = creds.get('password', '')
                except:
                    pass
            
            if not username or not password:
                self.log_message("❌ Cannot start monitoring: No credentials available")
                # Show the main window so user can enter credentials
                self.show_window()
                return
            
            # Start monitoring
            if not self.monitoring_active:
                self.monitoring_active = True
                
                # Update GUI
                self.update_monitoring_button()
                
                if hasattr(self, 'monitor_status_label'):
                    self.monitor_status_label.config(text="▶️ Running", fg='green')
                
                self.log_message("🚀 Starting post monitoring from system tray...")
                
                # Start monitoring in separate thread
                self.monitor_thread = threading.Thread(target=self.monitor_loop, args=(username, password), daemon=True)
                self.monitor_thread.start()
                
                # Update tray menu
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.update_menu()
            else:
                self.log_message("⚠️ Monitoring is already active")
                
        except Exception as e:
            self.log_message(f"❌ Error starting monitoring from tray: {e}")
    
    def tray_stop_monitoring(self, icon=None, item=None):
        """Stop monitoring from system tray"""
        try:
            if self.monitoring_active:
                self.stop_monitoring()
                
                # Update tray menu
                if hasattr(self, 'tray_icon') and self.tray_icon:
                    self.tray_icon.update_menu()
                    
                self.log_message("⏹️ Monitoring stopped from system tray")
            else:
                self.log_message("⚠️ Monitoring is not active")
                
        except Exception as e:
            self.log_message(f"❌ Error stopping monitoring from tray: {e}")
    
    def tray_check_now(self, icon=None, item=None):
        """Perform immediate check from system tray"""
        try:
            # Check if credentials are available
            username = ""
            password = ""
            
            # Try to get credentials from GUI fields if available
            if hasattr(self, 'username_entry') and hasattr(self, 'password_entry'):
                username = self.get_username()
                password = self.get_password()
            
            # If no credentials in GUI, try to load from file
            if not username or not password:
                try:
                    if os.path.exists(self.credentials_file):
                        with open(self.credentials_file, 'r', encoding='utf-8') as f:
                            creds = json.load(f)
                            username = creds.get('username', '')
                            password = creds.get('password', '')
                except:
                    pass
            
            if not username or not password:
                self.log_message("❌ Cannot check now: No credentials available")
                # Show the main window so user can enter credentials
                self.show_window()
                return
            
            self.log_message("🔍 Performing immediate check from system tray...")
            
            # Run check in separate thread
            def tray_check_thread():
                try:
                    driver = self.setup_driver(headless=True)  # Always headless from tray
                    
                    if self.perform_login(driver, username, password):
                        new_posts = self.check_for_posts(driver, force_full_scroll=True)
                        
                        # Update GUI in main thread
                        self.root.after(0, lambda: self.handle_check_results(new_posts))
                        
                        if new_posts:
                            self.log_message(f"🎉 Found {len(new_posts)} new posts from tray check!")
                            # Show tray notification
                            if hasattr(self, 'tray_icon') and self.tray_icon:
                                self.tray_icon.notify(
                                    f"Found {len(new_posts)} new posts!",
                                    "Click to view details"
                                )
                        else:
                            self.log_message("✅ No new posts found from tray check")
                    else:
                        self.log_message("❌ Login failed during tray check")
                    
                    if driver:
                        driver.quit()
                        
                except Exception as e:
                    self.log_message(f"❌ Tray check failed: {e}")
            
            threading.Thread(target=tray_check_thread, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"❌ Error performing tray check: {e}")
    
    def quit_application(self, icon=None, item=None):
        """Quit the application completely"""
        if self.monitoring_active:
            # Stop monitoring first
            self.stop_monitoring()
            time.sleep(1)
        
        # Stop system tray
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop()
        
        # Close main window
        self.root.quit()
        self.root.destroy()
    
    def on_closing(self):
        """Handle window close button - minimize to tray instead of closing"""
        if self.tray_icon:
            # If system tray is available, minimize to tray
            self.hide_window()
        else:
            # If no system tray, ask user what to do
            if self.monitoring_active:
                if messagebox.askyesno("Confirm", "Monitoring is active. Stop monitoring and exit?"):
                    self.stop_monitoring()
                    time.sleep(1)
                    self.root.destroy()
            else:
                self.root.destroy()

if __name__ == "__main__":
    # Check for required packages
    required_packages = ['selenium', 'webdriver-manager']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\nInstall them with:")
        print(f"   pip install {' '.join(missing_packages)}")
        print("\nOptional for notifications:")
        print("   pip install plyer")
        exit(1)
    
    # Start the application
    app = SupersetGUIMonitor()
    app.run()