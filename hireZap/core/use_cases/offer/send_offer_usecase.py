import logging
from io import BytesIO
from typing import List, Dict
from application.models import ApplicationModel
from core.interface.offer_repository_port import OfferRepositoryPort
from infrastructure.utils.pdf_generator import generate_offer_letter_pdf

logger = logging.getLogger(__name__)


class SendOfferUseCase:
    def __init__(
        self,
        offer_repo: OfferRepositoryPort,
        notification_service,
        storage_service,
    ):
        self.offer_repo           = offer_repo
        self.notification_service = notification_service
        self.storage              = storage_service

    def execute(self, application_id: int, data: dict, recruiter_user_id: int) -> Dict:
        # 1. Validate application exists and is in offer stage
        try:
            app = ApplicationModel.objects.select_related(
                'job__company', 'candidate', 'current_stage'
            ).get(id=application_id)
        except ApplicationModel.DoesNotExist:
            return {'success': False, 'error': 'Application not found'}

        if app.status not in ('shortlisted', 'offered'):
            return {
                'success': False,
                'error': f'Candidate is not in offer stage (status: {app.status})'
            }

        # 2. Prevent duplicate offers
        existing = self.offer_repo.get_offer_by_application(application_id)
        if existing:
            return {'success': False, 'error': 'Offer already sent to this candidate'}

        # 3. Create offer record
        offer = self.offer_repo.create_and_send_offer(
            application_id=application_id,
            data=data,
            sent_by_user_id=recruiter_user_id,
        )

        # 4. Generate PDF and upload to R2
        pdf_url = self._generate_and_upload_pdf(offer)
        if pdf_url:
            offer.offer_letter_url = pdf_url
            offer.save(update_fields=['offer_letter_url'])

        # 5. Send email with PDF attached
        self._send_offer_email(offer, pdf_url)

        # 6. WebSocket notification to candidate
        self._notify_candidate_websocket(offer)

        return {'success': True, 'offer': offer}

    def _generate_and_upload_pdf(self, offer) -> str | None:
        try:
            pdf_bytes = generate_offer_letter_pdf(offer)
            candidate_name = f"{offer.application.first_name}_{offer.application.last_name}"
            filename = f"offer_{offer.id}_{candidate_name}.pdf"

            file_like = BytesIO(pdf_bytes)
            result = self.storage.upload_file(
                file=file_like,
                folder='offer_letters',
                filename=filename,
                content_type='application/pdf',
                make_public=True,
            )
            return result.get('url')
        except Exception as e:
            logger.error(f"PDF generation/upload failed for offer {offer.id}: {e}")
            return None

    def _send_offer_email(self, offer, pdf_url: str | None):
        try:
            from offer.tasks import send_offer_email_task
            send_offer_email_task.apply_async(
                args=[offer.id],
                countdown=3
            )
        except Exception as e:
            logger.error(f"Offer email task failed for offer {offer.id}: {e}")

    def _notify_candidate_websocket(self, offer):
        try:
            self.notification_service.send_websocket_notification(
                user_id=offer.application.candidate_id,
                notification_type='offer_received',
                data={
                    'application_id': offer.application_id,
                    'job_title'     : offer.application.job.job_title,
                    'company_name'  : offer.application.job.company.company_name,
                    'position_title': offer.position_title,
                    'message'       : f"🎉 You have received an offer for {offer.position_title}!",
                    'offer_id'      : offer.id,
                }
            )
        except Exception as e:
            logger.error(f"WebSocket notification failed for offer {offer.id}: {e}")


class BulkSendOfferUseCase:
    def __init__(self, offer_repo, notification_service, storage_service):
        self._single = SendOfferUseCase(offer_repo, notification_service, storage_service)

    def execute(self, application_ids: List[int], data: dict, recruiter_user_id: int) -> Dict:
        sent, failed = [], []

        for app_id in application_ids:
            result = self._single.execute(app_id, data, recruiter_user_id)
            if result['success']:
                sent.append(app_id)
            else:
                failed.append({'application_id': app_id, 'reason': result['error']})

        return {
            'success'    : True,
            'sent_count' : len(sent),
            'fail_count' : len(failed),
            'sent'       : sent,
            'failed'     : failed,
        }