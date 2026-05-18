import sqlite3
from datetime import datetime

DB_NAME = "database.db"


# =========================
# الاتصال
# =========================
def connect():
    return sqlite3.connect(DB_NAME)


# =========================
# إنشاء الجداول
# =========================
def create_tables():
    conn = connect()
    cur = conn.cursor()

    # 🟢 جدول الأصناف
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT,
        name TEXT,
        buy_price REAL,
        sale_price REAL,
        qty INTEGER,
        supplier TEXT,
        date TEXT
    )
    """)

    # 🟢 جدول الفواتير
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        phone TEXT,
        total REAL,
        paid REAL,
        remain REAL,
        date TEXT
    )
    """)

    # 🟢 جدول أصناف الفاتورة
    cur.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        item_name TEXT,
        qty INTEGER,
        price REAL,
        total REAL
    )
    """)

    # 🔥 جدول التصنيفات (المهم)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    """)

    conn.commit()
    conn.close()


# =========================
# إضافة تصنيفات افتراضية
# =========================
def insert_default_categories():
    conn = connect()
    cur = conn.cursor()

    categories = [
        "عدسات طبية",
        "عدسات شمسية",
        "عدسات أطفال",
        "شمبر بدون عدسات",
        "عدسات لاصقة"
    ]

    for cat in categories:
        try:
            cur.execute("INSERT INTO categories (name) VALUES (?)", (cat,))
        except:
            pass

    conn.commit()
    conn.close()


# =========================
# جلب التصنيفات
# =========================
def get_categories():
    conn = connect()
    cur = conn.cursor()

    cur.execute("SELECT name FROM categories")
    rows = cur.fetchall()

    conn.close()

    return [r[0] for r in rows]


# =========================
# إضافة تصنيف
# =========================
def add_category(name):
    conn = connect()
    cur = conn.cursor()

    try:
        cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
    except:
        pass

    conn.close()


# =========================
# إضافة صنف
# =========================
def add_item(data):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO items (code, name, buy_price, sale_price, qty, supplier, date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()
    conn.close()


# =========================
# حذف صنف
# =========================
def delete_item(code):
    conn = connect()
    cur = conn.cursor()

    cur.execute("DELETE FROM items WHERE code=?", (code,))

    conn.commit()
    conn.close()


# =========================
# تحديث صنف
# =========================
def update_item(data):
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    UPDATE items
    SET name=?, buy_price=?, sale_price=?, qty=?, supplier=?
    WHERE code=?
    """, data)

    conn.commit()
    conn.close()


# =========================
# حفظ الفاتورة
# =========================
def save_invoice(self):
    conn = connect()
    cur = conn.cursor()

    total = getattr(self, "final_total", 0)
    paid = float(self.paid.get()) if self.paid.get() else 0
    remain = total - paid

    # 🟢 إدخال الفاتورة
    cur.execute("""
    INSERT INTO invoices (customer_name, phone, total, paid, remain, date)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        self.name.get(),
        self.phone.get(),
        total,
        paid,
        remain,
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))

    invoice_id = cur.lastrowid

    # 🟢 إدخال الأصناف
    for item in self.table.get_children():
        v = self.table.item(item)["values"]

        cur.execute("""
        INSERT INTO invoice_items (invoice_id, item_name, qty, price, total)
        VALUES (?, ?, ?, ?, ?)
        """, (
            invoice_id,
            v[3],
            v[1],
            v[2],
            v[0]
        ))

    conn.commit()
    conn.close()