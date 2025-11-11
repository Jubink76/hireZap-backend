from django.urls import path
from candidate.views import(
    ProfileView,
    SkillView,
    SkillDetailView,
    EducationListView,
    EducationDetailView,
    ExperienceListView,
    ExperienceDetailView,
    CertificationListView,
    CertificationDetailView
)

urlpatterns = [
    path('profile/', ProfileView.as_view(), name='candidate-profile'),
    path('skills/', SkillView.as_view(), name='candidate-skills'),
    path('skills/<int:skill_id>/', SkillDetailView.as_view(), name='skill-detail'),
    path('educations/', EducationListView.as_view(), name='candidate-educations'),
    path('educations/<int:education_id>/', EducationDetailView.as_view(), name='education-detail'),
    path('experiences/', ExperienceListView.as_view(), name='candidate-experiences'),
    path('experiences/<int:experience_id>/', ExperienceDetailView.as_view(), name='experience-detail'),
    path('certifications/', CertificationListView.as_view(), name='candidate-certifications'),
    path('certifications/<int:certification_id>/', CertificationDetailView.as_view(), name='certification-detail'),
]
