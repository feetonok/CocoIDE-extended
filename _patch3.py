P = '/workspace/cocoideV1.91.pyw'
src = open(P, encoding='utf-8').read()

def rep(old, new):
    global src
    assert src.count(old) == 1, "NOT UNIQUE/FOUND: %r -> count=%d" % (old[:60], src.count(old))
    src = src.replace(old, new, 1)

# ---------- A. Non-blocking run loop (UI stays responsive; Stop works during fast run) ----------
lines = src.split('\n')
start = next(i for i, l in enumerate(lines) if l.strip().startswith('def runProg'))
end = next(i for i, l in enumerate(lines[start+1:], start+1) if l.strip().startswith('def changeTextSize'))
old_block = '\n'.join(lines[start:end])
assert 'while self.running and not self.Emu.HALT' in old_block
new_block = '''    def runProg(self, event=None):
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

'''
src = src.replace(old_block, new_block, 1)

# stepOnce must also reset button state
rep('''    def stepOnce(self):
        """Single instruction step (used by CDM8 > Step menu item)."""
        self.running = False
        self.Emu.step(cdm8_io.interrupt, cdm8_io.interruptVector)
        self.updateOPs()
        self.updateDisp()
        return "break"''',
'''    def stepOnce(self):
        """Single instruction step (CDM8 > Step menu / speed slider)."""
        if self.running:
            self.running = False
            self.Emu.HALT = True
        self.Emu.step(cdm8_io.interrupt, cdm8_io.interruptVector)
        self.updateOPs()
        self.updateDisp()
        self.runStopButton.config(text="Run ", fg="black", activeforeground="black")
        return "break"''')

# highlighter & compileText stop the emulator cleanly
rep('''        first, last = self.asstxt.yview()
        self.running=False
        self.mcode_list.delete(1.0, tk.END)''',
'''        first, last = self.asstxt.yview()
        if self.running:
            self.running = False
            self.Emu.HALT = True
            self._runStopped()
        self.mcode_list.delete(1.0, tk.END)''')

rep('''    def compileText(self, event=None):
        #print("Compiling")
        self.changed=False
        self.running=False''',
'''    def compileText(self, event=None):
        #print("Compiling")
        self.changed=False
        if self.running:
            self.running = False
            self.Emu.HALT = True
            self._runStopped()''')

# close_window: stop run loop cleanly + save config
rep('''    def close_window(self):
        if self.running: # Stop Emulator
            self.running = False
            self.Emu.HALT=True
''',
'''    def close_window(self):
        if self.running: # Stop Emulator
            self.running = False
            self.Emu.HALT=True
        try:
            if getattr(self, "_runId", None):
                self.after_cancel(self._runId)
        except Exception:
            pass
''')

rep('''        self.after(100, self.master.destroy)
        return''',
'''        self.saveConfig()
        self.after(100, self.master.destroy)
        return''')

# ---------- B. file_open: project awareness, recents, external files ----------
rep('''    def file_open(self, event=None, filepath=None):
        result = self.save_if_modified()
        if result != None: #None => Aborted or Save cancelled, False => Discarded, True = Saved or Not modified
            if filepath == None:
                filepath = filedialog.askopenfilename(filetypes=(('CDM8 Assembly', '*.asm'), ('All files', '*.*')))
            fileContents=""
            if filepath != None  and filepath != '':
                try:''',
'''    def file_open(self, event=None, filepath=None):
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
                try:''')

