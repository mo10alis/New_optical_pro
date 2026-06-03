import os
import sqlite3
import logging
import json
from typing import List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "database.db")
ROOT_DB = os.path.join(os.path.dirname(BASE_DIR), "database.db")

if not os.path.isdir(BASE_DIR):
    os.makedirs(BASE_DIR, exist_ok=True)

# إذا كان هناك ملف قاعدة بيانات قديمة في جذر المشروع، ننقله إلى المجلد الصحيح
if os.path.exists(ROOT_DB) and not os.path.exists(DB_NAME):
    try:
        os.replace(ROOT_DB, DB_NAME)
    except OSError:
        pass

logger = logging.getLogger(__name__)
# إذا لم توجد إعدادات لوج، نفعل الإعداد البسيط (يمكن تعديل من الطرف الأعلى)
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)


# ==========================================
# 🔌 الاتصال بقاعدة البيانات (موحّد)
# ==========================================
def connect(check_same_thread: bool = False) -> sqlite3.Connection:
    """
    إرجاع اتصال مع تفعيل foreign keys.
    الافتراضي check_same_thread=False ليتناسب مع حالات الاستخدام المتعددة للخيوط إن وُجدت.
    """
    conn = sqlite3.connect(DB_NAME, check_same_thread=check_same_thread)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ==========================================
# 🛠️ إنشاء الجداول وتحديث الحقول المفقودة
# ==========================================
def create_tables():
    try:
        with connect() as conn:
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE,
                    category TEXT,
                    name TEXT,
                    buy_price REAL,
                    sale_price REAL,
                    qty INTEGER DEFAULT 0,
                    supplier TEXT,
                    date TEXT,
                    last_purchase_date TEXT,
                    last_sale_date TEXT,
                    last_return_date TEXT
                )
            """)
            for col_name, column_def in [
                ("last_purchase_date", "TEXT"),
                ("last_sale_date", "TEXT"),
                ("last_return_date", "TEXT")
            ]:
                try:
                    cur.execute(f"ALTER TABLE items ADD COLUMN {col_name} {column_def}")
                except sqlite3.OperationalError:
                    pass

            cur.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id TEXT PRIMARY KEY,
                    customer_name TEXT,
                    phone TEXT,
                    total REAL,
                    discount REAL,
                    final_total REAL,
                    paid REAL,
                    remain REAL,
                    date TEXT,
                    pdf_path TEXT,
                    status TEXT DEFAULT '',
                    delivery_date TEXT DEFAULT '',
                    order_type TEXT DEFAULT '',
                    payment_method TEXT DEFAULT '',
                    user_created TEXT DEFAULT 'admin',
                    sph_r TEXT DEFAULT '',
                    cyl_r TEXT DEFAULT '',
                    axis_r TEXT DEFAULT '',
                    sph_l TEXT DEFAULT '',
                    cyl_l TEXT DEFAULT '',
                    axis_l TEXT DEFAULT ''
                )
            """)

            for col_name, column_def in [
                ("status", "TEXT DEFAULT ''"),
                ("delivery_date", "TEXT DEFAULT ''"),
                ("order_type", "TEXT DEFAULT ''"),
                ("payment_method", "TEXT DEFAULT ''"),
                ("user_created", "TEXT DEFAULT 'admin'"),
                ("sph_r", "TEXT DEFAULT ''"),
                ("cyl_r", "TEXT DEFAULT ''"),
                ("axis_r", "TEXT DEFAULT ''"),
                ("sph_l", "TEXT DEFAULT ''"),
                ("cyl_l", "TEXT DEFAULT ''"),
                ("axis_l", "TEXT DEFAULT ''"),
            ]:
                try:
                    cur.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {column_def}")
                except sqlite3.OperationalError:
                    pass

            cur.execute("""
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id TEXT,
                    item_name TEXT,
                    qty INTEGER,
                    price REAL,
                    total REAL,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT UNIQUE,
                    notes TEXT,
                    discount REAL DEFAULT 0,
                    date TEXT
                )
            """)

            for col_name, column_def in [
                ("notes", "TEXT"),
                ("discount", "REAL DEFAULT 0"),
                ("date", "TEXT")
            ]:
                try:
                    cur.execute(f"ALTER TABLE customers ADD COLUMN {col_name} {column_def}")
                except sqlite3.OperationalError:
                    pass

            cur.execute("""
                CREATE TABLE IF NOT EXISTS returns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id TEXT,
                    customer_name TEXT,
                    total_refund REAL,
                    return_date TEXT,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS return_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    return_id INTEGER,
                    item_name TEXT,
                    qty INTEGER,
                    price REAL,
                    total REAL,
                    FOREIGN KEY (return_id) REFERENCES returns(id)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    city TEXT,
                    type TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    role TEXT,
                    email TEXT UNIQUE,
                    active INTEGER DEFAULT 1,
                    permissions TEXT DEFAULT '[]',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id TEXT PRIMARY KEY,
                    supplier TEXT,
                    total_cost REAL,
                    notes TEXT,
                    order_date TEXT,
                    created_at TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS purchase_order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT,
                    item_code TEXT,
                    item_name TEXT,
                    qty INTEGER,
                    price REAL,
                    total REAL,
                    FOREIGN KEY(order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE
                )
            """)

            conn.commit()
    except Exception:
        logger.exception("Failed to create or migrate tables")


