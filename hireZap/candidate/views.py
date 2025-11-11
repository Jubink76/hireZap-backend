from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from core.use_cases.candidate_profile.update_profile_usecase import UpdateProfileUsecase
from core.use_cases.candidate_profile.get_complete_profile_usecase import GetCompleteProfileUsecase
from core.use_cases.candidate_profile.add_education_usecase import AddEducationUsecase
from core.use_cases.candidate_profile.add_experience_usecase import AddExperienceUsecase
from core.use_cases.candidate_profile.add_skills_usecase import AddSkillUsecase
from core.use_cases.candidate_profile.add_certification_usecase import AddCertificationUsecase
from infrastructure.repositories.candidate_repository import CandidateRepository

# Import serializers
from .serializers import (
    CandidateProfileSerializer,
    EducationSerializer,
    ExperienceSerializer,
    SkillSerializer,
    CertificationSerializer
)

import logging
logger = logging.getLogger(__name__)

# Initialize repository and use cases
candidate_repo = CandidateRepository()
update_profile_usecase = UpdateProfileUsecase(candidate_repo)
get_complete_profile_usecase = GetCompleteProfileUsecase(candidate_repo)
add_education_usecase = AddEducationUsecase(candidate_repo)
add_experience_usecase = AddExperienceUsecase(candidate_repo)
add_skill_usecase = AddSkillUsecase(candidate_repo)  # Fixed typo
add_certificate_usecase = AddCertificationUsecase(candidate_repo)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get complete profile with all related data"""
        result = get_complete_profile_usecase.execute(request.user.id)
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(result, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """Update user profile with validation"""
        # Validate incoming data
        serializer = CandidateProfileSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute use case with validated data
        result = update_profile_usecase.execute(
            user_id=request.user.id,  
            profile_data=serializer.validated_data
        )
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result, status=status.HTTP_200_OK)


class SkillView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all skills for the current user"""
        skills = candidate_repo.get_skills(request.user.id)
        return Response({
            "success": True,
            "skills": [skill.to_dict() for skill in skills]
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Add new skill with validation"""
        # Validate incoming data
        serializer = SkillSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute use case with validated data
        result = add_skill_usecase.execute(
            candidate_id=request.user.id,
            skill_data=serializer.validated_data
        )
        
        if not result['success']:
            return Response(
                {'error': result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result, status=status.HTTP_201_CREATED)


class SkillDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, skill_id):
        """Delete a skill"""
        skill = candidate_repo.get_skill_by_id(skill_id)
        if not skill or skill.candidate_id != request.user.id:
            return Response(
                {"error": "Skill not found or unauthorized"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = candidate_repo.delete_skill(skill_id)
        if result:
            return Response(
                {"success": True, "message": "Skill deleted successfully"},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"error": "Failed to delete skill"},
            status=status.HTTP_400_BAD_REQUEST
        )


class EducationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all education records"""
        educations = candidate_repo.get_educations(request.user.id)
        return Response({
            "success": True,
            "educations": [edu.to_dict() for edu in educations]
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Add education with validation"""
        # Validate incoming data
        serializer = EducationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute use case with validated data
        result = add_education_usecase.execute(
            candidate_id=request.user.id,
            educational_data=serializer.validated_data
        )

        if not result['success']:
            return Response(
                {"error": result.get("error")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result, status=status.HTTP_201_CREATED)


class EducationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, education_id):
        """Delete education record"""
        education = candidate_repo.get_education_by_id(education_id)
        if not education or education.candidate_id != request.user.id:
            return Response(
                {"error": "Education not found or unauthorized"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = candidate_repo.delete_education(education_id)
        if result:
            return Response(
                {"success": True, "message": "Education deleted successfully"},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"error": "Failed to delete education"},
            status=status.HTTP_400_BAD_REQUEST
        )


class ExperienceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all experiences"""
        experiences = candidate_repo.get_experiences(request.user.id)
        return Response({
            "success": True,
            "experiences": [exp.to_dict() for exp in experiences]
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Add experience with validation"""
        # Validate incoming data
        serializer = ExperienceSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute use case with validated data
        result = add_experience_usecase.execute(
            candidate_id=request.user.id,
            experience_data=serializer.validated_data
        )
        
        if not result['success']:
            return Response(
                {"error": result.get("error")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result, status=status.HTTP_201_CREATED)


class ExperienceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, experience_id):
        """Delete experience"""
        experience = candidate_repo.get_experience_by_id(experience_id)
        if not experience or experience.candidate_id != request.user.id:
            return Response(
                {"error": "Experience not found or unauthorized"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = candidate_repo.delete_experience(experience_id)
        if result:
            return Response(
                {"success": True, "message": "Experience deleted successfully"},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"error": "Failed to delete experience"},
            status=status.HTTP_400_BAD_REQUEST
        )


class CertificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all certifications"""
        certifications = candidate_repo.get_certifications(request.user.id)  # Fixed method name
        return Response({
            "success": True,
            "certifications": [cert.to_dict() for cert in certifications]
        }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Add certification with validation"""
        # Validate incoming data
        serializer = CertificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute use case with validated data
        result = add_certificate_usecase.execute(
            candidate_id=request.user.id,
            certification_data=serializer.validated_data
        )
        
        if not result['success']:
            return Response(
                {"error": result.get("error")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(result, status=status.HTTP_201_CREATED)


class CertificationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, certification_id):
        """Delete certification"""
        certification = candidate_repo.get_certification_by_id(certification_id)
        if not certification or certification.candidate_id != request.user.id:
            return Response(
                {"error": "Certification not found or unauthorized"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        result = candidate_repo.delete_certification(certification_id)
        if result:
            return Response(
                {"success": True, "message": "Certification deleted successfully"},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"error": "Failed to delete certification"},
            status=status.HTTP_400_BAD_REQUEST
        )