import customtkinter as ctk
from utils.arabic import ar


class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("مركز الغزالي للبصريات")
        self.geometry("1200x700")

        # تقسيم الشاشة
        self.grid_columnconfigure(0, weight=1)  # المحتوى
        self.grid_columnconfigure(1, weight=0)  # القائمة (يمين)
        self.grid_rowconfigure(0, weight=1)

        # =========================
        # المحتوى الرئيسي
        # =========================
        self.content_frame = ctk.CTkFrame(self, fg_color="#f5f6fa")
        self.content_frame.grid(row=0, column=0, sticky="nsew")

        # =========================
        # القائمة الجانبية (يمين)
        # =========================
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#2f3640")
        self.sidebar.grid(row=0, column=1, sticky="ns")

        self.build_sidebar()

        # أول شاشة
        self.show_dashboard()

    # =========================
    # بناء القائمة الجانبية
    # =========================
    def build_sidebar(self):

        buttons = [
            ("الرئيسية", self.show_dashboard),
            ("نقطة البيع", self.show_pos),
            ("المخزون", self.show_inventory),
            ("العملاء", self.show_customers),
            ("التقارير", self.show_reports),
            ("الإعدادات", self.show_settings),
        ]

        for text, command in buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                fg_color="transparent",
                hover_color="#353b48",
                anchor="e",
                height=40,
                font=("Cairo", 14, "bold")
            )
            btn.pack(fill="x", pady=5, padx=10)

    # =========================
    # شاشة الداشبورد
    # =========================
    def show_dashboard(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        from modules.dashboard import Dashboard
        Dashboard(self.content_frame)

    # =========================
    # شاشة نقطة البيع
    # =========================
    def show_pos(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        from modules.pos import PosScreen
        PosScreen(self.content_frame)


    def show_inventory(self):

        # مسح أي شاشة مفتوحة
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # استدعاء شاشة المخزون الحقيقية
        from modules.inventory import InventoryScreen

        InventoryScreen(self.content_frame)

    # =========================
    # شاشات مؤقتة (لحد ما نعملها)
    # =========================


    def show_customers(self):
        self._placeholder("شاشة العملاء")

    def show_reports(self):
        self._placeholder("شاشة التقارير")

    def show_settings(self):
        self._placeholder("شاشة الإعدادات")

    # =========================
    # Placeholder مؤقت
    # =========================
    def _placeholder(self, text):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        label = ctk.CTkLabel(
            self.content_frame,
            text=text,
            font=("Cairo", 22, "bold")
        )
        label.pack(expand=True)

    def show_inventory(self):

        from modules.inventory import InventoryScreen

        # مسح الشاشة الحالية
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # فتح شاشة المخزون
        InventoryScreen(self.content_frame)