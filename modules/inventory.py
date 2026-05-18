import customtkinter as ctk
from tkinter import ttk, messagebox
from database.db import connect, add_item, delete_item, update_item, get_categories
from datetime import datetime
from utils.arabic import ar


class InventoryScreen:

    def __init__(self, parent):
        self.parent = parent
        self.build_ui()

    def build_ui(self):

        self.frame = ctk.CTkFrame(self.parent)
        self.frame.pack(fill="both", expand=True)

        title = ctk.CTkLabel(self.frame, text="إدارة المخزون", font=("Cairo", 20, "bold"))
        title.pack(pady=10)

        # =========================
        # الإدخال
        # =========================
        form = ctk.CTkFrame(self.frame)
        form.pack(pady=10)

        self.entries = {}

        # 🔥 إضافة category
        fields = [
            ("الكود", "code"),
            ("جروب الصنف", "category"),   # 🟢 جديد
            ("اسم الصنف", "name"),       # 🔵 بقى Entry
            ("سعر الشراء", "buy"),
            ("سعر البيع", "sale"),
            ("الكمية", "qty"),
            ("المورد", "supplier"),
        ]

        for i, (txt, key) in enumerate(fields):

            ctk.CTkLabel(form, text=txt).grid(row=0, column=i)

            # =========================
            # 🟢 جروب الصنف = ComboBox
            # =========================
            if key == "category":

                categories = [ar(x) for x in get_categories()]

                ent = ctk.CTkComboBox(
                    form,
                    values=categories,
                    width=140,
                    justify="right"
                )

                if categories:
                    ent.set(categories[0])

            # =========================
            # 🔵 باقي الحقول = Entry
            # =========================
            else:

                ent = ctk.CTkEntry(
                    form,
                    width=120,
                    justify="right",
                    font=("Cairo", 12)
                )

                # 🔥 Validation
                if key == "qty":
                    vcmd = (self.parent.register(lambda v: v.isdigit() or v == ""), "%P")
                    ent.configure(validate="key", validatecommand=vcmd)

                elif key in ["buy", "sale"]:
                    vcmd = (self.parent.register(lambda v: v.replace(".", "", 1).isdigit() or v == ""), "%P")
                    ent.configure(validate="key", validatecommand=vcmd)

            ent.grid(row=1, column=i, padx=5)

            # اتجاه الكتابة
            ent.bind("<FocusIn>", lambda e, entry=ent: entry.icursor("end"))

            self.entries[key] = ent

        # =========================
        # أزرار
        # =========================
        btns = ctk.CTkFrame(self.frame)
        btns.pack(pady=10)

        ctk.CTkButton(btns, text="➕ إضافة", command=self.add).pack(side="right", padx=5)
        ctk.CTkButton(btns, text="✏️ تعديل", command=self.update).pack(side="right", padx=5)
        ctk.CTkButton(btns, text="❌ حذف", command=self.delete).pack(side="right", padx=5)

        # =========================
        # جدول
        # =========================
        self.table = ttk.Treeview(
            self.frame,
            columns=("code", "category", "name", "buy", "sale", "qty", "supplier", "date"),
            show="headings"
        )

        headers = {
            "code": "الكود",
            "category": "جروب الصنف",
            "name": "اسم الصنف",
            "buy": "سعر الشراء",
            "sale": "سعر البيع",
            "qty": "الكمية",
            "supplier": "المورد",
            "date": "التاريخ"
        }

        for col in self.table["columns"]:
            self.table.heading(col, text=headers[col])
            self.table.column(col, anchor="center", width=100)

        self.table.pack(fill="both", expand=True)

        self.table.bind("<<TreeviewSelect>>", self.fill_fields)

        self.load_data()

    # =========================
    # تحميل البيانات
    # =========================
    def load_data(self):

        self.table.delete(*self.table.get_children())

        conn = connect()
        cur = conn.cursor()

        # 🔥 لازم تضيف category في الداتابيز
        cur.execute("""
            SELECT code, category, name, buy_price, sale_price, qty, supplier, date 
            FROM items
        """)

        for row in cur.fetchall():
            self.table.insert("", "end", values=row)

        conn.close()

    # =========================
    # إضافة
    # =========================
    def add(self):

        try:
            data = (
                self.entries["code"].get(),
                self.entries["category"].get(),  # 🟢 جديد
                self.entries["name"].get(),
                float(self.entries["buy"].get() or 0),
                float(self.entries["sale"].get() or 0),
                int(self.entries["qty"].get() or 0),
                self.entries["supplier"].get(),
                datetime.now().strftime("%Y-%m-%d")
            )

            conn = connect()
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO items 
                (code, category, name, buy_price, sale_price, qty, supplier, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

            conn.commit()
            conn.close()

            self.load_data()
            messagebox.showinfo("تم", "تمت الإضافة")

        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    # =========================
    # حذف
    # =========================
    def delete(self):

        selected = self.table.selection()

        if not selected:
            return

        code = self.table.item(selected[0])["values"][0]

        delete_item(code)
        self.load_data()

    # =========================
    # تعديل
    # =========================
    def update(self):

        try:
            conn = connect()
            cur = conn.cursor()

            cur.execute("""
                UPDATE items
                SET category=?, name=?, buy_price=?, sale_price=?, qty=?, supplier=?
                WHERE code=?
            """, (
                self.entries["category"].get(),
                self.entries["name"].get(),
                float(self.entries["buy"].get() or 0),
                float(self.entries["sale"].get() or 0),
                int(self.entries["qty"].get() or 0),
                self.entries["supplier"].get(),
                self.entries["code"].get()
            ))

            conn.commit()
            conn.close()

            self.load_data()

        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    # =========================
    # تعبئة الحقول
    # =========================
    def fill_fields(self, event=None):

        selected = self.table.selection()

        if not selected:
            return

        values = self.table.item(selected[0])["values"]

        keys = ["code", "category", "name", "buy", "sale", "qty", "supplier"]

        for i, key in enumerate(keys):

            widget = self.entries[key]

            if isinstance(widget, ctk.CTkComboBox):
                widget.set(values[i])
            else:
                widget.delete(0, "end")
                widget.insert(0, values[i])