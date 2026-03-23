"""LLM-powered builder agent for Build What I Mean benchmark.

Receives natural language building instructions and outputs block placements
in the format: [BUILD];Color,X,Y,Z;Color,X,Y,Z;...
Or asks clarification: [ASK];Question text
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are Rita, an expert builder in a collaborative block-building game. You receive instructions from an architect describing structures to build on a 9×9×9 grid.

# Your Task
Interpret the architect's instructions and place colored blocks at the correct coordinates.

# Response Format
You MUST respond in ONE of these two formats:

## Option 1: BUILD (when you understand the instruction)
[BUILD];Color,X,Y,Z;Color,X,Y,Z;...

Example:
[BUILD];Red,0,0,0;Red,100,0,0;Blue,0,100,0

## Option 2: ASK (when the instruction is ambiguous - USE SPARINGLY, costs -5 points)
[ASK];Your specific question about the structure

# Grid Coordinate System
- The grid is 9×9×9
- Coordinates use increments of 100 (so valid X/Y/Z values are: -400, -300, -200, -100, 0, 100, 200, 300, 400)
- Y axis is vertical (0 = bottom, 400 = top... but structures typically use 0, 50, 100, 150, 200, 250, 300, 350)
- Actually, Y coordinates appear to use increments of 50 in examples

# Block Colors
Available colors: Red, Blue, Green, Yellow, Orange, Purple

# Strategy
- If the instruction is clear enough to build, BUILD immediately (+10 for correct, -10 for wrong)
- Only ASK if truly ambiguous (-5 per question)
- Pay attention to: colors mentioned, positions described (left/right/front/back/top/bottom), quantities
- When colors are not specified, make reasonable assumptions
- When numbers are not specified, use the most common/default interpretation

# IMPORTANT
- Output ONLY the [BUILD] or [ASK] response. No other text.
- Each block placement is Color,X,Y,Z separated by semicolons
- Capitalize color names (Red, not red)
"""


class BuilderAgent:
    """LLM-powered builder that interprets instructions and places blocks."""

    def __init__(self):
        self.backend = os.getenv("LLM_BACKEND", "bedrock")
        self.model = os.getenv("LLM_MODEL", "us.anthropic.claude-sonnet-4-6-20260516-v1:0")
        self.client = self._create_client()
        self.conversation_history: list[dict] = []

    def _create_client(self):
        if self.backend == "bedrock":
            from anthropic import AnthropicBedrock
            return AnthropicBedrock(
                aws_access_key=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
                aws_region=os.getenv("AWS_REGION", "us-east-1"),
            )
        else:
            from anthropic import Anthropic
            return Anthropic()

    def respond(self, message: str) -> str:
        """Process an instruction and return [BUILD] or [ASK] response."""
        self.conversation_history.append({"role": "user", "content": message})

        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=self.conversation_history,
            )
            reply = resp.content[0].text.strip()

            # Validate format
            if not reply.startswith("[BUILD]") and not reply.startswith("[ASK]"):
                # Try to extract [BUILD] or [ASK] from response
                if "[BUILD]" in reply:
                    reply = reply[reply.index("[BUILD]"):]
                elif "[ASK]" in reply:
                    reply = reply[reply.index("[ASK]"):]
                else:
                    # Default to a simple build if format is wrong
                    logger.warning(f"Invalid response format, defaulting: {reply[:100]}")
                    reply = "[BUILD];Red,0,0,0"

            self.conversation_history.append({"role": "assistant", "content": reply})
            logger.info(f"Response: {reply[:200]}")
            return reply

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return "[BUILD];Red,0,0,0"

    def reset(self):
        """Reset conversation for new evaluation."""
        self.conversation_history = []
