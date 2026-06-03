import customtkinter as ctk
from tkinter import ttk, messagebox
from utils.arabic import ar
from utils.colors import COLORS
import webbrowser
from utils.pdf_utils import generate_invoice_pdf
from utils.whatsapp_utils import send_whatsapp_invoice
from database.db import connect, get_all_items, get_customers
from tkcalendar import DateEntry
from datetime import datetime
import sqlite3
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PosScreen:

    def __init__(self, parent):
        self.parent = parent
        self.final_total = 0
        self.final_after_discount = 0
        self.discount_percent_value = 0
        self.discount_value_calc = 0
        self.invoice_saved = False
        self.saved_invoice_id = None
        self.print_enabled = False

        # تحديث وتأمين هيكل قاعدة البيانات تلقائياً لمنع خطأ تعذر الحفظ
        self.auto_update_database_schema()

        self.build_ui()

    def auto_update_database_schema(self):
        """فحص جدول الفواتير وإضافة الأعمدة الجديدة تلقائياً إذا كانت ناقصة"""
        try:
            with connect() as conn:
                cursor = conn.cursor()

                # جلب أسماء الأعمدة الحالية في جدول invoices
                cursor.execute("PRAGMA table_info(invoices)")
                columns = [col[1] for col in cursor.fetchall()]

                # الأعمدة الجديدة المراد التأكد من وجودها لقفل عملية الحفظ بنجاح
                new_cols = {
                    "status": "TEXT DEFAULT ''",
                    "delivery_date": "TEXT DEFAULT ''",
                    "order_type": "TEXT DEFAULT ''",
                    "payment_method": "TEXT DEFAULT ''",
                    "sph_r": "TEXT DEFAULT ''",
                    "cyl_r": "TEXT DEFAULT ''",
                    "axis_r": "TEXT DEFAULT ''",
                    "sph_l": "TEXT DEFAULT ''",
                    "cyl_l": "TEXT DEFAULT ''",
                    "axis_l": "TEXT DEFAULT ''"
                }

                for col_name, col_type in new_cols.items():
                    if col_name not in columns:
                        cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
                conn.commit()
        except Exception as e:
            print(f"تنبيه تحديث قاعدة البيانات: {e}")

    def build_ui(self):
        # ==========================================
        # الحاوية الرئيسية والسكرول المطور
        # ==========================================
        self.scroll = ctk.CTkScrollableFrame(
            self.parent,
            fg_color=COLORS["bg"]
        )
        self.scroll.pack(fill="both", expand=True, padx=5, pady=5)

        # شريط علوي لزر فاتورة جديدة
        top_action_bar = ctk.CTkFrame(self.scroll, fg_color="transparent")
        top_action_bar.pack(fill="x", padx=15, pady=(5, 0))

        self.new_invoice_btn = ctk.CTkButton(
            top_action_bar,
            text=ar("➕ فاتورة جديدة"),
            font=("Cairo", 12, "bold"),
            fg_color="#00bcd4",
            hover_color="#0097a7",
            width=130,
            command=self.reset_for_new_invoice
        )
        self.new_invoice_btn.pack(side="left")

        # ==========================================
        # 1️⃣ بيانات العميل والطلب
        # ==========================================
        self.card_client = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["card"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"]
        )
        self.card_client.pack(fill="x", padx=15, pady=10, expand=True)

        ctk.CTkLabel(
            self.card_client,
            text=ar("بيانات العميل والطلب"),
            font=("Cairo", 16, "bold"),
            text_color=COLORS["primary"]
        ).pack(anchor="e", padx=15, pady=8)

        grid = ctk.CTkFrame(self.card_client, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=5)

        for i in range(6):
            grid.grid_columnconfigure(i, weight=1)

        self.customers_data = get_customers()

        self.customer_combo = ttk.Combobox(
            grid,
            values=[f"{c[1]} | {c[2]}" for c in self.customers_data],
            width=30,
            justify="right"
        )
        self.customer_combo.set("")
        self.customer_combo.grid(row=0, column=5, padx=5, pady=5)

        self.customer_combo.bind("<KeyRelease>", self.filter_customers)
        self.customer_combo.bind("<<ComboboxSelected>>", self.select_customer)

        self.add_cust_btn = ctk.CTkButton(
            grid,
            text="+ عميل",
            width=80,
            fg_color="#2ecc71",
            command=self.open_quick_customer
        )
        self.add_cust_btn.grid(row=0, column=4, padx=5, pady=5)

        ctk.CTkLabel(grid, text=ar("اسم العميل"), font=("Cairo", 12)).grid(row=0, column=3, sticky="e", padx=5)

        self.name = ctk.CTkEntry(
            grid,
            justify="right",
            font=("Cairo", 12),
            state="readonly"
        )
        self.name.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(grid, text=ar("رقم الهاتف"), font=("Cairo", 12)).grid(row=0, column=1, sticky="e", padx=5)

        self.phone = ctk.CTkEntry(
            grid,
            justify="left",
            font=("Cairo", 12),
            state="readonly"
        )
        self.phone.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        ctk.CTkLabel(grid, text=ar("نوع الطلب"), font=("Cairo", 12)).grid(row=1, column=5, sticky="e", padx=5)

        self.type = ctk.CTkComboBox(
            grid,
            values=[ar(x) for x in ["طبي", "غير طبي"]],
            justify="right",
            command=self.toggle_eye_card_visibility
        )
        self.type.grid(row=1, column=4, padx=5, pady=5, sticky="ew")
        self.type.set(ar("طبي"))

        # ==========================================
        # 2️⃣ فحص النظر والمقاسات
        # ==========================================
        self.eye_card = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"]
        )
        self.eye_card.pack(fill="x", padx=15, pady=4, expand=True)

        ctk.CTkLabel(
            self.eye_card,
            text=ar("مقاسات العدسات (فحص النظر)"),
            font=("Cairo", 14, "bold"),
            text_color=COLORS["primary"]
        ).pack(anchor="e", padx=12, pady=4)

        eye_grid = ctk.CTkFrame(self.eye_card, fg_color="transparent")
        eye_grid.pack(pady=2, fill="x")

        headers = ["SPH", "CYL", "AXIS"]
        for i, h in enumerate(headers):
            ctk.CTkLabel(eye_grid, text=h, font=("Arial", 10, "bold")).grid(row=0, column=i + 1, padx=15)

        ctk.CTkLabel(eye_grid, text=ar("العين اليمنى"), font=("Cairo", 11)).grid(row=1, column=0, padx=10, pady=2)
        ctk.CTkLabel(eye_grid, text=ar("العين اليسرى"), font=("Cairo", 11)).grid(row=2, column=0, padx=10, pady=2)

        self.eye_entries = {}
        for r in range(2):
            for c in range(3):
                e = ctk.CTkEntry(
                    eye_grid,
                    width=65,
                    height=24,
                    justify="center"
                )
                e.grid(row=r + 1, column=c + 1, padx=5, pady=3)
                self.eye_entries[(r, c)] = e

        # ==========================================
        # 3️⃣ سلة المبيعات
        # ==========================================
        self.cart_card = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["card"],
            corner_radius=16,
            border_width=1,
            border_color="#e0e3ea"
        )
        self.cart_card.pack(fill="x", padx=15, pady=6, expand=True)

        ctk.CTkLabel(
            self.cart_card,
            text=ar("سلة المبيعات"),
            font=("Cairo", 16, "bold"),
            text_color=COLORS["primary"]
        ).pack(anchor="e", padx=15, pady=8)

        # حاوية التصفية والتحكم العلوية للسلة
        top_bar = ctk.CTkFrame(self.cart_card, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(top_bar, text=ar("المجموعة:"), font=("Cairo", 12)).pack(side="right", padx=(5, 2))

        self.group_combo = ttk.Combobox(
            top_bar,
            width=15,
            justify="right",
            font=("Cairo", 11)
        )
        self.group_combo.set(ar("الكل"))
        self.group_combo.pack(side="right", padx=5)
        self.group_combo.bind("<<ComboboxSelected>>", self.on_group_selected)

        ctk.CTkLabel(top_bar, text=ar("اختر الصنف:"), font=("Cairo", 12)).pack(side="right", padx=(10, 2))

        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "TCombobox",
            fieldbackground="white",
            background="white",
            foreground="#2f3640",
            padding=5
        )

        self.items_data = get_all_items()

        self.item_combo = ttk.Combobox(
            top_bar,
            width=38,
            justify="right",
            font=("Cairo", 11)
        )
        self.item_combo.set("")
        self.item_combo.pack(side="right", padx=5)
        self.item_combo.bind("<KeyRelease>", self.filter_items)
        self.item_combo.bind("<<ComboboxSelected>>", self.update_preview)

        self.init_filter_data()

        # إصلاح خط السعر والمتاح لعرضه بشكل مفهوم ومرتب تماماً
        self.preview = ctk.CTkLabel(
            top_bar,
            text="السعر: 0  |  المتاح: 0",
            text_color=COLORS["info"],
            font=("Cairo", 12, "bold"),
            justify="right"
        )
        self.preview.pack(side="right", padx=15)

        self.qty = ctk.CTkEntry(top_bar, width=50, justify="center")
        self.qty.insert(0, "1")
        self.qty.pack(side="left", padx=5)

        self.add_item_btn = ctk.CTkButton(
            top_bar,
            text=ar("➕ إضافة"),
            fg_color=COLORS["success"],
            font=("Cairo", 12, "bold"),
            width=80,
            command=self.add_to_cart
        )
        self.add_item_btn.pack(side="left", padx=5)

        # حل نهائي لانضغاط زر مسح السلة بزيادة العرض لـ 140 ليتسع للجميع بارتياح
        self.clear_cart_btn = ctk.CTkButton(
            top_bar,
            text=ar("🗑️ مسح السلة"),
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=("Cairo", 12, "bold"),
            width=140,
            command=self.clear_cart
        )
        self.clear_cart_btn.pack(side="left", padx=5)

        table_frame = ctk.CTkFrame(
            self.cart_card,
            fg_color="white",
            corner_radius=10,
            border_width=1,
            border_color="#e4e6eb"
        )
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # ترتيب الأعمدة: الكود أولاً ثم الصنف ثم السعر
        self.table = ttk.Treeview(
            table_frame,
            columns=("total", "qty", "price", "name", "code"),
            show="headings",
            height=8
        )
        self.table.tag_configure("odd", background="#fafbfc")
        self.table.tag_configure("even", background="white")
        self.table.tag_configure("hover", background="#eef2ff")

        for col, txt in [
            ("code", "الكود"),
            ("name", "الصنف"),
            ("price", "السعر"),
            ("qty", "الكمية"),
            ("total", "الإجمالي")
        ]:
            self.table.heading(col, text=ar(txt))

        self.table.column("code", anchor="e", width=100)
        self.table.column("name", anchor="e", width=180)
        self.table.column("price", anchor="center", width=100)
        self.table.column("qty", anchor="center", width=80)
        self.table.column("total", anchor="center", width=120)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        self.table.bind("<Delete>", self.delete_selected)

        def on_row_hover(event):
            if self.invoice_saved: return
            row = self.table.identify_row(event.y)
            for i, item in enumerate(self.table.get_children()):
                tag = "even" if i % 2 == 0 else "odd"
                self.table.item(item, tags=(tag,))
            if row:
                self.table.item(row, tags=("hover",))

        def on_leave(event):
            for i, item in enumerate(self.table.get_children()):
                tag = "even" if i % 2 == 0 else "odd"
                self.table.item(item, tags=(tag,))

        self.table.bind("<Motion>", on_row_hover)
        self.table.bind("<Leave>", on_leave)

        # ==========================================
        # 4️⃣ قسم الحسابات والدفع السفلي المطور
        # ==========================================
        self.pay_card = ctk.CTkFrame(
            self.scroll,
            fg_color="#ffffff",
            corner_radius=16,
            border_width=1,
            border_color="#e4e6eb",
        )
        self.pay_card.pack(fill="x", padx=15, pady=10, expand=True)

        top_line = ctk.CTkFrame(self.pay_card, height=4, fg_color=COLORS["primary"], corner_radius=5)
        top_line.pack(fill="x", padx=10, pady=(5, 8))

        container = ctk.CTkFrame(self.pay_card, fg_color="transparent")
        container.pack(fill="x", padx=15, pady=10)

        container.grid_columnconfigure(0, weight=3)  # الأزرار اليسارية
        container.grid_columnconfigure(1, weight=5)  # الحقول والمدخلات الوسطى
        container.grid_columnconfigure(2, weight=4)  # الصناديق المالية اليمنى

        left = ctk.CTkFrame(container, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        mid = ctk.CTkFrame(container, fg_color="transparent")
        mid.grid(row=0, column=1, sticky="nsew")

        right = ctk.CTkFrame(container, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e")

        # --- الأزرار (يسار) ---
        self.save_btn = ctk.CTkButton(
            left, text=ar("حفظ الفاتورة"), fg_color=COLORS["primary"],
            hover_color=COLORS["primary"], width=160, height=42, corner_radius=12, font=("Cairo", 12, "bold")
        )
        self.save_btn.configure(command=lambda: [self.press_effect(self.save_btn), self.save_invoice_to_db()])
        self.save_btn.pack(pady=6)

        self.print_btn = ctk.CTkButton(
            left, text=ar("طباعة"), fg_color="#f39c12", hover_color="#e67e22",
            width=160, height=42, corner_radius=12, font=("Cairo", 12, "bold"),
            command=lambda: [self.press_effect(self.print_btn), self.print_guard()]
        )
        self.print_btn.pack(pady=6)

        self.whatsapp_btn = ctk.CTkButton(
            left, text=ar("واتساب"), fg_color="#25D366", hover_color="#1da851",
            corner_radius=12, width=160, height=42, font=("Cairo", 13, "bold"), cursor="hand2"
        )
        self.whatsapp_btn.configure(command=lambda: [self.press_effect(self.whatsapp_btn), self.send_whatsapp_guard()])
        self.whatsapp_btn.pack(pady=6)

        # --- حقول الإدخال والتحكم (منتصف) بتنسيق شبكي متناسق لمنع الفراغات العمودية ---
        inputs_grid = ctk.CTkFrame(mid, fg_color="transparent")
        inputs_grid.pack(expand=True, fill="both", padx=10)
        inputs_grid.grid_columnconfigure(0, weight=1)
        inputs_grid.grid_columnconfigure(1, weight=1)

        # الصف الأول: حالة الطلب وبجانبها تاريخ التسليم المتوقع
        ctk.CTkLabel(inputs_grid, text=ar("حالة الطلب"), font=("Cairo", 11, "bold")).grid(row=0, column=1, sticky="e",
                                                                                          padx=5, pady=2)
        self.status = ctk.CTkComboBox(
            inputs_grid,
            values=[ar(x) for x in ["تم التسليم في حينه", "جاري تنفيذه"]],
            justify="center",
            width=160,
            command=self.toggle_delivery_date_ui
        )
        self.status.set(ar("تم التسليم في حينه"))
        self.status.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

        self.delivery_frame = ctk.CTkFrame(inputs_grid, fg_color="transparent")

        self.delivery_date_label = ctk.CTkLabel(self.delivery_frame, text=ar("تاريخ التسليم المتوقع"),
                                                font=("Cairo", 11, "bold"), text_color=COLORS["primary"])
        self.delivery_date_picker = DateEntry(
            self.delivery_frame,
            width=14,
            background=COLORS["primary"],
            foreground='white',
            borderwidth=2,
            font=("Arial", 10),
            date_pattern='yyyy-mm-dd',
            drop_down_direction='up'
        )

        # الصف الثاني: طريقة الدفع والخصم %
        ctk.CTkLabel(inputs_grid, text=ar("طريقة الدفع"), font=("Cairo", 11, "bold")).grid(row=2, column=1, sticky="e",
                                                                                           padx=5, pady=2)
        self.payment_method = ctk.CTkComboBox(inputs_grid, values=[ar(x) for x in ["كاش", "فيزا", "تحويل"]],
                                              justify="center", width=160)
        self.payment_method.set("كاش")
        self.payment_method.grid(row=3, column=1, padx=5, pady=2, sticky="ew")

        ctk.CTkLabel(inputs_grid, text=ar("الخصم %"), font=("Cairo", 11, "bold")).grid(row=2, column=0, sticky="e",
                                                                                       padx=5, pady=2)
        self.discount = ctk.CTkEntry(inputs_grid, width=160, height=30, justify="center", corner_radius=8)
        self.discount.insert(0, "0")
        self.discount.grid(row=3, column=0, padx=5, pady=2, sticky="ew")

        # الصف الثالث: المدفوع
        ctk.CTkLabel(inputs_grid, text=ar("المدفوع"), font=("Cairo", 11, "bold")).grid(row=4, column=1, sticky="e",
                                                                                       padx=5, pady=2)
        self.paid = ctk.CTkEntry(inputs_grid, width=160, height=30, justify="center", corner_radius=8, border_width=2)
        self.paid.grid(row=5, column=1, padx=5, pady=2, sticky="ew")

        vcmd = (self.parent.register(lambda v: v == "" or all(c.isdigit() or c == '.' for c in v)), "%P")
        self.paid.configure(validate="key", validatecommand=vcmd)
        self.discount.configure(validate="key", validatecommand=vcmd)

        self.paid.bind("<KeyRelease>", lambda e: self.update_remaining())
        self.discount.bind("<KeyRelease>", lambda e: self.update_remaining())

        # --- المخرجات المالية الموسعة الأنيقة (يمين) ---
        total_box = ctk.CTkFrame(right, fg_color="#eef2ff", corner_radius=12, border_width=1, border_color="#c7d2fe",
                                 width=240, height=40)
        total_box.pack_propagate(False)
        total_box.pack(anchor="e", pady=3)
        ctk.CTkLabel(total_box, text=ar("الإجمالي قبل الخصم:"), font=("Cairo", 12, "bold"), text_color="#1e3a8a").pack(
            side="right", padx=10)
        self.total_value = ctk.CTkLabel(total_box, text="0.00", font=("Arial", 14, "bold"),
                                        text_color=COLORS["primary"])
        self.total_value.pack(side="left", padx=12)

        discount_box = ctk.CTkFrame(right, fg_color="#fff8e1", corner_radius=12, border_width=1, border_color="#ffe082",
                                    width=240, height=40)
        discount_box.pack_propagate(False)
        discount_box.pack(anchor="e", pady=3)
        ctk.CTkLabel(discount_box, text=ar("قيمة الخصم:"), font=("Cairo", 12, "bold"), text_color="#78350f").pack(
            side="right", padx=10)
        self.discount_value_label = ctk.CTkLabel(discount_box, text="0.00 (0%)", font=("Arial", 13, "bold"),
                                                 text_color="#d97706")
        self.discount_value_label.pack(side="left", padx=12)

        net_box = ctk.CTkFrame(right, fg_color="#f0fdf4", corner_radius=12, border_width=1, border_color="#bbf7d0",
                               width=240, height=40)
        net_box.pack_propagate(False)
        net_box.pack(anchor="e", pady=3)
        ctk.CTkLabel(net_box, text=ar("الصافي بعد الخصم:"), font=("Cairo", 12, "bold"), text_color="#166534").pack(
            side="right", padx=10)
        self.net_value = ctk.CTkLabel(net_box, text="0.00", font=("Arial", 14, "bold"), text_color="#15803d")
        self.net_value.pack(side="left", padx=12)

        self.remain_box = ctk.CTkFrame(right, fg_color="#fff5f5", corner_radius=12, border_width=1,
                                       border_color="#ffd6d6", width=240, height=40)
        self.remain_box.pack_propagate(False)
        self.remain_box.pack(anchor="e", pady=3)
        ctk.CTkLabel(self.remain_box, text=ar("المتبقي مطلوب:"), font=("Cairo", 12, "bold"), text_color="#991b1b").pack(
            side="right", padx=10)
        self.remain_value = ctk.CTkLabel(self.remain_box, text="0.00", font=("Arial", 14, "bold"), text_color="#dc2626")
        self.remain_value.pack(side="left", padx=12)

    def toggle_eye_card_visibility(self, selected_value):
        if selected_value == ar("طبي"):
            self.eye_card.pack(fill="x", padx=15, pady=4, expand=True, before=self.cart_card)
        else:
            self.eye_card.pack_forget()

    def toggle_delivery_date_ui(self, selected_value):
        if selected_value == ar("جاري تنفيذه"):
            self.delivery_frame.grid(row=1, column=0, padx=5, pady=2, sticky="ew")
            self.delivery_date_label.pack(anchor="e", padx=2)
            self.delivery_date_picker.pack(fill="x", pady=2)
        else:
            self.delivery_date_label.pack_forget()
            self.delivery_date_picker.pack_forget()
            self.delivery_frame.grid_forget()

    def init_filter_data(self):
        if not hasattr(self, "items_data") or not self.items_data:
            return

        groups = {ar("الكل")}
        for item in self.items_data:
            if len(item) > 4 and item[4]:
                groups.add(str(item[4]).strip())
            else:
                if "عدسة" in str(item[1]):
                    groups.add(ar("عدسات طبية"))
                elif "فريم" in str(item[1]) or "نظارة" in str(item[1]):
                    groups.add(ar("نظارات وفريمات"))
                else:
                    groups.add(ar("إكسسوارات وأخرى"))

        self.group_combo["values"] = sorted(list(groups))
        self.group_combo.set(ar("الكل"))
        self.refresh_item_combo_values()

    def refresh_item_combo_values(self, filtered_list=None):
        target_items = filtered_list if filtered_list is not None else self.items_data
        display_values = []

        for item in target_items:
            code = item[0]
            name = item[1]
            price = item[2]
            display_text = f"{name} (كود: {code}) - السعر: {price}"
            display_values.append(display_text)

        self.item_combo["values"] = display_values

    def on_group_selected(self, event=None):
        selected_group = self.group_combo.get().strip()
        self.item_combo.set("")

        if selected_group == ar("الكل"):
            self.refresh_item_combo_values()
            return

        filtered_items = []
        for item in self.items_data:
            item_group = ""
            if len(item) > 4 and item[4]:
                item_group = str(item[4]).strip()
            else:
                if "عدسة" in str(item[1]):
                    item_group = ar("عدسات طبية")
                elif "فريم" in str(item[1]) or "نظارة" in str(item[1]):
                    item_group = ar("نظارات وفريمات")
                else:
                    item_group = ar("إكسسوارات وأخرى")

            if item_group == selected_group:
                filtered_items.append(item)

        self.refresh_item_combo_values(filtered_items)

    def filter_items(self, event=None):
        typed = self.item_combo.get().lower().strip()
        selected_group = self.group_combo.get().strip()

        base_items = []
        for item in self.items_data:
            item_group = ""
            if len(item) > 4 and item[4]:
                item_group = str(item[4]).strip()
            else:
                if "عدسة" in str(item[1]):
                    item_group = ar("عدسات طبية")
                elif "فريم" in str(item[1]) or "نظارة" in str(item[1]):
                    item_group = ar("نظارات وفريمات")
                else:
                    item_group = ar("إكسسوارات وأخرى")

            if selected_group == ar("الكل") or item_group == selected_group:
                base_items.append(item)

        if typed == "":
            self.refresh_item_combo_values(base_items)
            return

        filtered = [
            item for item in base_items
            if typed in str(item[1]).lower() or typed in str(item[0]).lower()
        ]

        self.refresh_item_combo_values(filtered)
        if filtered:
            self.item_combo.event_generate("<Down>")

    def update_preview(self, event=None):
        selected = self.item_combo.get()
        if not selected or "كود:" not in selected:
            return

        try:
            code_part = selected.split("كود:")[1].split(")")[0].strip()
            for item in self.items_data:
                if str(item[0]) == code_part:
                    qty = item[3]
                    price = item[2]
                    # تحسين شكل وعرض النص ليكون مفهوماً تماماً وبدون لخبطة لغوية للرموز والأرقام
                    self.preview.configure(
                        text=f"السعر: {price}  |  المتاح: {qty}"
                    )
                    return
        except:
            pass

    def add_to_cart(self):
        if self.invoice_saved:
            messagebox.showwarning("تنبيه",
                                   "تم حفظ الفاتورة الحالية بالفعل. يرجى الضغط على 'فاتورة جديدة' لإنشاء طلب جديد.")
            return

        selected = self.item_combo.get()
        if not selected or "كود:" not in selected:
            messagebox.showwarning("تنبيه", "اختر الصنف أولاً")
            return

        try:
            qty = int(self.qty.get())
            if qty <= 0: raise ValueError
        except:
            qty = 1

        try:
            selected_code = selected.split("كود:")[1].split(")")[0].strip()
        except:
            messagebox.showerror("خطأ", "فشل التعرف على كود الصنف")
            return

        for index, item in enumerate(self.items_data):
            code = item[0]
            name = item[1]
            stock_qty = item[3]
            price = item[2]

            if str(code) == selected_code:
                if qty > stock_qty:
                    messagebox.showerror("خطأ في الكمية", f"الكمية المطلوبة غير متوفرة! المتاح هو: {stock_qty}")
                    return

                for existing_row in self.table.get_children():
                    row_values = self.table.item(existing_row)["values"]
                    if str(row_values[4]) == str(code):
                        new_qty = int(row_values[1]) + qty
                        if new_qty > stock_qty:
                            messagebox.showerror("خطأ في الكمية", f"مجموع الكمية بالسلة يتجاوز المتاح: {stock_qty}")
                            return

                        new_total = price * new_qty
                        self.table.item(existing_row, values=(f"{new_total:.2f}", new_qty, f"{price:.2f}", name, code))

                        updated_item = list(item)
                        updated_item[3] -= qty
                        self.items_data[index] = tuple(updated_item)

                        self.update_totals()
                        self.update_preview()
                        return

                total = price * qty
                count = len(self.table.get_children())
                tag = "even" if count % 2 == 0 else "odd"

                self.table.insert(
                    "",
                    "end",
                    values=(f"{total:.2f}", qty, f"{price:.2f}", name, code),
                    tags=(tag,)
                )

                updated_item = list(item)
                updated_item[3] -= qty
                self.items_data[index] = tuple(updated_item)

                self.update_totals()
                self.update_preview()
                return

    def delete_selected(self, event=None):
        if self.invoice_saved: return
        selected = self.table.selection()
        if not selected:
            return

        if not messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف الصنف المحدد من السلة؟"):
            return

        for item in selected:
            values = self.table.item(item)["values"]
            qty_returned = int(values[1])
            code_returned = values[4]

            for index, it in enumerate(self.items_data):
                if str(it[0]) == str(code_returned):
                    updated_item = list(it)
                    updated_item[3] += qty_returned
                    self.items_data[index] = tuple(updated_item)
                    break

            self.table.delete(item)

        self.update_totals()
        self.update_preview()

    def clear_cart(self):
        if self.invoice_saved: return
        if not messagebox.askyesno("تأكيد", "هل تريد مسح كافة محتويات السلة؟"):
            return

        for item in self.table.get_children():
            self.table.delete(item)

        from database.db import get_all_items
        self.items_data = get_all_items()
        self.item_combo.set("")
        self.group_combo.set(ar("الكل"))
        self.refresh_item_combo_values()
        self.preview.configure(text="السعر: 0  |  المتاح: 0")

        self.final_total = 0
        self.final_after_discount = 0
        self.discount_percent_value = 0
        self.discount_value_calc = 0

        self.total_value.configure(text="0.00")
        self.net_value.configure(text="0.00")
        self.paid.delete(0, "end")
        self.discount.delete(0, "end")
        self.discount.insert(0, "0")
        self.remain_value.configure(text="0.00")

        self.remain_box.configure(
            fg_color="#fff5f5",
            border_color="#ffd6d6"
        )

    def save_invoice_to_db(self):
        if self.invoice_saved:
            messagebox.showinfo("معلومة", "هذه الفاتورة تم حفظها مسبقاً بنجاح.")
            return

        if len(self.table.get_children()) == 0:
            messagebox.showwarning("تنبيه", "لا يمكن حفظ فاتورة فارغة")
            return

        try:
            # 1. تحديد مجلد الفواتير بالنسبة للمشروع الحالي
            project_root = Path(__file__).resolve().parent.parent
            pdf_folder = project_root / "invoices_pdf"
            pdf_folder.mkdir(parents=True, exist_ok=True)

            # 2. توليد رقم فاتورة فريد مع الثواني
            invoice_number = datetime.now().strftime("%Y%m%d%H%M%S")

            # 3. اسم الملف سيكون دائماً invoice_رقم_الفاتورة.pdf
            pdf_filename = f"invoice_{invoice_number}.pdf"
            pdf_path = str(pdf_folder / pdf_filename)

            # تخزين المسار ليتم استخدامه في قاعدة البيانات
            self.generated_pdf_path = pdf_path

            self.update_totals()

            # استدعاء دالة توليد الـ PDF (تأكد أن دالة generate_invoice_pdf تستقبل هذا المسار وتستخدمه)
            # ملاحظة: تأكد أن دالة توليد الـ PDF الخاصة بك لا تقوم بتغيير المسار مرة أخرى
            generate_invoice_pdf(self)

            try:
                paid_value = float(self.paid.get() or 0)
            except:
                paid_value = 0

            try:
                discount_value = float(self.discount.get() or 0)
            except:
                discount_value = 0

            order_status = self.status.get()
            delivery_date = self.delivery_date_picker.get_date().strftime('%Y-%m-%d') if order_status == ar(
                "جاري تنفيذه") else datetime.now().strftime('%Y-%m-%d')
            order_type = self.type.get()
            pay_method = self.payment_method.get()

            # جلب مقاسات النظر إذا كان نوع الطلب طبي
            sph_r, cyl_r, axis_r = "", "", ""
            sph_l, cyl_l, axis_l = "", "", ""

            if order_type == ar("طبي"):
                sph_r = self.eye_entries[(0, 0)].get().strip()
                cyl_r = self.eye_entries[(0, 1)].get().strip()
                axis_r = self.eye_entries[(0, 2)].get().strip()
                sph_l = self.eye_entries[(1, 0)].get().strip()
                cyl_l = self.eye_entries[(1, 1)].get().strip()
                axis_l = self.eye_entries[(1, 2)].get().strip()

            with connect() as conn:
                cursor = conn.cursor()

                # الحفظ في قاعدة البيانات
                cursor.execute("""
                               INSERT INTO invoices (id, customer_name, phone, total, discount, final_total, paid, remain,
                                                     date, pdf_path, status, delivery_date, order_type, payment_method,
                                                     sph_r, cyl_r, axis_r, sph_l, cyl_l, axis_l)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                               """, (
                                   invoice_number, self.name.get().strip(), self.phone.get().strip(),
                                   self.final_total, discount_value, self.final_after_discount, paid_value,
                                   (self.final_after_discount - paid_value), self.generated_pdf_path,
                                   order_status, delivery_date, order_type, pay_method,
                                   sph_r, cyl_r, axis_r, sph_l, cyl_l, axis_l
                               ))

                for child in self.table.get_children():
                    row = self.table.item(child, 'values')
                    total_line = float(row[0])
                    qty_sold = int(row[1])
                    price_line = float(row[2])
                    item_name = row[3]
                    item_code = row[4]

                    cursor.execute("""
                                   INSERT INTO invoice_items (invoice_id, item_name, qty, price, total)
                                   VALUES (?, ?, ?, ?, ?)
                                   """, (invoice_number, item_name, qty_sold, price_line, total_line))

                    cursor.execute("""
                                   UPDATE items
                                   SET qty = qty - ?, last_sale_date = datetime('now')
                                   WHERE code = ?
                                   """, (qty_sold, item_code))

                conn.commit()

            self.invoice_saved = True
            self.saved_invoice_id = invoice_number
            self.print_enabled = True
            self.lock_ui_elements()

            messagebox.showinfo("تم بنجاح", f"✅ تم حفظ الفاتورة بنجاح في:\n{pdf_path}")

        except sqlite3.Error as e:
            messagebox.showerror("خطأ في قاعدة البيانات", f"حدث خطأ أثناء الحفظ:\n{e}")
        except Exception as e:
            messagebox.showerror("خطأ عام", f"حدثت مشكلة غير متوقعة:\n{e}")


    def lock_ui_elements(self):
        self.customer_combo.configure(state="disabled")
        self.type.configure(state="disabled")
        self.status.configure(state="disabled")
        self.payment_method.configure(state="disabled")
        self.paid.configure(state="disabled")
        self.discount.configure(state="disabled")
        self.qty.configure(state="disabled")
        self.item_combo.configure(state="disabled")
        self.group_combo.configure(state="disabled")
        self.add_item_btn.configure(state="disabled")
        self.clear_cart_btn.configure(state="disabled")
        self.add_cust_btn.configure(state="disabled")

        for key in self.eye_entries:
            self.eye_entries[key].configure(state="disabled")

    def reset_for_new_invoice(self):
        self.invoice_saved = False
        self.saved_invoice_id = None
        self.print_enabled = False
        self.final_total = 0
        self.final_after_discount = 0
        self.discount_percent_value = 0
        self.discount_value_calc = 0

        self.customer_combo.configure(state="normal")
        self.customer_combo.set("")
        self.type.configure(state="normal")
        self.type.set(ar("طبي"))
        self.status.configure(state="normal")
        self.status.set(ar("تم التسليم في حينه"))
        self.payment_method.configure(state="normal")
        self.payment_method.set("كاش")

        self.paid.configure(state="normal")
        self.paid.delete(0, "end")
        self.discount.configure(state="normal")
        self.discount.delete(0, "end")
        self.discount.insert(0, "0")

        self.qty.configure(state="normal")
        self.qty.delete(0, "end")
        self.qty.insert(0, "1")

        self.item_combo.configure(state="normal")
        self.item_combo.set("")
        self.group_combo.configure(state="normal")
        self.group_combo.set(ar("الكل"))

        self.add_item_btn.configure(state="normal")
        self.clear_cart_btn.configure(state="normal")
        self.add_cust_btn.configure(state="normal")

        self.name.configure(state="normal")
        self.name.delete(0, "end")
        self.name.configure(state="readonly")

        self.phone.configure(state="normal")
        self.phone.delete(0, "end")
        self.phone.configure(state="readonly")

        for key in self.eye_entries:
            self.eye_entries[key].configure(state="normal")
            self.eye_entries[key].delete(0, "end")

        for item in self.table.get_children():
            self.table.delete(item)

        self.toggle_eye_card_visibility(ar("طبي"))
        self.toggle_delivery_date_ui(ar("تم التسليم في حينه"))

        from database.db import get_all_items, get_customers
        self.items_data = get_all_items()
        self.customers_data = get_customers()
        self.refresh_item_combo_values()

        self.preview.configure(text="السعر: 0  |  المتاح: 0")
        self.total_value.configure(text="0.00")
        self.discount_value_label.configure(text="0.00 (0%)")
        self.net_value.configure(text="0.00")
        self.remain_value.configure(text="0.00")
        self.remain_box.configure(fg_color="#fff5f5", border_color="#ffd6d6")

        messagebox.showinfo("فاتورة جديدة", "تم تهيئة الشاشة بنجاح، ومستعدة لاستقبال الفاتورة الجديدة!")

    def select_customer(self, event=None):
        selected = self.customer_combo.get().strip()
        for c in self.customers_data:
            if f"{c[1]} | {c[2]}" == selected:
                self.fill_customer_data(c)
                return

    def fill_customer_data(self, customer):
        name = customer[1]
        phone = customer[2]

        self.name.configure(state="normal")
        self.name.delete(0, "end")
        self.name.insert(0, name)
        self.name.configure(state="readonly")

        self.phone.configure(state="normal")
        self.phone.delete(0, "end")
        self.phone.insert(0, phone)
        self.phone.configure(state="readonly")

    def filter_customers(self, event=None):
        typed = self.customer_combo.get().strip()
        if typed == "":
            self.customer_combo["values"] = [f"{c[1]} | {c[2]}" for c in self.customers_data]
            self.clear_customer_fields()
            return

        if not typed.isdigit() or len(typed) < 11:
            self.clear_customer_fields()

        filtered = [f"{c[1]} | {c[2]}" for c in self.customers_data if typed in c[1] or typed in c[2]]
        self.customer_combo["values"] = filtered

        if typed.isdigit() and len(typed) == 11:
            found = False
            for c in self.customers_data:
                if c[2] == typed:
                    self.fill_customer_data(c)
                    found = True
                    break
            if not found:
                self.clear_customer_fields()
                messagebox.showwarning("تنبيه", "⚠️ العميل غير مسجل")

    def clear_customer_fields(self):
        self.name.configure(state="normal")
        self.phone.configure(state="normal")
        self.name.delete(0, "end")
        self.phone.delete(0, "end")
        self.name.configure(state="readonly")
        self.phone.configure(state="readonly")

    def open_quick_customer(self):
        from database.db import add_customer, get_customers

        win = ctk.CTkToplevel(self.parent)
        win.title("إضافة عميل")
        win.geometry("340x280")
        win.resizable(False, False)
        win.transient(self.parent)
        win.grab_set()
        win.focus_force()
        win.lift()

        ctk.CTkLabel(win, text="اسم العميل الجديد", font=("Cairo", 11)).pack(pady=(10, 0))
        name = ctk.CTkEntry(win, justify="right", font=("Cairo", 12))
        name.pack(pady=5, padx=20, fill="x")

        phone = ctk.CTkEntry(win, placeholder_text="رقم الهاتف", justify="center", font=("Cairo", 12))
        phone.pack(pady=10, padx=20, fill="x")

        notes = ctk.CTkEntry(win, placeholder_text="ملاحظات العميل", justify="right", font=("Cairo", 12))
        notes.pack(pady=10, padx=20, fill="x")

        def save():
            if not name.get().strip() or not phone.get().strip():
                messagebox.showwarning("تنبيه", "ادخل الاسم ورقم الهاتف بالكامل")
                return

            existing = [c[2] for c in get_customers()]
            if phone.get().strip() in existing:
                messagebox.showerror("خطأ", "رقم الهاتف مسجل بالفعل لعميل آخر")
                return

            try:
                name_value = name.get().strip()
                phone_value = phone.get().strip()
                notes_value = notes.get().strip()

                add_customer(name_value, phone_value, notes_value, 0)
                messagebox.showinfo("تم", "تم إضافة العميل بنجاح للقائمة")
                win.destroy()

                self.customers_data = get_customers()
                self.customer_combo["values"] = [
                    f"{c[1]} | {c[2]}" for c in self.customers_data
                ]

                for c in self.customers_data:
                    if c[2] == phone_value:
                        self.customer_combo.set(f"{c[1]} | {c[2]}")
                        self.fill_customer_data(c)
                        break
            except sqlite3.IntegrityError:
                messagebox.showerror("خطأ", "رقم الهاتف هذا مسجل بالفعل، الرجاء استخدام رقم مختلف.")
            except Exception as e:
                logger.exception("Failed to add quick customer")
                messagebox.showerror("خطأ", f"حدث خطأ غير متوقع أثناء الحفظ: {e}")

        ctk.CTkButton(win, text="حفظ البيانات", fg_color=COLORS["success"], command=save).pack(pady=15)

    def update_totals(self):
        total = 0
        for item in self.table.get_children():
            total += float(self.table.item(item)["values"][0])

        try:
            discount_percent = float(self.discount.get())
        except:
            discount_percent = 0

        self.discount_percent_value = discount_percent
        discount_value = total * (discount_percent / 100)
        final_after_discount = total - discount_value

        self.final_total = total
        self.discount_value_calc = discount_value
        self.final_after_discount = final_after_discount

        self.animate_total(total)

        if hasattr(self, "discount_value_label"):
            self.discount_value_label.configure(text=f"{discount_value:.2f} ({discount_percent:.0f}%)")

        if hasattr(self, "net_value"):
            self.net_value.configure(text=f"{final_after_discount:.2f}")

        self.update_remaining()

    def update_remaining(self):
        try:
            total = getattr(self, "final_total", 0)
            discount_percent = float(self.discount.get()) if self.discount.get() else 0
            paid = float(self.paid.get()) if self.paid.get() else 0

            discount_amount = total * (discount_percent / 100)
            after_discount = total - discount_amount

            self.discount_value_label.configure(text=f"{discount_amount:.2f} ({discount_percent:.0f}%)")
            self.net_value.configure(text=f"{after_discount:.2f}")

            remain = after_discount - paid
            self.remain_value.configure(text=f"{remain:.2f}")

            if remain <= 0:
                self.remain_value.configure(text_color="#27ae60")
                self.remain_box.configure(fg_color="#eafaf1", border_color="#b7f5c5")
            else:
                self.remain_value.configure(text_color="#dc2626")
                self.remain_box.configure(fg_color="#fff5f5", border_color="#ffd6d6")
        except:
            pass

    def animate_total(self, target):
        try:
            current = float(self.total_value.cget("text"))
        except:
            current = 0

        step = (target - current) / 10

        def update():
            nonlocal current
            if abs(target - current) < 0.5:
                self.total_value.configure(text=f"{target:.2f}")
                return
            current += step
            self.total_value.configure(text=f"{current:.2f}")
            self.parent.after(20, update)

        update()

    def press_effect(self, btn):
        original_width = btn.cget("width")
        original_height = btn.cget("height")
        btn.configure(width=original_width - 5, height=original_height - 2)
        self.parent.after(100, lambda: btn.configure(width=original_width, height=original_height))

    def print_guard(self):
        if not self.invoice_saved:
            messagebox.showwarning("تنبيه", "لا يمكن الطباعة قبل حفظ الفاتورة")
            return
        generate_invoice_pdf(self)

    def send_whatsapp_guard(self):
        if not self.invoice_saved:
            messagebox.showwarning("تنبيه", "لا يمكن إرسال الفاتورة قبل الحفظ")
            return
        send_whatsapp_invoice(self)