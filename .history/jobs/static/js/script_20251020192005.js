function showMessage() {
  alert("Welcome to JobBoard! 🚀 Explore new opportunities today.");
}


// script.js - Complete Resume Analysis Functionality

class ResumeAnalyzer {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Resume Upload Page
        if (document.getElementById('uploadArea')) {
            this.initializeResumeUpload();
        }

        // Job Application Page with Resume Analysis
        if (document.getElementById('resumeUpload')) {
            this.initializeJobApplicationAnalysis();
        }

        // Resume List Page
        if (document.getElementById('resumeList')) {
            this.initializeResumeList();
        }

        // Resume Analysis Detail Page
        if (document.getElementById('resumeAnalysis')) {
            this.initializeResumeAnalysis();
        }
    }

    // Resume Upload Page Functionality
    initializeResumeUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const analysisResults = document.getElementById('analysisResults');

        if (!uploadArea || !fileInput) return;

        // Click to upload
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        // Drag and drop functionality
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleResumeUpload(files[0], 'upload');
            }
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleResumeUpload(e.target.files[0], 'upload');
            }
        });

        // Global functions for buttons
        window.saveResume = () => this.saveResume();
        window.analyzeAnother = () => this.analyzeAnother();
    }

    // Job Application Page Functionality
    initializeJobApplicationAnalysis() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('resumeUpload');
        const analysisResults = document.getElementById('analysisResults');
        const applicationForm = document.getElementById('applicationForm');

        if (!uploadArea || !fileInput) return;

        // Click to upload
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        // Drag and drop functionality
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleResumeUpload(files[0], 'application');
            }
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleResumeUpload(e.target.files[0], 'application');
            }
        });

        // Form submission enhancement
        if (applicationForm) {
            applicationForm.addEventListener('submit', (e) => {
                this.handleApplicationSubmit(e);
            });
        }
    }

    // Resume List Page Functionality
    initializeResumeList() {
        // Add delete functionality for resumes
        const deleteButtons = document.querySelectorAll('.delete-resume');
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.deleteResume(e.target.closest('button').dataset.resumeId);
            });
        });

        // Add quick analysis functionality
        const analyzeButtons = document.querySelectorAll('.quick-analyze');
        analyzeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.quickAnalyze(e.target.closest('button').dataset.resumeId);
            });
        });

        console.log('Resume list page initialized');
    }

    // Resume Analysis Detail Page Functionality
    initializeResumeAnalysis() {
        // Add functionality for downloading analysis report
        const downloadReportBtn = document.getElementById('downloadReport');
        if (downloadReportBtn) {
            downloadReportBtn.addEventListener('click', () => {
                this.downloadAnalysisReport();
            });
        }

        // Add functionality for finding job matches
        const findMatchesBtn = document.getElementById('findMatches');
        if (findMatchesBtn) {
            findMatchesBtn.addEventListener('click', () => {
                this.findJobMatches();
            });
        }

        // Add functionality for skill filters
        const skillFilters = document.querySelectorAll('.skill-filter');
        skillFilters.forEach(filter => {
            filter.addEventListener('click', (e) => {
                this.filterBySkill(e.target.textContent);
            });
        });

        console.log('Resume analysis page initialized');
    }

    // Handle Resume Upload and Analysis
    async handleResumeUpload(file, context) {
        if (!this.isValidFileType(file)) {
            alert('Please upload a PDF, DOCX, DOC, or TXT file.');
            return;
        }

        const uploadArea = document.getElementById('uploadArea');
        const fileInput = context === 'application' ? 
            document.getElementById('resumeUpload') : 
            document.getElementById('fileInput');

        // Show loading state
        this.showLoadingState(uploadArea);

        const formData = new FormData();
        formData.append('resume', file);
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        try {
            const response = await fetch("/analyze-resume/", {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            if (data.success) {
                this.displayAnalysisResults(data, context);
                // Also set the resume file in the actual form for application context
                if (context === 'application' && fileInput) {
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    fileInput.files = dataTransfer.files;
                }
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error analyzing resume: ' + error.message);
            this.resetUploadArea(uploadArea, context);
        }
    }

    // Handle Job Application Form Submission
    handleApplicationSubmit(e) {
        const resumeFile = document.querySelector('input[type="file"][name="resume"]').files[0];
        if (!resumeFile) {
            e.preventDefault();
            alert('Please upload a resume before submitting your application.');
            return;
        }

        const submitBtn = document.getElementById('submitBtn');
        if (submitBtn) {
            submitBtn.innerHTML = '⏳ Submitting...';
            submitBtn.disabled = true;
        }
    }

    // Save Resume to Database
    async saveResume() {
        const fileInput = document.getElementById('fileInput');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Please upload a resume first.');
            return;
        }

        const saveFormData = new FormData();
        saveFormData.append('resume', file);
        saveFormData.append('csrfmiddlewaretoken', this.getCSRFToken());

        try {
            const response = await fetch("/upload-resume/", {
                method: 'POST',
                body: saveFormData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                alert('Resume saved successfully!');
                window.location.href = "/resumes/";
            } else {
                alert('Error saving resume: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error saving resume');
        }
    }

    // Delete Resume
    async deleteResume(resumeId) {
        if (!confirm('Are you sure you want to delete this resume? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/delete-resume/${resumeId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                alert('Resume deleted successfully!');
                // Remove the resume card from the UI
                const resumeCard = document.querySelector(`[data-resume-id="${resumeId}"]`).closest('.resume-card');
                if (resumeCard) {
                    resumeCard.remove();
                }
            } else {
                alert('Error deleting resume: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error deleting resume');
        }
    }

    // Quick Analyze Resume
    async quickAnalyze(resumeId) {
        try {
            const response = await fetch(`/quick-analyze/${resumeId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                alert('Resume re-analyzed successfully!');
                // Refresh the page to show updated analysis
                window.location.reload();
            } else {
                alert('Error analyzing resume: ' + data.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error analyzing resume');
        }
    }

    // Download Analysis Report
    async downloadAnalysisReport() {
        const resumeId = window.location.pathname.split('/').pop();
        
        try {
            const response = await fetch(`/download-report/${resumeId}/`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `resume-analysis-${resumeId}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                alert('Error downloading report');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error downloading report');
        }
    }

    // Find Job Matches
    findJobMatches() {
        const resumeId = window.location.pathname.split('/').pop();
        window.location.href = `/match-jobs/${resumeId}/`;
    }

    // Filter by Skill (on analysis page)
    filterBySkill(skill) {
        const jobCards = document.querySelectorAll('.job-card');
        jobCards.forEach(card => {
            const skills = card.dataset.skills ? JSON.parse(card.dataset.skills) : [];
            if (skills.includes(skill.toLowerCase())) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    // Reset Upload Area
    analyzeAnother() {
        const analysisResults = document.getElementById('analysisResults');
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput') || document.getElementById('resumeUpload');

        if (analysisResults) analysisResults.style.display = 'none';
        this.resetUploadArea(uploadArea, 'upload');
        if (fileInput) fileInput.value = '';
    }

    // Utility Functions
    isValidFileType(file) {
        const allowedTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword',
            'text/plain'
        ];
        return allowedTypes.includes(file.type) || 
               file.name.toLowerCase().endsWith('.pdf') ||
               file.name.toLowerCase().endsWith('.docx') ||
               file.name.toLowerCase().endsWith('.doc') ||
               file.name.toLowerCase().endsWith('.txt');
    }

    showLoadingState(uploadArea) {
        if (uploadArea) {
            uploadArea.innerHTML = `
                <div class="upload-icon">⏳</div>
                <h4>Analyzing Resume...</h4>
                <p>Please wait while we process your resume</p>
            `;
        }
    }

    displayAnalysisResults(data, context) {
        // Update analysis results
        const matchScoreElement = document.getElementById('matchScore');
        const analysisSummaryElement = document.getElementById('analysisSummary');
        const yearsExperienceElement = document.getElementById('yearsExperience');
        const skillsContainer = document.getElementById('extractedSkills');
        const analysisResults = document.getElementById('analysisResults');

        if (matchScoreElement) matchScoreElement.textContent = data.match_score + '%';
        if (analysisSummaryElement) analysisSummaryElement.textContent = data.summary;
        if (yearsExperienceElement) yearsExperienceElement.textContent = data.years_experience;
        
        // Update skills list
        if (skillsContainer) {
            skillsContainer.innerHTML = '';
            if (data.skills && data.skills.length > 0) {
                data.skills.forEach(skill => {
                    const skillTag = document.createElement('span');
                    skillTag.className = 'skill-tag';
                    skillTag.textContent = skill;
                    skillsContainer.appendChild(skillTag);
                });
            } else {
                skillsContainer.innerHTML = '<p>No skills detected</p>';
            }
        }

        // Show results
        if (analysisResults) analysisResults.style.display = 'block';
    }

    resetUploadArea(uploadArea, context) {
        if (uploadArea) {
            uploadArea.innerHTML = `
                <div class="upload-icon">📁</div>
                <h4>Drag & Drop Your Resume Here</h4>
                <p>or click to browse files</p>
                <p class="supported-formats">Supported formats: PDF, DOCX, DOC, TXT</p>
            `;
        }
    }

    getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new ResumeAnalyzer();
});