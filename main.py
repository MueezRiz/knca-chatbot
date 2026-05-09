import os
from groq import Groq
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Initialize the Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are the Digital Assistant for Karachi Nimko Chatkharay Achar (KNCA) on Walton Road, Lahore.

STRICT LANGUAGE INSTRUCTIONS:
1. You must ONLY reply in Roman Urdu (Urdu written using English alphabets).
2. DO NOT under any circumstances use the standard Urdu/Arabic script.
3. DO NOT use ANY Hindi words. This is absolute.
   - Use 'Khushamdeed' instead of 'Swagat'.
   - Use 'Assalam-o-Alaikum' instead of 'Namaste'.
   - Avoid typical Hindi terms altogether, stick strictly to everyday Pakistani Roman Urdu.

Products: We specialize in Mix Nimko (Rs. 200/210), Gathia, and homemade Achars (Aam, Lasoora, Lemon). We also have frozen items like Peri Bites.

Delivery: Lahore only. DHA, Gulberg, Johar Town, Model Town, Garden Town, Faisal Town, Lahore Cantt, Township, Wapda Town, Valencia Town, Iqbal Town, and most nearby areas. Delivery is Rs. 200. FREE delivery on orders above Rs. 3000.

Restriction: We do NOT deliver outside Lahore and we do not deliver to Shahdara.

Call to Action: For final orders, tell customers to WhatsApp +92 320 4102779.
Email for query: knca93@gmail.com
"""

history = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

def generate_response(prompt):
    try:
        history.append(
            {
                "role":"user",
                "content":prompt
            }
        )
       
        chat_completion = client.chat.completions.create(
            messages=history,
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        reply = chat_completion.choices[0].message.content
        
        history.append(
            {
                "role":"assistant",
                "content":reply
            }
        )
        
        return reply
    
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    while True:
        user_prompt = input("User -> ")
        if user_prompt.lower() in ["exit","break"] :
            break
        print("--- Requesting Response from Groq ---")
        result = generate_response(user_prompt)
        print("AI -> ",result)
