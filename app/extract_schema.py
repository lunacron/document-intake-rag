"""The record we want out of an enrollment form. This one model is both the schema Claude is
given (as a tool's input schema) and the validator for what comes back."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Contact(BaseModel):
    name: str
    relationship: str | None = Field(None, description="e.g. Mother, Father, Grandmother")
    phone: str | None = None
    email: str | None = None


class Enrollment(BaseModel):
    """Every field is copied from the form. Use null when the form does not say; never guess."""

    is_enrollment_form: bool = Field(
        description="true only if this document is an undergraduate enrollment form; false for anything else "
                    "(a transcript, handbook, letter...)")
    application_id: str = Field(description="Application ID, e.g. MROU-2026-00417")
    submitted_date: date | None = Field(None, description="Date the form was submitted, YYYY-MM-DD")
    legal_name: str = Field(description="Student legal name, exactly as written")
    preferred_name: str | None = None
    date_of_birth: date = Field(description="YYYY-MM-DD")
    gender: str | None = None
    admission_type: str | None = Field(None, description="e.g. First-year student, Transfer")
    home_address: str | None = None
    email: str | None = Field(None, description="Student email")
    phone: str | None = Field(None, description="Student phone")
    previous_school: str | None = None
    start_term: str | None = Field(None, description="e.g. Fall 2026")
    enrollment_status: Literal["full_time", "part_time"] | None = None
    intended_major: str | None = None
    requested_courses: list[str] = Field(default_factory=list, description="One entry per course")
    transfer_credits: list[str] = Field(default_factory=list, description="AP / transfer credit entries")
    financial_aid_applied: bool | None = None
    emergency_contacts: list[Contact] = Field(default_factory=list)
    known_allergies: str | None = Field(None, description="Copy the form's text, including 'None known'; null only if the form has no such line")
    physician: str | None = None
    disability_accommodations_requested: bool | None = None
    disability_accommodations_details: str | None = Field(None, description="Text after 'Yes -', if any")
    ferpa_waiver: bool | None = Field(None, description="Share records with parents: true if Yes")
    ferpa_waiver_names: list[str] = Field(default_factory=list, description="People records may be shared with")
    date_signed: date | None = Field(None, description="Date the student signed, YYYY-MM-DD")
    uncertain_fields: list[str] = Field(
        default_factory=list,
        description="Names of fields you were not sure about (unclear, missing, or ambiguous in the form)")
