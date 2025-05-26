import os
import subprocess
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, scrolledtext
import threading


class ASTModuleGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AST Generator")
        self.root.geometry("820x620")
        self.root.resizable(False, False)

        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # Main Frame with padding
        main_frame = tb.Frame(root, padding=15)
        main_frame.pack(fill="both", expand=True)

        # Label + Entry + Browse Button Frame
        file_select_frame = tb.Frame(main_frame)
        file_select_frame.pack(fill="x", pady=(0, 10))

        tb.Label(
            file_select_frame, text="Select a C++ file:", font=("Segoe UI", 11)
        ).pack(anchor="w")

        entry_frame = tb.Frame(file_select_frame)
        entry_frame.pack(fill="x", pady=5)

        self.file_path_var = tb.StringVar()
        self.entry = tb.Entry(
            entry_frame,
            textvariable=self.file_path_var,
            font=("Segoe UI", 10),
            width=70,
        )
        self.entry.pack(side="left", fill="x", expand=True)

        self.browse_button = tb.Button(
            entry_frame, text="Browse", bootstyle="primary", command=self.browse_file
        )
        self.browse_button.pack(side="left", padx=(10, 0))

        # Run Button
        self.run_button = tb.Button(
            main_frame,
            text="Run AST Module",
            bootstyle="success",
            width=25,
            command=self.run_module_thread,
        )
        self.run_button.pack(pady=10)

        # Progress Bar (indeterminate)
        self.progress = tb.Progressbar(main_frame, mode="indeterminate")
        self.progress.pack(fill="x", pady=(0, 10))

        # Output Box (read-only)
        self.output_text = scrolledtext.ScrolledText(
            main_frame, wrap="word", height=25, font=("Consolas", 10), state="disabled"
        )
        self.output_text.pack(fill="both", expand=True)

        # Status Bar at bottom
        self.status_var = tb.StringVar(value="Ready")
        status_bar = tb.Label(
            root, textvariable=self.status_var, relief="sunken", anchor="w", padding=5
        )
        status_bar.pack(fill="x", side="bottom")

    def browse_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("C++ Files", "*.cpp")])
        if file_path:
            self.file_path_var.set(file_path)

    def run_module_thread(self):
        # Run in separate thread to avoid freezing GUI
        threading.Thread(target=self.run_module, daemon=True).start()

    def run_module(self):
        cpp_file = self.file_path_var.get()
        if not os.path.isfile(cpp_file):
            messagebox.showerror("Error", "Invalid C++ file selected.")
            return

        # Disable run button & start progress bar
        self.run_button.config(state="disabled")
        self.progress.start(10)
        self.set_status("Running AST module...")

        try:
            self.clear_output()
            cmds = [
                ["lex", "ast.l"],
                ["yacc", "-d", "ast.y"],
                ["gcc", "y.tab.c", "lex.yy.c"],
            ]

            for cmd in cmds:
                self.append_output(f"Running: {' '.join(cmd)}\n")
                process = subprocess.run(
                    cmd, capture_output=True, text=True, cwd=self.script_dir
                )
                if process.returncode != 0:
                    self.append_output(
                        f"Error running {' '.join(cmd)}:\n{process.stderr}\n"
                    )
                    self.set_status("Error during compilation.")
                    return

            with open(cpp_file, "r") as input_file:
                self.append_output(
                    f"\nExecuting ./a.out with input file {os.path.basename(cpp_file)}...\n"
                )
                final_process = subprocess.run(
                    ["./a.out"],
                    stdin=input_file,
                    capture_output=True,
                    text=True,
                    cwd=self.script_dir,
                )
                self.append_output(final_process.stdout)
                if final_process.stderr:
                    self.append_output(f"\n[stderr]\n{final_process.stderr}")

            self.set_status("Done.")
        except Exception as e:
            self.append_output(f"Exception: {str(e)}\n")
            self.set_status("Exception occurred!")
        finally:
            self.progress.stop()
            self.run_button.config(state="normal")

    def clear_output(self):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.config(state="disabled")

    def append_output(self, text):
        self.output_text.config(state="normal")
        self.output_text.insert("end", text)
        self.output_text.see("end")
        self.output_text.config(state="disabled")

    def set_status(self, text):
        self.status_var.set(text)


if __name__ == "__main__":
    root = tb.Window(themename="superhero")
    app = ASTModuleGUI(root)
    root.mainloop()
