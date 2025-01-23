import time

# Langchain imports
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate


chat_template = """

Answer the question below. 

Here is the conversation history: {context}

Question: {question}

Answer: """


class Model:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self.model = OllamaLLM(model=model_name)
        self.exit_commands = ["exit", "exit()", "leave", "leave()", "stop", "stop()"]

    def get_result(self, prompt: str):
        result = self.model.invoke(input=prompt)
        return result

    def handle_chat(self, invoke_instructions: dict):
        prompt = ChatPromptTemplate.from_template(chat_template)
        chain = prompt | self.model
        result = chain.invoke(invoke_instructions)
        return result

    def get_chain_result(self, invoke_instructions: dict, template: str) -> str:
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.model
        result = chain.invoke(invoke_instructions)
        return result

    def start_chat(self):
        context = ""
        context_template = "User: {}\nChatbot: {}"
        chatting = True
        print(
            f"\n\n===========================================\nHello I am [{self.model_name}], how can I help you?\n\n"
        )
        while chatting:

            user_input = str(input("Enter a prompt: "))
            if user_input.lower() in self.exit_commands:
                chatting = False
            prompt = (
                f"Here is the context: {context}\n\nHere user's response: {user_input}"
            )
            print(f"\n[User]: {user_input}\n\n")
            model_response = self.get_result(prompt)
            print(f"\n[Model]: {model_response}\n\n")
            current_context = context_template.format(user_input, model_response)
            # Add current context to memory.
            context += current_context


if __name__ == "__main__":

    model = Model(model_name="deepseek-r1")
    model.start_chat()
