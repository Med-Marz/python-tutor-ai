from tutor_ai.config import ConfigError, load_settings
from tutor_ai.llm_client import LLMError
from tutor_ai.tutor import InvalidQuestionError, answer, clean_question

EXIT_COMMAND = "exit"


def main() -> int:
    try:
        settings = load_settings()
    except ConfigError as err:
        print(f"Error: {err}")
        return 1

    print(f"Python Tutor AI ({settings.model}).")
    print(f"Type your question, or '{EXIT_COMMAND}' to quit.")
    try:
        while True:
            question = input("> ")
            if question.strip().lower() == EXIT_COMMAND:
                break
            try:
                question = clean_question(question)
                print("Thinking...")
                reply = answer(question, settings)
            except (InvalidQuestionError, LLMError) as err:
                print(f"Error: {err}")
                continue
            print(reply.text)
            print(f"({reply.seconds:.1f} s)")
    except (KeyboardInterrupt, EOFError):
        print()
    print("Bye.")
    return 0
