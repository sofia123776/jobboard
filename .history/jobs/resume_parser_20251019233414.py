import pdfplumber
import docx
import re
import spacy
import magic
from datetime import datetime
import nltk
from nltk.corpus import stopwords
from dateutil.relativedelta import relativedelta

# Download NLTK data
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class ResumeParser:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.stop_words = set(stopwords.words('english'))
        
        # Regex patterns
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        self.date_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}'
    
    def extract_text(self, file_path, file_type):
        """Extract text from different file types"""
        text = ""
        
        try:
            if file_type == 'pdf':
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
            elif file_type == 'docx':
                doc = docx.Document(file_path)
                text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            else:
                # For txt files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    text = file.read()
        except Exception as e:
            print(f"Error extracting text: {e}")
            
        return text
    
    def extract_personal_info(self, text):
        """Extract personal information from resume text"""
        # Extract email
        emails = re.findall(self.email_pattern, text)
        email = emails[0] if emails else ""
        
        # Extract phone
        phones = re.findall(self.phone_pattern, text)
        phone = phones[0] if phones else ""
        
        # Extract name (simple heuristic - first two words of first line)
        lines = text.split('\n')
        name = ""
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and not any(word in line.lower() for word in ['email', 'phone', 'resume', 'cv']):
                words = line.split()
                if 1 <= len(words) <= 4:
                    name = line
                    break
        
        return {
            'full_name': name,
            'email': email,
            'phone': phone,
            'location': self.extract_location(text)
        }
    
    def extract_location(self, text):
        """Extract location using spaCy NER"""
        doc = self.nlp(text)
        locations = []
        
        for ent in doc.ents:
            if ent.label_ == "GPE":  # Geopolitical Entity
                locations.append(ent.text)
        
        return locations[0] if locations else ""
    
    def extract_education(self, text):
        """Extract education information"""
        education = []
        education_keywords = [
            'university', 'college', 'institute', 'school', 
            'bachelor', 'master', 'phd', 'mba', 'bs', 'ms', 'ba', 'ma'
        ]
        
        lines = text.split('\n')
        current_edu = {}
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in education_keywords):
                # Look for dates in this line and next few lines
                dates = re.findall(self.date_pattern, line)
                
                current_edu = {
                    'institution': line.strip(),
                    'degree': self.extract_degree(line),
                    'dates': [date[0] for date in dates] if dates else []
                }
                
                education.append(current_edu)
        
        return education
    
    def extract_degree(self, text):
        """Extract degree from text"""
        degrees = ['bachelor', 'master', 'phd', 'mba', 'bs', 'ms', 'ba', 'ma', 'associate']
        words = text.lower().split()
        
        for degree in degrees:
            if degree in words:
                return degree.capitalize()
        
        return ""
    
    def extract_experience(self, text):
        """Extract work experience"""
        experience = []
        lines = text.split('\n')
        
        current_exp = {}
        in_experience_section = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Check if we're in experience section
            if any(keyword in line.lower() for keyword in ['experience', 'employment', 'work']):
                in_experience_section = True
                continue
                
            if in_experience_section and line:
                # Simple heuristic: if line has dates and looks like job title
                dates = re.findall(self.date_pattern, line)
                if dates or any(title in line.lower() for title in ['manager', 'developer', 'engineer', 'analyst', 'director']):
                    if current_exp:
                        experience.append(current_exp)
                    
                    current_exp = {
                        'title': line,
                        'company': self.extract_company(line, lines[i+1] if i+1 < len(lines) else ""),
                        'dates': [date[0] for date in dates],
                        'description': []
                    }
                elif current_exp and len(line.split()) > 3:
                    current_exp['description'].append(line)
        
        if current_exp:
            experience.append(current_exp)
            
        return experience
    
    def extract_company(self, current_line, next_line):
        """Extract company name from experience lines"""
        # Remove dates and job titles to find company
        line = re.sub(self.date_pattern, '', current_line)
        return line.strip()
    
    def extract_skills(self, text):
        """Extract skills from resume text"""
        # Common skills database
        common_skills = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin'],
            'web': ['html', 'css', 'react', 'angular', 'vue', 'django', 'flask', 'node.js'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis'],
            'tools': ['git', 'docker', 'aws', 'azure', 'jenkins', 'kubernetes'],
            'soft_skills': ['leadership', 'communication', 'teamwork', 'problem solving']
        }
        
        found_skills = []
        text_lower = text.lower()
        
        for category, skills in common_skills.items():
            for skill in skills:
                if skill in text_lower:
                    found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def calculate_experience(self, experience_data):
        """Calculate total years of experience"""
        total_months = 0
        
        for exp in experience_data:
            dates = exp.get('dates', [])
            if len(dates) >= 2:
                # Simple calculation - assume 2 years per job if we can't parse dates properly
                total_months += 24
            elif dates:
                total_months += 12
        
        return round(total_months / 12, 1)
    
    def parse_resume(self, file_path, file_type):
        """Main method to parse resume"""
        text = self.extract_text(file_path, file_type)
        
        if not text:
            return None
        
        personal_info = self.extract_personal_info(text)
        education = self.extract_education(text)
        experience = self.extract_experience(text)
        skills = self.extract_skills(text)
        
        return {
            'raw_text': text,
            'personal_info': personal_info,
            'education': education,
            'experience': experience,
            'skills': skills,
            'years_experience': self.calculate_experience(experience),
            'summary': self.generate_summary(experience, skills, education)
        }
    
    def generate_summary(self, experience, skills, education):
        """Generate a summary based on parsed data"""
        summary_parts = []
        
        if experience:
            latest_exp = experience[0]
            summary_parts.append(f"Experienced {latest_exp.get('title', 'professional')}")
        
        if skills:
            primary_skills = skills[:5]  # Top 5 skills
            summary_parts.append(f"skilled in {', '.join(primary_skills)}")
        
        if education:
            highest_edu = education[0]
            summary_parts.append(f"with {highest_edu.get('degree', 'educational background')} from {highest_edu.get('institution', '')}")
        
        return ". ".join(summary_parts) + "."