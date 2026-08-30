from enum import StrEnum


class ApplicationStatus(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    TECHNICAL_INTERVIEW = "technical_interview"
    FINAL_INTERVIEW = "final_interview"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class JobSource(StrEnum):
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    COMPANY_WEBSITE = "company_website"
    RECRUITER = "recruiter"
    REFERRAL = "referral"
    OTHER = "other"


class WorkModel(StrEnum):
    ONSITE = "onsite"
    HYBRID = "hybrid"
    REMOTE = "remote"
