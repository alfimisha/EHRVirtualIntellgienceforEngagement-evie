import tkinter as tk
from tkinter import ttk, messagebox
import requests

BASE_URL = "http://127.0.0.1:8001"  # Flask server address

class PatientAlertsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Critical Patient Alerts")

        # Queue list
        self.queue_listbox = tk.Listbox(root, width=50, height=15)
        self.queue_listbox.pack(pady=10)

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack()

        refresh_btn = ttk.Button(btn_frame, text="Refresh Queue", command=self.refresh_queue)
        refresh_btn.grid(row=0, column=0, padx=5)

        view_btn = ttk.Button(btn_frame, text="View Alert", command=self.view_alert)
        view_btn.grid(row=0, column=1, padx=5)

        clear_btn = ttk.Button(btn_frame, text="Clear Queue", command=self.clear_queue)
        clear_btn.grid(row=0, column=2, padx=5)

        # Patient info text area
        self.alert_text = tk.Text(root, width=60, height=15, state="disabled")
        self.alert_text.pack(pady=10)

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

        self.queue_listbox.delete(0, tk.END)
        for alert in self.queue:
            display_text = f"{alert['patient_id']} - {alert['name']} (Priority: {alert['priority']})"
            self.queue_listbox.insert(tk.END, display_text)

    def view_alert(self):
        """Show full alert details for selected patient"""
        selection = self.queue_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an alert first.")
            return

        idx = selection[0]
        alert = self.queue[idx]

        # Show patient alert details
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
