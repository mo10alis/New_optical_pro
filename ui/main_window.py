import json
import customtkinter as ctk

from database.db import get_user_by_username, get_permission_keys
from modules.login import LoginScreen
from modules.dashboard import Dashboard
from modules.pos import PosScreen
from modules.customers import CustomersScreen
from modules.inventory import InventoryScreen
from modules.invoices import InvoicesScreen
from modules.purchase_orders import PurchaseOrdersScreen
from modules.reports import ReportsScreen
from modules.returns import ReturnsScreen
from modules.products import ProductsScreen
from modules.movements import MovementsScreen
from modules.suppliers import SupplierScreen
from modules.settings import SettingsScreen
from modules.user_permissions import UserPermissionsScreen


class MainWindow(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("مركز الغزالي للبصريات - ERP SYSTEM")
        self.geometry("1200x700")

        self.current_screen = None
        self.buttons = []
        self.sidebar_visible = True
        self.current_user = "admin"
        self.user_role = "admin"
        self.user_permissions = set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.content_frame = ctk.CTkFrame(self, fg_color="#f4f6f9", corner_radius=0)
        self.content_frame.grid(row=0, column=0, sticky="nsew")

        self.sidebar = ctk.CTkScrollableFrame(
            self,
            width=240,
            fg_color="#0f172a",
            corner_radius=0,
            scrollbar_fg_color="#1e293b",
            scrollbar_button_color="#4f46e5"
        )
        self.sidebar.grid(row=0, column=1, sticky="ns")

        self.load_current_user()
        self.build_sidebar()
        self.build_sidebar_toggle()
        # افتح شاشة تسجيل الدخول أولاً
        self.show_login()
        # تأكد من إغلاق نظيف عند الضغط على زر الإغلاق
        try:
            self.protocol("WM_DELETE_WINDOW", self.on_close)
        except Exception:
            pass

    # ==========================================
    # زر إظهار/إخفاء الشريط الجانبي
    # ==========================================
    def build_sidebar_toggle(self):
        self.toggle_sidebar_btn = ctk.CTkButton(
            self,
            text="إخفاء القائمة  ⬅️",
            fg_color="transparent",
            text_color="#475569",
            hover=False,
            font=("Cairo", 11, "bold"),
            command=self.toggle_sidebar
        )
        self.toggle_sidebar_btn.place(relx=0.98, rely=0.02, anchor="ne")

    # ==========================================
    # مسح المحتوى
    # ==========================================
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.update_idletasks()

    # ==========================================
    # التنقل بين الشاشات
    # ==========================================
    def switch_screen(self, command, name):
        self.clear_content()
        command()

        for btn in self.buttons:
            btn_text = btn.cget("text").split("  ")[0].strip()
            if btn_text == name:
                btn.configure(fg_color="#4f46e5", text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color="#94a3b8")

    # ==========================================
    # بناء القائمة الجانبية
    # ==========================================
    def build_sidebar(self):
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=5, pady=(10, 5))

        ctk.CTkLabel(
            logo_frame,
            text="ERP SYSTEM  🔮",
            font=("Cairo", 18, "bold"),
            text_color="#6366f1"
        ).pack(side="right", padx=5)

        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.pack(fill="x", padx=5, pady=(0, 15))

        ctk.CTkLabel(
            user_frame,
            text=f"{self.current_user} ({self.user_role})  👤",
            font=("Cairo", 11),
            text_color="#94a3b8"
        ).pack(side="right", padx=5)

        menu_structure = [
            (None, [("لوحة التحكم", "📊", self.show_dashboard)]),

            ("المبيعات", [
                ("نقطة البيع", "🛒", self.show_pos),
                ("الفواتير", "🧾", self.show_invoices),
                ("المرتجعات", "🔄", self.show_returns)
            ]),

            ("المخزون", [
                ("الأصناف", "📦", self.show_products),
                ("المخزون", "🏠", self.show_inventory),
                ("أوامر الشراء", "🧾", self.show_purchase_orders),
                ("حركات المخزون", "🔃", self.show_movements)
            ]),

            ("العملاء والموردين", [
                ("العملاء", "👥", self.show_customers),
                ("الموردين", "🤝", self.show_suppliers)
            ]),

            ("التقارير", [
                ("التقارير المالية", "📈", self.show_reports)
            ]),

            ("الإعدادات", [
                ("إعدادات النظام", "⚙️", self.show_settings),
                ("إدارة المستخدمين", "👥", self.show_users_permissions)
            ])
        ]

        permission_map = {
            "لوحة التحكم": "لوحة التحكم",
            "نقطة البيع": "نقطة البيع",
            "الفواتير": "الفواتير",
            "المرتجعات": "المرتجعات",
            "الأصناف": "الأصناف",
            "المخزون": "المخزون",
            "أوامر الشراء": "أوامر الشراء",
            "حركات المخزون": "حركات المخزون",
            "العملاء": "العملاء",
            "الموردين": "الموردين",
            "التقارير المالية": "التقارير",
            "إعدادات النظام": "الإعدادات",
            "إدارة المستخدمين": "إدارة المستخدمين"
        }

        for section_title, buttons in menu_structure:
            visible_buttons = [btn for btn in buttons if self.is_menu_allowed(permission_map.get(btn[0], btn[0]))]
            if not visible_buttons:
                continue

            if section_title:
                ctk.CTkLabel(
                    self.sidebar,
                    text=section_title,
                    font=("Cairo", 11, "bold"),
                    text_color="#475569",
                    anchor="e"
                ).pack(fill="x", padx=10, pady=(10, 2))

            for text, icon, command in visible_buttons:
                btn = ctk.CTkButton(
                    self.sidebar,
                    text=f"{text}  {icon}",
                    command=lambda c=command, t=text: self.switch_screen(c, t),
                    fg_color="transparent",
                    text_color="#94a3b8",
                    hover_color="#1e293b",
                    anchor="e",
                    height=38,
                    corner_radius=8,
                    font=("Cairo", 13, "bold")
                )
                btn.pack(fill="x", pady=2, padx=5)
                self.buttons.append(btn)

        # تم نقل زر التحكم بالشريط الجانبي إلى عنصر مستقل لتظل الوظيفة متاحة عند إخفائه.

    # ==========================================
    # شاشات البرنامج
    # ==========================================
    def show_dashboard(self):
        self.current_screen = Dashboard(
            self.content_frame,
            current_user=self.current_user,
            user_role=self.user_role,
            on_new_invoice=lambda: self.switch_screen(self.show_pos, "نقطة البيع"),
            on_return_invoice=lambda: self.switch_screen(self.show_returns, "المرتجعات"),
            on_print_report=self.print_shift_pdf_report
        )

    def show_pos(self):
        self.current_screen = PosScreen(self.content_frame)

    def show_invoices(self):
        self.current_screen = InvoicesScreen(self.content_frame, current_user=self.current_user, user_permissions=self.user_permissions)

    def show_returns(self):
        self.current_screen = ReturnsScreen(self.content_frame)

    def show_products(self):
        self.current_screen = ProductsScreen(self.content_frame, current_user=self.current_user, user_permissions=self.user_permissions)

    def show_inventory(self):
        self.current_screen = InventoryScreen(self.content_frame)

    def show_purchase_orders(self):
        self.current_screen = PurchaseOrdersScreen(self.content_frame)

    def show_movements(self):
        self.current_screen = MovementsScreen(self.content_frame)

    def show_customers(self):
        self.current_screen = CustomersScreen(self.content_frame, current_user=self.current_user, user_permissions=self.user_permissions)

    def show_suppliers(self):
        self.current_screen = SupplierScreen(self.content_frame)

    def show_reports(self):
        self.current_screen = ReportsScreen(self.content_frame)

    def show_settings(self):
        self.current_screen = SettingsScreen(self.content_frame, current_user=self.current_user, user_permissions=self.user_permissions)

    def show_users_permissions(self):
        if not self.is_menu_allowed("إدارة المستخدمين"):
            self._placeholder("ليس لديك صلاحية لدخول هذه الشاشة")
            return
        self.current_screen = UserPermissionsScreen(self.content_frame)

    # ==========================================
    # شاشة تسجيل الدخول وربط المستخدم
    # ==========================================
    def show_login(self):
        self.clear_content()
        self.current_screen = LoginScreen(self.content_frame, on_success=self.set_logged_in_user)

    def set_logged_in_user(self, username: str):
        self.current_user = username
        self.load_current_user()
        # إعادة بناء الشريط الجانبي لتطبيق صلاحيات المستخدم
        for w in self.sidebar.winfo_children():
            w.destroy()
        self.buttons = []
        self.build_sidebar()
        self.build_sidebar_toggle()
        self.switch_screen(self.show_dashboard, "لوحة التحكم")

    # ==========================================
    # دوال الصلاحيات
    # ==========================================
    def load_current_user(self):
        user_record = get_user_by_username(self.current_user)
        all_permissions = set(get_permission_keys())
        if user_record:
            self.user_role = user_record[3] or self.user_role
            self.user_permissions = set(json.loads(user_record[6] or "[]")) if user_record[6] else set()
            if self.user_role == "مدير":
                self.user_permissions = all_permissions
        else:
            self.user_permissions = all_permissions

    def is_menu_allowed(self, permission_key: str) -> bool:
        return self.user_role == "مدير" or permission_key in self.user_permissions

    # ==========================================
    # دوال فرعية
    # ==========================================
    def print_shift_pdf_report(self):
        username = getattr(self, "logged_in_username", "مدير النظام")
        print(f"طباعة تقرير الوردية للمستخدم: {username}")

    def _placeholder(self, text):
        self.clear_content()
        ctk.CTkLabel(
            self.content_frame,
            text=text,
            text_color="#1e293b",
            font=("Cairo", 20, "bold")
        ).pack(pady=60, fill="x")

    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        if self.sidebar_visible:
            self.sidebar.grid()
            self.toggle_sidebar_btn.configure(text="إخفاء القائمة  ⬅️")
        else:
            self.sidebar.grid_remove()
            self.toggle_sidebar_btn.configure(text="عرض القائمة  ➡️")
            self.toggle_sidebar_btn.place(relx=0.98, rely=0.02, anchor="ne")

    def on_close(self):
        # محاولات إنهاء نظيفة: تدمير النافذة ثم إنهاء العملية
        try:
            for widget in self.winfo_children():
                try:
                    widget.destroy()
                except Exception:
                    pass
            self.update_idletasks()
            self.destroy()
        finally:
            import sys
            try:
                sys.exit(0)
            except SystemExit:
                raise


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
