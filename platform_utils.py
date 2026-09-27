import ctypes
import os
import platform
import sys
import time

from pynput.keyboard import Controller, Key


def get_foreground_target():
    system = platform.system()

    if system == "Windows":
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        return ("windows", int(hwnd)) if hwnd else None

    if system == "Darwin":
        try:
            from AppKit import NSWorkspace

            app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if app:
                return ("macos", int(app.processIdentifier()))
        except Exception:
            return None

    return None


def target_name(target):
    if not target:
        return ""

    kind, identifier = target

    if kind == "Windows":
        user32 = ctypes.windll.user32
        length = user32.GetWindowTextLengthW(identifier)
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(identifier, buffer, length + 1)
        return buffer.value

    if kind == "macos":
        try:
            from AppKit import NSRunningApplication
            app = NSRunningApplication.runningApplicationWithProcessIdentifier_(identifier)
            return app.localizedName() if app else ""
        except Exception:
            return ""

    return ""


def restore_foreground_target(target):
    if not target:
        return False

    kind, identifier = target

    if kind == "Windows":
        user32 = ctypes.windll.user32
        if not user32.IsWindow(identifier):
            return False
        user32.ShowWindow(identifier, 9)
        return bool(user32.SetForegroundWindow(identifier))

    if kind == "macos":
        try:
            from AppKit import NSApplicationActivateIgnoringOtherApps, NSRunningApplication
            app = NSRunningApplication.runningApplicationWithProcessIdentifier_(identifier)
            if not app:
                return False
            return bool(app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps))
        except Exception:
            return False

    return False


def type_text(text, target=None, delay=0.12, press_enter=False):
    restore_foreground_target(target)
    time.sleep(delay)
    controller = Controller()
    controller.type(text)
    if press_enter:
        controller.press(Key.enter)
        controller.release(Key.enter)


def set_autostart(enabled):
    system = platform.system()

    if system == "Windows":
        import winreg

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        command = f'"{sys.executable}" "{os.path.abspath("main.py")}"'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, "WordHelper", 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, "WordHelper")
                except FileNotFoundError:
                    pass
        return True

    if system == "Darwin":
        launch_agents = os.path.expanduser("~/Library/LaunchAgents")
        os.makedirs(launch_agents, exist_ok=True)
        plist_path = os.path.join(launch_agents, "com.donmilo.wordhelper.plist")

        if enabled:
            command = os.path.abspath("main.py")
            plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.donmilo.wordhelper</string>
<key>ProgramArguments</key><array><string>{sys.executable}</string><string>{command}</string></array>
<key>RunAtLoad</key><true/>
</dict></plist>"""
            with open(plist_path, "w", encoding="utf-8") as file:
                file.write(plist)
        elif os.path.exists(plist_path):
            os.remove(plist_path)
        return True

    return False



def find_target_by_name(name):
    wanted = (name or "").lower()
    system = platform.system()

    if system == "Windows":
        user32 = ctypes.windll.user32
        matches = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        def enum_proc(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value
            if wanted in title.lower():
                matches.append(("windows", int(hwnd)))
            return True

        user32.EnumWindows(enum_proc, 0)
        return matches[0] if matches else None

    if system == "Darwin":
        try:
            from AppKit import NSWorkspace
            for app in NSWorkspace.sharedWorkspace().runningApplications():
                app_name = app.localizedName() or ""
                if wanted in app_name.lower():
                    return ("macos", int(app.processIdentifier()))
        except Exception:
            return None

    return None
