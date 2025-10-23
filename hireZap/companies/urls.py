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
)

urlpatterns = [
    path('company/create-company/',CreateCompanyView.as_view(), name='create-company'),
    path('company/details/',FetchCompanyByRecruiterView.as_view(),name="company-details"),
    path('company/pending-companies/',ListPendingCompanies.as_view(),name='pending-companies'),
    path('company/fetch-company/<int:company_id>/',FetchCompanyById.as_view(),name='fetch-company'),
    path('company/approve-company/<int:company_id>/',ApproveCompany.as_view(),name='approve-company'),
    path('company/reject-company/<int:company_id>/',RejectCompany.as_view(),name='reject-company'),
    path('company/verified-companies/',ListVerifiedCompanies.as_view(),name='verified-companies'),
    path('company/rejected-companies/',ListRejectedCompanies.as_view(),name='rejected-companies'),
]