#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Python3 and 2
from __future__ import absolute_import, division, print_function

# Coco De Mere 8 IDE and emulator
# (c) M L Walters June-July 2018
# Code/Modules based on cocoemu.py, cocas.py and cocol.py
    # V1 By Prof. Alex Shaferenko.  July 2016
    # V1.1. GUI modifications by M L Walters, August/Sept 2015
    # V1.2. Fixed bug in app.reload() where memory not displaying correctly

# CocoIDE V0.4 Radical Overhaul of GUI M.L.Walters July-Oct 2016
# V0.5 -    V0.8 Updates to GUI for Win and MAC versions. minor bugs fixed
# V0.9 -    Updates and fixes.(also in cocas.py V2.3)
# V0.91 -   Initial Save error bug fixed (only affects cocoide.pyw)
# v0.92 -   Adjusts default font to fit screen better!
#           Improved Watch display of binary strings
#           Saved breakpoints if assembly list not changed.
#           Editor now supports additional keyboard shortcuts:
#               Ctrl+Left Arrow – Move cursor to beginning of previous word.
#               Ctrl+Right Arrow – Move cursor to beginning of next word
#               Ctrl+Backspace – Delete previous word.
#               Ctrl+Delete – Delete next word.
#              Selecting Text. All of the above shortcuts can be combined
#                   with the Shift key to select text.
#               Ctrl+A – Select all text.
#               Ctrl+C, Ctrl+Insert – Copy selected text.
#               Ctrl+X, Shift+Delete – Cut selected text.
#               Ctrl+V, Shift+Insert – Paste text at cursor.
#               Ctrl+Z – Undo.
#               Ctrl+Y – Redo.
#           Note: Mac users Use the Option key instead of the Ctrl key?
#           Included IF to Ames system (if sendfile.py is in program directory)
#           Adjusts to screen resolution automatically for small screens.
#           For large screens, option to set presenter mode (fills screen). Also
#           good for smaller laptop/notebook screens. Can be set in cdm8_xxx.py file
#
# V0.93 -   Now able to save Memory Image file (for loading into Logisim
#           Use Meta comments #$<option> to format Memory Watch labels in Watch
#           Window:
#            #$str = String
#            #$dec = Signed Decimal
#            #$hex = Hexadecimal
#            #$bin = Binary
#           "Run From" dropdown menu to select entry point (picks up any label
#           beginning with _ e.g. _Start: or _Start> )
#           Disables editing on AMES meta comment lines containing "#!" while
#           Ames is running. E.g. _Q1> #! cannot be edited
#           Added auto-indent feature to editor
# V0.94 -   Fixed tab bug! Now lines up correctly
#           Able to use command line options: <filename> and
#           -p for presenter screenmode (overides setting in cdm8_asm.py file)
# V0.941    Fixed Mac bug for Compile/Save Image buttons???
# V0.942    Tidied up runFrom options re. reset and clearing memory etc.
#           Also changed Exit (save, cancel) options. More intuitive.
# V0.95     Distribution version for deployment
# V0.951    Changesd AMES exit behaviour to stop saving the file twice
#           Fixed #! behaviour (16/1/17)
# V0.96     Added Ames Logisim download/open/close capability for BPT
# V0.97     Passed final tests on LAb PCs with Ames extensions
# V0.971    Save pointer display
# V0.98     Ames control keys improved filtering!
#           Changed circ save file name (._circ.circ). Allows student to Save As?
# V0.982    Fixed OSX/Mac save problem??
# V0.983    If program to large for memory - Error message implemented
# V0.991    Nasty Macro compile error fixed in cocas.py (V2.4)
# V0.992    Cut/Paste fixed bug if Ames is running!
# V0.993    Fixed CDM8 compiler problem in cocas.py and this file. Note, emulator not working
#           with new stack instructions yet.
# V0.994    Put Emulator class in seperate file/module
# V1.0      Remove Logisim Ames extensions - now to be coded in Logisim by D Bowes.
# V1.1      Fixed bugs in AMES I/F
# V1.2      Changed AMES to allow post Timeout load/submit.
# V1.3      AMES changes tested in labs and from home.
# V1.4      Support for saving object file and Cocol linker GUI added
# V1.41     Ames "New" bug fixed
# V1.5      In development. AMES Python2/3 compatibility fixed, 
#           Mousewheel bug fixed, EditorCodelist textsize bug fixed (Windows 10 problem!)
# V1.52     Various improvements to Editor and GUI.
#           Also most of Steve's bugs/suggestions inc. Selfmodifying code warning.
#           Implemented Harvard Arch option.
# V1.53     Bug fixes/Testing, 
#           GUI improvements - Layout, Search and goto Line functions.
# V1.6      Implement IO Panel(/Plugins?):
#           Basic IO: Buttons, LEDs, Hex/Dec displays and 16 Alha Char Display.
# V1.7      Bug fixes, Editor text bindings (Tab ->text block, Ctrl+Tab <- unTab.
#           Keyboard, terminal, 
# V1.8      Paged memory + interrupts. To do gRobotIF, LogisimIF, graphics??,

title = 'CocoIDE Extended V2.0'  # Should be updated to reflect version

try:
    # Python 3 tk
    import tkinter as tk
    from tkinter import ttk
    from tkinter import filedialog
    from tkinter import messagebox
    from tkinter import TclError
    import tkinter.font as font
except:
    # Python 2 tk (runs but not exhaustively tested!)
    import Tkinter as tk
    import ttk
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
    from Tkinter import TclError
    import tkFont as font

import argparse
import random
random.seed()
import time
import os
import sys
import signal
import io
from sys import platform
import collections as colls
import atexit
import codecs
import copy
import json
import subprocess
import pyclbr


# Language hightlight/syntax definitions
#from cdm8_asm_config import *
import cdm8_asm as cf
# Compiler/linker
import cocas
#import cocol
import cdm8_emu
import cdm8_io

# Get list of IOport classes

#ioPorts = pyclbr.readmodule('cdm8_io')
#del ioPorts["IOport"] # Do not need Super class name
#print(ioPorts)#debug
#ioPortnames = [ x.name for x in ioPorts.values()]
#print(ioPortnames)# debug

try:

    import sendfile as ames
    amesSession = True
    #print("Ames found")
except ImportError:
    print("No AMES library!")# debug
    amesSession = False

# ---------------------------------------------------------------------------
# Bundled-app support (PyInstaller / py2app .app and plain Windows .exe)
# When frozen, __file__ points inside the read-only bundle; keep user files
# (config, recent projects) next to the executable instead, and make sure
# bundled data files (standard.mlb, sendfile.py) can be located either way.
# ---------------------------------------------------------------------------
def _isFrozen():
    return getattr(sys, "frozen", False)

def appDir():
    """Directory of the running program (bundle dir when frozen)."""
    if _isFrozen():
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

def resPath(name):
    """Path to a data file that ships with the program."""
    if _isFrozen():
        # PyInstaller extracts datas into sys._MEIPASS; py2app into Resources
        for base in (getattr(sys, "_MEIPASS", None),
                     os.path.join(appDir(), "Resources"),
                     appDir()):
            if base:
                p = os.path.join(base, name)
                if os.path.exists(p):
                    return p
    return os.path.join(appDir(), name)

USERDIR = appDir() if _isFrozen() else os.path.expanduser("~")

def _macActivate():
    """Bring CocoIDE to the front on macOS and give it a proper application
    identity (menu-bar name, Dock icon, 'Quit CocoIDE'). Works both when run
    from source (via Cocoa-Python / python.org Tk frameworks) and inside a
    PyInstaller .app bundle."""
    try:
        from AppKit import (NSApplication, NSApp, NSApplicationActivationPolicyRegular,
                           NSThread)
        if not NSThread.isMainThread():
            return False
        if NSApp is None:
            NSApplication.sharedApplication()
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        NSApp.activateIgnoringOtherApps_(True)
        info = NSApplication.sharedApplication().infoDictionary()
        if info is not None:
            try:
                info["CFBundleName"] = "CocoIDE"
            except Exception:
                pass
        return True
    except Exception:
        return False


def _macAboutHandler(_sender=None):
    """Route the native 'About CocoIDE' menu item to our own dialog."""
    try:
        for w in tk.Toplevel.winfo_toplevel(tk)._default_root.winfo_children():
            pass
    except Exception:
        pass
    root = getattr(tk, "_cocoide_root", None)
    if root is not None and hasattr(root, "aboutDialog"):
        try:
            root.aboutDialog()
        except Exception:
            pass


def _macInstallAppMenu():
    """Build a real macOS application menu (About/Hide/Quit) so the app feels
    native instead of relying on Tk's minimal default menu."""
    try:
        from AppKit import (NSApplication, NSApp, NSMenu, NSMenuItem,
                            NSThread)
        if not NSThread.isMainThread():
            return False
        app = NSApplication.sharedApplication()
        main_menu = NSMenu.alloc().init()
        # Application submenu
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("CocoIDE", None, "")
        submenu = NSMenu.alloc().initWithTitle_("CocoIDE")
        ai = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "About CocoIDE", _macAboutHandler, "")
        submenu.addItem_(ai)
        sep1 = NSMenuItem.separatorItem()
        submenu.addItem_(sep1)
        hi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Hide CocoIDE", "hide:", "h")
        submenu.addItem_(hi)
        ho = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Hide Others", "hideOtherApplications:", "h")
        ho.setKeyEquivalentModifierMask_(0x100000 | 0x80000)  # Cmd+Opt
        submenu.addItem_(ho)
        su = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show All", "unhideAllApplications:", "")
        submenu.addItem_(su)
        submenu.addItem_(NSMenuItem.separatorItem())
        qi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit CocoIDE", "terminate:", "q")
        submenu.addItem_(qi)
        item.setSubmenu_(submenu)
        main_menu.addItem_(item)
        # Window submenu (needed for Minimize/Zoom that Tk expects)
        witem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Window", None, "")
        wsub = NSMenu.alloc().initWithTitle_("Window")
        mi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Minimize", "performMiniaturize:", "m")
        wsub.addItem_(mi)
        zi = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Zoom", "performZoom:", "")
        wsub.addItem_(zi)
        witem.setSubmenu_(wsub)
        main_menu.addItem_(witem)
        app.setMainMenu_(main_menu)
        try:
            app.setWindowsMenu_(wsub)
        except Exception:
            pass
        return True
    except Exception:
        return False
    #raise # debug

class CreateToolTip(object):
    """
    Create a tooltip for any given widget
    tk_ToolTip_class101.py
        gives a Tkinter widget a tooltip as the mouse is above the widget
        tested with Python27 and Python34  by  vegaseat  09sep2014
        www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
        Modified to include a delay time by Victor Zaccardo, 25mar16
        Modified by M L Walters July 2016
    """
    def __init__(self, widget, text='widget info', waittime=500):
        self.waittime = waittime    #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        # NOTE: this class is instantiated with no-arg after() callbacks, so
        # `event` is always None here -> position from the widget geometry.
        # (The old code used bbox("insert"), which raises TclError on Label
        # widgets like the memory cells - that was the source of empty/broken
        # hover boxes.)
        try:
            self.widget.winfo_toplevel().update_idletasks()
        except Exception:
            pass
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 6
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw,  justify='left',
                       background="#3a3a3c", foreground="#ffffff",
                       relief='flat', borderwidth=0, padx=10, pady=7,
                       font=("TkDefaultFont", 10),
                       wraplength = self.wraplength)
        # Get memory cell content (guard: widget text must be a hex byte)
        try:
            memValHex = self.widget["text"]
            memValDec = int(memValHex, 16)
        except Exception:
            self.hidetip()
            return
        if memValDec >= 32 and memValDec < 127:
            memValStr = "'"+chr(memValDec)+"'"
        elif memValDec == 0:
            memValStr = "NUL"
        else:
            memValStr = "..."

        if memValDec==0:
            memValBin="00000000"
        else:
            memValBin = format(memValDec,"08b")
        if memValDec<128:
            #signed int
            memValDecS=256+memValDec
        else:
            memValDecS = memValDec
        memValDec = format(memValDecS-256,"+04d")+" %03d" % memValDec
        self.text = "0x"+memValHex+"\n'"+memValStr+"'\n"+memValDec+"\n"+memValBin
        label.config(text=self.text)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()


class VerticalScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    """
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)            

        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        vscrollbar.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
        canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.TRUE)
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = tk.Frame(canvas)
        self.interior_id = canvas.create_window(0, 0, window=self.interior,
                                           anchor=tk.NW)
        
        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if self.interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=self.interior.winfo_reqwidth())
        self.interior.bind('<Configure>', _configure_interior)

        def _configure_IOcanvas(event):
            if self.interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(self.interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_IOcanvas)    
  

class CocoIDE(tk.Frame):

    def __init__(self, Emulator=None, master=None, filename=None, name='cocoide'):
        global amesSession # Flag for exam/test session capability
        tk.Frame.__init__(self, master=master, name=name)
        self.master.resizable(width=True, height=True)
        self.grid_rowconfigure(1, weight=1)     # For mainPanel to fill the window Horiz
        self.grid_columnconfigure(0, weight=1)  # For mainPanel to fill the window Vert??
        self.pack(fill=tk.BOTH, expand=1)#expand=1,
        self.TITLE = title
        self.master.title(self.TITLE)
        self.master.protocol("WM_DELETE_WINDOW",self.close_window) # Overide default quit
        self.master.config(cursor="watch") 
        
        ## Make global the CDM8 emulator
        self.Emu=Emulator
        self.Emu.parent = self # allows for callbacks to CocoIDE
        self.bind("<<checkInPorts>>", self.inputPortHandler)
        # Useful CDM8 (self.Emu) attributes/defaults
        # Emu.CVZN = ob0000 # SP Flags
        # Emu.memory = [n][0]*256 where n = pages
        # Emu.PC 
        # Emu.regs=[0,0,0,0]) # Registers (r0 to r3)
        # Emu.SP = 0 # Stack Pointer

        ## Class-wide variables
        self.file_name = "Untitled"
        self.file_path = None ##??
        self.changed = False
        ## Project / recent-files management (modern IDE style)
        self.projectPath = None       # currently open project folder (abs path)
        self.rootProjectPath = None   # top-level folder opened as project (VS Code style)
        self.expandedDirs = set()     # folders currently expanded in the tree browser
        self.recentProjects = []      # most recent first
        self.openedFiles = []         # abs paths of files opened this session
        self.configDir = os.path.join(USERDIR, ".cocoide")
        self.configFile = os.path.join(self.configDir, "config.json")
        self.startupFolder = None     # last folder used by Open/Save dialogs
        self.labelList=[]
        self.hidden=True
        self.memArray=[]
        self.running=False
        self.prevPC=0
        self.prevSP = 255
        self._lastSP = None            # previous SP shown (for pulse animation)
        ## Change-animation state (register/PS "pulse" on step execution)
        self._lastRegVals = [None]*4   # last shown r0-r3 values
        self._lastCVZNtxt = None       # last shown PS bit string
        self._pulseIds = {}            # widget -> pending after() id
        self.bpTagNames = []
        self.runDict = colls.OrderedDict()
        self.cliptext = ""
        self.runDict["00:"] = 0x00
        self.watches = [] # List of lists for watches and watch labels etc.
        self.cdm8ver=4 # CDM8 Instruction set Version. Default = 4?
        self.memChanged = []
        self.startIndex = "1.0"
        self.prevStr = ""
        self.pageDisp = False # No memory pages shown as default (simple display)
        self.bgColour = None # to restore bg colour when AMES exits.
        ## Interupt defaults
        self.interrupt = False 
        self.intVector = 0
        self.bind("<<genInterrupt>>", self.interruptHandler)
        
        ## IO Ports 
        # Get list of Port names from cdm8_io module
        self.ioPorts = pyclbr.readmodule('cdm8_io')
        del self.ioPorts["IOport"] # Do not need Super class name
        #print(self.ioPorts)#debug
        self.ioPortnames = [ x.name for x in self.ioPorts.values()]
        self.ioPortnames.sort()
        # List to hold dynamically instantiated IOPorts, tk objects and attributes
        self.IOPorts = [] 

        ## Fonts
        # macOS-friendly monospace default (Menlo is the system mono font)
        if platform == "darwin" and not cf.basefont:
            self.editorFontName = "Menlo"
        elif platform.startswith("win"):
            self.editorFontName = "Consolas"
        else:
            self.editorFontName = "Courier"
        # Scale text font size to screen size, unless not configured
        if self.winfo_screenwidth() > 1200 and cf.screenScaleMode == False:
            self.textsize=10
        else:
            screenheight=self.winfo_screenheight()/100
            screenwidth = self.winfo_screenwidth()/150
            #print (screenwidth, screenheight)#debug
            if screenwidth > screenheight:
                self.textsize = int(screenheight)
            else:
                self.textsize = int(screenwidth)
        #print("textsize=", self.textsize)
        
        ## Configure fonts
        self.defaultfont = font.nametofont("TkDefaultFont")
        self.defaultfont.configure(size=self.textsize)
        self.option_add("*Font", self.defaultfont)
        
        # Set default font for all widgets, etc.
        if cf.basefont:
            self.option_add("*Font", cf.basefont)
        else:
            self.option_add("*Font", self.defaultfont)
        
        # Save the default fixed font and set to size=self.textsize
        self.defaulttxtfont = font.Font(family=self.editorFontName, size=self.textsize)
        #self.editfont=font.Font(font="TkFixedFont")
        self.defaulttxtfont.configure(size=self.textsize)
        
        # Create bold and smaller versions of the default text window font
        self.boldfont = font.Font(font="TkFixedFont")#self.asstxt['font'])
        self.boldfont.config(weight='bold', size=self.textsize)
        self.smallfont = font.Font(font="TkFixedFont")#self.asstxt['font'])
        self.smallfont.config(size=self.textsize-2)
        self.smallboldfont = font.Font(font="TkFixedFont")#self.asstxt['font'])
        self.smallboldfont.config(size=self.textsize-2, weight="bold")
        # proportional UI font for hover tooltips (macOS help-book bubbles)
        try:
            self.tipfont = font.Font(family="TkDefaultFont", size=self.textsize-1)
        except Exception:
            self.tipfont = ("TkDefaultFont", self.textsize-1)
        
        # Ames stuff
        self.amesRunning = False#True
        self.homeDir = os.path.expanduser("~")
        self.timeleft = 0
        self.endtime = None
        self.testcount = None # None for normal AMES operation.
        self.arch=["vn"] * 8 # default = "vn" = Von Neuman, "hv" = Harvard
        ## Local variables
        #editorWidth = 50
        
        #### GUI Window Display
        ### Menus
        self.menubar = tk.Menu(self)
        if platform == "darwin":
            comkey = "Command-"
        else:
            comkey = "Ctrl+"
        # File menu, and add it to the menu bar
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="New", command=self.file_new, accelerator=comkey+"n")
        self.filemenu.add_command(label="Open...", command=self.file_open, accelerator=comkey+"o")
        if platform == "darwin":
            self.filemenu.add_command(label="Open Folder...", command=self.open_project_dialog,
                                      accelerator="Command-Shift-O")
        else:
            self.filemenu.add_command(label="Open Folder...", command=self.open_project_dialog,
                                      accelerator="Ctrl+Shift+O")
        self.filemenu.add_command(label="Save", command=self.file_save, accelerator=comkey+"s")
        self.filemenu.add_command(label="Save As...", command=self.file_save_as, accelerator=comkey+"S")
        self.filemenu.add_separator()
        self.recentMenu = tk.Menu(self.filemenu, tearoff=0)
        self.filemenu.add_cascade(label="Open Recent", menu=self.recentMenu)
        self._rebuildRecentMenu()
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Quick Open File\u2026", command=self.showQuickOpen,
                                  accelerator=comkey+"p")
        self.filemenu.add_command(label="Command Palette\u2026", command=self.showCmdPalette,
                                  accelerator=(comkey+"⇧P") if platform == "darwin" else "Ctrl+Shift+P")
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Close File", command=self.file_close)
        self.filemenu.add_command(label="Quit", command=self.close_window, accelerator=comkey+"q")#self.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu, accelerator=comkey+"f")

        # Project menu - work with a task folder (assignment directories etc.)
        self.projmenu = tk.Menu(self.menubar, tearoff=0)
        self.projmenu.add_command(label="Open Folder as Project...", command=self.open_project_dialog,
                                  accelerator="Cmd+Shift+O")
        self.projmenu.add_command(label="New File in Project", command=self.new_file_in_project,
                                  accelerator="Cmd+Alt+N")
        self.projmenu.add_command(label="Reveal in Finder", command=self.reveal_project_folder)
        self.projmenu.add_command(label="Open Terminal Here", command=self.open_terminal_here)
        self.projmenu.add_separator()
        self.projmenu.add_command(label="Close Project", command=self.close_project)
        self.menubar.insert_cascade(1, label="Project", menu=self.projmenu)
        
        # Edit menu
        self.editmenu = tk.Menu(self.menubar, tearoff=0)
        self.editmenu.add_command(label="Undo", command=self.undo, accelerator=comkey+"z")
        self.editmenu.add_command(label="Redo", command=self.redo, accelerator=comkey+"y")
        self.editmenu.add_command(label="Cut", command=self.cut, accelerator=comkey+"t")
        self.editmenu.add_command(label="Copy", command=self.copy, accelerator=comkey+"c")
        self.editmenu.add_command(label="Paste", command=self.paste, accelerator=comkey+"p")
        self.editmenu.add_command(label="Select All", command=self.selectall, accelerator=comkey+"a")
        self.editmenu.add_separator()
        # Auto-completion toggle (VS Code / PyCharm style suggestions)
        self.menuEdit = self.editmenu   # kept for compatibility with AC code
        self.acMenuItem = "Auto-completion   ✔"
        self.editmenu.add_command(label=self.acMenuItem, command=self.toggleAutocomplete,
                                  accelerator=comkey+"space")
        self.editmenu.add_command(label="Trigger Completion", command=self.acTrigger,
                                  accelerator=comkey+"shift+space")
        self.editmenu.add_separator()
        self.txtmenu = tk.Menu(self.editmenu, tearoff=0)
        self.txtmenu.add_radiobutton(label="V Large", command=lambda: self.changeTextSize(22))
        self.txtmenu.add_radiobutton(label="Large", command=lambda: self.changeTextSize(12))
        self.txtmenu.add_radiobutton(label="Default", command = lambda: self.changeTextSize(10))
        self.txtmenu.add_radiobutton(label="Small", command = lambda: self.changeTextSize(8))
        self.menubar.add_cascade(label="Edit", menu=self.editmenu)
        self.editmenu.add_cascade(label="Text Size", menu=self.txtmenu)
        
        # Emulator menu
        self.emumenu = tk.Menu(self.menubar, tearoff=0)
        self.emumenu.add_command(label="Compile/Reset", command=self.compileText,
                                 accelerator="Cmd+B")
        self.emumenu.add_command(label="Run", command=self.runProg, accelerator="Cmd+R")
        self.emumenu.add_command(label="Step", command=lambda: self.stepOnce())
        self.emumenu.add_command(label="Toggle BP", command=self.toggleBP, accelerator="Cmd+F9")
        self.emumenu.add_command(label="Clear Breakpoints", command=self.clearBPs)
        self.emumenu.add_command(label="Save Image", command=self.saveImage)
        self.emumenu.add_command(label="Save Object File", command=self.saveObjFile)
        self.emumenu.add_command(label="Cocol CDM8 Linker", command=self.cocolnk)
        self.emumenu.add_separator()
        self.emumenu.add_command(label="Arch = Von Neuman ", command=self.toggleArch)
        self.emumenu.add_command(label="Paged Memory     ", command=self.toggleMemPageDisp)
        self.emumenu.add_command(label="Shadow SPs      ✔", command=self.setShadowSP)
        self.menubar.add_cascade(label="CDM8", menu=self.emumenu)
        # Help Menu
        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="Manual", command=self.helpwin)
        self.helpmenu.add_command(label="About CocoIDE", command=self.aboutDialog)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)
        # Display the menu
        self.master.config(menu=self.menubar)
        
        ### Buttonbar
        buttonBar = tk.Frame(self, name="buttonbar", height=40)#, border=1)#, bg="red")
        buttonBar.grid(row=0,column=0, columnspan =4, sticky="ew")

        ## Shortcut buttons
        # Editor
        self.editButtons = tk.Frame(buttonBar)
        self.editButtons.pack(side=tk.LEFT, fill=tk.BOTH)
        # Modern minimal toolbar: New / Open (files & folders menu) / Save / Save As / Quit.
        # Row 0: New / Open... / Save / Save As... / Quit (one per grid cell)
        self.newButton = tk.Button(self.editButtons, text="+ New", command=self.file_new)
        self.newButton.grid(row=0, column=0, sticky="ns", padx=1)
        self.openButton = tk.Button(self.editButtons, text="Open...")
        self.openButton.grid(row=0, column=1, sticky="ns", padx=1)
        self.openButton.bind("<Button-1>", self.show_open_menu)
        self.saveButton = tk.Button(self.editButtons, text="Save", command=self.file_save)
        self.saveButton.grid(row=0, column=2, sticky="ns", padx=1)
        self.saveAsButton = tk.Button(self.editButtons, text="Save As...")
        self.saveAsButton.grid(row=0, column=3, sticky="ns", padx=1)
        self.saveAsButton.bind("<Button-1>", lambda e: self.file_save_as())
        self.exitButton = tk.Button(self.editButtons, text="Quit", command=self.close_window)
        self.exitButton.grid(row=0, column=4, sticky="ns", padx=1)

        # Row 1: Find box + Search | Go-to-line box.
        # (Previously the "Search" button was grid'ed into the SAME cell as
        # "+ New" and "Line" overlapped the spacer next to "Quit" - buttons
        # printed on top of each other at small window widths.)
        self.searchBox = tk.Entry(self.editButtons, width=10, fg="grey")
        self.searchPlaceholder = "Find..."
        self.searchBox.insert(0, self.searchPlaceholder)
        self.searchBox.bind("<FocusIn>", self._searchFocusIn)
        self.searchBox.bind("<FocusOut>", self._searchFocusOut)
        self.searchBox.bind("<Return>", self.searchText)
        self.searchBox.bind("<Button-3>", self.searchText)
        self.lineBox = tk.Entry(self.editButtons, width=5)
        self.lineBox.bind("<Return>", self.gotoLine)
        self.lineBox.bind("<Button-3>", self.gotoLine)
        tk.Label(self.editButtons, text="Go:").grid(row=1, column=0, sticky="e")
        self.searchBox.grid(row=1, column=1, columnspan=2, sticky="ew")
        tk.Button(self.editButtons, text="Search", command=self.searchText).grid(row=1, column=3, sticky="ew")
        self.lineBox.grid(row=1, column=4, sticky="ew")
        tk.Button(self.editButtons, text="Line", command=self.gotoLine).grid(row=1, column=5, sticky="w")

        ## CDM8 Emulator Buttons
        # Cludge for Mac button display!!!
        if platform == "darwin":
            self.saveImageButton = tk.Button(buttonBar, text="Save Image ",
                height=3, command=self.saveImage)
        else:
            self.saveImageButton = tk.Button(buttonBar, text="Save Mem\nImage ", 
                height=3, command=self.saveImage)
        
        self.saveImageButton.pack(side=tk.RIGHT)
        self.spacer=tk.Label(buttonBar, text="", width=2)
        self.spacer.pack(side=tk.RIGHT)
        self.speedScale = tk.Scale(buttonBar, from_=3, to=0, orient=tk.HORIZONTAL,
            showvalue=0, width=18, label="Step <--> Fast")
        self.speedScale.set(1)
        self.speedScale.pack(side=tk.RIGHT)
        self.runStopButton = tk.Button(buttonBar, text="Run ", height=3, padx=6,
            command=self.runProg)
        self.runStopButton.pack(side=tk.RIGHT)

        self.runFromFrame = tk.Frame(buttonBar)
        self.runFromFrame.pack(side=tk.RIGHT)
        self.runFromLabel = tk.Label(self.runFromFrame, text="Run From")
        self.runFromLabel.pack(side=tk.TOP)
        self.runFrom = tk.StringVar()
        self.runFrom.set("00:")
        
        # Create Style for RunSelect dropdown select
        style = ttk.Style()
        style.map('TCombobox', fieldbackground=[('readonly','white')])
        style.map('TCombobox', selectbackground=[('readonly', 'white')])
        style.map('TCombobox', selectforeground=[('readonly', 'black')])
        
        self.runEPSelect = ttk.Combobox(self.runFromFrame, textvariable=self.runFrom,
            state='readonly', width=6, foreground="black", background="white")
        self.runEPSelect.bind('<<ComboboxSelected>>',self.initPC) # reset Program Counter
        self.runEPSelect['values'] = ['00:']
        self.runEPSelect.current(0)
        self.runEPSelect.pack(side=tk.TOP)
        
        # Cludge for Mac/OSX
        if platform == "darwin":
            compileButton = tk.Button(buttonBar, text="Compile/Reset", command=self.compileText, height=3)
        else:
            compileButton = tk.Button(buttonBar, text="Compile\nReset", command=self.compileText, height=3, padx=6)
        compileButton.pack(side=tk.RIGHT)
        
        # Staus/Run time warning/Error pane
        self.statusMsg=tk.Label(buttonBar, text="", width=20, fg="red", bg="white", 
            height=3,  relief="sunken", border=3, )#int(self.textsize)*2)padx=8,
        self.statusMsg.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)
        
        # AMES extensions
        if amesSession:
            #self.spacer0=tk.Label(buttonBar, text="", width=1)
            #self.spacer0.pack(side=tk.LEFT)
            self.amesFrame=tk.Frame(buttonBar, relief="flat", padx=6)
            self.amesFrame.pack(side=tk.LEFT, expand=0, fill=tk.Y)
            self.amesButton = tk.Button(self.amesFrame, text="Start ", command=self.amesStart)#, height=2)
            self.amesButton.grid(row = 1, column=0, sticky="w")#, rowspan=1)
            self.pinVar = tk.IntVar()
            self.pinVar.set("")
            self.pinEntry = tk.Entry(self.amesFrame, show="*", text=self.pinVar, width = 4)
            self.pinEntry.grid(row=1, column=1, padx=2, sticky="w")
            self.pinEntry.bind("<Return>", self.amesStart)
            self.pinLabel = tk.Label(self.amesFrame, text = "AMES          PIN?",  anchor="w", width=18)
            self.pinLabel.grid(row=0, column=0, columnspan=2, sticky="ws")#, pady=3)
            #self.amesStatus = tk.Label(self.amesFrame, text="",  height=3, 
            #    width=25, fg="red", padx=6)#, wrap=tk.WORD)width=25,
            #self.amesStatus.grid(row=0, column=2, rowspan=2, sticky="w")
        
        ## Status bar (below the main panel): cursor position, file type, project
        self.statusbar = tk.Frame(self, name="statusbar", bg="#e8e8e8", height=22)
        # NOTE: row 3, not row 2 - mainPanel occupies row 1; sharing a grid row
        # made the bar overlap/clip the bottom of the panels above it.
        self.statusbar.grid(row=3, column=0, sticky="ew")
        self.statusbar.grid_propagate(False)
        self.cursorLabel = tk.Label(self.statusbar, text="Ln 1, Col 1", anchor="w",
                                    bg="#e8e8e8", font=self.smallfont, padx=6)
        self.cursorLabel.pack(side=tk.RIGHT)
        self.fileKindLabel = tk.Label(self.statusbar, text="CDM8 Assembly", anchor="e",
                                      bg="#e8e8e8", font=self.smallfont, padx=6)
        self.fileKindLabel.pack(side=tk.RIGHT)
        self.projStatusLabel = tk.Label(self.statusbar, text="No folder", anchor="w",
                                        bg="#e8e8e8", font=self.smallfont, padx=6)
        self.projStatusLabel.pack(side=tk.LEFT)
        # NOTE: asstxt is created later in this __init__ (main panel section);
        # the CaretMove bindings are attached there, not here.

        ### Create mainPanel under buttonBAr
        mainPanel = tk.Frame(self, name='cocoidewin')#, bg="yellow")
        self.mainPanel = mainPanel
        mainPanel.grid(row=1,column=0, sticky="nsew")
        mainPanel.rowconfigure(0, weight=1)     # Allow text and mcode windows to scale vertically
        mainPanel.columnconfigure(1, weight=1)  # Allow text and watch windows to scale horizontally
        
        ## Create the assembly code editor panel
        # Text editor with scrollbar and syntax highlighting
        
        # Text Line Number pane
        self.lntext = tk.Text(mainPanel, width = 4,
                padx = 4, highlightthickness = 0,
                takefocus = 0, bd = 0, background = 'lightgrey',
                foreground = 'black', font=self.boldfont,
                yscrollcommand=self.yscroll3)
        self.lntext.grid(row=0, column=0, sticky="ns")
        self.lntext.config(state="disabled")
        self.lntext.bind('<MouseWheel>', lambda e: "break")
        
        # Text editor window
        self.asstxt = tk.Text(mainPanel, wrap=tk.NONE,font=self.defaulttxtfont,
                                undo=True, yscrollcommand=self.yscroll1,
                                autoseparators=True, maxundo=-1, width=40)#, height=10,) height=editorHeight,
        self.asstxt.grid(row=0, column=1, sticky="nsew")
        # Scroll bars
        self.vscroll = ttk.Scrollbar(mainPanel, orient=tk.VERTICAL, command=self.yview)
        self.vscroll.grid(row=0, column=2, sticky="ns")
        txtHscroll = ttk.Scrollbar(mainPanel, orient=tk.HORIZONTAL, command=self.asstxt.xview)
        txtHscroll.grid(row=1, column=0,columnspan=2, sticky="ew")
        self.asstxt.config(xscrollcommand=txtHscroll.set)

        # VS Code style error strip (red ticks on the scrollbar gutter).
        # Created after asstxt exists; placed over the editor's right edge.
        try:
            self._makeErrStrip()
        except Exception:
            pass
        
        # Status-bar cursor position updates (asstxt exists only from here on)
        self.asstxt.bind("<<CaretMove>>", self._updateStatusCursor, add=True)
        self.asstxt.bind("<ButtonRelease-1>", self._updateStatusCursor)
        self.asstxt.bind("<KeyRelease>", self._updateStatusCursor, add=True)

        # Editor - other configurations
        self.asstxt.edit_separator()
        #print("**\n",self.asstxt.bindtags())#debug
        
        # Editor formatting options
        tab_width = self.defaulttxtfont.measure('OOOO')  # compute desired width of tabs
        self.asstxt.config(font=self.boldfont, tabs=tab_width, tabstyle="wordprocessor")#"1.0c 2.0c 3.0c")#tab_width,))

        ## Create the machine code memory list display panel
        # The right-hand bottom area is a TAB STRIP (VS Code style): the fixed
        # "Machine Code" listing tab plus one closable tab per file opened from
        # the project tree (asm/txt listings shown inline; PDFs and other types
        # open in the system viewer but still get a tab). Handy for demoing a
        # task brief next to the code.
        mcodeTabs = ttk.Frame(mainPanel)
        mcodeTabs.grid(row=0, column=3, sticky="nsew")
        mcodeTabs.rowconfigure(1, weight=1)
        mcodeTabs.columnconfigure(0, weight=1)
        self.mcodeTabBar = tk.Frame(mcodeTabs, bg="#e6e6e6", height=24)
        self.mcodeTabBar.grid(row=0, column=0, sticky="ew")
        self.mcodeTabBar.grid_propagate(False)
        self.mcodeTabStack = tk.Frame(mcodeTabs)   # switchable content frames
        self.mcodeTabStack.grid(row=1, column=0, sticky="nsew")
        self.mcodeTabStack.rowconfigure(0, weight=1)
        self.mcodeTabStack.columnconfigure(0, weight=1)

        mcode_frame = ttk.Frame(self.mcodeTabStack)
        mcode_frame.grid(row=0, column=0, sticky="nsew")
        self._mcodeFrame = mcode_frame
        self.mcode_list=tk.Text(mcode_frame, yscrollcommand=self.yscroll2, width=25,
                                wrap=tk.NONE, font=self.defaulttxtfont)#, height=editorHeight)
        mcodeHscroll = ttk.Scrollbar(mcode_frame, orient=tk.HORIZONTAL, command=self.mcode_list.xview)
        mcodeHscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.mcode_list.config(xscrollcommand=mcodeHscroll.set)

        # Tab state: first entry is the fixed Machine Code tab
        self.viewTabs = [("__mcode__", None)]     # (key, filepath-or-None)
        self.activeViewTab = "__mcode__"
        self.tabButtons = {}                      # key -> (label widget, frame)
        self._fileTabFrames = {}                  # filepath -> frame
        self._rebuildMcodeTabBar()                        
                                
        self.mcode_list.bind("<Key>", lambda e: "break") # Disable editing
        self.mcode_list.pack(fill=tk.BOTH, expand=1)

        # --- Editor tab bar (VS Code style multiple open files) ---
        self.editorTabs = [{"path": None, "name": "Untitled", "dirty": False}]
        self.activeTab = 0
        self._tabSwapGuard = False
        self._savedBuffers = {}      # path -> (content, insert-index) while inactive
        self.editorTabBar = tk.Frame(mainPanel, bg="#e6e6e6", height=25)
        self.editorTabBar.grid(row=2, column=0, columnspan=3, sticky="ew")
        self.editorTabBar.grid_propagate(False)
        self.asstxt.bind("<<Modified>>", self._onTextModifiedFlag)

        ## Bind editor keys
        self.bindKeys()

        # Robustness: some Tk builds (e.g. python.org Python 3.14 + Tk) lack
        # certain keysyms like BracketLeft/BracketRight -> bind those
        # block-indent shortcuts safely, never crashing startup over them.
        try:
            self._bindBlockIndentShortcuts()
        except Exception as _e:
            print("block-indent shortcuts skipped:", _e)

        # Modern editor niceties: current-line highlight & mouse wheel scrolling
        self.asstxt.config(insertbackground="red")
        self.asstxt.tag_configure("currentline", background="#f0f0f0")
        self.asstxt.bind("<<CaretMove>>", self._markCurrentLine)
        self._bindMouseWheel(self.asstxt)
        self._bindMouseWheel(self.mcode_list)
        # (watchList is created later in this __init__; wheel-bound there)

        # Autocomplete popup state (modern IDE style inline suggestions)
        self.acListbox = None      # tk.Listbox popup, created on demand
        self.acWordStart = None    # text index where the completed word begins
        self.acPrefix = ""         # prefix typed so far
        self.acWords = []          # current candidate list
        self.acAfterId = None      # id of the debounced KeyRelease handler
        self.acIgnored = False     # True while we modify the buffer ourselves
        self.acEnabled = True      # toggled via Edit menu / config (restored in loadConfig)

        # Autocomplete key wiring: navigation/accept keys are handled by _acKeyFilter
        # (<Key> binding added further below); Tab is intercepted first so that it
        # accepts a suggestion when the popup is visible and indents otherwise.
        # NOTE: these are bound WITHOUT add="+" on purpose. Tk's built-in Text
        # class bindings for <Tab>/<Return> (insert tab / newline) run AFTER
        # widget bindings only if the handler returns None; our handlers return
        # "break" when they accept a completion, which stops that chain. With
        # add="+" an earlier binding existed, Tk's chained script could swallow
        # the "break" and insert the character anyway - the popup appeared to
        # do nothing on Tab/Enter.
        self.asstxt.bind("<Tab>", self._acTabHandler)
        # Return must be a real method binding, not a lambda that inserts
        # "\n" as its *return value*: Tk treats a returned string as a Tcl
        # script to EVAL (like "break"), so the old lambda inserted the letter
        # 'n' instead of a newline. acAccept returns "break" when it consumed
        # the key on a visible popup; returning None here lets Tk's built-in
        # Text class binding insert the newline normally afterwards.
        self.asstxt.bind("<Return>", self._returnHandler)
        # Explicit widget-level bindings for popup navigation. The <Key> filter
        # alone is not enough: Tk's built-in Text bindings for Up/Down/Escape
        # run first and move the caret / close dialogs before we can "break"
        # them (bindtags order), so the popup would never be navigable.
        self.asstxt.bind("<Up>", lambda e: self.acMoveSel(-1))
        self.asstxt.bind("<Down>", lambda e: self.acMoveSel(1))
        # Escape: close the popup first (clearEditorHighlights below is bound
        # with add="+" and only runs when acCancel returns None, i.e. closed).
        self.asstxt.bind("<Escape>", self.acCancel)
        # Autocomplete trigger (VS Code style). Use lowercase 'space' keysym
        # and _safeBind: some Tk builds (e.g. python.org 3.14) don't know
        # the capitalized "Space" keysym and would crash startup otherwise.
        if platform == "darwin":
            self._safeBind(self, "<Command-space>", lambda e: self.acTrigger())
            self._safeBind(self, "<Command-Shift-space>", lambda e: self.acTrigger())
        else:
            self._safeBind(self, "<Control-space>", lambda e: self.acTrigger())
            self._safeBind(self, "<Control-Shift-space>", lambda e: self.acTrigger())
        # Cmd+Shift+P / Ctrl+Shift+P: command palette (VS Code style)
        if platform == "darwin":
            self._safeBind(self, "<Command-Shift-p>", lambda e: self.showCmdPalette())
        else:
            self._safeBind(self, "<Control-Shift-p>", lambda e: self.showCmdPalette())
        self.asstxt.bind("<FocusOut>", lambda e: self.acHide())


        ## Bind mcode keys
        self.mcode_list.bind("<Control-T>", self.toggleBP)
        self.mcode_list.bind("<Control-t>", self.toggleBP)
        #if platform == "darwin":
        self.mcode_list.bind("<Command-T>", self.toggleBP)
        self.mcode_list.bind("<Command-t>", self.toggleBP)


        # Bind keys for highlighting (autocomplete hooks are appended to the same
        # <Key>/<KeyRelease> sequences so both run on every keystroke)
        self.asstxt.bind("<Key>", self.keydisable, add="+")
        self.asstxt.bind("<Key>", self._acKeyFilter, add="+")
        self.asstxt.bind('<KeyRelease>', self.highlighter, add="+")
        self.asstxt.bind('<KeyRelease>', self.acSchedule, add="+")

        ## Bind mouse events
        
        # Disable Mouse Wheel button (2)
        self.asstxt.bind("<ButtonRelease-2>", lambda e: "break")
        #self.asstxt.bind("<Double-Button-2>", lambda e: "break")
        self.asstxt.bind("<Double-ButtonRelease-2>", lambda e: "break")
        #self.asstxt.bind("<Triple-Button-2>", lambda e: "break")
        self.asstxt.bind("<Triple-ButtonRelease-2>", lambda e: "break")
        self.mcode_list.bind("<ButtonRelease-2>", lambda e: "break")
        #self.asstxt.bind("<Double-Button-2>", lambda e: "break")
        self.mcode_list.bind("<Double-ButtonRelease-2>", lambda e: "break")
        #self.asstxt.bind("<Triple-Button-2>", lambda e: "break")
        self.mcode_list.bind("<Triple-ButtonRelease-2>", lambda e: "break")
        
        # Pop up edit menu
        self.asstxt.bind("<Button-3>",self.popmenu)
        
        # Toggle BreakPoint
        self.mcode_list.bind("<Button-3>", self.toggleBP)# Confusing?
        self.mcode_list.bind('<Double-Button-1>', self.toggleBP)

        ## Create and add Watch panel
        watchPanel = tk.Frame(mainPanel, name="watchpanel")#, bg="blue")#,  height=80)#,  background="red") #width=570,
        # start at column 1 so the PROJECT sidebar (column 0) never covers
        # the Memory Watches list - previously this spanned from column 0 and
        # the watches were hidden behind the file tree.
        watchPanel.grid(row=2, column=1, columnspan=2, sticky="nsew")
        watchPanel.columnconfigure(0, weight=1)
        #watchPanel.columnconfigure(1, weight=1) 
        # And contents
        watchTitle = tk.Label(watchPanel, text="Memory Watches", relief="raised",  padx=0, font=self.boldfont)#, width=51)
        watchTitle.grid(row=0, column=0, columnspan=2, sticky="ew")#pack(side=tk.TOP, fill=tk.X)

        watchHeader = tk.Label(watchPanel, text="Adr:  Label:                  Content ")
        watchHeader.grid(row=1, column=0, columnspan=2, sticky="w")#pack(side=tk.TOP, fill=tk.X, anchor="w")
        
        self.watchList = tk.Text(watchPanel, height=9, bg="white", font=self.boldfont,  wrap=tk.NONE)#,width=editorWidth-2, text='data: OE: "Hello there"')
        self.watchList.bind("<Key>", lambda e: "break") # Disable editing
        self.watchList.grid(row=2, column=0, columnspan=2, sticky="nsew")
        watchScrollY = tk.Scrollbar(watchPanel, orient=tk.VERTICAL, command=self.watchList.yview)
        self.watchList.config(yscrollcommand=watchScrollY.set)
        watchScrollY.grid(row=2, column=1, sticky="nse")
        watchScrollX = tk.Scrollbar(watchPanel, orient=tk.HORIZONTAL, command=self.watchList.xview)
        self.watchList.config(xscrollcommand=watchScrollX.set)
        watchScrollX.grid(row=3, column=0, columnspan=2, sticky="sew")

        # Disable Mouse Wheel button (2)
        self.watchList.bind("<Button-2>", lambda e: "break")
        self.watchList.bind("<ButtonRelease-2>", lambda e: "break")
        self.watchList.bind("<Double-ButtonRelease-2>", lambda e: "break")
        self.watchList.bind("<Double-Button-2>", lambda e: "break")
        self.watchList.bind("<Triple-Button-2>", lambda e: "break")
        self.watchList.bind("<Triple-ButtonRelease-2>", lambda e: "break")
        self._bindMouseWheel(self.watchList)   # wheel-scrolling, now that it exists
        
        
        self.mcode_list.bind("<Double-ButtonRelease-2>", lambda e: "break")
        #self.asstxt.bind("<Triple-Button-2>", lambda e: "break")
        self.mcode_list.bind("<Triple-ButtonRelease-2>", lambda e: "break")
        
        
        ## Create and add Register panel
        self.regPanel = tk.Frame(mainPanel, name="regpanel",  height=80, padx=0, relief="sunken", bd=2)#,  background="blue") #width=300,
        self.regPanel.grid(row=2, column=3, sticky="nsew")#pack(side=tk.LEFT, fill=tk.Y)
        regTitle = tk.Label(self.regPanel, text="Registers", font=self.boldfont)
        regTitle.grid(row=0, column=1, columnspan=2)
        
        # Program counter
        self.pcLab = tk.Label(self.regPanel, text="^ PC  ", width=6, font=self.boldfont, padx=3)
        self.pcLab.grid(row=1, column=0, sticky="w")#, columnspan=2)
        self.pcLabVal = tk.Label(self.regPanel, text="00",width=6, bg=cf.PCcolour, relief="sunken", padx=3, font=self.defaulttxtfont)
        self.pcLabVal.grid(row=2, column=0, sticky="w")
        self.pcLabVal.bind("<Enter>", lambda e: self._showTip(self.pcLabVal, self.tipPC, e))
        self.pcLabVal.bind("<Leave>", self._hideTip)

        # PS register (CVZN etc.)
        
        self.CVZN_Lab = tk.Label(self.regPanel, text="PS: I Page CVZN",width=15, font=self.boldfont)
        self.CVZN_Lab.grid(row=1, column=1, columnspan=2)#,sticky="e")#, columnspan=2)
        self.CVZN_Val = tk.Label(self.regPanel, text="0 000 0000", bg="white", width=15, relief="sunken", font=self.defaulttxtfont)
        self.CVZN_Val.grid(row=2, column=1, columnspan=2)#, sticky="e")#, columnspan=2)
        # macOS-style tooltips: live decode of the PS (status) register bits
        self.CVZN_Lab.bind("<Enter>", lambda e: self._showTip(self.CVZN_Lab, self.tipPS, e))
        self.CVZN_Lab.bind("<Leave>", self._hideTip)
        self.CVZN_Val.bind("<Enter>", lambda e: self._showTip(self.CVZN_Val, self.tipPS, e))
        self.CVZN_Val.bind("<Leave>", self._hideTip)

        # Stack Pointer
        self.spLab = tk.Label(self.regPanel, text=" SP  ",width=7, font=self.boldfont)
        self.spLab.grid(row=1, column=3)#, columnspan=2)
        self.spVal = tk.Label(self.regPanel, text="00", bg=cf.SPcolour, width=7, relief="sunken", font=self.defaulttxtfont)
        self.spVal.grid(row=2, column=3)#, columnspan=2)
        self.spVal.bind("<Enter>", lambda e: self._showTip(self.spVal, self.tipSP, e))
        self.spVal.bind("<Leave>", self._hideTip)


        spacer1= tk.Label(self.regPanel, text="")#, height=1)
        spacer1.grid(row=3, column=0)
        #Registers
        self.regLabs = [0]*4
        self.regHexs = [0]*4
        self.regStrs = [0]*4
        self.regDecs = [0]*4
        self.regBins = [0]*4
        for index in range(4):
            self.regLabs[index] = tk.Label(self.regPanel, text="r"+str(index), width=8, padx=5, fg="blue", font=self.boldfont)
            self.regLabs[index].grid(row=4, column=index, sticky="n")
            self.regLabs[index].bind("<Enter>", lambda e, i=index: self._showTip(self.regLabs[i], lambda: self.tipReg(i), e))
            self.regLabs[index].bind("<Leave>", self._hideTip)
            self.regHexs[index] = tk.Label(self.regPanel, text="0x00", width=8, bg="white", relief="sunken",font=self.defaulttxtfont)
            self.regHexs[index].grid(row=5, column=index, sticky="n")
            self.regStrs[index] = tk.Label(self.regPanel, text="NUL", width=8, bg="white", relief="sunken",font=self.defaulttxtfont)
            self.regStrs[index].grid(row=6, column=index, sticky="n")
            self.regDecs[index] = tk.Label(self.regPanel, text="+000 000", width=8, bg="white", relief="sunken",font=self.defaulttxtfont)
            self.regDecs[index].grid(row=7, column=index, sticky="n")
            self.regBins[index] = tk.Label(self.regPanel, text="00000000", width=8, bg="white", relief="sunken",font=self.defaulttxtfont)
            self.regBins[index].grid(row=8, column=index, sticky="n")

        ### Create the machine panel
        self.mcPanel = tk.Frame(mainPanel)#, bg="blue")
        #mcPanel.pack(side=tk.RIGHT, fill=tk.Y)#, expand=1)
        self.mcPanel.grid(row=0, column=5, sticky="nsew", rowspan=5)#, columnspan=4)
        self.mcPanel.grid_rowconfigure(index=4, weight=1)
        
        ## Memory Page select frame
        self.memPageFrame = tk.Frame(self.mcPanel)
        self.memPageFrame.grid(row=0, column=0, sticky="ew")
        self.memPageFrame.grid_remove()
        self.memPageVar = tk.IntVar()
        self.memPageVar.set(0)
        self.pageLabel = tk.Label(self.memPageFrame, text="Memory: Page:")
        self.pageLabel.pack(side=tk.LEFT)
        self.pageRadButtons = []
        for n in range(8):
            self.pageRadButtons.append(tk.Radiobutton(self.memPageFrame, text=str(n),
                variable=self.memPageVar, value=n, indicatoron=0, width=3, padx=4,
                command= lambda : self.dispAllMemory(page=self.memPageVar.get())))
            self.pageRadButtons[-1].pack(side=tk.LEFT) 
        
        ## Create the Advanced notebook memory panel
        self.emuNb = ttk.Notebook(self.mcPanel, name='notebook')#, width=420)
        # extend bindings to top level window allowing
        #   CTRL+TAB - cycles thru tabs
        #   SHIFT+CTRL+TAB - previous tab
        #   ALT+K - select tab using mnemonic (K = underlined letter)
        self.emuNb.enable_traversal()
        self.emuNb.grid(row=1, column=0)#, sticky="nsew")#(columnspan=2,
        #self.emuNb.pack(side=tk.TOP, expand=0, padx=5, pady=2)# 

        # Create machine memory frame(s) and add to notebook panel
        self.mem_frame=[[],[]]
        for n in range(len(self.mem_frame)):
            self.mem_frame[n] = ttk.Frame(self.emuNb)
            self.emuNb.add(self.mem_frame[n])
    
        self.setArch(self.arch[0], page=0) 
        
        # Also populates mem panel(s) and tooltips

        ## Add I/O Port display area to mcPanel
        # I/O Title Header
        self.IOHeader = tk.Frame(self.mcPanel, relief="raised", borderwidth=1)
        #self.IOHeader.pack(side=tk.TOP, fill=tk.X, padx=5, pady=3)
        self.IOHeader.grid(row=2, column=0)
        self.IOAdrLabel =  tk.Label(self.IOHeader, text="Addr.")
        self.IOAdrLabel.pack(side=tk.LEFT)
        self.IOLabel = tk.Label(self.IOHeader, font=self.boldfont, text="               I/O Ports")
        self.IOLabel.pack(side=tk.LEFT)
        # IO ADD/DEL IO port Buttons
        self.portVar = tk.StringVar()
        self.portVar.set(self.ioPortnames[0])
        self.addPortSelect = ttk.Combobox(self.IOHeader, textvariable=self.portVar,
            state='readonly', width=15)
        self.addPortSelect.pack(side=tk.RIGHT)
        self.addPortSelect['values']= self.ioPortnames
        self.addPortSelect.bind('<<ComboboxSelected>>', self.addport)
        self.addPortSelect.bind('<Return>', self.addport)
        self.portVarLabel = tk.Button(self.IOHeader, text="+", command=self.addport, width=1)
        self.portVarLabel.pack(side=tk.RIGHT)
        
        ## I/O Panel with canvas and scrollbar
        # Based on code by novel-yet-trivial/VerticalScrolledFrame.py, 2017
        self.IOPanel = tk.Frame(self.mcPanel)#, bg="red")#.pack(fill=tk.BOTH, expand=1)
        #self.IOPanel.pack(side=tk.TOP, fill=tk.BOTH, expand=1, padx=5)#, pady=1)
        self.IOPanel.grid(row=4, column=0, sticky="nsew")
        self.IOscroll = ttk.Scrollbar(self.IOPanel, orient=tk.VERTICAL)#, command=self.IOcanvas.yview)
        self.IOscroll.pack(side=tk.RIGHT, fill=tk.Y, expand=0)#row=0, column=2, sticky="ns")
        self.IOcanvas = tk.Canvas(self.IOPanel, yscrollcommand=self.IOscroll.set)# bg="yellow")
        self.IOcanvas.pack(side=tk.TOP, fill=tk.BOTH, padx=2, pady=2, expand=1)
        self.IOscroll.config(command=self.IOcanvas.yview)
        self.IOcanvas.yview_moveto(0)
        #self.IOcanvas.xview_moveto(0)#?? 
        
        ## Create a window on the canvas for the IOFrame 
        self.IOFrame = tk.Frame(self.IOcanvas)#, bg="purple")
        self.IOFrame_win = self.IOcanvas.create_window(0, 0, window=self.IOFrame,anchor=tk.NW)
        
        ## Various event bindings to update IOFrame ands GUI correctly
        # Track changes to the canvas and frame widths
        # Sync them, and update the scrollbar
        # Based on code by novel-yet-trivial/VerticalScrolledFrame.py, 2017
        def _configure_IOFrame(event=None):
            # Update the scrollbars to match the size of the inner frame
            size = (self.IOFrame.winfo_reqwidth(), self.IOFrame.winfo_reqheight())
            self.IOcanvas.config(scrollregion="0 0 %s %s" % size)
            if self.IOFrame.winfo_reqwidth() != self.IOcanvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.IOcanvas.config(width=self.IOFrame.winfo_reqwidth())
        self.IOFrame.bind('<Configure>', _configure_IOFrame)
        self.IOFrame.bind("<<updatePort>>", self.updatePort)

        def _configure_IOcanvas(event=None):
            #self.IOcanvas.configure(scrollregion=self.IOcanvas.bbox("all"))
            if self.IOFrame.winfo_reqwidth() != self.IOcanvas.winfo_width():
                # update the inner frame's width to fill the canvas
                self.IOcanvas.itemconfigure(self.IOFrame_win, width=self.IOcanvas.winfo_width())
        self.IOcanvas.bind('<Configure>', _configure_IOcanvas)
        
        # Intialise the IOFrame and IOcanvas- just use the callbacks
        _configure_IOFrame()
        _configure_IOcanvas()
        
        # Mousewheel scrolling
        def _bind_mouse(event=None):
            self.IOcanvas.bind_all("<4>", _on_mousewheel)
            self.IOcanvas.bind_all("<5>", _on_mousewheel)
            self.IOcanvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_mouse(event=None):
            self.IOcanvas.unbind_all("<4>")
            self.IOcanvas.unbind_all("<5>")
            self.IOcanvas.unbind_all("<MouseWheel>")
        
        def _on_mousewheel(event):
            """Linux uses event.num; Windows / Mac uses event.delta"""
            if event.num == 4 or event.delta > 0:
                self.IOcanvas.yview_scroll(-1, "units" )
            elif event.num == 5 or event.delta < 0:
                self.IOcanvas.yview_scroll(1, "units" )
        
        self.IOcanvas.bind("<Enter>", _bind_mouse)
        self.IOcanvas.bind("<Leave>", _unbind_mouse)
        
        ### Finally load file if filename provided from command line
        self.loadConfig()
        # Build the autocomplete dictionary (mnemonics, directives, macros, registers)
        self._acBuildDict()
        self.toggleAutocomplete(refreshOnly=True)   # sync Edit menu with saved setting
        if filename:
            try:
                self.file_open(filepath=filename)
            except:
                print("File not found!")
                exit()
        if self.savedWindowGeom:
            try:
                self.master.geometry(self.savedWindowGeom)
            except tk.TclError:
                self.master.geometry(self._defaultGeometry())
        else:
            self.master.geometry(self._defaultGeometry())
        # Never let the window be larger than the screen (toolbar buttons
        # used to get clipped/overlapped on smaller displays)
        try:
            sw, sh = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
            self.master.minsize(min(1000, sw - 60), min(600, sh - 120))
            self.update_idletasks()
            if self.master.winfo_width() > sw - 40 or self.master.winfo_height() > sh - 80:
                self.master.geometry(self._defaultGeometry())
        except Exception:
            pass

        # Build the project file browser sidebar (VS Code style Explorer)
        self._buildProjectBrowser()
        # Restore expanded folders from last session (only those inside root)
        savedExp = [p for p in getattr(self, "_savedExpandedDirs", [])
                    if os.path.isdir(p)]
        # Reopen last session's project (if it still exists)
        if self.projectPath and os.path.isdir(self.projectPath):
            self.set_project(self.projectPath, startup=True)
            for p in savedExp:
                rp = self.rootProjectPath or ""
                if rp and (p == rp or p.startswith(rp + os.sep)):
                    self.expandedDirs.add(p)
            if savedExp:
                self._populateProjectTree()
        elif self.recentProjects:
            for p in self.recentProjects:
                if os.path.isdir(p):
                    self.set_project(p, startup=True)
                    break

        self.master.config(cursor="")

    
    #### IO Port functions
    
    def updatePort(self, event=None, portno=None):
        #for item in event:
        #print(event.state)# cludge to pass portno index back from IOport interrupt
        # if a port no is specified, either explicitly in portno, or from event.state,
        # then delete it
        n = None
        if event != None and event.state<256: 
            n = event.state
        if portno != None:# ignore any events, use portno
            n = portno
        # Delete and renumber ports if n is a port number
        if n != None and n >= 0:
            # Event generated by deleting an IO port 
            del self.IOPorts[n]
            # Update and renumber ports 
            portno=0
            for port in self.IOPorts:
                port.updatePort()
                port.portno = portno
                portno += 1
        # In all cases, update the Memory Display
        #self.dispAllMemory()
        self.updateDisp()
        return
        
    def addport(self, event=None, portno=0):
        # self.IOPorts is list of IO Port objects
        portkey = self.portVar.get()
        if portno>0 and (portno) < len(self.IOPorts): # Replace existing port
            # replace existing port
            self.updatePort(portno=portno) # delete port, then
            self.IOPorts.insert(portno, getattr(cdm8_io, portkey)(self.IOFrame, portno))
        else: # Append
            portno = len(self.IOPorts)
            self.IOPorts.append(getattr(cdm8_io, portkey)(self.IOFrame, portno))
            # renumber ports
            portno=0
            for port in self.IOPorts:
                port.portno = portno
                portno += 1
        #self.dispAllMemory()
        self.updateDisp()

    def inputPortHandler(self, event=None):
        # Interrupt handler called by the Emulator whenever an 
        # Input (data memory) Port address is read .
        # Memory address passed via self.Emu.ipAdr,
        # If found in any IP port,then sets self.Emu.ipVal to Input port value.
        # Emulator then substitutes value from ipVal instead memory adr val. 
        # Also used by OP ports to trigger a dislpay update
        for port in self.IOPorts:
            for adr in port.portIPvals.keys():
                #print(adr, self.Emu.ipAdr)
                if adr == self.Emu.ipAdr:
                    self.Emu.ipVal = port.portIPvals[adr]
        self.updateDisp()    
        return 
    
    def updateOPs(self):
        ## Check for Output port value updates
        if  self.Emu.memChanged[0]:
            adr = self.Emu.memChanged[0][-1] 
            for port in self.IOPorts:
                #print("**",list(port.getOPadr()))
                if adr in port.getOPadr():
                    #print("*", adr, list(port.getOPadr()), memval)
                    port.setOPval(adr, self.Emu.memory[0][self.Emu.datamem[0]][adr])

    
    def interruptHandler(self, event=None):
        # Interupt handler
        self.interrupt = True # set interrupt flag
        self.intVector = 0 # ???


    #### Ames functionality
    def amesStart(self, event=None):
        self.statusMsg.config(text="") # Clear any error messages
        self.disableMenus()
        errormsg = None
        self.bgColour = self.pinLabel.cget("bg")
        # get and check pin formatted ok)
        #print("*",self.pinVar.get(), "8")
        try:
            self.pin = self.pinVar.get()
            #print(type(self.pin), self.pin)#debug
        except:
            errormsg="BAD PIN!"
        #print( "*", errormsg)
        self.statusMsg.config(text="PLEASE WAIT")
        self.update()
        if errormsg == None and not ames.ping():
            errormsg = "NETWORK FAULT"
        if errormsg == None: # No network errors etc.
            #print("Ames selected", self.pin)#debug
            # get remote file and load to text editwindow
            #timeleft=None
            # First try .asm file
            received_file = None
            success = False
            timeleft = 0
            try:
                (success,received_file, timeleft) = ames.download(self.pin,"asm")
                #print("timeleft1=",timeleft)#debug
                #print(received_file[:20], success, timeleft) #debug - just first line or so
                #if timeleft and timeleft>0:
                self.timeleft = timeleft #Use AMES timeleft value
                #print("asm",success, received_file[:20])#debug
                #print("timeleft2=",self.timeleft) #debug
            except:
                #raise # debug for Mac Ames problem
                success = False
                received_file = False
            ## hack for testing
            if self.testcount:
                self.timeleft = self.testcount # hack for testing !!!!
                self.testcount = None
            ##
            #print("Timeleft = ", self.timeleft)#debug
            
            if self.timeleft and self.timeleft<=0:
                statusMsg = "AMES: TEST TIMED OUT"
            else:
                statusMsg = "AMES: TEST STARTED OK"
            if not success:
                if received_file:
                    errormsg=received_file
                else:
                    errormsg = "UNSPECIFIED NETWORK ERROR"
                    
            if success and self.timeleft: #if errormsg == None: # commnent out for testing w out ames.
                # load file into editor
                # Set current text to file contents
                self.amesRunning=True
                self.cliptext=""
                self.asstxt.delete(1.0, "end")
                self.mcode_list.delete(1.0, tk.END)
                self.asstxt.insert(1.0, received_file)
                self.asstxt.edit_modified(False)
                self.asstxt.edit_separator()
                self.asstxt.edit_reset()
                self.highlighter()
               
        if errormsg:# or self.timeleft <= 0:
            self.statusMsg.config(text=errormsg)
            self.pinVar.set("")
            self.enableMenus()
            self.amesRunning=False
        else:
            if self.timeleft >0:
                self.set_title(titletxt="AMES: TEST RUNNING")
            else:
                self.set_title(titletxt="AMES: TEST TIMED OUT")
            self.amesButton.config(text="Submit", state=tk.NORMAL, command=self.amesSubmit)
            self.statusMsg.config(text=statusMsg)#"AMES: TEST STARTED OK")
            self.amesSubmit()# Immediately submit file for timestamp
            self.amesClockUpdate(self.timeleft)

    def amesClockUpdate(self, timeleft=None):
        # When AMES is running this function runs every 10 secs
        now = time.time()
        if timeleft!=None:
            self.endtime = now + timeleft*60
        self.timeleft = self.endtime - now
        print("Ames Timeleft", int(self.timeleft)," secs")#debug
    
        if  self.amesRunning and (self.timeleft > 0 or self.timeleft < -11): # Still time left?
            if self.timeleft % 300 < 11:
                #print("amesRunning ", self.amesRunning)#debug
                self.amesSubmit(auto=True) # auto-submit every 5 mins (300 secs)
                # Update display every 10 secs approx
            #self.statusMsg.config(text="TIME LEFT = "+str(int(self.timeleft//60)+1)+" MIN ")#+str(int(self.timeleft%60))+" SEC")#, width=30)
            self.pinLabel.config(text = "AMES <"+str(int(self.timeleft//60)+1)+" MIN LEFT", fg="white", bg="black")
            # Schedule update in 10 secs
            self.after(10000, self.amesClockUpdate) # every 10 secs
            #print("Clock Update in 10secs")#debug
        else:
            self.amesStop()
        return

    def amesSubmit(self, ext="asm", auto=False):
        errormsg=None
        content = None
        content = copy.copy(self.asstxt.get(1.0, "end"))# deep copy for 00: bug?
        #if content: print(content[:20], ext, self.pin)#debug
        # init submit vars to avoid type errors on error
        PE = False
        success = False
        diag = ""
        if content and self.amesRunning:
            try:
                #print(content[:20], ext, self.pin)
                (PE,success,diag) = ames.submit(content,ext,self.pin)
            except:
                #raise # debug
                pass
            #print(PE, success, diag)# debug
            #print(diag)# debug
            if PE:
                errormsg = "Protocol error: "+diag+'\n'
            if not success:
                errormsg = "Submit Failure: "+diag+'\n'
            if not errormsg:
                if self.timeleft>0:
                    if not auto: self.statusMsg.config(text="SUBMITTED OK")
                elif self.timeleft < -1: 
                    self.statusMsg.config(text="LATE SUBMISSION!")
                else:
                    self.statusMsg.config(text="TIME UP\nSUBMITTED OK!")

                print("File Submitted to ames")#debug
            else:
                # problem submitting
                self.statusMsg.config(text=errormsg+":\nTry again, or call tutor?")
                #self.pinEntry.config(state=tk.NORMAL)

    def amesStop(self):
        self.after_cancel(self.amesClockUpdate) # cancel clock update
        self.amesSubmit()
        if self.timeleft>0:
            self.statusMsg.config(text="Exited AMES OK")
        elif self.timeleft < -10: self.statusMsg.config(text="LATE SUBMISSION\nERROR!")
        else:
            self.statusMsg.config(text="TIME UP\nSUBMITTED OK!")
        self.pinLabel.config(text = "AMES          PIN?", fg="black", bg=self.bgColour)
        self.amesRunning=False
        #self.asmActive = False
        self.asstxt.edit_modified(False)
        if self.file_path: # Restore previous file if applicable
            self.file_open(filepath=self.file_path)
        else:
            self.file_new()
        self.enableMenus()
        return "break"

    def disableMenus(self):
        # disable load/save buttons
        self.newButton.config(state=tk.DISABLED)
        self.openButton.config(state=tk.DISABLED)
        self.saveButton.config(state=tk.DISABLED)
        self.saveAsButton.config(state=tk.DISABLED)
        self.saveImageButton.config(state=tk.DISABLED)
        self.pinEntry.config(state=tk.DISABLED)
        self.amesButton.config(state=tk.DISABLED)
        self.exitButton.config(command=self.amesStop, text="End ")
        self.unbindKeys()

        # Ames backdoor
        #self.asstxt.bind("<Control-p>", self.amesPause)
        #self.asstxt.bind("<Control-P>", self.amesPause)

        # Disable load/save menus
        self.menubar.entryconfig("File", state=tk.DISABLED)

    def enableMenus(self):
        # Enable file menu and load.save buttons
        self.newButton.config(state=tk.NORMAL)
        self.openButton.config(state=tk.NORMAL)
        self.saveButton.config(state=tk.NORMAL)
        self.saveAsButton.config(state=tk.NORMAL)
        self.saveImageButton.config(state=tk.NORMAL)
        self.pinEntry.config(state=tk.NORMAL)
        #if platform == "darwin":
        #    self.amesButton.config(text="AMES Start ", state=tk.NORMAL, command=self.amesStart)
        #else:
        self.amesButton.config(text="Start ", state=tk.NORMAL, command=self.amesStart)    
        self.exitButton.config(command=self.close_window, text="Quit")#??
        self.pinVar.set("")
        # Enable Load/Save hot keys
        self.bindKeys()
        # Enable load/save menus
        self.menubar.entryconfig("File", state=tk.NORMAL)

    def _defaultGeometry(self):
        """Default window size: generous, but never exceeds the screen."""
        try:
            sw, sh = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        except Exception:
            sw, sh = 1400, 900
        w = max(1000, min(1300, sw - 80))
        h = max(640, min(820, sh - 130))   # leave room for menubar/dock
        return "%dx%d+40+60" % (w, h)

    def bindKeys(self):
        # Bind editing keys
        self.asstxt.unbind("<Control-Tab>")
        self.asstxt.bind("<Control-n>", self.file_new)
        self.asstxt.bind("<Control-N>", self.file_new)
        self.asstxt.bind("<Control-o>", self.file_open)
        self.asstxt.bind("<Control-O>", self.file_open)
        self.asstxt.bind("<Control-S>", self.file_save)
        self.asstxt.bind("<Control-s>", self.file_save)
        self.asstxt.bind("<Control-S>", self.file_save_as)
        
        self.asstxt.bind("<Control-a>", self.selectall)
        self.asstxt.bind("<Control-q>", self.file_quit)
        self.asstxt.bind("<Control-Q>", self.file_quit)
        self.asstxt.bind("<Control-Y>", self.redo)
        self.asstxt.bind("<Control-y>", self.redo)
        self.asstxt.bind("<Control-Z>", self.undo)
        self.asstxt.bind("<Control-z>", self.undo)
        if platform != "darwin":
            # On macOS plain Control bindings clash with Cmd ones (Tk maps
            # Command->Control there); real Cmd bindings are added below.
            self.asstxt.bind("<Control-c>", self.copy)
            self.asstxt.bind("<Control-C>", self.copy)
            self.asstxt.bind("<Control-t>", self.cut)
            self.asstxt.bind("<Control-T>", self.cut)
            self.asstxt.bind("<Control-v>", self.paste)
            self.asstxt.bind("<Control-V>", self.paste)
        
        # NOTE: <Tab>/<Return> are bound once in __init__ to the autocomplete
        # handlers (returning "break" when a candidate is accepted, falling back
        # to indent/newline otherwise); bindKeys() is re-called later (AMES stop
        # -> enableMenus) and must NEVER rebind these - that silently replaced
        # the AC handlers and broke Tab/Enter completion.
        self.asstxt.bind("<Shift-Tab>", lambda e: self.tabBlock(shift=-1))
        self.asstxt.bind("<Control-ISO_Left_Tab>", lambda e: self.tabBlock(shift=-1))
        self.asstxt.bind("<Control-Tab>", lambda e: self.tabBlock(shift=-1))
        # (Cmd+Shift-[ / Cmd+] block-indent shortcuts are attached safely
        # further below via _safeBind – some Tk builds lack those keysyms.) 
        
        # Compile / Run / Step / Breakpoint shortcuts (both platforms)
        self.asstxt.bind("<F5>", self.compileRun)
        self.asstxt.bind("<Control-F5>", lambda e: self.compileText())
        self.bind_all("<Control-F5>", lambda e: self.compileText())
        self.bind_all("<Command-b>", lambda e: self.compileText())
        self.bind_all("<Command-r>", self.runProg)
        self.bind_all("<Command-B>", lambda e: self.compileText())
        self.bind_all("<Command-R>", self.runProg)
        self.bind_all("<Command-f>", self.focusSearchBox)
        self.bind_all("<Command-F>", self.focusSearchBox)
        self.bind_all("<Command-g>", self.gotoLineDialog)
        self.bind_all("<Command-G>", self.gotoLineDialog)
        self.bind_all("<Command-Shift-O>", lambda e: self.open_project_dialog())
        self.bind_all("<Command-Alt-n>", lambda e: self.new_file_in_project())
        self.bind_all("<Command-Alt-N>", lambda e: self.new_file_in_project())
        self.asstxt.bind("<Escape>", self.clearEditorHighlights, add="+")
        if platform != "darwin":
            self._safeBind(self, "<Control-p>", lambda e: self.showQuickOpen())

        # OSX/Mac OS users add cmd key options as well
        if platform == "darwin":
            self.asstxt.bind("<Command-o>", self.file_open)
            self.asstxt.bind("<Command-O>", self.file_open)
            self.asstxt.bind("<Command-S>", self.file_save_as)
            self.asstxt.bind("<Command-s>", self.file_save)
            self.asstxt.bind("<Command-n>", self.file_new)
            self.asstxt.bind("<Command-N>", self.file_new)
            self.asstxt.bind("<Command-d>", self.copyLineDown)
            self.asstxt.bind("<Command-D>", self.copyLineDown)
            self.asstxt.bind("<Command-Delete>", self.deleteLine)
            self.asstxt.bind("<BackSpace>", self.macBackspace)
            self.asstxt.bind("<Shift-BackSpace>", self.macBackspace)
            self.asstxt.bind("<Command-a>", self.selectall)
            self.asstxt.bind("<Command-A>", self.selectall)
            self.asstxt.bind("<Command-z>", self.undo)
            self.asstxt.bind("<Command-Z>", self.redo)
            self.asstxt.bind("<Command-x>", self.cut)
            self.asstxt.bind("<Command-X>", self.cut)
            self.asstxt.bind("<Command-c>", self.copy)
            self.asstxt.bind("<Command-C>", self.copy)
            self.asstxt.bind("<Command-v>", self.paste)
            self.asstxt.bind("<Command-V>", self.paste)
            self.asstxt.bind("<Command-Right>", self.lineEnd)
            self.asstxt.bind("<Command-Left>", self.lineStart)
            self.asstxt.bind("<Command-Up>", lambda e: self.asstxt.yview_moveto(0))
            self.asstxt.bind("<Command-Down>", lambda e: self.asstxt.yview_moveto(1))
            # Quick-open file picker (VS Code style). Lowercase 'p' keysym via
            # _safeBind; Ctrl-Tab cycles editor tabs (unbound for editing above).
            self._safeBind(self, "<Command-p>", lambda e: self.showQuickOpen())
            self._safeBind(self, "<Command-P>", lambda e: self.showQuickOpen())
            self.bind_all("<Control-Tab>", lambda e: self.nextTab())
            self.bind_all("<Control-Shift-Tab>", lambda e: self.prevTab())

    def _setMenuLabel(self, menu, match, newlabel):
        """Change a menu entry's label by substring match (index-independent)."""
        try:
            for i in range(menu.index("end")+1):
                lab = str(menu.entrycget(i, "label"))
                if match in lab:
                    menu.entryconfig(i, label=newlabel)
                    return True
        except TclError:
            pass
        return False

    def _safeBind(self, widget, seq, func):
        """Bind a shortcut, skipping it if this Tk build lacks the keysym
        (e.g. BracketLeft/BracketRight are missing in some macOS Tk 8.6/9.x)."""
        try:
            widget.bind(seq, func)
            return True
        except TclError:
            return False

    def _bindBlockIndentShortcuts(self):
        """VS Code-style block indent: Cmd+] / Cmd+Shift+[ (+ Ctrl on Linux/Win)."""
        combos = [
            ("<Control-BracketRight>", lambda e: self.tabBlock(shift=1)),
            ("<Control-Shift-BracketLeft>", lambda e: self.tabBlock(shift=-1)),
        ]
        if platform == "darwin":
            combos += [
                ("<Command-BracketRight>", lambda e: self.tabBlock(shift=1)),
                ("<Command-bracketright>", lambda e: self.tabBlock(shift=1)),
                ("<Command-Shift-BracketLeft>", lambda e: self.tabBlock(shift=-1)),
                ("<Command-bracketleft>", lambda e: self.tabBlock(shift=1)),
                ("<Command-Shift-bracketleft>", lambda e: self.tabBlock(shift=-1)),
            ]
        for seq, fn in combos:
            self._safeBind(self.asstxt, seq, fn)
        
    def unbindKeys(self):
        self.asstxt.bind("<Control-N>", None)
        self.asstxt.bind("<Control-n>", None)
        self.asstxt.bind("<Control-o>", None)
        self.asstxt.bind("<Control-O>", None)
        self.asstxt.bind("<Control-S>", None)
        self.asstxt.bind("<Control-s>", None)
        self.asstxt.bind("<Control-A>", None)
        self.asstxt.bind("<Control-a>", None)
        self.asstxt.bind("<Control-Shift-S>", None)
        self.asstxt.bind("<Control-Shift-s>", None)
        
        if platform == "darwin":
            self.asstxt.bind("<Command-o>", None)
            self.asstxt.bind("<Command-O>", None)
            self.asstxt.bind("<Command-S>", None)
            self.asstxt.bind("<Command-s>", None)
            self.asstxt.bind("<Command-n>", None)
            self.asstxt.bind("<Command-N>", None)
            self.asstxt.bind("<Command-d>", None)
            self.asstxt.bind("<Command-D>", None)
            self.asstxt.bind("<Command-Delete>", None)
            self.asstxt.bind("<Command-a>", None)
            self.asstxt.bind("<Command-A>", None)
            self.asstxt.bind("<Command-z>", None)
            self.asstxt.bind("<Command-Z>", None)
            self.asstxt.bind("<Command-x>", None)
            self.asstxt.bind("<Command-c>", None)
            self.asstxt.bind("<Command-v>", None)
            
        
    def amesPause(self, event=None):
        # Back door for editing #! lines when ames is running
        if self.amesRunning:
            self.amesRunning = False
            self.enableMenus()
        else:
            self.amesRunning = True
            self.asstxt.bind("<Control-p>", None)
            self.asstxt.bind("<Control-P>", None)
            self.disableMenus()

    def keydisable(self, event=None):
        # Disable ! and editing keys for lines with #! when running ames
        #print("keydisable",event.keysym, event.keycode, repr(event.char), event.type)# debug
        if platform == "darwin":
            try:
                if self.asstxt.edit_modified():
                    self.set_title()  # refresh the unsaved-changes dot
            except Exception:
                pass

        if self.amesRunning and event.keysym not in ["Left", "Right", "Up", "Down",
                        "Home", "End", "Prior", "Next"]:#, "Control_R"]:# Ames backdoor
            # Do not allow editing of #! lines, or inserting ! after #
            if event.keysym == "exclam" and self.asstxt.search("#", "insert-1c", "insert"):
                return "break"
            if self.asstxt.search("#!", "insert linestart", "insert lineend+1c"):
                #print(event.keysym, event.keycode)# debug
                return "break"
            if event.char=="#" and self.asstxt.search("!", "insert", "insert+1c"):
                return "break"
            if event.char=="!" and self.asstxt.search("#", "insert-1c", "insert"):
                return "break"
                

    #### Functions for updating GUI display
    
    def initMemDisplay(self, page=None):
        if not page:
            page = self.Emu.curPage
        #print("**",self.Emu.memory[0])
        for n in range(len(self.mem_frame)):
            gridpos=1
            for col in range(16):
                tk.Label(self.mem_frame[n], text=self.Emu.hx(col)[1]+" ", font=self.boldfont).grid(row=0, column=gridpos, padx=2, pady=2)
                tk.Label(self.mem_frame[n], text=self.Emu.hx(col)[1]+" ", font=self.boldfont).grid(row=gridpos, column=0, padx=2, pady=2)
                gridpos += 1
        
        self.memLabel = [0]*256*len(self.Emu.memory[0])
        self.ttArray = [0]*256*len(self.Emu.memory[0])
        #print(self.memLabel,"\n", self.ttArray)
        
        index=0
        
        for n in range(len(self.Emu.memory[self.Emu.curPage])):
            for gridy in range(1,17):
                for gridx in range(1, 17):
                    #print(n, "*", index, end=":")
                    self.memLabel[index] = tk.Label(self.mem_frame[n], font=self.defaulttxtfont, text="00", width=2, bg="white")#, font=self.smallfont)
                    self.memLabel[index].grid(row=gridy, column=gridx)
                    self.ttArray[index] = CreateToolTip(self.memLabel[index], "", 200)
                    index += 1
            #print("\n")# debug
        
    def updateDisp(self):
        self.dispAllMemory()
        self.dispCVZN()
        self.dispSP()
        self.dispRegs()
        self.updateWatchWin()
        self.dispPC()
        self.update()# TK update!

    def dispCVZN(self):
        #print(format(self.Emu.CVZN,"04b"))debug
        CVZNstr = format(self.Emu.CVZN & 0b00001111,"04b")
        pageStr = format((self.Emu.CVZN & 0b01110000)>>4, "03b")
        intStr = str(self.Emu.CVZN >> 7)
        newtxt = "    "+intStr+" "+pageStr+"  "+CVZNstr
        if self._lastCVZNtxt is not None and newtxt != self._lastCVZNtxt \
                and (self.running or self.stepModeActive()):
            self.pulseWidget(self.CVZN_Val)   # animate PS change during execution
        self._lastCVZNtxt = newtxt
        self.CVZN_Val.config(text= newtxt)
        return

    def stepModeActive(self):
        """True while single-stepping / running in the emulator panels.
        Any non-zero program counter means the user has executed at least one
        instruction, so change-pulses are wanted; before first run they are not."""
        try:
            return self.Emu.PC != 0
        except Exception:
            return False

    #### Change-animation ("pulse") for register/memory cells ------------------
    _PULSE_STEPS = ["#FFE9A8", "#FFD966", "#FFF3CF"]  # amber flash -> fade back

    def pulseWidget(self, w):
        """Briefly highlight a label to draw attention to a value change."""
        try:
            base = w.cget("bg")
            if isinstance(base, tuple):      # 3-tuple rgb form
                base = "#%02x%02x%02x" % base
        except Exception:
            return
        old = self._pulseIds.get(w)
        if old:
            try: self.after_cancel(old)
            except Exception: pass
        self._pulseSeq(w, 0, base)

    def _pulseSeq(self, w, i, base):
        try:
            if not w.winfo_exists():
                self._pulseIds.pop(w, None); return
            if i < len(self._PULSE_STEPS):
                w.config(bg=self._PULSE_STEPS[i])
                self._pulseIds[w] = self.after(55, lambda: self._pulseSeq(w, i+1, base))
            else:
                w.config(bg=base)
                self._pulseIds.pop(w, None)
        except Exception:
            self._pulseIds.pop(w, None)

    #### Tooltips (macOS-style hover help) -------------------------------------
    def _showTip(self, widget, textfn, event=None):
        """macOS 'help-book' style tooltip: rounded dark bubble with white text.
        Own-drawn Canvas pill (a plain Label would render as a grey/white box
        whose light-on-light text is invisible)."""
        self._hideTip()
        try:
            txt = textfn() if callable(textfn) else textfn
        except Exception:
            return
        if not txt:
            return
        # position near the widget (or the mouse when we have an event),
        # clamped inside the screen so the bubble is never cut off
        try:
            root = widget.winfo_toplevel()
            scr_w, scr_h = root.winfo_screenwidth(), root.winfo_screenheight()
        except Exception:
            scr_w, scr_h = 1920, 1080
        mx = event.x_root if event is not None else widget.winfo_rootx() \
                                                + widget.winfo_width() + 6
        my = event.y_root if event is not None else widget.winfo_rooty() - 4
        tw = tk.Toplevel(self)
        tw.wm_overrideredirect(True)
        try:
            tw.attributes("-topmost", True)
            tw.attributes("-alpha", 0.95)
        except Exception:
            pass
        BG, FG = "#3a3a3c", "#ffffff"          # dark bubble, WHITE text
        tw.configure(bg=BG, highlightthickness=0)
        cv = tk.Canvas(tw, bg=BG, highlightthickness=0, bd=0)
        cv.pack()
        fnt = getattr(self, "tipfont", None) or ("TkDefaultFont", 10)
        # measure text width with a throwaway item (create_text returns the
        # item id as an int - it has no .bbox(); use cv.bbox(id) instead)
        def textw(s):
            _id = cv.create_text(0, 0, text=s, font=fnt)
            bb = cv.bbox(_id)
            cv.delete(_id)
            return bb[2] - bb[0] if bb else 0
        pad, lh = 12, 19
        lines = []
        for raw in str(txt).split("\n"):
            words, cur = raw.split(), ""
            for w in words:
                trial = (cur + " " + w).strip()
                if textw(trial) > 400:
                    if cur:
                        lines.append(cur)
                    cur = w
                else:
                    cur = trial
            lines.append(cur)
        W = max(textw(s) for s in lines) + 2*pad
        H = len(lines)*lh + 2*pad - (lh - 14)
        r = min(10, H//2, W//2)                 # rounded corners -> macOS bubble
        cv.configure(width=W, height=H)
        pts = [r, 0, W-r, 0, W, r, W, H-r, W-r, H, r, H, 0, H-r, 0, r]
        cv.create_polygon(*pts, smooth=True, splinesteps=36, fill=BG, outline=BG)
        for i, s in enumerate(lines):
            cv.create_text(pad, pad + i*lh, anchor="nw", text=s,
                           font=fnt, fill=FG, justify=tk.LEFT)
        tw.update_idletasks()
        x = min(max(0, mx + 12), scr_w - W - 8)
        y = min(max(0, my + 14), scr_h - H - 8)
        tw.wm_geometry("+%d+%d" % (x, y))
        self._tipWin = tw

    def _hideTip(self, event=None):
        tw = getattr(self, "_tipWin", None)
        self._tipWin = None
        if tw:
            try: tw.destroy()
            except Exception: pass

    def tipPS(self):
        v = self.Emu.CVZN
        I   = (v >> 7) & 1
        pg  = (v >> 4) & 0b111
        C,V,Z,N = [(v >> s) & 1 for s in (3,2,1,0)]
        lines = [
            "PS — Processor Status byte:  I ppp CVZN",
            "",
            "I    Interrupts enable: %d (%s)" % (I, "allowed" if I else "masked"),
            "Page Current memory page (bank): p%d" % pg,
            "C    Carry/borrow: %d" % C,
            "V    oVerflow (signed): %d" % V,
            "Z    Zero result: %d" % Z,
            "N    Negative result (bit7): %d" % N,
            "",
            "Branch conditions that read these flags:",
            "  beq/bne  -> Z      bhs/bls (unsigned) -> C",
            "  bmi/bpl  -> N      blt/bge/ble/bgt (signed) -> V & N",
            "  bvs/bvc  -> V      bhi/blo (unsigned) -> C & Z",
            "",
            "Raw value: 0x%02X  (%s)" % (v, format(v, "08b")),
        ]
        return "\n".join(lines)

    def tipSP(self):
        spage = self.Emu.curPage if self.Emu.shadowSP else 0
        val = self.Emu.SP[spage]
        return ("SP — Stack Pointer (page p%d)\n"
                "Top of stack at RAM address 0x%02X.\n"
                "push decrements SP then stores;\npop loads then increments."
                % (spage, val))

    def tipPC(self):
        pc = self.Emu.PC
        try:
            instr = self.Emu.disassemble(pc) if hasattr(self.Emu, "disassemble") else ""
        except Exception:
            instr = ""
        if not instr:  # fall back to the disasm shown in the Machine-Code panel
            try:
                key = "%02X:" % pc
                ln = self.mcode_list.search(key, "1.0", tk.END, regexp=False)
                if ln:
                    line = self.mcode_list.get("%s linestart" % ln[1], "%s lineend" % ln[1])
                    instr = line.split(":", 1)[-1].strip() if ":" in line else ""
            except Exception:
                instr = ""
        t = "PC — Program Counter\nNext instruction at page p%d, address 0x%02X." % (self.Emu.curPage, pc)
        if instr:
            t += "\n\nNext: " + instr.strip()
        return t

    def tipReg(self, i):
        r = self.Emu.regs[i]
        lo, hi = r & 0xFF, (r >> 8) & 0xFF
        sgn = r - 65536 if r > 32767 else r
        return ("r%d — 16-bit general register\n"
                "Value: 0x%04X = %d unsigned, %+d signed\n"
                "High byte r%dh = 0x%02X ('%s'), low byte r%dl = 0x%02X ('%s')\n\n"
                "Byte operands usable in instructions:\n"
                "  r%dh (high), r%dl (low)" ) % (
                i, r, r, sgn, i, hi, chr(hi) if 32 <= hi < 127 else ".",
                i, lo, chr(lo) if 32 <= lo < 127 else ".", i, i)

    def dispAllMemory(self, page=None):#?? 
        #print("\n\n", "dispAllMemory Call***",len(self.Emu.memory))
        #print("&&",self.Emu.memChanged[self.Emu.curPage])
        # Update Code and Data Memories
        index = 0
        if page:
            curPage = page
        elif self.running:
            curPage = self.Emu.curPage
        else:
            curPage = self.memPageVar.get()
        
        self.memPageVar.set(curPage)
        self.memChanged = self.Emu.memChanged[curPage]
        #print("£",page, self.Emu.curPage, curPage)#, self.Emu.memory[self.Emu.curPage])
        #print("$",self.Emu.memChanged, "\n",self.memChanged)

        # Hide bank 1 (data page) if arch=vn - switch back on if Harvard arch
        # and update Menu
        if self.Emu.arch[curPage] == "vn":
            numbanks = 1
            self.emuNb.add(self.mem_frame[0], text="Page "+str(curPage)+" Memory")
            #self.emuNb.config(0, text=)
            self.emuNb.hide(1)
            self._setMenuLabel(self.emumenu, "Arch.", "Arch. = Harvard   ")
        else:
            numbanks = 2
            self.emuNb.add(self.mem_frame[0], text=("Page "+str(curPage)+" ROM"))
            self.emuNb.add(self.mem_frame[1], text=("Page "+str(curPage)+" RAM"))#, state="normal")#, underline=0, padding=2)
            self._setMenuLabel(self.emumenu, "Arch.", "Arch. = Von Neuman")
            
        for n in range(numbanks): # All banks in in current CDM8 memory page
            #print("Memory page ", curPage, " bank ", n, "=",self.Emu.memory[curPage][n])
            #if n == 1, Harvard Arch,  so show bank 1
            
            for memval in self.Emu.memory[curPage][n]:#self.Emu.curPage][n]: # For each bank
                self.memLabel[index].config(text=self.Emu.hx(memval),fg=cf.memColour, bg=cf.membgColour)
                    
                if self.memChanged:
                    # Mark any changes in memory contents
                    #print(self.runFrom.get())#debug
                    #print("*", index, n, self.Emu.PC, self.memChanged)
                    if index == 0 or self.Emu.PC==self.runDict[self.runFrom.get()] == 0: # Except at start of run
                        self.memLabel[index].config(fg=cf.memColour)
                    elif n == self.Emu.datamem[curPage]: # If n = 0, then VN Arch, else 1 = HV Arch
                        for addr in self.memChanged:
                            if (index % 256) == addr:# Highlight if memory cell has changed
                                #print(index, int(addr))# debug
                                self.memLabel[index].config(fg=cf.chMemColour)
                   
                    # Runtime Self modifying code warning 
                    if  self.arch[curPage]=="vn" and (self.Emu.PC in self.memChanged): #(n < self.Emu.datamem[curPage] or
                        self.statusMsg.config(text="Runtime Warning:\nExecuting Self\nModified Code?")
                        txtaddr = self.mcode_list.search(self.Emu.hx(self.Emu.PC)+":", "1.0", tk.END)
                        if txtaddr:
                            self.mcode_list.tag_add("smod", "%s linestart+3c" % txtaddr, "%s lineend+1c" % txtaddr) # add tag to k
                            self.mcode_list.tag_config("smod", font=self.boldfont, foreground="red")
                else:
                    self.memLabel[index].config(fg=cf.memColour, text=self.Emu.hx(memval))
                
                if curPage==0: # First page of data (RAM) memory only, show IO ports
                    # Colour IO port adresses
                    indadr = index - (self.Emu.datamem[0] *256)
                    for port in self.IOPorts:
                        for adr in port.getOPadr():
                            #print("**", adr, self.Emu.datamem[self.Emu.curPage])
                            if n == self.Emu.datamem[0] and adr == indadr: # Only page 0 has IO
                                if adr in self.memChanged:
                                    fgcolour=cf.oportColour#cf.chMemColour
                                else: 
                                    fgcolour=cf.oportColour
                                self.memLabel[index].config(bg=cf.oportColour, fg=fgcolour, text=self.Emu.hx(memval))
                        for adr in port.getIPadr():
                            if n == self.Emu.datamem[0] and adr == index - (self.Emu.datamem[0] *256):
                                self.memLabel[index].config(bg=cf.iportColour, fg=cf.membgColour, text=("%02X" % port.portIPvals[adr]))#self.Emu.hx(memval))

                index += 1
        return

    def dispPC(self):
        #print("**", self.Emu.hx(self.Emu.PC))#debug
        ## Update current line, mem addr highlight
        if self.prevPC in self.Emu.BP:
            self.memLabel[self.prevPC].config(bg=cf.bpColour)
        else:
            self.memLabel[self.prevPC].config(bg="white")
        self.prevPC=self.Emu.PC
        self.pcLabVal.config(text=self.Emu.hx(self.Emu.PC))
        self.memLabel[self.Emu.PC].config(bg=cf.PCcolour)

        # Set current line highlighted in memList panel
        #print("**"+self.pcLabVal.cget('text')+":")# debug
        startIndex = self.mcode_list.search(self.pcLabVal.cget('text')+":", "1.0", tk.END, regexp=True)
        #print(startIndex)# debug
        if startIndex:
            # Highlight in mcode panel
            self.mcode_list.tag_delete("pc")
            self.mcode_list.tag_add("pc", "%s linestart+3c" % startIndex, "%s lineend+1c" % startIndex) # add tag to k
            self.mcode_list.tag_config("pc", background=cf.PCcolour)#cf.PCcolour)
            
            # and in asstxt panel
            self.asstxt.tag_delete("pc")
            self.asstxt.tag_add("pc", "%s linestart" % startIndex, "%s lineend+1c" % startIndex) # add tag to k
            self.asstxt.tag_config("pc", background=cf.PCcolour)
            self.asstxt.see("%s linestart" % startIndex)
        return

    def dispRegs(self):
        for index in range(4):
            val = self.Emu.regs[index]
            # Pulse the whole register column when its value changed during execution
            if (self._lastRegVals[index] is not None and val != self._lastRegVals[index]
                    and (self.running or self.stepModeActive())):
                for w in (self.regHexs[index], self.regStrs[index],
                          self.regDecs[index], self.regBins[index]):
                    self.pulseWidget(w)
            self._lastRegVals[index] = val
            self.regHexs[index].config(text="0x"+self.Emu.hx(val)) # hex row
            self.regStrs[index].config(text=self.Emu.convert(2,val)) # Char row

            self.regDecs[index].config(text="%+04d" % int(self.Emu.convert(1,val))+ " %03d" % val) # dec row
            #print("*"+convert(1,Regs[k]))# debug
            self.regBins[index].config(text=format(val,"08b")) # Bin row
        return

    def dispSP (self):
        if self.Emu.shadowSP:
            stackpage = self.Emu.curPage
        else:
            stackpage = 0
        #print("!",self.Emu.SP)
        newSP = self.Emu.SP[stackpage]
        if getattr(self, "_lastSP", None) == newSP:
            pass
        elif self._lastSP is not None and (self.running or self.stepModeActive()):
            self.pulseWidget(self.spVal)   # animate SP change during execution
        self._lastSP = newSP
        self.spVal.config(text=self.Emu.hx(newSP))# ??
        self.memLabel[self.prevSP+self.Emu.datamem[stackpage]*256].config(bg="white")
        if self.Emu.SP[stackpage] != 0: #self.runFrom.get():
            self.memLabel[self.Emu.SP[stackpage]+self.Emu.datamem[stackpage]*256].config(bg=cf.SPcolour)
        self.prevSP = self.Emu.SP[stackpage]
        return

    def dispIR(self, IRVal):
        return

    def runProg(self, event=None):
        # Non-blocking run loop: keeps the GUI responsive (no macOS "beachball")
        # and lets Stop/breakpoints interrupt even a fast infinite loop.
        if self.running: # Then stop
            self.running = False
            self.Emu.HALT = True
            return
        runAction = self.speedScale.get()
        self.statusMsg.config(text="")
        if runAction == 3: # Single step
            self.stepOnce()
            return
        self.running = True
        self.Emu.HALT = False
        self._runBatchSteps = 1 if runAction == 2 else 24  # slow / medium / fast
        self._runDelayMs = 300 if runAction == 2 else 20
        self.runStopButton.config(text="Stop", fg="red", activeforeground="red")
        self.speedScale.config(state="disabled")
        self._runId = self.after(0, self._runLoopStep)
        return

    def _runLoopStep(self):
        if not self.running:
            return
        n = 0
        while self.running and not self.Emu.HALT and n < self._runBatchSteps:
            self.Emu.step(cdm8_io.interrupt, cdm8_io.interruptVector)
            self.updateOPs()
            n += 1
            if self.Emu.PC in self.Emu.BP:
                self.running = False
                break
        self.updateDisp()
        if self.running and not self.Emu.HALT:
            self._runId = self.after(self._runDelayMs, self._runLoopStep)
        else:
            self._runStopped()

    def _runStopped(self):
        self.running = False
        self.updateOPs()
        self.updateDisp()
        self.runStopButton.config(text="Run ", fg="black", activeforeground="black")
        self.speedScale.config(state="normal")


    def changeTextSize(self, textsize=None):#, event=None):
        if textsize:
            self.textsize = textsize 
        else:
            self.textsize = 10
        #self.default_font = font.nametofont("TkDefaultFont")
        self.defaultfont.configure(size=self.textsize)
        self.option_add("*Font", self.defaultfont)
        
        self.defaulttxtfont.configure(size=self.textsize)
        self.boldfont.configure(size=self.textsize)
        self.smallfont.configure(size=self.textsize-2)
        for port in self.IOPorts:
            port.updateFont()

    def highlighter(self,  event=None):

        # Auto indent (=4) = Only works with tabs, not spaces.
        if event != None:
            #print(event.keysym)# debug
            if event.keysym=="Return":
                #print(event.keysym)#debug
                startIndex=self.asstxt.index("insert linestart -1 lines")
                #print(startIndex)#debug
                while startIndex:
                    startIndex = self.asstxt.search("\t", startIndex, "%s+1c" % startIndex)
                    if startIndex:
                        #print("tab ins", startIndex)
                        self.asstxt.insert("insert", "\t" )
                        startIndex = self.asstxt.index("%s +1c" % startIndex)
                        
        # Clear all highlights, set text to black
        #if self.changed == False:
        #if event!= None and (event.char == event.keysym or len(event.char)) == 1: #ignore special keys
        #msg = 'Punctuation Key %r (%r)' % (event.keysym, event.char)
        first, last = self.asstxt.yview()
        if self.running:
            self.running = False
            self.Emu.HALT = True
            self._runStopped()
        self.mcode_list.delete(1.0, tk.END)
        self.watchList.delete(1.0, tk.END)
        self.updateLineNos()
        self.clearBPs()
        for n in range(8):# Clear code memory
            self.Emu.memory[n]= [[0]*256, [0]*256]
        self.runDict={"00:":0}
        self.runEPSelect['values'] = ['00:']
        self.runEPSelect.current(0)
        self.labelList=[]
        self.resetEmu()
        self.changed=True
        self.update()
        self.asstxt.yview_moveto(first)
        self.lntext.tag_delete("gline")
        for tag in self.asstxt.tag_names():
            self.asstxt.tag_delete(tag)
        self.watches=[]
        self.asstxt.tag_add("all", '1.0', tk.END) # add tag to k
        self.asstxt.tag_config("all", foreground="black", font=self.defaulttxtfont)#font=self.boldfont)

        # Highlight keywords as defined in cdm8_XXX.py file
        for fgcolour in cf.highlights:
            #print(fgcolour) # Debug
            for word in cf.highlights[fgcolour]: # iterate over directive words list
                startIndex = '1.0'
                while startIndex:
                    startIndex = self.asstxt.search("\\y"+word+"\\y", startIndex, tk.END, regexp=True)
                    if startIndex:
                        endIndex = self.asstxt.index('%s+%dc' % (startIndex, (len(word)))) # find end of word
                        self.asstxt.tag_add(word, startIndex, endIndex) # add tag to k
                        self.asstxt.tag_config(word, foreground=fgcolour, font=self.boldfont)      # and color it with v
                        startIndex = endIndex # reset startIndex to continue searching
                        
                        # Update Watches list
                        # if a line contains a dc or ds (and not commented!)
                        if not self.asstxt.search(cf.commentprefix, "%s linestart"% startIndex, startIndex):
                            for watchword in cf.watchtrigs:
                                if watchword == word:
                                    fmtStr = self.asstxt.search(cf.commentprefix+"$", "%s linestart"% startIndex, "%s lineend" % startIndex)
                                    if fmtStr:
                                        fmtStr = self.asstxt.get("%s + 2c" % fmtStr, "%s + 5c" % fmtStr)
                                        #print("*"+fmtStr)# debug
                                    else:
                                        fmtStr=None
                                    self.watches.append([int(float(startIndex))-1, None, None, fmtStr, 0]) #[lineno, label, adr, disp, items]
                                    # Note, line nos start from 1.0, but indexes from 0

                #print(self.watches)#debug

        # Highlight comments
        fgcolour=cf.commentcolour
        #print("**"+commentcolour)# debug
        startIndex = '1.0'
        while startIndex:
            startIndex = self.asstxt.search(cf.commentprefix, startIndex, tk.END, regexp=False)
            if startIndex:
                endIndex = self.asstxt.index('%s lineend'% startIndex)
                self.asstxt.tag_add("comment", startIndex, endIndex) # add tag to k
                self.asstxt.tag_config("comment", foreground=fgcolour, font=self.asstxt['font'])
                startIndex = endIndex

        # Parse labels and add to self.watches as required
        self.labelList=[]
        fgcolour=cf.labelcolour
        for token in cf.labelspec:
            startIndex = '1.0'
            while startIndex:
                # need to look for : and > as label specifiers
                startIndex = self.asstxt.search(token, startIndex, tk.END, regexp=False)
                if startIndex:
                    lineStart = self.asstxt.index('%s linestart ' % startIndex)
                    lineno = int(lineStart.split(".")[0])
                    # Check line not commented
                    if  not self.asstxt.search(cf.commentprefix, lineStart, startIndex):
                        tagname=self.asstxt.get(lineStart, startIndex).lstrip()
                        #print(tagname)#debug
                        if tagname !="" : # Ignore if not a valid label
                            self.labelList.append(tagname) # Here store lineno as well for runfrom??
                            self.asstxt.tag_add(tagname, lineStart, startIndex) # add tag to k
                            self.asstxt.tag_config(tagname, foreground=fgcolour, font=self.asstxt['font'])
                            #print(lineStart, startIndex)# debug
                            # Check if a watch line
                        # Might still be a label-less dc/ds line, so still add the memory address
                        for index in range(len(self.watches)):
                            if lineno-1 == self.watches[index][0]:
                                self.watches[index][1] = tagname # Store label line num for adding watches
                                #print(self.watches[index][0],"**", lineno, tagname)# debug

                    startIndex = str(float(lineStart)+1) # start from next line
                    #print(self.labelList)#, labelLines)#debug

        # And highlights to brs, ldis etc. where the labels are used
        for word in self.labelList: # iterate over directive words list
            startIndex = '1.0'
            while startIndex:
                startIndex = self.asstxt.search("\\y"+word+"\\y", startIndex, tk.END, regexp=True)
                if startIndex:
                    #print(startIndex)# debug
                    lineStart = startIndex#self.asstxt.index('%s linestart ' % startIndex)
                    endIndex = self.asstxt.index('%s+%dc' % (startIndex, (len(word)))) # find end of word
                    #print(self.asstxt.get(startIndex, endIndex))
                    # Check line not commented
                    if not self.asstxt.search(cf.commentprefix, lineStart+" linestart", lineStart):
                        self.asstxt.tag_add(word, startIndex, endIndex) # add tag to k
                        self.asstxt.tag_config(word, foreground=fgcolour, font=self.boldfont)      # and color it with v
                    startIndex = endIndex # reset startIndex to continue searching
        return



    # Callback to toggle breakpoints
    def toggleBP(self, event=None):
        try:
            bpAdrStr = str(self.mcode_list.get("insert linestart", "insert linestart +2c"))
            #print("*"+bpAdrStr+"*") debug
            bpAdr = int(bpAdrStr, 16)
            #bpAdrStr = "adr"+bpAdrStr
            if bpAdr in self.Emu.BP:
                self.mcode_list.tag_remove(bpAdrStr, 1.0, "end")
                self.asstxt.tag_remove(bpAdrStr, 1.0, "end")
                for n in range(len(self.bpTagNames)):
                    if bpAdrStr == self.bpTagNames[n]: del self.bpTagNames[n]

                self.memLabel[bpAdr].config(bg="white")
                for adr in range(len(self.Emu.BP)):
                    if self.Emu.BP[adr]==bpAdr:
                        del self.Emu.BP[adr]
            else:
                self.Emu.BP.append(bpAdr)
                self.mcode_list.tag_add(bpAdrStr, "insert linestart", "insert lineend+1c")
                self.mcode_list.tag_configure(bpAdrStr, background=cf.bpColour)
                self.bpTagNames.append(bpAdrStr)
                lineNum = self.mcode_list.index("insert linestart")# debug
                self.asstxt.tag_add(bpAdrStr, lineNum+" linestart", lineNum+" lineend+1c")
                self.asstxt.tag_configure(bpAdrStr, background=cf.bpColour)
                self.memLabel[bpAdr].config(bg=cf.bpColour)
        except:
            bpAdr=None
            #print(bpAdr)#debug
        return 'break'

    def clearBPs(self):
        # clear all break points
        self.Emu.BP = []
        for tag in self.bpTagNames:
            self.asstxt.tag_delete(tag)
            #self.mcode_list.delete(tag)
        for mlab in self.memLabel:
            mlab.config(bg="white")
        self.bpTagNames = []

    # Handler when run entry point changed
    def initPC(self, event=None):
        self.Emu.PC = self.runDict[self.runFrom.get()]
        self.Emu.curPage = 0
        self.dispPC()
        #self.dispAllMemory()

    # Callbacks for syncing the text and mcode windows scrolling
    def yscroll1(self, *args):
        if self.asstxt.yview() != self.mcode_list.yview():
            self.mcode_list.yview_moveto(args[0])
            self.lntext.yview_moveto(args[0])
        self.vscroll.set(*args)

    def yscroll2(self, *args):
        if self.asstxt.yview() != self.mcode_list.yview():
            self.asstxt.yview_moveto(args[0])
            self.lntext.yview_moveto(args[0])
        self.vscroll.set(*args)
        
    def yscroll3(self, *args):
        if self.asstxt.yview() != self.lntext.yview():
            self.asstxt.yview_moveto(args[0])
            self.mcode_list.yview_moveto(args[0])
        self.vscroll.set(*args)

    def yview(self, *args):
        #connect the yview (scroll) actions together for asstxt, lntext and mcode_list panels
        self.asstxt.yview(*args)
        self.mcode_list.yview(*args)
        self.lntext.yview_moveto(self.asstxt.yview()[0])
        return
        
    def updateLineNos(self, event=None):
        #numOfLines = int(float(self.asstxt.index('end'))) # Get lines already present in asstxt window
        #endlines = int(self.asstxt.index('end').split('.')[0])
        #print(numOfLines, endlines)
        # Then pack out with same numberof lines as in text window
        
        #print("updateLineNos", self.asstxt.index('end').split('.')[0])# debug
        if self.asstxt.index('end').split('.')[0] != self.lntext.index('end').split('.')[0]:
            self.lntext.config(state="normal")
            self.lntext.delete(1.0, tk.END)
            for n in range(1, int(self.asstxt.index('end').split('.')[0])-1):
                self.lntext.insert(tk.END, str(n)+'\n')
            first, last = self.asstxt.yview()
            self.lntext.yview_moveto(first)
            self.lntext.config(state="disabled")
        return

    #### Project / folder support (modern IDE-style workspace)

    def loadConfig(self):
        """Load recent projects/files and window geometry from ~/.cocoide/config.json"""
        self.savedWindowGeom = None
        try:
            with open(self.configFile, encoding="utf-8") as f:
                cfg = json.load(f)
            self.recentProjects = [p for p in cfg.get("recentProjects", []) if os.path.isdir(p)]
            self.openedFiles = [p for p in cfg.get("recentFiles", []) if os.path.isfile(p)]
            self.savedWindowGeom = cfg.get("windowGeom") or None
            sf = cfg.get("startupFolder")
            if sf and os.path.isdir(sf):
                self.startupFolder = sf
            if not self.projectPath:
                rp = cfg.get("rootProject") or cfg.get("project")
                if rp and os.path.isdir(rp):
                    self.projectPath = rp
                    self.rootProjectPath = rp
            self._savedExpandedDirs = [p for p in cfg.get("expandedDirs", [])]
            if "autocomplete" in cfg:
                self.acEnabled = bool(cfg["autocomplete"])
        except Exception:
            pass

    def saveConfig(self):
        """Persist settings; called on exit and when the project changes."""
        try:
            if not os.path.isdir(self.configDir):
                os.makedirs(self.configDir)
            geom = ""
            try:
                geom = "%dx%d+%d+%d" % (self.master.winfo_width(), self.master.winfo_height(),
                                        self.master.winfo_x(), self.master.winfo_y())
            except Exception:
                pass
            cfg = {"recentProjects": self.recentProjects[:10],
                   "recentFiles": self.openedFiles[:15],
                   "project": self.rootProjectPath or "",
                   "rootProject": self.rootProjectPath or "",
                   "expandedDirs": sorted(self.expandedDirs)[:40],
                   "startupFolder": self.startupFolder or "",
                   "autocomplete": bool(getattr(self, "acEnabled", True)),
                   "windowGeom": geom}
            with open(self.configFile, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=1)
        except Exception as e:
            print("Could not save config:", e)

    def _rebuildRecentMenu(self):
        """Rebuild the File > Open Recent submenu (folders + files)."""
        m = getattr(self, "recentMenu", None)
        if m is None:
            return
        m.delete(0, tk.END)
        if self.recentProjects:
            m.add_command(label="Folders:", state=tk.DISABLED)
            for p in self.recentProjects[:8]:
                m.add_command(label=os.path.basename(p) or p,
                              command=lambda path=p: self.set_project(path))
            m.add_separator()
        if self.openedFiles:
            m.add_command(label="Files:", state=tk.DISABLED)
            for fp in self.openedFiles[:10]:
                name = os.path.basename(fp)
                parent = os.path.basename(os.path.dirname(fp))
                m.add_command(label="%s  (%s)" % (name, parent),
                              command=lambda path=fp: self.file_open(filepath=path))
        if not self.recentProjects and not self.openedFiles:
            m.add_command(label="(no recent items)", state=tk.DISABLED)
        m.add_separator()
        m.add_command(label="Clear List", command=self._clearRecent)

    def _clearRecent(self):
        self.recentProjects = []
        self.openedFiles = []
        self._rebuildRecentMenu()
        self.saveConfig()

    def show_open_menu(self, event=None):
        """Toolbar 'Open...' button: choose between a file and a project folder."""
        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="Open File...", command=self.file_open)
        menu.add_command(label="Open Folder as Project...", command=self.open_project_dialog)
        menu.add_separator()
        for p in self.recentProjects[:6]:
            menu.add_command(label="  " + os.path.basename(p),
                             command=lambda path=p: self.set_project(path))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def open_project_dialog(self, event=None):
        folder = filedialog.askdirectory(title="Select Project Folder",
                                         initialdir=self.startupFolder or self.homeDir)
        if folder:
            self.set_project(os.path.abspath(folder))
        return "break"

    def set_project(self, folder, startup=False):
        """Open a folder as the project root (VS Code style: one root window,
        sub-folders are expanded *inside* the tree, never replacing it)."""
        folder = os.path.abspath(folder)
        if not os.path.isdir(folder):
            messagebox.showerror("Project", "Folder not found:\n" + folder)
            return
        same_root = (folder == self.rootProjectPath)
        self.projectPath = folder
        self.rootProjectPath = folder
        if not same_root:
            self.expandedDirs = {folder}   # auto-expand the root itself
        else:
            self.expandedDirs.add(folder)  # keep previously expanded sub-folders
        self.startupFolder = folder
        if folder not in self.recentProjects:
            self.recentProjects.insert(0, folder)
        self.recentProjects = self.recentProjects[:10]
        self._populateProjectTree()
        self._rebuildRecentMenu()
        self.projmenu.entryconfig("Close Project",
                                  state=tk.NORMAL if self.projectPath else tk.DISABLED)
        self.saveConfig()
        if not startup:
            self.statusMsg.config(text="Project:\n" + os.path.basename(folder))
        try:
            self.projStatusLabel.config(text="Folder: " + folder)
        except Exception:
            pass
        return folder

    def close_project(self, event=None):
        self.projectPath = None
        self.rootProjectPath = None
        self.expandedDirs = set()
        self._populateProjectTree()
        self.saveConfig()
        return "break"

    def reveal_project_folder(self, event=None):
        """Reveal the project folder in Finder (macOS) / Explorer / Finder equivalents."""
        folder = self.projectPath or self.startupFolder
        if not folder:
            self.open_project_dialog()
            return
        try:
            if platform == "darwin":
                subprocess.Popen(["open", folder])
            elif platform.startswith("win"):
                subprocess.Popen(["explorer", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            print("Reveal failed:", e)
        return "break"

    def open_terminal_here(self, event=None):
        """Open a Terminal window in the project folder (macOS: Terminal.app)."""
        folder = self.projectPath or self.startupFolder or self.homeDir
        try:
            if platform == "darwin":
                safe = folder.replace("'", "'\\''")
                script = ('tell application "Terminal"\nactivate\n'
                          "do script \"cd '" + safe + "'\"\nend tell")
                subprocess.Popen(["osascript", "-e", script])
            elif platform.startswith("win"):
                subprocess.Popen(["cmd", "/c", "start", "cmd", "/k",
                                  'cd /d "' + folder + '"'])
            else:
                subprocess.Popen(["x-terminal-emulator", "--working-directory=" + folder])
        except Exception as e:
            print("Open terminal failed:", e)
        return "break"

    def new_file_in_project(self, event=None):
        """Create a new .asm file inside the project folder and open it."""
        if not self.projectPath:
            self.open_project_dialog()
            if not self.projectPath:
                return "break"
        filepath = filedialog.asksaveasfilename(title="New File in Project",
                                                initialdir=self.projectPath,
                                                defaultextension=cf.fileext,
                                                initialfile="newProg" + cf.fileext,
                                                filetypes=(('CDM8 Assembly', '*'+cf.fileext),
                                                           ('All files', '*.*')))
        if not filepath:
            return "break"
        try:
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("; " + os.path.basename(filepath) + "\n")
        except Exception as e:
            messagebox.showerror("New File", "Could not create file:\n%s" % e)
            return "break"
        self.file_open(filepath=filepath)
        self._populateProjectTree()
        return "break"

    def _buildProjectBrowser(self):
        """Create the collapsible project-file sidebar to the left of the editor."""
        panel = tk.Frame(self.mainPanel, name="projbrowser", bg="#fafafa",
                         highlightthickness=1, highlightbackground="#cccccc")
        header = tk.Frame(panel, bg="#ededed")
        header.pack(side=tk.TOP, fill=tk.X)
        self.projToggle = tk.Button(header, text="▾", width=2, relief=tk.FLAT, bd=0,
                                    command=self.toggleProjectBrowser)
        self.projToggle.pack(side=tk.LEFT)
        self.projTitle = tk.Label(header, text="PROJECT", anchor="w", bg="#ededed",
                                  font=(self.editorFontName, self.textsize, "bold"))
        self.projTitle.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(header, text="↻", width=2, relief=tk.FLAT, bd=0,
                  command=self._populateProjectTree).pack(side=tk.RIGHT)
        tk.Button(header, text="…", width=2, relief=tk.FLAT, bd=0,
                  command=self.open_project_dialog).pack(side=tk.RIGHT)

        body = tk.Frame(panel, bg="#fafafa")
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.projCanvas = tk.Canvas(body, bg="#fafafa", highlightthickness=0, width=180)
        vbar = ttk.Scrollbar(body, orient=tk.VERTICAL, command=self.projCanvas.yview)
        self.projCanvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.projCanvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.projFrame = tk.Frame(self.projCanvas, bg="#fafafa")
        self.projWin = self.projCanvas.create_window(0, 0, window=self.projFrame, anchor=tk.NW)

        def _conf_inner(event=None):
            # Debounce: rebuilding the tree fires a storm of <Configure> events;
            # recomputing the scrollregion on every one made the whole window
            # "jitter" and froze event processing. Coalesce them into one update.
            if getattr(self, "_projConfAfter", None):
                try:
                    self.projCanvas.after_cancel(self._projConfAfter)
                except Exception:
                    pass
            self._projConfAfter = self.projCanvas.after(
                50, lambda: self._updateProjScrollregion())
        self.projFrame.bind('<Configure>', _conf_inner)

        def _conf_canvas(event=None):
            # Only widen to fit content; never shrink below the canvas width,
            # otherwise reqwidth↔itemconfigure feedback loops resize the layout.
            try:
                self.projCanvas.itemconfigure(self.projWin,
                                              width=max(event.width, 160))
            except Exception:
                pass
        self.projCanvas.bind('<Configure>', _conf_canvas)
        self._bindMouseWheel(self.projCanvas)

        # Insert into the layout as column 0 (editor shifts to column 1 etc.).
        # IMPORTANT: only span rows 0-1 (editor + machine code). Row 2 holds the
        # Memory Watches panel; if the sidebar spanned it too, its 190px column
        # would cover the watches and they could never be seen/scrolled.
        panel.grid(row=0, column=0, sticky="nsew", rowspan=2)
        self.mainPanel.grid_columnconfigure(0, minsize=190)
        # NOTE: do NOT add weight to the sidebar column. The editor column keeps
        # weight=1, so resizing the window never "jitters" the whole layout.
        self.projPanel = panel
        self.projVisible = True
        self._projBusy = False        # guards against re-entrant rebuild loops
        self.projTreeItems = {}   # dirpath -> (row_index, label_widget)
        self._populateProjectTree()
        self.projmenu.entryconfig("Close Project",
                                  state=tk.NORMAL if self.projectPath else tk.DISABLED)

    def toggleProjectBrowser(self, event=None):
        if getattr(self, "projVisible", True):
            self.projCanvas.itemconfigure(self.projWin, state="hidden")
            self.mainPanel.grid_columnconfigure(0, minsize=28)
            self.projToggle.config(text="▸")
            self.projTitle.config(text="")
            self.projVisible = False
        else:
            self.projCanvas.itemconfigure(self.projWin, state="normal")
            self.mainPanel.grid_columnconfigure(0, minsize=190)
            self.projToggle.config(text="▾")
            root = self.rootProjectPath or self.projectPath
            self.projTitle.config(text=(os.path.basename(root).upper()[:16]
                                        if root else "PROJECT"))
            self.projVisible = True
        return "break"

    def _projHover(self, widget, on):
        """Highlight one tree row; remember it so a rebuild can clean up."""
        try:
            prev = getattr(self, "_projHoverW", None)
            if prev is not None and prev is not widget and prev.winfo_exists():
                prev.config(bg="#fafafa")
            if on:
                widget.config(bg="#e2ecf7")
                self._projHoverW = widget
            else:
                if widget.winfo_exists():
                    widget.config(bg="#fafafa")
                if prev is widget:
                    self._projHoverW = None
        except Exception:
            pass

    def _updateProjScrollregion(self):
        """Recompute the sidebar scroll region once (after debounced <Configure>)."""
        try:
            self._projConfAfter = None
            if not self.projFrame.winfo_exists():
                return
            self.projCanvas.configure(
                scrollregion=(0, 0, self.projCanvas.winfo_width(),
                              max(self.projFrame.winfo_reqheight(),
                                  self.projCanvas.winfo_height())))
        except Exception:
            pass

    def _toggleDirExpanded(self, path):
        """Expand/collapse a folder in place (VS Code style - the project root
        never changes; sub-folders just open inside the tree)."""
        if path in self.expandedDirs:
            self.expandedDirs.discard(path)
        else:
            self.expandedDirs.add(path)
            # keep the tree responsive on huge folders: cap how many are open
            if len(self.expandedDirs) > 40:
                self.expandedDirs = {self.rootProjectPath} | \
                    set(list(self.expandedDirs)[-39:])
        self._populateProjectTree()

    def _showDirMenu(self, event, path):
        """Right-click (macOS Ctrl-click included) menu for a folder row."""
        m = tk.Menu(self, tearoff=0)
        expanded = path in self.expandedDirs
        m.add_command(label=("Collapse" if expanded else "Expand"),
                      command=lambda p=path: self._toggleDirExpanded(p))
        m.add_command(label="Open in Finder",
                      command=lambda p=path: subprocess.Popen(["open", p])
                      if platform == "darwin" else self.reveal_project_folder())
        m.add_command(label="New File Here...",
                      command=lambda p=path: self.new_file_in_dir(p))
        m.tk_popup(event.x_root, event.y_root)
        return "break"

    def revealInTree(self, filepath):
        """Expand every ancestor folder of *filepath* inside the tree (root
        stays untouched), highlight the active file and scroll it into view."""
        root = self.rootProjectPath or self.projectPath
        if not root:
            return
        d = os.path.dirname(os.path.abspath(filepath))
        guard = 0
        while d and d.startswith(root) and d != root and guard < 40:
            self.expandedDirs.add(d)
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
            guard += 1
        self._populateProjectTree()
        # scroll the row of the currently-open file into view
        try:
            for child in self.projFrame.winfo_children():
                txt = child.cget("text")
                if isinstance(txt, str) and txt.strip().lstrip("\u25CF").strip() \
                        == os.path.basename(filepath):
                    self.projCanvas.update_idletasks()
                    total = max(1, self.projFrame.winfo_reqheight())
                    frac = child.winfo_y() / float(total)
                    self.projCanvas.yview_moveto(max(0.0, min(frac - 0.1, 1.0)))
                    break
        except Exception:
            pass

    def new_file_in_dir(self, dirpath):
        """Create a new .asm file inside dirpath and open it in the editor."""
        filepath = filedialog.asksaveasfilename(title="New File in Folder",
                                                initialdir=dirpath,
                                                defaultextension=cf.fileext,
                                                initialfile="newProg" + cf.fileext,
                                                filetypes=(('CDM8 Assembly', '*'+cf.fileext),
                                                           ('All files', '*.*')))
        if not filepath:
            return
        try:
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("; " + os.path.basename(filepath) + "\n")
        except Exception as e:
            messagebox.showerror("New File", "Could not create file:\n%s" % e)
            return
        self.file_new()
        self.file_open(filepath=filepath)   # reveals the path in the tree too

    def _populateProjectTree(self, event=None):
        """Fill the sidebar with the *full* project tree under the opened root
        folder. Folders expand/collapse in place (like VS Code Explorer); the
        root itself never changes when you browse into a sub-folder."""
        if not hasattr(self, "projFrame"):
            return
        if getattr(self, "_projBusy", False):
            return                      # re-entrancy guard (no rebuild loops)
        self._projBusy = True
        try:
            self._rebuildProjectTree()
        finally:
            self._projBusy = False

    def _rebuildProjectTree(self):
        # remember scroll position so expanding a node does not jump the view
        try:
            first = self.projCanvas.yview()[0]
        except Exception:
            first = 0.0
        for child in self.projFrame.winfo_children():
            child.destroy()
        self._projHoverW = None         # old highlighted rows no longer exist
        self.projTreeItems = {}
        bold = (self.editorFontName, self.textsize, "bold")
        norm = (self.editorFontName, self.textsize)
        row = [0]

        def addLabel(text, fg="#000000", fontspec=norm, indent=0, command=None,
                     bg="#fafafa", rclick=None, tip=None):
            l = tk.Label(self.projFrame, text=text, anchor="w", justify=tk.LEFT,
                         fg=fg, font=fontspec, bg=bg, padx=4 + indent*12,
                         cursor="hand2")
            l.grid(row=row[0], column=0, sticky="ew")
            if command:
                l.bind("<Button-1>", command)
                # Hover highlight only when the pointer actually moves over the
                # row (plain <Enter> fires on every tree rebuild and produced an
                # event storm that froze the UI). No tooltips in the project
                # tree: they were empty/invisible boxes with no real value -
                # full paths are shown in the window title bar instead.
                l.bind("<Motion>", lambda e, ww=l: self._projHover(ww, True))
                l.bind("<Leave>", lambda e, ww=l: self._projHover(ww, False))
            if rclick:
                l.bind("<Button-2>", rclick)          # macOS 2-finger click
                l.bind("<Button-3>", rclick)
                l.bind("<Control-Button-1>", rclick)  # Ctrl+click on Mac
            row[0] += 1
            return l

        root = self.rootProjectPath or self.projectPath
        if not root:
            addLabel("No folder open", fg="#888888")
            addLabel('Click "\u2026" to open', fg="#888888")
            addLabel("a task folder", fg="#888888")
        else:
            title = os.path.basename(root) or root
            self.projTitle.config(text=title.upper()[:16])
            addLabel(title, fontspec=bold, fg="#333333",
                     command=lambda e: self.open_project_dialog(),
                     rclick=lambda e: self._showDirMenu(e, root),
                     tip=lambda: root + "\nClick: open another folder\n" \
                                       "Right-click: menu")
            self._addTreeLevel(root, 0, bold, norm, addLabel)
        self.projFrame.update_idletasks()
        try:
            self.projCanvas.yview_moveto(first)
        except Exception:
            pass

    def _addTreeLevel(self, dirpath, depth, bold, norm, addLabel):
        """Recursively render one directory level of the project tree."""
        if depth > 12:
            return
        asmFiles, otherFiles, dirs = [], [], []
        try:
            entries = sorted(os.listdir(dirpath), key=lambda s: s.lower())
        except Exception:
            addLabel(("  "*depth) + "\u26A0 no access", fg="#aa5500", indent=depth)
            return
        for name in entries:
            if name.startswith("."):
                continue
            full = os.path.join(dirpath, name)
            try:
                isdir = os.path.isdir(full)
            except OSError:
                continue
            if isdir:
                dirs.append((name, full))
            elif name.lower().endswith(cf.fileext):
                asmFiles.append((name, full))
            else:
                otherFiles.append((name, full))
        # VS Code ordering: folders first, then files
        for name, full in dirs:
            expanded = full in self.expandedDirs
            arrow = "\u25BE" if expanded else "\u25B8"   # ▾ / ▸
            lbl = addLabel("%s %s/" % (arrow, name), fontspec=bold, fg="#333333",
                           indent=depth,
                           command=lambda e, p=full: self._toggleDirExpanded(p),
                           rclick=lambda e, p=full: self._showDirMenu(e, p),
                           tip=lambda f=full, x=expanded: f + (
                               "\nClick to collapse" if x else "\nClick to expand"))
            self.projTreeItems[full] = (lbl, expanded)
            if expanded:
                self._addTreeLevel(full, depth+1, bold, norm, addLabel)
        for name, full in asmFiles:
            mark = "\u25CF " if full == self.file_path else "   "
            lbl = addLabel(mark+name, fg="#0b6e0b", indent=depth,
                           command=lambda e, p=full: self.file_open(filepath=p),
                           tip=lambda f=full: f + "\nClick: open in editor tab")
            if full == self.file_path:
                lbl.config(font=bold)
        for name, full in otherFiles:
            ext = os.path.splitext(name)[1].lower()
            if ext in (".txt", ".md", ".log", ".obj", ".s", ""):
                act, hint = ("\nClick: open in Machine Code tab",
                             lambda e, p=full: self.openFileInTab(p))
            elif ext in (".pdf", ".doc", ".docx"):
                act, hint = ("\nClick: open in system viewer",
                             lambda e, p=full: self.openExternalFile(p))
            else:
                act, hint = ("\nClick: open in system viewer",
                             lambda e, p=full: self.openExternalFile(p))
            addLabel("   " + name, fg="#5555aa", indent=depth,
                     command=hint, tip=lambda f=full, a=act: f + a)

    def openExternalFile(self, filepath):
        """Open non-asm project files (PDF briefs, READMEs...) with the system viewer."""
        try:
            if platform == "darwin":
                subprocess.Popen(["open", filepath])
            elif platform.startswith("win"):
                os.startfile(filepath)
            else:
                subprocess.Popen(["xdg-open", filepath])
        except Exception as e:
            print("Could not open", filepath, e)

    #### Bottom tab strip (Machine Code + opened files)  ##################

    def _rebuildMcodeTabBar(self):
        """Redraw the small tab bar above the Machine Code panel."""
        for w in self.mcodeTabBar.winfo_children():
            w.destroy()
        self.tabButtons = {}
        boldf = getattr(self, "boldfont", None) or ("TkDefaultFont", 10, "bold")
        normf = getattr(self, "smallfont", None) or ("TkDefaultFont", 10)
        for key, path in self.viewTabs:
            label = "Machine Code" if key == "__mcode__" else os.path.basename(path)
            active = (key == self.activeViewTab)
            cell = tk.Frame(self.mcodeTabBar,
                            bg="#ffffff" if active else "#e6e6e6",
                            highlightbackground="#cccccc",
                            highlightthickness=1)
            cell.pack(side=tk.LEFT, fill=tk.Y)
            lbl = tk.Label(cell, text=label, padx=8, pady=2, cursor="hand2",
                           bg=cell.cget("bg"), fg="#222222" if active else "#666666",
                           font=boldf if active else normf)
            lbl.pack(side=tk.LEFT)
            lbl.bind("<Button-1>", lambda e, k=key: self.selectViewTab(k))
            if key != "__mcode__":
                x = tk.Label(cell, text="\u2715", padx=4, pady=2, cursor="hand2",
                             bg=cell.cget("bg"), fg="#888888", font=normf)
                x.pack(side=tk.LEFT)
                x.bind("<Button-1>", lambda e, k=key: self.closeViewTab(k))
            self.tabButtons[key] = cell
        # stretchy filler so tabs don't span the whole width
        tk.Frame(self.mcodeTabBar, bg="#e6e6e6").pack(side=tk.LEFT, fill=tk.X, expand=True)

    def selectViewTab(self, key):
        self.activeViewTab = key
        try:
            self._mcodeFrame.tk_raise() if key == "__mcode__" else None
        except Exception:
            pass
        # show/hide content frames
        self._mcodeFrame.grid(row=0, column=0, sticky="nsew")
        for fp, fr in self._fileTabFrames.items():
            if fp == key:
                fr.grid(row=0, column=0, sticky="nsew")
                fr.tkraise()
            else:
                fr.grid_remove()
        if key == "__mcode__":
            self._mcodeFrame.tkraise()
        self._rebuildMcodeTabBar()

    def openFileInTab(self, filepath):
        """Open a project file as a new tab in the bottom area (idempotent)."""
        if filepath in self.viewTabs:
            self.selectViewTab(filepath)
            return
        self.viewTabs.append((filepath, filepath))
        frame = tk.Frame(self.mcodeTabStack, bg="white")
        frame.grid(row=0, column=0, sticky="nsew")
        txt = tk.Text(frame, wrap=tk.NONE, font=self.defaulttxtfont, bg="white",
                      relief=tk.FLAT, bd=0)
        vs = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=txt.yview)
        hs = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=txt.xview)
        txt.config(yscrollcommand=vs.set, xscrollcommand=hs.set)
        vs.pack(side=tk.RIGHT, fill=tk.Y)
        hs.pack(side=tk.BOTTOM, fill=tk.X)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        txt.bind("<Key>", lambda e: "break")   # read-only listing
        self._bindMouseWheel(txt)
        title = tk.Label(frame, text=os.path.basename(filepath), anchor="w",
                         bg="#f2f2f2", font=self.smallfont, padx=4)
        title.place(relx=1.0, rely=0.0, anchor="ne")
        try:
            with open(filepath, encoding="utf-8", errors="replace") as f:
                txt.insert("1.0", f.read())
        except Exception as ex:
            txt.insert("1.0", "Cannot display this file inline:\n%s" % ex)
        txt.edit_modified(False)
        self._fileTabFrames[filepath] = frame
        self.selectViewTab(filepath)

    def closeViewTab(self, key):
        if key == "__mcode__":
            return
        self.viewTabs = [t for t in self.viewTabs if t[0] != key]
        fr = self._fileTabFrames.pop(key, None)
        if fr:
            try: fr.destroy()
            except Exception: pass
        if self.activeViewTab == key:
            self.selectViewTab("__mcode__")
        else:
            self._rebuildMcodeTabBar()

    def closeAllFileTabs(self):
        """Called on compile: bring focus back to the Machine Code listing."""
        if self.viewTabs and self.activeViewTab != "__mcode__":
            self.selectViewTab("__mcode__")

    #### Editor tabs (VS Code style multiple open files)  #################

    def _onTextModifiedFlag(self, event=None):
        """<<Modified>> virtual event: keep the active tab's dirty dot fresh."""
        try:
            if self._tabSwapGuard:
                return
            mod = self.asstxt.edit_modified()
            if mod and self.editorTabs:
                self.editorTabs[self.activeTab]["dirty"] = True
                self._rebuildEditorTabBar()
                self.set_title()
            self.asstxt.edit_modified(False)   # reset so we get the event again
        except Exception:
            pass

    def _rebuildEditorTabBar(self):
        if not hasattr(self, "editorTabBar"):
            return
        for w in self.editorTabBar.winfo_children():
            w.destroy()
        boldf = getattr(self, "boldfont", None) or ("TkDefaultFont", 10, "bold")
        normf = getattr(self, "smallfont", None) or ("TkDefaultFont", 10)
        for i, tab in enumerate(self.editorTabs):
            active = (i == self.activeTab)
            name = ("\u25cf " if tab["dirty"] else "") + tab["name"]
            cell = tk.Frame(self.editorTabBar,
                            bg="#ffffff" if active else "#dcdcdc",
                            highlightbackground="#bbbbbb", highlightthickness=1)
            cell.pack(side=tk.LEFT, fill=tk.Y)
            lbl = tk.Label(cell, text=name, padx=8, pady=2, cursor="hand2",
                           bg=cell.cget("bg"), fg="#222222" if active else "#666666",
                           font=boldf if active else normf)
            lbl.pack(side=tk.LEFT)
            lbl.bind("<Button-1>", lambda e, k=i: self.switchToTab(k))
            x = tk.Label(cell, text="\u2715", padx=4, pady=2, cursor="hand2",
                         bg=cell.cget("bg"), fg="#999999", font=normf)
            x.pack(side=tk.LEFT)
            x.bind("<Button-1>", lambda e, k=i: self.closeTab(k))
        tk.Frame(self.editorTabBar, bg="#e6e6e6").pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _storeActiveBuffer(self):
        """Snapshot current editor content into its tab record."""
        tab = self.editorTabs[self.activeTab]
        try:
            tab["content"] = self.asstxt.get("1.0", tk.END)
            tab["insert"] = self.asstxt.index(tk.INSERT)
        except Exception:
            pass

    def switchToTab(self, idx, event=None):
        if idx == self.activeTab or not (0 <= idx < len(self.editorTabs)):
            return "break"
        self.acHide()
        self._storeActiveBuffer()
        self.activeTab = idx
        tab = self.editorTabs[idx]
        self._tabSwapGuard = True
        try:
            self.file_path = tab["path"]
            self.asstxt.delete("1.0", tk.END)
            self.asstxt.insert("1.0", tab.get("content", ""))
            self.asstxt.mark_set(tk.INSERT, tab.get("insert", "1.0"))
            self.asstxt.edit_modified(False)
            self.asstxt.edit_separator()
            self.highlighter()          # re-parse labels/watch/mcode for this file
            self.set_title()
        finally:
            self._tabSwapGuard = False
        self._rebuildEditorTabBar()
        self._populateProjectTree()     # refresh the \u25cf active-file marker
        return "break"

    def openInNewTab(self, filepath, contents=None):
        """Open a file as an editor tab (reuse existing tab if already open)."""
        for i, tab in enumerate(self.editorTabs):
            if tab["path"] == filepath:
                return self.switchToTab(i)
        self._storeActiveBuffer()
        if contents is None:
            try:
                with open(filepath, encoding="utf-8", errors="replace") as f:
                    contents = f.read()
            except Exception as ex:
                messagebox.showerror("Open failed", str(ex))
                return "break"
        # replace a pristine empty Untitled tab instead of piling up blanks
        t = self.editorTabs[self.activeTab]
        cur = self.asstxt.get("1.0", tk.END).strip()
        if t["path"] is None and not cur and not t["dirty"]:
            tab = t
        else:
            tab = {"path": None, "name": "", "dirty": False}
            self.editorTabs.append(tab)
            self.activeTab = len(self.editorTabs) - 1
        tab.update({"path": filepath, "name": os.path.basename(filepath),
                    "dirty": False, "content": contents + "\n",
                    "insert": "1.0"})
        self.file_path = filepath
        self._tabSwapGuard = True
        try:
            self.asstxt.delete("1.0", tk.END)
            self.asstxt.insert("1.0", contents)
            self.asstxt.edit_modified(False)
            self.asstxt.edit_reset()
            self.asstxt.edit_separator()
            self.mcode_list.delete(1.0, tk.END)
            self.highlighter()
            self.asstxt.see("1.0")
            self.set_title()
        finally:
            self._tabSwapGuard = False
        self._rebuildEditorTabBar()
        self._populateProjectTree()
        return "break"

    def closeTab(self, idx, event=None):
        if not (0 <= idx < len(self.editorTabs)):
            return "break"
        tab = self.editorTabs[idx]
        # flush live edits if closing the visible tab
        if idx == self.activeTab:
            self._storeActiveBuffer()
        if tab["dirty"]:
            ans = messagebox.askyesno(
                "Unsaved changes",
                "'%s' has unsaved changes.\nSave before closing?" % tab["name"])
            if ans:
                if idx != self.activeTab:
                    self.switchToTab(idx)
                self.file_save()
                if self.editorTabs[idx]["dirty"]:
                    return "break"   # save was cancelled
            elif not ans:
                pass  # discard
        self.editorTabs.pop(idx)
        if not self.editorTabs:      # never leave the strip empty
            self.editorTabs = [{"path": None, "name": "Untitled", "dirty": False,
                                "content": "", "insert": "1.0"}]
        if idx == self.activeTab:
            self.activeTab = min(idx, len(self.editorTabs) - 1)
            t = self.editorTabs[self.activeTab]
            self.file_path = t["path"]
            self._tabSwapGuard = True
            try:
                self.asstxt.delete("1.0", tk.END)
                self.asstxt.insert("1.0", t.get("content", ""))
                self.asstxt.edit_modified(False)
                self.highlighter()
                self.set_title()
            finally:
                self._tabSwapGuard = False
        elif idx < self.activeTab:
            self.activeTab -= 1
        self._rebuildEditorTabBar()
        self._populateProjectTree()
        return "break"

    def nextTab(self, event=None):
        if len(self.editorTabs) > 1:
            self.switchToTab((self.activeTab + 1) % len(self.editorTabs))
        return "break"

    def prevTab(self, event=None):
        if len(self.editorTabs) > 1:
            self.switchToTab((self.activeTab - 1) % len(self.editorTabs))
        return "break"

    #### Quick-open file picker (Cmd+P)  ##################################

    def _collectProjectFiles(self, root, limit=3000):
        out = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fn in filenames:
                if fn.startswith("."):
                    continue
                out.append(os.path.join(dirpath, fn))
                if len(out) >= limit:
                    return out
        return out

    def showQuickOpen(self, event=None):
        root = self.rootProjectPath or self.projectPath
        if not root or not os.path.isdir(root):
            self.open_project_dialog()
            return "break"
        if getattr(self, "_qoWin", None) and self._qoWin.winfo_exists():
            self._qoWin.destroy()
        win = tk.Toplevel(self)
        self._qoWin = win
        win.title("Open File")
        try:
            win.attributes("-topmost", True)
            win.transient(self)
        except Exception:
            pass
        win.geometry("+%d+%d" % (self.master.winfo_rootx()+120,
                                 self.master.winfo_rooty()+120))
        win.resizable(True, True)
        ent = tk.Entry(win, font=("Menlo", 14) if platform == "darwin" else ("Courier", 14),
                       relief=tk.FLAT)
        ent.pack(fill=tk.X, padx=6, pady=(6, 2))
        lb = tk.Listbox(win, height=16, width=70, font=self.defaulttxtfont,
                        activestyle="none", relief=tk.FLAT,
                        selectbackground="#1a5fb4", selectforeground="white")
        lb.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        allFiles = self._collectProjectFiles(root)
        rel = [(os.path.relpath(f, root), f) for f in allFiles]
        state = {"items": []}

        def refresh(*_):
            q = ent.get().strip().lower().replace(" ", "")
            rows = []
            for r, full in rel:
                if not q or self._fuzzyScore(q, r) is not None:
                    score = self._fuzzyScore(q, r) if q else 0
                    rows.append((score if isinstance(score, int) else 999, r, full))
            rows.sort(key=lambda it: (it[0], len(it[1])))
            state["items"] = rows[:60]
            lb.delete(0, tk.END)
            for _, r, _f in state["items"]:
                lb.insert(tk.END, "  " + r)
            if state["items"]:
                lb.selection_set(0)

        def openSel(*_):
            sel = lb.curselection()
            if not sel or sel[0] >= len(state["items"]):
                return "break"
            path = state["items"][sel[0]][2]
            win.destroy()
            ext = os.path.splitext(path)[1].lower()
            if ext in ("", ".asm", ".obj", ".txt", ".s"):
                self.file_open(filepath=path)
            else:
                self.openExternalFile(path)
            return "break"

        ent.bind("<KeyRelease>", refresh)
        ent.bind("<Return>", openSel)
        lb.bind("<Return>", openSel)
        lb.bind("<Double-Button-1>", openSel)
        win.bind("<Escape>", lambda e: win.destroy())
        for seq in ("<Down>", "<Up>"):
            delta = 1 if seq == "<Down>" else -1
            def nav(e, d=delta):
                if not lb.size():
                    return "break"
                cur = (lb.curselection() or ((0,),))[0][0]
                cur = max(0, min(lb.size()-1, cur + d))
                lb.selection_clear(0, tk.END)
                lb.selection_set(cur)
                lb.see(cur)
                return "break"
            ent.bind(seq, nav)
        refresh()
        ent.focus_set()
        return "break"

    #### Command palette (Cmd+Shift+P)  ###################################

    def _paletteCommands(self):
        cmds = [
            ("Open Folder as Project\u2026", lambda: self.open_project_dialog(), "Cmd+Shift+O"),
            ("New File in Project", lambda: self.new_file_in_project(), ""),
            ("New File", lambda: self.file_new(), ""),
            ("Open File\u2026", lambda: self.file_open(), ""),
            ("Save", lambda: self.file_save(), ""),
            ("Save As\u2026", lambda: self.file_save_as(), ""),
            ("Compile", lambda: self.compileText(), "Cmd+B"),
            ("Compile & Run", lambda: self.compileRun(), "F5"),
            ("Run", lambda: self.runProg(), "Cmd+R"),
            ("Step Once", lambda: self.stepOnce(), ""),
            ("Toggle Breakpoint at Cursor", lambda: self.toggleBPAtCursor(), ""),
            ("Clear Breakpoints", lambda: self.clearBPs(), ""),
            ("Go to Line\u2026", lambda: self.gotoLineDialog(), "Cmd+G"),
            ("Find\u2026", lambda: self.focusSearchBox(), "Cmd+F"),
            ("Trigger Completion", lambda: self.acTrigger(), "Cmd+Space"),
            ("Toggle Auto-completion", lambda: self.toggleAutocomplete(), ""),
            ("Reveal Project Folder in Finder", lambda: self.reveal_project_folder(), ""),
            ("Open Terminal in Project Folder", lambda: self.open_terminal_here(), ""),
            ("Close Project", lambda: self.close_project(), ""),
            ("Show Manual", lambda: self.helpwin(), ""),
            ("About CocoIDE", lambda: self.aboutDialog(), ""),
        ]
        # recent projects & files become palette entries too
        for p in (self.recentProjects or [])[:6]:
            name = os.path.basename(p) or p
            cmds.append(("Project: " + name, lambda path=p: self.set_project(path), ""))
        for fp in (self.openedFiles or [])[:8]:
            nm = os.path.basename(fp)
            par = os.path.basename(os.path.dirname(fp))
            cmds.append(("Open: %s (%s)" % (nm, par),
                         lambda path=fp: self.file_open(filepath=path), ""))
        return cmds

    def _fuzzyScore(self, query, text):
        """Simple subsequence fuzzy match; lower = better, None = no match."""
        q = query.lower().replace(" ", "")
        t = text.lower()
        if not q:
            return 0
        pos, score = -1, 0
        for ch in q:
            pos = t.find(ch, pos + 1)
            if pos == -1:
                return None
            score += pos  # prefer early matches
        return score

    def showCmdPalette(self, event=None):
        if getattr(self, "_paletteWin", None) and self._paletteWin.winfo_exists():
            self._paletteWin.destroy()
        win = tk.Toplevel(self)
        self._paletteWin = win
        win.title("Command Palette")
        win.attributes("-topmost", True)
        try:
            win.transient(self)
        except Exception:
            pass
        w, h = 560, 380
        try:
            x = self.master.winfo_rootx() + max(0, (self.master.winfo_width() - w)//2)
            y = self.master.winfo_rooty() + 120
        except Exception:
            x, y = 200, 200
        win.geometry("+%d+%d" % (x, y))
        win.resizable(False, False)
        ent = tk.Entry(win, font=("Menlo", 14) if platform == "darwin" else ("Courier", 14),
                       relief=tk.FLAT)
        ent.pack(fill=tk.X, padx=6, pady=(6, 2))
        lb = tk.Listbox(win, height=14, font=self.defaulttxtfont, activestyle="none",
                        relief=tk.FLAT, selectbackground="#1a5fb4", selectforeground="white")
        lb.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))
        cmds = self._paletteCommands()
        state = {"items": []}

        def refresh(*_):
            q = ent.get().strip()
            lb.delete(0, tk.END)
            items = []
            for c in cmds:
                sc = self._fuzzyScore(q, c[0]) if q else 0
                if q and sc is None:
                    continue
                items.append((sc, c))
            items.sort(key=lambda it: it[0])
            state["items"] = [c for _, c in items][:40]
            for name, _, acc in state["items"]:
                lb.insert(tk.END, ("  %-46s %s" % (name, acc)).rstrip())
            if state["items"]:
                lb.selection_clear(0, tk.END)
                lb.selection_set(0)

        def runSel(*_):
            sel = lb.curselection()
            if not sel or sel[0] >= len(state["items"]):
                return "break"
            win.destroy()
            self.after(30, state["items"][sel[0]][1])
            return "break"

        ent.bind("<KeyRelease>", refresh)
        ent.bind("<Down>", lambda e: (lb.selection_clear(0, tk.END),
                                      lb.selection_set(min(lb.size()-1, (lb.curselection() or ((-1,)),)[0][0]+1)),
                                      lb.see(tk.ACTIVE), "break")[3] if lb.size() else "break")
        ent.bind("<Up>", lambda e: (lb.selection_clear(0, tk.END),
                                    lb.selection_set(max(0, (lb.curselection() or ((0,),))[0][0]-1)),
                                    lb.see(tk.ACTIVE), "break")[3] if lb.size() else "break")
        ent.bind("<Return>", runSel)
        lb.bind("<Return>", runSel)
        lb.bind("<Double-Button-1>", runSel)
        win.bind("<Escape>", lambda e: win.destroy())
        refresh()
        ent.focus_set()
        return "break"

    def _bindMouseWheel(self, widget):
        """Two-finger scroll on macOS (MouseWheel/delta) and Linux (buttons 4/5)."""
        def onWheel(event):
            if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
                widget.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5 or getattr(event, "delta", 0) < 0:
                widget.yview_scroll(1, "units")
            return "break"
        widget.bind("<MouseWheel>", onWheel)
        widget.bind("<Button-4>", onWheel)
        widget.bind("<Button-5>", onWheel)

    #######  Enhanced compiler diagnostics (CDM8)  #######
    # CDM8 operand categories, straight from cocas.iset:
    #   bi  = two register operands      e.g. add rA, rB / ld rA, rB
    #   un  = one register (ldi/ldsa: reg + value)
    #   br  = branch to a label/number
    #   zer = no operands                e.g. halt, rts, pushall
    #   spmove = stack-pointer ops       addsp/setsp <number>
    _DIAG_FORMS = {
        "bi":     "rA, rB          (two registers)",
        "un":     "rA              (one register)",
        "br":     "label           (a label or number)",
        "zer":    "(no operands)",
        "spmove": "<number>        (stack offset)",
        "osix":   "<n>             (OS call number)",
    }

    def _diagForm(self, op):
        """Return the legal operand form of an instruction/macro name."""
        try:
            if op in cocas.iset:
                cat = cocas.iset[op][1]
                for nm, val in (("bi", 2), ("un", 1), ("zer", 0), ("br", -1),
                                ("spmove", -2), ("osix", -3)):
                    if cat == val:
                        return self._DIAG_FORMS[nm]
                return None
        except Exception:
            pass
        try:  # macro library?  standard.mlb lines look like:  jmp:  ...
            mlb = resPath("standard.mlb")
            import re as _re
            with open(mlb) as f:
                for line in f:
                    m = _re.match(r"^([A-Za-z]\w*):\s*$", line.rstrip())
                    if m and m.group(1).lower() == op:
                        return "macro call – see standard.mlb"
        except Exception:
            pass
        return None

    def diagnoseError(self, msg, errLineNo=None):
        """Produce a concrete hint ('what to do instead') for a terse
        cocas.py error message. Returns plain text (or None)."""
        import re as _re
        low = msg.lower()
        src = ""
        if errLineNo:
            try:
                src = self.asstxt.get("%d.0" % errLineNo, "%d.end" % errLineNo)
            except Exception:
                src = ""
        stripped = src.lstrip()
        opcode = stripped.split()[0].rstrip(":,").lower() if stripped else ""
        if opcode.endswith(":"):
            opcode = opcode[:-1]
        hint = None

        if "register expected" in low:
            form = self._diagForm(opcode)
            hint = ("'%s' requires register operand(s): %s."
                    % (opcode or "this instruction",
                       form or "see the instruction set"))
            if opcode in ("add", "sub", "and", "or", "xor", "cmp", "addc",
                          "move", "ld", "st", "ldc"):
                hint += ("\nThe CDM8 has NO 'add register, constant' form — "
                         "you cannot combine a register with a number here.")
                hint += ("\nTo add a constant:  ldi rB, <const>  then  add rA, rB"
                         "\nExample:  add r0, r1      ✓        add r0, 1      ✗")
            elif opcode in ("not", "neg", "dec", "inc", "shr", "shla",
                            "shra", "rol", "push", "pop", "ldi", "ldsa"):
                if opcode in ("ldi", "ldsa"):
                    hint += ("\nCorrect forms:  ldi rA, <value>   or   "
                             "ldsa rA, template.field")
                else:
                    hint += ("\nExample:  inc r0      ✓        inc 5      ✗"
                             "\nFor constants use ldi:  ldi r0, 5")

        elif "comma expected" in low:
            hint = ("Operands must be separated by a comma:  'op rA, rB'. "
                    "Spaces alone are not enough.")
            hint += "\nExample:  add r0 r1 →  add r0, r1"

        elif "invalid opcode" in low:
            m = _re.search(r"invalid opcode:\s*(\S+)", low)
            bad = m.group(1) if m else opcode
            cands = [k for k in cocas.iset if k.startswith(bad[:2])]
            hint = ("'%s' is not a CDM8 instruction or defined macro." % bad)
            if cands:
                hint += " Did you mean: " + ", ".join(sorted(cands)[:8]) + "?"
            hint += ("\nRemember: load-immediate is 'ldi', jump-to-subroutine "
                     "is 'jsr', conditional jumps are 'beq/bne/blt/...'.")

        elif "only one operand expected" in low:
            form = self._diagForm(opcode)
            hint = ("'%s' takes exactly ONE operand (%s)."
                    % (opcode or "this instruction",
                       form or "one register"))
            if opcode in ("inc", "dec", "not", "neg", "shr", "shla",
                          "shra", "rol", "push", "pop"):
                hint += ("\nExample:  inc r0        ✓"
                         "\nTwo-operand arithmetic uses add/sub/and/or/xor:  "
                         "add r0, r1")

        elif "label or number expected" in low:
            hint = ("Branches (beq, bne, br, jsr…) need an existing label or "
                    "a numeric address.")
            if opcode:
                hint += "\nCheck spelling of the label used after '%s'." % opcode
            hint += "\nLabels end with ':' and must be defined somewhere in the file."

        elif "not found" in low and "label" in low:
            m = _re.search(r"label (\S+) not found", low)
            lbl = m.group(1) if m else "?"
            hint = ("The label '%s' is never defined in this file." % lbl)
            hint += ("\nAdd a definition such as '%s:' on its own line, "
                     "or fix the spelling where it is used." % lbl)

        elif "unexpected text" in low:
            hint = ("Extra text after the operands. A comment must start "
                    "with '#'.")
            if src:
                hint += "\nOffending line:  " + src.strip()

        elif "label or opcode expected" in low:
            hint = ("The line starts with something the assembler cannot "
                    "parse. Lines must begin with a label (name:), an "
                    "instruction, or whitespace.")
            if src:
                hint += "\nOffending line:  " + src.strip()

        elif "decimal out of range" in low:
            hint = ("Byte values must fit in 0…255 (signed −128…127 for "
                    "arithmetic). Split larger constants across bytes/"
                    "template fields, or use dc with several values.")

        elif "illegal register number" in low:
            hint = "Registers are r0–r3 only (plus r0h/r0l/r1h/r1l halves, sp, pc)."

        elif "expect a digit after a $" in low:
            hint = "'$' introduces a hex literal, e.g. $FF, $0A."

        elif "runaway string" in low:
            hint = "An opening \" has no matching closing quote on that line."

        elif "unknown escape character" in low:
            hint = ("Valid escapes inside strings: \\n \\t \\\\ \\\" etc. "
                    "Check the character after the backslash.")

        elif "numerical address expected" in low:
            hint = ("'org'/'ds' style directives need a numeric address "
                    "(e.g. org $80), not a label defined later.")

        elif "data expected" in low:
            hint = "'dc' needs at least one value:  dc $01,$02  or  dc \"text\""

        elif "does not match definition of macro" in low:
            hint = ("Wrong number of arguments for this macro call. "
                    "Open standard.mlb (or your macro definition between "
                    "macro:/mend:) and count the parameters.")

        elif "illegal separator" in low:
            hint = "List items in dc/ds must be separated by commas."

        elif "overlapping asect" in low:
            hint = ("Two sections were placed at overlapping addresses. "
                    "Move one section's 'asect' address (or shorten the "
                    "other section) so they don't collide.")

        elif "memory overflow" in low:
            hint = "A page holds 256 bytes; split code/data across pages ($page=n)."

        elif "negative out of range" in low:
            hint = "The computed value is negative but must be a positive byte/word."

        elif "reserved by assembler" in low:
            hint = "You cannot use an instruction mnemonic as a macro/label name."

        elif "template already defined" in low:
            hint = "Rename the second tplate, or remove the duplicate definition."

        elif "unknown template" in low or "unknown field name" in low:
            hint = ("Check the 'name.field' reference against the tplate "
                    "definitions earlier in the file.")

        elif "unassigned macro-variable" in low:
            hint = "A macro variable was used before being set inside the macro body."

        elif "too many macro expansions" in low:
            hint = "Likely infinite macro recursion (a macro calling itself)."

        elif "unrecognised architecture" in low:
            hint = "#$arch= must be 'hv' (Harvard) or 'vn' (Von Neumann)."

        # Generic fallback: show the correct syntax of the instruction
        if hint is None and opcode and opcode in cocas.iset:
            form = self._diagForm(opcode)
            if form:
                hint = ("Syntax of '%s':  %s %s" % (opcode, opcode, form))

        if hint and src.strip():
            hint += "\nYour line %s:  %s" % (errLineNo, src.strip())
        return hint
    #######  END enhanced diagnostics  #######

    #######  Autocompletion (VS Code / PyCharm style inline suggestions)  #######
    def _acBuildDict(self):
        """Collect every CDM8 word that can be completed:
        - hardware mnemonics & assembler directives (from cocas.iset)
        - macro-library names (standard.mlb, e.g. tst/clr/jmp/tplate...)
        - registers r0-r3/r0h-r1l, SP/PC, condition codes, page numbers p0-p7
        - syntax-highlighter vocabulary (cdm8_asm.highlights)
        Words are stored with their category for display in the popup."""
        words = {}
        # Instruction/directive categories from the assembler itself
        catnames = {0: "instruction", -1: "branch", -2: "stack op", -3: "osi call",
                    -4: "directive", -5: "macro", -6: "macro"}
        try:
            for w, (_, cat) in cocas.iset.items():
                words.setdefault(w.lower(), catnames.get(cat, "instruction"))
        except Exception:
            pass
        # Macro library (standard.mlb): lines like '*name/n'
        try:
            mlb = resPath("standard.mlb")
            if not os.path.exists(mlb):
                mlb = "standard.mlb"
            with open(mlb, "r") as f:
                for line in f:
                    line = line.rstrip()
                    if line.startswith("*"):
                        nm = line[1:].split("/")[0].strip()
                        if nm.isalnum() or "_" in nm:
                            words.setdefault(nm.lower(), "macro")
        except Exception:
            pass
        # Registers, condition codes, pages etc. from the highlight definitions
        try:
            for colour, lst in cf.highlights.items():
                for w in lst:
                    words.setdefault(w.lower(), "register" if w.startswith("r") and len(w) <= 4 else "keyword")
        except Exception:
            pass
        for i in range(4):
            words.setdefault("r%d" % i, "register")
            words.setdefault("r%dh" % i, "register")
            words.setdefault("r%dl" % i, "register")
        words.setdefault("sp", "register")
        words.setdefault("pc", "register")
        self.acDict = words

    def _acLineTokens(self):
        """Return (word_start_index, prefix) for the identifier under the cursor."""
        idx = self.asstxt.index(tk.INSERT)
        lineStart = "%s linestart" % idx
        before = self.asstxt.get(lineStart, idx)
        # don't complete inside comments
        cp = before.find(cf.commentprefix)
        if cp != -1:
            return None, ""
        k = len(before)
        while k > 0 and (before[k-1].isalnum() or before[k-1] == "_"):
            k -= 1
        prefix = before[k:]
        start = "%s.%d" % (idx.split(".")[0], k)
        return start, prefix

    def _acCandidates(self, prefix):
        """Ranked completion candidates for a given prefix."""
        if not prefix:
            return []
        p = prefix.lower()
        dictMatches = sorted([w for w in self.acDict if w.startswith(p)])
        # prefer shorter/common words first
        dictMatches.sort(key=lambda w: (len(w), w))
        # document words (labels/variables defined in this file) as backup matches
        docWords = set()
        text = self.asstxt.get("1.0", tk.END).lower()
        for m in __import__("re").finditer(r"\b[a-z_][a-z0-9_]*\b", text):
            w = m.group()
            if w.startswith(p) and w != p:
                docWords.add(w)
        extra = [w for w in sorted(docWords) if w not in dictMatches]
        result = dictMatches[:60] + extra[:20]
        return result

    def acSchedule(self, event=None):
        """Debounced KeyRelease handler: refresh the popup shortly after typing."""
        if getattr(self, "acIgnored", True):
            return
        if not getattr(self, "acEnabled", True):
            self.acHide()
            return
        if self.acAfterId:
            try:
                self.after_cancel(self.acAfterId)
            except Exception:
                pass
        self.acAfterId = self.after(120, self.acUpdate)

    def acUpdate(self):
        self.acAfterId = None
        if not getattr(self, "acEnabled", True):
            return
        start, prefix = self._acLineTokens()
        if start is None or len(prefix) < 1:
            self.acHide()
            return
        cands = self._acCandidates(prefix)
        # Hide if nothing to offer. A word that is EXACTLY typed (e.g. the
        # register "r0") still shows its longer variants (r0h, r0l) - VS Code
        # keeps suggesting refinements of a complete word too.
        if not cands:
            self.acHide()
            return
        # keep the popup open while the user arrows through it: don't steal
        # focus back to the text widget on every refresh (that retriggered
        # KeyRelease chains and made the whole app feel frozen/jumpy)
        hadFocus = self.asstxt.focus_get() is self.asstxt
        self.acWordStart = start
        self.acPrefix = prefix
        self.acWords = cands
        self._acShowPopup()
        if hadFocus:
            try:
                self.asstxt.focus_force()
            except Exception:
                pass

    def _acShowPopup(self):
        if self.acListbox is None:
            self.acListbox = tk.Listbox(self, height=8, activestyle="none",
                                        exportselection=False, relief=tk.RIDGE, bd=1,
                                        font=self.defaulttxtfont, selectbackground="#1a5fb4",
                                        selectforeground="white", highlightthickness=1)
            self.acListbox.bind("<ButtonRelease-1>", self.acSelectClick)
            self._bindMouseWheel(self.acListbox)
        lb = self.acListbox
        lb.delete(0, tk.END)
        shown = self.acWords[:8]
        for w in shown:
            cat = self.acDict.get(w, "")
            lb.insert(tk.END, "  %-14s %s" % (w, cat))
        lb.selection_clear(0, tk.END)
        lb.selection_set(0)
        lb.activate(0)
        # position just below the caret
        try:
            bbox = self.asstxt.bbox(tk.INSERT)
        except tk.TclError:
            bbox = None
        if bbox:
            x, y, h, wdt = bbox
            gx, gy = self.asstxt.winfo_rootx() + x, self.asstxt.winfo_rooty() + y + h
            lb.config(width=max(16, max(len(s) for s in shown) + 6))
            lb.place(x=self.winfo_pointerx() - self.winfo_rootx() if False else
                     gx - self.winfo_rootx(), y=gy - self.winfo_rooty())
            lb.tkraise()
            lb.update_idletasks()
            # flip above if it would run off the bottom of the screen
            if lb.winfo_rooty() + lb.winfo_height() > self.winfo_screenheight():
                lb.place(y=gy - self.winfo_rooty() - lb.winfo_height() - h)

    def acIsVisible(self):
        return self.acListbox is not None and self.acListbox.winfo_exists() \
               and self.acListbox.winfo_ismapped()

    def acHide(self):
        if self.acListbox is not None:
            try:
                self.acListbox.place_forget()
            except Exception:
                pass

    def acMoveSel(self, delta):
        if not self.acIsVisible():
            return "break"
        lb = self.acListbox
        sel = lb.curselection()
        cur = sel[0] if sel else 0
        n = lb.size() - 1
        cur = max(0, min(n, cur + delta))
        lb.selection_clear(0, tk.END)
        lb.selection_set(cur)
        lb.activate(cur)
        lb.see(cur)
        return "break"

    def _acRealEnd(self):
        """True caret position: <Key>/<KeyRelease> events fire *before* the
        widget applies the insertion, so 'insert' still points one char back."""
        idx = self.asstxt.index(tk.INSERT)
        try:
            nxt = "%s+1c" % idx
            if self.asstxt.compare(nxt, "<=", tk.END) \
               and self.asstxt.get(idx, nxt) == self._acLastChar:
                idx = nxt
        except Exception:
            pass
        return idx

    def _returnHandler(self, event=None):
        """<Return>: accept a completion candidate when the popup is open.
        Returns None otherwise so Tk's class binding inserts the newline."""
        if self.acIsVisible():
            return self.acAccept()
        return None

    def acAccept(self, event=None):
        """Insert the highlighted candidate (Tab / Enter)."""
        if not self.acIsVisible():
            return None  # let normal Tab/Return behaviour happen
        lb = self.acListbox
        sel = lb.curselection()
        if not sel:
            self.acHide()
            return "break"
        word = self.acWords[sel[0]]
        start = self.acWordStart
        end = self._acRealEnd()
        lineTxt = self.asstxt.get(start, "%s lineend" % end)
        tail = lineTxt[len(word):] if lineTxt.startswith(word) else ""
        # smart suffix: completing an instruction with no operands yet gets
        # ", " appended (VS Code style); never duplicates an existing comma
        suffix = ""
        if not tail.lstrip().startswith(",") \
           and self.acDict.get(word, "") in ("instruction", "directive"):
            suffix = ", "
        self.acIgnored = True
        try:
            self.asstxt.edit_separator()
            self.asstxt.delete(start, end)
            self.asstxt.insert(start, word + suffix)
            if suffix:
                self.asstxt.mark_set(tk.INSERT, start + "+%dc" % len(word))
        finally:
            self.acIgnored = False
        self.acHide()
        self.highlighter()
        return "break"

    def acSelectClick(self, event=None):
        lb = self.acListbox
        sel = lb.nearest(event.y)
        lb.selection_clear(0, tk.END)
        lb.selection_set(sel)
        self.asstxt.focus_set()
        self.acAccept()
        return "break"

    def acCancel(self, event=None):
        if self.acIsVisible():
            self.acHide()
            return "break"
        return None

    def acTrigger(self, event=None):
        """Force-open the completion list (Ctrl+Space / Cmd+Space)."""
        start, prefix = self._acLineTokens()
        if start is None:
            return "break"
        cands = self._acCandidates(prefix) if prefix else list(
            sorted(self.acDict.keys()))
        cands = [c for c in cands if c != prefix.lower()]
        if not cands:
            return "break"
        self.acWordStart = start
        self.acPrefix = prefix
        self.acWords = cands
        self._acShowPopup()
        return "break"

    def _acTabHandler(self, event=None):
        """<Tab> binding: accept a completion candidate when the popup is
        open; otherwise fall back to normal Tab behaviour (block indent)."""
        if self.acIsVisible():
            return self.acAccept()
        return self.tabBlock(shift=1)

    def toggleAutocomplete(self, event=None, refreshOnly=False):
        if not refreshOnly:
            self.acEnabled = not self.acEnabled
        if not self.acEnabled:
            self.acHide()
        try:
            self.menuEdit.entryconfig("Auto-completion",
                                      label=("Auto-completion   ✔" if self.acEnabled
                                             else "Auto-completion   "))
        except Exception:
            pass
        if not refreshOnly:
            self.saveConfig()

    def _acKeyFilter(self, event):
        """Bind on <Key>: intercept navigation/acceptance keys while popup shows."""
        # remember the just-typed char so acAccept can compute the true caret
        # position (<Key>/<KeyRelease> fire before the widget inserts it)
        try:
            self._acLastChar = event.char if (event.char and len(event.char) == 1) \
                               else ""
        except Exception:
            self._acLastChar = ""
        if not self.acIsVisible():
            return None
        ks = event.keysym
        if ks in ("Up", "Down"):
            return self.acMoveSel(1 if ks == "Down" else -1)
        if ks in ("Tab", "ISO_Left_Tab", "Return"):
            return self.acAccept()
        if ks == "Escape":
            return self.acCancel()
        return None  # typing continues normally; popup updates via KeyRelease

    def _updateStatusCursor(self, event=None):
        try:
            idx = self.asstxt.index(tk.INSERT)
            ln, col = idx.split(".")
            sel = ""
            try:
                nchars = len(self.asstxt.get("sel.first", "sel.last"))
                if nchars:
                    sel = " (%d selected)" % nchars
            except tk.TclError:
                pass
            self.cursorLabel.config(text="Ln %s, Col %d%s" % (ln, int(col)+1, sel))
            if self.projectPath:
                self.projStatusLabel.config(text="Folder: " + self.projectPath)
            else:
                self.projStatusLabel.config(text="No folder open \u2014 use Project > Open Folder\u2026")
        except Exception:
            pass

    def _markCurrentLine(self, event=None):
        try:
            self.asstxt.tag_remove("currentline", "1.0", tk.END)
            ln = self.asstxt.index("insert").split(".")[0]
            self.asstxt.tag_add("currentline", ln + ".0", "%s lineend+1c" % ln)
        except Exception:
            pass

    def macBackspace(self, event=None):
        """On classic Mac keyboards Fn+Delete sends BackSpace - honour word delete w/ Option."""
        if platform == "darwin" and (event.state & 0x080000):  # Option held
            return self.deletePrevWord(event)
        return None  # default Tk behaviour

    def deletePrevWord(self, event=None):
        try:
            start = self.asstxt.search(r"(\S+\s*)?\S*$", "insert linestart", "insert",
                                       index="backwards", regexp=True, stopindex="1.0")
            if start and start != "insert":
                self.asstxt.delete(start, "insert")
        except Exception:
            pass
        return "break"

    def copyLineDown(self, event=None):
        """Duplicate current line below (Cmd+D, like VS Code Shift+Alt+Down)."""
        ln = int(float(self.asstxt.index("insert linestart")))
        lineTxt = self.asstxt.get("%d.0" % ln, "%d.0 lineend" % ln)
        self.asstxt.insert("%d.0 lineend+1c" % ln, "\n" + lineTxt)
        self.asstxt.mark_set(tk.INSERT, "%d.0" % (ln+1))
        self.asstxt.see(tk.INSERT)
        return "break"

    def deleteLine(self, event=None):
        """Cmd+BackSpace deletes the whole current line."""
        ln = int(float(self.asstxt.index("insert linestart")))
        self.asstxt.delete("%d.0" % ln, "%d.0 lineend+1c" % ln)
        return "break"

    def lineEnd(self, event=None):
        self.asstxt.mark_set(tk.INSERT, "insert lineend")
        self.asstxt.see(tk.INSERT)
        return "break"

    def lineStart(self, event=None):
        self.asstxt.mark_set(tk.INSERT, "insert linestart")
        self.asstxt.see(tk.INSERT)
        return "break"

    def selectall(self, event=None):
        self.asstxt.tag_add(tk.SEL, "1.0", tk.END)
        self.asstxt.mark_set(tk.INSERT, "1.0")
        self.asstxt.see(tk.INSERT)
        return "break"

    def focusSearchBox(self, event=None):
        """Cmd+F focuses the toolbar find box and pre-selects its content."""
        self.searchBox.focus_set()
        self.searchBox.select_range(0, tk.END)
        return "break"

    def gotoLineDialog(self, event=None):
        """Cmd+G: jump-to-line dialog, like modern IDEs."""
        maxLine = int(float(self.asstxt.index("end-1c")))
        try:
            from tkinter import simpledialog
        except ImportError:
            simpledialog = None
        if simpledialog is None:
            return "break"
        dlg = simpledialog.askstring("Go to Line", "Line number (1 - %d):" % maxLine,
                                     parent=self.master)
        if dlg:
            try:
                n = int(dlg)
                if 1 <= n <= maxLine:
                    self.asstxt.mark_set(tk.INSERT, "%d.0" % n)
                    self.asstxt.see("%d.0" % n)
                    self.highlightLine("%d.0" % n)
            except ValueError:
                pass
        return "break"

    def clearEditorHighlights(self, event=None):
        self.highlightLine(None)
        return "break"

    def stepOnce(self):
        """Single instruction step (CDM8 > Step menu / speed slider)."""
        if self.running:
            self.running = False
            self.Emu.HALT = True
        self.Emu.step(cdm8_io.interrupt, cdm8_io.interruptVector)
        self.updateOPs()
        self.updateDisp()
        self.runStopButton.config(text="Run ", fg="black", activeforeground="black")
        return "break"

    def compileRun(self, event=None):
        """F5: compile then run, like pressing both buttons."""
        self.compileText()
        if not self.running:
            self.runProg()
        return "break"

    def aboutDialog(self, event=None):
        messagebox.showinfo("About CocoIDE",
            self.TITLE + "\n"
            "CDM8 assembler/IDE/emulator for teaching\n"
            "Extended fork: project folders, file browser, recent files,\n"
            "macOS-friendly shortcuts (Cmd+S/O/N/B/R/F/G/D).\n"
            "Original: (c) M L Walters, Prof A Shafarenko 2016-2018")
        return "break"

    # Editor Popup menu for asstxt widget
    def popmenu(self, event=None):
        menu = tk.Menu(self.master,tearoff=0)
        menu.add_command(label="Cut",command=self.cut)
        menu.add_command(label="Copy",command=self.copy)
        menu.add_command(label="Paste",command=self.paste)
        menu.add_separator()
        menu.add_command(label="Select All", command=self.selectall)
        menu.add_command(label="Duplicate Line", command=self.copyLineDown)
        menu.add_command(label="Delete Line", command=self.deleteLine)
        menu.add_separator()
        menu.add_command(label="Toggle Breakpoint", command=self.toggleBPAtCursor)
        menu.post(event.x_root,event.y_root)
        return

    def toggleBPAtCursor(self, event=None):
        """Toggle a breakpoint on the editor line under the cursor."""
        try:
            ln = int(float(self.asstxt.index("insert linestart")))
            pos = self.mcode_list.search(":", "%d.0" % ln, "%d.0 lineend+1c" % ln)
            if pos:
                # emulate clicking that mcode line
                self.mcode_list.mark_set(tk.INSERT, "%s linestart" % pos)
                self.toggleBP()
            else:
                messagebox.showinfo("Breakpoint", "No compiled code on this line.\n"
                                    "Use CDM8 > Compile/Reset first.")
        except Exception:
            pass
        return "break"

    # Mcode listing Popup menu for mcode_list widget
    def popmenuBrk(self, event=None):
        menu = tk.Menu(self.master,tearoff=0)
        menu.add_command(label="Toggle Break",command=self.toggleBP())
        menu.add_command(label="Cancel")
        menu.post(event.x_root,event.y_root)
        return

    def close_window(self):
        if self.running: # Stop Emulator
            self.running = False
            self.Emu.HALT=True
        try:
            if getattr(self, "_runId", None):
                self.after_cancel(self._runId)
        except Exception:
            pass
            
        if self.amesRunning:
            self.amesSubmit()
            self.changed=False
            #print(self.timeleft)#debug
            if self.timeleft and self.timeleft>0:
                if not messagebox.askyesno("Are you sure?","Exit Test?"):
                    return
        else:
            if self.asstxt.edit_modified():
                if messagebox.askyesno("Quit","Do you want to save the file..."):
                        self.file_save()
        self.saveConfig()
        self.after(100, self.master.destroy)
        return

    ### Editor functions
    def save_if_modified(self, event=None):
        if self.asstxt.edit_modified(): #modified
            response = messagebox.askyesnocancel("Save?", "This document has been modified. Do you want to save changes?") #yes = True, no = False, cancel = None
            if response: #yes/save
                result = self.file_save()
                if result == "saved": #saved
                    return True
                else: #save cancelled
                    return None
            else:
                return response #None = cancel/abort, False = no/discard
        else: #not modified
            return True

    def file_new(self, event=None):
        # VS Code style: New File opens a fresh Untitled TAB; the current
        # buffer is kept (not destroyed) as another tab.
        if getattr(self, "editorTabs", None):
            self._storeActiveBuffer()
            blank = {"path": None, "name": "Untitled", "dirty": False,
                     "content": "", "insert": "1.0"}
            self.editorTabs.append(blank)
            self.activeTab = len(self.editorTabs) - 1
            self.file_path = None
            self._tabSwapGuard = True
            try:
                self.asstxt.delete(1.0, tk.END)
                self.asstxt.edit_modified(False)
                self.asstxt.edit_reset()
                self.asstxt.edit_separator()
                self.mcode_list.delete(1.0, tk.END)
                self.highlighter()
                self.set_title()
            finally:
                self._tabSwapGuard = False
            self._rebuildEditorTabBar()
            return "break"
        result = self.save_if_modified()
        if result != None: #None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            self.asstxt.delete(1.0, "end")
            self.mcode_list.delete(1.0, tk.END)
            self.asstxt.edit_modified(False)
            self.labelList = []
            self.changed=True
            self.asstxt.edit_reset()
            self.file_path = None
            self.set_title()
            for n in range(len(self.Emu.memory)):# Clear code memory
                self.Emu.memory[n] = [[0]*256, [0]*256]
                
            self.watches=[]
            self.resetEmu()
        return "break"

    def file_open(self, event=None, filepath=None):
        result = self.save_if_modified()
        if result != None: #None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            if filepath == None:
                filepath = filedialog.askopenfilename(
                    initialdir=self.projectPath or self.startupFolder or self.homeDir,
                    filetypes=(('CDM8 Assembly', '*.asm'), ('All files', '*.*')))
            if filepath:
                filepath = os.path.abspath(filepath)
                ext = os.path.splitext(filepath)[1].lower()
                if ext not in ("", ".asm", ".obj", ".txt", ".s"):
                    # e.g. task brief PDF/doc - open with system viewer instead
                    self.openExternalFile(filepath)
                    return "break"
            fileContents=""
            if filepath != None  and filepath != '':
                try:
                    #Python 3
                    with open(filepath, encoding="utf-8") as f:
                        fileContents = f.read()# Get all the text from file.
                except:
                    try:
                        # Python 2
                        with open(filepath) as f:#, encoding="utf-8") as f:
                            fileContents = f.read()# Get all the text from file.
                    except:
                        pass
                # Set current text to file contents (in an editor tab)
                if fileContents != "" or os.path.isfile(filepath):
                    self.openInNewTab(filepath, contents=fileContents)
                    self.changed=True
                    # Track recents. Opening a file NEVER replaces the project
                    # root (VS Code behaviour): we only expand the tree so the
                    # opened file's folder is visible and the file is marked.
                    if filepath not in self.openedFiles:
                        self.openedFiles.insert(0, filepath)
                    self.openedFiles = self.openedFiles[:15]
                    folder = os.path.dirname(filepath)
                    root = self.rootProjectPath or self.projectPath
                    if root and folder.startswith(root + os.sep):
                        # inside the current project - just reveal it in place
                        self.revealInTree(filepath)
                    elif not root:
                        # no project open yet: adopt the file's folder as root
                        self.set_project(folder)
                        self.revealInTree(filepath)
                    else:
                        # file lives outside the project: keep the project as is,
                        # just refresh the recent-files menu
                        self._rebuildRecentMenu()
                        self._populateProjectTree()
                    self.saveConfig()
        return "break"

    def file_close(self, event=None):
        """Close current file (editor becomes an empty Untitled buffer)."""
        if self.asstxt.edit_modified():
            if messagebox.askyesno("Close File", "Save changes before closing?"):
                self.file_save()
        self.file_new()
        return "break"

    def file_save(self, event=None):
        #if platform != "darwin":#Fix for Mac Save problem??
        self.master.config(cursor="watch")
        self.asstxt.config(cursor="watch")

        if self.file_path == None:
            result = self.file_save_as()
        else:
            result = self.file_save_as(filepath=self.file_path)

        self.update()
        time.sleep(0.5)
        #if platform != "darwin":
        self.master.config(cursor="")
        self.asstxt.config(cursor="")
        return "break"

    def file_save_as(self, event=None, filepath=None, ext=".asm", text=None):
        if ext == ".asm": filetype="CDM8 Assembly"
        if ext == ".obj": filetype = "CDM8 Object File"
        if filepath == None:
            initdir = self.projectPath or self.startupFolder or self.homeDir
            if self.file_path:
                self.file_path = str(self.file_path)[:-4]+ext
                filepath = filedialog.asksaveasfilename(initialdir=initdir,
                        filetypes=((filetype, '*'+ext), ('All files', '*.*')),
                        defaultextension=ext, initialfile=os.path.basename(self.file_path))
            else:
                filepath = filedialog.asksaveasfilename(initialdir=initdir,
                    filetypes=((filetype, '*'+ext), ('All files', '*.*')),
                    defaultextension=ext) #defaultextension='.asm'
        try:
            with open(filepath, 'wb') as f:
                if text == None:
                    text = self.asstxt.get(1.0, "end-1c")
                try: # Python3
                    # python 3
                    f.write(bytes(text, 'UTF-8'))
                except: # Python2
                    # python 2
                    f.write(bytes(text))#, 'UTF-8'))
                self.asstxt.edit_modified(False)
                self.file_path = os.path.abspath(filepath)
                self.startupFolder = os.path.dirname(self.file_path)
                # keep the editor-tab strip in sync with the saved file
                if getattr(self, "editorTabs", None):
                    t = self.editorTabs[self.activeTab]
                    if t["path"] is None:
                        t["name"] = os.path.basename(self.file_path)
                    t["path"] = self.file_path
                    t["dirty"] = False
                    try:
                        t["content"] = self.asstxt.get("1.0", tk.END)
                    except Exception:
                        pass
                    self._rebuildEditorTabBar()
                if self.file_path not in self.openedFiles:
                    self.openedFiles.insert(0, self.file_path)
                self.openedFiles = self.openedFiles[:15]
                self._rebuildRecentMenu()
                self._populateProjectTree()
                self.set_title()
                return "Saved"
        except TypeError:
            return "break"
        except:
            #('FileNotFoundError')
            return "break"

        return "break"

    def file_quit(self, event=None):
        result = self.save_if_modified()
        if result != None: #None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            self.root.destroy() #sys.exit(0)

    def set_title(self, event=None, titletxt=None):
        if titletxt != None:
            title=titletxt
        elif self.file_path != None:
            title = os.path.basename(self.file_path)
            try:
                if self.asstxt.edit_modified():
                    title = "\u25cf " + title   # VS Code style unsaved marker
            except Exception:
                pass
        else:
            title = "Untitled"
        proj = ""
        if self.projectPath:
            proj = " \u2014 " + os.path.basename(self.projectPath)
        self.master.title(title + proj + " - " + self.TITLE)
        return

    def undo(self, event=None):
        try:
            self.asstxt.edit_undo()
        except:
            pass
        return "break"

    def redo(self, event=None):
        try:
            self.asstxt.edit_redo()
        except:
            pass
        return "break"

    def cut(self, event=None):
        try:
            self.copy() # selected text in self.cliptext
            if self.amesRunning and ("#!" in self.cliptext): # DO not delete #! lines
                self.cliptext = ""
            elif not(self.amesRunning and self.asstxt.search("#!", "insert linestart", "insert lineend")):
                self.asstxt.delete("sel.first","sel.last")
                self.changed = True
                self.highlighter()
        except tk.TclError:
            pass
        return "break"

    def copy(self, event=None):
        try:
            self.asstxt.clipboard_clear()
            self.cliptext = self.asstxt.get("sel.first","sel.last")
            if self.amesRunning: #Do not use system clipboard
                if ("#!" in self.cliptext): # DO not copy whole #! lines
                    self.cliptext = ""
            else:
                self.asstxt.clipboard_append(self.cliptext)
                #self.cliptext=""
        except tk.TclError:
            pass
        return "break"

    def paste(self, event=None):
        try:
            if self.amesRunning: #Do not use system clipboard
                if ("#!" in self.cliptext): # DO not paste  #! into lines ##
                    self.cliptext = ""
                if self.asstxt.search("#!", "insert linestart", "insert lineend"):
                    # or paste into #! lines
                    self.cliptext = ""
                if self.asstxt.search("#", "insert-1c", "insert") and self.cliptext=="!":
                    self.cliptext=""
                if self.asstxt.search("!", "insert", "insert+1c") and self.cliptext=="#":
                    self.cliptext=""
            else:
                self.cliptext = self.asstxt.selection_get(selection="CLIPBOARD")

            try:
                self.asstxt.delete("sel.first","sel.last")
            except tk.TclError:
                pass #nothing selected
            #print("*", self.cliptext, "*")# debug
            self.asstxt.insert(tk.INSERT,self.cliptext)
            self.changed = True
            self.highlighter()
        except tk.TclError:
            #print("paste error")#debug
            #raise#debug
            pass
        return "break"

    def _searchFocusIn(self, event=None):
        if self.searchBox.get() == getattr(self, "searchPlaceholder", ""):
            self.searchBox.delete(0, tk.END)
            self.searchBox.config(fg="black")

    def _searchFocusOut(self, event=None):
        if not self.searchBox.get():
            self.searchBox.config(fg="grey")
            self.searchBox.insert(0, getattr(self, "searchPlaceholder", ""))

    def gotoLine(self, event=None):
        #print(type(self.lineBox.get()))# debug
        try:
            linno = self.lineBox.get()
            #print(linno)
            if linno:
                linno = self.lntext.search(linno, "1.0")
                self.highlightLine(linno)
                self.asstxt.see(linno)
            else: 
                self.highlightLine()
        except:
            pass
        return "break"

    def searchText(self, event=None):
        try:
            searchStr = self.searchBox.get()
            if searchStr == getattr(self, "searchPlaceholder", ""):
                return "break"
            if searchStr:
                if self.prevStr != searchStr:
                    self.startIndex = "1.0"
                self.prevStr = searchStr
                try:
                    self.startIndex = self.asstxt.search(searchStr, self.startIndex, tk.END)
                except tk.TclError:
                    # wrapped past the end - restart from top
                    self.startIndex = "1.0"
                    self.startIndex = self.asstxt.search(searchStr, self.startIndex, tk.END)
                endIndex = self.asstxt.index('%s+%dc' % (self.startIndex, (len(searchStr)))) # find end of word
                #print(self.startIndex)
                self.highlightLine(self.startIndex, endIndex)
                self.asstxt.see(self.startIndex)
                self.startIndex = endIndex
            else:
                self.highlightLine()
        except:
            self.startIndex = "1.0"
        return "break"

    def tabBlock(self, event=None, shift=0):
        #if event:
        #    print("*", event.keysym)
        #print(shift)#event.keysym)
        if self.asstxt.tag_ranges("sel"): 
            selecttext = self.asstxt.get("sel.first linestart","sel.last")
            #print("*", selecttext, "*")
            startline = int(self.asstxt.index("sel.first linestart").split('.')[0])
            endline = int(self.asstxt.index("sel.last linestart").split('.')[0])
            if shift == 1: 
                #print(shift)
                # Add a tab char to each line
                for line in range(startline, endline+1):
                    self.asstxt.insert(str(line)+".00", "\t")
                return "break"
            elif shift == -1: #remove tab from all lines of selected text
                #print(shift)
                # check all lines have a tab in forst position
                tabfirst = True 
                for line in range(startline, endline+1):
                    if self.asstxt.get(str(line)+".00", str(line)+".01") != "\t":
                        tabfirst = False
                if tabfirst:
                    for line in range(startline, endline+1):
                        self.asstxt.delete(str(line)+".00", str(line)+".01")                    
            return "break"
        return

        

    #### CDM8 Functions
    def toggleMemPageDisp(self, event=None):
        if self.pageDisp:
            self.memPageFrame.grid_remove()
            self.pageDisp = False
            self._setMenuLabel(self.emumenu, "Paged Memory", "Paged Memory   ")
        else:
            self.memPageFrame.grid()
            self.pageDisp = True
            self._setMenuLabel(self.emumenu, "Paged Memory", "Paged Memory  ✔")
    
    
    def toggleArch(self, event=None):
        if self.arch[self.memPageVar.get()]=="vn":
            self.setArch(arch="hv", page=self.memPageVar.get())
        else:
            self.setArch(arch="vn", page=self.memPageVar.get())
            
    def setShadowSP(self, event=None):
        if self.Emu.shadowSP == False:
            # Toggle off shadow SPs
            self._setMenuLabel(self.emumenu, "Shadow SPs", "Shadow SPs      ✔")
            self.Emu.shadowSP = True
        else:
            self._setMenuLabel(self.emumenu, "Shadow SPs", "Shadow SPs       ")
            self.Emu.shadowSP = False
        
    def setArch(self, arch="vn", page=0, event=None):
   
        if self.Emu.setArch(arch, page=page)!="Unrecognised Architecture":
            self.arch[page]=arch
        else:
            return "Unrecognised Architecture"
        
        #print(self.memChanged)
        ## Whole Memory display with tooltips to see content!
        self.initMemDisplay(page=page)
        #print("$",self.Emu.memory[page])
        self.updateDisp()
        self.highlighter()
    
    def saveImage(self, event=None, filepath=None):
        #print("save Image")#debug
        self.compileText()
        if filepath == None:
            filepath = filedialog.asksaveasfilename(
                initialdir=self.projectPath or self.startupFolder or self.homeDir,
                filetypes=(('Logisim Memory Image', '*.img'), ('All files', '*.*')),
                defaultextension =".img") #defaultextension='.txt'
        
        try:
            with open(filepath, 'wb') as f:
                try: # Python3
                        f.write(bytes("v2.0 raw\n", 'UTF-8'))
                except: # Python2
                        # python 2
                        f.write(bytes("v2.0 raw\n"))#, 'UTF-8'))
                for memVal in self.Emu.memory[0][0]:
                    try: # Python3
                        f.write(bytes(self.Emu.convert(0, memVal)+"\n", 'UTF-8'))
                    except: # Python2
                        f.write(bytes(self.Emu.convert(0, memVal)+"\n"))#, 'UTF-8'))
                return "saved"
        #except IOError:
        #    return "Cancelled"
        except:
            #raise
            #('FileNotFoundError')
            return "Cancelled"
        
            
    def saveObjFile(self, event=None):
        objText = self.compileText()
        self.file_save_as(ext=".obj", text=objText)

    #def linkObjFiles(self, event=None):
    #    print("Linker")
    #    import cocol
    #    cocol.CocoLink(master=self.master, sym=True)

    def compileText(self, event=None):
        #print("Compiling")
        self.changed=False
        # bring the listing (Machine Code tab) to front if a file tab is shown
        try:
            if getattr(self, "viewTabs", None) \
                    and self.activeViewTab != "__mcode__":
                self.selectViewTab("__mcode__")
        except Exception:
            pass
        if self.running:
            self.running = False
            self.Emu.HALT = True
            self._runStopped()
        self.Emu.curPage = 0
        textList=[]
        errorMsg=None
        cocas.errLine=None
        overlapStart = None
        page = 0
        
        self.statusMsg.config(text="")
         # Clear errLine tag from asstxt window
        self.asstxt.tag_delete("err")
        # error strip: forget marks from the previous compile run
        try:
            self._errMarkLines = []
            self._refreshErrMarks()
        except Exception:
            pass
        self.mcode_list.delete(1.0, tk.END)
        self.mcode_list.config(wrap=tk.NONE)
        # Clear memory
        #print("£",self.Emu.memory[0])# debug
        for n in range(len(self.Emu.memory)):# Clear code(/data) memory
            self.Emu.memory[n]= [[0]*256, [0]*256] 
        #self.dispAllMemory()
        
        
        ## Compile the program!
        text = self.asstxt.get("1.0", tk.END)
        
        
        
        # IDE directives (prefixed by #$<keyw>=<option>
        # Set architecture. # Harvard $arch=hv, Von Neuman #$arch=vn 
        archpos = self.asstxt.search('#$arch=', "1.0", tk.END)
        if archpos:
            self.arch[0] = self.asstxt.get(archpos+"+7c", archpos+"+9c")
            if self.setArch(self.arch[0], page=0) == "Unrecognised Architecture":
                cocas.errLine = int(float(archpos))
                errorMsg="Line "+str(cocas.errLine)+": Unrecognised Architecture, expected 'hv' or 'vn'"
        
        # Include IO 
        
        
        # Call the Compiler (cocas.py)
        codetext=None
        obj_code=None
        if errorMsg==None:
            filebuff = io.StringIO(text) # cocas likes to use a file type object!
            try:
                obj_code, codetext, errorMsg = cocas.compile_asm(filebuff, self.cdm8ver)
            except Exception as e:
                errorMsg = e

        #print("33", errorMsg)#debug
        
        # If no errors, load CocoEmu, and Update the GUI display
        if codetext != None or obj_code != None and errorMsg==None:
            strippedCode = ""
            for line in codetext.splitlines():#("\n"):
                textList += line
                if line[18:20] == "  " and line[2] == ":":# line is fragmented
                    strippedCode += line[3:15].rstrip(" ")
                else:
                    strippedCode += '\n'+line[:15].rstrip(" ")
            strippedCode = strippedCode[1:]
            #print(strippedCode)# debug
            # Insert in Mcode list window
            index = 0
            for line in strippedCode.splitlines():
                line=line.upper()
                self.mcode_list.insert("end",line+'\n')
                self.mcode_list.tag_add("hexNo", "end -1 lines", tk.END) # add tag to k
                self.asstxt.tag_config("hexNo", font=self.boldfont)

                # Uddate the watch window
                for watch in self.watches:
                    #print(index, watch[0])#debug
                    if index == watch[0]: # Is a watch line
                        #print(line)
                        if ":" in line:
                            watchLine = line.split(":")
                            #print(index, watch[0],"watchLine", watchLine)#debug
                            watch[2] = watchLine[0] # Memory address as str
                            watchLine[1] = watchLine[1].split(" ")
                            #print(watchLine)#debug
                            if type(watchLine[1])==list:
                                watch[4] = len(watchLine[1])-1 # split(" ") inserts an empty item in list???
                            else:
                                watch[4]=1 # Probably not needed?
                            linno = str(index+1)+".0"

                            if not watch[3]:
                                if self.asstxt.search('"', linno, "%s lineend" % linno): watch[3]="str"
                                elif self.asstxt.search('0b', linno, "%s lineend" % linno): watch[3]="bin"
                                elif self.asstxt.search('0x', linno, "%s lineend" % linno): watch[3]="hex"
                                else: watch[3] = "dec"
                index += 1
            #print("**",self.watches)#debug

            # Put memory values in list and load to emulator
            memChunks=obj_code.splitlines()
            lineNum = 1
            for line in memChunks:
                #print("*"+line)#[:4])#debug
                if "ABS" in line:
                    mem = [line.lstrip("ABS").split(":")]
                    for item in mem:
                        memadr = int("0x"+item[0].lstrip(" "), 16)
                        memlist = item[1].lstrip(" ").split(" ")
                        for val in memlist: # Check here for overlapping sects
                            if memadr > 255:
                                errorMsg = "Memory Overflow - program too large"
                                break
                            elif self.Emu.memory[0][0][memadr] > 0 : # Already occupied by code?
                                #print(memadr, lineNum, line)
                                #Find line where asect overlaps?? Problem here??
                                overlapStart=None
                                overlapStart = self.mcode_list.search('%02x:' % memadr, "1.0", stopindex="end" )
                                #print("**",overlapStart, " memadr ", memadr)#debug
                                overlapStart = self.mcode_list.search('%02x:' % memadr, overlapStart, stopindex="end" )
                                #overlapStart = self.asstxt.search('assect %02x:' % memadr, "1.0", stopindex="end" )
                                
                                if overlapStart:
                                    #adr = self.mcode_list.search('%02X:' % memadr, overlapStart+"+1l", stopindex="end" )
                                    #print("*", adr)
                                    #if adr:
                                    cocas.errLine = int(float(overlapStart))
                                    errorMsg = "On line "+str(cocas.errLine)+" ERROR: Overlapping asect! Code from this line onward, will overwrite previously compiled code"
                                    
                                    break
                            else:
                                self.Emu.memory[0][0][memadr]=int("0x"+val, 16)
                                memadr += 1
                        if errorMsg: break
            #print("%",self.Emu.memory[0][1])# debug Memory array image
            if not errorMsg:
                self.resetEmu()
                # Clear errLine tag from asstxt window
                self.asstxt.tag_delete("err")
                self.update()

        # Show error/warning in mcode window
        if errorMsg:
            #print("*"+errorMsg)#DEBUG
            # ---- Enhanced diagnostics (CDM8) ------------------------------
            # Turn terse assembler messages into concrete, actionable ones
            # and show the offending source line with a caret marker.
            try:
                errorMsg = str(errorMsg)
            except Exception:
                pass
            errLineNo = None
            try:
                if "On line" in errorMsg:
                    errLineNo = int(errorMsg[8:errorMsg.find(" ", 8)])
                elif errorMsg.startswith("Line"):
                    errLineNo = int(errorMsg.split(":")[0][4:].strip())
                elif cocas.errLine:
                    errLineNo = int(cocas.errLine)
            except Exception:
                errLineNo = None
            helpTxt = self.diagnoseError(errorMsg, errLineNo)
            if helpTxt:
                errorMsg = errorMsg + "\n\n" + helpTxt
            # ---- end enhanced diagnostics --------------------------------
            errorMsg = errorMsg.split(" ")
            #print(retError)
            self.mcode_list.delete(1.0, tk.END)
            self.mcode_list.config(wrap=tk.WORD)
            #self.mcode_list.insert(tk.END, errorMsg)#[0]+":\n")
            if len(errorMsg)>6:
                errorMsg.insert(4, "\n")
            if len(errorMsg)>10:
                errorMsg.insert(10, "\n")
            msg = ""
            for word in errorMsg:
                msg += (word + " ")
            errorMsg = msg 
            self.statusMsg.config(text=errorMsg)

            # ---- error strip: collect every diagnostic line number -------
            # The listing pane is filled by cocas with one message per
            # problem; scan it so the scrollbar shows a tick per error even
            # when only the first one is highlighted in the editor.
            try:
                self._errMarkLines = self.collectErrorLines()
                if errLineNo and errLineNo not in self._errMarkLines:
                    self._errMarkLines.append(errLineNo)
                    self._errMarkLines.sort()
                self._refreshErrMarks()
            except Exception:
                pass
            
            # Then highlight line in text editor where error occurs
            if "On line" in errorMsg:
                #print("error line =", int(errorMsg[0][8:11]))
                # cocas.errline picks up some error line numbers, but not all!
                # So more reliable to check the error message directly
                if not cocas.errLine:
                    cocas.errLine = int(errorMsg[8:errorMsg.find(" ", 8)])
                #cocas.errline = int(errorMsg[0][8:11])
                #print(cocas.errLine)# debug
            if cocas.errLine: # Highlights error line
                self.highlightLine(str(cocas.errLine)+".0")
                #self.asstxt.tag_delete("err")
                #self.asstxt.tag_add("err", "%s linestart" % (str(cocas.errLine)+".0"), "%s lineend+1c" % (str(cocas.errLine)+".0")) # add tag to k
                #self.asstxt.tag_config("err", background=cf.errColour)
                #self.updateLineNos()
                #self.update()
                #self.asstxt.see("%s" % str(cocas.errLine)+".0")# scroll to see error line

            for n in range(self.Emu.datamem[self.Emu.curPage],len(self.Emu.memory[self.Emu.curPage])):# Clear data memory
                 self.Emu.memory[n]= [[0]*256]#??
            return None
        else:
            self.resetEmu()
            #print(self.Emu.memory[0][1]) # debug data mem for hv arch
            self.updateDisp()
            #self.dispAllMemory()
        return obj_code # For when cocas called from CLI.
    
    def highlightLine(self, lintxt=None, linend=None):
        if linend ==None:
            linend = "%s lineend+1c" % (lintxt)
        self.asstxt.tag_delete("err")
        # VS Code style error strip: repaint the red marks along the
        # scrollbar gutter for every error/warning line found in the
        # Machine-Code listing.
        try:
            self._refreshErrMarks()
        except Exception:
            pass
        if lintxt:
            self.asstxt.tag_add("err", lintxt, linend)#"%s linestart" % (lintxt), "%s lineend+1c" % (lintxt)) # add tag to k
            self.asstxt.tag_config("err", background=cf.errColour)
            self.update()
            self.asstxt.see(lintxt)# scroll to see error line

    #### Error strip (VS Code "problem decorations" on the scrollbar) #####
    # Small red ticks painted on a thin canvas glued to the right edge of
    # the editor: one tick per line that the assembler complained about.
    # Clicking a tick jumps the caret to that line - handy in long listings
    # where several errors are far apart and only one is visible at a time.

    def _makeErrStrip(self):
        """Create the strip canvas; call once after asstxt/scrollbar exist."""
        self.errStrip = tk.Canvas(None, width=10, background="#2b2b2b",
                                  highlightthickness=0, borderwidth=0)
        self.errStrip.place(in_=self.asstxt, relx=1.0, x=-13, rely=0.0,
                            relheight=1.0)
        self.errStrip.bind("<Button-1>", self._errStripClick)
        self.errStrip.bind("<Configure>",
                           lambda e: self._refreshErrMarks())
        self._errMarkLines = []      # sorted list of problem line numbers
        self._errTickPos = []         # (ytop, ybot, lineno) for click mapping

    def collectErrorLines(self):
        """Scan the Machine Code output pane for 'On line N' diagnostics
        and return the sorted set of reported line numbers."""
        lines = set()
        try:
            txt = self.mcode_list.get("1.0", tk.END)
        except Exception:
            return []
        import re as _re2
        for m in _re2.finditer(r"[Ll]ine[^\d]{0,4}(\d+)", txt):
            n = int(m.group(1))
            if 0 < n <= 100000:
                lines.add(n)
        return sorted(lines)

    def _refreshErrMarks(self):
        if not getattr(self, "errStrip", None):
            return
        c = self.errStrip
        c.delete("all")
        self._errTickPos = []
        try:
            total = int(float(self.asstxt.index("end-1c").split(".")[0]))
        except Exception:
            return
        h = c.winfo_height()
        if h < 5 or total < 1:
            return
        pxPerLine = h / float(total)
        pad = 1 if pxPerLine > 3 else 0
        for n in self._errMarkLines:
            y1 = (n - 1) * pxPerLine + pad
            y2 = y1 + max(2.0, min(pxPerLine - 2 * pad, 6.0))
            c.create_rectangle(1, y1, 9, y2, fill="#e05555", outline="")
            self._errTickPos.append((y1, y2, n))

    def _errStripClick(self, event):
        """Jump to the error whose tick was clicked (nearest wins)."""
        best = None
        bestd = 1e9
        for (y1, y2, n) in self._errTickPos:
            d = 0 if y1 <= event.y <= y2 else min(abs(event.y - y1),
                                                  abs(event.y - y2))
            if d < bestd:
                bestd, best = d, n
        if best is not None:
            self.asstxt.mark_set(tk.INSERT, "%d.0" % best)
            self.asstxt.see("%d.0" % best)
            self.asstxt.focus_set()
        return "break"

    def cocolnk(self, event=None):
        try:
            import cocol
        except ImportError:
            print("Cocol Linker not found")
        cocol.CocoLink(self.master)


    def resetEmu(self, event=None):
        self.initPC()
        self.Emu.SP = [0] * 8
        self.Emu.curPage = 0
        if self.changed:
            self.clearBPs()
            #print("BPs cleared")#debug
        else:
            #otherwise replace breakpoints
            #print(self.Emu.BP)
            #print("*",self.mcode_list.tag_names())
            for tagname in self.bpTagNames:
                #print(tagname)#debug
                tagpos = self.mcode_list.search(tagname+":", "1.0", tk.END)
                #print(tagpos)#debug
                self.mcode_list.tag_add(tagname, tagpos, "%s lineend+1c" % tagpos)
                self.mcode_list.tag_configure(tagname, background=cf.bpColour)
                self.asstxt.tag_add(tagname, tagpos, "%s lineend+1c" % tagpos)
                self.asstxt.tag_configure(tagname, background=cf.bpColour)
        self.initPC()
        self.Emu.regs = [0]*4
        self.Emu.CVZN = 0
        # need to clear all memory changed pages
        for n in range(len(self.Emu.memChanged)):
            self.Emu.memChanged[n]=[]
        #self.highlighter()
        # Reset IO ports
        for port in self.IOPorts:
            port.resetPort()
        self.updateDisp()
        self.updateRunSelect()

    def updateRunSelect(self):
        self.runDict=colls.OrderedDict()
        self.runDict["00:"] = 0x00
        for label in self.labelList:
            if cf.entrySpec in label[0]:
                # Add to runDict
                labline=self.asstxt.search("\n"+label, "1.0", tk.END)
                #print(labline, "*"+label+"*")#debug
                runAddr=self.mcode_list.search(":", labline, tk.END)
                #print("**"+runAddr+"**")#debug
                if runAddr != "" and runAddr != "0.0":
                    self.runDict[label]= int(self.mcode_list.get("%s-2c"% runAddr, runAddr),16)
        self.runEPSelect['values']= list(self.runDict.keys())
        self.runEPSelect.current(0)
        self.runFrom.set("00:")#??
        self.Emu.PC = 0
        self.initPC()

    def updateWatchWin(self):
        #print(self.watches)#debug
        self.watchList.delete(1.0, tk.END)
        for watch in self.watches:
            # get watch cells from memory
            #print("watch=", watch)
            if watch[2]:
                memStart=int(watch[2],16)
                if watch[1]:
                    watchLine = watch[2]+"  "+watch[1]
                else:
                    watchLine = watch[2]
                watchLine += " "* (15-len(watchLine))# Align to len = 30
                for n in range(memStart, memStart + watch[4]):
                    
                    #if self.arch == "vn":
                    memCell = self.memLabel[n].cget("text")
                    #else: # harvard
                    #    memCell = self.memLabel[n+256*self.Emu.datamem[self.Emu.curPage]].cget("text")
                    fmt=0 #default = hex
                    if watch[3] == "hex": fmt=0
                    if watch[3] == "dec": fmt=1
                    if watch[3] == "bin": fmt=3
                    if watch[3]== "str": fmt=2
                    #print(watch)#debug
                    #int(self.Emu.convert(1,self.Emu.regs[index]))
                    memCell = self.Emu.convert(fmt, int(memCell,16))
                    if fmt == 0:
                        memCell="Ox"+memCell

                    #print(memCell)#debug
                    watchLine += memCell + " "
                #print(watchLine)# debug
                self.watchList.insert("end", watchLine+'\n')

    # Help function
    def helpwin(self, event=None):
        import webbrowser
        webbrowser.open(cf.helpFile)

