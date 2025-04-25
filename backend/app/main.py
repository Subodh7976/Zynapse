from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Any, Dict, Optional
import traceback
import uvicorn
import os
import shutil
from dotenv import load_dotenv
load_dotenv()

from core.schema import *
from worker import async_chat_task
from helper.parsers import get_web_content, get_youtube_info, parse_pdf
from services.summarizer import get_brief_summary
from core.models import Conversation, Source
from core.db import create_conversation, create_source
from config import SourceTypeEnum, redis_repo


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


origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/initiate-page")
async def initiate_page(request: InitiatePage):
    try:
        conv = Conversation(title=request.title)
        conv_id = create_conversation(conv)
        return {"page_id": conv_id}
        return {"page_id": "sample"}
    except Exception:
        return ExceptionHandler.handle_exception()


@app.post("/upload-source")
async def upload_source(
    source: Optional[UploadFile] = File(None,
                                    description="The PDF file to upload"),
    url: Optional[str] = Form(None, description="The URL to upload"),
    source_type: str = Form(...,
                            description="The type of source (e.g., 'document')"),
    page_id: str = Form(...,
                                description="The associated conversation ID")
):
    # import random
    # return {"source_id": "page_id"+str(random.randint(1, 100000))}
    if not source and not url:
        raise HTTPException(400, detail="Provide at-least one - Source or URL")
    if source and source.content_type != "application/pdf":
        raise HTTPException(400, detail="Only PDF files are allowed")

    try:
        if source_type == SourceTypeEnum.DOCUMENT.value and source:
            file = source
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
        elif url and source_type == SourceTypeEnum.WEB.value:
            response = get_web_content(url)
            if response:
                title, content = response
            else:
                title, content = "Not Available", "Not Available"
        elif url and source_type == SourceTypeEnum.YOUTUBE.value:
            response = get_youtube_info(url)

            response = response if response and isinstance(response, dict) else {}
            title = response.get('title', url)
            content = response.get("transcript", "Not Available").strip()
            print(title, content)
            # else:
            #     raise Exception("Failed to fetch Youtube transcript" + str(response['error']))
        else:
            raise Exception("Unknown type of the source")

        response = await get_brief_summary(source_type, content)
        source_entry = Source(
            conversation_id=page_id, type=SourceTypeEnum.DOCUMENT,
            link=url,
            content=content, title=title, brief=response.get(
                "brief", "Not available"),
            summary=response.get("summary", "Not available")
        )

        source_id = create_source(source_entry)

        return {"source_id": source_id}
    except Exception as e:
        print(e)
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
