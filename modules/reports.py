import customtkinter as ctk
from tkinter import ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib

import arabic_reshaper
from bidi.algorithm import get_display

from database.db import (
    get_reports_summary,
    get_top_items,
    get_last_invoices
)

matplotlib.rcParams['font.family'] = 'DejaVu Sans'


# دالة معالجة النصوص العربية الصافية
def ar(text):
    if not text:
        return ""
    return get_display(arabic_reshaper.reshape(str(text)))


class ReportsScreen:

    def __init__(self, parent):
        self.parent = parent

        # ألوان افتراضية احترافية متناسقة مع مظهر النظام الخارجي ومنعاً للأخطاء
        self.text_dark = "#1e293b"
        self.card_bg = "#ffffff"

        # 🌟 جعل الحاوية الداخلية للتقارير قابلة للتمرير بالكامل (CTkScrollableFrame)
        self.main_frame = ctk.CTkScrollableFrame(
            self.parent,
            fg_color="transparent",  # لكي تأخذ لون الخلفية الرمادي المريح للـ MainWindow
            corner_radius=0
        )
        # جعل الحاوية تفرش الشاشة كاملة أفقياً ورأسياً
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # الآن ابدأ بناء عناصر التقارير (الكروت، الجداول، الرسوم) داخل self.main_frame
        self.build_ui()

    def filter_data(self, selected_filter):
        self.update_dashboard(selected_filter)

    def build_ui(self):
        # =========================================================================
        # 🌟 تم ربط جميع العناصر بـ self.main_frame لتعمل داخل الـ Scrollbar بسلاسة
        # =========================================================================

        # ========================= 1. الشريط العلوي والفلاتر =========================
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=(0, 10))

        ctk.CTkLabel(
            header_frame,
            text=ar("لوحة التحكم / نظرة عامة على أداء نظامك"),
            font=("Cairo", 16, "bold"),
            text_color=self.text_dark
        ).pack(side="right")

        self.time_filter = ctk.CTkSegmentedButton(
            header_frame,
            values=["إجمالي", "شهري", "أسبوعي", "يومي"],
            command=self.filter_data,
            font=("Cairo", 11, "bold"),
            selected_color="#6366f1",
            selected_hover_color="#4f46e5",
            text_color=self.text_dark
        )
        self.time_filter.pack(side="left", padx=5)

        # ========================= 2. حاوية الكروت العلوية الرقمية =========================
        self.kpi_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.kpi_container.pack(fill="x", pady=5)

        # حجز مساحات مرنة وموزعة بالتساوي تماماً لمنع ضغط النصوص
        for i in range(7):
            self.kpi_container.grid_columnconfigure(i, weight=1, uniform="kpi")

        # ========================= 3. حاوية المخططات البيانية =========================
        self.charts_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.charts_container.pack(fill="x", pady=10)

        self.financial_card = ctk.CTkFrame(self.charts_container, fg_color=self.card_bg, corner_radius=12)
        self.financial_card.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.items_card = ctk.CTkFrame(self.charts_container, fg_color=self.card_bg, corner_radius=12)
        self.items_card.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # ========================= 4. الحاوية السفلية (الجدول والملخص الجانبي) =========================
        bottom_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        bottom_container.pack(fill="both", expand=True, pady=(5, 5))

        # جدول آخر الفواتير الصادرة
        table_card = ctk.CTkFrame(bottom_container, fg_color=self.card_bg, corner_radius=12)
        table_card.pack(side="right", fill="both", expand=True, padx=(10, 0))

        table_header_frame = ctk.CTkFrame(table_card, fg_color="transparent")
        table_header_frame.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(table_header_frame, text=ar("آخر الفواتير الصادرة"), font=("Cairo", 13, "bold"),
                     text_color=self.text_dark).pack(side="right")
        ctk.CTkLabel(table_header_frame, text="🧾", font=("Arial", 12)).pack(side="right", padx=(0, 5))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=30, font=("Arial", 10), background="#ffffff", fieldbackground="#ffffff",
                        borderwidth=0)
        style.configure("Treeview.Heading", font=("Cairo", 10, "bold"), background="#f8fafc", foreground="#64748b",
                        borderwidth=0)
        style.map("Treeview", background=[("selected", "#6366f1")], foreground=[("selected", "white")])

        table_wrapper = ctk.CTkFrame(table_card, fg_color="transparent")
        table_wrapper.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        columns = ("status", "remain", "paid", "discount", "total", "date", "customer", "id")
        self.table = ttk.Treeview(table_wrapper, columns=columns, show="headings", height=5)

        scrollbar = ctk.CTkScrollbar(table_wrapper, orientation="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.table.pack(side="left", fill="both", expand=True)

        headers = {
            "status": "الحالة", "remain": "المتبقي", "paid": "المدفوع",
            "discount": "الخصم", "total": "الصافي", "date": "التاريخ الفعلي",
            "customer": "العميل", "id": "رقم الفاتورة"
        }
        for col in columns:
            self.table.heading(col, text=ar(headers[col]))
            self.table.column(col, anchor="center", width=90)
        self.table.column("id", width=110)
        self.table.column("customer", width=120)
        self.table.tag_configure("even", background="#f8fafc")
        self.table.tag_configure("odd", background="#ffffff")

        # كرت الملخص المالي الجانبي المطور
        self.quick_summary_card = ctk.CTkFrame(bottom_container, fg_color=self.card_bg, corner_radius=12, width=290)
        self.quick_summary_card.pack(side="left", fill="both", padx=(0, 10))
        self.quick_summary_card.pack_propagate(False)

        # تشغيل الفلتر الافتراضي الأول
        self.time_filter.set("إجمالي")
        self.update_dashboard("إجمالي")

    def update_dashboard(self, filter_type):
        # تنظيف العناصر القديمة تماماً منعاً للتراكم
        for w in self.kpi_container.winfo_children(): w.destroy()
        for w in self.financial_card.winfo_children(): w.destroy()
        for w in self.items_card.winfo_children(): w.destroy()
        for w in self.quick_summary_card.winfo_children(): w.destroy()
        for item in self.table.get_children(): self.table.delete(item)

        # جلب البيانات المحدثة بمبالغ الخصم من قاعدة البيانات
        invoices_count, sales_after_discount, paid, remain, customers_period, items_count, total_discount = get_reports_summary(
            filter_type)

        # الحساب المالي لقيمة الفواتير قبل الخصم
        sales_before_discount = sales_after_discount + total_discount

        # 🟢 فصل المتغيرات عن النصوص لضمان قراءة عربية صحيحة 100%
        kpis = [
            (ar("إجمالي قبل الخصم"), f"{sales_before_discount:,.2f}", "💰", "#3b82f6",
             f"{ar('فواتير قبل الخصم')} ({ar(filter_type)})"),
            (ar("إجمالي الخصومات"), f"{total_discount:,.2f}", "🏷️", "#e11d48",
             f"{ar('خصومات الفواتير')} ({ar(filter_type)})"),
            (ar("الصافي (بعد الخصم)"), f"{sales_after_discount:,.2f}", "🛒", "#10b981",
             f"{ar('صافي المبيعات')} ({ar(filter_type)})"),
            (ar("إجمالي المدفوع"), f"{paid:,.2f}", "💵", "#6366f1", f"{ar('إجمالي المدفوعات')} ({ar(filter_type)})"),
            (ar("إجمالي المتبقي"), f"{remain:,.2f}", "💳", "#ef4444", f"{ar('إجمالي المستحقات')} ({ar(filter_type)})"),
            (ar("عدد العملاء"), str(customers_period), "👥", "#8b5cf6", f"{ar('العملاء النشطين')} ({ar(filter_type)})"),
            (ar("عدد الفواتير"), str(invoices_count), "🧾", "#64748b", f"{ar('الفواتير الصادرة')} ({ar(filter_type)})"),
        ]

        # 🟢 الحل السحري لعكس اتجاه الـ Grid ليصبح الترتيب صحيحاً من اليمين إلى اليسار
        total_kpis = len(kpis)
        for idx, (title, value, icon, color, subtext) in enumerate(kpis):
            card = ctk.CTkFrame(self.kpi_container, fg_color=self.card_bg, corner_radius=12, border_width=1,
                                border_color="#e2e8f0")

            reversed_column = (total_kpis - 1) - idx
            card.grid(row=0, column=reversed_column, padx=5, pady=5, sticky="nsew")

            ctk.CTkLabel(card, text=icon, font=("Arial", 18), text_color=color).pack(anchor="center", pady=(8, 2))
            ctk.CTkLabel(card, text=title, font=("Cairo", 11, "bold"), text_color="#64748b", justify="center").pack(
                anchor="center")
            ctk.CTkLabel(card, text=value, font=("Arial", 14, "bold"), text_color=self.text_dark,
                         justify="center").pack(anchor="center", pady=2)
            ctk.CTkLabel(card, text=subtext, font=("Cairo", 9), text_color=color, justify="center").pack(
                anchor="center", pady=(0, 8))

        # ========================= 🛠️ تنسيق وإزاحة الدائرة والمؤشرات الماليّة =========================
        fin_title_frame = ctk.CTkFrame(self.financial_card, fg_color="transparent")
        fin_title_frame.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(fin_title_frame, text=ar("التحليل المالي لصافي العمليات"), font=("Cairo", 13, "bold"),
                     text_color=self.text_dark).pack(side="right")

        fig1, ax1 = plt.subplots(figsize=(5, 2.5), subplot_kw=dict(aspect="equal"))
        sizes = [sales_after_discount, paid, remain] if sum([sales_after_discount, paid, remain]) > 0 else [1, 0, 0]
        colors = ['#10b981', '#6366f1', '#ef4444']

        # رسم الدائرة المجوفة بنصف قطر متناسق
        ax1.pie(sizes, colors=colors, startangle=90, wedgeprops=dict(width=0.3, edgecolor='w'), radius=0.9)

        # 🌟 [تعديل الإزاحة] دفع جسم الدائرة بالكامل إلى أقصى يسار الكرت (حرف الشاشة) لتوفير مساحة للكلام
        ax1.set_position([0.05, 0.05, 0.45, 0.9])

        # النص المركزي داخل الدائرة
        ax1.text(0, -0.05, f"{sales_after_discount:,.0f}\n" + ar("الصافي"), ha='center', va='center', fontsize=9,
                 weight='bold', color=self.text_dark)

        total_all = sum(sizes) if sum(sizes) > 0 else 1

        # 🌟 [تنسيق الكلمات] محاذاة عمودية ودفع النصوص لأقصى اليمين بعيداً تماماً عن الدائرة لمنع التداخل
        x_text_position = 1.65

        ax1.text(x_text_position, 0.45,
                 f"{(sales_after_discount / total_all) * 100:.1f}%   {sales_after_discount:,.2f}   " + ar("الصافي"),
                 va='center', ha='left', fontsize=9, color='#10b981', weight='bold')

        ax1.text(x_text_position, 0.0,
                 f"{(paid / total_all) * 100:.1f}%   {paid:,.2f}   " + ar("المدفوع"),
                 va='center', ha='left', fontsize=9, color='#6366f1', weight='bold')

        ax1.text(x_text_position, -0.45,
                 f"{(remain / total_all) * 100:.1f}%   {remain:,.2f}   " + ar("المتبقي"),
                 va='center', ha='left', fontsize=9, color='#ef4444', weight='bold')

        fig1.patch.set_facecolor('none')
        ax1.set_facecolor('none')
        canvas1 = FigureCanvasTkAgg(fig1, self.financial_card)
        canvas1.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=2)
        plt.close(fig1)

        # ========================= مخطط أفضل الأصناف مبيعاً =========================
        itm_title_frame = ctk.CTkFrame(self.items_card, fg_color="transparent")
        itm_title_frame.pack(fill="x", padx=15, pady=8)
        ctk.CTkLabel(itm_title_frame, text=ar("أفضل الأصناف مبيعاً"), font=("Cairo", 13, "bold"),
                     text_color=self.text_dark).pack(side="right")

        top_items = get_top_items(filter_type)
        item_names = [ar(i[0]) for i in top_items]
        item_qtys = [i[1] for i in top_items]

        fig2, ax2 = plt.subplots(figsize=(4, 2.3))
        if item_qtys:
            ax2.bar(item_names, item_qtys, color="#6366f1", width=0.35)
            ax2.set_xticks(range(len(item_names)))
            ax2.set_xticklabels(item_names, fontdict={'size': 9, 'weight': 'bold'})
        else:
            ax2.text(0.5, 0.5, ar("لا توجد مبيعات في هذه الفترة"), ha='center', va='center', fontsize=11,
                     color='#64748b')
            ax2.set_xlim(0, 1)
            ax2.set_ylim(0, 1)

        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        fig2.patch.set_facecolor('none')
        ax2.set_facecolor('none')
        canvas2 = FigureCanvasTkAgg(fig2, self.items_card)
        canvas2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=2)
        plt.close(fig2)

        # تعبئة الجدول بالبيانات الدقيقة
        for i, row in enumerate(get_last_invoices(filter_type)):
            status_text = "مدفوعة" if float(row[5]) == 0 else "متبقي"
            self.table.insert("", "end", values=(
                ar(status_text), f"{row[5]:,.2f}", f"{row[4]:,.2f}", f"{row[3]:,.2f}",
                f"{row[2]:,.2f}", row[6], ar(row[1]), row[0]
            ), tags=("even" if i % 2 == 0 else "odd",))

        # ========================= ملخص المسار المالي الجانبي =========================
        summary_title_frame = ctk.CTkFrame(self.quick_summary_card, fg_color="transparent")
        summary_title_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(summary_title_frame, text=ar("ملخص المسار المالي الحالي"), font=("Cairo", 12, "bold"),
                     text_color=self.text_dark).pack(side="right")

        summary_list = [
            (f"{sales_before_discount:,.2f}", ar("إجمالي قبل الخصم"), "💰"),
            (f"{total_discount:,.2f}", ar("إجمالي الخصومات"), "🏷️"),
            (f"{sales_after_discount:,.2f}", ar("الصافي (بعد الخصم)"), "🛒"),
            (f"{paid:,.2f}", ar("إجمالي المدفوع"), "🟢"),
            (f"{remain:,.2f}", ar("إجمالي المتبقي"), "🔴"),
            (str(invoices_count), ar("عدد الفواتير"), "📄")
        ]
        for val, title, icon in summary_list:
            rf = ctk.CTkFrame(self.quick_summary_card, fg_color="transparent")
            rf.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(rf, text=val, font=("Arial", 11, "bold"), text_color=self.text_dark).pack(side="left")
            lt = ctk.CTkFrame(rf, fg_color="transparent")
            lt.pack(side="right")
            ctk.CTkLabel(lt, text=title, font=("Cairo", 10), text_color="#64748b").pack(side="right")
            ctk.CTkLabel(lt, text=icon, font=("Arial", 10)).pack(side="right", padx=(0, 3))