#### Final error save files!
def savefiles():
    print("Fatal Error!!! Trying to save files for recovery")
    #CocoIDE.file_save_as(CocoIDE, filepath="AMES-recovery.asm")



def main():
    parser = argparse.ArgumentParser(description='CocoIDE Extended - CDM8 assembler IDE')
    parser.add_argument('filename', nargs='?', help="Optional <filename> to open")
    parser.add_argument("-P", "--project", dest="project", type=str, default=None,
                        help="Open a folder as project (task directory)")
    args = parser.parse_args()
    # Frozen macOS apps launched from Finder start in "/"; running the IDE's
    # folder makes standard.mlb & co. resolvable by every code path (CWD-based
    # lookups included) without any Terminal involvement.
    if _isFrozen() and sys.platform == "darwin":
        try:
            os.chdir(appDir())
        except Exception:
            pass
    Emu = cdm8_emu.CDM8Emu()
    app = CocoIDE(Emu, filename=args.filename)
    tk._cocoide_root = app          # used by the native About menu handler
    if args.project:
        app.set_project(os.path.abspath(args.project))
    if sys.platform == "darwin":
        # Give the Tk window a moment to realize, then take over the macOS
        # application identity: Dock icon, menu-bar name, bring-to-front.
        app.after(150, _macActivate)
        app.after(300, _macInstallAppMenu)
    app.mainloop()

if __name__ == '__main__':
    main()



