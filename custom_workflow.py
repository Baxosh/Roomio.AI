"""
Custom workflow handler for Roomio AI.

This module provides a custom workflow handler with Roomio branding
in the welcome message instead of the default Vanna branding.
"""

from typing import TYPE_CHECKING, List, Optional

from vanna.components import RichTextComponent, UiComponent
from vanna.core.workflow.base import WorkflowHandler

if TYPE_CHECKING:
    from vanna.core.agent.agent import Agent
    from vanna.core.storage import Conversation
    from vanna.core.user.models import User


class RoomioWorkflowHandler(WorkflowHandler):
    """Custom workflow handler with Roomio branding."""

    async def try_handle(
        self, agent: "Agent", user: "User", conversation: "Conversation", message: str
    ):
        """No custom workflow handling - pass through to LLM."""
        from vanna.core.workflow.base import WorkflowResult

        return WorkflowResult(should_skip_llm=False)

    async def get_starter_ui(
        self, agent: "Agent", user: "User", conversation: "Conversation"
    ) -> Optional[List[UiComponent]]:
        """Generate starter UI with Roomio branding."""

        components = []

        welcome_content = (
            "# 👋 Welcome to Roomio AI!\n\n"
            "I'm your AI data analyst assistant, ready to help you explore your data!\n\n"
            "Go ahead and ask me anything about your data!\n\n"
        )

        components.append(
            UiComponent(
                rich_component=RichTextComponent(
                    content=welcome_content, markdown=True
                ),
                simple_component=None,
            )
        )

        return components
