from tutor_ai.llm_client import LLMError
from tutor_ai.tutor import InvalidQuestionError, answer, clean_question

EXIT_COMMAND = "exit"


def main() -> int:
    print(f"Python Tutor AI. Type your question, or '{EXIT_COMMAND}' to quit.")
    try:
        while True:
            question = input("> ")
            if question.strip().lower() == EXIT_COMMAND:
                break
            try:
                question = clean_question(question)
                print("Thinking...")
                reply = answer(question)
            except (InvalidQuestionError, LLMError) as err:
                print(f"Error: {err}")
                continue
            print(reply.text)
            print(f"({reply.seconds:.1f} s)")
    except (KeyboardInterrupt, EOFError):
        print()
    print("Bye.")
    return 0