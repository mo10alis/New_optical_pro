import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
from database.db import connect


class SupplierScreen:
    def __init__(self, parent):
        self.parent = parent
        self.font_ar = ("Tahoma", 14)

        self.create_or_upgrade_database()
        self.build_ui()

    # ==================================
    # إنشاء أو ترقية قاعدة البيانات
    # ==================================
    def create_or_upgrade_database(self):
        with connect() as conn:
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT,
                    city TEXT,
                    type TEXT
                )
            """)

        # فحص الأعمدة الحالية
        cur.execute("PRAGMA table_info(suppliers)")
        columns = [column[1] for column in cur.fetchall()]

        # إضافة created_at إذا لم يكن موجودًا
        if "created_at" not in columns:
            cur.execute(
                "ALTER TABLE suppliers ADD COLUMN created_at TEXT"
            )

            cur.execute("""
                UPDATE suppliers
                SET created_at = datetime('now','localtime')
                WHERE created_at IS NULL
            """)

            conn.commit()

    # ==================================
    # واجهة المستخدم
    # ==================================
    def build_ui(self):
        self.frame = ctk.CTkFrame(self.parent)
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        # -------------------------
        # قسم الإدخال
        # -------------------------
        input_frame = ctk.CTkFrame(self.frame)
        input_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(
            input_frame,
            text="تسجيل مورد جديد",
            font=("Tahoma", 18, "bold")
        ).pack(pady=10)

        # اسم المورد
        ctk.CTkLabel(
            input_frame,
            text="اسم المورد",
            font=self.font_ar
        ).pack(anchor="e", padx=20)

        self.name_entry = ctk.CTkEntry(
            input_frame,
            width=350,
            justify="right",
            font=self.font_ar
        )
        self.name_entry.pack(pady=5)

        # الهاتف
        ctk.CTkLabel(
            input_frame,
            text="رقم الهاتف",
            font=self.font_ar
        ).pack(anchor="e", padx=20)

        vcmd = (
            self.parent.register(
                lambda p: p.isdigit() or p == ""
            ),
            "%P"
        )

        self.phone_entry = ctk.CTkEntry(
            input_frame,
            width=350,
            justify="right",
            font=self.font_ar,
            validate="key",
            validatecommand=vcmd
        )
        self.phone_entry.pack(pady=5)

        # المحافظات
        self.cities = [
            "القاهرة", "الجيزة", "الإسكندرية", "الدقهلية",
            "الشرقية", "المنوفية", "القليوبية", "البحيرة",
            "الغربية", "كفر الشيخ", "الفيوم", "بني سويف",
            "المنيا", "أسيوط", "سوهاج", "قنا",
            "الأقصر", "أسوان", "بورسعيد", "دمياط",
            "الإسماعيلية", "السويس", "مطروح",
            "شمال سيناء", "جنوب سيناء",
            "البحر الأحمر", "الوادي الجديد"
        ]

        ctk.CTkLabel(
            input_frame,
            text="المحافظة",
            font=self.font_ar
        ).pack(anchor="e", padx=20)

        self.city_menu = ttk.Combobox(
            input_frame,
            values=self.cities,
            width=40,
            justify="right",
            font=("Tahoma", 11)
        )
        self.city_menu.set("اختر المحافظة")
        self.city_menu.pack(pady=5)

        # التصنيف
        ctk.CTkLabel(
            input_frame,
            text="التصنيف",
            font=self.font_ar
        ).pack(anchor="e", padx=20)

        self.type_menu = ttk.Combobox(
            input_frame,
            values=[
                "شركة",
                "مورد حر",
                "شراء ذاتي"
            ],
            width=40,
            justify="right",
            font=("Tahoma", 11)
        )
        self.type_menu.set("اختر التصنيف")
        self.type_menu.pack(pady=5)

        # زر الحفظ
        ctk.CTkButton(
            input_frame,
            text="حفظ المورد",
            command=self.save_supplier
        ).pack(pady=15)

        # -------------------------
        # الجدول
        # -------------------------
        style = ttk.Style()
        style.configure(
            "Treeview",
            font=("Tahoma", 11),
            rowheight=28
        )

        style.configure(
            "Treeview.Heading",
            font=("Tahoma", 11, "bold")
        )

        self.tree = ttk.Treeview(
            self.frame,
            columns=(
                "date",
                "type",
                "city",
                "phone",
                "name"
            ),
            show="headings"
        )

        self.tree.heading("date", text="تاريخ الإضافة")
        self.tree.heading("type", text="التصنيف")
        self.tree.heading("city", text="المحافظة")
        self.tree.heading("phone", text="الهاتف")
        self.tree.heading("name", text="اسم المورد")

        self.tree.column("date", width=150, anchor="e")
        self.tree.column("type", width=120, anchor="e")
        self.tree.column("city", width=150, anchor="e")
        self.tree.column("phone", width=130, anchor="e")
        self.tree.column("name", width=250, anchor="e")

        self.tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        self.load_suppliers()

    # ==================================
    # حفظ المورد
    # ==================================
    def save_supplier(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        city = self.city_menu.get().strip()
        supplier_type = self.type_menu.get().strip()

        if not name:
            messagebox.showwarning(
                "تنبيه",
                "يرجى إدخال اسم المورد"
            )
            return

        if not phone:
            messagebox.showwarning(
                "تنبيه",
                "يرجى إدخال رقم هاتف المورد"
            )
            return

        if city == "اختر المحافظة" or city not in self.cities:
            messagebox.showwarning(
                "تنبيه",
                "يرجى اختيار المحافظة"
            )
            return

        if supplier_type == "اختر التصنيف" or supplier_type not in ["شركة", "مورد حر", "شراء ذاتي"]:
            messagebox.showwarning(
                "تنبيه",
                "يرجى اختيار تصنيف المورد"
            )
            return

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )

        try:
            with connect() as conn:
                cur = conn.cursor()

                cur.execute("SELECT id FROM suppliers WHERE name = ? OR phone = ?", (name, phone))
                if cur.fetchone():
                    messagebox.showwarning(
                        "تنبيه",
                        "المورد موجود بالفعل بنفس الاسم أو رقم الهاتف"
                    )
                    return

                cur.execute("""
                    INSERT INTO suppliers
                    (
                        name,
                        phone,
                        city,
                        type,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    name,
                    phone,
                    city,
                    supplier_type,
                    created_at
                ))
                conn.commit()

            messagebox.showinfo(
                "نجاح",
                "تم حفظ المورد بنجاح"
            )

            self.name_entry.delete(0, "end")
            self.phone_entry.delete(0, "end")

            self.city_menu.set("اختر المحافظة")
            self.type_menu.set("اختر التصنيف")

            self.load_suppliers()

        except Exception as e:
            messagebox.showerror(
                "خطأ",
                str(e)
            )

    # ==================================
    # تحميل الموردين
    # ==================================
    def load_suppliers(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        with connect() as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT
                    created_at,
                    type,
                    city,
                    phone,
                    name
                FROM suppliers
                ORDER BY id DESC
            """)

            rows = cur.fetchall()

        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=row
            )

        conn.close()