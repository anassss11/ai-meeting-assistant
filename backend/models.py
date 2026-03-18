from pydantic import BaseModel


class AudioUploadResponse(BaseModel):
    message: str
    transcript_chunk: str


class TranscriptResponse(BaseModel):
    transcript: str


class SummaryResponse(BaseModel):
    summary: str


class ActionItem(BaseModel):
    task: str
    owner: str
    deadline: str


class ActionItemsResponse(BaseModel):
    action_items: list[ActionItem]


class DecisionsResponse(BaseModel):
    decisions: list[str]


class SessionResponse(BaseModel):
    message: str


class AnalysisStatusResponse(BaseModel):
    transcript_ready: bool
    transcript_length: int
    summary_ready: bool
    action_items_ready: bool
    decisions_ready: bool
    analysis_ready: bool
