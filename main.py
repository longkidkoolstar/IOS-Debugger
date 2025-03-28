import os
import sys
import subprocess
import webbrowser
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import platform
import threading
import configparser
import time
import re
from bs4 import BeautifulSoup
import shutil
import tempfile

class IOSSafariDebuggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("iOS Safari Debugger")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Configuration
        self.config_file = os.path.join(os.path.expanduser("~"), ".ios_safari_debugger.ini")
        self.config = configparser.ConfigParser()
        
        # Variables
        self.webkit_path = tk.StringVar()
        self.pages_list = []
        self.page_ids = []  # Store actual page IDs
        self.debugging_process = None
        self.monitoring_thread = None
        self.stop_monitoring = False
        self.repository_url = "https://github.com/google/ios-webkit-debug-proxy"  # Default repository URL
        
        # Load saved configuration
        self.load_config()
        
        # Create UI
        self.create_ui()
        
    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
            if 'Settings' in self.config:
                if 'webkit_path' in self.config['Settings']:
                    self.webkit_path.set(self.config['Settings']['webkit_path'])
                if 'repository_url' in self.config['Settings']:
                    self.repository_url = self.config['Settings']['repository_url']
        else:
            self.config['Settings'] = {}
    
    def save_config(self):
        self.config['Settings']['webkit_path'] = self.webkit_path.get()
        self.config['Settings']['repository_url'] = self.repository_url
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # WebKit Path Section
        path_frame = ttk.LabelFrame(main_frame, text="WebKit Path", padding="10")
        path_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(path_frame, text="Path to WebKit folder:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(path_frame, textvariable=self.webkit_path, width=50).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(path_frame, text="Browse", command=self.browse_webkit_path).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(path_frame, text="Auto Setup", command=self.auto_setup_webkit).grid(row=0, column=3, padx=5, pady=5)
        
        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Not running")
        self.status_label.pack(fill=tk.X)
        
        # Buttons Section
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = ttk.Button(buttons_frame, text="Start Debugging Server", command=self.start_debugging)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="Stop Debugging Server", command=self.stop_debugging, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.refresh_button = ttk.Button(buttons_frame, text="Refresh Pages", command=self.refresh_pages, state=tk.DISABLED)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        # Pages Section
        pages_frame = ttk.LabelFrame(main_frame, text="Inspectable Pages", padding="10")
        pages_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview for pages
        columns = ('page_id', 'title', 'url')
        self.pages_tree = ttk.Treeview(pages_frame, columns=columns, show='headings')
        
        # Define headings
        self.pages_tree.heading('page_id', text='ID')
        self.pages_tree.heading('title', text='Title')
        self.pages_tree.heading('url', text='URL')
        
        # Column widths
        self.pages_tree.column('page_id', width=50)
        self.pages_tree.column('title', width=150)
        self.pages_tree.column('url', width=400)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(pages_frame, orient="vertical", command=self.pages_tree.yview)
        hsb = ttk.Scrollbar(pages_frame, orient="horizontal", command=self.pages_tree.xview)
        self.pages_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout for treeview and scrollbars
        self.pages_tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        
        # Configure grid weights
        pages_frame.grid_columnconfigure(0, weight=1)
        pages_frame.grid_rowconfigure(0, weight=1)
        
        # Open button
        open_button = ttk.Button(pages_frame, text="Open Debugger", command=self.open_debugger)
        open_button.grid(column=0, row=2, sticky='e', padx=5, pady=5)
        
        # Console output
        console_frame = ttk.LabelFrame(main_frame, text="Console Output", padding="10")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.console_text = tk.Text(console_frame, height=8, wrap=tk.WORD)
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        console_scroll = ttk.Scrollbar(console_frame, command=self.console_text.yview)
        console_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.console_text.config(yscrollcommand=console_scroll.set)
        self.console_text.config(state=tk.DISABLED)
        
        # Add event binding for double click on page
        self.pages_tree.bind("<Double-1>", lambda e: self.open_debugger())
    
    def auto_setup_webkit(self):
        """Automatically clone the repository and set up WebKit folder"""
        # Ask the user for a directory to store the WebKit files
        target_dir = filedialog.askdirectory(title="Select Directory for Repository")
        if not target_dir:
            return
        
        # Show progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Setup Progress")
        progress_window.geometry("400x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        progress_label = ttk.Label(progress_window, text="Initializing...")
        progress_label.pack(pady=10)
        
        progress_bar = ttk.Progressbar(progress_window, orient="horizontal", length=300, mode="indeterminate")
        progress_bar.pack(pady=10)
        progress_bar.start()
        
        log_text = tk.Text(progress_window, height=5, width=45)
        log_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        log_text.config(state=tk.DISABLED)
        
        def update_log(message):
            log_text.config(state=tk.NORMAL)
            log_text.insert(tk.END, f"{message}\n")
            log_text.see(tk.END)
            log_text.config(state=tk.DISABLED)
            self.log_message(message)
        
        def setup_thread():
            temp_dir = None
            try:
                update_log("Cloning repository...")
                # Make a temp directory for cloning
                temp_dir = tempfile.mkdtemp()
                
                # Clone the specified repository
                clone_cmd = ["git", "clone", "https://github.com/HimbeersaftLP/ios-safari-remote-debug-kit", temp_dir]
                update_log("Using git to clone repository...")
                process = subprocess.Popen(
                    clone_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        update_log(output.strip())
                
                if process.returncode != 0:
                    raise Exception("Git clone failed")
                
                # After cloning, generate WebKit files
                update_log("Generating WebKit files...")
                
                # Path to the cloned repository's src directory
                cloned_src_dir = os.path.join(temp_dir, "src")
                
                # Determine which script to run
                generate_cmd = None
                if platform.system() == "Windows":
                    generate_script = os.path.join(cloned_src_dir, "generate.ps1")
                    if not os.path.exists(generate_script):
                        raise Exception(f"Generate script not found: {generate_script}")
                    generate_cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", "generate.ps1"]
                else:  # Linux/macOS
                    generate_script = os.path.join(cloned_src_dir, "generate.sh")
                    if not os.path.exists(generate_script):
                        raise Exception(f"Generate script not found: {generate_script}")
                    generate_cmd = ["bash", "generate.sh"]
                
                # Run generate script from the cloned src directory
                process = subprocess.Popen(
                    generate_cmd,
                    cwd=cloned_src_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        update_log(output.strip())
                
                if process.returncode != 0:
                    raise Exception("Generate script failed")
                
                # Create target/src directory
                target_src_dir = os.path.join(target_dir, "src")
                os.makedirs(target_src_dir, exist_ok=True)
                
                # Copy ALL contents from cloned_src_dir to target_src_dir
                update_log("Copying repository files to target/src...")
                for item in os.listdir(cloned_src_dir):
                    src_item = os.path.join(cloned_src_dir, item)
                    dest_item = os.path.join(target_src_dir, item)
                    
                    if os.path.exists(dest_item):
                        if os.path.isdir(dest_item):
                            shutil.rmtree(dest_item)
                        else:
                            os.remove(dest_item)
                    
                    if os.path.isdir(src_item):
                        shutil.copytree(src_item, dest_item)
                    else:
                        shutil.copy2(src_item, dest_item)
                        if item.endswith(".sh"):
                            os.chmod(dest_item, 0o755)
                
                # Set configuration to point to the src directory (not WebKit subfolder)
                self.webkit_path.set(target_src_dir)  # Changed here
                self.save_config()
                update_log("Setup completed successfully! Using src directory as root.")
            
            except Exception as e:
                update_log(f"Error during setup: {str(e)}")
                messagebox.showerror("Setup Error", f"Failed to set up WebKit: {str(e)}")
            finally:
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
                
                self.root.after(0, progress_window.destroy)
        
        setup_thread = threading.Thread(target=setup_thread)
        setup_thread.daemon = True
        setup_thread.start()
    
    def _check_command_exists(self, command):
        """Check if a command exists in the system path"""
        try:
            if platform.system() == "Windows":
                subprocess.check_call(["where", command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                subprocess.check_call(["which", command], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except:
            return False
    
    def browse_webkit_path(self):
        path = filedialog.askdirectory(title="Select WebKit Folder")
        if path:
            self.webkit_path.set(path)
            self.save_config()
    
    def log_message(self, message):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, f"{message}\n")
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)
    
    def start_debugging(self):
        webkit_path = self.webkit_path.get()
        
        if not webkit_path or not os.path.exists(webkit_path):
            messagebox.showerror("Error", "Please select a valid WebKit folder or use Auto Setup")
            return
        
        self.save_config()
        
        # Determine which script to run based on platform
        script_path = None
        if platform.system() == "Windows":
            script_path = os.path.join(webkit_path, "start.ps1")
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]
        else:  # Assume Linux/macOS
            script_path = os.path.join(webkit_path, "start.sh")
            cmd = ["bash", script_path]
        
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"Script not found: {script_path}")
            return
        
        try:
            self.log_message(f"Starting debugging server with: {' '.join(cmd)}")
            self.log_message("Please ensure your iOS device is unlocked and connected.")
            
            # Start the process
            self.debugging_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=webkit_path
            )
            
            # Update UI
            self.status_label.config(text="Server is running")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.refresh_button.config(state=tk.NORMAL)
            
            # Start monitoring thread
            self.stop_monitoring = False
            self.monitoring_thread = threading.Thread(target=self.monitor_process)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
            # Wait a bit for the server to start
            self.root.after(3000, self.refresh_pages)
            
        except Exception as e:
            self.log_message(f"Error starting debugging server: {str(e)}")
            messagebox.showerror("Error", f"Failed to start debugging server: {str(e)}")
    
    def monitor_process(self):
        while self.debugging_process and not self.stop_monitoring:
            output = self.debugging_process.stdout.readline()
            if output:
                # Schedule UI update from the main thread
                self.root.after(0, lambda msg=output: self.log_message(msg.strip()))
            
            # Check if process has terminated
            if self.debugging_process.poll() is not None:
                if not self.stop_monitoring:  # Only log if not manually stopped
                    self.root.after(0, lambda: self.log_message("Debugging server has stopped"))
                    self.root.after(0, self.reset_ui)
                break
            
            time.sleep(0.1)
    
    def reset_ui(self):
        self.status_label.config(text="Not running")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.refresh_button.config(state=tk.DISABLED)
        self.pages_tree.delete(*self.pages_tree.get_children())
    
    def stop_debugging(self):
        if self.debugging_process:
            self.stop_monitoring = True
            self.log_message("Stopping debugging server...")
            
            # Kill the process
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.debugging_process.pid)])
            else:
                self.debugging_process.terminate()
                try:
                    self.debugging_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.debugging_process.kill()
            
            self.debugging_process = None
            self.reset_ui()
    
    def extract_page_ids_from_html(self, html_content):
        """Extract page IDs from the HTML content of localhost:9222/"""
        page_ids = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            list_items = soup.find_all('li')
            
            for item in list_items:
                # Extract the value attribute which contains the page ID
                if 'value' in item.attrs:
                    page_ids.append(item['value'])
            
            self.log_message(f"Found page IDs: {', '.join(page_ids)}")
            return page_ids
        except Exception as e:
            self.log_message(f"Error parsing HTML: {str(e)}")
            return []
    
    def refresh_pages(self):
        try:
            # Clear current list
            self.pages_tree.delete(*self.pages_tree.get_children())
            self.pages_list = []
            self.page_ids = []
            
            # First try to get HTML content from localhost:9222
            try:
                html_response = requests.get("http://localhost:9222/")
                if html_response.status_code == 200:
                    self.page_ids = self.extract_page_ids_from_html(html_response.text)
                else:
                    self.log_message(f"Failed to get HTML listing, status: {html_response.status_code}")
            except Exception as e:
                self.log_message(f"Error getting HTML listing: {str(e)}")
            
            # Fetch JSON data for page details
            response = requests.get("http://localhost:9222/json")
            if response.status_code == 200:
                self.pages_list = response.json()
                
                # Add pages to treeview
                for i, page in enumerate(self.pages_list):
                    # Use the extracted page ID if available, otherwise default to index+1
                    page_id = self.page_ids[i] if i < len(self.page_ids) else str(i+1)
                    title = page.get('title', 'Untitled')
                    url = page.get('url', '')
                    
                    self.pages_tree.insert('', tk.END, values=(page_id, title, url))
                
                self.log_message(f"Found {len(self.pages_list)} inspectable pages")
            else:
                self.log_message(f"Failed to get JSON data, server returned: {response.status_code}")
        
        except requests.exceptions.ConnectionError:
            self.log_message("Could not connect to debugging server. Make sure it's running.")
        except Exception as e:
            self.log_message(f"Error refreshing pages: {str(e)}")
    
    def open_debugger(self):
        selection = self.pages_tree.selection()
        if not selection:
            messagebox.showinfo("Selection Required", "Please select a page to debug")
            return
        
        # Get the selected item's index
        selected_idx = self.pages_tree.index(selection[0])
        
        if selected_idx < len(self.pages_list):
            # Get the page ID from the tree view
            page_id = self.pages_tree.item(selection[0])['values'][0]
            
            if page_id:
                debugger_url = f"http://localhost:8080/Main.html?ws=localhost:9222/devtools/page/{page_id}"
                title = self.pages_tree.item(selection[0])['values'][1]
                
                self.log_message(f"Opening debugger for: {title}")
                self.log_message(f"Debugger URL: {debugger_url}")
                
                # Open in default browser
                webbrowser.open(debugger_url)
            else:
                messagebox.showerror("Error", "Selected page has no valid ID")
        else:
            messagebox.showerror("Error", "Invalid selection")

def main():
    root = tk.Tk()
    app = IOSSafariDebuggerApp(root)
    
    # Handle application close
    def on_closing():
        if app.debugging_process:
            if messagebox.askyesno("Quit", "Debugging server is still running. Stop it and exit?"):
                app.stop_debugging()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Apply a theme if available
    try:
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')
    except:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    main()