"""Todo platform for Allegro: unread messages as a checklist."""

from __future__ import annotations

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import AllegroApiError
from .const import DOMAIN, ICON_MESSAGES
from .coordinator import AllegroConfigEntry, AllegroCoordinator
from .entity import AllegroEntity
from .messages import (
    CATEGORY_INVOICE,
    CATEGORY_ORDER_STATUS,
    MessageThread,
    collapse_text,
)

SUMMARY_LENGTH = 90
CATEGORY_TAGS = {CATEGORY_ORDER_STATUS: "auto", CATEGORY_INVOICE: "faktura"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AllegroConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Allegro messages checklist."""
    async_add_entities([AllegroMessagesTodo(entry.runtime_data)])


def _summary(thread: MessageThread) -> str:
    tag = CATEGORY_TAGS.get(thread.category)
    prefix = f"[{tag}] " if tag else ""
    text = collapse_text(thread.preview)
    if len(text) > SUMMARY_LENGTH:
        text = text[: SUMMARY_LENGTH - 1].rstrip() + "…"
    return f"{prefix}{thread.seller}: {text}"


class AllegroMessagesTodo(AllegroEntity, TodoListEntity):
    """Unread message threads. Checking an item marks the thread as read."""

    _attr_translation_key = "messages_todo"
    _attr_icon = ICON_MESSAGES
    _attr_supported_features = TodoListEntityFeature.UPDATE_TODO_ITEM

    def __init__(self, coordinator: AllegroCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._user_prefix}messages_todo"

    @property
    def todo_items(self) -> list[TodoItem] | None:
        """Return the unread threads, newest first."""
        data = self.coordinator.data
        if data is None:
            return None
        return [
            TodoItem(
                uid=thread.id,
                summary=_summary(thread),
                status=TodoItemStatus.NEEDS_ACTION,
                description=collapse_text(thread.preview),
            )
            for thread in data.messages.unread_threads
        ]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        """Mark the thread as read when its item is checked."""
        if item.status != TodoItemStatus.COMPLETED or not item.uid:
            return
        try:
            await self.coordinator.async_open_thread(item.uid)
        except AllegroApiError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="mark_read_failed",
                translation_placeholders={"error": str(err)},
            ) from err
