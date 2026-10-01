#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_app.py — one-click packaging of CocoIDE into a double-clickable app.

Usage (run from the project folder, no arguments needed):

    python3 build_app.py            # auto-detect platform
    python3 build_app.py --clean    # remove build artefacts and retry

What it produces:

  * macOS   -> dist/CocoIDE.app      (drag to /Applications or Desktop)
  * Windows -> dist\\CocoIDE\\CocoIDE.exe  (folder with exe + libs)
  * Linux   -> dist/CocoIDE/CocoIDE  (same folder layout; can be desktop-linked)

Requirements: Python 3 with Tkinter (tkinter is part of the standard python.org
macOS installer; on Debian/Ubuntu: sudo apt install python3-tk). PyInstaller is
installed automatically into a throwaway virtualenv by this script if missing.

The resulting bundle contains the interpreter, Tk/Tcl and all program modules
(cocas.py, cdm8_emu.py, ...), plus data files standard.mlb / sendfile.py /
cocol.py, so the app runs standalone — no terminal, no Python install needed
on the target machine.
"""

import os
import subprocess
import sys
import shutil
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ENTRY = "cocoideV1.91.pyw"          # main module (also works as plain entry)
APP_NAME = "CocoIDE"
DATA_FILES = ["standard.mlb", "sendfile.py", "cocol.py"]
HIDDEN_IMPORTS = ["cdm8_asm", "cocas", "cdm8_emu", "cdm8_io", "sendfile",
                  "cocol"]  # pyserial is not used by this fork


def run(cmd, **kw):
    print("+ " + " ".join(cmd))
    return subprocess.check_call(cmd, cwd=HERE, **kw)


def make_venv():
    """Create ./.venv-build and pip-install pyinstaller there."""
    venv = os.path.join(HERE, ".venv-build")
    py = os.path.join(venv, "bin", "python") if os.name != "nt" \
        else os.path.join(venv, "Scripts", "python.exe")
    if not os.path.exists(py):
        print("Creating build virtualenv in .venv-build ...")
        run([sys.executable, "-m", "venv", venv])
    print("Installing PyInstaller ...")
    run([py, "-m", "pip", "--quiet", "--disable-pip-version-check",
         "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "--quiet", "--disable-pip-version-check",
         "install", "pyinstaller"])
    return py


def icon_flag():
    for cand in ("cocoide.icns", "icon.icns", "assets/cocoide.icns"):
        p = os.path.join(HERE, cand)
        if os.path.exists(p):
            return ["--icon", p]
    return []


def build(pybin):
    cmd = [pybin, "-m", "PyInstaller",
           "--noconfirm", "--clean",
           "--name", APP_NAME,
           "--windowed",                    # no console window (GUI app)
           "--distpath", "dist",
           "--workpath", "build",
           "--specpath", "build",
           ] + icon_flag()
    for d in DATA_FILES:
        src = os.path.join(HERE, d)
        if os.path.exists(src):
            cmd += ["--add-data", src + os.pathsep + "."]
    for h in HIDDEN_IMPORTS:
        cmd += ["--hidden-import", h]
    cmd.append(ENTRY)
    run(cmd)


def mac_postprocess():
    """Write Info.plist keys that make the .app behave natively."""
    app = os.path.join(HERE, "dist", APP_NAME + ".app")
    plist = os.path.join(app, "Contents", "Info.plist")
    if not os.path.exists(plist):
        return
    with open(plist, "r", encoding="utf-8") as f:
        txt = f.read()
    repl = {
        "<key>CFBundleDisplayName</key>": None,  # ensure present below
    }
    add = textwrap.dedent("""\
        <key>CFBundleDisplayName</key><string>CocoIDE</string>
        <key>NSHighResolutionCapable</key><true/>
        <key>CFBundleShortVersionString</key><string>1.91</string>
        <key>CFBundleDevelopmentRegion</key><string>en</string>
        """)
    if "NSHighResolutionCapable" not in txt:
        txt = txt.replace("</dict>", add + "</dict>", 1)
    with open(plist, "w", encoding="utf-8") as f:
        f.write(txt)
    print("Patched Info.plist (Retina support, display name).")


def main():
    if "--clean" in sys.argv:
        for d in ("build", "dist", ".venv-build", APP_NAME + ".spec"):
            p = os.path.join(HERE, d)
            if os.path.isdir(p):
                shutil.rmtree(p)
            elif os.path.exists(p):
                os.remove(p)
        print("Cleaned.")
        return
    # sanity checks
    if not os.path.exists(os.path.join(HERE, ENTRY)):
        sys.exit("Entry %s not found - run this script from the project folder."
                 % ENTRY)
    try:
        import tkinter  # noqa: F401
    except ImportError:
        sys.exit(textwrap.fill(
            "ERROR: Python's Tkinter is not available. On macOS use the "
            "python.org installer (Tk included); on Debian/Ubuntu run: "
            "sudo apt install python3-tk"))
    pybin = make_venv()
    build(pybin)
    if sys.platform == "darwin":
        mac_postprocess()
    print()
    if sys.platform == "darwin":
        print("DONE. Double-clickable app:  dist/CocoIDE.app")
        print("Tip: drag it to /Applications. First launch via network copy "
              "may need right-click -> Open (Gatekeeper).")
    elif os.name == "nt":
        print("DONE. Run:  dist\\%s\\%s.exe" % (APP_NAME, APP_NAME))
    else:
        print("DONE. Run:  dist/%s/%s" % (APP_NAME, APP_NAME))


if __name__ == "__main__":
    main()
