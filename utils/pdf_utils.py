from tkinter import messagebox


def generate_invoice_pdf(self):

    import os
    import sys
    from datetime import datetime

    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    import arabic_reshaper
    from bidi.algorithm import get_display

    # ===================== 🟢 الخطوط =====================
    pdfmetrics.registerFont(TTFont('Arial', 'assets/fonts/Arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'assets/fonts/Arial-Bold.ttf'))

    def ar_text(text):
        return get_display(arabic_reshaper.reshape(str(text)))

    # ===================== 🟢 بيانات =====================
    filename = f"invoice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    invoice_id = datetime.now().strftime("%Y%m%d%H%M")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=25,
        bottomMargin=25
    )

    elements = []

    base_dir = os.path.dirname(os.path.dirname(__file__))
    logo_path = os.path.join(base_dir, "assets", "logo.png")

    # ===================== 🟢 WATERMARK كامل الصفحة =====================
    def draw_watermark(canvas, doc):
        if os.path.exists(logo_path):
            from reportlab.lib.utils import ImageReader

            canvas.saveState()

            # شفافية خفيفة
            canvas.setFillAlpha(0.05)

            width, height = A4

            # 🔥 يغطي الصفحة بالكامل
            canvas.drawImage(
                ImageReader(logo_path),
                0, 0,
                width=width,
                height=height,
                preserveAspectRatio=False,
                mask='auto'
            )

            canvas.restoreState()

    # ===================== 🟢 HEADER =====================
    header_style = ParagraphStyle(
        name="header",
        fontName="Arial-Bold",
        fontSize=18,
        alignment=2
    )

    if os.path.exists(logo_path):
        header = Table([
            [Paragraph(ar_text("الغزوالى للبصريات"), header_style),
             Image(logo_path, width=70, height=50)]
        ], colWidths=[400, 100])
    else:
        header = Table([
            [Paragraph(ar_text("الغزوالى للبصريات"), header_style), ""]
        ], colWidths=[400, 100])

    elements.append(header)
    elements.append(Spacer(1, 10))

    # ===================== 🟢 TITLE =====================
    elements.append(Paragraph(
        ar_text("فاتورة مبيعات"),
        ParagraphStyle(name="title", fontName="Arial-Bold", fontSize=20, alignment=1)
    ))
    elements.append(Spacer(1, 15))

    # ===================== 🟢 CUSTOMER =====================
    normal_style = ParagraphStyle(
        name="normal",
        fontName="Arial",
        fontSize=12,
        alignment=2
    )

    customer_data = [
        [ar_text(f"العميل: {self.name.get()}")],
        [ar_text(f"الهاتف: {self.phone.get()}")],
        [ar_text(f"رقم الفاتورة: {invoice_id}")]
    ]

    customer_table = Table(customer_data, colWidths=[500])
    customer_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(customer_table)
    elements.append(Spacer(1, 20))

    # ===================== 🟢 TABLE (عربي مظبوط) =====================
    data = [[
        ar_text("الإجمالي"),
        ar_text("السعر"),
        ar_text("الكمية"),
        ar_text("الصنف")
    ]]

    for item in self.table.get_children():
        values = self.table.item(item)["values"]

        data.append([
            values[0],  # الإجمالي
            values[2],  # السعر
            values[1],  # الكمية
            ar_text(values[3])  # الصنف
        ])

    table = Table(data, colWidths=[100, 100, 80, 220])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),  # الصنف يمين
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.whitesmoke, colors.lightgrey]),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 25))

    # ===================== 🟢 TOTAL =====================
    total = getattr(self, "final_total", 0)
    paid = float(self.paid.get()) if self.paid.get() else 0
    remain = total - paid

    totals = [
        [f"{total:.2f}", ar_text("الإجمالي")],
        [f"{paid:.2f}", ar_text("المدفوع")],
        [f"{remain:.2f}", ar_text("المتبقي")],
    ]

    totals_table = Table(totals, colWidths=[250, 150])
    totals_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), "Arial-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("TEXTCOLOR", (0, 2), (-1, 2),
         colors.red if remain > 0 else colors.green),
    ]))

    elements.append(totals_table)
    elements.append(Spacer(1, 30))

    # ===================== 🟢 FOOTER =====================
    elements.append(Paragraph(
        ar_text(" شكراً لتعاملكم معنا "),
        ParagraphStyle(name="footer", fontName="Arial-Bold", fontSize=14, alignment=1)
    ))

    # ===================== 🟢 BUILD =====================
    doc.build(elements, onFirstPage=draw_watermark, onLaterPages=draw_watermark)

    # ===================== 🟢 فتح تلقائي =====================
    try:
        if sys.platform == "win32":
            os.startfile(filename)
    except:
        pass

    # ===================== 🟢 رسالة =====================
    from tkinter import messagebox
    messagebox.showinfo("تم", "تم إنشاء الفاتورة الاحترافية ✅")
