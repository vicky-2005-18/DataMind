# DataMind Startup Guide

## Quick Start

### Option 1: Run Setup Script (Recommended for First Time)

1. Open PowerShell in the DataMind project directory
2. Run the setup script:
   ```powershell
   .\setup_datamind.ps1
   ```
3. After setup completes, run:
   ```powershell
   .\start_datamind.ps1
   ```

### Option 2: Direct Startup (If Dependencies Already Installed)

```powershell
.\start_datamind.ps1
```

Or for a simple startup without checks:
```powershell
.\start_datamind_simple.ps1
```

### Option 3: Manual Startup

```powershell
streamlit run app.py
```

## Available Scripts

### `setup_datamind.ps1`
- **Purpose**: Install all required dependencies
- **When to use**: First time setup or if you encounter dependency issues
- **What it does**:
  - Checks Python installation
  - Upgrades pip
  - Installs all project dependencies

### `start_datamind.ps1`
- **Purpose**: Start DataMind with full checks
- **When to use**: Regular startup
- **What it does**:
  - Checks Python installation
  - Verifies correct directory
  - Installs/updates dependencies if needed
  - Starts the application

### `start_datamind_simple.ps1`
- **Purpose**: Quick startup without checks
- **When to use**: When you know everything is set up correctly
- **What it does**: Just runs `streamlit run app.py`

## Troubleshooting

### "streamlit is not recognized"
**Solution**: Run the setup script first:
```powershell
.\setup_datamind.ps1
```

### "python is not recognized"
**Solution**: Install Python 3.11+ from https://www.python.org/
- **Important**: Check "Add Python to PATH" during installation

### Script execution policy error
**Solution**: Allow script execution in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Dependencies not installing
**Solution**: Try upgrading pip first:
```powershell
python -m pip install --upgrade pip
pip install -e .
```

## System Requirements

- **Python**: 3.11 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Disk Space**: 500MB for dependencies

## After Startup

Once DataMind starts:
1. The application will open in your default browser
2. Navigate to `http://localhost:8501` if it doesn't open automatically
3. Create a project or load a demo dataset to get started

## Stopping the Application

Press `Ctrl+C` in the PowerShell window to stop the DataMind server.
