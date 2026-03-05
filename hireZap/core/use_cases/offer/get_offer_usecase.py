from typing import Dict
from core.interface.offer_repository_port import OfferRepositoryPort


class GetRankedCandidatesUseCase:
    def __init__(self, offer_repo: OfferRepositoryPort):
        self.offer_repo = offer_repo

    def execute(self, job_id: int) -> Dict:
        ranked = self.offer_repo.get_candidate_by_rank(job_id)
        return {
            'success'   : True,
            'total'     : len(ranked),
            'candidates': ranked,
        }


class GetOfferDetailUseCase:
    def __init__(self, offer_repo: OfferRepositoryPort):
        self.offer_repo = offer_repo

    def execute(self, application_id: int) -> Dict:
        offer = self.offer_repo.get_offer_by_application(application_id)
        if not offer:
            return {'success': False, 'error': 'No offer found for this application'}
        return {'success': True, 'offer': offer}