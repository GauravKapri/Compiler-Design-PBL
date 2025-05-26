import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from ttkthemes import ThemedStyle
from program_converter import (
    ProgramConverter,
)


class TACGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("S-Expression to 3-Address Code Converter")
        self.root.geometry("1000x600")

        style = ThemedStyle(root)
        style.set_theme("winxpblue")

        # Configure styles
        style.configure("TButton", padding=6, relief="flat", background="#000000")
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))

        # Create menu bar
        self.create_menu()

        # Notebook tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Input Tab
        self.input_frame = ttk.Frame(self.notebook)
        self.input_text = ScrolledText(
            self.input_frame, wrap=tk.NONE, height=20, font=("Consolas", 11)
        )
        self.input_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.notebook.add(self.input_frame, text="AST Input")

        # TAC Tab
        self.output_frame = ttk.Frame(self.notebook)
        self.output_text = ScrolledText(
            self.output_frame, wrap=tk.NONE, height=20, font=("Consolas", 11)
        )
        self.output_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.notebook.add(self.output_frame, text="3-Address Code")

        # Button frame
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=10)

        self.generate_button = ttk.Button(
            btn_frame, text="Generate TAC", command=self.generate_TAC, width=20
        )
        self.generate_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(
            btn_frame, text="Clear Output", command=self.clear_output, width=15
        )
        self.clear_button.pack(side="left", padx=5)

        # Status bar
        self.status_bar = ttk.Label(root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.load_ast_input()
        self.highlight_syntax()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load AST File...", command=self.load_file_dialog)
        file_menu.add_command(label="Save TAC As...", command=self.save_tac_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

    def load_ast_input(self):
        try:
            script_dir = os.path.dirname(__file__)
            ast_path = os.path.join(script_dir, "..", "2. AST", "ast_output.txt")
            if os.path.exists(ast_path):
                with open(ast_path, "r") as f:
                    content = f.read().strip()
                    self.input_text.insert("1.0", content)
                self.update_status(f"Loaded: {ast_path}")
            else:
                self.input_text.insert("1.0", "; No AST input found.")
                self.update_status("Default AST not found. Ready for manual input.")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading AST: {e}")

    def load_file_dialog(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            try:
                with open(file_path, "r") as f:
                    content = f.read()
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", content)
                self.update_status(f"Loaded custom file: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file: {e}")

    def save_tac_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text Files", "*.txt")]
        )
        if file_path:
            try:
                tac_content = self.output_text.get("1.0", tk.END)
                with open(file_path, "w") as f:
                    f.write(tac_content.strip())
                self.update_status(f"TAC saved to: {file_path}")
                messagebox.showinfo("Success", "TAC successfully saved!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def clear_output(self):
        self.output_text.delete("1.0", tk.END)
        self.update_status("Output cleared.")

    def update_status(self, message):
        self.status_bar.config(text=message)

    def highlight_syntax(self):
        """Basic syntax highlighting for S-expressions"""
        keywords = {"(", ")", "=", "+", "-", "*", "/", "if", "for", "++"}
        tags = {
            "(": "bracket",
            ")": "bracket",
            "=": "assign",
            "+": "op",
            "-": "op",
            "*": "op",
            "/": "op",
            "if": "keyword",
            "for": "keyword",
            "++": "keyword",
        }

        self.input_text.tag_configure("bracket", foreground="blue")
        self.input_text.tag_configure("assign", foreground="purple")
        self.input_text.tag_configure("op", foreground="green")
        self.input_text.tag_configure("keyword", foreground="darkorange")

        def rehighlight(event=None):
            self.input_text.mark_set("matchStart", "1.0")
            self.input_text.mark_set("matchEnd", "1.0")
            self.input_text.mark_set("searchLimit", f"1.0+{1000}c")
            for tag in self.input_text.tag_names():
                self.input_text.tag_remove(tag, "1.0", tk.END)

            for token in tags:
                idx = "1.0"
                while True:
                    idx = self.input_text.search(
                        token, idx, stopindex="searchLimit", regexp=False
                    )
                    if not idx:
                        break
                    end_idx = f"{idx}+{len(token)}c"
                    self.input_text.tag_add(tags[token], idx, end_idx)
                    idx = end_idx

        self.input_text.bind("<KeyRelease>", rehighlight)

    def generate_TAC(self):
        try:
            s_expr = self.input_text.get("1.0", tk.END).strip()
            if not s_expr:
                messagebox.showwarning("Warning", "Input is empty.")
                return

            converter = ProgramConverter()
            tac = converter.convert(s_expr)

            script_dir = os.path.dirname(__file__)
            icg_path = os.path.join(script_dir, "icg_output.txt")
            lines = []

            for instruction in tac:
                op = instruction[0]
                if op == "ASSIGN":
                    line = f"{instruction[3]} = {instruction[1]}"
                elif op in [
                    "ADD",
                    "SUB",
                    "MUL",
                    "DIV",
                    ">",
                    "<",
                    "<=",
                    ">=",
                    "==",
                    "!=",
                ]:
                    symbols = {"ADD": "+", "SUB": "-", "MUL": "*", "DIV": "/"}
                    line = f"{instruction[3]} = {instruction[1]} {symbols.get(op, op)} {instruction[2]}"
                elif op == "IF_FALSE":
                    line = f"ifFalse {instruction[1]} goto {instruction[3]}"
                elif op == "GOTO":
                    line = f"goto {instruction[1]}"
                elif op == "LABEL":
                    line = f"{instruction[1]}:"
                else:
                    line = f"UNHANDLED_INSTRUCTION: {instruction}"
                lines.append(line)

            with open(icg_path, "w") as f:
                f.write("\n".join(lines))

            self.output_text.delete("1.0", tk.END)
            self.output_text.insert("1.0", "\n".join(lines))
            self.notebook.select(self.output_frame)
            self.update_status("TAC generated successfully.")
            messagebox.showinfo("Success", f"TAC written to icg_output.txt")

        except Exception as e:
            self.update_status("Error generating TAC.")
            messagebox.showerror("Error", f"Error generating TAC:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TACGeneratorGUI(root)
    root.mainloop()
