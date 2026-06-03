import customtkinter as ctk
from tkinter import ttk
import sqlite3
import logging
from datetime import datetime
from database.db import connect
from utils.arabic import ar

logger = logging.getLogger(__name__)


class Dashboard:
    def __init__(self, parent, current_user="admin", user_role="admin",
                 on_new_invoice=None, on_return_invoice=None, on_print_report=None):
        """
        current_user: اسم المستخدم الحالي
        user_role: الصلاحية الحالية (admin / cashier)
        on_new_invoice: دالة فتح شاشة فاتورة جديدة الممررة من الملف الرئيسي
        on_return_invoice: دالة فتح شاشة المرتجعات الممررة من الملف الرئيسي
        on_print_report: دالة طباعة تقرير الوردية الممررة من الملف الرئيسي
        """
        self.parent = parent
        self.current_user = current_user
        self.user_role = user_role

        # ربط الروابط الخارجية بالمتغيرات الداخلية للكلاس
        self.on_new_invoice = on_new_invoice
        self.on_return_invoice = on_return_invoice
        self.on_print_report = on_print_report

        self.current_sub_frame = None
        self.build_ui()

    def build_ui(self):
        # الحاوية الرئيسية للشاشة
        self.main_frame = ctk.CTkFrame(self.parent, fg_color="#f8f9fa")
        self.main_frame.pack(fill="both", expand=True)

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # ==========================================
        # 🗂️ 1. القسم العلوي: الكروت الذكية وأزرار التنقل
        # ==========================================
        top_cards_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        top_cards_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        top_cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.card_search = ctk.CTkButton(
            top_cards_frame, text="🔍 محرك الاستعلام الموحد\n(أصناف وعملاء)",
            font=("Arial", 13, "bold"), fg_color="#1abc9c", hover_color="#16a085",
            height=60, corner_radius=10, command=lambda: self.switch_sub_view("search")
        )
        self.card_search.grid(row=0, column=2, padx=8, sticky="ew")

        self.card_orders = ctk.CTkButton(
            top_cards_frame, text="👓 موقف الطلبات الحالي\n(حالات النظارات ومواعيدها)",
            font=("Arial", 13, "bold"), fg_color="#3498db", hover_color="#2980b9",
            height=60, corner_radius=10, command=lambda: self.switch_sub_view("orders")
        )
        self.card_orders.grid(row=0, column=1, padx=8, sticky="ew")

        self.card_debts = ctk.CTkButton(
            top_cards_frame, text="💰 المبالغ المتبقية والديون\n(مواعيد استحقاق المبالغ)",
            font=("Arial", 13, "bold"), fg_color="#e67e22", hover_color="#d35400",
            height=60, corner_radius=10, command=lambda: self.switch_sub_view("debts")
        )
        self.card_debts.grid(row=0, column=0, padx=8, sticky="ew")

        # ==========================================
        # 📺 2. الحاوية الديناميكية الممتدة لأسفل الشاشة
        # ==========================================
        self.container_view = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.container_view.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)

        # فتح الشاشة الرئيسية المودرن (ملخص اليوم الحالي) كعرض افتراضي
        self.switch_sub_view("main_session")

    def switch_sub_view(self, view_name):
        """تنظيف وتبديل العرض السفلي بسلاسة دون تضارب"""
        if self.current_sub_frame:
            self.current_sub_frame.destroy()

        self.current_sub_frame = ctk.CTkFrame(self.container_view, fg_color="transparent")
        self.current_sub_frame.pack(fill="both", expand=True)

        if view_name == "main_session":
            self.show_main_session_view()
        elif view_name == "search":
            self.show_search_view()
        elif view_name == "orders":
            self.show_orders_view()
        elif view_name == "debts":
            self.show_debts_view()

    # =========================================================================
    # ⭐ واجهة ملخص اليوم وجلسة العمل (تصميم الكاشير العصري)
    # =========================================================================
    def show_main_session_view(self):
        self.current_sub_frame.grid_columnconfigure(0, weight=3)  # الطرف الأيسر (الفواتير)
        self.current_sub_frame.grid_columnconfigure(1, weight=1)  # الطرف الأيمن (بيانات الشيفت والاختصارات)
        self.current_sub_frame.grid_rowconfigure(1, weight=1)

        # ---------------------------------------------------
        # 📊 أ. كروت الإحصائيات الخدمية اليومية
        # ---------------------------------------------------
        stats_frame = ctk.CTkFrame(self.current_sub_frame, fg_color="transparent")
        stats_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        sales_today, paid_today, remaining_today, total_invoices = self.get_session_stats()

        # كرت المبيعات
        c1 = ctk.CTkFrame(stats_frame, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e4e6eb")
        c1.grid(row=0, column=3, padx=5, sticky="ew")
        ctk.CTkLabel(c1, text="إجمالي المبيعات اليوم", font=("Arial", 11), text_color="#7f8c8d").pack(pady=(8, 2))
        ctk.CTkLabel(c1, text=f"{sales_today:,.2f} ج", font=("Arial", 14, "bold"), text_color="#2c3e50").pack(
            pady=(0, 8))

        # كرت المدفوع
        c2 = ctk.CTkFrame(stats_frame, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e4e6eb")
        c2.grid(row=0, column=2, padx=5, sticky="ew")
        ctk.CTkLabel(c2, text="إجمالي المدفوع نقداً", font=("Arial", 11), text_color="#7f8c8d").pack(pady=(8, 2))
        ctk.CTkLabel(c2, text=f"{paid_today:,.2f} ج", font=("Arial", 14, "bold"), text_color="#2ecc71").pack(
            pady=(0, 8))

        # كرت المتبقي
        c3 = ctk.CTkFrame(stats_frame, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e4e6eb")
        c3.grid(row=0, column=1, padx=5, sticky="ew")
        ctk.CTkLabel(c3, text="المتبقي للتحصيل", font=("Arial", 11), text_color="#7f8c8d").pack(pady=(8, 2))
        ctk.CTkLabel(c3, text=f"{remaining_today:,.2f} ج", font=("Arial", 14, "bold"), text_color="#e74c3c").pack(
            pady=(0, 8))

        # كرت عدد الفواتير
        c4 = ctk.CTkFrame(stats_frame, fg_color="#ffffff", corner_radius=10, border_width=1, border_color="#e4e6eb")
        c4.grid(row=0, column=0, padx=5, sticky="ew")
        ctk.CTkLabel(c4, text="إجمالي فواتير اليوم", font=("Arial", 11), text_color="#7f8c8d").pack(pady=(8, 2))
        ctk.CTkLabel(c4, text=str(total_invoices), font=("Arial", 14, "bold"), text_color="#3498db").pack(pady=(0, 8))

        # ---------------------------------------------------
        # 📄 ب. جدول الفواتير الكامل اليومي مع شريط التمرير
        # ---------------------------------------------------
        left_box = ctk.CTkFrame(self.current_sub_frame, fg_color="#ffffff", corner_radius=12, border_width=1,
                                border_color="#e4e6eb")
        left_box.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        left_box.grid_rowconfigure(1, weight=1)
        left_box.grid_columnconfigure(0, weight=1)

        title_text = "📄 جميع فواتير المركز اليوم (عرض المدير العام)" if self.user_role == "admin" else "📄 فواتيرك المسجلة خلال وردية اليوم"
        ctk.CTkLabel(left_box, text=title_text, font=("Arial", 13, "bold"), text_color="#2c3e50").grid(row=0, column=0,
                                                                                                       sticky="w",
                                                                                                       padx=15, pady=10)

        table_container = ctk.CTkFrame(left_box, fg_color="transparent")
        table_container.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))

        self.today_inv_table = ttk.Treeview(table_container, columns=("id", "time", "customer", "status", "total"),
                                            show="headings")
        self.today_inv_table.heading("id", text="رقم الفاتورة")
        self.today_inv_table.heading("time", text="الوقت")
        self.today_inv_table.heading("customer", text="اسم العميل")
        self.today_inv_table.heading("status", text="الحالة")
        self.today_inv_table.heading("total", text="الإجمالي")

        self.today_inv_table.column("customer", width=180, anchor="e")
        self.today_inv_table.column("id", width=80, anchor="center")
        self.today_inv_table.column("time", width=80, anchor="center")
        self.today_inv_table.column("status", width=100, anchor="center")
        self.today_inv_table.column("total", width=90, anchor="center")

        session_scroller = ttk.Scrollbar(table_container, orient="vertical", command=self.today_inv_table.yview)
        self.today_inv_table.configure(yscrollcommand=session_scroller.set)

        self.today_inv_table.pack(side="left", fill="both", expand=True)
        session_scroller.pack(side="right", fill="y")

        # ---------------------------------------------------
        # 👤 ج. بيانات الشيفت والاختصارات السريعة (الطرف الأيمن مطابقة للصورة)
        # ---------------------------------------------------
        right_box = ctk.CTkFrame(self.current_sub_frame, fg_color="#ffffff", corner_radius=12, border_width=1,
                                 border_color="#e4e6eb")
        right_box.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        ctk.CTkLabel(right_box, text="💻 بيانات شيفت العمل", font=("Arial", 13, "bold"), text_color="#2c3e50").pack(
            anchor="w", padx=15, pady=10)

        info_frame = ctk.CTkFrame(right_box, fg_color="#f8f9fa", corner_radius=8)
        info_frame.pack(fill="x", padx=15, pady=5)

        user_display = "مدير النظام (Admin)" if self.user_role == "admin" else f"كاشير: {self.current_user}"
        ctk.CTkLabel(info_frame, text=user_display, font=("Arial", 12, "bold"), text_color="#2c3e50").pack(pady=6)
        ctk.CTkLabel(info_frame, text=f"تاريخ اليوم: {datetime.now().strftime('%Y-%m-%d')}", font=("Arial", 11),
                     text_color="#7f8c8d").pack(pady=(0, 6))

        # قسم الاختصارات السريعة (Quick Shortcuts)
        ctk.CTkLabel(right_box, text="⚡ اختصارات سريعة", font=("Arial", 12, "bold"), text_color="#2c3e50").pack(
            anchor="w", padx=15, pady=(15, 5))

        shortcuts_frame = ctk.CTkFrame(right_box, fg_color="transparent")
        shortcuts_frame.pack(fill="x", padx=15, pady=5)

        # زر فاتورة مبيعات جديدة
        btn_new_inv = ctk.CTkButton(
            shortcuts_frame, text="➕ فاتورة مبيعات جديدة",
            font=("Arial", 12, "bold"), fg_color="#2ecc71", hover_color="#27ae60",
            height=35, corner_radius=8, command=self.shortcut_new_invoice
        )
        btn_new_inv.pack(fill="x", pady=4)

        # زر مرتجع مبيعات
        btn_return_inv = ctk.CTkButton(
            shortcuts_frame, text="🔄 عمل إرجاع / مرتجع",
            font=("Arial", 12, "bold"), fg_color="#e74c3c", hover_color="#c0392b",
            height=35, corner_radius=8, command=self.shortcut_return_invoice
        )
        btn_return_inv.pack(fill="x", pady=4)

        # زر طباعة تقرير الجلسة الحالية للشيفت
        btn_print_report = ctk.CTkButton(
            shortcuts_frame, text="🖨️ طباعة تقرير الوردية الحالي",
            font=("Arial", 12, "bold"), fg_color="#9b59b6", hover_color="#8e44ad",
            height=35, corner_radius=8, command=self.shortcut_print_shift_report
        )
        btn_print_report.pack(fill="x", pady=4)

        # زر التحديث
        btn_refresh = ctk.CTkButton(
            right_box, text="🔄 تحديث البيانات الآن",
            font=("Arial", 12, "bold"), fg_color="#34495e", hover_color="#2c3e50",
            height=35, corner_radius=8, command=lambda: self.switch_sub_view("main_session")
        )
        btn_refresh.pack(fill="x", padx=15, pady=(25, 5))

        # ملء الجدول فوراً بالبيانات
        self.load_today_invoices_table()

    # ==========================================
    # 🎯 تشغيل واستدعاء الاختصارات الحقيقية بحماية وأمان
    # ==========================================
    def shortcut_new_invoice(self):
        """استدعاء شاشة المبيعات الفعلية الممررة للكلاس"""
        if self.on_new_invoice:
            self.on_new_invoice()
        else:
            print("تنبيه: دالة فتح الفاتورة الجديدة غير ممررة للـ Dashboard")

    def shortcut_return_invoice(self):
        """استدعاء شاشة المرتجعات الفعلية الممررة للكلاس"""
        if self.on_return_invoice:
            self.on_return_invoice()
        else:
            print("تنبيه: دالة فتح المرتجعات غير ممررة للـ Dashboard")

    def shortcut_print_shift_report(self):
        """استدعاء دالة الطباعة الفعلية الممررة للكلاس"""
        if self.on_print_report:
            self.on_print_report()
        else:
            print("تنبيه: دالة طباعة التقرير غير ممررة للـ Dashboard")

    # ------------------------------------------
    # 🔍 3. شاشة محرك البحث والاستعلام الموحد
    # ------------------------------------------
    def show_search_view(self):
        self.current_sub_frame.grid_columnconfigure(0, weight=1)
        self.current_sub_frame.grid_rowconfigure(2, weight=1)

        lbl = ctk.CTkLabel(self.current_sub_frame, text="🔍 البحث السريع والموحد داخل المركز",
                           font=("Arial", 15, "bold"), text_color="#2c3e50")
        lbl.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(self.current_sub_frame,
                                         placeholder_text="اكتب اسم صنف، كود، أو اسم عميل للتأكد من بياناته...",
                                         justify="right", font=("Arial", 13), height=40)
        self.search_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.global_search)

        t_frame = ctk.CTkFrame(self.current_sub_frame, fg_color="white")
        t_frame.grid(row=2, column=0, sticky="nsew")

        self.table = ttk.Treeview(t_frame, columns=("type", "name", "info1", "info2"), show="headings")
        self.table.heading("type", text="نوع السجل")
        self.table.heading("name", text="الاسم / البيان")
        self.table.heading("info1", text="التفاصيل / الهاتف")
        self.table.heading("info2", text="السعر")
        self.table.column("name", width=250, anchor="e")
        self.table.column("type", width=100, anchor="center")
        self.table.column("info1", width=150, anchor="center")
        self.table.column("info2", width=150, anchor="center")

        scroller = ttk.Scrollbar(t_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scroller.set)
        self.table.pack(side="left", fill="both", expand=True)
        scroller.pack(side="right", fill="y")

    # ------------------------------------------
    # 👓 4. شاشة موقف وحالات تسليمات النظارات
    # ------------------------------------------
    def show_orders_view(self):
        self.current_sub_frame.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(self.current_sub_frame, text="👓 الموقف الحالي لتنفيذ وتسليم النظارات بالمعمل",
                           font=("Arial", 15, "bold"), text_color="#2c3e50")
        lbl.pack(anchor="w", pady=(0, 10))

        filter_frame = ctk.CTkFrame(self.current_sub_frame, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))

        statuses = [
            (ar("تم التسليم في حينه"), "#2ecc71"),
            (ar("جاري تنفيذه"), "#3498db"),
            (ar("جاهز للتسليم"), "#e67e22"),
            (ar("ملغي / معلق"), "#95a5a6")
        ]
        for title, color in statuses:
            btn = ctk.CTkButton(filter_frame, text=title, font=("Arial", 11), fg_color=color, height=30,
                                command=lambda t=title: self.filter_orders_by_status(t))
            btn.pack(side="right", padx=5)

        t_frame = ctk.CTkFrame(self.current_sub_frame, fg_color="white")
        t_frame.pack(fill="both", expand=True)

        self.orders_table = ttk.Treeview(t_frame, columns=("inv_id", "cust_name", "status", "delivery_date"),
                                         show="headings")
        self.orders_table.heading("inv_id", text="رقم الفاتورة")
        self.orders_table.heading("cust_name", text="اسم العميل")
        self.orders_table.heading("status", text="حالة الطلب")
        self.orders_table.heading("delivery_date", text="موعد التسليم")
        self.orders_table.column("cust_name", width=250, anchor="e")
        self.orders_table.column("inv_id", width=80, anchor="center")
        self.orders_table.column("status", width=120, anchor="center")
        self.orders_table.column("delivery_date", width=150, anchor="center")
        self.orders_table.pack(fill="both", expand=True)
        self.load_orders_data()

    # ------------------------------------------
    # 💰 5. شاشة كشف حساب المتبقيات والديون
    # ------------------------------------------
    def show_debts_view(self):
        lbl = ctk.CTkLabel(self.current_sub_frame, text="💰 المبالغ المتبقية على العملاء ومواعيد تحصيلها مع التسليم",
                           font=("Arial", 15, "bold"), text_color="#2c3e50")
        lbl.pack(anchor="w", pady=(0, 10))

        t_frame = ctk.CTkFrame(self.current_sub_frame, fg_color="white")
        t_frame.pack(fill="both", expand=True)

        self.debts_table = ttk.Treeview(t_frame,
                                        columns=("inv_id", "cust_name", "total", "paid", "remaining", "due_date"),
                                        show="headings")
        self.debts_table.heading("inv_id", text="رقم الفاتورة")
        self.debts_table.heading("cust_name", text="اسم العميل")
        self.debts_table.heading("total", text="الإجمالي")
        self.debts_table.heading("paid", text="المدفوع")
        self.debts_table.heading("remaining", text="المتبقي")
        self.debts_table.heading("due_date", text="موعد الاستحقاق")

        self.debts_table.column("cust_name", width=200, anchor="e")
        for col in ["inv_id", "total", "paid", "remaining", "due_date"]:
            self.debts_table.column(col, width=100, anchor="center")
        self.debts_table.pack(fill="both", expand=True)
        self.load_debts_data()

    # =========================================================================
    # 💾 دوال السحب من قاعدة البيانات
    # =========================================================================
    def get_session_stats(self):
        sales = paid = remaining = 0.0
        count = 0
        query = "SELECT total, paid, remain FROM invoices WHERE date(date) = date('now')"
        params = ()
        if self.user_role != "admin":
            query = "SELECT total, paid, remain FROM invoices WHERE date(date) = date('now') AND user_created = ?"
            params = (self.current_user,)

        try:
            with connect() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(query, params)
                except sqlite3.OperationalError:
                    cursor.execute("SELECT total, paid, remain FROM invoices WHERE date(date) = date('now')")
                rows = cursor.fetchall()
                count = len(rows)
                for total, paid_amount, remain_amount in rows:
                    sales += float(total or 0)
                    paid += float(paid_amount or 0)
                    remaining += float(remain_amount or 0)
        except sqlite3.Error:
            logger.exception("Dashboard: failed to load session stats")
        return sales, paid, remaining, count

    def load_today_invoices_table(self):
        for item in self.today_inv_table.get_children():
            self.today_inv_table.delete(item)
        query = "SELECT id, strftime('%H:%M', date), customer_name, status, total FROM invoices WHERE date(date) = date('now') ORDER BY id DESC"
        params = ()
        if self.user_role != "admin":
            query = "SELECT id, strftime('%H:%M', date), customer_name, status, total FROM invoices WHERE date(date) = date('now') AND user_created = ? ORDER BY id DESC"
            params = (self.current_user,)

        try:
            with connect() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(query, params)
                except sqlite3.OperationalError:
                    cursor.execute(
                        "SELECT id, strftime('%H:%M', date), customer_name, status, total FROM invoices WHERE date(date) = date('now') ORDER BY id DESC")
                for row in cursor.fetchall():
                    self.today_inv_table.insert("", "end", values=row)
        except sqlite3.Error:
            logger.exception("Dashboard: failed to load today's invoices")
            demo_data = [
                ("1001", "10:20 ص", "أحمد محمد أحمد", "مدفوعة", "2,500.00"),
                ("1002", "10:20 ص", "سارة علي محمود", "مدفوعة", "3,200.00"),
                ("1003", "09:55 ص", "محمد خالد عبد الله", "جزئية", "1,800.00"),
                ("1004", "09:00 ص", "نورة عبد الله", "مدفوعة", "2,750.00"),
                ("1005", "08:25 ص", "يوسف أحمد حسن", "معلقة", "1,950.00")
            ]
            for row in demo_data:
                self.today_inv_table.insert("", "end", values=row)

    def global_search(self, event=None):
        query = self.search_entry.get().strip()
        for item in self.table.get_children():
            self.table.delete(item)
        if len(query) < 2:
            return

        search_term = f"%{query}%"
        try:
            with connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, sale_price, qty FROM items WHERE name LIKE ? OR code LIKE ? LIMIT 10",
                               (search_term, search_term))
                for row in cursor.fetchall():
                    self.table.insert("", "end", values=("📦 صنف", row[0], f"المتاح: {row[2]}", f"{row[1]:.2f} ج"))

                cursor.execute("SELECT name, phone FROM customers WHERE name LIKE ? OR phone LIKE ? LIMIT 10",
                               (search_term, search_term))
                for row in cursor.fetchall():
                    self.table.insert("", "end", values=("👤 عميل", row[0], row[1], "نشط"))
        except sqlite3.Error:
            logger.exception("Dashboard: failed to perform global search")

    def load_orders_data(self):
        try:
            with connect() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT id, customer_name, status, delivery_date FROM invoices ORDER BY id DESC LIMIT 30")
                except sqlite3.OperationalError:
                    cursor.execute("SELECT id, customer_name, '' AS status, date AS delivery_date FROM invoices ORDER BY id DESC LIMIT 30")
                for row in cursor.fetchall():
                    self.orders_table.insert("", "end", values=row)
        except sqlite3.Error:
            logger.exception("Dashboard: failed to load orders data")
            self.orders_table.insert("", "end", values=("1024", "أحمد رأفت محمد", "جاري التنفيذ بالمعمل", "2026-06-02"))

    def filter_orders_by_status(self, status_text):
        for item in self.orders_table.get_children():
            self.orders_table.delete(item)
        try:
            with connect() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT id, customer_name, status, delivery_date FROM invoices WHERE status = ?", (status_text,))
                except sqlite3.OperationalError:
                    cursor.execute("SELECT id, customer_name, ? AS status, date AS delivery_date FROM invoices", (status_text,))
                for row in cursor.fetchall():
                    self.orders_table.insert("", "end", values=row)
        except sqlite3.Error:
            logger.exception("Dashboard: failed to filter orders by status")

    def load_debts_data(self):
        try:
            with connect() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "SELECT id, customer_name, total, paid, remain, delivery_date FROM invoices WHERE remain > 0")
                except sqlite3.OperationalError:
                    cursor.execute(
                        "SELECT id, customer_name, total, paid, remain, date AS delivery_date FROM invoices WHERE remain > 0")
                for row in cursor.fetchall():
                    self.debts_table.insert("", "end", values=row)
        except sqlite3.Error:
            logger.exception("Dashboard: failed to load debts data")
            self.debts_table.insert("", "end", values=("1024", "أحمد رأفت محمد", "1500", "500", "1000", "2026-06-02"))