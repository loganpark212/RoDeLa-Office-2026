import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font as tkfont

APP_NAME = "RoDeLa Office 2026"


def center_window(window, width, height):
    window.update_idletasks()
    screen_w = window.winfo_screenwidth()
    screen_h = window.winfo_screenheight()
    x = (screen_w - width) // 2
    y = (screen_h - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def show_splash(master, on_done):
    splash = tk.Toplevel(master)
    splash.overrideredirect(True)
    splash.configure(bg="#0b1a3a")
    splash.attributes("-topmost", True)

    width, height = 820, 480
    center_window(splash, width, height)

    title = tk.Label(
        splash,
        text="",
        fg="white",
        bg="#0b1a3a",
        font=("Segoe UI", 30, "bold"),
    )
    title.place(relx=0.5, rely=0.40, anchor="center")

    subtitle = tk.Label(
        splash,
        text="Loading RoDeLa Office 2026...",
        fg="#b9c7e6",
        bg="#0b1a3a",
        font=("Segoe UI", 11),
    )
    subtitle.place(relx=0.5, rely=0.50, anchor="center")

    percent_label = tk.Label(
        splash,
        text="0%",
        fg="#b9c7e6",
        bg="#0b1a3a",
        font=("Segoe UI", 10),
    )
    percent_label.place(relx=0.5, rely=0.77, anchor="center")

    bar_bg = tk.Frame(splash, bg="#d7dbe6", width=600, height=20)
    bar_bg.place(relx=0.5, rely=0.84, anchor="center")
    bar_bg.pack_propagate(False)

    bar_fill = tk.Frame(bar_bg, bg="#27c24c", width=0, height=20)
    bar_fill.place(x=0, y=0)

    def animate_text(i=0):
        if not splash.winfo_exists():
            return
        title.config(text=APP_NAME[:i])
        if i < len(APP_NAME):
            splash.after(55, animate_text, i + 1)

    def animate_bar(value=0):
        if not splash.winfo_exists():
            return
        if value <= 100:
            percent_label.config(text=f"{value}%")
            bar_fill.config(width=int(600 * value / 100))
            splash.after(18, animate_bar, value + 1)
        else:
            splash.after(200, finish)

    def finish():
        if splash.winfo_exists():
            splash.destroy()
        on_done()

    animate_text()
    splash.after(200, lambda: animate_bar(0))


class RoDeLaOfficeApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1200x760")
        self.root.minsize(900, 600)
        self.root.configure(bg="#eff3fb")

        self.current_file = None
        self._ignore_modified = False

        self.base_family = "Segoe UI"
        self.base_size = 12

        self.base_font = tkfont.Font(family=self.base_family, size=self.base_size)
        self.bold_font = tkfont.Font(family=self.base_family, size=self.base_size, weight="bold")
        self.italic_font = tkfont.Font(family=self.base_family, size=self.base_size, slant="italic")
        self.bold_italic_font = tkfont.Font(
            family=self.base_family, size=self.base_size, weight="bold", slant="italic"
        )

        self._setup_style()
        self._build_top_header()
        self._build_ribbon()
        self._build_editor()
        self._build_status_bar()
        self._bind_shortcuts()

        self.text.edit_modified(False)
        self.update_title()
        self.set_status("새 문서")

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Ribbon.TNotebook", background="#eff3fb", borderwidth=0)
        style.configure("Ribbon.TNotebook.Tab", padding=(14, 8), background="#dfe7f7")
        style.map(
            "Ribbon.TNotebook.Tab",
            background=[("selected", "#f7f9ff")],
            expand=[("selected", (2, 1, 2, 0))],
        )

        style.configure("RibbonCard.TFrame", background="#f7f9ff")
        style.configure("Status.TLabel", background="#eff3fb", foreground="#334155")
        style.configure("TopTitle.TLabel", background="#eff3fb", foreground="#0f172a")
        style.configure("TopSub.TLabel", background="#eff3fb", foreground="#475569")

    def _build_top_header(self):
        header = tk.Frame(self.root, bg="#eff3fb")
        header.pack(fill="x", padx=14, pady=(12, 6))

        left = tk.Frame(header, bg="#eff3fb")
        left.pack(side="left", anchor="w")

        tk.Label(
            left,
            text=APP_NAME,
            bg="#eff3fb",
            fg="#0f172a",
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")

        tk.Label(
            left,
            text="RoDeLa 문서 편집기",
            bg="#eff3fb",
            fg="#475569",
            font=("Segoe UI", 10),
        ).pack(anchor="w")

    def _build_ribbon(self):
        self.ribbon = ttk.Notebook(self.root, style="Ribbon.TNotebook")
        self.ribbon.pack(fill="x", padx=14, pady=(0, 10))

        self.home_tab = ttk.Frame(self.ribbon, style="RibbonCard.TFrame")
        self.edit_tab = ttk.Frame(self.ribbon, style="RibbonCard.TFrame")
        self.view_tab = ttk.Frame(self.ribbon, style="RibbonCard.TFrame")

        self.ribbon.add(self.home_tab, text="홈")
        self.ribbon.add(self.edit_tab, text="편집")
        self.ribbon.add(self.view_tab, text="보기")

        self._build_home_tab()
        self._build_edit_tab()
        self._build_view_tab()

    def _make_group(self, parent, title):
        outer = tk.Frame(parent, bg="#f7f9ff", bd=1, relief="solid")
        body = tk.Frame(outer, bg="#f7f9ff")
        body.pack(side="top", padx=8, pady=(8, 4))
        label = tk.Label(
            outer,
            text=title,
            bg="#f7f9ff",
            fg="#334155",
            font=("Segoe UI", 9),
        )
        label.pack(side="bottom", pady=(0, 6))
        return outer, body

    def _make_button(self, parent, text, command, width=10, height=1, bold=False):
        font = ("Segoe UI", 10, "bold") if bold else ("Segoe UI", 10)
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            font=font,
            bg="#e8efff",
            fg="#0f172a",
            activebackground="#d3e2ff",
            activeforeground="#0f172a",
            relief="flat",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
        )
        btn.bind("<Enter>", lambda e: btn.config(bg="#dce9ff"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#e8efff"))
        return btn

    def _build_home_tab(self):
        frame = tk.Frame(self.home_tab, bg="#f7f9ff")
        frame.pack(fill="x", padx=10, pady=8)

        file_group, file_body = self._make_group(frame, "파일")
        file_group.pack(side="left", padx=6, pady=4)

        self._make_button(file_body, "새 문서", self.new_file, width=10).grid(row=0, column=0, padx=4, pady=4)
        self._make_button(file_body, "열기", self.open_file, width=10).grid(row=1, column=0, padx=4, pady=4)
        self._make_button(file_body, "저장", self.save_file, width=10).grid(row=2, column=0, padx=4, pady=4)

        clip_group, clip_body = self._make_group(frame, "클립보드")
        clip_group.pack(side="left", padx=6, pady=4)

        self._make_button(clip_body, "붙여넣기", self.paste_text, width=12, height=2, bold=True).grid(
            row=0, column=0, rowspan=2, padx=4, pady=4, sticky="nsew"
        )
        self._make_button(clip_body, "복사", self.copy_text, width=8).grid(row=0, column=1, padx=4, pady=4)
        self._make_button(clip_body, "잘라내기", self.cut_text, width=8).grid(row=1, column=1, padx=4, pady=4)

        font_group, font_body = self._make_group(frame, "글꼴")
        font_group.pack(side="left", padx=6, pady=4)

        self._make_button(font_body, "B", self.toggle_bold, width=4, bold=True).grid(row=0, column=0, padx=3, pady=3)
        self._make_button(font_body, "I", self.toggle_italic, width=4).grid(row=0, column=1, padx=3, pady=3)
        self._make_button(font_body, "A+", self.zoom_in, width=4).grid(row=1, column=0, padx=3, pady=3)
        self._make_button(font_body, "A-", self.zoom_out, width=4).grid(row=1, column=1, padx=3, pady=3)

    def _build_edit_tab(self):
        frame = tk.Frame(self.edit_tab, bg="#f7f9ff")
        frame.pack(fill="x", padx=10, pady=8)

        select_group, select_body = self._make_group(frame, "선택")
        select_group.pack(side="left", padx=6, pady=4)

        self._make_button(select_body, "전체 선택", self.select_all, width=12).grid(row=0, column=0, padx=4, pady=4)
        self._make_button(select_body, "서식 제거", self.clear_formatting, width=12).grid(row=1, column=0, padx=4, pady=4)

        edit_group, edit_body = self._make_group(frame, "편집")
        edit_group.pack(side="left", padx=6, pady=4)

        self._make_button(edit_body, "복사", self.copy_text, width=8).grid(row=0, column=0, padx=4, pady=4)
        self._make_button(edit_body, "붙여넣기", self.paste_text, width=8).grid(row=0, column=1, padx=4, pady=4)
        self._make_button(edit_body, "잘라내기", self.cut_text, width=8).grid(row=1, column=0, padx=4, pady=4)
        self._make_button(edit_body, "새 문서", self.new_file, width=8).grid(row=1, column=1, padx=4, pady=4)

    def _build_view_tab(self):
        frame = tk.Frame(self.view_tab, bg="#f7f9ff")
        frame.pack(fill="x", padx=10, pady=8)

        view_group, view_body = self._make_group(frame, "보기")
        view_group.pack(side="left", padx=6, pady=4)

        self._make_button(view_body, "확대", self.zoom_in, width=8).grid(row=0, column=0, padx=4, pady=4)
        self._make_button(view_body, "축소", self.zoom_out, width=8).grid(row=0, column=1, padx=4, pady=4)
        self._make_button(view_body, "기본", self.reset_zoom, width=8).grid(row=1, column=0, padx=4, pady=4)

    def _build_editor(self):
        editor_frame = tk.Frame(self.root, bg="#eff3fb")
        editor_frame.pack(fill="both", expand=True, padx=14, pady=(0, 10))

        self.text = tk.Text(
            editor_frame,
            wrap="word",
            undo=True,
            autoseparators=True,
            maxundo=-1,
            font=self.base_font,
            bg="white",
            fg="#111827",
            insertbackground="#111827",
            relief="flat",
            padx=16,
            pady=14,
            selectbackground="#cfe3ff",
            selectforeground="#111827",
        )

        scroll = ttk.Scrollbar(editor_frame, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)

        self.text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.text.tag_configure("fmt_bold", font=self.bold_font)
        self.text.tag_configure("fmt_italic", font=self.italic_font)
        self.text.tag_configure("fmt_bold_italic", font=self.bold_italic_font)

        self.text.bind("<<Modified>>", self._on_modified)

    def _build_status_bar(self):
        bottom = tk.Frame(self.root, bg="#eff3fb")
        bottom.pack(fill="x", padx=14, pady=(0, 10))

        self.status = tk.StringVar(value="준비됨")
        self.status_label = ttk.Label(bottom, textvariable=self.status, style="Status.TLabel", anchor="w")
        self.status_label.pack(fill="x")

    def _bind_shortcuts(self):
        self.root.bind_all("<Control-s>", self._shortcut(self.save_file))
        self.root.bind_all("<Control-o>", self._shortcut(self.open_file))
        self.root.bind_all("<Control-n>", self._shortcut(self.new_file))
        self.root.bind_all("<Control-c>", self._shortcut(self.copy_text))
        self.root.bind_all("<Control-v>", self._shortcut(self.paste_text))
        self.root.bind_all("<Control-x>", self._shortcut(self.cut_text))
        self.root.bind_all("<Control-a>", self._shortcut(self.select_all))
        self.root.bind_all("<Control-b>", self._shortcut(self.toggle_bold))
        self.root.bind_all("<Control-i>", self._shortcut(self.toggle_italic))
        self.root.bind_all("<Control-plus>", self._shortcut(self.zoom_in))
        self.root.bind_all("<Control-equal>", self._shortcut(self.zoom_in))
        self.root.bind_all("<Control-minus>", self._shortcut(self.zoom_out))

    def _shortcut(self, func):
        def handler(event=None):
            func()
            return "break"
        return handler

    def set_status(self, message):
        self.status.set(message)

    def update_title(self):
        suffix = " *" if self.text.edit_modified() else ""
        filename = os.path.basename(self.current_file) if self.current_file else "새 문서"
        self.root.title(f"{APP_NAME} - {filename}{suffix}")

    def _on_modified(self, event=None):
        if self._ignore_modified:
            return
        self.update_title()
        self._update_cursor_status()
        self.text.edit_modified(False)

    def _update_cursor_status(self):
        try:
            line, col = self.text.index("insert").split(".")
            self.set_status(f"줄 {line}, 칸 {int(col) + 1}")
        except Exception:
            pass

    def _confirm_discard_changes(self):
        if self.text.edit_modified():
            answer = messagebox.askyesnocancel(
                "저장 확인",
                "저장되지 않은 내용이 있습니다.\n저장하고 계속할까요?",
            )
            if answer is None:
                return False
            if answer:
                return self.save_file()
        return True

    def new_file(self):
        if not self._confirm_discard_changes():
            return
        self._ignore_modified = True
        self.text.delete("1.0", tk.END)
        self.text.edit_modified(False)
        self._ignore_modified = False
        self.current_file = None
        self.update_title()
        self.set_status("새 문서")

    def open_file(self):
        if not self._confirm_discard_changes():
            return

        path = filedialog.askopenfilename(
            title="문서 열기",
            filetypes=[
                ("RoDeLa 문서", "*.rdl"),
                ("텍스트 문서", "*.txt"),
                ("모든 파일", "*.*"),
            ],
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="cp949", errors="replace") as f:
                content = f.read()
        except OSError as e:
            messagebox.showerror("열기 실패", str(e))
            return

        self._ignore_modified = True
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.text.edit_modified(False)
        self._ignore_modified = False

        self.current_file = path
        self.update_title()
        self.set_status(f"열림: {os.path.basename(path)}")

    def save_file(self, event=None):
        if self.current_file is None:
            path = filedialog.asksaveasfilename(
                title="문서 저장",
                defaultextension=".rdl",
                filetypes=[
                    ("RoDeLa 문서", "*.rdl"),
                    ("텍스트 문서", "*.txt"),
                    ("모든 파일", "*.*"),
                ],
            )
            if not path:
                return False
            self.current_file = path

        try:
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", tk.END).rstrip("\n"))
        except OSError as e:
            messagebox.showerror("저장 실패", str(e))
            return False

        self.text.edit_modified(False)
        self.update_title()
        self.set_status(f"저장됨: {os.path.basename(self.current_file)}")
        return True

    def _get_target_range(self):
        try:
            return self.text.index("sel.first"), self.text.index("sel.last")
        except tk.TclError:
            pass

        index = self.text.index("insert")
        line_no, col_no = index.split(".")
        line_start = f"{line_no}.0"
        line_end = f"{line_no}.end"
        line = self.text.get(line_start, line_end)

        if not line.strip():
            return None

        col = int(col_no)
        matches = list(re.finditer(r"\S+", line))
        for m in matches:
            if m.start() <= col < m.end():
                return f"{line_no}.{m.start()}", f"{line_no}.{m.end()}"

        for m in reversed(matches):
            if m.end() <= col:
                return f"{line_no}.{m.start()}", f"{line_no}.{m.end()}"

        return None

    def _style_at(self, index):
        tags = self.text.tag_names(index)
        return {
            "bold": "fmt_bold" in tags or "fmt_bold_italic" in tags,
            "italic": "fmt_italic" in tags or "fmt_bold_italic" in tags,
        }

    def _apply_style_range(self, start, end, bold=False, italic=False):
        for tag in ("fmt_bold", "fmt_italic", "fmt_bold_italic"):
            self.text.tag_remove(tag, start, end)

        if bold and italic:
            self.text.tag_add("fmt_bold_italic", start, end)
        elif bold:
            self.text.tag_add("fmt_bold", start, end)
        elif italic:
            self.text.tag_add("fmt_italic", start, end)

    def _toggle_style(self, key):
        target = self._get_target_range()
        if not target:
            self.set_status("서식을 적용할 단어를 선택하거나 커서를 단어 안에 두세요.")
            return

        start, end = target
        current = self._style_at(start)
        current[key] = not current[key]
        self._apply_style_range(start, end, bold=current["bold"], italic=current["italic"])
        self.text.edit_modified(True)
        self.update_title()
        self.set_status("서식 적용됨")

    def toggle_bold(self):
        self._toggle_style("bold")

    def toggle_italic(self):
        self._toggle_style("italic")

    def clear_formatting(self):
        target = self._get_target_range()
        if not target:
            self.set_status("서식을 제거할 단어를 선택하거나 커서를 단어 안에 두세요.")
            return

        start, end = target
        for tag in ("fmt_bold", "fmt_italic", "fmt_bold_italic"):
            self.text.tag_remove(tag, start, end)

        self.text.edit_modified(True)
        self.update_title()
        self.set_status("서식 제거됨")

    def copy_text(self):
        try:
            text = self.text.get("sel.first", "sel.last")
        except tk.TclError:
            target = self._get_target_range()
            if not target:
                self.set_status("복사할 내용이 없습니다.")
                return
            text = self.text.get(*target)

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.set_status("복사됨")

    def cut_text(self):
        try:
            text = self.text.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.text.delete("sel.first", "sel.last")
            self.text.edit_modified(True)
            self.update_title()
            self.set_status("잘라내기 완료")
        except tk.TclError:
            self.set_status("잘라낼 내용을 선택하세요.")

    def paste_text(self):
        try:
            text = self.root.clipboard_get()
        except tk.TclError:
            self.set_status("클립보드가 비어 있습니다.")
            return

        self.text.insert("insert", text)
        self.text.edit_modified(True)
        self.update_title()
        self.set_status("붙여넣기 완료")

    def select_all(self):
        self.text.tag_add("sel", "1.0", "end-1c")
        self.set_status("전체 선택")

    def _set_font_size(self, size):
        self.base_font.configure(size=size)
        self.bold_font.configure(size=size)
        self.italic_font.configure(size=size)
        self.bold_italic_font.configure(size=size)
        self.set_status(f"글자 크기 {size}px")

    def zoom_in(self):
        size = int(self.base_font.cget("size"))
        if size < 30:
            self._set_font_size(size + 2)

    def zoom_out(self):
        size = int(self.base_font.cget("size"))
        if size > 8:
            self._set_font_size(size - 2)

    def reset_zoom(self):
        self._set_font_size(self.base_size)


def main():
    root = tk.Tk()
    root.withdraw()

    def launch_app():
        app = RoDeLaOfficeApp(root)
        root.deiconify()
        root.lift()
        root.focus_force()

    show_splash(root, launch_app)
    root.mainloop()


if __name__ == "__main__":
    main()
