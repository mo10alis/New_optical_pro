import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from database.db import connect
from utils.colors import COLORS


class MovementsScreen:
    """شاشة حركات المخزون - الواردات والمنصرفات"""

    def __init__(self, parent):
        self.parent = parent
        self.build_ui()
        self.load_data()

    def build_ui(self):
        self.frame = ctk.CTkFrame(self.parent, fg_color=COLORS["bg"], corner_radius=0)
        self.frame.pack(fill="both", expand=True)

        # ── العنوان ──────────────────────────────────
        ctk.CTkLabel(
            self.frame,
            text="🔃  حركات المخزون",
            font=("Cairo", 20, "bold"),
            text_color="#0f172a"
        ).pack(pady=(15, 8))

        # ── فورم الإدخال ──────────────────────────────
        form = ctk.CTkFrame(self.frame, fg_color="#ffffff", corner_radius=12)
        form.pack(fill="x", padx=20, pady=(0, 8))

        row = ctk.CTkFrame(form, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=12)

        # نوع الحركة
        ctk.CTkLabel(row, text="نوع الحركة", font=("Cairo", 12), text_color="#374151").pack(side="right", padx=(10, 0))
        self.movement_type = ctk.CTkComboBox(
            row,
            values=["وارد", "منصرف", "تعديل"],
            font=("Cairo", 12), width=120, state="readonly"
        )
        self.movement_type.set("وارد")
        self.movement_type.pack(side="right", padx=5)

        # الكود
        ctk.CTkLabel(row, text="كود الصنف", font=("Cairo", 12), text_color="#374151").pack(side="right", padx=(10, 0))
        self.code_input = ctk.CTkEntry(row, placeholder_text="كود الصنف", font=("Cairo", 12), width=140, justify="right")
        self.code_input.pack(side="right", padx=5)

        # الكمية
        ctk.CTkLabel(row, text="الكمية", font=("Cairo", 12), text_color="#374151").pack(side="right", padx=(10, 0))
        self.qty_input = ctk.CTkEntry(row, placeholder_text="الكمية", font=("Cairo", 12), width=100, justify="center")
        self.qty_input.pack(side="right", padx=5)

        # ملاحظات
        ctk.CTkLabel(row, text="ملاحظات", font=("Cairo", 12), text_color="#374151").pack(side="right", padx=(10, 0))
        self.notes_input = ctk.CTkEntry(row, placeholder_text="ملاحظات اختيارية", font=("Cairo", 12), width=180, justify="right")
        self.notes_input.pack(side="right", padx=5)

        # زرار الحفظ
        ctk.CTkButton(
            row,
            text="💾 تسجيل الحركة",
            font=("Cairo", 12, "bold"),
            fg_color="#4f46e5",
            hover_color="#3730a3",
            width=140,
            command=self.save_movement
        ).pack(side="left", padx=5)

        # ── الجدول ──────────────────────────────────
        table_frame = ctk.CTkFrame(self.frame, fg_color="#ffffff", corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Mov.Treeview", font=("Cairo", 11), rowheight=30,
                        background="#ffffff", fieldbackground="#ffffff", foreground="#1e293b")
        style.configure("Mov.Treeview.Heading", font=("Cairo", 12, "bold"),
                        background="#e0e7ff", foreground="#3730a3")
        style.map("Mov.Treeview", background=[("selected", "#c7d2fe")])

        cols = ("date", "code", "name", "type", "qty", "notes")
        self.table = ttk.Treeview(table_frame, columns=cols, show="headings", style="Mov.Treeview")

        headers = {
            "date":  ("التاريخ",     140),
            "code":  ("الكود",       100),
            "name":  ("الصنف",       200),
            "type":  ("نوع الحركة",  110),
            "qty":   ("الكمية",       80),
            "notes": ("ملاحظات",     200),
        }
        for col, (label, width) in headers.items():
            self.table.heading(col, text=label, anchor="center")
            self.table.column(col, width=width, anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.table.pack(fill="both", expand=True, padx=8, pady=8)

    def save_movement(self):
        code  = self.code_input.get().strip()
        qty_s = self.qty_input.get().strip()
        mtype = self.movement_type.get().strip()
        notes = self.notes_input.get().strip()

        if not code or not qty_s:
            messagebox.showwarning("تنبيه", "أدخل كود الصنف والكمية")
            return

        try:
            qty = int(qty_s)
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("تنبيه", "الكمية يجب أن تكون رقماً موجباً")
            return

        try:
            with connect() as conn:
                cur = conn.cursor()

                # تحقق من وجود الصنف
                cur.execute("SELECT name, qty FROM items WHERE code=?", (code,))
                row = cur.fetchone()
                if not row:
                    messagebox.showerror("خطأ", f"لا يوجد صنف بالكود: {code}")
                    return

                item_name = row[0]
                try:
                    current_qty = int(row[1] or 0)
                except Exception:
                    current_qty = 0

                # تحديث الكمية حسب نوع الحركة
                if mtype == "وارد":
                    new_qty = current_qty + qty
                elif mtype == "منصرف":
                    if qty > current_qty:
                        messagebox.showerror("خطأ", f"الكمية المطلوبة ({qty}) أكبر من المتاح ({current_qty})")
                        return
                    new_qty = current_qty - qty
                else:  # تعديل
                    new_qty = qty

                cur.execute("UPDATE items SET qty=? WHERE code=?", (new_qty, code))

                # حفظ الحركة في جدول مخصص
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS stock_movements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        code TEXT,
                        name TEXT,
                        type TEXT,
                        qty INTEGER,
                        notes TEXT
                    )
                """)
                cur.execute("""
                    INSERT INTO stock_movements (date, code, name, type, qty, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (datetime.now().strftime("%Y-%m-%d %H:%M"), code, item_name, mtype, qty, notes))

                conn.commit()

            self.code_input.delete(0, "end")
            self.qty_input.delete(0, "end")
            self.notes_input.delete(0, "end")

            self.load_data()
            messagebox.showinfo("نجاح", f"✔ تم تسجيل الحركة - الكمية الجديدة: {new_qty}")

        except Exception as e:
            messagebox.showerror("خطأ", str(e))

    def load_data(self):
        for row in self.table.get_children():
            self.table.delete(row)

        try:
            conn = connect()
            cur  = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    code TEXT,
                    name TEXT,
                    type TEXT,
                    qty INTEGER,
                    notes TEXT
                )
            """)
            cur.execute("""
                SELECT date, code, name, type, qty, notes
                FROM stock_movements
                ORDER BY id DESC
            """)
            rows = cur.fetchall()
            conn.close()

            for i, row in enumerate(rows):
                tag = "even" if i % 2 == 0 else "odd"
                self.table.insert("", "end", values=row, tags=(tag,))

            self.table.tag_configure("even", background="#f8fafc")
            self.table.tag_configure("odd",  background="#ffffff")

        except Exception:
            # الجدول لم يُنشأ بعد — طبيعي في أول تشغيل
            pass
