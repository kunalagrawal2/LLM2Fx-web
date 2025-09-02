import json, httpx
from .config import settings
from .logger import logger

async def call_openai_chat(messages: list[dict], *, force_json: bool = True) -> str:
    """
    Calls OpenAI Chat Completions API.
    Returns assistant message content as string.
    Raises httpx.HTTPError on transport errors.
    """
    # Validate API key
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
    
    # Check if it's a valid OpenAI API key format (sk- or sk-proj-)
    if not (settings.openai_api_key.startswith("sk-") or settings.openai_api_key.startswith("sk-proj-")):
        raise ValueError("Invalid OpenAI API key format. Must start with 'sk-' or 'sk-proj-'")
    
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.openai_model,
        "messages": messages,
        "temperature": settings.gen_temperature,
        "max_tokens": settings.gen_max_tokens,
    }
    if force_json:
        body["response_format"] = {"type": "json_object"}

    # Ensure proper URL construction with trailing slash handling
    base_url = settings.openai_base_url.rstrip("/")
    url = f"{base_url}/chat/completions"
    
    # Debug: Print the request details
    logger.info("openai_request", extra={
        "extra": {
            "model": settings.openai_model,
            "base_url": settings.openai_base_url,
            "constructed_url": url,
            "api_key_prefix": settings.openai_api_key[:10] + "...",
            "messages_count": len(messages)
        }
    })
    
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_s) as client:
            resp = await client.post(url, headers=headers, json=body)
            
            # Debug: Log the response status and headers
            logger.info("openai_response_received", extra={
                "extra": {
                    "status_code": resp.status_code,
                    "headers": dict(resp.headers)
                }
            })
            
            resp.raise_for_status()
            data = resp.json()
            out = data["choices"][0]["message"]["content"]
            logger.info("openai_response", extra={"extra": {"usage": data.get("usage", {})}})
            return out
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            logger.error("openai_auth_error", extra={"extra": {"status": e.response.status_code}})
            raise ValueError("OpenAI authentication failed. Check your API key.")
        elif e.response.status_code == 429:
            logger.error("openai_rate_limit", extra={"extra": {"status": e.response.status_code}})
            raise ValueError("OpenAI rate limit exceeded. Try again later.")
        else:
            logger.error("openai_http_error", extra={"extra": {"status": e.response.status_code, "text": e.response.text}})
            # Log the full error response for debugging
            try:
                error_data = e.response.json()
                logger.error("openai_error_details", extra={"extra": error_data})
                raise ValueError(f"OpenAI API error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            except:
                raise ValueError(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error("openai_unknown_error", extra={"extra": {"error": str(e)}})
        raise ValueError(f"Unexpected error calling OpenAI: {e}")

def parse_json_safe(text: str) -> dict | None:
    try:
        return json.loads(text)
    except Exception:
        return None
