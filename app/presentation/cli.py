from app.config import load_settings
from app.presentation.agent import build_agent


def run_cli() -> None:
    """Main interaction loop for the agent with conversation memory."""
    settings = load_settings()
    agent = build_agent(settings)

    print("=" * 60)
    print("IDO AI Assistant - IDO System Helper")
    print("=" * 60)
    print("Type your questions about IDO.")
    print("Commands: 'exit', 'quit', 'q' to exit")
    print("Commands: 'clear' to clear conversation history\n")

    # Maintain conversation history for context
    conversation_messages = []

    while True:
        try:
            user_input = input("\n🤖 You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit", "q", "close"}:
                print("\n👋 Goodbye! Have a great day!")
                break

            if user_input.lower() in {"clear", "reset"}:
                conversation_messages = []
                print("\n✅ Conversation history cleared.")
                continue

            # Build messages with history
            messages = conversation_messages.copy()
            messages.append({"role": "user", "content": user_input})

            response = agent.invoke(
                {"messages": messages},
                max_iterations=settings.max_iterations,
            )
            
            # Get assistant response
            assistant_reply = response["messages"][-1].content
            
            # Update conversation history
            conversation_messages.append({"role": "user", "content": user_input})
            conversation_messages.append({"role": "assistant", "content": assistant_reply})
            
            # Keep only last 20 messages for context
            if len(conversation_messages) > 20:
                conversation_messages = conversation_messages[-20:]
            
            print("\n💡 Assistant:")
            print("-" * 60)
            print(assistant_reply)
            print("-" * 60)
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as exc:
            print(f"\n❌ Error: {exc}")
            print("Please try again or type 'exit' to quit.")

