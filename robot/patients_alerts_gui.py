import tkinter as tk
from tkinter import ttk, messagebox
import requests
import datetime

BASE_URL = "http://127.0.0.1:8001"  # Flask server address

class PatientAlertsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Nursing Home Alerts and Severity Tracking")
        self.root.configure(bg="#f5f7fa")  # subtle gray background
        self.queue = []

        # --------------------
        # Title banner
        # --------------------
        title_frame = tk.Frame(root, bg="#4a90e2", height=70)
        title_frame.pack(fill="x")

        title_label = tk.Label(
            title_frame,
            text="Nursing Home Alerts and Severity Tracking",
            font=("Helvetica", 20, "bold"),
            fg="white",
            bg="#4a90e2",
            pady=15
        )
        title_label.pack(expand=True)

        # --------------------
        # High Priority Alerts Section
        # --------------------
        self.build_alert_section(
            parent=root,
            title="High Priority Alerts",
            bg="#ffe1e1",
            list_attr="high_listbox"
        )

        # --------------------
        # General Alerts Section
        # --------------------
        self.build_alert_section(
            parent=root,
            title="General Alerts",
            bg="#e3f9e5",
            list_attr="general_listbox"
        )

        # --------------------
        # Buttons
        # --------------------
        btn_frame = tk.Frame(root, bg="#f5f7fa")
        btn_frame.pack(pady=5)

        style = ttk.Style()
        style.configure(
            "TButton",
            font=("Helvetica", 11, "bold"),
            padding=6
        )

        refresh_btn = ttk.Button(btn_frame, text="Refresh Queue", command=self.refresh_queue)
        refresh_btn.grid(row=0, column=0, padx=5)

        view_btn = ttk.Button(btn_frame, text="View Selected", command=self.view_alert)
        view_btn.grid(row=0, column=1, padx=5)

        clear_btn = ttk.Button(btn_frame, text="Clear All", command=self.clear_queue)
        clear_btn.grid(row=0, column=2, padx=5)

        # --------------------
        # Alert details text area
        # --------------------
        detail_frame = tk.LabelFrame(root, text=" Alert Details ", font=("Helvetica", 12, "bold"), bg="#f5f7fa")
        detail_frame.pack(fill="both", padx=15, pady=10, expand=True)

        self.alert_text = tk.Text(
            detail_frame,
            width=70,
            height=12,
            state="disabled",
            wrap="word",
            bg="#ffffff",
            relief="flat",
            font=("Helvetica", 11)
        )
        self.alert_text.pack(padx=10, pady=10, fill="both", expand=True)

        # --------------------
        # Status bar
        # --------------------
        self.status_label = tk.Label(
            root, text="Ready", anchor="w",
            font=("Helvetica", 10),
            bg="#dfe6ed", fg="#333"
        )
        self.status_label.pack(fill="x", side="bottom")

        self.refresh_queue()

    def build_alert_section(self, parent, title, bg, list_attr):
        """Helper to build a styled alert section with scrollable listbox."""
        frame = tk.LabelFrame(
            parent, text=title,
            font=("Helvetica", 14, "bold"),
            bg=bg, fg="black", padx=10, pady=10
        )
        frame.pack(fill="x", padx=15, pady=7)

        # Add scrollable listbox
        container = tk.Frame(frame, bg=bg)
        container.pack(fill="x")

        scrollbar = tk.Scrollbar(container, orient="vertical")
        listbox = tk.Listbox(
            container, width=60, height=6,
            font=("Helvetica", 12),
            bg="white", fg="black",
            relief="flat", yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=listbox.yview)
        scrollbar.pack(side="right", fill="y")
        listbox.pack(side="left", fill="both", expand=True)

        setattr(self, list_attr, listbox)

    def refresh_queue(self):
        """Fetch and display alert queue from server"""
        try:
            response = requests.get(f"{BASE_URL}/alerts")
            response.raise_for_status()
            self.queue = response.json()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch queue:\n{e}")
            return

        self.high_listbox.delete(0, tk.END)
        self.general_listbox.delete(0, tk.END)

        for alert in self.queue:
            display_text = f"{alert['patient_id']} - {alert['name']} | Score: {alert.get('score','?')} | Priority: {alert['priority']}"
            if str(alert.get("priority", "")).lower() in ["high", "critical"]:
                self.high_listbox.insert(tk.END, display_text)
            else:
                self.general_listbox.insert(tk.END, display_text)

        self.status_label.config(text=f"Last refreshed at {datetime.datetime.now().strftime('%H:%M:%S')}")

    def view_alert(self):
        """Show full alert details for selected patient"""
        alert = None

        if self.high_listbox.curselection():
            idx = self.high_listbox.curselection()[0]
            alert = [a for a in self.queue if str(a.get("priority", "")).lower() in ["high", "critical"]][idx]
        elif self.general_listbox.curselection():
            idx = self.general_listbox.curselection()[0]
            alert = [a for a in self.queue if str(a.get("priority", "")).lower() not in ["high", "critical"]][idx]
        else:
            messagebox.showwarning("No Selection", "Please select an alert first.")
            return

        self.alert_text.config(state="normal")
        self.alert_text.delete("1.0", tk.END)
        for key, value in alert.items():
            self.alert_text.insert(tk.END, f"{key}: {value}\n")
        self.alert_text.config(state="disabled")

    def clear_queue(self):
        """Clear the queue via server"""
        if not messagebox.askyesno("Confirm", "Are you sure you want to clear the entire queue?"):
            return

        try:
            response = requests.post(f"{BASE_URL}/clear")
            response.raise_for_status()
            msg = response.json().get("msg", "Queue cleared")
            messagebox.showinfo("Success", msg)
            self.refresh_queue()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear queue:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PatientAlertsGUI(root)
    root.mainloop()
