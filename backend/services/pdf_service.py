"""
PDF Bank Statement generator using ReportLab.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER


# Brand colours
NAVY   = colors.HexColor('#1E3A8A')
BLUE   = colors.HexColor('#2563EB')
GREEN  = colors.HexColor('#10B981')
RED    = colors.HexColor('#EF4444')
LIGHT  = colors.HexColor('#F8FAFC')
BORDER = colors.HexColor('#E2E8F0')
MUTED  = colors.HexColor('#64748B')


def generate_statement(user, account, transactions, period_start=None, period_end=None):
    """
    Generate a PDF bank statement and return bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm,
        title=f"SmartBank Statement — {account.account_number}"
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Header ────────────────────────────────────────────────
    header_data = [[
        Paragraph('<font color="#1E3A8A"><b>💳 SmartBank</b></font><br/>'
                  '<font size="8" color="#64748B">Digital Banking Platform</font>', styles['Normal']),
        Paragraph('<font color="#64748B" size="8">BANK STATEMENT<br/>'
                  f'Generated: {datetime.utcnow().strftime("%B %d, %Y %H:%M")} UTC</font>',
                  ParagraphStyle('right', alignment=TA_RIGHT, fontSize=8, textColor=MUTED))
    ]]
    header_tbl = Table(header_data, colWidths=[95*mm, 75*mm])
    header_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT]),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER),
        ('ROUNDEDCORNERS', [6]),
        ('LEFTPADDING',  (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING',   (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 6*mm))

    # ── Account Info ──────────────────────────────────────────
    status_color = '#10B981' if account.status == 'active' else '#EF4444'
    info_data = [
        ['Account Holder',  user.full_name,         'Account Number', account.account_number],
        ['Email',           user.email,              'Account Status',
            Paragraph(f'<font color="{status_color}"><b>{account.status.upper()}</b></font>', styles['Normal'])],
        ['Phone',           user.phone,              'Current Balance',
            Paragraph(f'<b>৳{account.balance:,.2f}</b>', styles['Normal'])],
        ['Member Since',    user.created_at.strftime('%B %d, %Y'),
            'Statement Period',
            f"{period_start or 'All time'} – {period_end or datetime.utcnow().strftime('%b %d, %Y')}"],
    ]
    info_tbl = Table(info_data, colWidths=[35*mm, 55*mm, 35*mm, 45*mm])
    info_tbl.setStyle(TableStyle([
        ('FONTSIZE',        (0,0), (-1,-1), 8.5),
        ('FONTNAME',        (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME',        (2,0), (2,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR',       (0,0), (0,-1), MUTED),
        ('TEXTCOLOR',       (2,0), (2,-1), MUTED),
        ('ROWBACKGROUNDS',  (0,0), (-1,-1), [colors.white, LIGHT]),
        ('BOX',             (0,0), (-1,-1), 0.5, BORDER),
        ('INNERGRID',       (0,0), (-1,-1), 0.25, BORDER),
        ('LEFTPADDING',     (0,0), (-1,-1), 8),
        ('RIGHTPADDING',    (0,0), (-1,-1), 8),
        ('TOPPADDING',      (0,0), (-1,-1), 6),
        ('BOTTOMPADDING',   (0,0), (-1,-1), 6),
        ('VALIGN',          (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 6*mm))

    # ── Summary Stats ─────────────────────────────────────────
    deposits    = sum(t.amount for t in transactions if t.transaction_type == 'deposit')
    withdrawals = sum(t.amount for t in transactions if t.transaction_type == 'withdrawal'
                      and t.sender_account == account.account_number)
    transfers   = sum(t.amount for t in transactions if t.transaction_type == 'transfer'
                      and t.sender_account == account.account_number)

    summary_data = [
        [
            Paragraph('<font color="#64748B" size="8">TOTAL DEPOSITS</font><br/>'
                      f'<font size="12" color="#10B981"><b>৳{deposits:,.2f}</b></font>', styles['Normal']),
            Paragraph('<font color="#64748B" size="8">TOTAL WITHDRAWALS</font><br/>'
                      f'<font size="12" color="#EF4444"><b>৳{withdrawals:,.2f}</b></font>', styles['Normal']),
            Paragraph('<font color="#64748B" size="8">TOTAL TRANSFERS OUT</font><br/>'
                      f'<font size="12" color="#2563EB"><b>৳{transfers:,.2f}</b></font>', styles['Normal']),
            Paragraph('<font color="#64748B" size="8">TRANSACTIONS</font><br/>'
                      f'<font size="12" color="#0F172A"><b>{len(transactions)}</b></font>', styles['Normal']),
        ]
    ]
    summary_tbl = Table(summary_data, colWidths=[42.5*mm]*4)
    summary_tbl.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT]),
        ('BOX',           (0,0), (-1,-1), 0.5, BORDER),
        ('INNERGRID',     (0,0), (-1,-1), 0.25, BORDER),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(summary_tbl)
    story.append(Spacer(1, 6*mm))

    # ── Transaction Table ──────────────────────────────────────
    story.append(Paragraph('<b>Transaction History</b>',
                           ParagraphStyle('sec', fontSize=11, textColor=NAVY, spaceAfter=4)))
    story.append(HRFlowable(width='100%', thickness=1.5, color=NAVY))
    story.append(Spacer(1, 2*mm))

    tx_rows = [['Date & Time', 'Type', 'Amount', 'Reference', 'Direction']]
    for tx in transactions:
        if tx.transaction_type == 'deposit':
            direction = '↓ IN'
            d_color = '#10B981'
            amt_str = f'+৳{tx.amount:,.2f}'
        elif tx.transaction_type == 'withdrawal':
            direction = '↑ OUT'
            d_color = '#EF4444'
            amt_str = f'-৳{tx.amount:,.2f}'
        elif tx.transaction_type == 'transfer':
            if tx.sender_account == account.account_number:
                direction = '↑ OUT'
                d_color = '#EF4444'
                amt_str = f'-৳{tx.amount:,.2f}'
            else:
                direction = '↓ IN'
                d_color = '#10B981'
                amt_str = f'+৳{tx.amount:,.2f}'
        else:
            direction = '—'
            d_color = '#64748B'
            amt_str = f'৳{tx.amount:,.2f}'

        tx_rows.append([
            tx.timestamp.strftime('%b %d, %Y\n%H:%M'),
            tx.transaction_type.capitalize(),
            Paragraph(f'<font color="{d_color}"><b>{amt_str}</b></font>', styles['Normal']),
            (tx.reference or '—')[:40],
            Paragraph(f'<font color="{d_color}">{direction}</font>', styles['Normal']),
        ])

    tx_tbl = Table(tx_rows, colWidths=[32*mm, 22*mm, 28*mm, 60*mm, 28*mm])
    tx_tbl.setStyle(TableStyle([
        # Header row
        ('BACKGROUND',    (0,0), (-1,0), NAVY),
        ('TEXTCOLOR',     (0,0), (-1,0), colors.white),
        ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,0), 8),
        ('ALIGN',         (0,0), (-1,0), 'CENTER'),
        # Body
        ('FONTSIZE',      (0,1), (-1,-1), 8),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [colors.white, LIGHT]),
        ('INNERGRID',     (0,0), (-1,-1), 0.25, BORDER),
        ('BOX',           (0,0), (-1,-1), 0.5, BORDER),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(tx_tbl)

    if not transactions:
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph('No transactions found for this period.',
                               ParagraphStyle('center', alignment=TA_CENTER, textColor=MUTED)))

    # ── Footer ─────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=BORDER))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        '<font size="7" color="#94A3B8">This is a computer-generated statement and does not require a signature. '
        'SmartBank — Digital Banking Platform. For queries contact support@smartbank.com</font>',
        ParagraphStyle('footer', alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
