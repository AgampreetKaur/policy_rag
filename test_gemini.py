import google.generativeai as genai

genai.configure(api_key="AQ.Ab8RN6JHlN4qH5VfqUpxeC6mESzqwv0oD2rcQlW2NhY38P0BPA")

model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content("Hello")
print(response.text)