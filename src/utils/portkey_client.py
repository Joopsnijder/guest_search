"""Portkey client wrapper for Anthropic SDK with observability.

This module provides a factory function that returns either a standard Anthropic
client or a Portkey client using Model Catalog, depending on environment configuration.
"""

import os

from anthropic import Anthropic


def get_anthropic_client(api_key: str):
    """
    Get Anthropic client, optionally using Portkey for observability.

    If PORTKEY_API_KEY is set, uses Portkey's Model Catalog with the provider
    slug from PORTKEY_PROVIDER_SLUG (defaults to '@aitoday-anthropic').

    If PORTKEY_MODEL_NAME is set, uses that model, otherwise defaults to
    'claude-sonnet-4-5-20250929'.

    Args:
        api_key: Anthropic API key (used only when Portkey is not configured)

    Returns:
        Anthropic client or Portkey-wrapped client

    Example:
        >>> from src.utils.portkey_client import get_anthropic_client
        >>> client = get_anthropic_client(Config.ANTHROPIC_API_KEY)
        >>> response = client.messages.create(...)
    """
    portkey_api_key = os.getenv("PORTKEY_API_KEY")

    if portkey_api_key:
        # Use Portkey Model Catalog for observability
        try:
            from portkey_ai import Portkey

            print("🔍 Portkey observability enabled (Model Catalog)")

            # Get provider slug and model from environment (with defaults)
            provider_slug = os.getenv("PORTKEY_PROVIDER_SLUG", "@aitoday-anthropic")
            model_name = os.getenv("PORTKEY_MODEL_NAME", "claude-sonnet-4-5-20250929")

            portkey_client = Portkey(api_key=portkey_api_key)

            # Return a wrapper that adapts Portkey to Anthropic interface
            return AnthropicPortkeyAdapter(portkey_client, provider_slug, model_name)

        except ImportError:
            print("⚠️  Portkey not installed, falling back to standard Anthropic client")
            print("   Install with: pip install portkey-ai")
            return Anthropic(api_key=api_key)
    else:
        # Standard Anthropic client (no observability)
        return Anthropic(api_key=api_key)


class AnthropicPortkeyAdapter:
    """
    Adapter that wraps Portkey client to provide Anthropic-compatible interface.

    This allows existing code using Anthropic SDK to work with Portkey's Model Catalog
    without modification.
    """

    def __init__(self, portkey_client, provider_slug: str, model_name: str):
        """Initialize adapter with Portkey client and model configuration."""
        self.portkey_client = portkey_client
        self.provider_slug = provider_slug
        self.model_name = model_name
        self.messages = MessagesAdapter(portkey_client, provider_slug, model_name)


