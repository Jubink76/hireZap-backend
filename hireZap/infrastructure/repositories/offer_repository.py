from core.interface.offer_repository_port import OfferRepositoryPort
from offer.models import OfferLetterModel
from django.utils import timezone
from django.db.models import Avg, Count
from application.models import ApplicationModel, ApplicationStageHistory
from selection_process.models import SelectionStageModel

class OfferRepository(OfferRepositoryPort):

    def create_and_send_offer(self, application_id:int, data:dict, sent_by_user_id:int) -> OfferLetterModel:
        offer = OfferLetterModel.objects.create(
            application_id=application_id,
            position_title= data['position_title'],
            offered_salary=data['offered_salary'],
            joining_date=data['joining_date'],
            offer_expiry_date=data['offer_expiry_date'],
            custom_message=data.get('custom_message'),
            sent_by_id = sent_by_user_id,
            status='sent',
        )
        ApplicationModel.objects.filter(id=application_id).update(
            status='offered',
            updated_at=timezone.now()
        )
        return offer
    
    def get_offer_by_id(self, offer_id:int):
        try:
            return OfferLetterModel.objects.select_related(
                'application__candidate', 'application__job', 'sent_by'
            ).get(id=offer_id)
        except OfferLetterModel.DoesNotExist:
            return None
        
    def get_offer_by_application(self, application_id:int):
        try:
            return OfferLetterModel.objects.select_related(
                'application__candidate', 'application__job'
            ).get(application_id=application_id)
        except OfferLetterModel.DoesNotExist:
            return None
        
    def candidate_respond(self,offer_id:int, action:str, note:str=None) -> OfferLetterModel:
        offer = self.get_offer_by_id(offer_id)
        if not offer:
            raise ValueError("Offer not found")
        if offer.status != 'sent':
            raise ValueError(f"Cannot respond to offer in '{offer.status}' status")
        if offer.is_expired:
            raise ValueError("This offer is expired")
        
        offer.status = 'accepted' if action =='accept' else 'declined'
        offer.candidate_response_note = note
        offer.responded_at = timezone.now()
        offer.save(update_fields=['status', 'candidate_response_note', 'responded_at', 'updated_at'])

        new_app_status = 'hired' if action =='accept' else 'rejected'
        new_stage_status = 'qualified' if action == 'accept' else 'rejected'
        ApplicationModel.objects.filter(id=offer.application_id).update(
            status=new_app_status,
            current_stage_status=new_stage_status,
            updated_at = timezone.now()
        )

        app = offer.application
        if app.current_stage_id:
            ApplicationStageHistory.objects.update_or_create(
                application=app,
                stage_id=app.current_stage_id,
                defaults={
                    'status':'qualified' if action == 'accept' else 'rejected',
                    'feedback':note,
                    'completed_at':timezone.now(),
                }
            )
        return offer
    
    def get_candidate_by_rank(self, job_id:int) -> list:

        offer_stage = SelectionStageModel.objects.filter(slug='offer').first()
        if not offer_stage:
            return []
        
        applications = (
            ApplicationModel.objects.filter(
                job_id=job_id,
                current_stage = offer_stage,
                status__in=['shortlisted', 'offered', 'hired', 'rejected']
            )
            .select_related('candidate','current_stage')
            .prefetch_related('stage_history__stage','offer_letter')
        )
        ranked = []
        for app in applications:
            histories = [
                h for h in app.stage_history.all()
                if h.stage_id != offer_stage.id and h.completed_at is not None
            ]
            histories_sorted = sorted(histories, key=lambda h: h.completed_at)
            last_history     = histories_sorted[-1] if histories_sorted else None
            last_score       = last_history.score if last_history and last_history.score is not None else 0

            offer = getattr(app, 'offer_letter', None)

            ranked.append({
                'application_id'     : app.id,
                'candidate_id'       : app.candidate_id,
                'name'               : f"{app.first_name} {app.last_name}",
                'email'              : app.email,
                'phone'              : app.phone,
                'location'           : app.location,
                'current_company'    : app.current_company,
                'years_of_experience': app.years_of_experience,
                'resume_url'         : app.resume_url,
                'linkedin_profile'   : app.linkedin_profile,
                'application_status' : app.status,
                'last_score'         : last_score,
                'last_stage_name'    : last_history.stage.name if last_history else None,
                'stage_performances' : [
                    {
                        'stage_id'    : h.stage_id,
                        'stage_name'  : h.stage.name,
                        'status'      : h.status,
                        'score'       : h.score,
                        'feedback'    : h.feedback,
                        'started_at'  : h.started_at,
                        'completed_at': h.completed_at,
                    }
                    for h in histories_sorted
                ],
                'offer_status': offer.status if offer else None,
                'offer_id'    : offer.id if offer else None,
                'offer_letter_url'   : offer.offer_letter_url if offer else None,
            })

        ranked.sort(key=lambda x: x['last_score'], reverse=True)
        return ranked