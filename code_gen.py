# File: code_gen.py
import openai
import os
import requests

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_code(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": f"Generate production-ready code for: {prompt}"}]
    )
    return response.choices[0].message.content

# Example: Generate marketing SaaS billing module
billing_code = generate_code("Python Stripe subscription system with 3 pricing tiers")
with open("src/billing.py", "w") as f:
    f.write(billing_code)
  
