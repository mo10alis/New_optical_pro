import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from utils.arabic import ar

class Dashboard:
    def __init__(self, parent):
        self.parent = parent
        self.build_ui()

    def build_ui(self):

        # =========================
        # عنوان الصفحة
        # =========================
        title = ctk.CTkLabel(
            self.parent,
            text="لوحة التحكم",
            font=("Arial", 24, "bold")
        )
        title.pack(pady=20)

        # =========================
        # الإحصائيات (Boxes)
        # =========================
        stats_frame = ctk.CTkFrame(self.parent)
        stats_frame.pack(pady=10)

        stats = [
            ("المبيعات", "15000 ج", "#1abc9c"),
            ("الطلبات", "120", "#3498db"),
            ("العملاء", "45", "#9b59b6"),
            ("الأرباح", "5000 ج", "#e67e22")
        ]

        for text, value, color in stats:
            box = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=10)
            box.pack(side="right", padx=10)

            ctk.CTkLabel(
                box,
                text=text,
                font=("Arial", 14, "bold"),
                text_color="white"
            ).pack(pady=(10, 0), padx=20)

            ctk.CTkLabel(
                box,
                text=value,
                font=("Arial", 16, "bold"),
                text_color="white"
            ).pack(pady=(0, 10))

        # =========================
        # الجراف
        # =========================
        self.create_chart()

    def create_chart(self):

        # بيانات تجريبية
        days = ["السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء"]
        values = [1000, 1500, 1200, 1800, 2000]

        fig = Figure(figsize=(6, 3), dpi=100)
        ax = fig.add_subplot(111)

        ax.plot(days, values, marker='o')

        ax.set_title("تحليل المبيعات")
        ax.set_ylabel("القيمة")
        ax.set_xlabel("الأيام")

        # عرض الجراف داخل Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)