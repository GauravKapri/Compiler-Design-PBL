import os
import subprocess
import threading
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, scrolledtext


class LexicalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("C++ Lexical Analyzer GUI")
        self.root.geometry("820x620")
        self.root.resizable(False, False)

        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.LEXICAL_CPP = os.path.join(self.BASE_DIR, "lexicalanalyzer.cpp")
        self.EXECUTABLE = os.path.join(self.BASE_DIR, "lexicalanalyzer.out")

        main_frame = tb.Frame(root, padding=15)
        main_frame.pack(fill="both", expand=True)

        self.file_label_var = tb.StringVar(value="No file selected")
        self.file_label = tb.Label(
            main_frame, textvariable=self.file_label_var, font=("Segoe UI", 11)
        )
        self.file_label.pack(pady=(0, 10), anchor="w")

        file_btn_frame = tb.Frame(main_frame)
        file_btn_frame.pack(fill="x", pady=5)

        self.select_button = tb.Button(
            file_btn_frame,
            text="Select C++ File",
            bootstyle="primary",
            command=self.select_file,
        )
        self.select_button.pack(side="left")

        self.run_button = tb.Button(
            file_btn_frame,
            text="Run Lexical Analyzer",
            bootstyle="success",
            state="disabled",
            command=self.run_analyzer_thread,
        )
        self.run_button.pack(side="left", padx=(10, 0))

        self.progress = tb.Progressbar(main_frame, mode="indeterminate")
        self.progress.pack(fill="x", pady=(10, 10))

        self.output_area = scrolledtext.ScrolledText(
            main_frame, wrap="word", height=30, font=("Consolas", 10), state="disabled"
        )
        self.output_area.pack(fill="both", expand=True)

        self.status_var = tb.StringVar(value="Ready")
        status_bar = tb.Label(
            root, textvariable=self.status_var, relief="sunken", anchor="w", padding=5
        )
        status_bar.pack(fill="x", side="bottom")

        self.selected_file = None

        # Compile on startup in a thread to keep UI responsive
        threading.Thread(target=self.compile_cpp, daemon=True).start()

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("C++ Files", "*.cpp")])
        if file_path:
            # Show truncated filename if too long
            display_name = os.path.basename(file_path)
            if len(display_name) > 50:
                display_name = "..." + display_name[-47:]
            self.file_label_var.set(f"Selected: {display_name}")
            self.selected_file = file_path
            self.run_button.config(state="normal")

    def compile_cpp(self):
        if not os.path.exists(self.LEXICAL_CPP):
            messagebox.showerror("Error", f"Missing file: {self.LEXICAL_CPP}")
            self.root.destroy()
            return

        self.set_status("Compiling lexical analyzer...")
        self.progress.start(10)
        compile_cmd = ["g++", "-std=c++11", self.LEXICAL_CPP, "-o", self.EXECUTABLE]

        try:
            subprocess.check_output(compile_cmd, stderr=subprocess.STDOUT)
            self.set_status("Compilation successful. Select a C++ file to analyze.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Compilation Error", e.output.decode())
            self.set_status("Compilation failed. See error above.")
            self.run_button.config(state="disabled")
        finally:
            self.progress.stop()

    def run_analyzer_thread(self):
        threading.Thread(target=self.run_analyzer, daemon=True).start()

    def run_analyzer(self):
        if not self.selected_file:
            return

        self.run_button.config(state="disabled")
        self.set_status("Running lexical analyzer...")
        self.progress.start(10)

        try:
            result = subprocess.check_output(
                [self.EXECUTABLE, self.selected_file], stderr=subprocess.STDOUT
            )
            output = result.decode()
        except subprocess.CalledProcessError as e:
            output = "Runtime Error:\n" + e.output.decode()

        self.append_output(output)
        self.set_status("Done.")
        self.run_button.config(state="normal")
        self.progress.stop()

    def append_output(self, text):
        self.output_area.config(state="normal")
        self.output_area.delete("1.0", "end")
        self.output_area.insert("end", text)
        self.output_area.see("end")
        self.output_area.config(state="disabled")

    def set_status(self, text):
        self.status_var.set(text)


if __name__ == "__main__":
    root = tb.Window(themename="superhero")
    app = LexicalGUI(root)
    root.mainloop()
