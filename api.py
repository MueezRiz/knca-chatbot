from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import os
import json
import urllib.request
import re
import asyncio
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -------------------------------------------------------------
# DYNAMIC INVENTORY UPDATER (BACKGROUND TASK)
# -------------------------------------------------------------
def strip_html(html_str):
    if not html_str: return ""
    text = re.sub('<[^<]+?>', ' ', html_str)
    return re.sub('\\s+', ' ', text).strip()

def fetch_and_update_catalog():
    print("Fetching latest products from Shopify...")
    base_url = "https://knca.pk/collections/all/products.json?limit=250&page="
    all_products = []
    page = 1
    
    while True:
        url = base_url + str(page)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                products = data.get('products', [])
                if not products:
                    break
                for p in products:
                    clean_product = {
                        "title": p.get("title", ""),
                        "product_type": p.get("product_type", "Other").strip(),
                        "description": strip_html(p.get("body_html", "")),
                        "available": True,
                        "variants": []
                    }
                    if not clean_product["product_type"]:
                        clean_product["product_type"] = "Other"
                        
                    for v in p.get("variants", []):
                        clean_variant = {
                            "id": v.get("id", ""),
                            "title": v.get("title", ""),
                            "price": v.get("price", ""),
                            "available": v.get("available", True)
                        }
                        clean_product["variants"].append(clean_variant)
                        
                    if clean_product["variants"]:
                        clean_product["available"] = any(v.get("available", True) for v in clean_product["variants"])
                    all_products.append(clean_product)
                page += 1
        except Exception as e:
            print(f"Shopify scrape error: {e}")
            break

    if not all_products:
        print("No products pulled, skipping update.")
        return

    grouped = {}
    for p in all_products:
        grouped.setdefault(p["product_type"], []).append(p)

    output_lines = [
        "** KARACHI NIMKO CHATKHARAY ACHAR - COMPLETE PRODUCT CATALOG **\n",
        "(CRITICAL INSTRUCTION: Reply ONLY using the information below. Do not invent products or prices. State 'OUT OF STOCK' if asked about sold-out items.)\n"
    ]

    for ptype, items in grouped.items():
        output_lines.append("======================================")
        output_lines.append(f" {ptype.upper()} ")
        output_lines.append("======================================")
        for idx, p in enumerate(items, 1):
            title = p.get("title", "")
            avail = "AVAILABLE" if p.get("available") else "OUT OF STOCK"
            output_lines.append(f"{idx}. {title} [{avail}]")
            
            desc = p.get("description", "")
            if desc:
                if len(desc) > 200: desc = desc[:197] + "..."
                output_lines.append(f"   - Details: {desc}")
                
            for v in p.get("variants", []):
                v_id = v.get("id", "")
                v_title = v.get("title", "")
                price = v.get("price", "N/A")
                v_avail = "Available" if v.get("available") else "Out of stock"
                if v_title and v_title.lower() != "default title":
                    output_lines.append(f"   - Variant: {v_title} | Rs. {price} ({v_avail}) | Variant ID: {v_id}")
                else:
                    output_lines.append(f"   - Price: Rs. {price} ({v_avail}) | Variant ID: {v_id}")
            output_lines.append("")

    with open("product_catalog.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print(f"Catalog dynamically updated with {len(all_products)} products.")

async def periodic_catalog_updater():
    while True:
        # Use to_thread so the synchronous HTTP request doesn't block FastAPI
        await asyncio.to_thread(fetch_and_update_catalog)
        # Wait for 1 hour (3600 seconds) before updating again
        await asyncio.sleep(3600)

@app.on_event("startup")
async def schedule_updater():
    print("Scheduling dynamic catalog updater background task...")
    asyncio.create_task(periodic_catalog_updater())

# -------------------------------------------------------------
# CHATBOT ENDPOINT
# -------------------------------------------------------------
def get_product_knowledge():
    try:
        with open("product_catalog.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Product catalog file not found."

BASE_SYSTEM_PROMPT = """You are the Digital Assistant for Karachi Nimko Chatkharay Achar (KNCA) on Walton Road, Lahore.

STRICT LANGUAGE INSTRUCTIONS:
1. You must ONLY reply in Roman Urdu (Urdu written using English alphabets).
2. DO NOT under any circumstances use the standard Urdu/Arabic script.
3. DO NOT use ANY Hindi words. This is absolute.
   - Use 'Khushamdeed' instead of 'Swagat'.
   - Use 'Assalam-o-Alaikum' instead of 'Namaste'.
   - Avoid typical Hindi terms altogether, stick strictly to everyday Pakistani Roman Urdu.

Delivery: Lahore only. DHA, Gulberg, Johar Town, Model Town, Garden Town, Faisal Town, Lahore Cantt, Township, Wapda Town, Valencia Town, Iqbal Town, and most nearby areas. Delivery is Rs. 200. FREE delivery on orders above Rs. 3000.

Restriction: We do NOT deliver outside Lahore and we do not deliver to Shahdara.

Call to Action: When a customer is ready to finalize their order, you MUST output a secret JSON command with the specific Variant IDs they want, exactly like this format:
<cart_command>
{{"command": "add_to_cart", "items": [{{"id": 43240838922487, "quantity": 2}}]}}
</cart_command>
Then, tell the user in Roman Urdu: "Bhai/Behan, aapka order maine cart mein add kar diya hai! Please website par upper checkout per click kar lein."
DO NOT tell them to use WhatsApp.
Email for query: knca93@gmail.com

---
SHOP CATALOG AND PRICING:
{catalog}
---
CRITICAL RULE: Rely ONLY on the shop catalog above to answer questions about products, availability, and prices. Do not invent items.
"""

class ChatRequest(BaseModel):
    user_input: str
    history: list[dict] = []

@app.get("/")
def home():
    return {"status": "Online", "store": "Karachi Nimko Chatkharay Achar"}

@app.post("/chat")
def chat_with_bot(request: ChatRequest):
    try:
        catalog_info = get_product_knowledge()
        final_system_prompt = BASE_SYSTEM_PROMPT.format(catalog=catalog_info)
        
        messages = [{"role": "system", "content": final_system_prompt}]
        messages.extend(request.history)
        messages.append({"role": "user", "content": request.user_input})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )
        return {"bot_says": completion.choices[0].message.content}

    except Exception as e:
        return {"error": str(e)}