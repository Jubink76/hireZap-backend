from core.interface.subscription_plan_repository_port import SubscriptionPlanRepositoryPort
import logging

logger = logging.getLogger(__name__)
class UpdatelanUsecase:
    def __init__(self,repository:SubscriptionPlanRepositoryPort):
        self.repository = repository

    def execute(self,plan_id:int, plan_data:dict) -> dict:
        try:
            existing_plan = self.repository.get_plan_by_id(plan_id)
            if not existing_plan:
                logger.error(f"Plan {plan_id} not found")
                return {
                    'success': False,
                    'error': 'Plan not found'
                }
            
            if existing_plan.is_free:
                
                allowed_fields = ['name','description','features','button_text']
                plan_data = {k:v for k,v in plan_data.items() if k in allowed_fields}

                plan_data['is_free'] = True
                plan_data['is_default'] = True
                plan_data['price'] = 0
                plan_data['card_color'] = 'gray'
                plan_data['badge'] = None

            updated_plan = self.repository.update_plan(plan_id, plan_data)

            if not updated_plan:
                return {
                    'success':False,
                    'error':'Failed to deleted plan'
                }
            return {
                'success':True,
                'data':updated_plan.to_dict(),
                'message':'Subscription plan updated successfully'
            }
        except Exception as e:
            logger.error(f'error updating plan {plan_id} : {str(e)}')
            return {
                'success':False,
                'error':f'Failed to update plan {str(e)}'
            }