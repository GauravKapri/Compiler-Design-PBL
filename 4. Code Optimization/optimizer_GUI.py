import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import threading

from code_optimizer import optimize_code  # Make sure this matches your script name

SCRIPT_DIR = os.path.dirname(__file__)
ICG_PATH = os.path.join(SCRIPT_DIR, "..", "3. ICG", "icg_output.txt")
OPTIMIZED_PATH = os.path.join(SCRIPT_DIR, "optimized_code.txt")
LOG_PATH = os.path.join(SCRIPT_DIR, "optimization_log.txt")


class OptimizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ICG Code Optimizer")
        self.root.geometry("1100x750")
        self.root.minsize(800, 600)

        self.dark_mode = False

        self.setup_style()
        self.create_widgets()
        self.load_input_code()

    def setup_style(self):
        """Configure styles for light/dark mode"""
        self.style = ttk.Style()
        self.default_font = ("Helvetica", 11)
        self.code_font = ("Consolas", 11)

        # Light Theme
        self.light_colors = {
            "bg": "#ffffff",
            "fg": "#000000",
            "tab_bg": "#f0f0f0",
            "button": "#e0e0e0",
            "text_bg": "#ffffff",
            "text_fg": "#000000",
        }

        # Dark Theme
        self.dark_colors = {
            "bg": "#2e2e2e",
            "fg": "#ffffff",
            "tab_bg": "#3a3a3a",
            "button": "#4a4a4a",
            "text_bg": "#1e1e1e",
            "text_fg": "#dcdcdc",
        }

        self.current_colors = self.dark_colors

        self.apply_theme()

    def apply_theme(self):
        """Apply current theme colors"""
        style = self.style
        c = self.current_colors

        style.configure("TFrame", background=c["bg"])
        style.configure(
            "TLabel", foreground=c["fg"], background=c["bg"], font=self.default_font
        )
        style.configure(
            "TButton", background=c["button"], foreground=c["fg"], padding=6, width=20
        )
        style.map("TButton", background=[("active", c["tab_bg"])])
        style.configure(
            "TLabelframe",
            foreground=c["fg"],
            background=c["bg"],
            font=("Helvetica", 12, "bold"),
        )
        style.configure(
            "TNotebook.Tab",
            background=c["tab_bg"],
            foreground=c["fg"],
            padding=(10, 5),
            font=("Helvetica", 11, "bold"),
        )
        style.map("TNotebook.Tab", background=[("selected", c["bg"])])

        self.root.configure(bg=c["bg"])

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.current_colors = self.dark_colors if self.dark_mode else self.light_colors
        self.apply_theme()
        self.update_text_colors()

    def update_text_colors(self):
        c = self.current_colors
        for widget in [self.input_text, self.optimized_tab, self.log_tab]:
            widget.config(
                bg=c["text_bg"], fg=c["text_fg"], insertbackground=c["text_fg"]
            )

    def create_scrollable_text(self, parent):
        frame = ttk.Frame(parent)
        text_widget = tk.Text(
            frame,
            wrap=tk.NONE,
            font=self.code_font,
            undo=True,
            bg=self.current_colors["text_bg"],
            fg=self.current_colors["text_fg"],
            insertbackground=self.current_colors["text_fg"],
        )
        vsb = ttk.Scrollbar(frame, orient="vertical", command=text_widget.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=text_widget.xview)
        text_widget.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        text_widget.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        return frame, text_widget

    def create_widgets(self):
        menu_bar = tk.Menu(self.root)
        options_menu = tk.Menu(menu_bar, tearoff=0)
        options_menu.add_command(
            label="Toggle Dark/Light Mode", command=self.toggle_theme
        )
        menu_bar.add_cascade(label="Options", menu=options_menu)
        self.root.config(menu=menu_bar)

        input_frame = ttk.LabelFrame(self.root, text="ICG Input Code")
        input_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.input_text_frame, self.input_text = self.create_scrollable_text(
            input_frame
        )
        self.input_text_frame.pack(fill="both", expand=True)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        run_btn = ttk.Button(
            button_frame,
            text="⚙️ Run Optimization",
            command=self.run_optimization_in_thread,
        )
        run_btn.pack(side="left", padx=5)

        clear_btn = ttk.Button(
            button_frame, text="🗑 Clear Output", command=self.clear_output
        )
        clear_btn.pack(side="left", padx=5)

        tab_control = ttk.Notebook(self.root)

        self.optimized_frame, self.optimized_tab = self.create_scrollable_text(
            tab_control
        )
        self.log_frame, self.log_tab = self.create_scrollable_text(tab_control)

        tab_control.add(self.optimized_frame, text="🛠 Optimized Code")
        tab_control.add(self.log_frame, text="📝 Optimization Log")
        tab_control.pack(fill="both", expand=True, padx=10, pady=5)

        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_input_code(self):
        try:
            with open(ICG_PATH, "r") as f:
                self.input_text.insert("1.0", f.read())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load input file:\n{e}")

    def run_optimization_in_thread(self):
        threading.Thread(target=self.run_optimization).start()

    def run_optimization(self):
        input_code = self.input_text.get("1.0", tk.END).strip()
        if not input_code:
            messagebox.showwarning("Warning", "Input code is empty.")
            return

        self.status_bar.config(text="Optimizing code...")
        self.root.update_idletasks()

        try:
            optimized_code, log = optimize_code(input_code)

            with open(OPTIMIZED_PATH, "w") as f:
                f.write(optimized_code)
            with open(LOG_PATH, "w") as f:
                f.write("\n".join(log))

            self.root.after(0, self._update_output_tabs, optimized_code, "\n".join(log))
            self.root.after(
                0, lambda: messagebox.showinfo("Success", "Optimization complete!")
            )
        except Exception as e:
            self.root.after(
                0, lambda: messagebox.showerror("Error", f"Optimization failed:\n{e}")
            )
        finally:
            self.root.after(0, lambda: self.status_bar.config(text="Ready"))

    def _update_output_tabs(self, optimized_code, log):
        self.optimized_tab.delete("1.0", tk.END)
        self.optimized_tab.insert("1.0", optimized_code)

        self.log_tab.delete("1.0", tk.END)
        self.log_tab.insert("1.0", log)

    def clear_output(self):
        self.optimized_tab.delete("1.0", tk.END)
        self.log_tab.delete("1.0", tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = OptimizerGUI(root)
    root.mainloop()
