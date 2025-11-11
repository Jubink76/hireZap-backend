from typing import Optional, List
from core.interface.candidate_profile_repository_port import CandidateRepositoryPort
from core.entities.candidate_profile import (
    CandidateProfile as ProfileEntity,
    Education as EducationEntity,
    Experience as ExperienceEntity,
    Skill as SkillEntity,
    Certification as CertificationEntity
)

from candidate.models import (
    CandidateProfile,
    CandidateEducation,
    CandidateExperience,
    CandidateSkill,
    CandidateCertification
)

class CandidateRepository(CandidateRepositoryPort):
    def get_profile_by_user_id(self, user_id: int) -> Optional[ProfileEntity]:
        try:
            profile = CandidateProfile.objects.select_related('user').get(user_id=user_id)
            return self._profile_to_entity(profile)
        except CandidateProfile.DoesNotExist:
            return None
        
    def update_profile(self, profile: ProfileEntity) -> ProfileEntity:
        try:
            model = CandidateProfile.objects.get(user_id=profile.user_id)
            # Update fields
            if profile.bio is not None:
                model.bio = profile.bio
            if profile.phone_number is not None:
                model.phone_number = profile.phone_number
            if profile.linkedin_url is not None:
                model.linkedin_url = profile.linkedin_url
            if profile.github_url is not None:
                model.github_url = profile.github_url
            if profile.location is not None:
                model.location = profile.location
            if profile.website is not None:
                model.website = profile.website
            if profile.resume_url is not None:
                model.resume_url = profile.resume_url

            model.save()
            return self._profile_to_entity(model)
        except CandidateProfile.DoesNotExist:
            raise ValueError("Profile does not exist")
        
    def get_complete_profile(self, user_id: int) -> Optional[dict]:
        try:
            profile = CandidateProfile.objects.select_related('user').prefetch_related(
                'educations', 'experiences', 'skills', 'certifications'
            ).get(user_id=user_id)
            return {
                'profile': self._profile_to_entity(profile),
                'educations': self.get_educations(user_id),
                'experiences': self.get_experiences(user_id),
                'skills': self.get_skills(user_id),
                'certifications': self.get_certifications(user_id)
            }
        except CandidateProfile.DoesNotExist:
            return None

    def _profile_to_entity(self, model: CandidateProfile) -> ProfileEntity:
        return ProfileEntity(
            user_id=model.user_id,
            bio=model.bio,
            phone_number=model.phone_number,
            linkedin_url=model.linkedin_url,
            github_url=model.github_url,
            location=model.location,
            resume_url=model.resume_url,
            website=model.website,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    ### Educational methods 

    def get_educations(self, candidate_id: int) -> List[EducationEntity]:
        educations = CandidateEducation.objects.filter(candidate_id=candidate_id)
        return [self._education_to_entity(edu) for edu in educations]
    
    def add_education(self, education: EducationEntity) -> EducationEntity:
        model = CandidateEducation.objects.create(
            candidate_id=education.candidate_id,  # Fixed typo
            degree=education.degree,
            field_of_study=education.field_of_study,
            institution=education.institution,
            start_year=education.start_year,
            end_year=education.end_year,
        )
        education.id = model.id
        education.created_at = model.created_at
        education.updated_at = model.updated_at
        return education
    
    def get_education_by_id(self, education_id: int) -> Optional[EducationEntity]:
        try:
            education = CandidateEducation.objects.select_related('candidate').get(id=education_id)
            return self._education_to_entity(education)
        except CandidateEducation.DoesNotExist:
            return None
        
    def update_education(self, education: EducationEntity) -> EducationEntity:
        model = CandidateEducation.objects.get(id=education.id)
        model.degree = education.degree
        model.field_of_study = education.field_of_study
        model.institution = education.institution
        model.start_year = education.start_year
        model.end_year = education.end_year
        model.save()
        education.updated_at = model.updated_at
        return education
    
    def delete_education(self, education_id: int) -> bool:
        try:
            CandidateEducation.objects.get(id=education_id).delete()
            return True
        except CandidateEducation.DoesNotExist:
            return False

    def _education_to_entity(self, model: CandidateEducation) -> EducationEntity:
        return EducationEntity(
            id=model.id,
            candidate_id=model.candidate_id,  # Access FK's primary key
            degree=model.degree,
            field_of_study=model.field_of_study,
            institution=model.institution,  # Fixed typo
            start_year=model.start_year,
            end_year=model.end_year,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    ### Experience methods
    def get_experiences(self, candidate_id: int) -> List[ExperienceEntity]:
        experiences = CandidateExperience.objects.filter(candidate_id=candidate_id)
        return [self._experience_to_entity(exp) for exp in experiences]
    
    def add_experience(self, experience: ExperienceEntity) -> ExperienceEntity:
        model = CandidateExperience.objects.create(
            candidate_id=experience.candidate_id,
            company_name=experience.company_name,
            role=experience.role,
            start_date=experience.start_date,
            end_date=experience.end_date,
            description=experience.description
        )
        experience.id = model.id
        experience.created_at = model.created_at
        experience.updated_at = model.updated_at
        return experience
    
    def get_experience_by_id(self, experience_id: int) -> Optional[ExperienceEntity]:
        try:
            experience = CandidateExperience.objects.select_related('candidate').get(id=experience_id)
            return self._experience_to_entity(experience)
        except CandidateExperience.DoesNotExist:
            return None
    
    def update_experience(self, experience: ExperienceEntity) -> ExperienceEntity:
        model = CandidateExperience.objects.get(id=experience.id)
        model.company_name = experience.company_name
        model.role = experience.role
        model.start_date = experience.start_date
        model.end_date = experience.end_date
        model.description = experience.description
        model.save()
        experience.updated_at = model.updated_at
        return experience
    
    def delete_experience(self, experience_id: int) -> bool:
        try:
            CandidateExperience.objects.get(id=experience_id).delete()
            return True
        except CandidateExperience.DoesNotExist:
            return False
        
    def _experience_to_entity(self, model: CandidateExperience) -> ExperienceEntity:
        return ExperienceEntity(
            id=model.id,
            candidate_id=model.candidate_id,  # Access FK's primary key
            company_name=model.company_name,
            role=model.role,
            start_date=model.start_date,
            end_date=model.end_date,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    ### Skill methods
    def get_skills(self, candidate_id: int) -> List[SkillEntity]:
        skills = CandidateSkill.objects.filter(candidate_id=candidate_id)
        return [self._skill_to_entity(skill) for skill in skills]
    
    def add_skill(self, skill: SkillEntity) -> SkillEntity:
        model = CandidateSkill.objects.create(
            candidate_id=skill.candidate_id,
            skill_name=skill.skill_name,
            proficiency=skill.proficiency,
            years_of_experience=skill.years_of_experience
        )
        skill.id = model.id
        skill.created_at = model.created_at
        skill.updated_at = model.updated_at
        return skill
    
    def get_skill_by_id(self, skill_id: int) -> Optional[SkillEntity]:
        try:
            skill = CandidateSkill.objects.select_related('candidate').get(id=skill_id)
            return self._skill_to_entity(skill)
        except CandidateSkill.DoesNotExist:
            return None
    
    def update_skill(self, skill: SkillEntity) -> SkillEntity:
        model = CandidateSkill.objects.get(id=skill.id)
        model.skill_name = skill.skill_name
        model.proficiency = skill.proficiency
        model.years_of_experience = skill.years_of_experience
        model.save()
        skill.updated_at = model.updated_at
        return skill
    
    def delete_skill(self, skill_id: int) -> bool:
        try:
            CandidateSkill.objects.get(id=skill_id).delete()
            return True
        except CandidateSkill.DoesNotExist:
            return False
        
    def _skill_to_entity(self, model: CandidateSkill) -> SkillEntity:  # Fixed method name
        return SkillEntity(
            id=model.id,
            candidate_id=model.candidate_id,  # Access FK's primary key
            skill_name=model.skill_name,
            proficiency=model.proficiency,
            years_of_experience=model.years_of_experience,  # Fixed typo
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    ### Certification methods
    def get_certifications(self, candidate_id: int) -> List[CertificationEntity]:  # Fixed method name
        certifications = CandidateCertification.objects.filter(candidate_id=candidate_id)
        return [self._certification_to_entity(cert) for cert in certifications]
    
    def add_certification(self, certification: CertificationEntity) -> CertificationEntity:
        model = CandidateCertification.objects.create(
            candidate_id=certification.candidate_id,
            name=certification.name,
            issuer=certification.issuer,
            field=certification.field,
            issue_date=certification.issue_date,
            expiry_date=certification.expiry_date,
            credential_url=certification.credential_url
        )
        certification.id = model.id
        certification.created_at = model.created_at
        certification.updated_at = model.updated_at
        return certification
    
    def get_certification_by_id(self, certification_id: int) -> Optional[CertificationEntity]:
        try:
            certification = CandidateCertification.objects.select_related('candidate').get(id=certification_id)
            return self._certification_to_entity(certification)
        except CandidateCertification.DoesNotExist:
            return None
    
    def update_certification(self, certification: CertificationEntity) -> CertificationEntity:
        model = CandidateCertification.objects.get(id=certification.id)
        model.name = certification.name
        model.issuer = certification.issuer
        model.field = certification.field
        model.issue_date = certification.issue_date
        model.expiry_date = certification.expiry_date
        model.credential_url = certification.credential_url
        model.save()
        certification.updated_at = model.updated_at
        return certification
    
    def delete_certification(self, certification_id: int) -> bool:
        try:
            CandidateCertification.objects.get(id=certification_id).delete()
            return True
        except CandidateCertification.DoesNotExist:
            return False
        
    def _certification_to_entity(self, model: CandidateCertification) -> CertificationEntity:
        return CertificationEntity(
            id=model.id,
            candidate_id=model.candidate_id,  # Access FK's primary key
            name=model.name,
            issuer=model.issuer,
            field=model.field,
            issue_date=model.issue_date,  
            expiry_date=model.expiry_date,
            credential_url=model.credential_url,
            created_at=model.created_at,
            updated_at=model.updated_at
        )