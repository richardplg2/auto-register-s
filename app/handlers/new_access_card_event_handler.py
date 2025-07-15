from app.core.event_bus import Event, EventHandler


class NewAccessCardEventHandler(EventHandler):
    async def handle(self, event: Event) -> None:
        if isinstance(event, NewAccessCardEvent):
            await self.process_new_access_card_event(event)

    async def process_new_access_card_event(self, event: NewAccessCardEvent) -> None:
        # Implement your event processing logic here
        pass
