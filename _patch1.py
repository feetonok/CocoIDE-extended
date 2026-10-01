import re

P = '/workspace/cocoideV1.91.pyw'
src = open(P, encoding='utf-8').read()

def rep(old, new):
    global src
    assert src.count(old) == 1, "NOT UNIQUE/FOUND: %r -> count=%d" % (old[:60], src.count(old))
    src = src.replace(old, new, 1)

# ---------- 1. Title & version ----------
rep("title = 'CocoIDE V1.91'", "title = 'CocoIDE Extended V2.0'")

# ---------- 2. Imports ----------
rep("import codecs\nimport copy\nimport pyclbr",
    "import codecs\nimport copy\nimport json\nimport subprocess\nimport pyclbr")

# ---------- 3. __init__ state for projects ----------
rep('''        self.file_name = "Untitled"
        self.file_path = None ##??
        self.changed = False''',
'''        self.file_name = "Untitled"
        self.file_path = None ##??
        self.changed = False
        ## Project / recent-files management (modern IDE style)
        self.projectPath = None       # currently open project folder (abs path)
        self.recentProjects = []      # most recent first
        self.openedFiles = []         # abs paths of files opened this session
        self.configDir = os.path.join(os.path.expanduser("~"), ".cocoide")
        self.configFile = os.path.join(self.configDir, "config.json")
        self.startupFolder = None     # last folder used by Open/Save dialogs''')

# ---------- 4. Menus ----------
rep('''        self.filemenu.add_command(label="Open", command=self.file_open, accelerator=comkey+"o")
        self.filemenu.add_command(label="Save", command=self.file_save, accelerator=comkey+"s")
        self.filemenu.add_command(label="SaveAs", command=self.file_save_as, accelerator=comkey+"S")
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Quit", command=self.close_window, accelerator=comkey+"q")#self.quit)
        self.menubar.add_cascade(label="File", menu=self.filemenu, accelerator=comkey+"f")
''',
'''        self.filemenu.add_command(label="Open...", command=self.file_open, accelerator=comkey+"o")
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
''')

# Emulator menu: Step / Clear BPs / shortcuts
rep('''        self.emumenu.add_command(label="Compile/Reset", command=self.compileText)
        self.emumenu.add_command(label="Run", command=self.runProg)
        self.emumenu.add_command(label="Stop", command=self.runProg)
        self.emumenu.add_command(label="Toggle BP", command=self.toggleBP)''',
'''        self.emumenu.add_command(label="Compile/Reset", command=self.compileText,
                                 accelerator="Cmd+B")
        self.emumenu.add_command(label="Run", command=self.runProg, accelerator="Cmd+R")
        self.emumenu.add_command(label="Step", command=lambda: self.stepOnce())
        self.emumenu.add_command(label="Toggle BP", command=self.toggleBP, accelerator="Cmd+F9")
        self.emumenu.add_command(label="Clear Breakpoints", command=self.clearBPs)''')

# Edit menu: Select All
rep('''        self.editmenu.add_separator()
        self.txtmenu = tk.Menu(self.editmenu, tearoff=0)''',
'''        self.editmenu.add_command(label="Select All", command=self.selectall, accelerator=comkey+"a")
        self.editmenu.add_separator()
        self.txtmenu = tk.Menu(self.editmenu, tearoff=0)''')

# Help menu: About
rep('''        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="Manual", command=self.helpwin)''',
'''        self.helpmenu = tk.Menu(self.menubar, tearoff=0)
        self.helpmenu.add_command(label="Manual", command=self.helpwin)
        self.helpmenu.add_command(label="About CocoIDE", command=self.aboutDialog)''')

# ---------- 5. Toolbar tidy-up + search placeholder ----------
rep('''        self.editButtons = tk.Frame(buttonBar)
        self.editButtons.pack(side=tk.LEFT, fill=tk.BOTH)
        self.newButton = tk.Button(self.editButtons, text="New", command=self.file_new)
        self.newButton.grid(row=0, column=0, rowspan=1, sticky="news")
        self.openButton = tk.Button(self.editButtons, text="Open", command=self.file_open)
        self.openButton.grid(row=0, column=1, rowspan=1,sticky="ns")
        self.saveButton = tk.Button(self.editButtons, text="Save", command=self.file_save)
        self.saveButton.grid(row=0, column=2, rowspan=1, sticky="ns")
        
        self.saveAsButton = tk.Button(self.editButtons, text="SaveAs", command=self.file_save_as)
        self.saveAsButton.grid(row=0, column=3, rowspan=1, columnspan=2, sticky="nws")
        self.exitButton = tk.Button(self.editButtons, text="Quit", height=3, command=self.close_window)
        self.exitButton.grid(row=0, column=5, rowspan=2, sticky="ns")
        
        self.searchBox = tk.Entry(self.editButtons, width=8)
        self.searchBox.bind("<Return>", self.searchText)
        self.searchBox.bind("<Button-3>", self.searchText)''',
'''        self.editButtons = tk.Frame(buttonBar)
        self.editButtons.pack(side=tk.LEFT, fill=tk.BOTH)
        # Modern minimal toolbar: New / Open (files & folders menu) / Save / Save As / Quit.
        self.newButton = tk.Button(self.editButtons, text="+ New", command=self.file_new)
        self.newButton.grid(row=0, column=0, rowspan=2, sticky="ns", padx=1)
        self.openButton = tk.Button(self.editButtons, text="Open...")
        self.openButton.grid(row=0, column=1, rowspan=2, sticky="ns", padx=1)
        self.openButton.bind("<Button-1>", self.show_open_menu)
        self.saveButton = tk.Button(self.editButtons, text="Save", command=self.file_save)
        self.saveButton.grid(row=0, column=2, rowspan=2, sticky="ns", padx=1)
        self.saveAsButton = tk.Button(self.editButtons, text="Save As...")
        self.saveAsButton.grid(row=0, column=3, rowspan=2, sticky="ns", padx=1)
        self.saveAsButton.bind("<Button-1>", lambda e: self.file_save_as())
        self.exitButton = tk.Button(self.editButtons, text="Quit", command=self.close_window)
        self.exitButton.grid(row=0, column=5, rowspan=2, sticky="ns", padx=1)

        self.searchBox = tk.Entry(self.editButtons, width=10, fg="grey")
        self.searchPlaceholder = "Find..."
        self.searchBox.insert(0, self.searchPlaceholder)
        self.searchBox.bind("<FocusIn>", self._searchFocusIn)
        self.searchBox.bind("<FocusOut>", self._searchFocusOut)
        self.searchBox.bind("<Return>", self.searchText)
        self.searchBox.bind("<Button-3>", self.searchText)''')

open(P, 'w', encoding='utf-8').write(src)
print("patch1 OK")