rep('''                if fileContents != "":
                    self.asstxt.delete(1.0, "end")
                    self.asstxt.edit_reset()
                    self.asstxt.edit_separator()
                    self.mcode_list.delete(1.0, tk.END)
                    self.asstxt.insert(1.0, fileContents)
                    self.asstxt.edit_modified(False)
                    self.file_path = filepath
                    self.set_title()
                    self.changed=True
                    self.highlighter()
                    self.asstxt.see("1.0")
        return "break"''',
'''                if fileContents != "":
                    self.asstxt.delete(1.0, "end")
                    self.asstxt.edit_reset()
                    self.asstxt.edit_separator()
                    self.mcode_list.delete(1.0, tk.END)
                    self.asstxt.insert(1.0, fileContents)
                    self.asstxt.edit_modified(False)
                    self.file_path = filepath
                    self.set_title()
                    self.changed=True
                    self.highlighter()
                    self.asstxt.see("1.0")
                    # Track recents & auto-open the containing folder as project
                    if filepath not in self.openedFiles:
                        self.openedFiles.insert(0, filepath)
                    self.openedFiles = self.openedFiles[:15]
                    folder = os.path.dirname(filepath)
                    if folder != self.projectPath:
                        self.set_project(folder)
                    else:
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
        return "break"''')

# ---------- C. Save dialogs start in project dir ----------
rep('''        if filepath == None:
            if self.file_path:
                self.file_path = str(self.file_path)[:-4]+ext
                filepath = filedialog.asksaveasfilename(filetypes=((filetype, '*'+ext), ('All files', '*.*')),
                        defaultextension ="ext", initialfile=self.file_path.split("/")[-1])
            else:
                filepath = filedialog.asksaveasfilename(filetypes=((filetype, '*'+ext), ('All files', '*.*')),
                    defaultextension=ext) #defaultextension='.asm\'''',
'''        if filepath == None:
            initdir = self.projectPath or self.startupFolder or self.homeDir
            if self.file_path:
                self.file_path = str(self.file_path)[:-4]+ext
                filepath = filedialog.asksaveasfilename(initialdir=initdir,
                        filetypes=((filetype, '*'+ext), ('All files', '*.*')),
                        defaultextension=ext, initialfile=os.path.basename(self.file_path))
            else:
                filepath = filedialog.asksaveasfilename(initialdir=initdir,
                    filetypes=((filetype, '*'+ext), ('All files', '*.*')),
                    defaultextension=ext) #defaultextension='.asm\'''')

rep('''            filepath = filedialog.asksaveasfilename(filetypes=(('Logisim Memory Image', '*.img'), ('All files', '*.*')), defaultextension =".img") #defaultextension='.txt\'''',
'''            filepath = filedialog.asksaveasfilename(
                initialdir=self.projectPath or self.startupFolder or self.homeDir,
                filetypes=(('Logisim Memory Image', '*.img'), ('All files', '*.*')),
                defaultextension =".img") #defaultextension='.txt\'''')

rep('''                self.asstxt.edit_modified(False)
                self.file_path = filepath
                self.set_title()
                return "Saved"''',
'''                self.asstxt.edit_modified(False)
                self.file_path = os.path.abspath(filepath)
                self.startupFolder = os.path.dirname(self.file_path)
                if self.file_path not in self.openedFiles:
                    self.openedFiles.insert(0, self.file_path)
                self.openedFiles = self.openedFiles[:15]
                self._rebuildRecentMenu()
                self._populateProjectTree()
                self.set_title()
                return "Saved"''')

# ---------- D. Title shows project + dirty dot ----------
rep('''    def set_title(self, event=None, titletxt=None):
        if titletxt != None:
            title=titletxt
        elif self.file_path != None:
            title = os.path.basename(self.file_path)
        else:
            title = "Untitled"
        self.master.title(title + " - " + self.TITLE)
        return''',
'''    def set_title(self, event=None, titletxt=None):
        if titletxt != None:
            title=titletxt
        elif self.file_path != None:
            title = os.path.basename(self.file_path)
            try:
                if self.asstxt.edit_modified():
                    title = "\\u25cf " + title   # VS Code style unsaved marker
            except Exception:
                pass
        else:
            title = "Untitled"
        proj = ""
        if self.projectPath:
            proj = " \\u2014 " + os.path.basename(self.projectPath)
        self.master.title(title + proj + " - " + self.TITLE)
        return''')

