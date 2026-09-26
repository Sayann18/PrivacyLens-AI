from fastapi import APIRouter
from models.request import VerifyRequest
from models.response import VerificationResponse
from services.verification import VerificationService
from utils.errors import structured_http_exception
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()
service = VerificationService()


@router.post("/verify", response_model=VerificationResponse)
async def verify_claim(payload: VerifyRequest) -> VerificationResponse:
    try:
        return await service.verify(payload)
    except Exception as exc:
        logger.error("Error verifying claim: %s", exc, exc_info=True)
        raise structured_http_exception(500, "VERIFICATION_FAILED", "An unexpected error occurred during verification.") from exc