# ==========================================
# 📦 إدارة الأصناف (Inventory Management)
# ==========================================
def add_item(data: Tuple):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO items (code, category, name, buy_price, sale_price, qty, supplier, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()


def delete_item(code: str):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM items WHERE code=?", (code,))
        conn.commit()


def update_item(data: Tuple):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE items
            SET category=?, name=?, buy_price=?, sale_price=?, qty=?, supplier=?
            WHERE code = ?
        """, data)
        conn.commit()


def get_all_items() -> List[Tuple]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT code, name, sale_price, qty FROM items")
        return cur.fetchall()


def add_purchase_order(data: Tuple):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO purchase_orders (id, supplier, total_cost, notes, order_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        return data[0]


def add_purchase_order_item(data: Tuple):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO purchase_order_items (order_id, item_code, item_name, qty, price, total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()


def get_purchase_orders() -> List[Tuple]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, supplier, total_cost, order_date, created_at FROM purchase_orders ORDER BY created_at DESC")
        return cur.fetchall()


def get_purchase_order_items(order_id: str) -> List[Tuple]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT item_code, item_name, qty, price, total FROM purchase_order_items WHERE order_id = ?", (order_id,))
        return cur.fetchall()


# ==========================================
# 👥 إدارة العملاء (Customers Management)
# ==========================================
def add_customer(name: str, phone: str, notes: str, discount: float):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO customers (name, phone, notes, discount, date)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (name, phone, notes, discount))
        conn.commit()


def get_customers() -> List[Tuple]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name, phone, notes, discount FROM customers")
        return cur.fetchall()


def delete_customer(customer_id: int):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM customers WHERE id=?", (customer_id,))
        conn.commit()


def update_customer(id: int, name: str, phone: str, notes: str, discount: float):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE customers
            SET name=?, phone=?, notes=?, discount=?
            WHERE id = ?
        """, (name, phone, notes, discount, id))
        conn.commit()


# ==========================================
# 🧾 إدارة الفواتير الأساسية
# ==========================================
def add_invoice(data: Tuple) -> str:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO invoices (id, customer_name, phone, total, discount,
                                  final_total, paid, remain, date, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        return data[0]


def get_invoices() -> List[Tuple]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, customer_name, phone, total, discount, final_total, paid, remain, date, pdf_path
            FROM invoices
            ORDER BY date DESC, id DESC
        """)
        return cur.fetchall()


def delete_invoice(invoice_id: str):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM invoice_items WHERE invoice_id=?", (invoice_id,))
        cur.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
        conn.commit()


def get_invoice_items(invoice_id: str) -> List[Tuple]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT item_name, qty, price, total
            FROM invoice_items
            WHERE invoice_id = ?
        """, (invoice_id,))
        return cur.fetchall()


