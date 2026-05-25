import os
import sys
import subprocess
import winreg

# Try to import get_conda_python from setup_startup to maintain consistency
try:
    from setup_startup import get_conda_python
except ImportError:
    # Fail-safe local version or fallback
    def get_conda_python():
        return sys.executable

def setup_logon_registry():
    python_exe = get_conda_python()
    script_dir = os.path.dirname(os.path.realpath(__file__))
    root_dir = os.path.dirname(script_dir)
    app_path = os.path.join(root_dir, "src", "ui", "app.py")
    
    # Use --startup flag to match setup_startup.py behavior
    cmd = f'cmd /c "cd /d \"{root_dir}\" && \"{python_exe}\" \"{app_path}\" --startup"'
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "EnglishPracticeCLI", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        print("✅ Ensured logon auto-run is in Registry.")
    except Exception as e:
        print(f"❌ Error updating registry: {e}")

def create_daily_task():
    python_exe = get_conda_python()
    script_dir = os.path.dirname(os.path.realpath(__file__))
    root_dir = os.path.dirname(script_dir)
    app_path = os.path.join(root_dir, "src", "ui", "app.py")
    
    task_name = "EnglishPracticeTask_Daily"
    cmd_args = f'/c "cd /d \"{root_dir}\" && \"{python_exe}\" \"{app_path}\""'
    
    try:
        subprocess.run([
            "schtasks", "/create", "/tn", task_name, 
            "/tr", f'cmd.exe {cmd_args}', 
            "/sc", "daily", "/st", "07:00", "/f"
        ], check=True)
        print("✅ Successfully created daily 7:00 AM Scheduled Task.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating daily task: {e}")

if __name__ == "__main__":
    setup_logon_registry()
    create_daily_task()
