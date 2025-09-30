# Docling FastAPI Microservice

Minimal FastAPI wrapper around Docling that converts uploaded documents to
Markdown and JSON. The service is sized for Google Cloud Run, requires only a
shared secret, and includes a smoke test script and sample Next.js client code.

## Local Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Smoke test (replace values as needed):

```bash
./scripts/smoke_test.sh http://127.0.0.1:8000 dummy-secret /path/to/sample.pdf
```

## Container Image

Build and run locally:

```bash
docker build -t docling-api .
docker run --rm -p 8080:8080 -e PORT=8080 -e DOCLING_KEY=dummy-secret docling-api
```

> The Docker image installs dependencies with
> `pip install --root-user-action=ignore ...` to suppress pip's warning about
> running as root inside the container.

## Deploy to Google Cloud Run

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/docling-api
gcloud run deploy docling-api \
  --image gcr.io/YOUR_PROJECT_ID/docling-api \
  --region us-central1 \
  --memory 2Gi \
  --cpu 1 \
  --platform managed \
  --allow-unauthenticated \
  --max-instances 2 \
  --concurrency 1
gcloud run services update docling-api --update-env-vars DOCLING_KEY=your-secret
```

Verify the deployment:

```bash
curl -sS https://<SERVICE_URL>/health
./scripts/smoke_test.sh https://<SERVICE_URL> your-secret /path/to/sample.pdf
```

## Next.js Integration Snippet

Set the following in Vercel (or your runtime environment):

- `DOCLING_URL`: `https://docling-api-xxxxx-a.run.app`
- `DOCLING_KEY`: shared secret configured on Cloud Run

Client helper (`lib/docling/client.ts`):

```ts
export class DoclingClientError extends Error {}

function baseUrl() {
  const raw = process.env.DOCLING_URL;
  if (!raw) throw new DoclingClientError('DOCLING_URL not set');
  return raw.replace(/\/$/, '');
}

export async function convertPdfWithDocling(pdfBytes: Buffer, signal?: AbortSignal) {
  const fd = new FormData();
  fd.append('file', new Blob([pdfBytes], { type: 'application/pdf' }), 'document.pdf');

  const headers: Record<string, string> = {};
  if (process.env.DOCLING_KEY) headers['X-Docling-Key'] = process.env.DOCLING_KEY;

  const res = await fetch(`${baseUrl()}/convert`, {
    method: 'POST',
    headers,
    body: fd,
    signal,
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new DoclingClientError(`Docling ${res.status}: ${detail}`);
  }

  return res.json() as Promise<{ markdown: string; json: unknown }>;
}
```

Example usage in your orchestrator (pseudo-code):

```ts
const pages = await getPdfPageCount(pdfBytes);
if (pages > 10) {
  const docling = await convertPdfWithDocling(pdfBytes, abortController.signal);
  // continue with AI SDK v5 chunk + merge flow
} else {
  // existing direct extraction path
}
```

## Maintenance Notes

- Keep `min-instances` at 0 to benefit from Cloud Run scale-to-zero pricing.
- Increase the `--memory` flag if you observe out-of-memory errors on large
  documents.
- Rotate `DOCLING_KEY` if the secret is ever exposed, and update both Cloud Run
  and Vercel.
