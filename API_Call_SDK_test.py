from core import API_Call_SDK_v1

if __name__ == "__main__":
    ai = API_Call_SDK_v1.AIClient()

    while True:
        user_input = input("你: ")

        if user_input.lower() in ["exit", "quit"]:
            break

        response = ai.chat_json(user_input)
        print("AI:", response)
