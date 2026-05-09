# 🌶️ KNCA Auto-Cart Transactional AI Agent

A fully autonomous, Shopify-integrated, strict Roman-Urdu speaking AI Agent representing **Karachi Nimko Chatkharay Achaar**. 

Unlike standard "Q&A" bots that simply tell customers to "WhatsApp your order," this project is a true **Transactional Agent** engineered to browse products, check live availability, and autonomously inject products directly into a customer's shopping cart.

---

## ⚡ Core Architecture & Functionality

### 1. The Vibe Check (Strict Language Guardrails)
The Large Language Model (Llama-3-70b via Groq) is prompt-engineered with severe restrictions to maintain a natively authentic Pakistani e-commerce experience.
* Completely bans Arabic/Urdu scripts.
* Strictly enforces Roman-Urdu communication.
* Explicitly programmed to avoid common overlapping Hindi vocabulary (e.g., uses *"Khushamdeed"* instead of *"Swagat"*).

### 2. The Dynamic Brain (Auto-Scraper Worker)
Hardcoded prices become outdated in minutes. This API features a "Zero-Maintenance" backend architecture. 
* A `FastAPI` background `asyncio` worker continuously runs while the server is active.
* Every hour, it silently crawls the live Shopify JSON API (`/collections/all/products.json`).
* It automatically extracts titles, HTML-sanitized descriptions, variant sizes (e.g., 250gms vs 500gms), variant IDs, and real-time stock availability.
* It reconstructs the LLM's system prompt memory bank (`product_catalog.txt`) on the fly, meaning the bot instantly knows if a specific product goes "Out of Stock" without any developer input.

### 3. The Holy Grail: Auto-Cart Interceptor
This is the primary transactional engine of the project.
* **Backend:** When a customer finalizes an order in the chat, the LLM is trained to identify the exact Shopify `Variant IDs` required. Instead of showing the user ugly code, the AI secretly emits an `<cart_command>` JSON payload.
* **Frontend:** The lightweight UI is trained to scan incoming chat streams for this payload via Regex. Upon detection, it intercepts it, strips it out of the UI so the customer never sees it, and triggers a simulated Shopify AJAX `/cart/add.js` checkout event.

---

## 🛠️ The Tech Stack (Zero Bloat)
* **LLM Engine:** Groq Cloud (`llama-3.3-70b-versatile`)
* **Backend:** Python + FastAPI + Uvicorn + Asyncio
* **Frontend UI:** Pure Vanilla HTML / CSS / Javascript. 
*(Note: A heavy frontend framework like React was explicitly avoided. The goal is to ultimately inject this UI cleanly as a floating chat-bubble widget over a production Shopify liquid template. Using lightweight vanilla libraries ensures zero performance degradation for the main e-commerce website engine).*

---

## 🚀 How to Run Locally

1. Create a virtual environment and generate your `.env` file containing:
   `GROQ_API_KEY=your_key_here`
2. Activate your environment:
   ```bash
   source chatbot-env/bin/activate
   ```
3. Boot the FastAPI background brain:
   ```bash
   python3 -m uvicorn api:app --reload
   ```
4. Boot the frontend widget server (in a separate terminal):
   ```bash
   python3 -m http.server 8080
   ```
5. Navigate to `http://localhost:8080/index.html` to begin chatting with the automated agent!
