import logging
import customtkinter as ctk
from tkinter import ttk, messagebox
from utils.colors import COLORS
from database.db import (
    add_customer as db_add_customer,
    get_customers,
    delete_customer,
    update_customer,
)

logger = logging.getLogger(__name__)

class CustomersScreen:

    def __init__(self, parent, current_user=None, user_permissions=None):
        self.parent = parent
        self.selected_id = None
        self.current_user = current_user
        self.user_permissions = set(user_permissions or [])
        self.build_ui()
        self.load_data()

    def build_ui(self):

        self.frame = ctk.CTkFrame(self.parent, fg_color=COLORS["bg"])
        self.frame.pack(fill="both", expand=True)

        # =========================
        # الفورم
        # =========================
        form = ctk.CTkFrame(self.frame, fg_color=COLORS["card"])
        form.pack(fill="x", padx=10, pady=10)

        # استخدم CTkEntry لكل الحقول لظهور موحد
        self.name = ctk.CTkEntry(form, placeholder_text="الاسم", justify="right", font=("Cairo", 14))
        self.name.pack(side="right", padx=5)

        self.phone = ctk.CTkEntry(form, placeholder_text="رقم الهاتف", justify="center")
        self.phone.pack(side="right", padx=5)

        self.notes = ctk.CTkEntry(form, placeholder_text="ملاحظات", justify="right")
        self.notes.pack(side="right", padx=5)

        self.discount = ctk.CTkEntry(form, placeholder_text="الخصم %", width=120, justify="center")
        self.discount.insert(0, "0")
        self.discount.pack(side="right", padx=5)

        ctk.CTkButton(form, text="➕ إضافة", fg_color=COLORS["success"],
                      command=self.add_customer).pack(side="right", padx=5)

        ctk.CTkButton(form, text="✏ تعديل", fg_color="#f39c12",
                      command=self.update_customer).pack(side="right", padx=5)

        ctk.CTkButton(form, text="🗑 حذف", fg_color="red",
                      command=self.delete_customer).pack(side="right", padx=5)

        # =========================
        # 🔍 البحث
        # =========================
        search_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=10)

        self.search_var = ctk.StringVar()

        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="بحث بالاسم أو الرقم...",
            textvariable=self.search_var
        )
        search_entry.pack(side="right", padx=5)
        search_entry.bind("<KeyRelease>", self.filter_customers)

        # =========================
        # الجدول
        # =========================
        self.table = ttk.Treeview(
            self.frame,
            columns=("id", "name", "phone", "notes", "discount"),
            show="headings"
        )

        for col, txt in [
            ("id", "ID"),
            ("name", "الاسم"),
            ("phone", "الهاتف"),
            ("notes", "ملاحظات"),
            ("discount", "الخصم %")
        ]:
            self.table.heading(col, text=txt)
            # ضبط عرض افتراضي مقبول
            if col == "id":
                self.table.column(col, width=60, anchor="center")
            elif col == "discount":
                self.table.column(col, width=80, anchor="center")
            else:
                self.table.column(col, width=150, anchor="w")

        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        self.table.bind("<<TreeviewSelect>>", self.select_row)

    def load_data(self):
        try:
            for item in self.table.get_children():
                self.table.delete(item)

            for row in get_customers():
                self.table.insert("", "end", values=row)
        except Exception:
            logger.exception("Failed to load customers")
            messagebox.showerror("خطأ", "فشل في جلب بيانات العملاء")

    def filter_customers(self, event=None):
        keyword = (self.search_var.get() or "").strip().lower()

        try:
            for item in self.table.get_children():
                self.table.delete(item)

            for row in get_customers():
                name = (row[1] or "").lower()
                phone = (row[2] or "").lower()
                if not keyword or keyword in name or keyword in phone:
                    self.table.insert("", "end", values=row)
        except Exception:
            logger.exception("Failed to filter customers")
            messagebox.showerror("خطأ", "حدث خطأ أثناء البحث")

    def select_row(self, event):
        selected = self.table.focus()
        if not selected:
            return

        data = self.table.item(selected).get("values") or []
        if len(data) < 5:
            return

        self.selected_id = data[0]

        self.name.delete(0, "end")
        self.name.insert(0, data[1])

        self.phone.delete(0, "end")
        self.phone.insert(0, data[2])

        self.notes.delete(0, "end")
        self.notes.insert(0, data[3])

        self.discount.delete(0, "end")
        self.discount.insert(0, data[4])

    def add_customer(self):
        # تحقق الصلاحية
        if "العملاء" not in self.user_permissions:
            messagebox.showerror("صلاحية مفقودة", "ليس لديك صلاحية لإضافة عملاء")
            return

        name = (self.name.get() or "").strip()
        phone = (self.phone.get() or "").strip()
        notes = (self.notes.get() or "").strip()

        try:
            discount = float(self.discount.get() or 0)
        except ValueError:
            discount = 0

        if not name or not phone:
            messagebox.showwarning("تنبيه", "أدخل الاسم ورقم الهاتف")
            return

        try:
            db_add_customer(name, phone, notes, discount)
            messagebox.showinfo("تم", "تم إضافة العميل")
        except Exception:
            logger.exception("Failed to add customer")
            messagebox.showerror("خطأ", "تعذر إضافة العميل (راجع السجل)")

        self.load_data()
        self.clear_form()
        self.name.focus()

    def update_customer(self):

        if "العملاء" not in self.user_permissions:
            messagebox.showerror("صلاحية مفقودة", "ليس لديك صلاحية لتعديل بيانات العملاء")
            return

        if not self.selected_id:
            messagebox.showwarning("تنبيه", "اختر عميلًا للتعديل")
            return

        try:
            update_customer(
                self.selected_id,
                self.name.get(),
                self.phone.get(),
                self.notes.get(),
                float(self.discount.get() or 0)
            )
            messagebox.showinfo("تم", "تم تعديل بيانات العميل")
        except Exception:
            logger.exception("Failed to update customer")
            messagebox.showerror("خطأ", "تعذر تعديل العميل")

        self.load_data()
        self.clear_form()

    def delete_customer(self):

        if "العملاء" not in self.user_permissions:
            messagebox.showerror("صلاحية مفقودة", "ليس لديك صلاحية لحذف العملاء")
            return

        if not self.selected_id:
            messagebox.showwarning("تنبيه", "اختر عميلًا للحذف")
            return

        if not messagebox.askyesno("تأكيد", "هل تريد حذف العميل؟"):
            return

        try:
            delete_customer(self.selected_id)
            messagebox.showinfo("تم", "تم حذف العميل")
        except Exception:
            logger.exception("Failed to delete customer")
            messagebox.showerror("خطأ", "تعذر حذف العميل")

        self.load_data()
        self.clear_form()

    def clear_form(self):

        self.selected_id = None

        self.name.delete(0, "end")
        self.phone.delete(0, "end")
        self.notes.delete(0, "end")

        self.discount.delete(0, "end")
        self.discount.insert(0, "0")