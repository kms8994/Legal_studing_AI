from pydantic import BaseModel


class UserProfile(BaseModel):
    id: str
    email: str
    plan: str

