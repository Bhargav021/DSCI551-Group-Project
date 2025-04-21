from google import genai

class Custom_GenAI:
    def __init__(self, API_KEY):
        self.client = genai.Client(api_key=API_KEY)

    def ask_ai(self, final_prompt):
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=final_prompt
        )
        return response.text
