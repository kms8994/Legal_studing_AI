from pydantic import BaseModel


class NormalizedInput(BaseModel):
    input_type: str
    text: str
    text_hash: str


class TextInputRequest(BaseModel):
    text: str


class CaseNumberInputRequest(BaseModel):
    case_number: str


class PdfInputRequest(BaseModel):
    file_base64: str
    filename: str | None = None


class ImageInputRequest(BaseModel):
    image_base64: str
    mime_type: str = "image/png"


class OcrResult(BaseModel):
    status: str
    extracted_text: str | None = None
    message: str | None = None
