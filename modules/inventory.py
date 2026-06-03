import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from database.db import connect
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
        # فلاتر البحث
        # =========================
        form = ctk.CTkFrame(self.frame)
        form.pack(pady=10, fill="x", padx=15)

        self.entries = {}

        labels = [
            ("اسم الصنف", "name", 5),
            ("الكود", "code", 4),
            ("المورد", "supplier", 3),
            ("من التاريخ", "date_from", 2),
            ("إلى التاريخ", "date_to", 1),
        ]

        for txt, key, col in labels:
            ctk.CTkLabel(form, text=txt).grid(row=0, column=col, sticky="e", padx=5, pady=2)

            if key in ("date_from", "date_to"):
                ent = DateEntry(form, width=18, background="#4f46e5", foreground="white",
                                borderwidth=2, font=("Arial", 10), date_pattern='yyyy-mm-dd')
                ent.delete(0, "end")
            else:
                ent = ctk.CTkEntry(
                    form,
                    width=140,
                    justify="right",
                    font=("Cairo", 12)
                )

            ent.grid(row=1, column=col, padx=5, pady=2)
            self.entries[key] = ent

        ctk.CTkButton(form, text="بحث", fg_color="#2563eb", width=120,
                      command=self.search_items).grid(row=1, column=0, padx=5, pady=2)
        ctk.CTkButton(form, text="مسح الفلاتر", fg_color="#64748b", width=120,
                      command=self.reset_filters).grid(row=0, column=0, padx=5, pady=2)

        # =========================
        # جدول
        # =========================
        self.table = ttk.Treeview(
            self.frame,
            columns=("code", "category", "name", "buy", "sale", "qty", "supplier",
                     "last_purchase_date", "last_sale_date", "last_return_date"),
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
            "last_purchase_date": "آخر طلب شراء",
            "last_sale_date": "آخر بيع",
            "last_return_date": "آخر مرتجع"
        }

        for col in self.table["columns"]:
            self.table.heading(col, text=headers[col])
            self.table.column(col, anchor="center", width=100)

        self.table.pack(fill="both", expand=True)
        self.load_data()

    # =========================
    # تحميل البيانات
    # =========================
    def load_data(self, filters: dict = None):

        self.table.delete(*self.table.get_children())

        query = """
            SELECT code, category, name, buy_price, sale_price, qty, supplier,
                   last_purchase_date, last_sale_date, last_return_date
            FROM items
            WHERE 1 = 1
        """
        params = []

        if filters:
            if filters.get("name"):
                query += " AND name LIKE ?"
                params.append(f"%{filters['name']}%")
            if filters.get("code"):
                query += " AND code LIKE ?"
                params.append(f"%{filters['code']}%")
            if filters.get("supplier"):
                query += " AND supplier LIKE ?"
                params.append(f"%{filters['supplier']}%")
            if filters.get("date_from"):
                query += " AND date(date) >= date(?)"
                params.append(filters["date_from"])
            if filters.get("date_to"):
                query += " AND date(date) <= date(?)"
                params.append(filters["date_to"])

        query += " ORDER BY date DESC, name COLLATE NOCASE"

        with connect() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            for row in cur.fetchall():
                self.table.insert("", "end", values=row)

    # =========================
    # بحث في المخزون
    # =========================
    def search_items(self):
        filters = {
            "name": self.entries["name"].get().strip(),
            "code": self.entries["code"].get().strip(),
            "supplier": self.entries["supplier"].get().strip(),
            "date_from": self.entries["date_from"].get().strip(),
            "date_to": self.entries["date_to"].get().strip()
        }
        self.load_data(filters)

    def reset_filters(self):
        self.entries["name"].delete(0, "end")
        self.entries["code"].delete(0, "end")
        self.entries["supplier"].delete(0, "end")
        self.entries["date_from"].delete(0, "end")
        self.entries["date_to"].delete(0, "end")
        self.load_data()

    # تعديل
    # =========================
