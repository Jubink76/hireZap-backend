from core.interface.subscription_plan_repository_port import SubscriptionPlanRepositoryPort
import logging

logger = logging.getLogger(__name__)
class DeletePlanUsecase:
    def __init__(self,repository:SubscriptionPlanRepositoryPort):
        self.repository = repository

    def execute(self,plan_id:int) -> bool:
        try:
            existing_plan =self.repository.get_plan_by_id(plan_id)
            if not existing_plan:
               logger.error(f"plan {plan_id} not found")
               return {
                   'success':False,
                   'error':'Plan not found'
               }
           
            if existing_plan.is_free:
               logger.warning(f"attempted to delete free plan {plan_id}")
               return {
                   'success':False,
                   'error':'Cannot delete free plan. Free plans are required for all users'
               }
            # Check if users are currently subscribed to this plan
            # Note: You'll need to implement this check based on your subscription model
            # if self.repository.has_active_subscriptions(plan_id):
            #     return {
            #         'success': False,
            #         'error': 'Cannot delete plan with active subscriptions. Please migrate users first.'
            #     }
            
            # Perform soft delete

            success = self.repository.delete_plan(plan_id)
            if not success:
                return {
                    'success':False,
                    'error':'Failed to delete plan'
                }
            logger.info(f"plan {plan_id} successfully deleted")
            return {
                'success':True,
                'message':'Subscription plan deleted successfully'
            }
        except Exception as e:
            logger.error(f"error deleting plan {plan_id}: {str(e)}")
            return {
                'success':False,
                'error':f'Failed to delete plan : {str(e)}'
            }