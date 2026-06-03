from datetime import datetime
import customtkinter as ctk
from tkinter import ttk, messagebox
from database.db import connect


class ProductsScreen(ctk.CTkFrame):
    """شاشة إدارة الأصناف - متوافقة مع CustomTkinter"""

    def __init__(self, parent, current_user=None, user_permissions=None):
        super().__init__(parent, fg_color="#f4f6f9", corner_radius=0)
        self.pack(fill="both", expand=True)
        self.current_user = current_user
        self.user_permissions = set(user_permissions or [])

        self.build_ui()
        self.load_categories()
        self.load_products()

    # =========================
    # UI
    # =========================
    def build_ui(self):

        # ── العنوان ────────────────────────────────────────────────
        title = ctk.CTkLabel(
            self,
            text="📦  إدارة الأصناف",
            font=("Cairo", 22, "bold"),
            text_color="#0f172a"
        )
        title.pack(pady=(20, 10))

        # ── إطار الإدخال ───────────────────────────────────────────
        form_frame = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12)
        form_frame.pack(fill="x", padx=30, pady=(0, 10))

        # صف 1: كود + اسم
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(15, 5))

        # اسم الصنف
        ctk.CTkLabel(row1, text="اسم الصنف", font=("Cairo", 13),
                     text_color="#374151").pack(side="right", padx=(10, 0))
        self.name_input = ctk.CTkEntry(
            row1, placeholder_text="اسم الصنف",
            font=("Cairo", 13), width=220,
            justify="right"
        )
        self.name_input.pack(side="right")

        # كود الصنف
        ctk.CTkLabel(row1, text="كود الصنف", font=("Cairo", 13),
                     text_color="#374151").pack(side="right", padx=(20, 0))
        self.code_input = ctk.CTkEntry(
            row1, placeholder_text="كود الصنف",
            font=("Cairo", 13), width=180,
            justify="right"
        )
        self.code_input.pack(side="right")

        # صف 2: التصنيف
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(5, 15))

        # زرار الحفظ
        save_btn = ctk.CTkButton(
            row2,
            text="💾  حفظ الصنف",
            font=("Cairo", 13, "bold"),
            fg_color="#4f46e5",
            hover_color="#3730a3",
            width=140,
            command=self.save_product
        )
        save_btn.pack(side="left", padx=(0, 20))

        # زرار إضافة تصنيف
        add_cat_btn = ctk.CTkButton(
            row2,
            text="+ تصنيف جديد",
            font=("Cairo", 12),
            fg_color="#10b981",
            hover_color="#059669",
            width=130,
            command=self.add_category
        )
        add_cat_btn.pack(side="left")

        # حقل التصنيف الجديد
        self.new_cat_input = ctk.CTkEntry(
            row2, placeholder_text="اسم تصنيف جديد",
            font=("Cairo", 13), width=180,
            justify="right"
        )
        self.new_cat_input.pack(side="right", padx=(10, 0))
        ctk.CTkLabel(row2, text="تصنيف جديد", font=("Cairo", 13),
                     text_color="#374151").pack(side="right")

        # ComboBox التصنيف
        ctk.CTkLabel(row2, text="التصنيف", font=("Cairo", 13),
                     text_color="#374151").pack(side="right", padx=(20, 0))
        self.category_combo = ctk.CTkComboBox(
            row2, font=("Cairo", 13), width=200,
            state="readonly"
        )
        self.category_combo.pack(side="right")

        # ── شريط البحث ─────────────────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=30, pady=(0, 8))

        self.search_input = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍  بحث بالكود أو الاسم ...",
            font=("Cairo", 13), width=300, justify="right"
        )
        self.search_input.pack(side="right")
        self.search_input.bind("<KeyRelease>", lambda e: self.load_products())

        # ── الجدول ─────────────────────────────────────────────────
        table_frame = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Products.Treeview",
            font=("Cairo", 12),
            rowheight=32,
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#1e293b"
        )
        style.configure(
            "Products.Treeview.Heading",
            font=("Cairo", 13, "bold"),
            background="#e0e7ff",
            foreground="#3730a3"
        )
        style.map("Products.Treeview", background=[("selected", "#c7d2fe")])

        cols = ("code", "name", "category", "created_at")
        self.table = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            style="Products.Treeview"
        )

        headings = {
            "code":       ("الكود",     120),
            "name":       ("الاسم",     220),
            "category":   ("التصنيف",  180),
            "created_at": ("التاريخ",  160),
        }
        for col, (label, width) in headings.items():
            self.table.heading(col, text=label, anchor="e")
            self.table.column(col, width=width, anchor="e")

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="left", fill="y")
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        # زرار حذف
        del_btn = ctk.CTkButton(
            self,
            text="🗑️  حذف الصنف المحدد",
            font=("Cairo", 12),
            fg_color="#ef4444",
            hover_color="#b91c1c",
            width=160,
            command=self.delete_product
        )
        del_btn.pack(pady=(0, 15))

    # =========================
    # Categories
    # =========================
    def load_categories(self):
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM categories ORDER BY name")
            data = [r[0] for r in cur.fetchall()]

        self.category_combo.configure(values=data)
        if data:
            self.category_combo.set(data[0])
        else:
            self.category_combo.set("")

    def add_category(self):
        name = self.new_cat_input.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "اكتب اسم التصنيف أولاً")
            return

        with connect() as conn:
            cur = conn.cursor()
            cur.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (name,))
            conn.commit()

        self.new_cat_input.delete(0, "end")
        self.load_categories()
        self.category_combo.set(name)

    # =========================
    # Save product
    # =========================
    def save_product(self):
        if "الأصناف" not in self.user_permissions:
            messagebox.showerror("صلاحية مفقودة", "ليس لديك صلاحية لحفظ الأصناف")
            return

        code     = self.code_input.get().strip()
        name     = self.name_input.get().strip()
        category = self.category_combo.get().strip()

        if not code or not name:
            messagebox.showwarning("تنبيه", "من فضلك ادخل الكود والاسم")
            return
        if not category:
            messagebox.showwarning("تنبيه", "من فضلك اختر أو أضف تصنيفاً أولاً")
            return

        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM items WHERE code=?", (code,))
            if cur.fetchone():
                messagebox.showwarning("تنبيه", "الكود موجود مسبقًا")
                return

            cur.execute("""
                INSERT INTO items (code, category, name, buy_price, sale_price, qty, supplier, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code, category, name, 0.0, 0.0, 0, "",
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ))
            conn.commit()

        self.code_input.delete(0, "end")
        self.name_input.delete(0, "end")
        self.load_products()
        messagebox.showinfo("نجاح", "✔  تم حفظ الصنف بنجاح")

    # =========================
    # Delete product
    # =========================
    def delete_product(self):
        if "الأصناف" not in self.user_permissions:
            messagebox.showerror("صلاحية مفقودة", "ليس لديك صلاحية لحذف الأصناف")
            return

        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("تنبيه", "اختر صنفاً من الجدول أولاً")
            return

        code = self.table.item(selected[0])["values"][0]
        confirm = messagebox.askyesno("تأكيد الحذف",
                                      f"هل تريد حذف الصنف بكود: {code} ؟")
        if not confirm:
            return

        with connect() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM items WHERE code=?", (code,))
            conn.commit()

        self.load_products()

    # =========================
    # Load products
    # =========================
    def load_products(self):
        keyword = self.search_input.get().strip() if hasattr(self, "search_input") else ""

        with connect() as conn:
            cur = conn.cursor()
            if keyword:
                cur.execute("""
                    SELECT code, name, category, date
                    FROM items
                    WHERE code LIKE ? OR name LIKE ?
                    ORDER BY id DESC
                """, (f"%{keyword}%", f"%{keyword}%"))
            else:
                cur.execute("""
                    SELECT code, name, category, date
                    FROM items ORDER BY id DESC
                """)
            rows = cur.fetchall()

        # مسح الجدول
        for row in self.table.get_children():
            self.table.delete(row)

        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            self.table.insert("", "end", values=row, tags=(tag,))

        self.table.tag_configure("even", background="#f8fafc")
        self.table.tag_configure("odd",  background="#ffffff")