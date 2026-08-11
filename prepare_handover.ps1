$ProjectRoot = "D:\Enterprise-Knowledge-Platform"
$OutputRoot = "D:\Enterprise-Knowledge-Platform-Handover"
$ZipPath = "D:\Enterprise-Knowledge-Platform-Handover.zip"

Write-Host "Preparing team handover..."

# Remove old handover
if (Test-Path $OutputRoot) {
    Remove-Item $OutputRoot -Recurse -Force
}

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

New-Item -ItemType Directory -Path $OutputRoot | Out-Null

# Copy project while excluding large/local folders
robocopy $ProjectRoot $OutputRoot /E `
    /XD `
    "$ProjectRoot\backend\venv" `
    "$ProjectRoot\frontend\node_modules" `
    "$ProjectRoot\.git" `
    "$ProjectRoot\chroma_data" `
    "$ProjectRoot\backend\__pycache__" `
    /XF `
    ".env" `
    "*.pyc" `
    "*.log"

# Create PROJECT_STATUS.md
@"
# Enterprise Knowledge Intelligence Platform

## Current Status

Development has reached:

Knowledge Retrieval + Basic Knowledge Validation

## Completed

- React + TypeScript frontend
- FastAPI backend
- PostgreSQL integration
- JWT authentication
- Role-based access control
- Admin / Knowledge Manager / Employee / Guest roles
- Protected frontend routes
- Admin User Management
- Frontend role upgrade/downgrade
- Role-based sidebar
- PDF upload
- Document listing
- Document deletion
- Document ownership/access control
- PDF text extraction
- Page extraction
- Text chunking
- Sentence Transformer embeddings
- all-MiniLM-L6-v2 model
- ChromaDB vector storage
- Document indexing
- Semantic retrieval
- Retrieval access control
- Similarity scoring
- Source/page retrieval
- Basic knowledge validation
- Draft documents marked untrusted
- Trust score
- Validation reason

## Successfully Tested

PDF
-> Text Extraction
-> Chunking
-> Embeddings
-> ChromaDB
-> Semantic Search
-> Access Check
-> Knowledge Validation

Test query:

"What is the leave policy?"

The correct Leave Policy chunks were retrieved.

The test document has:

status = draft

Therefore validation correctly returned:

trusted = false
trust_score = 0.35

## Currently Working On

Document version validation.

Goal:

Relevant Document
-> Status Check
-> Version Check
-> Newer Version Detection
-> Trust Decision

## Next

1. Complete version validation testing
2. Conflict detection
3. Trusted evidence selection
4. RAG / LLM generation
5. Connect backend to AI Chat
6. Citations and evidence
7. Trust/explainability improvements

## Important Architecture Rule

Do not replace existing modules without checking how they
affect later phases.

The project is being designed modularly so future features
can be changed or replaced independently.

## Project Vision

Other RAG systems primarily retrieve information for AI.

This platform aims to:

Find -> Validate -> Understand -> Trust -> Answer

enterprise knowledge.
"@ | Set-Content "$OutputRoot\PROJECT_STATUS.md"

# Create setup instructions
@"
# Team Setup

## Backend

Open terminal:

cd backend

Create virtual environment:

python -m venv venv

Activate:

.\venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Create/configure the .env file before starting.

Run backend:

python -m uvicorn app.main:app --reload


## Frontend

Open another terminal:

cd frontend

Install dependencies:

npm install

Run:

npm run dev


## Important

The following are intentionally NOT included:

- backend/venv
- frontend/node_modules
- .env
- local Python caches
- Git history
- local Chroma vector data

These should be generated/configured on each developer's computer.

Do not share passwords, JWT secrets, database passwords,
API keys, or other secrets through the project ZIP.
"@ | Set-Content "$OutputRoot\SETUP.md"

# Create ZIP
Compress-Archive `
    -Path "$OutputRoot\*" `
    -DestinationPath $ZipPath `
    -Force

Write-Host ""
Write-Host "====================================="
Write-Host "HANDOVER READY"
Write-Host "====================================="
Write-Host ""
Write-Host "Folder:"
Write-Host $OutputRoot
Write-Host ""
Write-Host "ZIP:"
Write-Host $ZipPath
Write-Host ""