# ==========================================
# ↩️ دالات شاشة المرتجعات
# ==========================================
def insert_return_transaction(invoice_id: str, customer_name: str, total_refund: float, returned_items: List[Tuple]) -> bool:
    """
    حفظ مستند حركة المرتجعات وتحديث المخزن تلقائيًا بزيادة كميات الـ qty المرتجعة.
    returned_items: قائمة من tuples (item_name, qty, price, total)
    """
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO returns (invoice_id, customer_name, total_refund, return_date)
            VALUES (?, ?, ?, datetime('now'))
        """, (invoice_id, customer_name, total_refund))

        return_id = cur.lastrowid

        for item in returned_items:
            cur.execute("""
                INSERT INTO return_items (return_id, item_name, qty, price, total)
                VALUES (?, ?, ?, ?, ?)
            """, (return_id, item[0], item[1], item[2], item[3]))

            cur.execute("""
                UPDATE items
                SET qty = COALESCE(qty,0) + ?, last_return_date = datetime('now')
                WHERE name = ?
            """, (item[1], item[0]))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


# ==========================================
# 🗂️ إدارة التصنيفات
# ==========================================
def get_categories() -> List[str]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM categories")
        rows = cur.fetchall()
        return [r[0] for r in rows]


def insert_default_categories():
    categories = [
        "عدسات طبية",
        "عدسات شمسية",
        "عدسات أطفال",
        "شمبر بدون عدسات",
        "عدسات لاصقة"
    ]
    with connect() as conn:
        cur = conn.cursor()
        cur.executemany("INSERT OR IGNORE INTO categories (name) VALUES (?)", [(c,) for c in categories])
        conn.commit()


# =================================================================
# 📊 دالات لوحة التحكم والتقارير
# =================================================================
def get_reports_summary(filter_type: str = "إجمالي"):
    with connect() as conn:
        cur = conn.cursor()

        query_condition = "WHERE 1=1"
        if filter_type == "يومي":
            query_condition = "WHERE date(date) = date('now')"
        elif filter_type == "أسبوعي":
            query_condition = "WHERE date(date) >= date('now', '-7 days')"
        elif filter_type == "شهري":
            query_condition = "WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"

        cur.execute(f"""
            SELECT
                COUNT(*),
                IFNULL(SUM(final_total), 0),
                IFNULL(SUM(paid), 0),
                IFNULL(SUM(remain), 0),
                IFNULL(SUM(total - final_total), 0)
            FROM invoices
            {query_condition}
        """)
        invoices_count, sales, paid, remain, total_discount = cur.fetchone()

        cur.execute(f"SELECT COUNT(DISTINCT customer_name) FROM invoices {query_condition}")
        customers_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM items")
        items_count = cur.fetchone()[0]

        return invoices_count, sales, paid, remain, customers_count, items_count, total_discount


def get_top_items(filter_type: str = "إجمالي"):
    with connect() as conn:
        cur = conn.cursor()

        query_condition = "WHERE 1=1"
        if filter_type == "يومي":
            query_condition = "WHERE date(invoices.date) = date('now')"
        elif filter_type == "أسبوعي":
            query_condition = "WHERE date(invoices.date) >= date('now', '-7 days')"
        elif filter_type == "شهري":
            query_condition = "WHERE strftime('%Y-%m', invoices.date) = strftime('%Y-%m', 'now')"

        cur.execute(f"""
            SELECT invoice_items.item_name, SUM(invoice_items.qty)
            FROM invoice_items
            INNER JOIN invoices ON invoice_items.invoice_id = invoices.id
            {query_condition}
            GROUP BY invoice_items.item_name
            ORDER BY SUM(invoice_items.qty) DESC
            LIMIT 5
        """)
        return cur.fetchall()


def get_last_invoices(filter_type: str = "إجمالي"):
    with connect() as conn:
        cur = conn.cursor()

        query_condition = "WHERE 1=1"
        limit_clause = "LIMIT 50"

        if filter_type == "يومي":
            query_condition = "WHERE date(date) = date('now')"
            limit_clause = ""
        elif filter_type == "أسبوعي":
            query_condition = "WHERE date(date) >= date('now', '-7 days')"
            limit_clause = ""
        elif filter_type == "شهري":
            query_condition = "WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')"
            limit_clause = ""

        cur.execute(f"""
            SELECT id, customer_name, final_total, (total - final_total) AS cash_discount, paid, remain, date
            FROM invoices
            {query_condition}
            ORDER BY date DESC, id DESC
            {limit_clause}
        """)
        return cur.fetchall()


# ==========================================
# دوال مساعدة إضافية
# ==========================================
def get_total_returned_qty(invoice_id: str, item_name: str) -> int:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT SUM(ri.qty)
            FROM return_items ri
            JOIN returns r ON ri.return_id = r.id
            WHERE r.invoice_id = ? AND ri.item_name = ?
        """, (invoice_id, item_name))
        res = cur.fetchone()
        return res[0] if res and res[0] is not None else 0


