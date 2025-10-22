from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from companies.serializers import(
    CreateCompanySerializer,
)
from infrastructure.repositories.company_repository import CompanyRepository
from core.use_cases.company.create_company import CreateCompanyUseCase
from core.use_cases.company.get_company import GetCompanyUseCase
from core.use_cases.company.pending_company import GetPendingCompanyUseCase
from core.use_cases.company.fetch_company_by_id import FetchCompanyByIdUsecase
from core.use_cases.company.approve_company import ApproveCompanyUsecase
from core.use_cases.company.reject_company import RejectCompanyUsecase

company_repo = CompanyRepository()
create_use_case = CreateCompanyUseCase(company_repo)
get_company_use_case = GetCompanyUseCase(company_repo)
list_company_use_case = GetPendingCompanyUseCase(company_repo)
fetch_company_by_id_use_case = FetchCompanyByIdUsecase(company_repo)
approve_company_use_case = ApproveCompanyUsecase(company_repo)
rejecet_company_use_case = RejectCompanyUsecase(company_repo)

class CreateCompanyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'recruiter':
            return Response(
                {'error': 'Only recruiters can create companies'},
                status = status.HTTP_403_FORBIDDEN
            )
        serializer = CreateCompanySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error':serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        result = create_use_case.execute(request.user.id, serializer.validated_data)
        if not result['success']:
            return Response(
                {'error': result['error']},
                status = status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {
                'message': 'Company created successfully. Pending verification.',
                'company' : result['company']
            },
            status=status.HTTP_201_CREATED
        )

class FetchCompanyById(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,company_id):
        res = fetch_company_by_id_use_case.execute(company_id)
        if not res['success']:
            return Response(
                {'error': res['error']}, status= status.HTTP_404_NOT_FOUND
            )
        return Response(res['company'], status=status.HTTP_200_OK)

class FetchCompanyByRecruiterView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        res = get_company_use_case.execute(request.user.id)
        if not res['success']:
            return Response(
                {'error': res['error']},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(res['company'], status=status.HTTP_200_OK)
    
class ListPendingCompanies(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        res = list_company_use_case.execute()
        if not res['success']:
            return Response(
                {'error': res['error']},status = status.HTTP_404_NOT_FOUND
            )
        print(res)
        return Response(res['companies'], status= status.HTTP_200_OK)

class ApproveCompany(APIView):
    permission_classes = [IsAdminUser]

    def post(self,request, company_id):
        res = approve_company_use_case.execute(company_id)
        if not res['success']:
            return Response(
                {'error': res['error']}, status= status.HTTP_404_NOT_FOUND
            )
        
        # 🔥 SEND WEBSOCKET NOTIFICATION
        company = res['company']
        recruiter_id = company.get('recruiter_id') or company.get('recruiter')
        
        if recruiter_id:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{recruiter_id}',  # Room name
                {
                    'type': 'company_verified',  # Calls company_verified() in consumer
                    'company': company,
                    'message': 'Your company has been verified!'
                }
            )

        return Response(
            {
                'message': "Company verified successfully",
                'company' : res['company']
            },
            status=status.HTTP_200_OK
        )
    
class RejectCompany(APIView):
    permission_classes = [IsAdminUser]

    def post(self,request, company_id):
        reason = request.data.get('reason')
        res = rejecet_company_use_case.execute(company_id, reason)
        if not res['success']:
            return Response(
                {'error':res['error']},
                status= status.HTTP_400_BAD_REQUEST
            )
        
        # 🔥 SEND WEBSOCKET NOTIFICATION
        company = res['company']
        recruiter_id = company.get('recruiter_id') or company.get('recruiter')
        
        if recruiter_id:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{recruiter_id}',
                {
                    'type': 'company_rejected',
                    'company': company,
                    'reason': reason
                }
            )
            
        return Response(
            {
                'message': "Company rejected successfully",
                'company' : res['company']
            },
            status=status.HTTP_200_OK
        )
