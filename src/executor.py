"""A2A executor for the BWIM builder agent."""

import logging

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from agent import BuilderAgent

logger = logging.getLogger(__name__)


class BuilderExecutor(AgentExecutor):
    """A2A executor bridging protocol with builder agent."""

    def __init__(self):
        self.agents: dict[str, BuilderAgent] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        ctx_id = context.context_id
        user_input = context.get_user_input()

        # Get or create agent per context
        agent = self.agents.get(ctx_id)
        if agent is None:
            agent = BuilderAgent()
            self.agents[ctx_id] = agent

        # Get response from LLM
        response = agent.respond(user_input)

        await event_queue.enqueue_event(
            new_agent_text_message(response, context_id=ctx_id)
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        ctx_id = context.context_id
        if ctx_id in self.agents:
            del self.agents[ctx_id]
