# app/routers/profile.py
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from app.services.resume_parser import ResumeParserService
from app.main import get_current_user_id # Import our token verification dependency
from app.services.vector_store import VectorStoreService

router = APIRouter(prefix="/profile", tags=["User Profile"])

# Limit file uploads to 5MB to defend against Denial of Service (DoS) memory exhaustion
MAX_FILE_SIZE = 5 * 1024 * 1024 

@router.post("/resume/parse")
async def parse_resume(
    file: UploadFile = File(...),
    current_user_id: int = Depends(get_current_user_id)
):
    # Validate file type extension boundary
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported."
        )
        
    # Read stream bytes securely
    file_bytes = await file.read()
    
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the maximum allowed limit of 5MB."
        )

    try:
        parsed_text = ResumeParserService.extract_text_from_pdf(file_bytes)
        return {
            "user_id": current_user_id,
            "filename": file.filename,
            "extracted_text": parsed_text
        }
    except Exception as e:
        # In production, hook this up to an internal error logger
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process and parse the structural layout of the resume."
        )


vector_service = VectorStoreService()

@router.post("/github/sync")
async def sync_github(
    github_username: str,
    current_user_id: int = Depends(get_current_user_id)
):
    try:
        synced_count = await vector_service.sync_github_repos(github_username)
        return {
            "message": "GitHub repository sync completed successfully.",
            "repositories_indexed": synced_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process GitHub vector ingestion: {str(e)}"
        )