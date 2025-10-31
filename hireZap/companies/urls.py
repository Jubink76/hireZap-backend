from django.urls import path
from companies.views import(
    CreateCompanyView,
    FetchCompanyByRecruiterView,
    ListPendingCompanies,
    FetchCompanyById,
    ApproveCompany,
    RejectCompany,
    ListRejectedCompanies,
    ListVerifiedCompanies,
    UpdateCompany
)

urlpatterns = [
    path('create-company/',CreateCompanyView.as_view(), name='create-company'),
    path('details/',FetchCompanyByRecruiterView.as_view(),name="company-details"),
    path('pending-companies/',ListPendingCompanies.as_view(),name='pending-companies'),
    path('fetch-company/<int:company_id>/',FetchCompanyById.as_view(),name='fetch-company'),
    path('approve-company/<int:company_id>/',ApproveCompany.as_view(),name='approve-company'),
    path('reject-company/<int:company_id>/',RejectCompany.as_view(),name='reject-company'),
    path('verified-companies/',ListVerifiedCompanies.as_view(),name='verified-companies'),
    path('rejected-companies/',ListRejectedCompanies.as_view(),name='rejected-companies'),
    path('update-company/<int:company_id>/',UpdateCompany.as_view(),name='update-company'),
]