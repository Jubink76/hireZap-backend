from core.interface.subscription_plan_repository_port import SubscriptionPlanRepositoryPort
import logging 

logger = logging.getLogger(__name__)

class GetALLPlansUsecase:
    def __init__(self, repository:SubscriptionPlanRepositoryPort):
        self.repository = repository
    
    def execute(self, user_type: str=None) -> dict:
        try:
            plans = self.repository.get_active_plans(user_type) if user_type else self.repository.get_all_plans()
            return {
                'success':True,
                'data':[plan.to_dict() for plan in plans],
                'message':'Plans retrieved successfully'
            }
        except Exception as e :
            logger.error(f"Error fetching plans: {str(e)}")
            return {
                'success':False,
                'error':'Failed to fetch plans',
                'data':[]
            }