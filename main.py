import customtkinter as ctk

from ui.main_window import MainWindow
from database.db import create_tables, insert_default_categories

# 🔥 تشغيل قاعدة البيانات مرة واحدة بس
create_tables()
insert_default_categories()

# =========================
# إعدادات الشكل
# =========================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# =========================
# تشغيل البرنامج
# =========================
app = MainWindow()
app.mainloop()

# تشغيل البرنامج# تشغيل البرنامج# تشغيل البرنامج