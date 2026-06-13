import google.generativeai as genai

genai.configure(api_key="Enter your API key")

model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content("Hello")
print(response.text)
