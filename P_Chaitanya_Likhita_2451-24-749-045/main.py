"""
ImageShield Application Entry Point
BE CSE(IOT-CS-BCT) – Sem IV 2025 – 2026 Batch-No: 1

Run this file to start the ImageShield GUI application.
"""

import sys
import os
import argparse

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def ensure_venv_python():
    """Restart the launcher in the workspace virtual environment when needed."""
    workspace_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(workspace_dir, ".venv", "bin", "python")

    if not os.path.exists(venv_python):
        return

    if sys.prefix == sys.base_prefix:
        os.execv(venv_python, [venv_python] + sys.argv)


ensure_venv_python()

from frontend import main, main_with_camera

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ImageShield application launcher")
    parser.add_argument(
        "--camera",
        action="store_true",
        help="Open ImageShield and launch the live camera capture window"
    )
    args = parser.parse_args()

    print("Starting ImageShield - Secure Image Encryption Tool...")
    print("=" * 60)
    print("ImageShield v1.0")
    print("Secure PNG/JPG Image Encryption")
    print("© 2026 MVSR Engineering College")
    print("=" * 60)
    print()
    
    try:
        if args.camera:
            main_with_camera()
        else:
            main()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)
