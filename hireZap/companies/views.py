from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from companies.serializers import(
    CreateCompanySerializer,
)
from infrastructure.repositories.company_repository import CompanyRepository
from core.use_cases.company.create_company import CreateCompanyUseCase
from core.use_cases.company.get_company import GetCompanyUseCase
from core.use_cases.company.pending_company import GetPendingCompanyUseCase
company_repo = CompanyRepository()
create_use_case = CreateCompanyUseCase(company_repo)
get_company_use_case = GetCompanyUseCase(company_repo)
list_company_use_case = GetPendingCompanyUseCase(company_repo)

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