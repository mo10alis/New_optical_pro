from tkinter import messagebox
import webbrowser
import urllib.parse
from datetime import datetime
from utils.settings import OWNER_PHONE, SHOP_NAME


def send_whatsapp_invoice(self):

    # =========================
    # 📞 تنظيف رقم الهاتف (احترافي)
    # =========================
    phone = self.phone.get().strip()

    if not phone:
        messagebox.showerror("خطأ", "أدخل رقم الهاتف أولاً")
        return

    # إزالة رموز
    phone = phone.replace(" ", "").replace("-", "").replace("+", "")

    # معالجة كل الحالات
    if phone.startswith("0"):
        phone = "20" + phone[1:]

    elif phone.startswith("20"):
        pass

    elif phone.startswith("2") and len(phone) == 11:
        phone = "20" + phone[1:]

    else:
        messagebox.showerror("خطأ", f"رقم غير صحيح: {phone}")
        return

    print("FINAL PHONE:", phone)  # 🔍 للتأكد

    # =========================
    # 🔥 تأكيد
    # =========================
    if not messagebox.askyesno("تأكيد", "إرسال الفاتورة للعميل؟"):
        return

    # =========================
    # 📊 بيانات الفاتورة
    # =========================
    customer = self.name.get()
    invoice_id = datetime.now().strftime("%Y%m%d%H%M")

    total = getattr(self, "final_total", 0)
    paid = float(self.paid.get()) if self.paid.get() else 0
    remain = total - paid

    # =========================
    # 📦 الأصناف
    # =========================
    items_text = ""

    for item in self.table.get_children():
        v = self.table.item(item)["values"]

        try:
            item_total = v[0]
            qty = v[1]
            price = v[2]
            name = v[3]

            items_text += f"\n🔹 {name}\n{qty} × {price} = {item_total}\n"

        except:
            continue

    if not items_text:
        items_text = "\n⚠️ لا توجد أصناف\n"

    # =========================
    # 🧾 رسالة العميل
    # =========================
    msg_customer = f"""
🧾 {SHOP_NAME}

👤 العميل: {customer}
🆔 {invoice_id}

━━━━━━━━━━━━━━
📦 الأصناف:
━━━━━━━━━━━━━━
{items_text}
━━━━━━━━━━━━━━
💰 الإجمالي: {total:.2f} جنيه
💵 المدفوع: {paid:.2f} جنيه
📌 المتبقي: {remain:.2f} جنيه
━━━━━━━━━━━━━━

🙏 شكراً لتعاملكم معنا ❤️
"""

    # =========================
    # 🏪 رسالة صاحب المحل
    # =========================
    msg_owner = f"""
📢 فاتورة جديدة

👤 العميل: {customer}
📞 {phone}
🆔 {invoice_id}

━━━━━━━━━━━━━━
📦 الأصناف:
━━━━━━━━━━━━━━
{items_text}
━━━━━━━━━━━━━━

💰 الإجمالي: {total:.2f}
📌 المتبقي: {remain:.2f}
"""

    # =========================
    # 🔗 ترميز الرسائل
    # =========================
    encoded_customer = urllib.parse.quote(msg_customer)
    encoded_owner = urllib.parse.quote(msg_owner)

    # =========================
    # 🔥 روابط واتساب (الأفضل)
    # =========================
    url_customer = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_customer}&app_absent=0"
    url_owner = f"https://web.whatsapp.com/send?phone={OWNER_PHONE}&text={encoded_owner}&app_absent=0"
    # =========================
    # 🚀 فتح شات العميل
    # =========================
    webbrowser.open_new_tab(url_customer)

    # =========================
    # 🚀 فتح صاحب المحل بعد 5 ثواني
    # =========================
    self.parent.after(15000, lambda: webbrowser.open_new_tab(url_owner))

    messagebox.showinfo("تم", "تم فتح الواتساب ✔️")