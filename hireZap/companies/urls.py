from django.urls import path
from companies.views import(
    CreateCompanyView,
    FetchCompanyByRecruiterView,
    ListPendingCompanies
)

urlpatterns = [
    path('company/create-company/',CreateCompanyView.as_view(), name='create-company'),
    path('company/details/',FetchCompanyByRecruiterView.as_view(),name="company-details"),
    path('company/pending-companies/',ListPendingCompanies.as_view(),name='pending-companies'),
]