# keep title's dirty dot fresh on edits (Mac only, cheap check)
rep('''    def keydisable(self, event=None):
        # Disable ! and editing keys for lines with #! when running ames
        #print("keydisable",event.keysym, event.keycode, repr(event.char), event.type)# debug
''',
'''    def keydisable(self, event=None):
        # Disable ! and editing keys for lines with #! when running ames
        #print("keydisable",event.keysym, event.keycode, repr(event.char), event.type)# debug
        if platform == "darwin":
            try:
                if self.asstxt.edit_modified():
                    self.set_title()  # refresh the unsaved-changes dot
            except Exception:
                pass
''')

# ---------- E. Status bar with line:col + selection info ----------
rep('''        ### Create mainPanel under buttonBAr''',
'''        ## Status bar (below the main panel): cursor position, file type, project
        self.statusbar = tk.Frame(self, name="statusbar", bg="#e8e8e8", height=22)
        self.statusbar.grid(row=2, column=0, sticky="ew")
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
        self.asstxt.bind("<<CaretMove>>", self._updateStatusCursor, add=True)
        self.asstxt.bind("<ButtonRelease-1>", self._updateStatusCursor)
        self.asstxt.bind("<KeyRelease>", self._updateStatusCursor, add=True)

        ### Create mainPanel under buttonBAr''')

rep('''    def _markCurrentLine(self, event=None):''',
'''    def _updateStatusCursor(self, event=None):
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
                self.projStatusLabel.config(text="No folder open \\u2014 use Project > Open Folder\\u2026")
        except Exception:
            pass

    def _markCurrentLine(self, event=None):''')

rep('''        if not startup:
            self.statusMsg.config(text="Project:\\n" + os.path.basename(folder))
        return folder''',
'''        if not startup:
            self.statusMsg.config(text="Project:\\n" + os.path.basename(folder))
        try:
            self.projStatusLabel.config(text="Folder: " + folder)
        except Exception:
            pass
        return folder''')

# ---------- F. Fix Mac Ctrl-vs-Cmd binding conflicts ----------
rep('''        self.asstxt.bind("<Control-c>", self.copy)
        self.asstxt.bind("<Control-C>", self.copy)
        self.asstxt.bind("<Control-t>", self.cut)
        self.asstxt.bind("<Control-T>", self.cut)
        self.asstxt.bind("<Control-v>", self.paste)
        self.asstxt.bind("<Control-V>", self.paste)
''',
'''        if platform != "darwin":
            # On macOS plain Control bindings clash with Cmd ones (Tk maps
            # Command->Control there); real Cmd bindings are added below.
            self.asstxt.bind("<Control-c>", self.copy)
            self.asstxt.bind("<Control-C>", self.copy)
            self.asstxt.bind("<Control-t>", self.cut)
            self.asstxt.bind("<Control-T>", self.cut)
            self.asstxt.bind("<Control-v>", self.paste)
            self.asstxt.bind("<Control-V>", self.paste)
''')

# ---------- G. searchText placeholder guard + wrap-around ----------
rep('''    def searchText(self, event=None):
        try:
            searchStr = self.searchBox.get()
            if searchStr:
                if self.prevStr != searchStr:
                    self.startIndex = "1.0"''',
'''    def searchText(self, event=None):
        try:
            searchStr = self.searchBox.get()
            if searchStr == getattr(self, "searchPlaceholder", ""):
                return "break"
            if searchStr:
                if self.prevStr != searchStr:
                    self.startIndex = "1.0"''')

rep('''                self.startIndex = self.asstxt.search(searchStr, self.startIndex, tk.END)
                endIndex = self.asstxt.index('%s+%dc' % (self.startIndex, (len(searchStr)))) # find end of word''',
'''                try:
                    self.startIndex = self.asstxt.search(searchStr, self.startIndex, tk.END)
                except tk.TclError:
                    # wrapped past the end - restart from top
                    self.startIndex = "1.0"
                    self.startIndex = self.asstxt.search(searchStr, self.startIndex, tk.END)
                endIndex = self.asstxt.index('%s+%dc' % (self.startIndex, (len(searchStr)))) # find end of word''')