def add_new_product(code: str, category: str, name: str, buy_price: float, sale_price: float, supplier: str):
    with connect() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO items (code, category, name, buy_price, sale_price, qty, supplier, date)
                VALUES (?, ?, ?, ?, ?, 0, ?, datetime('now'))
            """, (code, category, name, buy_price, sale_price, supplier))
            conn.commit()
        except sqlite3.IntegrityError:
            logger.warning("Product with code %s already exists", code)


def init_db():
    # wrapper لتهيئة المبدئية
    create_tables()
    insert_default_categories()
    insert_default_settings()
    insert_default_users()


def insert_default_users():
    try:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT OR IGNORE INTO users (username, full_name, role, email, active, permissions) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    "admin",
                    "المدير العام",
                    "مدير",
                    "admin@example.com",
                    1,
                    json.dumps(get_permission_keys(), ensure_ascii=False)
                )
            )
            conn.commit()
    except Exception:
        logger.exception("Failed to insert default admin user")


def insert_default_settings():
    default_values = {
        "company_name": "مركز الغزالي للبصريات",
        "company_address": "شارع التحرير، القاهرة",
        "invoice_prefix": "INV",
        "invoice_footer": "شكراً لتعاملكم معنا. مرحباً بكم دائماً.",
        "default_currency": "جنيه مصري",
        "default_payment_method": "كاش",
        "language": "العربية",
        "support_phone": "01000000000",
        "support_email": "info@example.com",
        "whatsapp_template": "شكراً لطلبك. سيتم التواصل معك قريباً.",
        "printer_copies": "1"
    }

    try:
        with connect() as conn:
            cur = conn.cursor()
            for key, value in default_values.items():
                cur.execute(
                    "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
                    (key, value)
                )
            conn.commit()
    except Exception:
        logger.exception("Failed to insert default settings")


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    try:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cur.fetchone()
            return row[0] if row else default
    except Exception:
        logger.exception("Failed to get setting %s", key)
        return default


def save_setting(key: str, value: str):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )
        conn.commit()


def get_all_settings() -> dict:
    try:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT key, value FROM app_settings")
            return {row[0]: row[1] for row in cur.fetchall()}
    except Exception:
        logger.exception("Failed to get all settings")
        return {}


def get_users() -> List[Tuple]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, full_name, role, email, active, permissions FROM users ORDER BY id DESC")
        return cur.fetchall()


def add_user(username: str, full_name: str, role: str, email: str, active: int, permissions: str):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, full_name, role, email, active, permissions) VALUES (?, ?, ?, ?, ?, ?)",
            (username, full_name, role, email, active, permissions)
        )
        conn.commit()


def update_user(user_id: int, username: str, full_name: str, role: str, email: str, active: int, permissions: str):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE users SET username=?, full_name=?, role=?, email=?, active=?, permissions=? WHERE id=?",
            (username, full_name, role, email, active, permissions, user_id)
        )
        conn.commit()


def delete_user(user_id: int):
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()


def get_user_by_id(user_id: int) -> Optional[Tuple]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, username, full_name, role, email, active, permissions FROM users WHERE id=?", (user_id,))
        return cur.fetchone()


def get_user_by_username(username: str) -> Optional[Tuple]:
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, full_name, role, email, active, permissions FROM users WHERE username=?",
            (username,)
        )
        return cur.fetchone()


def get_suppliers() -> List[str]:
    try:
        with connect() as conn:
            cur = conn.cursor()
            cur.execute("SELECT name FROM suppliers")
            return [row[0] for row in cur.fetchall()]
    except Exception:
        logger.exception("Failed to get suppliers")
        return []


def get_user_roles() -> List[str]:
    return ["مدير", "كاشير", "مخزن", "محاسب"]


def get_permission_keys() -> List[str]:
    return [
        "لوحة التحكم",
        "نقطة البيع",
        "الفواتير",
        "المرتجعات",
        "الأصناف",
        "المخزون",
        "أوامر الشراء",
        "حركات المخزون",
        "العملاء",
        "الموردين",
        "التقارير",
        "الإعدادات",
        "إدارة المستخدمين"
    ]


def update_db_schema():
    """
    محاولة آمنة لإضافة أعمدة جديدة إن لم تكن موجودة.
    يمكن تشغيلها مرة واحدة عند الحاجة.
    """
    try:
        with connect() as conn:
            cur = conn.cursor()
            # نستخدم محاولات بسيطة، إذا العمود موجود سترمي OperationalError فنلتقطها
            try:
                cur.execute("ALTER TABLE suppliers ADD COLUMN city TEXT;")
            except sqlite3.OperationalError:
                pass
            try:
                cur.execute("ALTER TABLE suppliers ADD COLUMN type TEXT;")
            except sqlite3.OperationalError:
                pass
            conn.commit()
    except Exception:
        logger.exception("Failed to update DB schema")