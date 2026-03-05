from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_offer_email_task(self, offer_id: int):  # ← remove pdf_url param
    try:
        from offer.models import OfferLetterModel
        offer = OfferLetterModel.objects.select_related(
            'application__job__company',
            'application__candidate',
            'sent_by'
        ).get(id=offer_id)

        app            = offer.application
        candidate_name = f"{app.first_name} {app.last_name}"
        company_name   = app.job.company.company_name
        recruiter_name = offer.sent_by.full_name if offer.sent_by else 'The Hiring Team'
        offer_url      = offer.offer_letter_url or ''

        plain_text = (
            f"Dear {candidate_name},\n\n"
            f"Congratulations! Please find your official offer letter below.\n\n"
            f"Role        : {offer.position_title}\n"
            f"Salary      : {offer.offered_salary}\n"
            f"Joining Date: {offer.joining_date.strftime('%B %d, %Y')}\n"
            f"Valid Until : {offer.offer_expiry_date.strftime('%B %d, %Y')}\n\n"
            + (f"View Offer Letter: {offer_url}\n\n" if offer_url else "")
            + f"Please log in to the portal to accept or decline this offer.\n\n"
            f"Best regards,\n{recruiter_name}"
        )

        html_body = f"""
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:40px auto;color:#333;">
          <div style="background:#1a1a2e;padding:28px 36px;border-radius:10px 10px 0 0;">
            <h2 style="color:#fff;margin:0;">{company_name}</h2>
            <p style="color:#a0aec0;font-size:12px;margin:4px 0 0;">Official Offer Letter</p>
          </div>
          <div style="background:#fff;padding:36px;border:1px solid #eee;border-top:none;border-radius:0 0 10px 10px;">
            <p>Dear <strong>{candidate_name}</strong>,</p>
            <p style="color:#555;line-height:1.7;">
              Congratulations! You have been offered the position of
              <strong>{offer.position_title}</strong> at <strong>{company_name}</strong>.
            </p>
            <div style="background:#f8f6f2;border-radius:8px;padding:20px 24px;margin:20px 0;">
              <p style="margin:0 0 8px;font-size:11px;color:#aaa;text-transform:uppercase;letter-spacing:1px;">Offer Summary</p>
              <p style="margin:4px 0;"><strong>Role:</strong> {offer.position_title}</p>
              <p style="margin:4px 0;"><strong>Salary:</strong> {offer.offered_salary}</p>
              <p style="margin:4px 0;"><strong>Joining Date:</strong> {offer.joining_date.strftime('%B %d, %Y')}</p>
              <p style="margin:4px 0;"><strong>Valid Until:</strong> {offer.offer_expiry_date.strftime('%B %d, %Y')}</p>
            </div>

            {f'''<div style="text-align:center;margin:28px 0;">
              <a href="{offer_url}" target="_blank"
                 style="display:inline-block;background:#f59e0b;color:#fff;padding:14px 32px;
                        border-radius:8px;text-decoration:none;font-weight:600;font-size:15px;">
                📄 View Offer Letter
              </a>
            </div>''' if offer_url else ''}

            <p style="color:#777;font-size:13px;">
              Log in to your portal to <strong>accept or decline</strong> this offer before it expires.
            </p>
            <p style="margin-top:24px;color:#999;font-size:13px;">
              Best regards,<br/><strong style="color:#1a1a2e;">{recruiter_name}</strong>
            </p>
          </div>
        </div>
        """

        msg = EmailMultiAlternatives(
            subject=f"🎉 Your Offer Letter — {offer.position_title} at {company_name}",
            body=plain_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[app.email],
        )
        msg.attach_alternative(html_body, 'text/html')

        # ── Always generate PDF on the fly and attach it ──────────────────
        from infrastructure.utils.pdf_generator import generate_offer_letter_pdf
        pdf_bytes = generate_offer_letter_pdf(offer)
        filename  = f"Offer_Letter_{candidate_name.replace(' ', '_')}.pdf"
        msg.attach(filename, pdf_bytes, 'application/pdf')

        msg.send()
        logger.info(f"Offer email sent successfully for offer {offer_id}")

    except Exception as e:
        logger.error(f"Offer email task failed for offer {offer_id}: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_offer_response_email_task(self, offer_id: int, action: str):
    """Notify recruiter when candidate responds to offer."""
    try:
        from offer.models import OfferLetterModel
        offer = OfferLetterModel.objects.select_related(
            'application__job', 'sent_by'
        ).get(id=offer_id)

        if not offer.sent_by or not offer.sent_by.email:
            return

        candidate_name = f"{offer.application.first_name} {offer.application.last_name}"
        action_word    = 'accepted' if action == 'accept' else 'declined '

        plain_text = (
            f"Hi {offer.sent_by.full_name or 'there'},\n\n"
            f"{candidate_name} has {action_word} the offer for {offer.position_title}.\n\n"
            f"Note     : {offer.candidate_response_note or 'None'}\n"
            f"Responded: {offer.responded_at.strftime('%B %d, %Y at %I:%M %p') if offer.responded_at else 'N/A'}\n\n"
            f"Log in to the platform to view the updated application."
        )

        msg = EmailMultiAlternatives(
            subject=f"{candidate_name} {action_word} the offer — {offer.position_title}",
            body=plain_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[offer.sent_by.email],
        )
        msg.send()

    except Exception as e:
        logger.error(f"Offer response email task failed: {e}")
        raise self.retry(exc=e)