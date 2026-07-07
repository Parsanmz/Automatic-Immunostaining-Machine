import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time

BG        = "#1e1e2e"
PANEL     = "#2a2a3e"
ACCENT    = "#7eb8f7"
SUCCESS   = "#50fa7b"
WARNING   = "#ffb86c"
DANGER    = "#ff5555"
TEXT      = "#cdd6f4"
SUBTEXT   = "#6c7086"
BORDER    = "#44475a"

FONT_TITLE  = ("Helvetica", 15, "bold")
FONT_LABEL  = ("Helvetica", 10)
FONT_SMALL  = ("Helvetica", 9)
FONT_MONO   = ("Courier", 9)
FONT_STATUS = ("Helvetica", 11, "bold")

class ImmunoGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Immunostaining Controller")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.ser = None
        self.running = False
        self.read_thread = None

        self._build_ui()


    def _build_ui(self):
        root = self.root

        title_frame = tk.Frame(root, bg=BG)
        title_frame.pack(fill="x", padx=20, pady=(18, 4))
        tk.Label(title_frame, text="Immunostaining Controller",
                 font=FONT_TITLE, bg=BG, fg=ACCENT).pack(side="left")
        tk.Label(title_frame, text="LadHyX · Ecole Polytechnique",
                 font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(side="right", anchor="s", pady=2)

        sep = tk.Frame(root, bg=BORDER, height=1)
        sep.pack(fill="x", padx=20, pady=4)

        conn_frame = tk.Frame(root, bg=BG)
        conn_frame.pack(fill="x", padx=20, pady=6)

        tk.Label(conn_frame, text="Port:", font=FONT_LABEL,
                 bg=BG, fg=TEXT).pack(side="left")

        self.port_var = tk.StringVar()
        self.port_menu = ttk.Combobox(conn_frame, textvariable=self.port_var,
                                      width=14, font=FONT_SMALL, state="readonly")
        self.port_menu.pack(side="left", padx=(6, 12))
        self._refresh_ports()

        self._btn(conn_frame, "Refresh", self._refresh_ports,
                  color=SUBTEXT).pack(side="left", padx=(0, 12))
        self.connect_btn = self._btn(conn_frame, "Connect",
                                     self._toggle_connection, color=ACCENT)
        self.connect_btn.pack(side="left")

        self.conn_indicator = tk.Label(conn_frame, text="●  Disconnected",
                                       font=FONT_SMALL, bg=BG, fg=DANGER)
        self.conn_indicator.pack(side="left", padx=12)

        sep2 = tk.Frame(root, bg=BORDER, height=1)
        sep2.pack(fill="x", padx=20, pady=4)

        vol_outer = tk.Frame(root, bg=BG)
        vol_outer.pack(fill="x", padx=20, pady=6)
        tk.Label(vol_outer, text="Reagent Volumes  (mL)",
                 font=("Helvetica", 10, "bold"), bg=BG, fg=TEXT).pack(anchor="w", pady=(0, 6))

        vol_grid = tk.Frame(vol_outer, bg=BG)
        vol_grid.pack(fill="x")

        self.vol_vars = {}
        pumps = [
            ("Fixation",          "pump1", "0.60"),
            ("Permeabilization",  "pump3", "0.60"),
            ("Antibody 1",        "pump4", "0.60"),
            ("Antibody 2",        "pump5", "0.60"),
            ("Wash",              "pump2", "0.80"),
        ]

        for i, (label, key, default) in enumerate(pumps):
            col = (i % 3) * 2
            row = i // 3

            tk.Label(vol_grid, text=label, font=FONT_LABEL,
                     bg=BG, fg=TEXT, anchor="w", width=17).grid(
                row=row, column=col, sticky="w", pady=3)

            var = tk.StringVar(value=default)
            self.vol_vars[key] = var
            entry = tk.Entry(vol_grid, textvariable=var, width=7,
                             font=FONT_LABEL, bg=PANEL, fg=TEXT,
                             insertbackground=TEXT,
                             relief="flat", bd=0,
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             highlightcolor=ACCENT)
            entry.grid(row=row, column=col + 1, sticky="w",
                       padx=(4, 24), pady=3)

        wash_row = (len(pumps) // 3) + 1
        tk.Label(vol_grid, text="Wash Cycles", font=FONT_LABEL,
                 bg=BG, fg=TEXT, anchor="w", width=17).grid(
            row=wash_row, column=0, sticky="w", pady=3)
        self.wash_cycles_var = tk.StringVar(value="1")
        tk.Entry(vol_grid, textvariable=self.wash_cycles_var, width=7,
                 font=FONT_LABEL, bg=PANEL, fg=TEXT,
                 insertbackground=TEXT,
                 relief="flat", bd=0,
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 highlightcolor=ACCENT).grid(
            row=wash_row, column=1, sticky="w", padx=(4, 24), pady=3)

        sep_inc = tk.Frame(vol_outer, bg=BORDER, height=1)
        sep_inc.pack(fill="x", pady=(8, 6))
        tk.Label(vol_outer, text="Incubation Times  (seconds)",
                 font=("Helvetica", 10, "bold"), bg=BG, fg=TEXT).pack(anchor="w", pady=(0, 6))

        inc_grid = tk.Frame(vol_outer, bg=BG)
        inc_grid.pack(fill="x")

        self.inc_vars = {}
        incubations = [
            ("After Fixation",         "inc_fix",  "3"),
            ("After Permeabilization", "inc_perm", "3"),
            ("After Antibody 1",       "inc_ab1",  "3"),
            ("After Antibody 2",       "inc_ab2",  "3"),
        ]
        for i, (label, key, default) in enumerate(incubations):
            col = (i % 2) * 2
            row = i // 2
            tk.Label(inc_grid, text=label, font=FONT_LABEL,
                     bg=BG, fg=TEXT, anchor="w", width=22).grid(
                row=row, column=col, sticky="w", pady=3)
            var = tk.StringVar(value=default)
            self.inc_vars[key] = var
            tk.Entry(inc_grid, textvariable=var, width=7,
                     font=FONT_LABEL, bg=PANEL, fg=TEXT,
                     insertbackground=TEXT,
                     relief="flat", bd=0,
                     highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=ACCENT).grid(
                row=row, column=col + 1, sticky="w", padx=(4, 32), pady=3)

        sep3 = tk.Frame(root, bg=BORDER, height=1)
        sep3.pack(fill="x", padx=20, pady=6)

        prog_outer = tk.Frame(root, bg=BG)
        prog_outer.pack(fill="x", padx=20, pady=4)
        tk.Label(prog_outer, text="Sequence Progress",
                 font=("Helvetica", 10, "bold"), bg=BG, fg=TEXT).pack(anchor="w", pady=(0, 6))

        self.step_label = tk.Label(prog_outer, text="—",
                                   font=FONT_STATUS, bg=BG, fg=ACCENT)
        self.step_label.pack(anchor="w")

        self.progress_bar = ttk.Progressbar(prog_outer, length=480,
                                             mode="determinate", maximum=100)
        self.progress_bar.pack(fill="x", pady=6)

        self.countdown_label = tk.Label(prog_outer, text="",
                                        font=FONT_SMALL, bg=BG, fg=SUBTEXT)
        self.countdown_label.pack(anchor="w")

        sep4 = tk.Frame(root, bg=BORDER, height=1)
        sep4.pack(fill="x", padx=20, pady=6)

        ctrl = tk.Frame(root, bg=BG)
        ctrl.pack(fill="x", padx=20, pady=6)

        self.send_btn  = self._btn(ctrl, "Set Volumes",  self._send_volumes,  color=WARNING)
        self.start_btn = self._btn(ctrl, "▶  Start",     self._start_sequence, color=SUCCESS)
        self.stop_btn  = self._btn(ctrl, "■  Stop",      self._stop_sequence,  color=DANGER)

        for btn in (self.send_btn, self.start_btn, self.stop_btn):
            btn.pack(side="left", padx=(0, 10))

        sep5 = tk.Frame(root, bg=BORDER, height=1)
        sep5.pack(fill="x", padx=20, pady=6)

        log_outer = tk.Frame(root, bg=BG)
        log_outer.pack(fill="x", padx=20, pady=(0, 16))
        tk.Label(log_outer, text="Serial Log",
                 font=("Helvetica", 10, "bold"), bg=BG, fg=TEXT).pack(anchor="w", pady=(0, 4))

        log_frame = tk.Frame(log_outer, bg=PANEL,
                             highlightthickness=1, highlightbackground=BORDER)
        log_frame.pack(fill="x")

        self.log_box = tk.Text(log_frame, height=7, width=68,
                               bg=PANEL, fg=TEXT, font=FONT_MONO,
                               relief="flat", bd=0,
                               state="disabled", wrap="word",
                               insertbackground=TEXT)
        scrollbar = tk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)
        self.log_box.pack(side="left", fill="both", expand=True, padx=6, pady=4)
        scrollbar.pack(side="right", fill="y")

        self._set_controls_enabled(False)


    def _btn(self, parent, text, cmd, color=TEXT):
        b = tk.Button(parent, text=text, command=cmd,
                      font=FONT_LABEL, fg=color, bg=PANEL,
                      activeforeground=color, activebackground=BORDER,
                      relief="flat", bd=0, padx=12, pady=6,
                      cursor="hand2",
                      highlightthickness=1,
                      highlightbackground=BORDER)
        return b

    def _refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_menu["values"] = ports
        if ports:
            self.port_var.set(ports[0])

    def _toggle_connection(self):
        if self.ser and self.ser.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port = self.port_var.get()
        if not port:
            messagebox.showerror("Error", "Please select a port.")
            return
        try:
            self.ser = serial.Serial(port, 9600, timeout=1)
            time.sleep(2)  # wait for Arduino reset
            self.conn_indicator.config(text="●  Connected", fg=SUCCESS)
            self.connect_btn.config(text="Disconnect")
            self._log(f"Connected to {port}")
            self._set_controls_enabled(True)
            self.read_thread = threading.Thread(
                target=self._serial_reader, daemon=True)
            self.read_thread.start()
        except Exception as e:
            messagebox.showerror("Connection error", str(e))

    def _disconnect(self):
        if self.ser:
            self.ser.close()
        self.conn_indicator.config(text="●  Disconnected", fg=DANGER)
        self.connect_btn.config(text="Connect")
        self._log("Disconnected.")
        self._set_controls_enabled(False)


    def _serial_reader(self):
        while self.ser and self.ser.is_open:
            try:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                self._log(f"← {line}")

                if line.startswith("STEP:"):
                    # Format: STEP:<label>,<duration_ms>
                    parts = line[5:].split(",")
                    label = parts[0]
                    duration_ms = int(parts[1]) if len(parts) > 1 else 0
                    self.root.after(0, self._start_step_progress,
                                    label, duration_ms)

                elif line == "DONE":
                    self.root.after(0, self._finish_step)

                elif line == "SEQ:start":
                    self.root.after(0, lambda: self.step_label.config(
                        text="Sequence running...", fg=SUCCESS))

                elif line == "SEQ:end":
                    self.root.after(0, self._sequence_finished)

            except Exception:
                break


    def _start_step_progress(self, label, duration_ms):
        self.step_label.config(text=f"▶  {label}", fg=ACCENT)
        self.progress_bar["value"] = 0
        self._step_start  = time.time()
        self._step_duration = duration_ms / 1000.0
        self._animate_progress()

    def _animate_progress(self):
        if not self._step_duration:
            return
        elapsed = time.time() - self._step_start
        pct = min(100, (elapsed / self._step_duration) * 100)
        remaining = max(0, self._step_duration - elapsed)
        self.progress_bar["value"] = pct
        self.countdown_label.config(
            text=f"{remaining:.0f} s remaining")
        if pct < 100:
            self.root.after(500, self._animate_progress)

    def _finish_step(self):
        self.progress_bar["value"] = 100
        self.countdown_label.config(text="Done")

    def _sequence_finished(self):
        self.step_label.config(text="✔  Sequence complete", fg=SUCCESS)
        self.progress_bar["value"] = 100
        self.countdown_label.config(text="")
        self.running = False


    def _send_volumes(self):
        try:
            v = [
                float(self.vol_vars["pump1"].get()),
                float(self.vol_vars["pump3"].get()),
                float(self.vol_vars["pump4"].get()),
                float(self.vol_vars["pump5"].get()),
                float(self.vol_vars["pump2"].get()),
            ]
            cycles = int(self.wash_cycles_var.get())
            if cycles < 1:
                raise ValueError
            pauses = [
                float(self.inc_vars["inc_fix"].get()),
                float(self.inc_vars["inc_perm"].get()),
                float(self.inc_vars["inc_ab1"].get()),
                float(self.inc_vars["inc_ab2"].get()),
            ]
            if any(p < 0 for p in pauses):
                raise ValueError
        except ValueError:
            messagebox.showerror("Error",
                "Volumes and incubation times must be positive numbers, "
                "wash cycles must be a positive integer.")
            return
        cmd = ("VOL:" + ",".join(f"{x:.2f}" for x in v)
               + f",{cycles}"
               + "," + ",".join(f"{p:.1f}" for p in pauses)
               + "\n")
        self._send(cmd)
        self._log(f"→ {cmd.strip()}")

    def _start_sequence(self):
        self._send_volumes()
        time.sleep(0.3)
        self._send("START\n")
        self.running = True
        self.step_label.config(text="Starting...", fg=WARNING)

    def _send(self, cmd):
        if self.ser and self.ser.is_open:
            self.ser.write(cmd.encode("utf-8"))


    def _log(self, msg):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _stop_sequence(self):
        self._send("STOP\n")
        self.running = False
        self.step_label.config(text="■  Stopped", fg=DANGER)
        self.progress_bar["value"] = 0
        self.countdown_label.config(text="")

    def _set_controls_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for btn in (self.send_btn, self.start_btn, self.stop_btn):
            btn.config(state=state)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImmunoGUI(root)
    root.mainloop()
