"""Type converters between Google types and dicts."""
import logging
from typing import Dict, Any, List, Optional, Union
from google.genai import types as genai_types
from google.adk.events import Event as AdkEvent, EventActions

logger = logging.getLogger(__name__)


def content_to_dict(content: Optional[genai_types.Content]) -> Optional[Dict[str, Any]]:
    """Convert genai_types.Content to dict."""
    if not content:
        return None
    
    return {
        "role": content.role,
        "parts": [part_to_dict(part) for part in content.parts]
    }


def part_to_dict(part: genai_types.Part) -> Dict[str, Any]:
    """Convert genai_types.Part to dict."""
    result = {}
    
    # Text
    if hasattr(part, 'text') and part.text:
        result["text"] = part.text
    
    # Function call
    if hasattr(part, 'function_call') and part.function_call:
        result["function_call"] = {
            "name": part.function_call.name,
            "args": dict(part.function_call.args) if part.function_call.args else {}
        }
    
    # Function response
    if hasattr(part, 'function_response') and part.function_response:
        result["function_response"] = {
            "name": part.function_response.name,
            "response": dict(part.function_response.response) if part.function_response.response else {}
        }
    
    # File data
    if hasattr(part, 'file_data') and part.file_data:
        result["file_data"] = {
            "file_uri": part.file_data.file_uri,
            "mime_type": part.file_data.mime_type
        }
    
    # Inline data (blob)
    if hasattr(part, 'inline_data') and part.inline_data:
        result["inline_data"] = {
            "mime_type": part.inline_data.mime_type,
            "data": part.inline_data.data
        }
    
    return result


def dict_to_content(data: Dict[str, Any]) -> genai_types.Content:
    """Convert dict to genai_types.Content."""
    parts = []
    
    if "parts" in data:
        for part_data in data["parts"]:
            parts.append(dict_to_part(part_data))
    
    return genai_types.Content(
        role=data.get("role", "user"),
        parts=parts
    )


def dict_to_part(data: Dict[str, Any]) -> genai_types.Part:
    """Convert dict to genai_types.Part."""
    # Text part
    if "text" in data:
        return genai_types.Part(text=data["text"])
    
    # Function call part
    if "function_call" in data:
        return genai_types.Part.from_function_call(
            name=data["function_call"]["name"],
            args=data["function_call"].get("args", {})
        )
    
    # Function response part
    if "function_response" in data:
        return genai_types.Part.from_function_response(
            name=data["function_response"]["name"],
            response=data["function_response"].get("response", {})
        )
    
    # File data part
    if "file_data" in data:
        return genai_types.Part(
            file_data=genai_types.FileData(
                file_uri=data["file_data"]["file_uri"],
                mime_type=data["file_data"]["mime_type"]
            )
        )
    
    # Default to empty text part
    return genai_types.Part(text="")


def event_actions_to_dict(actions: Optional[EventActions]) -> Dict[str, Any]:
    """Convert EventActions to dict."""
    if not actions:
        return {}
    
    result = {}
    
    if actions.state_delta:
        result["state_delta"] = dict(actions.state_delta)
    
    if actions.artifact_delta:
        result["artifact_delta"] = dict(actions.artifact_delta)
    
    if actions.transfer_to_agent:
        result["transfer_to_agent"] = actions.transfer_to_agent
    
    if actions.escalate is not None:
        result["escalate"] = actions.escalate
    
    return result


def dict_to_event_actions(data: Dict[str, Any]) -> EventActions:
    """Convert dict to EventActions."""
    return EventActions(
        state_delta=data.get("state_delta"),
        artifact_delta=data.get("artifact_delta"),
        transfer_to_agent=data.get("transfer_to_agent"),
        escalate=data.get("escalate")
    )


def adk_event_to_dict(event: Union[AdkEvent, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert ADK Event to dict for JSON serialization.
    
    Handles both Event objects and dict objects (from async_stream_query).
    """
    # If already a dict, return it
    if isinstance(event, dict):
        return event
    
    # Otherwise, convert Event object to dict
    result = {
        "id": event.id,
        "author": event.author,
        "invocation_id": event.invocation_id,
        "timestamp": event.timestamp,
    }
    
    # Add content if present
    if event.content:
        result["content"] = content_to_dict(event.content)
    
    # Add actions if present
    if event.actions:
        result["actions"] = event_actions_to_dict(event.actions)
    
    # Add other fields
    if hasattr(event, 'partial') and event.partial is not None:
        result["partial"] = event.partial
    
    if hasattr(event, 'turn_complete') and event.turn_complete is not None:
        result["turn_complete"] = event.turn_complete
    
    if hasattr(event, 'finish_reason') and event.finish_reason:
        result["finish_reason"] = event.finish_reason
    
    return result


def create_adk_event(
    author: str,
    invocation_id: str,
    timestamp: float,
    content: Optional[genai_types.Content] = None,
    actions: Optional[EventActions] = None
) -> AdkEvent:
    """Create an ADK Event from components."""
    return AdkEvent(
        author=author,
        invocation_id=invocation_id,
        timestamp=timestamp,
        content=content,
        actions=actions or EventActions()
    )