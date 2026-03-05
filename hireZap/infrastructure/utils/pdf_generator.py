from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame,
    Paragraph, Spacer, Table, TableStyle, HRFlowable
)

# ── Palette ──
NAVY      = colors.HexColor('#1a1a2e')
DARK_BLUE = colors.HexColor('#0f3460')
GOLD      = colors.HexColor('#f5a623')
LIGHT_BG  = colors.HexColor('#f8f6f2')
SUBTLE    = colors.HexColor('#f0ece4')
MUTED     = colors.HexColor('#999999')
TEXT_MID  = colors.HexColor('#555555')
TEXT_DARK = colors.HexColor('#1a1a1a')
EXPIRY_BG = colors.HexColor('#fff8ee')
EXPIRY_BD = colors.HexColor('#fde8bc')
EXPIRY_TX = colors.HexColor('#9a6200')

W, H = A4
TOP_BAND = 6 + 64 + 90   # accent(6) + header(64) + hero(90)
FOOTER_H = 44


def _draw_page(canvas, doc, context: dict):

    c = canvas
    c.saveState()

    # White base
    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── Accent bar (top 6pt) ──
    c.setFillColor(NAVY)
    c.rect(0, H - 6, W * 0.5, 6, fill=1, stroke=0)
    c.setFillColor(GOLD)
    c.rect(W * 0.5, H - 6, W * 0.5, 6, fill=1, stroke=0)

    # ── Header band ──
    c.setFillColor(NAVY)
    c.rect(0, H - 70, W, 64, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(40, H - 70 + 38, context['company_name'])
    c.setFillColor(colors.HexColor('#a0aec0'))
    c.setFont('Helvetica', 8)
    c.drawString(40, H - 70 + 22, 'OFFICIAL OFFER LETTER')

    # Badge
    bx = W - 40 - 92
    by = H - 70 + 34
    c.setFillColor(GOLD)
    c.roundRect(bx, by, 92, 18, 3, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont('Helvetica-Bold', 8)
    c.drawCentredString(bx + 46, by + 5, 'CONFIDENTIAL')

    c.setFillColor(colors.HexColor('#8899bb'))
    c.setFont('Helvetica', 8)
    c.drawRightString(W - 40, H - 70 + 18,
                      f"Offer Ref: OFR-{context['offer_id']:04d}")
    c.drawRightString(W - 40, H - 70 + 8,
                      f"Issued: {context['issued_date']}")

    # Hero band 
    hero_y = H - 70 - 90
    c.setFillColor(DARK_BLUE)
    c.rect(0, hero_y, W, 90, fill=1, stroke=0)

    # Decorative translucent circle
    c.setFillColor(colors.white)
    c.setFillAlpha(0.04)
    c.circle(W - 40, hero_y + 80, 80, fill=1, stroke=0)
    c.setFillAlpha(1)

    c.setFillColor(GOLD)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(40, hero_y + 66, 'CONGRATULATIONS')

    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 22)
    c.drawString(40, hero_y + 40, "You've Been Selected")

    c.setFillColor(colors.HexColor('#a0aec0'))
    c.setFont('Helvetica', 10)
    c.drawString(40, hero_y + 22,
                 'We are pleased to formally extend this offer of employment.')

    # Footer band
    c.setFillColor(NAVY)
    c.rect(0, 0, W, FOOTER_H, fill=1, stroke=0)

    c.setFillColor(colors.HexColor('#6b7a99'))
    c.setFont('Helvetica', 8)
    c.drawString(40, 15,
                 f"{context['company_name']}  ·  Confidential  ·  OFR-{context['offer_id']:04d}")
    c.drawRightString(W - 40, 15,
                      f"© {context['year']} {context['company_name']}. All rights reserved.")

    c.restoreState()


def generate_offer_letter_pdf(offer) -> bytes:
    app         = offer.application
    issued_date = date.today()

    context = {
        'offer_id'       : offer.id,
        'company_name'   : app.job.company.company_name,
        'candidate_name' : f"{app.first_name} {app.last_name}",
        'position_title' : offer.position_title,
        'offered_salary' : offer.offered_salary,
        'joining_date'   : offer.joining_date.strftime('%B %d, %Y'),
        'expiry_date'    : offer.offer_expiry_date.strftime('%B %d, %Y'),
        'custom_message' : offer.custom_message,
        'recruiter_name' : offer.sent_by.full_name if offer.sent_by else 'The Hiring Team',
        'recruiter_role' : getattr(offer.sent_by, 'job_title', 'Recruiter') if offer.sent_by else 'Recruiter',
        'issued_date'    : issued_date.strftime('%B %d, %Y'),
        'year'           : issued_date.year,
    }

    buffer = BytesIO()

    doc = BaseDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40, rightMargin=40,
        topMargin=TOP_BAND + 24,
        bottomMargin=FOOTER_H + 20,
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        W - doc.leftMargin - doc.rightMargin,
        H - doc.topMargin - doc.bottomMargin,
        id='main'
    )
    doc.addPageTemplates([PageTemplate(
        id='main', frames=[frame],
        onPage=lambda c, d: _draw_page(c, d, context)
    )])

    #Paragraph styles
    s_body = ParagraphStyle('body', fontName='Helvetica', fontSize=11,
                            leading=18, textColor=TEXT_MID, spaceAfter=6)
    s_salute = ParagraphStyle('salute', fontName='Helvetica', fontSize=12,
                              leading=20, textColor=TEXT_DARK, spaceAfter=10)
    s_label = ParagraphStyle('label', fontName='Helvetica-Bold', fontSize=8,
                             leading=12, textColor=GOLD, spaceBefore=14,
                             spaceAfter=8, letterSpacing=2)
    s_msg_label = ParagraphStyle('msg_label', fontName='Helvetica-Bold', fontSize=8,
                                 leading=12, textColor=colors.HexColor('#c8860a'),
                                 spaceAfter=6, letterSpacing=1.5)
    s_msg_text = ParagraphStyle('msg_text', fontName='Helvetica-Oblique', fontSize=10,
                                leading=17, textColor=TEXT_MID)
    s_closing = ParagraphStyle('closing', fontName='Helvetica', fontSize=11,
                               leading=18, textColor=TEXT_MID,
                               spaceBefore=6, spaceAfter=6)
    s_sig_name = ParagraphStyle('sig_name', fontName='Helvetica-Bold', fontSize=13,
                                leading=18, textColor=NAVY)
    s_sig_role = ParagraphStyle('sig_role', fontName='Helvetica', fontSize=9,
                                leading=14, textColor=MUTED)
    s_right = ParagraphStyle('right', fontName='Helvetica', fontSize=8,
                             textColor=MUTED, alignment=TA_RIGHT)
    s_right_bold = ParagraphStyle('right_bold', fontName='Helvetica-Bold', fontSize=11,
                                  textColor=TEXT_MID, alignment=TA_RIGHT)

    col_w = W - doc.leftMargin - doc.rightMargin  # usable width

    story = []

    # Salutation
    story.append(Paragraph(f"Dear <b>{context['candidate_name']}</b>,", s_salute))
    story.append(Spacer(1, 6))

    #Opening
    story.append(Paragraph(
        f"Following a comprehensive review of your qualifications and your outstanding performance "
        f"throughout our selection process, we are delighted to offer you the position of "
        f"<b>{context['position_title']}</b> at <b>{context['company_name']}</b>. "
        f"This offer reflects our confidence in your abilities and our excitement about what "
        f"you will bring to our team.",
        s_body
    ))
    story.append(HRFlowable(width='100%', thickness=1,
                            color=SUBTLE, spaceAfter=14, spaceBefore=14))

    #  Offer Details
    story.append(Paragraph('OFFER DETAILS', s_label))
    details = [
        ['Position',         context['position_title']],
        ['Offered Salary',   context['offered_salary']],
        ['Joining Date',     context['joining_date']],
        ['Offer Valid Until', context['expiry_date']],
    ]
    tbl = Table(details, colWidths=[150, col_w - 150])
    tbl.setStyle(TableStyle([
        *[('BACKGROUND', (0, i), (-1, i),
           LIGHT_BG if i % 2 == 0 else colors.white) for i in range(4)],
        ('FONTNAME',      (0,0), (0,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0), (0,-1), 9),
        ('TEXTCOLOR',     (0,0), (0,-1), MUTED),
        ('LEFTPADDING',   (0,0), (0,-1), 14),
        ('FONTNAME',      (1,0), (1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',      (1,0), (1,-1), 12),
        ('TEXTCOLOR',     (1,0), (1,-1), NAVY),
        ('ALIGN',         (1,0), (1,-1), 'RIGHT'),
        ('RIGHTPADDING',  (1,0), (1,-1), 14),
        # Salary row larger
        ('FONTSIZE',      (1,1), (1,1), 15),
        ('TEXTCOLOR',     (1,1), (1,1), DARK_BLUE),
        ('TOPPADDING',    (0,0), (-1,-1), 11),
        ('BOTTOMPADDING', (0,0), (-1,-1), 11),
        ('LINEBELOW',     (0,0), (-1,-2), 0.5, SUBTLE),
        ('BOX',           (0,0), (-1,-1), 0.5, SUBTLE),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 14))

    # Expiry notice
    expiry_tbl = Table(
        [[f"⏳   This offer is valid until  {context['expiry_date']}.  "
          f"Please confirm your acceptance before this date."]],
        colWidths=[col_w]
    )
    expiry_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), EXPIRY_BG),
        ('TEXTCOLOR',     (0,0), (-1,-1), EXPIRY_TX),
        ('FONTNAME',      (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE',      (0,0), (-1,-1), 10),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('BOX',           (0,0), (-1,-1), 0.75, EXPIRY_BD),
    ]))
    story.append(expiry_tbl)
    story.append(Spacer(1, 14))

    # Custom message (only if present)
    if context['custom_message']:
        msg_tbl = Table([
            [Paragraph('NOTE FROM THE HIRING TEAM', s_msg_label)],
            [Paragraph(context['custom_message'], s_msg_text)],
        ], colWidths=[col_w])
        msg_tbl.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), colors.HexColor('#fdf9f2')),
            ('LEFTPADDING',   (0,0), (-1,-1), 16),
            ('RIGHTPADDING',  (0,0), (-1,-1), 16),
            ('TOPPADDING',    (0,0), (0, 0),  12),
            ('BOTTOMPADDING', (0,-1),(-1,-1), 14),
            ('LINEBEFORE',    (0,0), (0,-1),   3, GOLD),
        ]))
        story.append(msg_tbl)
        story.append(Spacer(1, 18))

    # Closing
    story.append(Paragraph(
        f"We are excited about the prospect of you joining <b>{context['company_name']}</b> and "
        f"are confident this will be a mutually rewarding journey. Should you have any questions "
        f"regarding this offer or the onboarding process, please do not hesitate to reach out.",
        s_closing
    ))
    story.append(Paragraph('We look forward to your positive response.', s_closing))
    story.append(Spacer(1, 22))
    story.append(HRFlowable(width='100%', thickness=0.75, color=SUBTLE, spaceAfter=14))

    # Signature row 
    sig_left = Table([
        [Paragraph(context['recruiter_name'], s_sig_name)],
        [Paragraph(f"{context['recruiter_role']}  ·  {context['company_name']}", s_sig_role)],
    ], colWidths=[260])
    sig_left.setStyle(TableStyle([
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))

    sig_right = Table([
        [Paragraph('DATE ISSUED', s_right)],
        [Paragraph(f"<b>{context['issued_date']}</b>", s_right_bold)],
    ], colWidths=[col_w - 260])
    sig_right.setStyle(TableStyle([
        ('TOPPADDING',    (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))

    story.append(Table(
        [[sig_left, sig_right]],
        colWidths=[260, col_w - 260],
        style=TableStyle([('VALIGN', (0,0), (-1,-1), 'BOTTOM')])
    ))

    doc.build(story)
    return buffer.getvalue()