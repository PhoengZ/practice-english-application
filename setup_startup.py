import os
import sys
import winreg
import subprocess

def add_to_path(folder_path):
    """Adds a folder to the User PATH environment variable."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""

        if folder_path not in current_path:
            new_path = current_path + ";" + folder_path if current_path else folder_path
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            print(f"✅ Added {folder_path} to User PATH.")
            print("💡 Please restart your terminal/CMD to use the new commands.")
        else:
            print(f"ℹ️ {folder_path} is already in PATH.")
        winreg.CloseKey(key)
    except Exception as e:
        print(f"❌ Error updating PATH: {e}")

def create_shortcuts():
    script_dir = os.path.dirname(os.path.realpath(__file__))
    python_exe = sys.executable
    app_path = os.path.join(script_dir, "app.py")
    dashboard_path = os.path.join(script_dir, "dashboard.py")
    
    # Path to streamlit.exe (usually in the same folder as python.exe or in Scripts)
    streamlit_exe = os.path.join(os.path.dirname(python_exe), "Scripts", "streamlit.exe")
    if not os.path.exists(streamlit_exe):
        # Fallback for some installations
        streamlit_exe = os.path.join(os.path.dirname(python_exe), "streamlit.exe")

    # 1. Create Practice.bat
    practice_bat = os.path.join(script_dir, "Practice.bat")
    with open(practice_bat, "w") as f:
        f.write(f'@echo off\n"{python_exe}" "{app_path}" --force\n')
    print(f"✅ Created {practice_bat}")

    # 2. Create Dashboard.bat
    dashboard_bat = os.path.join(script_dir, "Dashboard.bat")
    with open(dashboard_bat, "w") as f:
        # Streamlit needs to run from the project directory to find modules
        f.write(f'@echo off\ncd /d "{script_dir}"\n"{streamlit_exe}" run "{dashboard_path}"\n')
    print(f"✅ Created {dashboard_bat}")

    # 3. Add project dir to PATH
    add_to_path(script_dir)

def add_to_startup():
    python_exe = sys.executable
    script_dir = os.path.dirname(os.path.realpath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    
    cmd = f'"{python_exe}" "{app_path}"'
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "EnglishPracticeCLI", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        print("✅ Successfully added to Windows startup (Auto-run on login).")
    except Exception as e:
        print(f"❌ Error adding to startup: {e}")

if __name__ == "__main__":
    if "conda" not in sys.executable.lower() and "envs" not in sys.executable.lower():
        print("⚠️ Warning: You might not be running this inside a Conda environment.")
    
    create_shortcuts()
    add_to_startup()
    print("\n🎉 Setup complete! You can now type 'Practice' or 'Dashboard' in any CMD window.")
