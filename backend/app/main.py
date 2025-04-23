from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse, Response
from typing import Any, Dict
import traceback
import uvicorn
import os
import shutil

from app.config import SourceTypeEnum, redis_repo
from app.core.db import create_conversation, create_source
from app.core.models import Conversation, Source
from app.services.summarizer import get_brief_summary
from app.helper.parsers import get_web_content, get_youtube_transcript, parse_pdf
from app.worker import async_chat_task
from app.core.schema import *


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


@app.post("/initiate-conversation")
async def initiate_conversation(request: InitiateConversation):
    try:
        conv = Conversation(title=request.title)
        conv_id = create_conversation(conv)
        return {"conversation_id": conv_id}
    except Exception:
        return ExceptionHandler.handle_exception()


@app.post("/upload-source")
async def upload_source(request: UploadSource):
    if isinstance(request.source, UploadFile) and request.source.content_type != "application/pdf":
        raise HTTPException(400, detail="Only PDF files are allowed")

    try:
        if isinstance(request.source, UploadFile) and request.type == SourceTypeEnum.DOCUMENT:
            file = request.source
            filename = file.filename

            # Save the file
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            try:
                content = parse_pdf(file_path)
                title = filename
            except Exception as e:
                os.remove(file_path)
                raise e

            os.remove(file_path)
        elif isinstance(request.source, str) and request.type == SourceTypeEnum.WEB:
            title, content = get_web_content(request.source)
        elif isinstance(request.source, str) and request.type == SourceTypeEnum.YOUTUBE:
            response = get_youtube_transcript(request.source)

            if response['success']:
                title = response['title']
                content = response['transcript']
            else:
                raise Exception("Failed to fetch Youtube transcript")
        else:
            raise Exception("Unknown type of the source")

        response = get_brief_summary(request.type, content)
        source = Source(
            conversation_id=request.conversation_id, type=request.type,
            link=request.source if request.type != SourceTypeEnum.DOCUMENT else None,
            content=content, title=title, brief=response.get(
                "brief", "Not available"),
            summary=response.get("summary", "Not available")
        )

        source_id = create_source(source)

        return {"source_id": source_id}
    except Exception:
        return ExceptionHandler.handle_exception()


@app.post("/chat")
async def chat_request(request: ChatRequest):
    try:
        request_id = redis_repo.create_record()
        response = async_chat_task.send(
            request_id, request.model_dump_json()
        )
        print(response)
        return JSONResponse({"request_id": request_id})
    except Exception:
        return ExceptionHandler.handle_exception()


@app.get("/chat")
async def chat_update(request_id: str):
    try:
        record = redis_repo.get_record(record_id=request_id)
        print("record: ")
        print(record)
        if record:
            return JSONResponse(record)
        else:
            return Response(status_code=404, content="Record not found")
    except Exception:
        return ExceptionHandler.handle_exception()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)