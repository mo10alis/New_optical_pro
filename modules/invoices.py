import customtkinter as ctk
from tkinter import ttk, messagebox
from database.db import get_invoices, delete_invoice, get_invoice_items
import os
import webbrowser
import urllib.parse
from pathlib import Path
from utils.colors import COLORS
from utils.arabic import ar
from tkcalendar import DateEntry
from datetime import datetime


class InvoicesScreen:

    def __init__(self, parent, current_user=None, user_permissions=None):
        self.parent = parent
        self.data = []
        self.selected_invoice = None
        self.current_user = current_user
        self.user_permissions = set(user_permissions or [])

        self.build_ui()
        self.load_data()

    # ==========================================
    # 🎨 بناء الواجهة العمودي الثلاثي المطور للابتوب
    # ==========================================
    def build_ui(self):
        # الحاوية الرئيسية للشاشة
        self.frame = ctk.CTkFrame(self.parent, fg_color=COLORS["bg"])
        self.frame.pack(fill="both", expand=True, padx=5, pady=5)

        # تقسيم الشاشة عمودياً إلى أجزاء متناسقة
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=0)  # العلوي: شريط البحث
        self.frame.grid_rowconfigure(1, weight=0)  # الأوسط العلوي: كروت الإحصائيات الذكية
        self.frame.grid_rowconfigure(2, weight=1)  # الأوسط: الجدول
        self.frame.grid_rowconfigure(3, weight=1)  # السفلي: تفاصيل الفاتورة والأزرار

        # ------------------------------------------
        # 1️⃣ القسم العلوي: شريط البحث والفلترة المتقدم
        # ------------------------------------------
        search_filter_bar = ctk.CTkFrame(
            self.frame,
            fg_color=COLORS["card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"]
        )
        search_filter_bar.grid(row=0, column=0, sticky="ew", pady=(2, 4), padx=5)

        for col_idx in range(6):
            search_filter_bar.grid_columnconfigure(col_idx, weight=1)

        # حقل البحث التدريجي اللحظي (مربوط بالدالة الفورية المصلحة)
        self.search = ctk.CTkEntry(
            search_filter_bar,
            placeholder_text="🔍 ابحث باسم العميل أو رقم الهاتف تدريجياً...",
            justify="right",
            font=("Cairo", 12),
            height=34
        )
        self.search.grid(row=0, column=5, padx=8, pady=8, sticky="ew")
        self.search.bind("<KeyRelease>", lambda e: self.filter_data())

        # فلتر التاريخ الذكي: إلى
        ctk.CTkLabel(search_filter_bar, text=ar("إلى:"), font=("Cairo", 11, "bold")).grid(row=0, column=4, sticky="e",
                                                                                          padx=2)
        self.date_to = DateEntry(
            search_filter_bar, width=12, background=COLORS["primary"], foreground='white', borderwidth=2,
            font=("Arial", 10), date_pattern='yyyy-mm-dd'
        )
        self.date_to.grid(row=0, column=3, padx=5, pady=8, sticky="ew")
        self.date_to.bind("<Escape>", lambda e: self.safe_close_calendar(self.date_to))

        # فلتر التاريخ الذكي: من
        ctk.CTkLabel(search_filter_bar, text=ar("من:"), font=("Cairo", 11, "bold")).grid(row=0, column=2, sticky="e",
                                                                                         padx=2)
        self.date_from = DateEntry(
            search_filter_bar, width=12, background=COLORS["primary"], foreground='white', borderwidth=2,
            font=("Arial", 10), date_pattern='yyyy-mm-dd'
        )
        self.date_from.grid(row=0, column=1, padx=5, pady=8, sticky="ew")
        self.date_from.bind("<Escape>", lambda e: self.safe_close_calendar(self.date_from))

        # حاوية أزرار التحكم بالفلترة والتحديث
        btn_action_frame = ctk.CTkFrame(search_filter_bar, fg_color="transparent")
        btn_action_frame.grid(row=0, column=0, padx=8, pady=8, sticky="w")

        filter_btn = ctk.CTkButton(
            btn_action_frame, text="🔍 تصفية بالتاريخ", font=("Cairo", 11, "bold"), fg_color=COLORS["primary"],
            width=100, height=32, command=self.filter_by_date_click
        )
        filter_btn.pack(side="left", padx=2)

        clear_filter_btn = ctk.CTkButton(
            btn_action_frame, text="❌ إلغاء", font=("Cairo", 11, "bold"), fg_color="#718093", hover_color="#2f3640",
            width=60, height=32, command=self.clear_date_filter
        )
        clear_filter_btn.pack(side="left", padx=2)

        refresh_btn = ctk.CTkButton(
            btn_action_frame, text="🔄 تحديث", font=("Cairo", 11, "bold"), fg_color=COLORS["info"],
            hover_color="#2980b9", width=70, height=32, command=self.load_data
        )
        refresh_btn.pack(side="left", padx=2)

        # ------------------------------------------
        # 2️⃣ القسم الأوسط العلوي: بوكسات الإحصائيات المالية الملوّنة والنقدية
        # ------------------------------------------
        stats_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        stats_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        for i in range(5):
            stats_frame.grid_columnconfigure(i, weight=1)

        self.card_total_before = self.create_stat_card(stats_frame, "الإجمالي (قبل)", "0.00 ج.م", "#34495e", 4)
        self.card_discount = self.create_stat_card(stats_frame, "إجمالي مبالغ الخصم", "0.00 ج.م", "#e67e22", 3)
        self.card_net = self.create_stat_card(stats_frame, "الصافي النهائي", "0.00 ج.م", COLORS["primary"], 2)
        self.card_paid = self.create_stat_card(stats_frame, "إجمالي المدفوع", "0.00 ج.م", "#2ea44f", 1)
        self.card_remain = self.create_stat_card(stats_frame, "إجمالي المتبقي الآجل", "0.00 ج.م", "#e74c3c", 0)

        # ------------------------------------------
        # 3️⃣ القسم الأوسط السفلي: جدول الفواتير المطور (السكرول بجانبه مباشرة)
        # ------------------------------------------
        middle_container = ctk.CTkFrame(self.frame, fg_color="transparent")
        middle_container.grid(row=2, column=0, sticky="nsew", padx=5, pady=2)
        middle_container.grid_rowconfigure(0, weight=1)
        middle_container.grid_columnconfigure(0, weight=1)

        table_frame = ctk.CTkFrame(middle_container, fg_color="white", corner_radius=12, border_width=1,
                                   border_color="#e4e6eb")
        table_frame.grid(row=0, column=0, sticky="nsew")

        style = ttk.Style()
        style.configure("Invoices.Treeview", font=("Cairo", 11), rowheight=28, fieldbackground="white")
        style.configure("Invoices.Treeview.Heading", font=("Cairo", 11, "bold"), background="#f8fafc",
                        foreground=COLORS["text"])

        self.table = ttk.Treeview(
            table_frame,
            columns=("id", "name", "phone", "total", "discount", "final_total", "paid", "remain", "status", "date"),
            show="headings",
            style="Invoices.Treeview",
            height=6
        )

        headers = [
            ("id", "رقم الفاتورة", 90),
            ("name", "اسم العميل", 150),
            ("phone", "رقم الهاتف", 100),
            ("total", "الإجمالي", 80),
            ("discount", "الخصم ج.م", 80),
            ("final_total", "الصافي", 80),
            ("paid", "المدفوع", 80),
            ("remain", "المتبقي", 80),
            ("status", "حالة الفاتورة", 110),
            ("date", "تاريخ الإنشاء", 130)
        ]

        for col, text, width in headers:
            self.table.heading(col, text=text, anchor="center")
            self.table.column(col, anchor="center", width=width, minwidth=width)

        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=v_scrollbar.set)

        self.table.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        v_scrollbar.pack(side="right", fill="y", padx=(0, 4), pady=4)

        self.table.bind("<<TreeviewSelect>>", self.on_select)

        # ------------------------------------------
        # 4️⃣ القسم السفلي: المعاينة الفاخرة المنسقة بالكامل والخطوط أحادية المسافة
        # ------------------------------------------
        bottom_container = ctk.CTkFrame(
            self.frame,
            fg_color=COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"]
        )
        bottom_container.grid(row=3, column=0, sticky="nsew", padx=5, pady=(4, 2))

        bottom_container.grid_rowconfigure(0, weight=0)
        bottom_container.grid_rowconfigure(1, weight=1)
        bottom_container.grid_rowconfigure(2, weight=0)
        bottom_container.grid_columnconfigure(0, weight=1)

        self.info_label = ctk.CTkLabel(
            bottom_container,
            text="📋 النظرة الفورية ومحتويات السند الفعلي المحدد (مرتب ومحاذى لليمين):",
            font=("Cairo", 12, "bold"),
            text_color=COLORS["primary"],
            anchor="e"
        )
        self.info_label.grid(row=0, column=0, sticky="ew", padx=15, pady=(6, 2))

        self.details_box = ctk.CTkTextbox(
            bottom_container,
            font=("Courier New", 12, "bold") if os.name == 'nt' else ("Cairo", 11, "bold"),
            wrap="none",
            border_width=1,
            border_color=COLORS["border"],
            fg_color="#fffdf9",
            text_color="#2c3e50",
            height=110
        )
        self.details_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)

        self.details_box._textbox.tag_configure("right_align", justify="right")
        self.details_box.insert("0.0",
                                "\n\t\t⚠️ الرجاء تحديد فاتورة من الجدول بالأعلى لعرض تفاصيل الأصناف والحسابات المربوطة.",
                                "right_align")

        # لوحة أزرار العمليات مصفوفة أفقياً
        buttons_frame = ctk.CTkFrame(bottom_container, fg_color="transparent")
        buttons_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(2, 6))

        for btn_col in range(4):
            buttons_frame.grid_columnconfigure(btn_col, weight=1)

        self.pdf_btn = ctk.CTkButton(
            buttons_frame, text="📄 فتح فاتورة PDF", font=("Cairo", 12, "bold"), fg_color=COLORS["primary"],
            hover_color="#6d28d9", height=34, command=self.open_pdf
        )
        self.pdf_btn.grid(row=0, column=3, padx=5, sticky="ew")

        self.ext_btn = ctk.CTkButton(
            buttons_frame, text="🌐 فتح بالمتصفح", font=("Cairo", 12), fg_color="#718093", hover_color="#2f3640",
            height=34, command=self.open_external_pdf
        )
        self.ext_btn.grid(row=0, column=2, padx=5, sticky="ew")

        self.wa_btn = ctk.CTkButton(
            buttons_frame, text="📱 إرسال واتساب", font=("Cairo", 12, "bold"), fg_color="#25D366", hover_color="#1da851",
            height=34, command=self.send_whatsapp
        )
        self.wa_btn.grid(row=0, column=1, padx=5, sticky="ew")

        self.del_btn = ctk.CTkButton(
            buttons_frame, text="🗑️ حذف الفاتورة", font=("Cairo", 12, "bold"), fg_color="#e74c3c",
            hover_color="#c0392b", height=34, command=self.delete_selected
        )
        self.del_btn.grid(row=0, column=0, padx=5, sticky="ew")

    def safe_close_calendar(self, date_widget):
        try:
            if hasattr(date_widget, '_top_cal') and date_widget._top_cal:
                date_widget._top_cal.withdraw()
        except:
            pass

    def create_stat_card(self, parent, title, val, color, col):
        card = ctk.CTkFrame(parent, fg_color=COLORS["card"], border_width=1, border_color=COLORS["border"],
                            corner_radius=10)
        card.grid(row=0, column=col, padx=4, pady=4, sticky="ew")

        lbl_title = ctk.CTkLabel(card, text=title, font=("Cairo", 10, "bold"), text_color="#7f8c8d")
        lbl_title.pack(pady=(4, 0))

        lbl_val = ctk.CTkLabel(card, text=val, font=("Cairo", 13, "bold"), text_color=color)
        lbl_val.pack(pady=(0, 4))

        return lbl_val

    def load_data(self):
        try:
            raw_data = get_invoices() or []
            self.data = []

            for r in raw_data:
                self.data.append((
                    r[0],  # id
                    r[1],  # customer_name
                    r[2],  # phone
                    r[3],  # total
                    r[4],  # discount (قد يحتوي على نسبة أو مبالغ تالفة أحياناً)
                    r[5],  # final_total
                    r[6],  # paid
                    r[7],  # remain
                    r[8],  # date
                    r[9] if len(r) > 9 else ""  # pdf_path
                ))

            self.refresh(self.data)
        except Exception as e:
            print("خطأ أثناء تحميل كشوفات الفواتير:", e)

    def refresh(self, data):
        for i in self.table.get_children():
            self.table.delete(i)

        sum_before = 0.0
        sum_discount = 0.0
        sum_net = 0.0
        sum_paid = 0.0
        sum_remain = 0.0

        for idx, row in enumerate(data):
            try:
                b = float(row[3])  # الإجمالي قبل
                n = float(row[5])  # الصافي
                p = float(row[6])  # المدفوع
                r_val = float(row[7])  # المتبقي

                # 🟢 تصحيح حساب مبالغ الخصم الحقيقية: الإجمالي قبل ناقص الصافي بعد
                actual_discount_money = b - n
                if actual_discount_money < 0:
                    actual_discount_money = 0.0
            except:
                b = n = p = r_val = actual_discount_money = 0.0

            sum_before += b
            sum_discount += actual_discount_money  # تجميع المبالغ النقدية الصحيحة 100%
            sum_net += n
            sum_paid += p
            sum_remain += r_val

            status_text = "🟢 مسددة بالكامل" if r_val <= 0 else "🔴 متبقي مديونية"

            # عرض مبلغ الخصم كقيمة نقدية حقيقية بالجدول أيضاً
            display_values = (
                row[0], row[1], row[2], f"{b:.2f}", f"{actual_discount_money:.2f}", f"{n:.2f}", f"{p:.2f}",
                f"{r_val:.2f}", status_text, row[8]
            )

            tag = "even" if idx % 2 == 0 else "odd"
            self.table.insert("", "end", values=display_values, tags=(tag,))

        self.table.tag_configure("odd", background="#fafbfc")
        self.table.tag_configure("even", background="white")

        # تعبئة الكروت العلوية بالمبالغ النقدية الصحيحة والمدققة تماماً كشاشة التقارير
        self.card_total_before.configure(text=f"{sum_before:.2f} ج.م")
        self.card_discount.configure(text=f"{sum_discount:.2f} ج.م")
        self.card_net.configure(text=f"{sum_net:.2f} ج.م")
        self.card_paid.configure(text=f"{sum_paid:.2f} ج.م")
        self.card_remain.configure(text=f"{sum_remain:.2f} ج.م")

    # ==========================================
    # 🔍 البحث التدرجي الفوري المصلح (مستقل وبأعلى كفاءة)
    # ==========================================
    def filter_data(self, event=None):
        search_query = self.search.get().strip().lower()

        # 🟢 إذا تم مسح حقل البحث، يعود لعرض كل البيانات فوراً دون قيود تاريخ اليوم
        if not search_query:
            self.refresh(self.data)
            return

        actual_filtered = []

        # فحص لحظي مباشر وسريع جداً بمجرد كتابة أول حرف أو رقم
        for row in self.data:
            cust_name = str(row[1]).strip().lower()
            cust_phone = str(row[2]).strip().lower()

            # يبحث تدريجياً في الاسم أو في رقم الهاتف مباشرة
            if (search_query in cust_name) or (search_query in cust_phone):
                actual_filtered.append(row)

        self.refresh(actual_filtered)

    # ==========================================
    # 📅 فلترة مخصصة بالتاريخ عند ضغط زر التصفية
    # ==========================================
    def filter_by_date_click(self):
        search_query = self.search.get().strip().lower()

        try:
            date_from_str = self.date_from.get_date().strftime('%Y-%m-%d')
            date_to_str = self.date_to.get_date().strftime('%Y-%m-%d')
        except:
            return

        actual_filtered = []

        for row in self.data:
            cust_name = str(row[1]).strip().lower()
            cust_phone = str(row[2]).strip().lower()
            invoice_date = str(row[8]).split()[0].strip()

            text_match = True
            if search_query:
                if (search_query not in cust_name) and (search_query not in cust_phone):
                    text_match = False

            # فحص النطاق الزمني بدقة
            date_match = (date_from_str <= invoice_date <= date_to_str)

            if text_match and date_match:
                actual_filtered.append(row)

        self.refresh(actual_filtered)

    def clear_date_filter(self):
        self.search.delete(0, "end")
        self.date_from.set_date(datetime.now())
        self.date_to.set_date(datetime.now())
        self.refresh(self.data)

    # ==========================================
    # 🎯 حدث تحديد الفاتورة وتنسيق الأعمدة واستقامتها كالمسطرة
    # ==========================================
    def on_select(self, event=None):
        item = self.table.focus()
        if not item:
            return

        display_values = self.table.item(item)["values"]
        invoice_id = display_values[0]

        self.selected_invoice = None
        for row in self.data:
            if str(row[0]) == str(invoice_id):
                self.selected_invoice = row
                break

        if not self.selected_invoice:
            return

        def safe_float(v):
            try:
                return float(v)
            except:
                return 0.0

        total_before = safe_float(self.selected_invoice[3])
        final_net = safe_float(self.selected_invoice[5])
        discount_val = total_before - final_net
        if discount_val < 0: discount_val = 0.0

        paid_amount = safe_float(self.selected_invoice[6])
        remain_amount = safe_float(self.selected_invoice[7])
        status_str = "🟢 مسددة بالكامل" if remain_amount <= 0 else "🔴 متبقي مديونية"

        # جلب تفاصيل قطع المبيعات مع تنسيق طولي ثابت ومحاذاة الفراغات بشكل متزن
        items = get_invoice_items(str(invoice_id))
        items_text = ""
        for idx, i in enumerate(items, start=1):
            item_name = f"{i[0]:<28}"
            qty = f"{i[1]:<6}"
            price = f"{i[2]:.2f} ج.م"
            tot = f"{i[3]:.2f} ج.م"
            items_text += f"   💎 [{idx}] {item_name} | الكمية: {qty} | السعر: {price:<12} | الإجمالي: {tot}\n"

        text_report = f"""
  📋 تفاصيل السند المالي رقم: [{invoice_id}]
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  👤 اسم العميل المعتمد : {str(self.selected_invoice[1])}
  📞 رقم هاتف التواصل   : {str(self.selected_invoice[2])}
  📅 تاريخ إصدار السند   : {str(self.selected_invoice[8])}
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📦 المنتجات والمشتملات المدرجة بالفاتورة:
{items_text if items_text else "   ⚠️ لا توجد مبيعات أصناف مدرجة داخل هذا السند بقاعدة البيانات."}
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  💰 الحساب المالي والتدقيق النهائي:
   ▪️ الإجمالي قبل الخصم: {total_before:.2f} ج.م            ▪️ المبلغ المدفوع نقداً: {paid_amount:.2f} ج.م
   ▪️ قيمة الخصم الممنوح: {discount_val:.2f} ج.م            ▪️ المتبقي الآجل الفعلي: {remain_amount:.2f} ج.م
   ▪️ الصافي بعد الخصم : {final_net:.2f} ج.م            ▪️ حالة مديونية السند  : {status_str}
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        self.details_box.delete("0.0", "end")
        self.details_box.insert("0.0", text_report, "right_align")

    def open_pdf(self):
        if not self.selected_invoice:
            messagebox.showwarning("تنبيه", "الرجاء اختيار الفاتورة أولاً.")
            return
        pdf_path = self.selected_invoice[9] if len(self.selected_invoice) > 9 else ""
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("خطأ", "الملف الرقمي للفاتورة PDF غير موجود بالمسار المحدد.")
            return
        os.startfile(pdf_path)

    def open_external_pdf(self):
        if not self.selected_invoice:
            messagebox.showwarning("تنبيه", "الرجاء اختيار الفاتورة أولاً.")
            return
        pdf_path = self.selected_invoice[9] if len(self.selected_invoice) > 9 else ""
        if pdf_path and os.path.exists(pdf_path):
            webbrowser.open(Path(pdf_path).resolve().as_uri())
        else:
            messagebox.showerror("خطأ", "لم يتم العثور على ملف الـ PDF الخارجي.")

    def delete_selected(self):
        if "الفواتير" not in self.user_permissions:
            messagebox.showerror("صلاحية مفقودة", "ليس لديك صلاحية لحذف الفواتير")
            return

        if not self.selected_invoice:
            messagebox.showwarning("تنبيه", "الرجاء اختيار الفاتورة المراد حذفها أولاً.")
            return
        confirm = messagebox.askyesno("تأكيد الحذف",
                                      f"⚠️ هل أنت متأكد من رغبتك في حذف الفاتورة رقم ({self.selected_invoice[0]}) نهائياً؟")
        if not confirm:
            return
        try:
            delete_invoice(self.selected_invoice[0])
            self.load_data()
            self.details_box.delete("0.0", "end")
            self.details_box.insert("0.0",
                                    "\n\t\t⚠️ الرجاء تحديد فاتورة من الجدول بالأعلى لعرض تفاصيل الأصناف والحسابات المربوطة.",
                                    "right_align")
            self.selected_invoice = None
            messagebox.showinfo("تم", "✅ تم مسح وحذف بيانات الفاتورة المحددة بنجاح.")
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل إجراء الحذف:\n{e}")

    def send_whatsapp(self):
        if not self.selected_invoice:
            messagebox.showwarning("تنبيه", "اختر الفاتورة المراد مشاركتها عبر الواتساب.")
            return

        phone = str(self.selected_invoice[2]).strip()
        if not phone or phone == "None":
            messagebox.showerror("خطأ", "لا يوجد رقم هاتف مسجل لهذا العميل.")
            return

        phone = phone.replace(" ", "").replace("-", "").replace("+", "")

        if phone.startswith("01") and len(phone) == 11:
            phone = "20" + phone[1:]
        elif phone.startswith("1") and len(phone) == 10:
            phone = "20" + phone
        elif phone.startswith("20"):
            pass
        else:
            messagebox.showerror("خطأ", f"صيغة رقم الهاتف غير صحيحة: {phone}")
            return

        invoice_id = self.selected_invoice[0]
        customer = self.selected_invoice[1]

        def safe_float(v):
            try:
                return float(v)
            except:
                return 0.0

        total_before = safe_float(self.selected_invoice[3])
        final_net = safe_float(self.selected_invoice[5])
        paid_amount = safe_float(self.selected_invoice[6])
        remain_amount = safe_float(self.selected_invoice[7])

        items = get_invoice_items(str(invoice_id))
        items_text = ""
        for idx, i in enumerate(items, start=1):
            items_text += f"\n🔹 *{i[0]}*\n  الكمية: {i[1]} × السعر: {i[2]:.2f} = {i[3]:.2f} ج.م\n"

        if not items_text:
            items_text = "\n⚠️ لا توجد أصناف مدرجة."

        msg = f"""*🧾 فاتورة مبيعات رقمية - Optical Elite System*

*👤 العميل الكريم:* {customer}
*🆔 رقم الفاتورة:* {invoice_id}
*📅 التاريخ والوقت:* {self.selected_invoice[8]}
━━━━━━━━━━━━━━━━━━
*📦 تفاصيل المشتريات والأصناف:*
{items_text}
━━━━━━━━━━━━━━━━━━
*💸 الصافي النهائي :* {final_net:.2f} جنيه
*💵 المبلغ المدفوع  :* {paid_amount:.2f} جنيه
*📌 المتبقي المستحق :* {remain_amount:.2f} جنيه
━━━━━━━━━━━━━━━━━━
🙏 شكراً لثقتكم بنا ونتطلع لزيارتكم القادمة دائماً ❤️"""

        encoded = urllib.parse.quote(msg)
        url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded}"
        webbrowser.open(url)