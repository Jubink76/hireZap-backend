import PyPDF2
import io
import requests
import re
from typing import Dict, List

class ResumeParser:
    """Extract structured data from resume"""
    def download_resume(self, resume_url: str) -> bytes:
        """Download resume from cloudinary"""
        try:
            response = requests.get(resume_url, timeout=30, stream=True)
            response.raise_for_status()
            content = b''
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    content += chunk

            return content
        
        except Exception as e:
            raise Exception(f"Failed to download resume: {str(e)}")
    
    def extract_text_from_pdf(self,pdf_content:bytes) -> str:
        """Extract text from pdf"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to parse PDF: {str(e)}")
        
    def extract_experience_years(self, text:str) -> float:
        """ Extract year of experience from resume"""
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of)?\s*experience',
            r'(experience\s*(?:of)?\s*(\d+)\+s*years)',
            r'(\d+)\s*years?\s*in',
        ]
        max_years = 0
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                years = int(match)
                max_years = max(max_years, years)

        return float(max_years)
    
    def extract_education(self, text:str) -> str:
        """Extract highest education level"""
        education_levels = [
            'phd', 'ph.d', 'doctorate',
            'master', 'msc', 'mba', 'ma',
            'bachelor', 'bsc', 'ba', 'btech', 'be',
            'diploma', 'associate',
        ]
        text_lower = text.lower()
        for level in education_levels:
            if level in text.lower:
                return level.title()
            
        return "Not specified"

    def find_skills(self, text: str, skill_list: List[str]) -> List[str]:
        """Find which skills from the list are in resume"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in skill_list:
            # Check for whole word match
            if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                found_skills.append(skill)
        
        return found_skills
    
    def find_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Find keywords in resume"""
        return self.find_skills(text, keywords)
    
    def check_ats_friendliness(self, text: str, pdf_content: bytes) -> tuple:
        """Check if resume is ATS-friendly"""
        issues = []
        
        # Check if text was extracted successfully
        if len(text) < 100:
            issues.append("Very short text extracted - may have formatting issues")
        
        # Check for common ATS issues
        if len(text) > 10000:
            issues.append("Resume is too long (over 10,000 characters)")
        
        # Check for special characters that might cause issues
        special_char_count = len(re.findall(r'[^a-zA-Z0-9\s\.\,\-\(\)]', text))
        if special_char_count > 100:
            issues.append("Too many special characters detected")
        
        is_ats_friendly = len(issues) == 0
        
        return is_ats_friendly, issues