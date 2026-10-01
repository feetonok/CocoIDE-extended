P = '/workspace/cocoideV1.91.pyw'
src = open(P, encoding='utf-8').read()

def rep(old, new):
    global src
    assert src.count(old) == 1, "NOT UNIQUE/FOUND: %r -> count=%d" % (old[:60], src.count(old))
    src = src.replace(old, new, 1)

# ---------- 1. macOS font defaults + window state restore in __init__ ----------
rep('''        ## Fonts
        # Scale text font size to screen size, unless not configured''',
'''        ## Fonts
        # macOS-friendly monospace default (Menlo is the system mono font)
        if platform == "darwin" and not cf.basefont:
            self.editorFontName = "Menlo"
        elif platform.startswith("win"):
            self.editorFontName = "Consolas"
        else:
            self.editorFontName = "Courier"
        # Scale text font size to screen size, unless not configured''')

rep('''        # Save the default fixed font and set to size=self.textsize
        self.defaulttxtfont = font.Font(font="TkFixedFont")''',
'''        # Save the default fixed font and set to size=self.textsize
        self.defaulttxtfont = font.Font(family=self.editorFontName, size=self.textsize)''')

rep('''        self.master.geometry("1200x600")
        self.master.config(cursor="watch")''',
'''        self.master.config(cursor="watch")''')

# ---------- 2. Editor niceties right after bindKeys() in __init__ ----------
rep('''        mainPanel = tk.Frame(self, name='cocoidewin')#, bg="yellow")
        mainPanel.grid(row=1,column=0, sticky="nsew")''',
'''        mainPanel = tk.Frame(self, name='cocoidewin')#, bg="yellow")
        self.mainPanel = mainPanel
        mainPanel.grid(row=1,column=0, sticky="nsew")''')

rep('''        ## Bind editor keys
        self.bindKeys()
''',
'''        ## Bind editor keys
        self.bindKeys()

        # Modern editor niceties: current-line highlight & mouse wheel scrolling
        self.asstxt.config(insertbackground="red")
        self.asstxt.tag_configure("currentline", background="#f0f0f0")
        self.asstxt.bind("<<CaretMove>>", self._markCurrentLine)
        self._bindMouseWheel(self.asstxt)
        self._bindMouseWheel(self.mcode_list)
        self._bindMouseWheel(self.watchList)
''')

# ---------- 3. Startup at end of __init__: config, project browser, saved window state ----------
rep('''        ### Finally load file if filename provided from commmand line
        if filename:
            try:
                self.file_open(filepath=filename)
            except:
                print("File not found!")
                exit()
        self.master.config(cursor="")
''',
'''        ### Finally load file if filename provided from command line
        self.loadConfig()
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
                self.master.geometry("1200x700")
        else:
            self.master.geometry("1200x700")

        # Build the project file browser sidebar (VS Code style Explorer)
        self._buildProjectBrowser()
        # Reopen last session's project (if it still exists)
        if self.projectPath and os.path.isdir(self.projectPath):
            self.set_project(self.projectPath, startup=True)
        elif self.recentProjects:
            for p in self.recentProjects:
                if os.path.isdir(p):
                    self.set_project(p, startup=True)
                    break

        self.master.config(cursor="")
''')

# ---------- 4. bindKeys: macOS Command bindings + compile/run/F5 + selectall ----------
rep('''        self.asstxt.bind("<Control-a>", self.file_save_as)
        self.asstxt.bind("<Control-q>", self.file_quit)''',
'''        self.asstxt.bind("<Control-a>", self.selectall)
        self.asstxt.bind("<Control-q>", self.file_quit)''')

