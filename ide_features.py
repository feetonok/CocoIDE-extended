#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CocoIDE Extended - modern IDE helper features.

Provides:
  * Cdm8AutoComplete   - keyword/register/macro-aware autocomplete popup
                         (VS Code style, Tab / Enter accept, Esc dismiss)
  * HoverTooltip       - word-hover documentation tooltips (registers,
                         opcodes, directives, condition codes, meta comments)
  * explain_error()    - turns raw cocas assembler errors into clear,
                         student-friendly messages with hints and examples
  * RecentProjects     - per-user "recent projects" store (~/.cocoide.json)
  * project helpers    - open a folder as a project, scan for .asm files,
                         create new task folders/files

(c) CocoIDE-extended fork
"""

from __future__ import absolute_import, print_function

import os
import sys
import json
import time

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:      # Python 2 fallback (legacy support)
    import Tkinter as tk

IS_MAC = (sys.platform == "darwin")

# ---------------------------------------------------------------------------
#  Language data (opcodes / directives / macros / registers / conditions)
# ---------------------------------------------------------------------------

# Core CDM8 Mark 4 instruction set with syntax + description.
# kind: 'insn' - instruction, 'dir' - assembler directive, 'cond' - condition code
CDM8_REFERENCE = [
    # ---- data transfer ----
    ("move", "insn", "move Rd, Rs", "Copy register Rs into Rd.", "instruction"),
    ("ld",   "insn", "ld Rs, addr", "Load the CONTENTS of memory byte 'addr' into register Rs.", "instruction"),
    ("st",   "insn", "st addr, Rs", "Store the value in register Rs into memory byte 'addr'.", "instruction"),
    ("ldc",  "insn", "ldc Rs, Rd", "Indirect load: Rd <- memory[Rs] (Rs is used as an address).", "instruction"),
    ("ldi",  "insn", "ldi Rd, n", "Load Immediate: put the number/label/character n directly into Rd.", "instruction"),
    ("ext",  "insn", "ext label", "Declare 'label' as external - defined in another module (link with Cocol).", "directive"),

    # ---- arithmetic & logic (Rd <- Rd OP Rs) ----
    ("add",  "insn", "add Rd, Rs", "Add: Rd <- Rd + Rs (flags C/V/Z/N updated).", "instruction"),
    ("addc", "insn", "addc Rd, Rs", "Add with Carry: Rd <- Rd + Rs + C.", "instruction"),
    ("sub",  "insn", "sub Rd, Rs", "Subtract: Rd <- Rd - Rs.", "instruction"),
    ("and",  "insn", "and Rd, Rs", "Bitwise AND: Rd <- Rd & Rs.", "instruction"),
    ("or",   "insn", "or Rd, Rs", "Bitwise OR: Rd <- Rd | Rs.", "instruction"),
    ("xor",  "insn", "xor Rd, Rs", "Bitwise XOR: Rd <- Rd ^ Rs.", "instruction"),
    ("cmp",  "insn", "cmp Rd, Rs", "Compare (Rd - Rs): sets flags but does NOT change Rd.", "instruction"),

    # ---- unary ops ----
    ("not",  "insn", "not Rd", "Bitwise complement: Rd <- ~Rd.", "instruction"),
    ("neg",  "insn", "neg Rd", "Two's complement negate: Rd <- -Rd.", "instruction"),
    ("dec",  "insn", "dec Rd", "Decrement: Rd <- Rd - 1.", "instruction"),
    ("inc",  "insn", "inc Rd", "Increment: Rd <- Rd + 1.", "instruction"),
    ("shr",  "insn", "shr Rd", "Shift right by 1 (0 shifted in, C gets bit 0).", "instruction"),
    ("shla", "insn", "shla Rd", "Shift left arithmetic (bit 7 -> C, 0 shifted in).", "instruction"),
    ("shra", "insn", "shra Rd", "Shift right arithmetic (sign bit preserved).", "instruction"),
    ("rol",  "insn", "rol Rd", "Rotate left.", "instruction"),

    # ---- stack ----
    ("push", "insn", "push Rs", "Decrement SP, then store Rs on the stack.", "instruction"),
    ("pop",  "insn", "pop Rd", "Load Rd from top of stack, then increment SP.", "instruction"),
    ("pushall", "insn", "pushall", "Push r0-r3 onto the stack (Mark 4).", "instruction"),
    ("popall",  "insn", "popall",  "Pop the stack into r0-r3 (Mark 4).", "instruction"),
    ("ldsa", "insn", "ldsa Rd, n", "Load Stack Address: Rd <- SP + n (local variable addressing).", "instruction"),
    ("addsp", "insn", "addsp n", "Add signed offset n to the Stack Pointer.", "instruction"),
    ("setsp", "insn", "setsp n", "Set Stack Pointer to the template frame size n.", "instruction"),

    # ---- subroutines / interrupts / misc ----
    ("jsr",  "insn", "jsr label", "Jump to Subroutine: push return address, PC <- label.", "instruction"),
    ("rts",  "insn", "rts", "Return from Subroutine: pop return address into PC.", "instruction"),
    ("osi",  "insn", "osi n", "Software interrupt: raise OS interrupt with vector/param n.", "instruction"),
    ("osix", "insn", "osix n", "Extended OS interrupt with parameter n.", "instruction"),
    ("ioi",  "insn", "ioi", "Enable I/O interrupts.", "instruction"),
    ("rti",  "insn", "rti", "Return from Interrupt.", "instruction"),
    ("crc",  "insn", "crc", "Clear the interrupt request line.", "instruction"),
    ("nop",  "insn", "nop", "No Operation.", "instruction"),
    ("wait", "insn", "wait", "Wait for next clock tick (low power).", "instruction"),
    ("halt", "insn", "halt", "Stop the processor.", "instruction"),

    # ---- branches ----
    ("br",  "insn", "br label", "Unconditional branch/jump to label.", "instruction"),
    ("beq", "insn", "beq label", "Branch if Equal (Z=1).", "instruction"),
    ("bz",  "insn", "bz label",  "Branch if Zero (Z=1). Same as beq.", "instruction"),
    ("bne", "insn", "bne label", "Branch if Not Equal (Z=0).", "instruction"),
    ("bnz", "insn", "bnz label", "Branch if Not Zero (Z=0).", "instruction"),
    ("bhs", "insn", "bhs label", "Branch if Higher or Same unsigned (C=0).", "instruction"),
    ("bcc", "insn", "bcc label", "Branch if Carry Clear (C=0). Same as bhs.", "instruction"),
    ("bcs", "insn", "bcs label", "Branch if Carry Set (C=1).", "instruction"),
    ("blo", "insn", "blo label", "Branch if Lower unsigned (C=1). Same as bcs.", "instruction"),
    ("bmi", "insn", "bmi label", "Branch if MInus / negative (N=1).", "instruction"),
    ("bpl", "insn", "bpl label", "Branch if PLus / non-negative (N=0).", "instruction"),
    ("bvs", "insn", "bvs label", "Branch if oVerflow Set (V=1).", "instruction"),
    ("bvc", "insn", "bvc label", "Branch if oVerflow Clear (V=0).", "instruction"),
    ("bhi", "insn", "bhi label", "Branch if HIger unsigned (C=0 and Z=0).", "instruction"),
    ("bls", "insn", "bls label", "Branch if Lower or Same unsigned (C=1 or Z=1).", "instruction"),
    ("bge", "insn", "bge label", "Branch if Greater or Equal signed (V=N).", "instruction"),
    ("blt", "insn", "blt label", "Branch if Less Than signed (V!=N).", "instruction"),
    ("bgt", "insn", "bgt label", "Branch if Greater Than signed (Z=0 and V=N).", "instruction"),
    ("ble", "insn", "ble label", "Branch if Less or Equal signed (Z=1 or V!=N).", "instruction"),

    # ---- assembler directives ----
    ("asect", "dir", "asect addr", "Absolute section: place following code/data at fixed memory address 'addr'.", "directive"),
    ("rsect", "dir", "rsect name", "Relative section: relocatable block named 'name' (linked by Cocol).", "directive"),
    ("tplate", "dir", "tplate name", "Define a stack frame template (for subroutine local variables).", "directive"),
    ("end",   "dir", "end", "End of the source program (required!).", "directive"),
    ("dc",    "dir", "dc list", "Define Constants: bytes, e.g. dc 0x41,65,'A',\"str\",label+1.", "directive"),
    ("ds",    "dir", "ds n", "Define Storage: reserve n zero bytes (variables/buffers).", "directive"),

    # ---- macro language (standard.mlb) ----
    ("macro", "dir", "macro name / arity", "Begin a macro definition with 'arity' parameters; ends with 'mend'.", "directive"),
    ("mend",  "dir", "mend", "End of a macro definition.", "directive"),
    ("mpush", "dir", "mpush $1,...", "Push values onto the macro-time stack.", "directive"),
    ("mpop",  "dir", "mpop var,...", "Pop the macro-time stack into macro variables.", "directive"),
    ("mread", "dir", "mread var,...", "Read macro-time stack into variables without popping.", "directive"),
    ("unique", "dir", "unique v1,v2,...", "Assign unused registers to macro variables.", "directive"),
    ("define", "dir", "define name, value", "Define an assembler symbol.", "directive"),
    ("while", "dir", "while ... wend", "Macro loop: repeat until a 'stays <cond>' fails.", "directive"),
    ("do",    "dir", "do ... until <cond>", "Macro loop: repeat at least once until condition holds.", "directive"),
    ("continue", "dir", "continue", "Restart the enclosing while/do loop.", "directive"),
    ("break", "dir", "break", "Exit the enclosing while/do loop.", "directive"),
    ("if",    "dir", "if <cond> ... fi", "Conditional assembly.", "directive"),
    ("then",  "dir", "then", "'if' continuation word.", "directive"),
    ("else",  "dir", "else", "'if' alternative branch.", "directive"),
    ("fi",    "dir", "fi", "End of 'if' block.", "directive"),
    ("wend",  "dir", "wend", "End of 'while' loop.", "directive"),
    ("until", "dir", "until <cond>", "End of 'do' loop with exit condition.", "directive"),
    ("tst",   "insn", "tst Rd", "Test register: sets Z/N flags from Rd (used by loops).", "instruction"),
    ("clr",   "insn", "clr Rd", "Clear register: Rd <- 0.", "instruction"),
    ("stays", "dir", "stays <cond>", "Loop continuation test used inside while/do loops.", "directive"),
    ("true",  "dir", "true", "Condition that always holds.", "directive"),
    ("false", "dir", "false", "Condition that never holds.", "directive"),

    # ---- condition codes (used by stays/if/until) ----
    ("eq", "cond", "eq", "EQual: Z=1.", "condition"),
    ("ne", "cond", "ne", "Not Equal: Z=0.", "condition"),
    ("z",  "cond", "z",  "Zero flag set.", "condition"),
    ("nz", "cond", "nz", "Not Zero.", "condition"),
    ("cs", "cond", "cs", "Carry Set.", "condition"),
    ("cc", "cond", "cc", "Carry Clear.", "condition"),
    ("hs", "cond", "hs", "Higher or Same (unsigned).", "condition"),
    ("lo", "cond", "lo", "Lower (unsigned).", "condition"),
    ("mi", "cond", "mi", "MInus (negative).", "condition"),
    ("pl", "cond", "pl", "PLus (non-negative).", "condition"),
    ("vs", "cond", "vs", "oVerflow Set.", "condition"),
    ("vc", "cond", "vc", "oVerflow Clear.", "condition"),
    ("hi", "cond", "hi", "HIer (unsigned, C=0 and Z=0).", "condition"),
    ("ls", "cond", "ls", "Lower or Same (unsigned).", "condition"),
    ("gt", "cond", "gt", "Greater Than (signed).", "condition"),
    ("ge", "cond", "ge", "Greater or Equal (signed).", "condition"),
    ("lt", "cond", "lt", "Less Than (signed).", "condition"),
    ("le", "cond", "le", "Less or Equal (signed).", "condition"),

    # ---- pseudo instructions implemented as macros in standard.mlb ----
    ("ret",    "insn", "ret", "Return from subroutine (macro for rts).", "instruction"),
    ("jmp",    "insn", "jmp label", "Jump (macro for br).", "instruction"),
    ("jsrr",   "insn", "jsrr Rs", "Jump to SubRoutine in register Rs.", "instruction"),
    ("shl",    "insn", "shl Rd", "Shift Left (macro for shla).", "instruction"),
    ("ei",     "insn", "ei", "Enable Interrupts (macro).", "instruction"),
    ("di",     "insn", "di", "Disable Interrupts (macro).", "instruction"),
    ("ldv",    "insn", "ldv Rd, t.field", "LoaD Variable from template field.", "instruction"),
    ("stv",    "insn", "stv Rs, t.field", "STore Variable into template field.", "instruction"),
    ("save",   "insn", "save ...", "Save registers on stack (macro).", "instruction"),
    ("restore","insn", "restore ...", "Restore registers from stack (macro).", "instruction"),
    ("stsp",   "insn", "stsp n", "STore SP plus n (Mark 3 compatible macro).", "instruction"),
    ("ldsp",   "insn", "ldsp n", " LoaD SP plus n (Mark 3 compatible macro).", "instruction"),
]

REG_INFO = {
    "r0": ("General purpose register r0 (8-bit, values 0..255).\n"
           "Conventionally used as the first data/pointer register.\n"
           "Also one of the two link registers for jsr/rts."),
    "r1": ("General purpose register r1 (8-bit, values 0..255).\n"
           "Conventionally the second data/pointer register.\n"
           "Also a link register for jsr/rts."),
    "r2": ("General purpose register r2 (8-bit, values 0..255)."),
    "r3": ("General purpose register r3 (8-bit, values 0..255).\n"
           "Conventionally reserved as the Stack Pointer shadow\n"
           "in some calling conventions."),
}

META_COMMENTS = [
    ("#$arch=hv", "Use Harvard architecture page (separate code ROM / data RAM banks)."),
    ("#$arch=vn", "Use Von Neumann architecture page (single shared memory bank). Default."),
    ("#$str", "Display this memory/watch row as ASCII String."),
    ("#$dec", "Display this memory/watch row as signed Decimal."),
    ("#$hex", "Display this memory/watch row as Hexadecimal."),
    ("#$bin", "Display this memory/watch row as Binary."),
]


def reg_doc(word):
    w = word.lower()
    if w in REG_INFO:
        return REG_INFO[w]
    return None


def ref_lookup(word):
    """Return (syntax, description, category) for a token, else None."""
    w = word.lower()
    for name, kind, syntax, desc, cat in CDM8_REFERENCE:
        if name == w:
            return syntax, desc, cat
    return None


# ---------------------------------------------------------------------------
#  Error explanation - make compiler diagnostics student friendly
# ---------------------------------------------------------------------------

_BIN_OPS = {"move", "add", "addc", "sub", "and", "or", "xor", "cmp", "ldc"}
_MEM_OPS = {"ld", "st"}
_UNARY_OPS = {"not", "neg", "dec", "inc", "shr", "shla", "shra", "rol",
              "push", "pop", "tst", "clr", "ldsa"}
_BRANCH_OPS = {"br", "beq", "bz", "bne", "bnz", "bhs", "bcs", "blo", "bcc",
               "bmi", "bpl", "bvs", "bvc", "bhi", "bls", "bge", "blt",
               "bgt", "ble", "jsr"}
_ZERO_OPS = {"rts", "rti", "ioi", "crc", "nop", "wait", "halt",
             "pushall", "popall", "ret", "jmp"}

# Common typos seen in student code
_TYPOS = {
    "mova": "move", "mov": "move", "mv": "move", "cp": "move",
    "lda": "ld", "load": "ld", "store": "st", "sto": "st",
    "jmp": "jmp (macro) or br", "goto": "br", "call": "jsr",
    "return": "rts / ret", "subb": "sub", "subtract": "sub",
    "multiply": "no MUL instruction - use repeated add",
    "div": "no DIV instruction - use repeated subtract",
    "mod": "no MOD instruction", "mul": "no MUL instruction",
    "adc": "addc", "cmpi": "cmp", "test": "tst",
    "pushal": "pushall", "popal": "popall", "ldia": "ldi",
    "ifz": "bz", "bnlz": "bnz", "branch": "br / b<cond>",
    "endif": "fi", "next": "wend", "loop": "while / do",
    "db": "dc", "dw": "dc", "resb": "ds", "equ": "define",
    "org": "asect", "section": "rsect / asect",
}


def _operand_hint(op):
    """One-line syntax reminder for an opcode."""
    r = ref_lookup(op)
    if r:
        return r[0]
    return None


def explain_error(raw_msg):
    """Translate a cocas error string into a clearer multi-line message.

    Returns the (possibly enriched) message string. Original information is
    always preserved so nothing gets lost.
    """
    if not raw_msg:
        return raw_msg
    msg = str(raw_msg).strip()
    low = msg.lower()
    hint = None

    # -- extract line number if present --
    import re
    m = re.search(r"line\s+(\d+)", msg, re.I)
    lineno = int(m.group(1)) if m else None

    # --- invalid opcode ---
    m = re.search(r"invalid opcode:\s*(\S+)", msg, re.I)
    if m:
        op = m.group(1)
        corr = _TYPOS.get(op.lower())
        if corr:
            hint = ("'%s' is not a CDM8 opcode. Did you mean '%s'?\n"
                    "Remember: after typing an opcode press Tab to accept an "
                    "autocomplete suggestion." % (op, corr))
        else:
            hint = ("'%s' is not a CDM8 opcode.\n"
                    "Check the spelling against the instruction set: ld, st, ldi, "
                    "move, ldc, add, sub, cmp, and, or, xor, not, neg, inc, dec, "
                    "push, pop, jsr, rts, br, b<cond>, halt ...\n"
                    "CDM8 has NO multiply/divide instructions - implement them "
                    "with repeated add/subtract loops." % op)
    # --- register expected ---
    elif "register expected" in low:
        # Try to find the offending opcode earlier in the message context
        op = None
        m2 = re.search(r"([a-z_][a-z0-9_]*)\s+r?\d?[, ]", msg)
        hint = ("This instruction expects REGISTER operands (r0..r3), "
                "but a number or label was found instead.\n"
                "Example: 'add r0, r1' adds two registers.\n"
                "To combine a register with a constant, load the constant "
                "first:  ldi r1, 1  then  add r0, r1.")
    elif "only one operand expected" in low:
        hint = ("Unary instructions take exactly ONE register operand, "
                "e.g. 'inc r0', 'push r1', 'neg r2'. No comma, no second operand.")
    elif "comma expected" in low:
        hint = ("Operands must be separated by a comma, e.g. 'add r0, r1' or "
                "'ld r0, Data'. Check for a missing or doubled comma.")
    elif "unexpected text" in low:
        hint = ("There is extra text after the end of the instruction. "
                "Comments must start with '#'. Only one instruction per line.")
    elif "label or opcode expected" in low or "illegal opcode" in low:
        hint = ("A line must start with a label (name:), an opcode, or a "
                "directive. Numbers and stray characters cannot start a line.")
    elif "label or number expected" in low:
        hint = ("An address/immediate operand was expected here: a decimal "
                "number (0..255), hex (0xNN), binary (0bNNNNNNNN), a quoted "
                "character ('A') or a defined label.")
    elif "not found" in low:
        m2 = re.search(r"label (\S+) not found", msg, re.I)
        lbl = m2.group(1) if m2 else "?"
        hint = ("Label '%s' is used before it is defined anywhere in this file.\n"
                "Check the spelling, make sure the definition ends with ':' "
                "(internal) or '>' (exported entry), or declare it external "
                "with 'ext %s' if it lives in another module." % (lbl, lbl))
    elif "already defined" in low:
        m2 = re.search(r"label '?([^' ]+)'? already defined", msg, re.I)
        lbl = m2.group(1) if m2 else "?"
        hint = ("Label '%s' occurs more than once. Labels must be unique - "
                "rename one of them." % lbl)
    elif "out of range" in low:
        hint = ("Every CDM8 value fits in ONE byte: decimal 0..255, "
                "hex 0x00..0xFF, binary 0b00000000..0b11111111, "
                "signed -128..127. Split larger constants across two bytes.")
    elif "signed hexadecimal" in low or "signed binary" in low:
        hint = ("You cannot write '-0x..' or '-0b..'. For a negative value use "
                "plain signed decimal (e.g. -5) or its two's-complement form.")
    elif "runaway string" in low:
        hint = "A double-quoted string is missing its closing quote \" ."
    elif "illegal character" in low:
        m2 = re.search(r"illegal character '(.?)'", msg)
        ch = m2.group(1) if m2 else "?"
        hint = ("Character '%s' does not exist in the CDM8 assembler alphabet.\n"
                "CDM8 has no square brackets for indirect addressing - use 'ldc Rs, Rd' "
                "(Rd <- mem[Rs]) or 'stc/st' forms instead of [rN]." % ch)
    elif "illegal separator" in low:
        hint = "Items in a dc/ds list must be separated by commas: dc 1,2,3"
    elif "data expected" in low:
        hint = "'dc' needs at least one value: dc 0x41 or dc \"Hello\""
    elif "number expected" in low:
        hint = ("A numeric value is required here (0..255, 0xNN or 0bNNNNNNNN).")
    elif "numerical address expected" in low:
        hint = "'asect' takes a numeric base address, e.g. 'asect 0x40'."
    elif "'asect' or 'rsect' expected" in low:
        hint = ("Code must be inside a section. Add 'asect 0x00' (or 'rsect name') "
                "before your first instruction.")
    elif "file ends before end of program" in low:
        hint = "The last line of every CDM8 program must be the directive 'end'."
    elif "overlapping asect" in low:
        hint = ("Two 'asect' blocks claim the same memory address, so one "
                "overwrites the other. Move the second block with a different "
                "'asect' address, leaving enough room for the first block's code.")
    elif "memory overflow" in low or "too large" in low:
        hint = ("The program exceeds the 256-byte single page. Use pages "
                "(Paged Memory / Harvard mode) or shorten the program.")
    elif "does not match definition of macro" in low:
        hint = ("The macro was called with the wrong number of arguments - "
                "count the parameters in its 'macro name / N' definition.")
    elif "template" in low:
        hint = ("Template syntax: define fields with 'tplate name', access them "
                "as 'name.field', e.g. 'ldi r0, t.frame' or 'ldsa r0, t.local1'.")
    elif "both ext and entry" in low:
        hint = "A label cannot be declared external (ext) and exported (>) at the same time."
    elif "reserved by assembler" in low:
        hint = "That name is part of the built-in instruction set - choose another macro name."
    elif "unknown escape character" in low:
        hint = "Only \\\\ and \\\" may be escaped inside strings."
    elif "unrecognised architecture" in low:
        hint = "#$arch= must be followed by 'vn' (Von Neumann) or 'hv' (Harvard)."

    if hint:
        head = ("Error on line %d:" % lineno) if lineno else "Error:"
        msg = head + "\n" + msg + "\n— " + hint
    return msg


# ---------------------------------------------------------------------------
#  Autocomplete popup (VS Code style)
# ---------------------------------------------------------------------------

class Cdm8AutoComplete(object):
    """Attaches an autocomplete dropdown to a tk.Text widget.

    Accept keys: Tab, Return (when popup visible), Right/Left arrows commit
    the common prefix like VS Code? (kept simple: Tab/Enter insert, Esc hides)
    """

    MAX_ROWS = 9

    def __init__(self, textwidget, get_labels=None, font=None):
        self.txt = textwidget
        self.get_labels = get_labels or (lambda: [])
        self.popup = None
        self.listbox = None
        self.font = font
        self._words = []
        self._start = None          # tk index where current word begins
        self._active = False
        self._ignore_next_return = False

        self.txt.bind("<KeyRelease>", self._on_keyrelease, add="+")
        self.txt.bind("<Tab>", self._on_tab, add="+")
        self.txt.bind("<<AutocompleteCancel>>", lambda e: self.hide())
        if IS_MAC:
            self.txt.bind("<Option-slash>", self.force_invoke)
        self.txt.bind("<Alt-slash>", self.force_invoke)

    # -- public --------------------------------------------------------------
    def force_invoke(self, event=None):
        """Invoke completion manually (Ctrl+Space equivalent)."""
        return self._invoke(force=True)

    def hide(self, event=None):
        if self.popup is not None:
            try:
                self.popup.destroy()
            except Exception:
                pass
            self.popup = None
            self.listbox = None
        self._active = False
        self._start = None
        return None

    # -- internals -----------------------------------------------------------
    def _word_at_cursor(self):
        idx = self.txt.index("insert")
        line_start = self.txt.index("insert linestart")
        before = self.txt.get(line_start, idx)
        # don't complete inside comments
        cpos = before.find("#")
        if cpos != -1 and (cpos == 0 or before[cpos-1] != "0"):
            pass  # '#' also used in #$ meta; still allow those
        tok = ""
        for ch in reversed(before):
            if ch.isalnum() or ch in "_$":
                tok = ch + tok
            else:
                break
        start = "%s-%dc" % (idx, len(tok)) if tok else idx
        return tok, start

    def _candidates(self, tok, force=False):
        tl = tok.lower()
        if not tl and not force:
            return []
        cands = {}
        # keywords + directives + conditions
        for name, kind, syntax, desc, cat in CDM8_REFERENCE:
            if name.startswith(tl):
                detail = syntax
                cands[name] = (name, detail)
        # registers
        for r in ("r0", "r1", "r2", "r3"):
            if r.startswith(tl):
                cands[r] = (r, "general-purpose register")
        # user labels known to the editor
        try:
            for lbl in self.get_labels():
                if lbl.lower().startswith(tl) and lbl not in cands:
                    cands[lbl] = (lbl, "user label")
        except Exception:
            pass
        res = sorted(cands.values(), key=lambda x: (len(x[0]), x[0]))
        return res

    def _on_keyrelease(self, event):
        if not self._popup_visible():
            # only start completing on word chars
            if event.char and (event.char.isalnum() or event.char in "_$."):
                self._invoke()
            elif event.keysym in ("BackSpace", "Delete"):
                self._invoke()
            return None
        # update live while popup is open
        self._invoke()
        return None

    def _popup_visible(self):
        return self.popup is not None and self.popup.winfo_exists()

    def _invoke(self, force=False):
        if getattr(self.txt, "ames_lock", False):
            return None
        tok, start = self._word_at_cursor()
        cands = self._candidates(tok, force)
        if not cands or (len(cands) == 1 and cands[0][0].lower() == tok.lower()):
            self.hide()
            return None
        self._words = cands
        self._start = start
        self._show_popup()
        return "break" if self._active else None

    def _show_popup(self):
        try:
            bbox = self.txt.bbox("insert")
        except tk.TclError:
            return
        if not bbox:
            return
        x, y, w, h = bbox
        gx = self.txt.winfo_rootx() + x
        gy = self.txt.winfo_rooty() + y + h + 2

        if self.popup is None:
            self.popup = tk.Toplevel(self.txt)
            self.popup.wm_overrideredirect(True)
            frame = tk.Frame(self.popup, bd=1, relief="solid", bg="#1e1e1e")
            frame.pack(fill="both", expand=True)
            self.listbox = tk.Listbox(frame, relief="flat", borderwidth=0,
                                      highlightthickness=0, activestyle="none",
                                      selectbackground="#094771",
                                      selectforeground="white",
                                      background="#252526", foreground="#dcdcdc")
            self.listbox.pack(fill="both", expand=True)
            self.listbox.bind("<Double-Button-1>", self.accept_click)
            self.listbox.bind("<<ListboxSelect>>", lambda e: "break")
        else:
            # keep existing popup, just refresh contents
            pass

        lb = self.listbox
        lb.delete(0, "end")
        maxw = 0
        for name, detail in self._words[:self.MAX_ROWS]:
            item = "  %-14s %s" % (name, detail)
            lb.insert("end", item)
            maxw = max(maxw, len(item))
        try:
            f = self.font or tkfont_measure_fallback(self.txt)
            pw = f.measure("x" * maxw) + 12
        except Exception:
            pw = maxw * 8 + 12
        lh = lb.linesize() * min(len(self._words), self.MAX_ROWS) + 4
        # keep on screen
        sw = self.txt.winfo_screenwidth()
        if gx + pw > sw:
            gx = sw - pw - 4
        self.popup.geometry("+%d+%d" % (gx, gy))
        lb.config(width=max(10, maxw), height=min(len(self._words), self.MAX_ROWS))
        lb.selection_set(0)
        lb.activate(0)
        self._active = True
        self.popup.lift(self.txt)

    def _on_tab(self, event):
        if self._popup_visible():
            self.accept()
            return "break"
        # otherwise let normal tab indenting happen
        return None

    def accept_click(self, event=None):
        sel = self.listbox.curselection()
        if sel:
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(sel[0])
        self.accept()
        return "break"

    def accept(self):
        """Insert the selected completion, replacing the typed prefix."""
        if not self._popup_visible() or not self._words:
            self.hide()
            return "break"
        try:
            sel = self.listbox.curselection()
            idx = sel[0] if sel else 0
            word = self._words[idx][0]
        except Exception:
            self.hide()
            return "break"
        tok, start = self._word_at_cursor()
        try:
            self.txt.edit_separator()
            self.txt.delete(start, "insert")
            self.txt.insert("insert", word)
            self.txt.edit_separator()
        finally:
            self.hide()
        return "break"

    # arrow navigation when popup up - bound from main window
    def handle_nav(self, keysym):
        """Returns True if the event was consumed by the popup."""
        if not self._popup_visible():
            return False
        lb = self.listbox
        cur = lb.curselection()
        i = cur[0] if cur else 0
        n = lb.size()
        if keysym == "Down":
            i = min(i + 1, n - 1)
        elif keysym == "Up":
            i = max(i - 1, 0)
        elif keysym == "Return":
            self.accept()
            return True
        elif keysym == "Escape":
            self.hide()
            return True
        else:
            return False
        lb.selection_clear(0, "end")
        lb.selection_set(i)
        lb.activate(i)
        return True


def tkfont_measure_fallback(widget):
    import tkinter.font as tkfont
    return tkfont.nametofont(widget.cget("font"))


# ---------------------------------------------------------------------------
#  Hover tooltip for the editor (registers, opcodes, labels...)
# ---------------------------------------------------------------------------

class HoverTooltip(object):
    """Shows documentation for the word under the mouse in a Text widget."""

    def __init__(self, textwidget):
        self.txt = textwidget
        self.tw = None
        self.job = None
        self.last_word = None
        self.txt.tag_configure("hover", background="#3a3d41")
        self.txt.bind("<Motion>", self._on_motion, add="+")
        self.txt.bind("<Button-1>", self._hide, add="+")
        self.txt.bind("<Leave>", self._leave, add="+")

    _WORDCHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_$"

    def _word_under(self, event):
        try:
            idx = self.txt.index("@%d,%d" % (event.x, event.y))
        except tk.TclError:
            return None, None
        # expand word boundaries manually
        line, col = idx.split(".")
        line = int(line); col = int(col)
        text = self.txt.get("%d.0" % line, "%d.end" % line)
        if col >= len(text):
            col = max(0, len(text) - 1)
        if not text or text[col] not in self._WORDCHARS:
            return None, None
        s = e = col
        while s > 0 and text[s - 1] in self._WORDCHARS:
            s -= 1
        while e < len(text) - 1 and text[e + 1] in self._WORDCHARS:
            e += 1
        word = text[s:e + 1]
        return word, ("%d.%d" % (line, s), "%d.%d" % (line, e + 1))

    def _on_motion(self, event):
        word, rng = self._word_under(event)
        if rng:
            self.txt.tag_remove("hover", "1.0", "end")
            self.txt.tag_add("hover", rng[0], rng[1])
        else:
            self.txt.tag_remove("hover", "1.0", "end")
        if word != self.last_word:
            self.last_word = word
            self._hide_tip()
            if self.job:
                self.txt.after_cancel(self.job)
            if word:
                self.job = self.txt.after(350, lambda: self._maybe_show(event))
        else:
            # remember position for re-showing
            self._ev = event

    def _leave(self, event=None):
        self.txt.tag_remove("hover", "1.0", "end")
        self._hide_tip()

    def _maybe_show(self, event=None):
        word = self.last_word
        if not word:
            return
        info = self._doc_for(word)
        if not info:
            return
        ev = getattr(self, "_ev", None)
        if ev is None:
            return
        x = self.txt.winfo_rootx() + ev.x + 12
        y = self.txt.winfo_rooty() + ev.y + 16
        self.tw = tk.Toplevel(self.txt)
        self.tw.wm_overrideredirect(True)
        self.tw.geometry("+%d+%d" % (x, y))
        frm = tk.Frame(self.tw, bg="#1e1e1e", bd=1, relief="solid")
        frm.pack()
        title, body = info
        tk.Label(frm, text=title, justify="left", anchor="w",
                 background="#1e1e1e", foreground="#4fc1ff",
                 font=("Menlo", 10, "bold")).pack(fill="x", padx=8, pady=(6, 0))
        tk.Label(frm, text=body, justify="left", anchor="w", wraplength=380,
                 background="#1e1e1e", foreground="#dcdcdc",
                 font=("Menlo", 9)).pack(fill="x", padx=8, pady=(2, 6))
        self.tw.lift()

    def _doc_for(self, word):
        lw = word.lower()
        r = REG_INFO.get(lw)
        if r:
            return (word + "  —  register", r)
        ref = ref_lookup(lw)
        if ref:
            syntax, desc, cat = ref
            return ("%s  —  %s" % (word, cat), syntax + "\n" + desc)
        # condition/meta etc handled above
        return None

    def _hide(self, event=None):
        self._hide_tip()
        return None

    def _hide_tip(self):
        if self.job:
            try:
                self.txt.after_cancel(self.job)
            except Exception:
                pass
            self.job = None
        self.last_word = None
        if self.tw:
            try:
                self.tw.destroy()
            except Exception:
                pass
            self.tw = None


# ---------------------------------------------------------------------------
#  Recent projects store
# ---------------------------------------------------------------------------

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".cocoide")
CONFIG_FILE = os.path.join(CONFIG_DIR, "recent.json")


def _load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_config(cfg):
    try:
        if not os.path.isdir(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


class RecentProjects(object):
    KEY = "projects"
    LIMIT = 12

    @staticmethod
    def all():
        return _load_config().get(RecentProjects.KEY, [])

    @staticmethod
    def add(path):
        if not path:
            return
        path = os.path.abspath(path)
        items = RecentProjects.all()
        if path in items:
            items.remove(path)
        items.insert(0, path)
        cfg = _load_config()
        cfg[RecentProjects.KEY] = items[:RecentProjects.LIMIT]
        _save_config(cfg)

    @staticmethod
    def forget(path):
        cfg = _load_config()
        items = cfg.get(RecentProjects.KEY, [])
        if path in items:
            items.remove(path)
            _save_config(cfg)


def scan_project_files(root, exts=(".asm",)):
    """Return list of (relpath, abspath) for source files in project root."""
    out = []
    if not root or not os.path.isdir(root):
        return out
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in sorted(dirnames)
                       if not d.startswith(".") and d != "__pycache__"]
        for fn in sorted(filenames):
            if fn.startswith("."):
                continue
            if not exts or fn.lower().endswith(tuple(exts)):
                ap = os.path.join(dirpath, fn)
                rp = os.path.relpath(ap, root)
                out.append((rp, ap))
    return out


NEW_TASK_TEMPLATE = """\
# ============================================================
#  Task {n}: <write the task title here>
#  Replace this comment with a summary of the task requirements.
# ============================================================

        asect   0x00            # Program starts at memory address 0
        br      _Start          # Jump over the data area

        asect   0x20
Data:   dc      "Hello!"        #$str
        dc      0               # NULL terminator

        asect   0x40
_Start: ldi     r0, Data        # point r0 at the data
        ldc     r0, r1          # r1 <- first byte
        halt                    # TODO: write your solution here

        asect   0x60
msg:    ds      16              #$str  output buffer

end                             # every program must end with 'end'
"""


def create_task_folder(project_root, task_no):
    """Create <project>/task<N>/task<N>.asm inside the opened project."""
    tdir = os.path.join(project_root, "task%d" % task_no)
    os.makedirs(tdir, exist_ok=True)
    asm_path = os.path.join(tdir, "task%d.asm" % task_no)
    if not os.path.exists(asm_path):
        with open(asm_path, "w") as f:
            f.write(NEW_TASK_TEMPLATE.format(n=task_no))
    return asm_path