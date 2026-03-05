from django.urls import path
from offer.views import (
    RankedCandidatesAPIView,
    SendOfferView,
    BulkSendOfferView,
    CandidateRespondOfferView,
    GetApplicationOfferView
)
urlpatterns = [
    path('jobs/<int:job_id>/offer-stage/',RankedCandidatesAPIView.as_view(), name='offer-stage-candidates'),
    path('applications/<int:application_id>/offer/send/', SendOfferView.as_view(), name='send-offer'),
    path('jobs/<int:job_id>/offer/bulk-send/',BulkSendOfferView.as_view(), name='bulk-send-offer'),
    path('applications/<int:application_id>/offer/', GetApplicationOfferView.as_view(), name='get-offer'),
    path('<int:offer_id>/respond/', CandidateRespondOfferView.as_view(), name='respond-offer'),
]