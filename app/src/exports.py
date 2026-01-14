import pandas as pd
from io import BytesIO
from docx import Document
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file

def export_to_csv(data, filename):
    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name=f"{filename}.csv")

def export_to_xlsx(data, filename):
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f"{filename}.xlsx")

def export_to_docx(data, filename, title):
    document = Document()
    document.add_heading(title, 0)
    
    if not data:
        document.add_paragraph("Brak danych do wyświetlenia.")
    else:
        keys = list(data[0].keys())
        table = document.add_table(rows=1, cols=len(keys))
        hdr_cells = table.rows[0].cells
        for i, key in enumerate(keys):
            hdr_cells[i].text = str(key).capitalize()
        
        for item in data:
            row_cells = table.add_row().cells
            for i, key in enumerate(keys):
                row_cells[i].text = str(item.get(key, ''))
                
    output = BytesIO()
    document.save(output)
    output.seek(0)
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', as_attachment=True, download_name=f"{filename}.docx")

def export_to_pdf(data, filename, title):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(letter))
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph(title, styles['Title']))
    
    if not data:
        elements.append(Paragraph("Brak danych.", styles['Normal']))
    else:
        keys = list(data[0].keys())
        table_data = [[str(k).capitalize() for k in keys]]
        for item in data:
            row = []
            for k in keys:
                val = str(item.get(k, ''))
                if k == 'QR_Link' and val.startswith('http'):
                    # Tworzymy klikalny link w PDF (uproszczone, bo reportlab Table nie obsługuje łatwo linków wprost)
                    # Ale możemy użyć Paragraph wewnątrz komórki
                    row.append(Paragraph(f'<a href="{val}" color="blue">Link</a>', styles['Normal']))
                else:
                    row.append(val)
            table_data.append(row)
            
        t = Table(table_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(t)
        
    doc.build(elements)
    output.seek(0)
    return send_file(output, mimetype='application/pdf', as_attachment=True, download_name=f"{filename}.pdf")
