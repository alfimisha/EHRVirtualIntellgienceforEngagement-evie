import tkinter as tk
from tkinter import ttk, messagebox
import requests

BASE_URL = "http://127.0.0.1:8001"  # Flask server address

class PatientAlertsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Nursing Home Alerts and Severity Tracking")
        self.root.configure(bg="white")

        # --------------------
        # Title banner
        # --------------------
        title_frame = tk.Frame(root, bg="#f8dfff", height=70)
        title_frame.pack(fill="x")

        title_label = tk.Label(
            title_frame,
            text="Nursing Home Alerts and Severity Tracking",
            font=("Helvetica", 20, "bold"),
            fg="#2b2b2b",
            bg="#f8dfff",
            pady=15
        )
        title_label.pack(expand=True)

        # --------------------
        # High Priority Alerts Section
        # --------------------
        high_frame = tk.Frame(root, bg="#f8c5a0", padx=10, pady=10)
        high_frame.pack(fill="x", padx=15, pady=(10, 5))

        high_label = tk.Label(
            high_frame,
            text="⚠️ High Priority Alerts",
            font=("Helvetica", 16, "bold"),
            bg="#f8c5a0",
            fg="black"
        )
        high_label.pack(anchor="w")

        self.high_listbox = tk.Listbox(
            high_frame, width=60, height=8, font=("Helvetica", 12),
            bg="white", fg="black", relief="flat"
        )
        self.high_listbox.pack(pady=5, fill="x")

        # --------------------
        # General Alerts Section
        # --------------------
        general_frame = tk.Frame(root, bg="#b5f5c8", padx=10, pady=10)
        general_frame.pack(fill="x", padx=15, pady=(5, 15))

        general_label = tk.Label(
            general_frame,
            text="ℹ️ General Alerts",
            font=("Helvetica", 16, "bold"),
            bg="#b5f5c8",
            fg="black"
        )
        general_label.pack(anchor="w")

        self.general_listbox = tk.Listbox(
            general_frame, width=60, height=8, font=("Helvetica", 12),
            bg="white", fg="black", relief="flat"
        )
        self.general_listbox.pack(pady=5, fill="x")

        # --------------------
        # Buttons
        # --------------------
        btn_frame = tk.Frame(root, bg="white")
        btn_frame.pack(pady=5)

        style = ttk.Style()
        style.configure("TButton", font=("Helvetica", 11, "bold"), padding=6)

        refresh_btn = ttk.Button(btn_frame, text="🔄 Refresh Queue", command=self.refresh_queue)
        refresh_btn.grid(row=0, column=0, padx=5)

        view_btn = ttk.Button(btn_frame, text="👁 View Selected", command=self.view_alert)
        view_btn.grid(row=0, column=1, padx=5)

        clear_btn = ttk.Button(btn_frame, text="🗑 Clear All", command=self.clear_queue)
        clear_btn.grid(row=0, column=2, padx=5)

        # --------------------
        # Alert details text area
        # --------------------
        self.alert_text = tk.Text(root, width=70, height=12, state="disabled", wrap="word", bg="#f9f9f9")
        self.alert_text.pack(pady=10, padx=10, fill="x")

        self.refresh_queue()

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
            display_text = f"{alert['patient_id']} - {alert['name']} (Priority: {alert['priority']})"
            if str(alert.get("priority", "")).lower() in ["high", "critical"]:
                self.high_listbox.insert(tk.END, display_text)
            else:
                self.general_listbox.insert(tk.END, display_text)

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