# ---------- H. Placeholder focus handlers ----------
rep('''    def gotoLine(self, event=None):''',
'''    def _searchFocusIn(self, event=None):
        if self.searchBox.get() == getattr(self, "searchPlaceholder", ""):
            self.searchBox.delete(0, tk.END)
            self.searchBox.config(fg="black")

    def _searchFocusOut(self, event=None):
        if not self.searchBox.get():
            self.searchBox.config(fg="grey")
            self.searchBox.insert(0, getattr(self, "searchPlaceholder", ""))

    def gotoLine(self, event=None):''')

# ---------- I. Editor popup menu: more commands ----------
rep('''        menu = tk.Menu(self.master,tearoff=0)
        menu.add_command(label="Cut",command=self.cut)
        menu.add_command(label="Copy",command=self.copy)
        menu.add_command(label="Paste",command=self.paste)
        menu.add_command(label="Cancel")
        menu.post(event.x_root,event.y_root)
        return

    # Mcode listing Popup memeu for mcode_list widget''',
'''        menu = tk.Menu(self.master,tearoff=0)
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
                messagebox.showinfo("Breakpoint", "No compiled code on this line.\\n"
                                    "Use CDM8 > Compile/Reset first.")
        except Exception:
            pass
        return "break"

    # Mcode listing Popup menu for mcode_list widget''')

# ---------- J. Shift-Tab outdent binding ----------
rep('''        self.asstxt.bind("<Tab>", lambda e: self.tabBlock(shift=1))
        self.asstxt.bind("<Control-Tab>", lambda e: self.tabBlock(shift=-1))''',
'''        self.asstxt.bind("<Tab>", lambda e: self.tabBlock(shift=1))
        self.asstxt.bind("<Shift-Tab>", lambda e: self.tabBlock(shift=-1))
        self.asstxt.bind("<Control-ISO_Left_Tab>", lambda e: self.tabBlock(shift=-1))
        self.asstxt.bind("<Control-Tab>", lambda e: self.tabBlock(shift=-1))
        if platform == "darwin":
            self.asstxt.bind("<Command-BracketLeft>", lambda e: self.tabBlock(shift=-1))
            self.asstxt.bind("<Command-BracketRight>", lambda e: self.tabBlock(shift=1))''')

# ---------- K. CLI: --project option in main() ----------
rep('''def main():
    parser = argparse.ArgumentParser(description='CocoIDE V0.92')
    #parser.add_argument('-p',dest='scrScale',action='store_const',const=True,default=False, help="-p  Presenter mode, expands program window to fill screen")
    parser.add_argument('filename', nargs='?', help="Option <filename>")
    #parser.add_argument("--file", "-f", type=str, required=False)
    args = parser.parse_args()
    #print(args.scrScale, args.filename)#debug
    #sys.excepthook = savefiles # If fatal error save files!
    Emu=cdm8_emu.CDM8Emu()
    CocoIDE(Emu, filename=args.filename).mainloop()
    #savefiles()''',
'''def main():
    parser = argparse.ArgumentParser(description='CocoIDE Extended - CDM8 assembler IDE')
    parser.add_argument('filename', nargs='?', help="Optional <filename> to open")
    parser.add_argument("-P", "--project", dest="project", type=str, default=None,
                        help="Open a folder as project (task directory)")
    args = parser.parse_args()
    Emu = cdm8_emu.CDM8Emu()
    app = CocoIDE(Emu, filename=args.filename)
    if args.project:
        app.set_project(os.path.abspath(args.project))
    app.mainloop()''')

open(P, 'w', encoding='utf-8').write(src)
print("patch3 OK")
