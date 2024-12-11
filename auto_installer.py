import subprocess
import urllib.request
import sys

def is_connected(host='https://www.google.com/'):
    """
    Check internet connectivity.
    Returns True if the internet is available, otherwise False.
    """
    try:
        urllib.request.urlopen(host, timeout=5)
        return True
    except Exception:
        return False
def update_pip():
    """
    Update pip to the latest version.
    """
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print("✅ Pip updated to the latest version.")
    except subprocess.CalledProcessError:
        print("⚠️ Failed to update pip.")

def install_module(module_name):
    """
    Install a single Python module using pip.
    """
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", module_name], check=True)
        print(f"✅ Module '{module_name}' installed successfully!")
    except subprocess.CalledProcessError:
        if not is_connected():
            print("❌ Error: Internet connection is required. Please check your connection.")
        else:
            print(f"❌ Error: Failed to install '{module_name}'. Ensure the module name is correct.")

def install_modules(module_list):
    """
    Install multiple Python modules.
    """
    for module in module_list:
        install_module(module)

def install_from_file(file_path):
    """
    Install modules listed in a file.
    Each module should be listed on a new line.
    """
    try:
        with open(file_path, "r") as file:
            modules = [line.strip() for line in file if line.strip()]
            print(f"Modules to install: {modules}")
            install_modules(modules)
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"❌ Error: An unexpected error occurred: {e}")

def main():
    """
    Main function to handle module installation.
    """
    update_pip()


    
    file_path = input("Enter the path to the file: ").strip()
    install_from_file(file_path)

if __name__ == "__main__":
    main()
