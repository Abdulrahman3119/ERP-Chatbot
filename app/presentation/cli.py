from app.config import load_settings
from app.presentation.agent import build_agent


def run_cli() -> None:
    """Main interaction loop for the agent."""
    settings = load_settings()
    agent = build_agent(settings)

    print("=" * 60)
    print("IDO AI Assistant - ERPNext Helper")
    print("=" * 60)
    print("Type your questions about ERPNext.")
    print("Commands: 'exit', 'quit', 'q' to exit\n")

    while True:
        try:
            user_input = input("\n🤖 You: ").strip()
            if not user_input:
                continue

            if user_input.lower() in {"exit", "quit", "q", "close"}:
                print("\n👋 Goodbye! Have a great day!")
                break

            response = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                max_iterations=settings.max_iterations,
            )
            print("\n💡 Assistant:")
            print("-" * 60)
            print(response["messages"][-1].content)
            print("-" * 60)
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as exc:
            print(f"\n❌ Error: {exc}")
            print("Please try again or type 'exit' to quit.")

