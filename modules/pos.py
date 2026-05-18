import customtkinter as ctk
from tkinter import ttk, messagebox
from utils.arabic import ar
from utils.colors import COLORS
import webbrowser
from utils.pdf_utils import generate_invoice_pdf
from utils.whatsapp_utils import send_whatsapp_invoice
from database.db import save_invoice



class PosScreen:

    def __init__(self, parent):
        self.parent = parent
        self.build_ui()

    def build_ui(self):

        # =========================
        # الخلفية
        # =========================
        self.scroll = ctk.CTkScrollableFrame(
            self.parent,
            fg_color=COLORS["bg"]
        )
        self.scroll.pack(fill="both", expand=True)

        # =========================
        # بيانات العميل
        # =========================
        card = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"]
        )
        card.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            card,
            text=ar("بيانات العميل والطلب"),
            font=("Cairo", 18, "bold"),
            text_color=COLORS["text"]
        ).pack(anchor="e", padx=15, pady=10)

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=15, pady=10)

        for i in range(4):
            grid.grid_columnconfigure(i, weight=1)

        # =========================
        # 🔥 Validation Functions
        # =========================
        def validate_name(value):
            if value == "":
                return True
            # ❌ يمنع الأرقام
            return all(not char.isdigit() for char in value)

        def validate_phone(value):
            if value == "":
                return True
            # ❌ أرقام فقط
            return value.isdigit()

        vcmd_name = (self.parent.register(validate_name), "%P")
        vcmd_phone = (self.parent.register(validate_phone), "%P")

        # =========================
        # 🟢 اسم العميل
        # =========================
        ctk.CTkLabel(grid, text=ar("اسم العميل")).grid(row=0, column=3, sticky="e")

        self.name = ctk.CTkEntry(
            grid,
            justify="right",
            font=("Cairo", 12),
            validate="key",
            validatecommand=vcmd_name
        )
        self.name.grid(row=0, column=2, padx=5)

        # تثبيت اتجاه الكتابة
        self.name.bind("<FocusIn>", lambda e: self.name.icursor("end"))

        # =========================
        # 🟢 رقم الهاتف
        # =========================
        ctk.CTkLabel(grid, text=ar("رقم الهاتف")).grid(row=0, column=1, sticky="e")

        self.phone = ctk.CTkEntry(
            grid,
            justify="left",  # الأرقام LTR
            font=("Cairo", 12),
            validate="key",
            validatecommand=vcmd_phone
        )
        self.phone.grid(row=0, column=0, padx=5)

        # تثبيت المؤشر
        self.phone.bind("<FocusIn>", lambda e: self.phone.icursor("end"))

        # الصف الثاني
        ctk.CTkLabel(grid, text=ar("نوع النظارة")).grid(row=1, column=3, sticky="e")

        self.type = ctk.CTkComboBox(
            grid,
            values=[ar(x) for x in ["عدسات طبية", "عدسات شمسية", "عدسات لاصقة"]],
            justify="right"
        )
        self.type.grid(row=1, column=2, padx=5)

        ctk.CTkLabel(grid, text=ar("حالة الطلب")).grid(row=1, column=1, sticky="e")

        self.status = ctk.CTkComboBox(
            grid,
            values=[ar(x) for x in ["قيد التنفيذ", "جاهزة", "تم التسليم"]],
            justify="right"
        )
        self.status.grid(row=1, column=0, padx=5)

        # =========================
        # فحص النظر
        # =========================
        eye_card = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["card"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"]
        )
        eye_card.pack(fill="x", padx=15, pady=6)

        ctk.CTkLabel(
            eye_card,
            text=ar("مقاسات العدسات (فحص النظر)"),
            font=("Cairo", 15, "bold")
        ).pack(anchor="e", padx=12, pady=6)

        eye_grid = ctk.CTkFrame(eye_card, fg_color="transparent")
        eye_grid.pack(pady=4)

        headers = ["SPH", "CYL", "AXIS"]

        for i, h in enumerate(headers):
            ctk.CTkLabel(
                eye_grid,
                text=h,
                font=("Cairo", 10, "bold")
            ).grid(row=0, column=i + 1, padx=5)

        ctk.CTkLabel(eye_grid, text=ar("العين اليمنى")).grid(row=1, column=0)
        ctk.CTkLabel(eye_grid, text=ar("العين اليسرى")).grid(row=2, column=0)

        self.eye_entries = {}

        for r in range(2):
            for c in range(3):
                e = ctk.CTkEntry(
                    eye_grid,
                    width=55,
                    height=25,  # 🔥 تصغير الارتفاع
                    justify="center"
                )
                e.grid(row=r + 1, column=c + 1, padx=3, pady=3)
                self.eye_entries[(r, c)] = e

        # =========================
        # السلة
        # =========================
        cart = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["card"],
            corner_radius=20,
            border_width=1,
            border_color="#e0e3ea"
        )
        cart.pack(fill="x", padx=15, pady=6)

        ctk.CTkLabel(
            cart,
            text=ar("سلة المبيعات"),
            font=("Cairo", 16, "bold")
        ).pack(anchor="e", padx=15, pady=10)

        # شريط الإضافة
        top_bar = ctk.CTkFrame(cart, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            top_bar,
            text=ar("اختر الصنف:")
        ).pack(side="right", padx=5)

        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "TCombobox",
            fieldbackground="white",
            background="white",
            foreground="#2f3640",
            padding=5
        )

        self.item_combo = ttk.Combobox(
            top_bar,
            width=28,
            justify="right",
            font=("Cairo", 11)
        )
        self.item_combo.pack(side="right", padx=5)
        self.item_combo.bind("<<ComboboxSelected>>", self.update_preview)

        self.preview = ctk.CTkLabel(
            top_bar,
            text=ar("السعر: 0 | متاح: 0"),
            text_color=COLORS["info"]
        )
        self.preview.pack(side="right", padx=10)

        self.qty = ctk.CTkEntry(top_bar, width=50, justify="center")
        self.qty.insert(0, "1")
        self.qty.pack(side="left", padx=5)

        ctk.CTkButton(
            top_bar,
            text=ar("➕ إضافة"),
            fg_color=COLORS["success"],
            command=self.add_to_cart  # 🔥 هنا الربط
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            top_bar,
            text=ar("🗑️ مسح السلة"),
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self.clear_cart
        ).pack(side="left", padx=5)


        # جدول
        style = ttk.Style()
        style.theme_use("default")

        style.configure(
            "Treeview",
            background="white",
            foreground="#2f3640",
            rowheight=28,
            fieldbackground="white",
            bordercolor="#e4e6eb",
            borderwidth=1,
            font=("Cairo", 10)
        )

        style.configure(
            "Treeview.Heading",
            background="#f1f3f6",
            foreground="#2f3640",
            font=("Cairo", 11, "bold")
        )

        # 🔥 لون الصف عند التحديد
        style.map(
            "Treeview",
            background=[("selected", "#4a6cf7")],
            foreground=[("selected", "white")]
        )
        # 🔥 Frame يحتوي الجدول + السكرول
        table_frame = ctk.CTkFrame(
            cart,
            fg_color="white",
            corner_radius=10,
            border_width=1,
            border_color="#e4e6eb"
        )
        table_frame.pack(fill="x", padx=10, pady=5)
        # 🔥 خلي الأعمدة عربية (يمين → شمال)
        self.table = ttk.Treeview(
            table_frame,
            columns=("total", "qty", "price", "name", "code"),
            show="headings",
            height=4  # 🔥 أهم سطر
        )
        self.table.tag_configure("odd", background="#fafbfc")
        self.table.tag_configure("even", background="white")
        self.table.tag_configure("hover", background="#eef2ff")

        # 🔥 العناوين
        for col, txt in [
            ("code", "الكود"),
            ("name", "الصنف"),
            ("price", "السعر"),
            ("qty", "الكمية"),
            ("total", "الإجمالي")
        ]:
            self.table.heading(col, text=ar(txt))

        # 🔥 توزيع الأعمدة (برا اللوب مهم جدًا)
        self.table.column("code", anchor="e", width=100)  # يمين
        self.table.column("name", anchor="e", width=180)  # يمين
        self.table.column("price", anchor="center", width=100)
        self.table.column("qty", anchor="center", width=80)
        self.table.column("total", anchor="center", width=120)

        # 🔥 Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)

        # 🔥 ترتيبهم باستخدام pack (بدون grid خالص)
        self.table.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

        self.table.bind("<Delete>", self.delete_selected)

        # =========================
        # 🔥 Hover Effect
        # =========================
        def on_row_hover(event):
            row = self.table.identify_row(event.y)

            # رجع كل الصفوف لطبيعتها
            for i, item in enumerate(self.table.get_children()):
                tag = "even" if i % 2 == 0 else "odd"
                self.table.item(item, tags=(tag,))

            # طبق hover على صف واحد فقط
            if row:
                self.table.item(row, tags=("hover",))


        def on_leave(event):
            for i, item in enumerate(self.table.get_children()):
                tag = "even" if i % 2 == 0 else "odd"
                self.table.item(item, tags=(tag,))

        self.table.bind("<Motion>", on_row_hover)
        self.table.bind("<Leave>", on_leave)

        # =========================
        # الدفع (Ultra UI)
        # =========================

        pay = ctk.CTkFrame(
            self.scroll,
            fg_color="#ffffff",
            corner_radius=20,
            border_width=1,
            border_color="#e4e6eb"
        )

        pay.pack(fill="x", padx=15, pady=10)

        # 🔥 خط علوي خفيف (زي الصورة)
        top_line = ctk.CTkFrame(
            pay,
            height=4,
            fg_color=COLORS["primary"],
            corner_radius=5
        )
        top_line.pack(fill="x", padx=10, pady=(5, 8))

        # 🔥 Container داخلي
        container = ctk.CTkFrame(pay, fg_color="transparent")
        container.pack(fill="x", padx=10, pady=5)

        container.grid_columnconfigure(0, weight=1)  # الأزرار
        container.grid_columnconfigure(1, weight=0)  # المدفوع
        container.grid_columnconfigure(2, weight=1)  # الإجمالي

        # =========================
        # 🟢 الشمال (الأزرار)
        # =========================
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        save_btn = ctk.CTkButton(
            left,
            text=ar("حفظ وطباعة"),
            fg_color=COLORS["success"],
            hover_color="#1e8449",
            corner_radius=12,
            border_width=0,
            width=150,
            height=40,
            font=("Cairo", 13, "bold"),
            cursor="hand2"
        )

        save_btn.configure(
            command=lambda: [
                self.press_effect(save_btn),
                save_invoice(self),
                generate_invoice_pdf(self)
            ]
        )

        save_btn.pack(pady=3)

        whatsapp_btn = ctk.CTkButton(
            left,
            text=ar("واتساب"),
            fg_color="#25D366",
            hover_color="#1da851",
            corner_radius=12,
            width=150,
            height=40,
            font=("Cairo", 13, "bold"),
            cursor="hand2"
        )

        whatsapp_btn.configure(
            command=lambda: [self.press_effect(whatsapp_btn), send_whatsapp_invoice(self)]
        )

        whatsapp_btn.pack()

        # =========================
        # 🟡 الوسط (المدفوع)
        # =========================
        mid = ctk.CTkFrame(container, fg_color="transparent")
        mid.grid(row=0, column=1)

        ctk.CTkLabel(
            mid,
            text=ar("المدفوع"),
            font=("Cairo", 13, "bold"),
            text_color=COLORS["text"]
        ).pack()

        self.paid = ctk.CTkEntry(
            mid,
            width=160,
            height=40,
            justify="center",
            corner_radius=10,
            border_width=2
        )
        self.paid.pack(pady=5)

        def validate_number(value):
            if value == "":
                return True
            try:
                float(value)
                return True
            except:
                return False

        vcmd = (self.parent.register(validate_number), "%P")

        self.paid.configure(validate="key", validatecommand=vcmd)

        # 🔥 focus effect
        def on_focus_in(e):
            self.paid.configure(border_color=COLORS["primary"])

        def on_focus_out(e):
            self.paid.configure(border_color=COLORS["border"])

        self.paid.bind("<FocusIn>", on_focus_in)
        self.paid.bind("<FocusOut>", on_focus_out)
        self.paid.bind("<KeyRelease>", lambda e: self.update_remaining())

        # =========================
        # 🔵 اليمين (الإجمالي + المتبقي)
        # =========================
        right = ctk.CTkFrame(container, fg_color="transparent")
        right.grid(row=0, column=2, sticky="e")

        # 🔵 Box للإجمالي
        total_box = ctk.CTkFrame(
            right,
            fg_color="#eef2ff",  # 🔥 لون أهدى وأشيك
            corner_radius=14,
            border_width=1,
            border_color="#c7d2fe"
        )

        total_box.pack(anchor="e", pady=2)

        ctk.CTkFrame(
            total_box,
            height=3,
            fg_color="#4a6cf7",
            corner_radius=5
        ).pack(fill="x", side="bottom", pady=(3, 0))

        ctk.CTkLabel(
            total_box,
            text=ar("إجمالي الفاتورة"),
            font=("Cairo",18)
        ).pack(side="right", padx=5)

        ctk.CTkLabel(total_box, text=" : ").pack(side="right")

        self.total_value = ctk.CTkLabel(
            total_box,
            text="0.00",
            font=("Cairo",18, "bold"),
            text_color=COLORS["primary"]
        )
        self.total_value.pack(side="right", padx=5)

        # 🔴 Box للمتبقي
        self.remain_box = ctk.CTkFrame(
            right,
            fg_color="#fff5f5",
            corner_radius=15,
            border_width=1,
            border_color="#ffd6d6"
        )
        self.remain_box.pack(anchor="e", pady=3)

        ctk.CTkLabel(
            self.remain_box,
            text=ar("المتبقي"),
            font=("Cairo",18)
        ).pack(side="right", padx=5)

        ctk.CTkLabel(self.remain_box, text=" : ").pack(side="right")

        self.remain_value = ctk.CTkLabel(
            self.remain_box,
            text="0.00",
            font=("Cairo",18, "bold"),
            text_color="#e74c3c"
        )
        self.remain_value.pack(side="right", padx=5)

        # =========================
        # 🟡 الوسط (المدفوع)
        # =========================

    def update_preview(self, event=None):
        self.preview.configure(
            text=ar("السعر: 150 | متاح: 10"),
            text_color="#4a6cf7"
        )

    def add_to_cart(self):

        # اسم الصنف
        item_name = self.item_combo.get()

        if not item_name:
            return

        # الكمية
        try:
            qty = int(self.qty.get())
        except:
            qty = 1

        # 🔴 مؤقت (لحد ما نربط الداتابيز)
        price = 150

        total = price * qty

        # إضافة للجدول
        count = len(self.table.get_children())

        tag = "even" if count % 2 == 0 else "odd"

        self.table.insert(
            "",
            "end",
            values=(total, qty, price, item_name, "101"),
            tags=(tag,)
        )

        # تحديث الحسابات
        self.update_totals()

    def clear_cart(self):

        if not messagebox.askyesno("تأكيد", "هل تريد مسح السلة؟"):
            return
        # مسح كل الصفوف
        for item in self.table.get_children():
            self.table.delete(item)

        # تصفير الإجمالي
        self.final_total = 0
        self.total_value.configure(text="0.00")

        # تصفير المدفوع
        self.paid.delete(0, "end")

        # تصفير المتبقي
        self.remain_value.configure(text="0.00")
        self.remain_value.configure(text_color="#e74c3c")

        # رجوع لون البوكس الطبيعي
        self.remain_box.configure(
            fg_color="#fff5f5",
            border_color="#ffd6d6"
        )


    def update_totals(self):

        total = 0

        for item in self.table.get_children():
            total += float(self.table.item(item)["values"][0])

        self.final_total = total  # 🔥 نخزن القيمة الصح
        self.animate_total(total)

        # 🔥 فلاش بسيط
        self.total_value.configure(text_color="#27ae60")
        self.parent.after(300, lambda: self.total_value.configure(text_color=COLORS["primary"]))

        self.update_remaining()

    def update_remaining(self):

        try:
            total = getattr(self, "final_total", 0)  # 🔥 نجيب الإجمالي

            paid = float(self.paid.get()) if self.paid.get() else 0

            remain = total - paid  # 🔥 نحسب المتبقي

            self.remain_value.configure(text=f"{remain:.2f}")

            # 🔥 تغيير اللون
            if remain <= 0:
                # 🟢 مدفوع بالكامل
                self.remain_value.configure(text_color="#27ae60")
                self.remain_box.configure(fg_color="#eafaf1", border_color="#b7f5c5")

            else:
                # 🔴 لسه فيه فلوس
                self.remain_value.configure(text_color="#e74c3c")
                self.remain_box.configure(fg_color="#fff5f5", border_color="#ffd6d6")

        except:
            pass

    def press_effect(self, btn):
        original_width = btn.cget("width")
        original_height = btn.cget("height")

        # تصغير بسيط
        btn.configure(width=original_width - 5, height=original_height - 2)

        # رجوع للحجم الطبيعي
        self.parent.after(
            100,
            lambda: btn.configure(width=original_width, height=original_height)
        )

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

    def save_invoice(self):

        import json
        from datetime import datetime
        from tkinter import messagebox

        items = []

        for item in self.table.get_children():
            values = self.table.item(item)["values"]

            items.append({
                "name": values[3],
                "price": values[2],
                "qty": values[1],
                "total": values[0],
            })

        data = {
            "customer": self.name.get(),
            "phone": self.phone.get(),
            "total": getattr(self, "final_total", 0),
            "items": items,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        filename = f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        messagebox.showinfo("تم", "تم حفظ الفاتورة بنجاح")

    def print_invoice(self):

        import os

        text = "فاتورة محل نظارات\n\n"

        for item in self.table.get_children():
            values = self.table.item(item)["values"]
            text += f"{values[3]} - {values[1]} × {values[2]} = {values[0]}\n"

        text += f"\nالإجمالي: {getattr(self, 'final_total', 0):.2f}"

        with open("temp_invoice.txt", "w", encoding="utf-8") as f:
            f.write(text)

        os.startfile("temp_invoice.txt", "print")

    def delete_selected(self, event=None):

        selected = self.table.selection()

        if not selected:
            return

        from tkinter import messagebox

        if not messagebox.askyesno("تأكيد", "حذف الصنف المحدد؟"):
            return

        for item in selected:
            self.table.delete(item)

        self.update_totals()