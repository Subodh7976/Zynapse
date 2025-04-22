from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import traceback
import os
import shutil

from app.core.constants import SourceTypeEnum


class ExceptionHandler:
    @staticmethod
    def handle_exception() -> Dict[str, Any]:
        """
        Handle exceptions and return a dictionary with error details.

        Returns:
            Dict[str, Any]: A dictionary containing error information.
        """
        error_info = {
            "error": True,
            "message": str(traceback.format_exc())
        }
        return error_info


app = FastAPI()


class InitiateConversation(BaseModel):
    title: str


class UploadSource(BaseModel):
    source: UploadFile | str
    type: SourceTypeEnum
    conversation_id: str


@app.post("/initiate-conversation")
async def initiate_conversation(request: InitiateConversation):
    try:
        pass
    except Exception:
        return ExceptionHandler.handle_exception()


@app.post("/upload-source")
async def upload_source(request: UploadSource):
    if isinstance(request.source, UploadFile) and request.source != "application/pdf":
        raise HTTPException(400, detail="Only PDF files are allowed")

    try:
        file = request.source
        filename = file.filename

        # Save the file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, filename)

        with open(file_path, "wb") as buffer:
            # Use shutil to copy from the SpooledTemporaryFile to the destination
            shutil.copyfileobj(file.file, buffer)

        return {"id": ""}
    except Exception:
        return ExceptionHandler.handle_exception()


