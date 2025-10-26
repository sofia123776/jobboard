import re
import os

class ResumeParser:
    def __init__(self):
        # Regex patterns for basic extraction
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
    def extract_text(self, file_path, file_type):
        """Mock text extraction - in real implementation, you'd use pdfplumber/docx"""
        # For now, return mock text for testing
        return """
        John Doe
        Software Developer
        john.doe@email.com
        +1-555-0123
        New York, NY
        
        EXPERIENCE
        Senior Software Developer at Tech Company (2020-Present)
        - Developed web applications using Python and Django
        - Led team of 5 developers
        - Implemented REST APIs
        
        Junior Developer at Startup Inc (2018-2020)
        - Built frontend with React
        - Worked with SQL databases
        
        EDUCATION
        Bachelor of Science in Computer Science
        University of Technology (2014-2018)
        
        SKILLS
        Python, Django, JavaScript, React, SQL, Git, AWS, Docker
        """
    
    def parse_resume(self, file_path, file_type):
        """Parse resume and return structured data"""
        text = self.extract_text(file_path, file_type)
        
        # Extract email
        emails = re.findall(self.email_pattern, text)
        email = emails[0] if emails else ""
        
        # Extract phone
        phones = re.findall(self.phone_pattern, text)
        phone = phones[0] if phones else ""
        
        # Simple skill extraction
        skills_keywords = ['python', 'django', 'javascript', 'react', 'sql', 'git', 'aws', 'docker', 
                          'html', 'css', 'java', 'c++', 'node.js', 'express', 'mongodb', 'postgresql']
        found_skills = []
        text_lower = text.lower()
        for skill in skills_keywords:
            if skill in text_lower:
                found_skills.append(skill)
        
        # Mock data structure
        return {
            'raw_text': text,
            'personal_info': {
                'full_name': 'John Doe',
                'email': email,
                'phone': phone,
                'location': 'New York, NY'
            },
            'education': [
                {
                    'institution': 'University of Technology',
                    'degree': 'Bachelor',
                    'dates': ['2014-2018'],
                    'description': ['Bachelor of Science in Computer Science']
                }
            ],
            'experience': [
                {
                    'title': 'Senior Software Developer',
                    'company': 'Tech Company',
                    'dates': ['2020-Present'],
                    'description': ['Developed web applications using Python and Django', 'Led team of 5 developers']
                },
                {
                    'title': 'Junior Developer',
                    'company': 'Startup Inc',
                    'dates': ['2018-2020'],
                    'description': ['Built frontend with React', 'Worked with SQL databases']
                }
            ],
            'skills': found_skills,
            'years_experience': 6.0,
            'summary': f"Experienced Software Developer with 6 years of experience skilled in {', '.join(found_skills[:3])}.",
            'error': None
        }