rep('''        # OSX/MAC os users add cmd key options as well
        if platform == "darwin":
            self.asstxt.bind("<Command-o>", self.file_open)
            self.asstxt.bind("<Command-O>", self.file_open)
            #self.asstxt.bind("<Command-Shift-S>", self.file_save_as)
            self.asstxt.bind("<Command-S>", self.file_save_as)
            self.asstxt.bind("<Command-s>", self.file_save)
            self.asstxt.bind("<Command-n>", self.file_new)
            self.asstxt.bind("<Command-N>", self.file_new)
''',
'''        # Compile / Run / Step / Breakpoint shortcuts (both platforms)
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
        self.asstxt.bind("<Escape>", self.clearEditorHighlights)

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
''')

# unbindKeys: also remove darwin extras so AMES mode is consistent
rep('''        if platform == "darwin":
            self.asstxt.bind("<Command-o>", None)
            self.asstxt.bind("<Command-O>", None)
            self.asstxt.bind("<Command-S>", None)
            self.asstxt.bind("<Command-s>", None)
            self.asstxt.bind("<Command-n>", None)
            self.asstxt.bind("<Command-N>", None)
''',
'''        if platform == "darwin":
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
''')

# ---------- 5. New methods block before popmenu ----------
rep('''    # Editor Popup menu for asstxt widget
    def popmenu(self, event=None):''',
'''    #### Project / folder support (modern IDE-style workspace)

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
                self.projectPath = cfg.get("project")
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
                   "project": self.projectPath or "",
                   "startupFolder": self.startupFolder or "",
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
        """Set the working project directory and populate the file browser."""
        folder = os.path.abspath(folder)
        if not os.path.isdir(folder):
            messagebox.showerror("Project", "Folder not found:\\n" + folder)
            return
        self.projectPath = folder
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
            self.statusMsg.config(text="Project:\\n" + os.path.basename(folder))
        return folder

    def close_project(self, event=None):
        self.projectPath = None
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
                script = ('tell application "Terminal"\\nactivate\\n'
                          'do script "cd \'%s\'"\\nend tell' % folder)
                subprocess.Popen(["osascript", "-e", script])
            elif platform.startswith("win"):
                subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", "cd /d \"%s\"" % folder])
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
                    f.write("; " + os.path.basename(filepath) + "\\n")
        except Exception as e:
            messagebox.showerror("New File", "Could not create file:\\n%s" % e)
            return "break"
        self.file_new()
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
            self.projCanvas.configure(scrollregion=(0, 0, self.projFrame.winfo_reqwidth(),
                                                    self.projFrame.winfo_reqheight()))
        self.projFrame.bind('<Configure>', _conf_inner)

        def _conf_canvas(event=None):
            self.projCanvas.itemconfigure(self.projWin, width=max(event.width,
                                                        self.projFrame.winfo_reqwidth()))
        self.projCanvas.bind('<Configure>', _conf_canvas)
        self._bindMouseWheel(self.projCanvas)

        # Insert into the layout as column 0 (editor shifts to column 1 etc.)
        panel.grid(row=0, column=0, sticky="nsew", rowspan=3)
        self.mainPanel.grid_columnconfigure(0, minsize=190)
        self.projPanel = panel
        self.projVisible = True
        self.projTreeItems = {}   # dirpath -> (row_index, label_widget)
        self._populateProjectTree()
        self.projmenu.entryconfig("Close Project",
                                  state=tk.NORMAL if self.projectPath else tk.DISABLED)

    def toggleProjectBrowser(self, event=None):
        if getattr(self, "projVisible", True):
            self.projCanvas.itemconfigure(self.projWin, state="hidden")
            self.projFrame.grid_remove()
            self.mainPanel.grid_columnconfigure(0, minsize=28)
            self.projToggle.config(text="▸")
            self.projTitle.config(text="")
            self.projVisible = False
        else:
            self.projCanvas.itemconfigure(self.projWin, state="normal")
            self.projFrame.grid()
            self.mainPanel.grid_columnconfigure(0, minsize=190)
            self.projToggle.config(text="▾")
            self.projTitle.config(text="PROJECT")
            self.projVisible = True
        self._populateProjectTree()
        return "break"

    def _populateProjectTree(self, event=None):
        """Fill the sidebar with the project tree: folders then .asm/PDF/doc files."""
        if not hasattr(self, "projFrame"):
            return
        for child in self.projFrame.winfo_children():
            child.destroy()
        self.projTreeItems = {}
        bold = (self.editorFontName, self.textsize, "bold")
        norm = (self.editorFontName, self.textsize)
        row = 0

        def addLabel(text, fg="#000000", fontspec=norm, indent=0, command=None, bg="#fafafa"):
            nonlocal row
            l = tk.Label(self.projFrame, text=text, anchor="w", justify=tk.LEFT,
                         fg=fg, font=fontspec, bg=bg, padx=4 + indent*12, cursor="hand2")
            l.grid(row=row, column=0, sticky="ew")
            if command:
                l.bind("<Button-1>", command)
                l.bind("<Enter>", lambda e, w=l: w.config(fg="#1a5fb4", underline=True))
                l.bind("<Leave>", lambda e, w=l, c=fg: w.config(fg=c, underline=False))
            row += 1
            return l

        if not self.projectPath:
            addLabel("No folder open", fg="#888888")
            addLabel("Click \"…\" to open", fg="#888888")
            addLabel("a task folder", fg="#888888")
        else:
            self.projTitle.config(text=os.path.basename(self.projectPath).upper()[:16] or "PROJECT")
            addLabel(os.path.basename(self.projectPath) or self.projectPath,
                     fontspec=bold, fg="#333333")
            asmFiles, otherFiles, dirs = [], [], []
            try:
                entries = sorted(os.listdir(self.projectPath),
                                 key=lambda s: s.lower())
            except Exception:
                entries = []
            for name in entries:
                if name.startswith("."):
                    continue
                full = os.path.join(self.projectPath, name)
                if os.path.isdir(full):
                    dirs.append(name)
                elif name.lower().endswith(cf.fileext):
                    asmFiles.append(name)
                else:
                    otherFiles.append(name)
            for name in asmFiles:
                full = os.path.join(self.projectPath, name)
                mark = "● " if full == self.file_path else "   "
                lbl = addLabel(mark+name, fg="#0b6e0b",
                               command=lambda e, p=full: self.file_open(filepath=p))
                if full == self.file_path:
                    lbl.config(font=bold)
            for name in otherFiles:
                full = os.path.join(self.projectPath, name)
                addLabel("   " + name, fg="#5555aa",
                         command=lambda e, p=full: self.openExternalFile(p))
            for name in dirs:
                full = os.path.join(self.projectPath, name)
                addLabel("  📁 " + name + "/", fontspec=bold, fg="#333333",
                         command=lambda e, p=full: self.set_project(p))
        self.projFrame.update_idletasks()

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
            start = self.asstxt.search(r"(\\S+\\s*)?\\S*$", "insert linestart", "insert",
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
        self.asstxt.insert("%d.0 lineend+1c" % ln, "\\n" + lineTxt)
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
        """Single instruction step (used by CDM8 > Step menu item)."""
        self.running = False
        self.Emu.step(cdm8_io.interrupt, cdm8_io.interruptVector)
        self.updateOPs()
        self.updateDisp()
        return "break"

    def compileRun(self, event=None):
        """F5: compile then run, like pressing both buttons."""
        self.compileText()
        if not self.running:
            self.runProg()
        return "break"

    def aboutDialog(self, event=None):
        messagebox.showinfo("About CocoIDE",
            self.TITLE + "\\n"
            "CDM8 assembler/IDE/emulator for teaching\\n"
            "Extended fork: project folders, file browser, recent files,\\n"
            "macOS-friendly shortcuts (Cmd+S/O/N/B/R/F/G/D).\\n"
            "Original: (c) M L Walters, Prof A Shafarenko 2016-2018")
        return "break"

    # Editor Popup menu for asstxt widget
    def popmenu(self, event=None):''')

open(P, 'w', encoding='utf-8').write(src)
print("patch2 OK")
