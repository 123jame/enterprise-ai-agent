from app.services import ChatService

service = ChatService()

response = service.chat("Hello, introduce yourself.")

print(response.model)
print()
print(response.answer)