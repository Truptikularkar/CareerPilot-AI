import sys
import subprocess
from pathlib import Path


def main():
    """CLI launcher for CareerPilot AI Streamlit application."""
    ui_app_path = Path(__file__).resolve().parent / "ui" / "app.py"
    if not ui_app_path.exists():
        print(f"Error: UI application entrypoint not found at {ui_app_path}")
        sys.exit(1)

    print("=" * 65)
    print("CAREERPILOT AI — LAUNCHING LOCAL STREAMLIT INTERFACE")
    print("=" * 65)
    print(f"App Path: {ui_app_path}")
    print("=" * 65 + "\n")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ui_app_path),
        "--server.headless",
        "false",
        "--browser.gatherUsageStats",
        "false",
    ]
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
