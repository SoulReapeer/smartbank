import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

NAVY  = colors.HexColor('#1E3A8A')
BLUE  = colors.HexColor('#2563EB')
GREEN = colors.HexColor('#10B981')
RED   = colors.HexColor('#EF4444')
LIGHT = colors.HexColor('#F8FAFC')
BORDER= colors.HexColor('#E2E8F0')
MUTED = colors.HexColor('#64748B')

def generate_statement(user, account, transactions, period_start=None, period_end=None):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story  = []

    # Header
    hd = [[
        Paragraph('<font color="#1E3A8A"><b>💳 SmartBank</b></font><br/><font size="8" color="#64748B">Digital Banking</font>', styles['Normal']),
        Paragraph(f'<font color="#64748B" size="8">BANK STATEMENT<br/>Generated: {datetime.utcnow().strftime("%B %d, %Y %H:%M")} UTC</font>',
                  ParagraphStyle('r', alignment=TA_RIGHT, fontSize=8, textColor=MUTED))
    ]]
    ht = Table(hd, colWidths=[95*mm, 75*mm])
    ht.setStyle(TableStyle([
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[LIGHT]),
        ('BOX',(0,0),(-1,-1),0.5,BORDER),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
    ]))
    story.append(ht)
    story.append(Spacer(1, 6*mm))

    # Account info
    sc = '#10B981' if account.status == 'active' else '#EF4444'
    info = [
        ['Account Holder', user.full_name, 'Account Number', account.account_number],
        ['Email', user.email, 'Status', Paragraph(f'<font color="{sc}"><b>{account.status.upper()}</b></font>', styles['Normal'])],
        ['Phone', user.phone, 'Balance', Paragraph(f'<b>৳{account.balance:,.2f}</b>', styles['Normal'])],
        ['Member Since', user.created_at.strftime('%B %d, %Y'), 'Period',
         f"{period_start or 'All'} – {period_end or datetime.utcnow().strftime('%b %d, %Y')}"],
    ]
    it = Table(info, colWidths=[35*mm,55*mm,35*mm,45*mm])
    it.setStyle(TableStyle([
        ('FONTSIZE',(0,0),(-1,-1),8.5),('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
        ('FONTNAME',(2,0),(2,-1),'Helvetica-Bold'),
        ('TEXTCOLOR',(0,0),(0,-1),MUTED),('TEXTCOLOR',(2,0),(2,-1),MUTED),
        ('ROWBACKGROUNDS',(0,0),(-1,-1),[colors.white,LIGHT]),
        ('BOX',(0,0),(-1,-1),0.5,BORDER),('INNERGRID',(0,0),(-1,-1),0.25,BORDER),
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(it)
    story.append(Spacer(1, 6*mm))

    # Transactions
    story.append(Paragraph('<b>Transaction History</b>',
                           ParagraphStyle('s', fontSize=11, textColor=NAVY, spaceAfter=4)))
    story.append(HRFlowable(width='100%', thickness=1.5, color=NAVY))
    story.append(Spacer(1, 2*mm))

    rows = [['Date', 'Type', 'Amount', 'Category', 'Reference']]
    for tx in transactions:
        if tx.transaction_type == 'deposit':
            amt = f'+৳{tx.amount:,.2f}'
            c   = '#10B981'
        elif tx.transaction_type == 'withdrawal' or (tx.transaction_type == 'transfer' and tx.sender_account == account.account_number):
            amt = f'-৳{tx.amount:,.2f}'
            c   = '#EF4444'
        else:
            amt = f'+৳{tx.amount:,.2f}'
            c   = '#10B981'
        rows.append([
            tx.timestamp.strftime('%b %d, %Y %H:%M'),
            tx.transaction_type.capitalize(),
            Paragraph(f'<font color="{c}"><b>{amt}</b></font>', styles['Normal']),
            tx.category or 'Others',
            (tx.reference or '—')[:40],
        ])

    tt = Table(rows, colWidths=[32*mm,22*mm,28*mm,22*mm,66*mm])
    tt.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,0),8),
        ('ALIGN',(0,0),(-1,0),'CENTER'),('FONTSIZE',(0,1),(-1,-1),8),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
        ('INNERGRID',(0,0),(-1,-1),0.25,BORDER),('BOX',(0,0),(-1,-1),0.5,BORDER),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(tt)

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph('<font size="7" color="#94A3B8">Computer-generated statement. SmartBank — Digital Banking Platform.</font>',
                           ParagraphStyle('f', alignment=TA_CENTER)))
    doc.build(story)
    buffer.seek(0)
    return buffer.read()
