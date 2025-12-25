from core.interface.subscription_plan_repository_port import SubscriptionPlanRepositoryPort
import logging

logger = logging.getLogger(__name__)

class ReactivatePlanUsecase:
    def __init__(self, repository: SubscriptionPlanRepositoryPort):
        self.repository = repository

    def execute(self,plan_id:int) -> dict:
        try:
            existing_plan = self.repository.get_plan_by_id(plan_id)
            if not existing_plan:
                return {
                    'success':False,
                    'error':'plan not found'
                }
            if existing_plan.is_active:
                return {
                    'success':False,
                    'error':'Plan is already active'
                }
            if existing_plan.is_free:
                active_plans = self.repository.get_active_plans(existing_plan.user_type)
                active_free_plans = [p for p in active_plans if p.is_free]

                if active_free_plans:
                    logger.warning(f"cannot reactivate this free plan, already free plan exist")
                    return {
                        'success':False,
                        'error':f'A free plan already exist'
                    }
                
            active_plans = self.repository.get_active_plans(existing_plan.user_type)
            duplicate_name = any(
                p.name.lower() == existing_plan.name.lower() and p.id != plan_id for p in active_plans
            )
            if duplicate_name:
                logger.warning("Another plan already exist with this name")
                return {
                    'success':False,
                    'error':"Already plan exist with this name"
                }
            
            reactivate_plan = self.repository.reactivate_plan(plan_id)
            if not reactivate_plan:
                return {
                    'success':False,
                    'error':'Failed to ractivate plan'
                }
            logger.info(f"plan {plan_id} reactivated successfully")
            return {
                'success':True,
                'data':reactivate_plan.to_dict(),
                'message':f"Subscription plan reactivated successfully"
            }
        except Exception as e:
            logger.error(f"error reactivate plan {plan_id}, {str(e)}")
            return {
                'success':False,
                'error':f"failed to reactivate plan,{str(e)}"
            }
