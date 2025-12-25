from core.interface.subscription_plan_repository_port import SubscriptionPlanRepositoryPort
import logging

logger = logging.getLogger(__name__)

class GetInactivePlanUsecase:
    def __init__(self, repository: SubscriptionPlanRepositoryPort):
        self.repository = repository
        
    def execute(self,user_type:str=None) -> dict:
        try:
            plans = self.repository.get_inactive_plans(user_type)
            if plans is None:  # Only if query actually failed
                logger.error("Failed to fetch inactive plans")
                return {
                    'success': False,
                    'error': "Failed to fetch inactive plans"
                }
            logger.info("inactive plans fetched successfully")
            return {
                'success':True,
                'data':[plan.to_dict() for plan in plans],
                'message':"Inactive plans retrieved successfully"
            }
        except Exception as e:
            logger.error(f"failed to fetch inactive plans, {str(e)}")
            return {
                'success':False,
                'error':'Failed to fetch inactive plans'
            }