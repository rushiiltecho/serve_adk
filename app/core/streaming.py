"""Server-Sent Events (SSE) streaming utilities."""
from typing import AsyncGenerator, Dict, Any
import json
import logging
from sse_starlette.sse import ServerSentEvent

logger = logging.getLogger(__name__)


class SSEEventType:
    """SSE event types."""
    MESSAGE_START = "message_start"
    CONTENT_DELTA = "content_delta"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESPONSE = "function_response"
    MESSAGE_COMPLETE = "message_complete"
    ERROR = "error"
    PING = "ping"


async def create_sse_event(
    event_type: str,
    data: Dict[str, Any],
    event_id: str = None
) -> ServerSentEvent:
    """Create SSE event."""
    return ServerSentEvent(
        data=json.dumps(data),
        event=event_type,
        id=event_id
    )


async def sse_keepalive_generator(
    event_generator: AsyncGenerator[ServerSentEvent, None],
    keepalive_interval: int = 15
) -> AsyncGenerator[ServerSentEvent, None]:
    """
    Wrap an SSE generator with keepalive pings.
    
    Args:
        event_generator: The original event generator
        keepalive_interval: Seconds between keepalive pings
    """
    import asyncio
    
    last_event_time = asyncio.get_event_loop().time()
    
    async def ping_generator():
        """Generate periodic ping events."""
        while True:
            await asyncio.sleep(keepalive_interval)
            yield await create_sse_event(
                event_type=SSEEventType.PING,
                data={"timestamp": asyncio.get_event_loop().time()}
            )
    
    ping_gen = ping_generator()
    
    try:
        async for event in event_generator:
            last_event_time = asyncio.get_event_loop().time()
            yield event
            
            # Check if we need a ping
            current_time = asyncio.get_event_loop().time()
            if current_time - last_event_time >= keepalive_interval:
                yield await anext(ping_gen)
    
    except Exception as e:
        logger.error(f"Error in SSE stream: {e}")
        yield await create_sse_event(
            event_type=SSEEventType.ERROR,
            data={"error": str(e)}
        )