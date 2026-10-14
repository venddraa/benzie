"""History lokal dan penyimpanan hasil request, tanpa Qt."""

from contextlib import closing
from pathlib import Path

from benzie.core.chat import ChatService
from benzie.inference.engine import InferenceCancelled
from benzie.persistence.conversations import ConversationStore


def completed_turns(messages):
    """Hanya pasangan user/assistant selesai; abaikan turn gagal/parsial/yatim."""
    result = []
    pending = None
    for message in messages:
        if message.role == "user":
            pending = message
        else:
            if pending is not None and message.status == "completed":
                result.extend([
                    {"role": "user", "content": pending.content},
                    {"role": "assistant", "content": message.content},
                ])
            pending = None
    return result


class HistoryService:
    def __init__(self, path: Path, chat: ChatService | None):
        self.store = ConversationStore(path)
        self.chat = chat

    def new_conversation(self):
        return self.store.create_conversation()

    def conversations(self):
        return self.store.list_conversations()

    def messages(self, conversation_id: int):
        return self.store.list_messages(conversation_id)

    def new_request(self, prompt: str, conversation_id: int):
        if self.chat is None:
            raise ValueError("Belum ada model dipilih.")
        return SavedRequest(self.store, conversation_id, prompt, self.chat.new_request(prompt))


class SavedRequest:
    def __init__(self, store, conversation_id, prompt, request):
        self.store = store
        self.conversation_id = conversation_id
        self.prompt = prompt
        self.request = request

    def cancel(self):
        self.request.cancel()

    def events(self):
        self.request.set_history(completed_turns(self.store.list_messages(self.conversation_id)))
        # Simpan input sebelum inference. Jika gagal, jangan mulai model.
        self.store.append_message(self.conversation_id, "user", self.prompt)
        parts = []
        status = "failed"
        try:
            with closing(self.request.events()) as events:
                for event in events:
                    if event.kind == "text":
                        parts.append(event.text)
                    yield event
            status = "completed"
        except InferenceCancelled:
            status = "cancelled"
            raise
        finally:
            # Cleanup inference sudah selesai sebelum menyimpan hasil akhir.
            self.store.append_message(
                self.conversation_id, "assistant", "".join(parts), status=status,
            )
