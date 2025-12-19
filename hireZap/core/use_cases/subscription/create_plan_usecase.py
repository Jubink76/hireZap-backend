from core.interface.subscription_plan_repository_port import SubscriptionPlanRepositoryPort
from core.entities.subscription import SubscriptionPlan
import logging

logger = logging.getLogger(__name__)

class CreatePlanUsecase:
    def __init__(self, repository:SubscriptionPlanRepositoryPort):
        self.repository = repository

    def execute(self,plan_data:dict) -> dict:
        try:
            required_fields = ['name','price','period','button_text','user_type',]
            for field in required_fields:
                if field not in plan_data or not plan_data[field]:
                    return{
                        'success':False,
                        'error':f'{field} is required'
                    }
            print(f"plan data", plan_data['description'])
            plan_entity = SubscriptionPlan(
                name=plan_data['name'],
                price=plan_data['price'],
                period=plan_data['period'],
                description=plan_data.get('description', ''),  
                features=plan_data.get('features', []),  
                button_text=plan_data['button_text'],
                card_color=plan_data.get('card_color', 'cyan'),  
                user_type=plan_data['user_type'],
                badge=plan_data.get('badge'),  
                is_default=plan_data.get('is_default', False),  
                is_active=plan_data.get('is_active', True)

            )
            created_plan = self.repository.create_plan(plan_entity)
            
            return {
                'success':True,
                'data':created_plan.to_dict(),
                'message':'Subscription plan created successfully'
            }
        except Exception as e:
            logger.error(f'Error creating subscription plan: {str(e)}')
            return {
                'success':False,
                'error':f'Failed to create plan:{str(e)}'
            }