class MessagesAdapter:
    """Adapter for messages.create() to work with Portkey's chat.completions interface."""

    def __init__(self, portkey_client, provider_slug: str, model_name: str):
        """Initialize messages adapter."""
        self.portkey_client = portkey_client
        self.provider_slug = provider_slug
        self.model_name = model_name

    def create(self, model: str = None, max_tokens: int = 4096, messages: list = None,
               tools: list = None, system: str = None, **kwargs):
        """
        Create a message using Portkey, translating from Anthropic to OpenAI format.

        This method translates Anthropic's messages.create() API to Portkey's
        chat.completions.create() API while maintaining compatibility.
        """
        # Use Model Catalog format: @provider-slug/model-name
        full_model = f"{self.provider_slug}/{self.model_name}"

        # Convert Anthropic messages format to OpenAI format
        openai_messages = []

        # Add system message if provided
        if system:
            openai_messages.append({"role": "system", "content": system})

        # Convert messages
        if messages:
            for msg in messages:
                # Extract content - handle both string and list formats
                content = msg.get("content", "")

                # If content is a list (Anthropic format with blocks), extract text
                if isinstance(content, list):
                    # Filter out empty blocks and extract text
                    text_parts = []
                    for block in content:
                        if isinstance(block, dict):
                            if block.get("type") == "text" and block.get("text"):
                                text_parts.append(block["text"])
                            elif block.get("type") == "tool_result":
                                # For tool results, include the content
                                result_content = block.get("content", "")
                                if isinstance(result_content, str) and result_content:
                                    text_parts.append(result_content)
                                elif isinstance(result_content, list):
                                    for item in result_content:
                                        if isinstance(item, dict) and item.get("text"):
                                            text_parts.append(item["text"])
                        elif isinstance(block, str):
                            text_parts.append(block)

                    content = "\n".join(text_parts) if text_parts else ""

                # Only add message if it has non-empty content
                # (OpenAI allows empty final assistant message, but not others)
                if content or (msg["role"] == "assistant" and msg == messages[-1]):
                    openai_messages.append({
                        "role": msg["role"],
                        "content": content
                    })

        # Convert Anthropic tools to OpenAI format if provided
        openai_tools = None
        if tools:
            openai_tools = self._convert_tools_to_openai(tools)

        # Call Portkey's chat.completions interface
        response = self.portkey_client.chat.completions.create(
            model=full_model,
            messages=openai_messages,
            max_tokens=max_tokens,
            tools=openai_tools,
            **kwargs
        )

        # Convert OpenAI response back to Anthropic format
        return self._convert_response_to_anthropic(response)

    def _convert_tools_to_openai(self, anthropic_tools):
        """
        Convert Anthropic tool format to OpenAI function calling format.

        Anthropic format:
        {
            "name": "tool_name",
            "description": "Tool description",
            "input_schema": {...}
        }

        OpenAI format:
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "Tool description",
                "parameters": {...}
            }
        }
        """
        openai_tools = []
        for tool in anthropic_tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {})
                }
            })
        return openai_tools

    def _convert_response_to_anthropic(self, openai_response):
        """Convert OpenAI-style response to Anthropic-style response."""
        from anthropic.types import Message, Usage, TextBlock, ToolUseBlock
        import json

        # Extract content
        choice = openai_response.choices[0]
        content = []

        # Add text content if present
        if choice.message.content:
            content.append(TextBlock(type="text", text=choice.message.content))

        # Handle tool calls if present
        if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
            for tool_call in choice.message.tool_calls:
                # Parse arguments if they're a JSON string
                arguments = tool_call.function.arguments
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        pass  # Keep as string if not valid JSON

                # Create Anthropic ToolUseBlock
                content.append(ToolUseBlock(
                    type="tool_use",
                    id=tool_call.id,
                    name=tool_call.function.name,
                    input=arguments
                ))

        # If no content at all, add empty text block
        if not content:
            content.append(TextBlock(type="text", text=""))

        # Create Anthropic-style usage
        usage = Usage(
            input_tokens=getattr(openai_response.usage, 'prompt_tokens', 0),
            output_tokens=getattr(openai_response.usage, 'completion_tokens', 0)
        )

        # Determine stop reason
        stop_reason = "end_turn"
        if hasattr(choice, 'finish_reason'):
            if choice.finish_reason == "tool_calls":
                stop_reason = "tool_use"
            elif choice.finish_reason == "stop":
                stop_reason = "end_turn"
            elif choice.finish_reason == "length":
                stop_reason = "max_tokens"

        # Create Anthropic-style message
        return Message(
            id=openai_response.id,
            type="message",
            role="assistant",
            content=content,
            model=openai_response.model,
            stop_reason=stop_reason,
            usage=usage
        )


def create_metadata(agent: str, phase: str, **kwargs) -> dict:
    """
    Create metadata dict for Portkey tracking.

    Args:
        agent: Agent name (e.g., "guest_finder", "topic_researcher")
        phase: Current phase (e.g., "planning", "search", "report")
        **kwargs: Additional metadata fields

    Returns:
        Metadata dictionary for Portkey

    Example:
        >>> metadata = create_metadata(
        ...     agent="guest_finder",
        ...     phase="search",
        ...     query_count=10,
        ...     iteration=1
        ... )
    """
    metadata = {"agent": agent, "phase": phase, "user": os.getenv("USER", "unknown")}

    # Add any additional metadata
    metadata.update(kwargs)

    return metadata
