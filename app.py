import os
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

    conv = DocumentConverter().convert(file.file)  # Docling usage per docs
    md = conv.document.export_to_markdown()
    js = conv.document.model_dump()
    return {"markdown": md, "json": js}
