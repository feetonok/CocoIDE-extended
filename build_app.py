#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_app.py — one-click packaging of CocoIDE into a double-clickable app.

Usage (run from the project folder, no arguments needed):

    python3 build_app.py            # auto-detect platform
    python3 build_app.py --clean    # remove build artefacts and retry

What it produces:

  * macOS   -> dist/CocoIDE.app      (drag to /Applications or Desktop;
                                      double-click launches the IDE directly -
                                      NO terminal window, no "close processes?"
                                      prompt, Dock icon + native menu bar)
  * Windows -> dist\\CocoIDE\\CocoIDE.exe  (folder with exe + libs)
  * Linux   -> dist/CocoIDE/CocoIDE  (same folder layout; can be desktop-linked)

Requirements: Python 3 with Tkinter (Tk is part of the python.org macOS
installer). PyInstaller is installed automatically into a throwaway virtualenv
by this script if missing.

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
# All local modules are shipped as data too: the app's resPath() finds them
# next to the executable inside the bundle, so even code that opens sources
# from disk (legacy paths) keeps working in the frozen .app.
DATA_FILES = ["standard.mlb", "sendfile.py", "cocol.py",
              "cdm8_asm.py", "cdm8_emu.py", "cdm8_io.py", "cocas.py"]
HIDDEN_IMPORTS = ["cdm8_asm", "cocas", "cdm8_emu", "cdm8_io", "sendfile",
                  "cocol"]  # pyserial is not used by this fork


def run(cmd, **kw):
    print("+ " + " ".join(cmd))
    return subprocess.check_call(cmd, cwd=HERE, **kw)


def _pip_ok(py):
    """True if the given interpreter can run 'python -m pip'."""
    try:
        subprocess.check_call([py, "-m", "pip", "--version"],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _bootstrap_pip(py):
    """Repair a venv whose pip is missing (some macOS 3.12+ installers /
    --without-pip environments). Uses ensurepip, then get-pip.py as fallback."""
    try:
        run([py, "-m", "ensurepip", "--upgrade", "--default-pip"])
        if _pip_ok(py):
            return True
    except Exception:
        pass
    # last resort: download get-pip.py into a temp file and run it
    import tempfile
    import urllib.request
    try:
        fd, gp = tempfile.mkstemp(suffix=".py")
        os.close(fd)
        urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", gp)
        run([py, gp])
        os.remove(gp)
        return _pip_ok(py)
    except Exception:
        return False


def make_venv():
    """Create ./.venv-build and pip-install pyinstaller there.

    Robust against broken system pythons: if 'python -m venv' produces an
    environment without pip (or fails outright), we bootstrap pip via
    ensurepip / get-pip.py; if even that fails, we fall back to installing
    PyInstaller for the *current* interpreter with --user and use it directly.
    """
    venv = os.path.join(HERE, ".venv-build")
    py = os.path.join(venv, "bin", "python") if os.name != "nt" \
        else os.path.join(venv, "Scripts", "python.exe")
    made = False
    if not os.path.exists(py):
        print("Creating build virtualenv in .venv-build ...")
        shutil.rmtree(venv, ignore_errors=True)
        try:
            run([sys.executable, "-m", "venv", venv])
            made = True
        except Exception as e:
            print("venv creation failed (%s) - trying --without-pip ..." % e)
            try:
                run([sys.executable, "-m", "venv", "--without-pip", venv])
                made = True
            except Exception as e2:
                print("venv unavailable (%s); will use the current Python." % e2)
                py = None
    if py and os.path.exists(py):
        if not _pip_ok(py):
            print("venv has no working pip - bootstrapping it ...")
            _bootstrap_pip(py)
        if _pip_ok(py):
            print("Installing PyInstaller ...")
            # NOTE: never 'pip install --upgrade pip' here: on some macOS
            # python.org builds that leaves site-packages/pip broken
            # ('No module named pip') and kills the whole build.
            for attempt in range(2):
                try:
                    run([py, "-m", "pip", "--quiet", "--disable-pip-version-check",
                         "install", "pyinstaller"])
                    return py
                except Exception as e:
                    print("pip install in venv failed (try %d): %s" % (attempt+1, e))
                    # maybe pip broke mid-install -> re-bootstrap once
                    if attempt == 0:
                        _bootstrap_pip(py)
    # ---- fallback: use the current interpreter -------------------------
    print("Falling back to the current interpreter: %s" % sys.executable)
    if not _pip_ok(sys.executable):
        if not _bootstrap_pip(sys.executable):
            sys.exit("ERROR: cannot get pip on this Python.\n"
                     "Install it manually:  python3 -m ensurepip --upgrade\n"
                     "then re-run:          python3 build_app.py")
    try:
        run([sys.executable, "-m", "pip", "--quiet",
             "--disable-pip-version-check", "install", "pyinstaller"])
    except Exception:
        run([sys.executable, "-m", "pip", "--quiet", "--user",
             "--disable-pip-version-check", "install", "pyinstaller"])
    return sys.executable


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
    if sys.platform == "darwin":
        # pyobjc lets the frozen app set its real macOS identity at runtime
        # (Dock name/icon, bring-to-front, native About/Hide/Quit menu).
        try:
            subprocess.check_call([pybin, "-c", "import AppKit"],
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL)
        except Exception:
            run([pybin, "-m", "pip", "--quiet", "--disable-pip-version-check",
                 "install", "pyobjc-framework-Cocoa"])
        cmd += ["--hidden-import", "AppKit"]
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
    add = ""
    if "CFBundleDisplayName" not in txt:
        add += "<key>CFBundleDisplayName</key><string>CocoIDE</string>\n\t"
    if "NSHighResolutionCapable" not in txt:
        add += "<key>NSHighResolutionCapable</key><true/>\n\t"
    if "CFBundleShortVersionString" not in txt:
        add += "<key>CFBundleShortVersionString</key><string>1.91</string>\n\t"
    if "CFBundleDevelopmentRegion" not in txt:
        add += ("<key>CFBundleDevelopmentRegion</key><string>en"
                "</string>\n\t")
    # GUI app must never pretend to be a background/agent app:
    if "LSUIElement" not in txt:
        add += "<key>LSUIElement</key><false/>\n\t"
    if add:
        txt = txt.replace("</dict>", add + "</dict>", 1)
        with open(plist, "w", encoding="utf-8") as f:
            f.write(txt)
        print("Patched Info.plist (display name, Retina, version).")


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
        print("Drag it to /Applications and launch from Launchpad/Finder -")
        print("it opens straight into the IDE, no Terminal involved.")
        print("(First launch after download may need right-click -> Open once;")
        print(" your own local builds are not quarantined and just open.)")
    elif os.name == "nt":
        print("DONE. Run:  dist\\%s\\%s.exe" % (APP_NAME, APP_NAME))
    else:
        print("DONE. Run:  dist/%s/%s" % (APP_NAME, APP_NAME))


if __name__ == "__main__":
    main()
