import customtkinter as ctk
from tkinter import ttk, messagebox, simpledialog
import os
import subprocess
import webbrowser
import threading
import time
import traceback
from database.db import (
    get_invoice_items,
    insert_return_transaction,
    connect,
    get_total_returned_qty
)
from utils.colors import COLORS
class ReturnsScreen:
    def __init__(self, parent):
        self.parent = parent
        self.invoice_items_list = []
        self.return_cart = []
        self.selected_invoice_id = None
        self.customer_name = "عميل مبيعات"
        self.customer_phone = ""
        self.invoice_discount_percentage = 0.0
        self.customer_invoices_map = {}
        self.is_saved_successfully = False
        self.owner_phone = "201000000000"

        # توحيد المسار بشكل ثابت لضمان عدم ضياع الملفات
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.invoices_pdf_path = os.path.join(self.base_path, "invoices_pdf")
        if not os.path.exists(self.invoices_pdf_path):
            os.makedirs(self.invoices_pdf_path)

        self.build_ui()


    # ==========================================
    # 🎨 بناء الواجهة البرمجية المتكاملة مع السكرول
    # ==========================================
    def build_ui(self):
        self.main_canvas = ctk.CTkCanvas(self.parent, bg=COLORS["bg"], highlightthickness=0)
        self.main_scrollbar = ctk.CTkScrollbar(self.parent, orientation="vertical", command=self.main_canvas.yview)

        self.frame = ctk.CTkFrame(self.main_canvas, fg_color=COLORS["bg"])

        self.frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )

        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.frame, anchor="nw")

        def _on_canvas_configure(event):
            self.main_canvas.itemconfig(self.canvas_window, width=event.width)

        self.main_canvas.bind('<Configure>', _on_canvas_configure)
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)

        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_scrollbar.pack(side="right", fill="y")

        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=0)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=0)

        # ------------------------------------------
        # 1️⃣ القسم العلوي: شريط البحث المقيد والآمن تماماً
        # ------------------------------------------
        search_bar = ctk.CTkFrame(self.frame, fg_color=COLORS["card"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        search_bar.grid(row=0, column=0, sticky="ew", pady=(2, 4), padx=6)

        for col_idx in range(7):
            search_bar.grid_columnconfigure(col_idx, weight=1)

        # خانة رقم الفاتورة المباشر
        lbl_search_inv = ctk.CTkLabel(search_bar, text="رقم الفاتورة:", font=("Cairo", 12, "bold"))
        lbl_search_inv.grid(row=0, column=6, padx=(5, 12), pady=12, sticky="e")

        self.ent_invoice_id = ctk.CTkEntry(search_bar, placeholder_text="رقم السند...", justify="center", font=("Cairo", 12), height=34)
        self.ent_invoice_id.grid(row=0, column=5, padx=5, pady=12, sticky="ew")
        self.ent_invoice_id.bind("<Return>", lambda e: self.search_invoice())

        self.btn_search = ctk.CTkButton(search_bar, text="🔍 جلب", font=("Cairo", 11, "bold"), fg_color=COLORS["primary"], width=60, height=34, command=self.search_invoice)
        self.btn_search.grid(row=0, column=4, padx=5, pady=12, sticky="w")

        # خانة البحث برقم الهاتف الكامل (قفل أمني)
        lbl_search_phone = ctk.CTkLabel(search_bar, text="رقم هاتف العميل:", font=("Cairo", 12, "bold"), text_color="#6366f1")
        lbl_search_phone.grid(row=0, column=3, padx=5, pady=12, sticky="e")

        self.ent_customer_phone = ctk.CTkEntry(search_bar, placeholder_text="اكتب 11 رقم كامل...", justify="center", font=("Cairo", 12), height=34)
        self.ent_customer_phone.grid(row=0, column=2, padx=5, pady=12, sticky="ew")
        self.ent_customer_phone.bind("<KeyRelease>", self.on_customer_search_keygen)

        # 👤 بوكس منفصل تماماً لعرض اسم العميل المكتشف
        self.ent_discovered_name = ctk.CTkEntry(search_bar, placeholder_text="اسم العميل المكتشف...", justify="center", font=("Cairo", 11, "bold"), fg_color="#f8fafc", text_color="#1e293b", height=34, state="readonly")
        self.ent_discovered_name.grid(row=0, column=1, padx=5, pady=12, sticky="ew")

        # قائمة الفواتير التابعة للهاتف المكتمل
        self.combo_invoices = ctk.CTkComboBox(search_bar, values=["اختر فاتورة..."], font=("Cairo", 11), dropdown_font=("Cairo", 11), height=34, state="readonly", command=self.on_invoice_selected_from_combo)
        self.combo_invoices.grid(row=0, column=0, padx=(12, 5), pady=12, sticky="ew")

        # =====================================================
        # الجداول الاحترافية
        # =====================================================

        tables_container = ctk.CTkFrame(
            self.frame,
            fg_color="transparent"
        )
        tables_container.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=10,
            pady=5
        )

        tables_container.grid_columnconfigure(0, weight=45)
        tables_container.grid_columnconfigure(1, weight=55)
        tables_container.grid_rowconfigure(0, weight=1)

        style = ttk.Style()

        style.theme_use("clam")

        style.configure(
            "Modern.Treeview",
            background="#ffffff",
            foreground="#0f172a",
            fieldbackground="#ffffff",
            rowheight=38,
            font=("Cairo", 10),
            borderwidth=0
        )

        style.configure(
            "Modern.Treeview.Heading",
            font=("Cairo", 10, "bold"),
            background="#eff6ff",
            foreground="#1e40af",
            relief="flat",
            padding=4
        )

        style.map(
            "Modern.Treeview",
            background=[
                ("selected", "#4f46e5")
            ],
            foreground=[
                ("selected", "white")
            ]
        )

        style.theme_use("default")

        style.configure(
            "Modern.Treeview",
            font=("Cairo", 10),
            rowheight=34,
            background="white",
            fieldbackground="white",
            borderwidth=0
        )

        style.configure(
            "Modern.Treeview.Heading",
            font=("Cairo", 10, "bold"),
            padding=4
        )

        # =====================================================
        # جدول المرتجعات
        # =====================================================

        cart_frame = ctk.CTkFrame(
            tables_container,
            fg_color="#ffffff",
            corner_radius=15,
            border_width=1,
            border_color="#e2e8f0"
        )

        cart_frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 5)
        )

        cart_frame.grid_rowconfigure(1, weight=1)
        cart_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cart_frame,
            text="↩️ سلة المرتجعات",
            font=("Cairo", 14, "bold"),
            text_color="#ea580c"
        ).grid(
            row=0,
            column=0,
            pady=10
        )

        self.table_return = ttk.Treeview(
            cart_frame,
            columns=("total", "net_price", "qty", "name"),
            show="headings",
            style="Modern.Treeview"
        )

        return_scroll = ttk.Scrollbar(
            cart_frame,
            orient="vertical",
            command=self.table_return.yview
        )

        self.table_return.configure(
            yscrollcommand=return_scroll.set
        )

        self.table_return.heading("total", text="الإجمالي")
        self.table_return.heading("net_price", text="السعر")
        self.table_return.heading("qty", text="الكمية")
        self.table_return.heading("name", text="الصنف")

        self.table_return.column(
            "name",
            width=180,
            anchor="center"
        )

        self.table_return.column(
            "qty",
            width=60,
            anchor="center"
        )

        self.table_return.column(
            "net_price",
            width=75,
            anchor="center"
        )

        self.table_return.column(
            "total",
            width=90,
            anchor="center"
        )

        self.table_return.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(8, 0),
            pady=(0, 8)
        )

        return_scroll.grid(
            row=1,
            column=1,
            sticky="ns",
            pady=(0, 8)
        )

        # =====================================================
        # جدول الفاتورة
        # =====================================================

        invoice_frame = ctk.CTkFrame(
            tables_container,
            fg_color="#ffffff",
            corner_radius=15,
            border_width=1,
            border_color="#e2e8f0"
        )

        invoice_frame.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(5, 0)
        )

        invoice_frame.grid_rowconfigure(1, weight=1)
        invoice_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            invoice_frame,
            text="📦 أصناف الفاتورة",
            font=("Cairo", 14, "bold"),
            text_color=COLORS["primary"]
        ).grid(
            row=0,
            column=0,
            pady=10
        )

        self.table_invoice = ttk.Treeview(
            invoice_frame,
            columns=(
                "ret_date",
                "ret_status",
                "total",
                "net_price",
                "qty",
                "name"
            ),
            show="headings",
            style="Modern.Treeview"
        )

        invoice_scroll = ttk.Scrollbar(
            invoice_frame,
            orient="vertical",
            command=self.table_invoice.yview
        )

        self.table_invoice.configure(
            yscrollcommand=invoice_scroll.set
        )


        self.table_invoice.heading("ret_date", text="تاريخ المرتجع")
        self.table_invoice.heading("ret_status", text="الحالة")
        self.table_invoice.heading("total", text="الإجمالي")
        self.table_invoice.heading("net_price", text="السعر")
        self.table_invoice.heading("qty", text="الكمية")
        self.table_invoice.heading("name", text="الصنف")

        self.table_invoice.column(
            "name",
            width=180,
            anchor="center"
        )

        self.table_invoice.column(
            "qty",
            width=60,
            anchor="center"
        )

        self.table_invoice.column(
            "net_price",
            width=75,
            anchor="center"
        )

        self.table_invoice.column(
            "total",
            width=90,
            anchor="center"
        )

        self.table_invoice.column(
            "ret_status",
            width=100,
            anchor="center"
        )

        self.table_invoice.column(
            "ret_date",
            width=90,
            anchor="center"
        )

        self.table_invoice.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(8, 0),
            pady=(0, 8)
        )

        invoice_scroll.grid(
            row=1,
            column=1,
            sticky="ns",
            pady=(0, 8)
        )


        # =====================================================
        # الربط بالدوال الأصلية
        # =====================================================

        self.table_invoice.bind(
            "<Double-1>",
            self.add_to_return_click
        )

        self.table_return.bind(
            "<Double-1>",
            self.remove_from_return_click
        )

        # ------------------------------------------
        # 3️⃣ القسم السفلي: بوكس التقرير ولوحة أزرار التحكم
        # ------------------------------------------
        bottom_container = ctk.CTkFrame(self.frame, fg_color=COLORS["card"], corner_radius=14, border_width=1, border_color=COLORS["border"])
        bottom_container.grid(row=2, column=0, sticky="ew", padx=6, pady=(4, 6))
        bottom_container.grid_columnconfigure(0, weight=3)
        bottom_container.grid_columnconfigure(1, weight=1)

        self.details_box = ctk.CTkTextbox(
            bottom_container,
            height=160,
            corner_radius=12,
            border_width=1,
            border_color="#e5e7eb",
            fg_color="#ffffff",
            text_color="#0f172a",
            font=("Cairo", 12)
        )
        self.details_box.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.details_box._textbox.tag_configure("right_align", justify="right")
        self.clear_details_box()

        actions_panel = ctk.CTkFrame(bottom_container, fg_color="transparent")
        actions_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

        self.lbl_total_refund = ctk.CTkLabel(actions_panel, text="إجمالي المسترد الصافي:\n0.00 ج.م", font=("Cairo", 13, "bold"), text_color="#e74c3c")
        self.lbl_total_refund.pack(pady=2)

        self.btn_submit = ctk.CTkButton(
            actions_panel,
            text="💾 حفظ مستند المرتجع",
            font=("Cairo", 11, "bold"),
            fg_color="#2ea44f",
            hover_color="#1da851",
            height=38,
            corner_radius=10,
            command=self.submit_return
        )

        self.btn_submit.pack(fill="x", pady=1)

        # ✨ تم إضافة وإظهار زر المعاينة هنا وتوصيله بالدالة الآمنة
        self.btn_preview_pdf = ctk.CTkButton(actions_panel, text="👁️ معاينة الفاتورة الأصلية (PDF)", font=("Cairo", 11, "bold"), fg_color="#475569", hover_color="#334155", height=38,
        corner_radius=10, command=self.open_invoice_pdf)

        self.btn_preview_pdf.pack(fill="x", pady=1)

        self.btn_print_receipt = ctk.CTkButton(actions_panel, text="🖨️ طباعة إيصال المرتجع", font=("Cairo", 11, "bold"), fg_color="#0284c7", hover_color="#0369a1", height=38,
        corner_radius=10, command=self.print_return_receipt)

        self.btn_print_receipt.pack(fill="x", pady=1)

        self.btn_whatsapp = ctk.CTkButton(actions_panel, text="📱 إرسال إشعارات واتساب", font=("Cairo", 11, "bold"), fg_color="#16a34a", hover_color="#15803d", height=38,
        corner_radius=10, command=self.manual_whatsapp_share)

        self.btn_whatsapp.pack(fill="x", pady=1)

    def clear_details_box(self):
        self.details_box.delete("0.0", "end")

        report = """
    ═══════════════════════════════════════

              📋 ملخص عملية المرتجع

    ═══════════════════════════════════════

    👤 العميل:
    —

    🧾 رقم الفاتورة:
    —

    📦 عدد الأصناف:
    0

    💰 إجمالي المسترد:
    0.00 ج.م

    ═══════════════════════════════════════

    الرجاء البحث برقم الفاتورة أو هاتف العميل

    ═══════════════════════════════════════
    """

        self.details_box.insert("0.0", report, "right_align")

    def set_discovered_name_text(self, text):
        self.ent_discovered_name.configure(state="normal")
        self.ent_discovered_name.delete(0, "end")
        self.ent_discovered_name.insert(0, text)
        self.ent_discovered_name.configure(state="readonly")

    # ==========================================
    # 🔒 تقييد البحث برقم الهاتف الكامل مع فك الحزم
    # ==========================================
    def on_customer_search_keygen(self, event):
        search_query = self.ent_customer_phone.get().strip()

        # في حالة مسح الرقم أو عدم اكتماله
        if len(search_query) < 11:
            self.combo_invoices.configure(values=["اختر فاتورة..."])
            self.combo_invoices.set("اختر فاتورة...")
            self.set_discovered_name_text("")
            return

        # عند اكتمال الرقم
        if len(search_query) == 11:
            try:
                conn = connect()
                cur = conn.cursor()
                cur.execute("SELECT id, total, date, customer_name FROM invoices WHERE phone = ? ORDER BY date DESC",
                            (search_query,))
                invoices = cur.fetchall()
                conn.close()

                if not invoices:
                    self.set_discovered_name_text("رقم غير مسجل!")
                    self.combo_invoices.configure(values=["لا توجد فواتير"])
                    self.combo_invoices.set("لا توجد فواتير")
                    return

                discovered_name = invoices[0][3] if invoices[0][3] else "عميل مبيعات غير مسمى"
                self.set_discovered_name_text(discovered_name)

                # تجهيز القائمة
                combo_values = ["اختر فاتورة..."]
                self.customer_invoices_map = {}

                for inv_id, final_total, inv_date, cust_name in invoices:
                    display_text = f"سند: {inv_id} | الصافي: {final_total:.2f} ج.م | تاريخ: {inv_date[:10]}"
                    combo_values.append(display_text)
                    self.customer_invoices_map[display_text] = inv_id

                # تحديث القائمة وضبطها على النص الترحيبي
                self.combo_invoices.configure(values=combo_values)
                self.combo_invoices.set("اختر فاتورة...")

            except Exception as e:
                print(f"خطأ أثناء البحث المقيد برقم الهاتف: {e}")

    def on_invoice_selected_from_combo(self, selected_value):
        # منع البحث إذا كان المستخدم لم يختار فاتورة بعد أو اختار النص الترحيبي
        if selected_value == "اختر فاتورة..." or not selected_value:
            return

        # جلب رقم الفاتورة من القاموس
        invoice_id = self.customer_invoices_map.get(selected_value)

        if invoice_id:
            self.ent_invoice_id.delete(0, "end")
            self.ent_invoice_id.insert(0, str(invoice_id))
            # تنفيذ عملية البحث فعلياً
            self.search_invoice()
    # ==========================================
    # 🔍 جلب الفاتورة الآمن وتحديث الجداول
    def search_invoice(self):
        inv_id = self.ent_invoice_id.get().strip()
        if not inv_id:
            messagebox.showwarning("تنبيه", "يرجى إدخال رقم الفاتورة للبحث.")
            return

        # تنظيف الجداول والمتغيرات
        for i in self.table_invoice.get_children(): self.table_invoice.delete(i)
        for i in self.table_return.get_children(): self.table_return.delete(i)

        self.return_cart = []
        self.selected_invoice_id = None
        self.update_refund_total()
        self.clear_details_box()

        try:
            conn = connect()
            cur = conn.cursor()
            cur.execute("SELECT customer_name, total, discount, phone FROM invoices WHERE id = ?", (inv_id,))
            inv_res = cur.fetchone()

            if not inv_res:
                messagebox.showerror("خطأ", f"لا توجد فاتورة بالرقم [{inv_id}].")
                self.set_discovered_name_text("")
                conn.close()
                return

            self.customer_name = inv_res[0] or "عميل مبيعات"
            total_before_discount = inv_res[1] or 0.0
            discount_percent = inv_res[2] or 0.0
            self.customer_phone = inv_res[3] or ""
            self.set_discovered_name_text(self.customer_name)

            self.invoice_discount_percentage = (discount_percent / 100.0) if total_before_discount > 0 else 0.0

            cur.execute("SELECT item_name, qty, price FROM invoice_items WHERE invoice_id = ?", (inv_id,))
            items = cur.fetchall()
            self.selected_invoice_id = inv_id
            self.invoice_items_list = []

            for idx, item in enumerate(items):
                item_name, original_qty, orig_price = item

                # تم التصحيح: استدعاء الدالة مباشرة واستخدام النتيجة
                returned_qty = get_total_returned_qty(inv_id, item_name)

                net_price = orig_price * (1.0 - self.invoice_discount_percentage)
                available_qty = original_qty - returned_qty
                self.invoice_items_list.append((item_name, available_qty, orig_price, net_price))

                status_text = "لا يوجد مرتجع" if returned_qty == 0 else (
                    f"مرتجع بالكامل" if available_qty == 0 else f"مرتجع جزئي")

                self.table_invoice.insert("", "end", iid=str(idx),
                                          values=("-", status_text, f"{(available_qty * net_price):.2f}",
                                                  f"{net_price:.2f}", available_qty, item_name))

            conn.close()
            self.update_live_report_text()
        except Exception as e:
            messagebox.showerror("خطأ تقني", f"حدث خطأ أثناء الاتصال:\n{str(e)}")
            if 'conn' in locals(): conn.close()


    # ==========================================
    # ➕ إضافة صنف إلى سلة المرتجعات
    # ==========================================
    def add_to_return_click(self, event):
        selected = self.table_invoice.focus()
        if not selected: return

        idx = int(selected)
        item_name, available_qty, orig_price, net_price = self.invoice_items_list[idx]

        if available_qty <= 0:
            messagebox.showwarning("تنبيه", "هذا الصنف تم استرداده بالكامل مسبقاً.")
            return

        for existing in self.return_cart:
            if existing[0] == item_name: return

        ret_qty = simpledialog.askinteger(
            "كمية الرد", f"المنتج: {item_name}\nالكمية المتاحة: {available_qty}\n\nأدخل الكمية المستردة:",
            minvalue=1, maxvalue=available_qty, parent=self.parent
        )
        if not ret_qty: return

        total_refund_item = ret_qty * net_price
        self.return_cart.append((item_name, ret_qty, orig_price, net_price, total_refund_item))

        self.table_return.insert("", "end", values=(f"{total_refund_item:.2f}", f"{net_price:.2f}", ret_qty, item_name))
        self.update_refund_total()
        self.update_live_report_text()
        self.is_saved_successfully = False

    # ==========================================
    # ❌ إلغاء الصنف المحدد بالخطأ
    # ==========================================
    def remove_from_return_click(self, event):
        selected = self.table_return.focus()
        if not selected: return
        values = self.table_return.item(selected)["values"]

        self.return_cart = [item for item in self.return_cart if item[0] != values[3]]
        self.table_return.delete(selected)

        self.update_refund_total()
        self.update_live_report_text()
        self.is_saved_successfully = False

    def update_refund_total(self):

        total_refund = sum(item[4] for item in self.return_cart)

        color = "#dc2626"

        if total_refund > 0:
            color = "#16a34a"

        self.lbl_total_refund.configure(
            text=f"{total_refund:.2f} ج.م",
            text_color=color
        )

    def update_live_report_text(self):

        if not self.selected_invoice_id:
            return

        total_refund = sum(item[4] for item in self.return_cart)

        items_count = len(self.return_cart)

        items_text = ""

        for idx, item in enumerate(self.return_cart, start=1):
            items_text += (
                f"\n{idx}- {item[0]}"
                f"\n   الكمية: {item[1]}"
                f"\n   المسترد: {item[4]:.2f} ج.م\n"
            )

        report = f"""
    ═══════════════════════════════════════

    📋 ملخص عملية المرتجع

    ═══════════════════════════════════════

    👤 العميل:
    {self.customer_name}

    🧾 رقم الفاتورة:
    {self.selected_invoice_id}

    📦 عدد الأصناف المرتجعة:
    {items_count}

    💰 إجمالي المسترد:
    {total_refund:.2f} ج.م

    ═══════════════════════════════════════

    الأصناف المرتجعة:

    {items_text if items_text else "لا توجد أصناف مضافة"}

    ═══════════════════════════════════════
    """

        self.details_box.delete("0.0", "end")
        self.details_box.insert("0.0", report, "right_align")

    # ==========================================
    # 👁️ دالة المعاينة (مصححة للمسار الموحد)
    # ==========================================
    def open_invoice_pdf(self):
        inv_id = self.ent_invoice_id.get().strip()
        if not inv_id:
            messagebox.showwarning("تنبيه", "يرجى جلب فاتورة أولاً.")
            return

        pdf_path = os.path.join(self.invoices_pdf_path, f"invoice_{inv_id}.pdf")

        if os.path.exists(pdf_path):
            os.startfile(pdf_path)
        else:
            messagebox.showerror("خطأ", f"الملف غير موجود في المسار:\n{pdf_path}")

    # ==========================================
    # 💾 دالة الحفظ (مصححة لضمان تسلسل العمليات)
    # ==========================================
    def submit_return(self):
        # 1. التحقق من وجود بيانات
        if not self.selected_invoice_id or not self.return_cart:
            messagebox.showwarning("تنبيه", "الرجاء جلب فاتورة وإضافة أصناف للمرتجع.")
            return

        # 2. التأكد من رغبة المستخدم
        if not messagebox.askyesno("تأكيد", f"هل أنت متأكد من حفظ مرتجع للفاتورة [{self.selected_invoice_id}]؟"):
            return

        # 3. إظهار حالة المعالجة (تعطيل الزر مؤقتاً)
        self.btn_submit.configure(state="disabled")

        try:
            # 4. الحفظ في قاعدة البيانات عبر الدالة المستوردة
            success = insert_return_transaction(
                self.selected_invoice_id,
                self.customer_name,
                sum(item[4] for item in self.return_cart),
                self.return_cart
            )

            if success:
                # 5. توليد ودمج الـ PDF
                pdf_success = self.generate_return_pdf_receipt()

                if pdf_success:
                    self.is_saved_successfully = True
                    messagebox.showinfo("تم بنجاح", "تم حفظ المرتجع وتحديث الفاتورة بنجاح.")

                    # 6. تحديث الواجهة فوراً لرؤية النتائج الجديدة
                    self.search_invoice()
                else:
                    messagebox.showerror("خطأ", "تم حفظ البيانات في القاعدة، ولكن فشل إنشاء أو دمج PDF.")
            else:
                messagebox.showerror("خطأ", "فشل الحفظ بقاعدة البيانات.")

        except Exception as e:
            messagebox.showerror("خطأ غير متوقع", f"حدث خطأ أثناء تنفيذ عملية الحفظ:\n{e}")
        finally:
            # إعادة تفعيل الزر في كل الحالات
            self.btn_submit.configure(state="normal")

    # ==========================================
    # 🖨️ زر [3]: طباعة الإيصال
    # ==========================================
        # ==========================================
        # 🖨️ زر [3]: طباعة الإيصال (الدالة الموحدة والمصححة)
    # ==========================================
    def print_return_receipt(self):
        if not self.is_saved_successfully:
            messagebox.showwarning("حماية أمنية",
                                   "🚨 لا يمكن طباعة الإيصال! الرجاء حفظ مستند المرتجع أولاً بقاعدة البيانات قبل إجراء هذه العملية.")
            return

        inv_id = self.ent_invoice_id.get().strip()
        if not inv_id:
            return

        # تحديد المسارات
        pdf_folder = self.invoices_pdf_path
        original_invoice_path = os.path.join(pdf_folder, f"invoice_{inv_id}.pdf")
        return_receipt_path = os.path.join(pdf_folder, f"return_receipt_{inv_id}.pdf")

        # الأولوية للطباعة: الفاتورة المدمجة (إن وجدت)، وإلا نعتمد على إيصال المرتجع المنفصل
        pdf_to_print = original_invoice_path if os.path.exists(original_invoice_path) else return_receipt_path

        if not os.path.exists(pdf_to_print):
            messagebox.showerror("خطأ", f"ملف الطباعة غير موجود في المسار:\n{pdf_to_print}")
            return

        messagebox.showinfo("إعداد الطباعة", "⏳ جاري توجيه الملف إلى الطابعة الافتراضية... الرجاء الانتظار.")

        try:
            if os.name == 'nt':
                # نظام ويندوز
                try:
                    os.startfile(pdf_to_print, "print")
                except Exception as e:
                    # في حال فشل الطباعة المباشرة، نفتح الملف للمستخدم ليطبعه يدوياً
                    messagebox.showwarning("تنبيه", f"فشل أمر الطباعة المباشر، سيتم فتح الملف يدوياً:\n{e}")
                    os.startfile(pdf_to_print)
            else:
                # أنظمة لينكس/ماك
                subprocess.run(["lp", pdf_to_print], check=True)

        except Exception as e:
            messagebox.showerror("خطأ طباعة", f"تعذر تنفيذ أمر الطباعة:\n{e}")

    # ==========================================
    # 📱 زر [4]: تشغيل إرسال الواتساب
    # ==========================================
    def manual_whatsapp_share(self):
        if not self.is_saved_successfully:
            messagebox.showwarning("حماية أمنية", "🚨 لا يمكن إرسال واتساب! الرجاء حفظ مستند المرتجع أولاً بقاعدة البيانات قبل إجراء هذه العملية.")
            return

        if not self.selected_invoice_id:
            messagebox.showwarning("تنبيه", "لا توجد بيانات فاتورة نشطة لإرسالها.")
            return

        messagebox.showinfo("إرسال واتساب", "⏳ جاري إعداد الرسائل وفتح نوافذ واتساب الويب للعميل وصاحب المحل تلقائياً...")
        threading.Thread(target=self.open_whatsapp_shares, daemon=True).start()

    def open_whatsapp_shares(self):
        try:
            with connect() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT IFNULL(SUM(ri.total), 0)
                    FROM return_items ri
                    JOIN returns r ON ri.return_id = r.id
                    WHERE r.invoice_id = ?
                """, (self.selected_invoice_id,))
                res = cur.fetchone()
                total_refund = res[0] if res and res[0] is not None else 0.0
        except:
            total_refund = 0.0

        client_msg = f"مرحبا سيد {self.customer_name}، تم اعتماد مستند المرتجع النقدي الخاص بك لطلب رقم [{self.selected_invoice_id}] بنجاح، قيمة المسترد الفعلي المرتجع لكم: {total_refund:.2f} ج.م. شكرا لتعاملك معنا."
        owner_msg = f"🚨 إشعار حركة مرتجع جديدة:\nتم عمل مرتجع مالي بنجاح للفاتورة رقم [{self.selected_invoice_id}]\nالعميل: {self.customer_name}\nإجمالي القيمة المستردة والمصروفة من الخزنة: {total_refund:.2f} ج.م."

        if self.customer_phone and len(self.customer_phone.strip()) >= 11:
            clean_client = self.customer_phone.strip().replace("+", "")
            if not clean_client.startswith("2"): clean_client = "2" + clean_client
            url_client = f"https://web.whatsapp.com/send?phone={clean_client}&text={client_msg}"
            webbrowser.open_new_tab(url_client)
            time.sleep(8)

        clean_owner = self.owner_phone.strip().replace("+", "")
        if not clean_owner.startswith("2"): clean_owner = "2" + clean_owner
        url_owner = f"https://web.whatsapp.com/send?phone={clean_owner}&text={owner_msg}"
        webbrowser.open_new_tab(url_owner)

    # ==========================================
    # 📄 توليد ودمج الـ PDF (مصححة للمسار الموحد)
    # ==========================================
    def generate_return_pdf_receipt(self):
        from reportlab.lib.pagesizes import A6
        from reportlab.pdfgen import canvas
        from pypdf import PdfWriter, PdfReader

        target_id = self.selected_invoice_id
        receipt_path = os.path.join(self.invoices_pdf_path, f"return_receipt_{target_id}.pdf")
        original_path = os.path.join(self.invoices_pdf_path, f"invoice_{target_id}.pdf")

        # 1. إنشاء إيصال المرتجع المنفصل كصفحة A6
        try:
            c = canvas.Canvas(receipt_path, pagesize=A6)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(30, 380, "Ghazaly Optical - Return Receipt")
            c.setFont("Helvetica", 9)
            c.drawString(30, 360, f"Invoice ID: {target_id}")
            c.drawString(30, 345, f"Date: {time.strftime('%Y-%m-%d %H:%M')}")
            c.drawString(30, 330, f"Customer: {self.customer_name}")
            c.save()
        except Exception as e:
            print(f"خطأ في إنشاء إيصال المرتجع: {e}")
            return False

        # 2. الدمج السليم مع الفاتورة الأصلية (إن وجدت)
        if os.path.exists(original_path):
            try:
                writer = PdfWriter()

                # إضافة صفحات الفاتورة الأصلية
                reader_orig = PdfReader(original_path)
                for page in reader_orig.pages:
                    writer.add_page(page)

                # إضافة صفحة المرتجع
                reader_ret = PdfReader(receipt_path)
                for page in reader_ret.pages:
                    writer.add_page(page)

                # الكتابة في ملف مؤقت لتجنب تداخل القراءة والكتابة
                temp_path = os.path.join(self.invoices_pdf_path, f"temp_{target_id}.pdf")
                with open(temp_path, "wb") as f_out:
                    writer.write(f_out)

                # استبدال الملف القديم بالجديد المدمج
                os.replace(temp_path, original_path)
                return True
            except Exception as e:
                print(f"خطأ أثناء دمج PDF: {e}")
                messagebox.showerror("خطأ دمج", f"تعذر دمج المرتجع مع الملف الأصلي: {e}")
                return False
        else:
            # إذا لم توجد فاتورة أصلية، نكتفي بإيصال المرتجع
            return True

