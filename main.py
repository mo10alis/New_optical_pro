import sys
import traceback
import customtkinter as ctk

def main():
    try:
        # استورد هنا لتجنّب side-effects عند الاستيراد
        from database.db import init_db
        from ui.main_window import MainWindow
    except Exception as e:
        print("Import failed:", e)
        traceback.print_exc()
        sys.exit(1)

    try:
        # تشغيل قاعدة البيانات مرة واحدة فقط
        init_db()
    except Exception as e:
        print("Database initialization failed:", e)
        traceback.print_exc()

    # إعدادات الشكل
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    # تشغيل التطبيق
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        print("Application failed:", e)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()