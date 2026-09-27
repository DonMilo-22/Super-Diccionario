import os
import subprocess
import sys


def main():
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "Word Helper",
        "--add-data",
        f"data{os.pathsep}data",
    ]

    icon = None
    if sys.platform == "darwin" and os.path.exists("icon.icns"):
        icon = "icon.icns"
    elif sys.platform == "win32" and os.path.exists("icon.ico"):
        icon = "icon.ico"

    if icon:
        command.extend(["--icon", icon])

    command.append("main.py")
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
