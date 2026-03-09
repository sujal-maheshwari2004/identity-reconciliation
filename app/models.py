from pydantic import BaseModel, EmailStr, model_validator
from typing import Optional

class IdentifyRequest(BaseModel):
    email: Optional[EmailStr] = None
    phoneNumber: Optional[str] = None

    @model_validator(mode='after')
    def check_at_least_one(self) -> 'IdentifyRequest':
        if self.email is None and self.phoneNumber is None:
            raise ValueError("At least one of email or phoneNumber must be provided")
        return self


class ContactResponse(BaseModel):
    primaryContactId: int
    emails: list[str]
    phoneNumbers: list[str]
    secondaryContactIds: list[int]


class IdentifyResponse(BaseModel):
    contact: ContactResponse
