#!/usr/bin/env python3
"""
Bootstrap / Setup Script for Laptop Recommender System.
Cross-platform environment setup, dependency installation, and diagnostics.
Works on Windows, macOS, and Linux.
"""

import os
import sys
import subprocess
import shutil
import platform

REQUIRED_PYTHON_VERSION = (3, 9)

def print_step(msg):
    print(f"\n========================================================")
    print(f"--> {msg}")
    print(f"========================================================")

def check_python_version():
    print(f"Checking Python version...")
    current_version = sys.version_info
    print(f"Current version: {platform.python_version()}")
    if current_version < REQUIRED_PYTHON_VERSION:
        print(f"Error: Python {REQUIRED_PYTHON_VERSION[0]}.{REQUIRED_PYTHON_VERSION[1]}+ is required.")
        sys.exit(1)
    print("Python version is compatible.")

def get_venv_python():
    if platform.system() == "Windows":
        return os.path.join(".venv", "Scripts", "python.exe")
    else:
        return os.path.join(".venv", "bin", "python")

def setup_virtual_environment():
    print_step("Setting up virtual environment")
    venv_dir = ".venv"
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment in '{venv_dir}'...")
        try:
            subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
            print("Virtual environment created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating virtual environment: {e}")
            sys.exit(1)
    else:
        print("Virtual environment already exists.")

def install_dependencies():
    print_step("Installing project dependencies")
    venv_python = get_venv_python()
    if not os.path.exists(venv_python):
        print(f"Error: Virtual environment python not found at {venv_python}")
        sys.exit(1)

    print("Upgrading pip...")
    try:
        subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    except subprocess.CalledProcessError:
        print("Warning: Failed to upgrade pip. Proceeding with package installation.")

    print("Installing requirements from requirements.txt...")
    try:
        subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def setup_env_file():
    print_step("Configuring environment variables")
    env_file = ".env"
    env_example = ".env.example"

    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            print(f"Copying {env_example} to {env_file}...")
            shutil.copy(env_example, env_file)
            print(f"Created local configuration file '{env_file}'.")
            print("Note: Please open '.env' and specify your OPENAI_API_KEY for Deep Learning capabilities.")
        else:
            print(f"Warning: {env_example} not found. Cannot create default .env.")
    else:
        print("Local configuration file '.env' already exists.")

def run_diagnostics():
    print_step("Running diagnostics and verification")
    venv_python = get_venv_python()
    
    # Define test script content
    diagnostic_script = """
import sys
import os

print("Python executable:", sys.executable)
print("Python version:", sys.version.split()[0])

modules = ['flask', 'requests', 'bs4', 'numpy', 'openai', 'dotenv']
missing = []
for mod in modules:
    try:
        __import__(mod)
        print(f"  [PASS] {mod} is successfully installed.")
    except ImportError:
        print(f"  [FAIL] {mod} is MISSING.")
        missing.append(mod)

# Check data files
data_files = ['laptops_cache.json', 'laptops_active.json']
for file in data_files:
    if os.path.exists(file):
        print(f"  [PASS] {file} exists.")
    else:
        print(f"  [WARN] {file} is missing.")

if missing:
    sys.exit(1)
sys.exit(0)
"""
    
    # Run test script inside the virtual environment
    try:
        result = subprocess.run(
            [venv_python, "-c", diagnostic_script],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        print("Diagnostics completed successfully. System is healthy!")
    except subprocess.CalledProcessError as e:
        print("Diagnostics FAILED!")
        print("Stdout:", e.stdout)
        print("Stderr:", e.stderr)
        sys.exit(1)

def print_onboarding_guide():
    print_step("Setup Complete! Startup Guide")
    
    activate_cmd = ".venv\\Scripts\\activate" if platform.system() == "Windows" else "source .venv/bin/activate"
    python_cmd = "python app.py"
    test_cmd = "pytest"

    print("To start the application:")
    print(f"  1. Activate the environment:  {activate_cmd}")
    print(f"  2. Run the Flask server:      {python_cmd}")
    print(f"  3. Open your browser at:      http://127.0.0.1:5000")
    print("")
    print("To run automated tests:")
    print(f"  1. Run with pytest:           {test_cmd}")
    print("========================================================")

def main():
    print("========================================================")
    print("Laptop Recommender System - Environment Bootstrapper")
    print("========================================================")
    
    check_python_version()
    setup_virtual_environment()
    install_dependencies()
    setup_env_file()
    run_diagnostics()
    print_onboarding_guide()

if __name__ == "__main__":
    main()
