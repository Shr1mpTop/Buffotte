import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.dependencies import get_bufftracker_client
from app.integrations.bufftracker import BuffTrackerClient


router = APIRouter(prefix="/api/bufftracker", tags=["bufftracker"])


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_bufftracker(
    request: Request,
    path: str,
    client: BuffTrackerClient = Depends(get_bufftracker_client),
):
    """Proxy buff-tracker requests through Buffotte to avoid mixed-content issues."""
    try:
        response = await client.proxy_request(
            method=request.method,
            path=path,
            query=request.url.query,
            headers=request.headers,
            body=await request.body(),
        )
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=client.response_headers(response.headers),
        )
    except Exception as exc:
        logging.error(f"Buff-tracker proxy error: {repr(exc)}")
        raise HTTPException(
            status_code=503,
            detail=f"Buff-tracker service unavailable: {str(exc)}",
        )
