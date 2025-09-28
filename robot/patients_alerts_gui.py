import tkinter as tk
from tkinter import ttk, messagebox
import requests

BASE_URL = "http://127.0.0.1:8001"


class RoundedFrame(tk.Frame):
    """Custom frame with rounded corners"""
    def __init__(self, parent, radius=10, color="#ffffff", border_color="#e0e0e0", **kwargs):
        super().__init__(parent, **kwargs)
        self.radius = radius
        self.color = color
        self.border_color = border_color

        self.canvas = tk.Canvas(self, highlightthickness=0, bg=color)
        self.canvas.pack(fill="both", expand=True)

        # Inner frame for child widgets
        self.inner = tk.Frame(self.canvas, bg=color)
        self.window_id = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")

        self.bind('<Configure>', self._on_configure)

    def _on_configure(self, event=None):
        """Handle resize events"""
        self.canvas.coords(self.window_id, 0, 0)
        self.canvas.itemconfig(
            self.window_id,
            width=self.canvas.winfo_width(),
            height=self.canvas.winfo_height()
        )
        self._draw_border()

    def _draw_border(self):
        """Draw rounded border"""
        self.canvas.delete("border")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width > 1 and height > 1:
            r = min(self.radius, width // 2, height // 2)
            points = [
                r, 0, width - r, 0, width, r, width, height - r,
                width - r, height, r, height, 0, height - r, 0, r
            ]
            self.canvas.create_polygon(
                points, fill=self.color, outline=self.border_color,
                width=2, tags="border", smooth=True
            )


class PatientAlertsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Medical Triage Alert Management System")
        self.root.configure(bg="#f5f7fa")
        self.root.geometry("900x750")
        
        # Initialize queue
        self.queue = []

        # Color scheme
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'danger': '#e74c3c',
            'success': '#27ae60',
            'background': '#f5f7fa',
            'white': '#ffffff',
            'border': '#95a5a6'
        }

        # Font scheme
        self.fonts = {
            'title': ('Segoe UI', 18, 'bold'),
            'header': ('Segoe UI', 14, 'bold'),
            'body': ('Segoe UI', 11),
            'button': ('Segoe UI', 10, 'bold'),
            'small': ('Segoe UI', 9)
        }

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        """Configure button styles"""
        style = ttk.Style()

        style.configure('Modern.TButton',
                        font=self.fonts['button'],
                        background=self.colors['secondary'],
                        foreground='white',
                        borderwidth=0,
                        padding=(12, 6))
        style.map('Modern.TButton',
                  background=[('active', '#2980b9'), ('pressed', '#21618c')])

        style.configure('Success.TButton',
                        font=self.fonts['button'],
                        background=self.colors['success'],
                        foreground='white',
                        borderwidth=0,
                        padding=(12, 6))
        style.map('Success.TButton',
                  background=[('active', '#229954'), ('pressed', '#1e8449')])

        style.configure('Danger.TButton',
                        font=self.fonts['button'],
                        background=self.colors['danger'],
                        foreground='white',
                        borderwidth=0,
                        padding=(12, 6))
        style.map('Danger.TButton',
                  background=[('active', '#c0392b'), ('pressed', '#a93226')])

    def create_widgets(self):
        """Create all GUI elements"""
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Title Section
        title_container = RoundedFrame(main_container, radius=12,
                                       color=self.colors['white'],
                                       border_color=self.colors['border'])
        title_container.pack(fill="x", pady=(0, 8))

        title_label = tk.Label(title_container.inner,
                               text="Medical Triage Alert Management System",
                               font=self.fonts['title'],
                               fg=self.colors['primary'],
                               bg=self.colors['white'])
        title_label.pack(pady=8)

        # High Priority Alerts
        self.create_alert_section(main_container, "High Priority Alerts",
                                  "high", '#fdf2f2', '#e74c3c', self.colors['danger'])

        # General Alerts
        self.create_alert_section(main_container, "General Alerts",
                                  "general", '#f0f9ff', '#3498db', self.colors['secondary'])

        # Action Buttons
        self.create_button_section(main_container)

        # Alert Details Section
        self.create_details_section(main_container)

    def create_alert_section(self, parent, title, section_type, bg_color, border_color, text_color):
        """Create an alert section (high priority or general)"""
        container = RoundedFrame(parent, radius=12, color=bg_color, border_color=border_color)
        container.pack(fill="x", pady=(0, 8))

        header = tk.Frame(container.inner, bg=bg_color)
        header.pack(fill="x", padx=15, pady=(8, 4))

        label = tk.Label(header, text=title, font=self.fonts['header'],
                         bg=bg_color, fg=text_color)
        label.pack(side="left")

        count_label = tk.Label(header, text="0 alerts", font=self.fonts['small'],
                               bg=bg_color, fg=self.colors['primary'])
        count_label.pack(side="right")

        listbox = tk.Listbox(container.inner, font=self.fonts['body'],
                             bg=self.colors['white'], fg=self.colors['primary'],
                             relief="solid", borderwidth=1, height=5,
                             selectbackground=bg_color, selectforeground=text_color)
        listbox.pack(fill="x", padx=15, pady=(0, 8))

        if section_type == "high":
            self.high_count_label = count_label
            self.high_listbox = listbox
        else:
            self.general_count_label = count_label
            self.general_listbox = listbox

    def create_button_section(self, parent):
        """Create button section"""
        btn_container = RoundedFrame(parent, radius=12,
                                     color=self.colors['white'],
                                     border_color=self.colors['border'])
        btn_container.pack(fill="x", pady=(0, 8))

        btn_frame = tk.Frame(btn_container.inner, bg=self.colors['white'])
        btn_frame.pack(pady=10)

        refresh_btn = ttk.Button(btn_frame, text="Refresh Queue",
                                 style='Modern.TButton', command=self.refresh_queue)
        refresh_btn.pack(side="left", padx=8)

        details_btn = ttk.Button(btn_frame, text="Show Details",
                                 style='Success.TButton', command=self.show_details)
        details_btn.pack(side="left", padx=8)

        clear_btn = ttk.Button(btn_frame, text="Clear All Alerts",
                               style='Danger.TButton', command=self.clear_queue)
        clear_btn.pack(side="left", padx=8)

    def create_details_section(self, parent):
        """Create alert details section"""
        details_container = RoundedFrame(parent, radius=12,
                                         color=self.colors['white'],
                                         border_color=self.colors['border'])
        details_container.pack(fill="both", expand=True)

        header = tk.Label(details_container.inner, text="Alert Details",
                          font=self.fonts['header'], bg=self.colors['white'],
                          fg=self.colors['primary'])
        header.pack(pady=(10, 5))

        text_frame = tk.Frame(details_container.inner, bg=self.colors['white'])
        text_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.alert_text = tk.Text(text_frame, font=self.fonts['body'],
                                  state="disabled", wrap="word", bg='#f8fafc',
                                  fg=self.colors['primary'], relief="solid",
                                  borderwidth=1, padx=10, pady=10)
        self.alert_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, command=self.alert_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.alert_text.config(yscrollcommand=scrollbar.set)

    def refresh_queue(self):
        """Fetch and display alerts from server"""
        try:
            response = requests.get(f"{BASE_URL}/alerts", timeout=2)
            response.raise_for_status()
            data = response.json()
            self.queue = data if data else []
        except Exception:
            # fallback demo data
            self.queue = [
                {"patient_id": "123", "name": "Alice Smith", "priority": "critical", "score": 87, "rationale": "Severe chest pain"},
                {"patient_id": "456", "name": "Bob Jones", "priority": "low", "score": 45, "rationale": "Mild cough"}
            ]

        self.high_listbox.delete(0, tk.END)
        self.general_listbox.delete(0, tk.END)

        high_count = 0
        general_count = 0

        for alert in self.queue:
            patient_id = alert.get('patient_id', 'Unknown')
            name = alert.get('name', 'Unknown Patient')
            priority = alert.get('priority', 'unknown')

            display_text = f"{patient_id} - {name} (Priority: {priority})"

            if str(priority).lower() in ["high", "critical"]:
                self.high_listbox.insert(tk.END, display_text)
                high_count += 1
            else:
                self.general_listbox.insert(tk.END, display_text)
                general_count += 1

        self.high_count_label.config(text=f"{high_count} alerts")
        self.general_count_label.config(text=f"{general_count} alerts")

    def get_selected_alert(self):
        """Get the currently selected alert"""
        if self.high_listbox.curselection():
            idx = self.high_listbox.curselection()[0]
            high_alerts = [a for a in self.queue if str(a.get("priority", "")).lower() in ["high", "critical"]]
            if idx < len(high_alerts):
                return high_alerts[idx]
        elif self.general_listbox.curselection():
            idx = self.general_listbox.curselection()[0]
            general_alerts = [a for a in self.queue if str(a.get("priority", "")).lower() not in ["high", "critical"]]
            if idx < len(general_alerts):
                return general_alerts[idx]
        return None

    def format_alert_details(self, alert):
        """Format alert details for display"""
        lines = []
        for k, v in alert.items():
            if isinstance(v, dict):
                lines.append(f"{k.title()}:")
                for subk, subv in v.items():
                    lines.append(f"  • {subk}: {subv}")
            elif isinstance(v, list):
                lines.append(f"{k.title()}:")
                for item in v:
                    lines.append(f"  • {item}")
            else:
                lines.append(f"{k.title()}: {v}")
        return "\n".join(lines)

    def show_details(self):
        """Show details for selected alert"""
        alert = self.get_selected_alert()
        if not alert:
            messagebox.showwarning("No Selection", "Please select an alert.")
            return
        details = self.format_alert_details(alert)
        self.alert_text.config(state="normal")
        self.alert_text.delete("1.0", tk.END)
        self.alert_text.insert("1.0", details)
        self.alert_text.config(state="disabled")

    def clear_queue(self):
        """Clear all alerts"""
        if not messagebox.askyesno("Confirm", "Are you sure you want to clear all alerts?"):
            return
        try:
            response = requests.post(f"{BASE_URL}/clear", timeout=2)
            response.raise_for_status()
            msg = response.json().get("msg", "All alerts cleared.")
            messagebox.showinfo("Success", msg)
            self.refresh_queue()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear alerts:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PatientAlertsGUI(root)
    # Delay first refresh until after window shows
    root.after(200, app.refresh_queue)
    root.mainloop()
