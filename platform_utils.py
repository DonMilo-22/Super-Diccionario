import ctypes
import platform
import time

from pynput.keyboard import Controller


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


def type_text(text, target=None, delay=0.15):
    restore_foreground_target(target)
    time.sleep(delay)
    Controller().type(text)
