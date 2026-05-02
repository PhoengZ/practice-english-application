import os
import sys
import winreg

def add_to_startup():
    # Get the path to the current script's directory
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # We want to run app.py
    app_path = os.path.join(script_dir, "app.py")
    # Path to the python executable
    python_exe = sys.executable
    
    # Command to run: python.exe app.py
    cmd = f'"{python_exe}" "{app_path}"'
    
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "EnglishPracticeCLI", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        print("Successfully added to Windows startup.")
    except Exception as e:
        print(f"Error adding to startup: {e}")

if __name__ == "__main__":
    add_to_startup()
