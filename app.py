import os
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, Header, HTTPException
from docling.document_converter import DocumentConverter

app = FastAPI()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/convert")
async def convert(file: UploadFile, x_docling_key: str | None = Header(None)):
    # simple auth
    if os.environ.get("DOCLING_KEY") and x_docling_key != os.environ["DOCLING_KEY"]:
        raise HTTPException(status_code=403, detail="forbidden")

    suffix = Path(file.filename or "").suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.file.seek(0)
        shutil.copyfileobj(file.file, tmp)
        temp_path = Path(tmp.name)

    try:
        conv = DocumentConverter().convert(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)
    md = conv.document.export_to_markdown()
    js = conv.document.model_dump()
    return {"markdown": md, "json": js}
