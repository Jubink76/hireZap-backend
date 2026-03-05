import logging
from typing import Dict
from core.interface.offer_repository_port import OfferRepositoryPort

logger = logging.getLogger(__name__)


class RespondToOfferUseCase:
    def __init__(self, offer_repo: OfferRepositoryPort, notification_service):
        self.offer_repo           = offer_repo
        self.notification_service = notification_service

    def execute(self, offer_id: int, action: str, note: str = None) -> Dict:
        if action not in ('accept', 'decline'):
            return {'success': False, 'error': "Action must be 'accept' or 'decline'"}

        try:
            offer = self.offer_repo.candidate_respond(offer_id, action, note)
        except ValueError as e:
            return {'success': False, 'error': str(e)}

        # Notify recruiter via WebSocket
        self._notify_recruiter_websocket(offer, action)

        # Notify recruiter via email (async)
        self._send_response_email(offer, action)

        return {'success': True, 'offer': offer}

    def _notify_recruiter_websocket(self, offer, action: str):
        try:
            recruiter_id = offer.sent_by_id
            if not recruiter_id:
                return

            candidate_name = f"{offer.application.first_name} {offer.application.last_name}"
            action_label   = 'accepted' if action == 'accept' else 'declined'

            self.notification_service.send_websocket_notification(
                user_id=recruiter_id,
                notification_type='offer_responded',
                data={
                    'offer_id'       : offer.id,
                    'application_id' : offer.application_id,
                    'candidate_name' : candidate_name,
                    'position_title' : offer.position_title,
                    'action'         : action,
                    'message'        : f"{candidate_name} has {action_label} the offer for {offer.position_title}",
                }
            )
        except Exception as e:
            logger.error(f"Recruiter WebSocket notification failed: {e}")

    def _send_response_email(self, offer, action: str):
        try:
            from offer.tasks import send_offer_response_email_task
            send_offer_response_email_task.apply_async(
                args=[offer.id, action],
                countdown=3
            )
        except Exception as e:
            logger.error(f"Offer response email task failed: {e}")