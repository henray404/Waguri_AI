"""
Kōhai AI - FastAPI Backend (Language Switcher Supported)
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel, PeftConfig
import uvicorn
import gc
import os

# --- Constants ---
SYSTEM_PROMPT_ID = "Anda adalah Waguri, asisten AI yang cerdas, ramah, dan membantu dalam Bahasa Indonesia. Jawablah dengan sopan dan informatif."
SYSTEM_PROMPT_EN = "You are Waguri, a smart, friendly, and helpful AI assistant. Please answer in English politely and informatively."

# --- Config ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    lang: str = "id" # Menerima input bahasa (default indo)

class ChatResponse(BaseModel):
    response: str

# --- Model Variables ---
LORA_ADAPTER_ID = "lumicero/Qwen2.5-bilingual-xlora"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = None
tokenizer = None

MAX_SEQ_LEN = 1024  # Kaggle GPU memorinya besar (16GB), jangan pelit pake 512
MAX_NEW_TOKENS = 512
TEMPERATURE = 0.9
TOP_P = 0.9
TOP_K = 50

# --- Load Logic (X-LoRA Corrected) ---
def load_model():
    global model, tokenizer
    print(f"⚙️ Loading on {DEVICE}...")
    gc.collect()
    torch.cuda.empty_cache()

    try:
        peft_config = PeftConfig.from_pretrained(LORA_ADAPTER_ID)
        tokenizer = AutoTokenizer.from_pretrained(LORA_ADAPTER_ID, trust_remote_code=True)
        if tokenizer.pad_token_id is None: tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "left"
        
        base_model = AutoModelForCausalLM.from_pretrained(
            peft_config.base_model_name_or_path,
            torch_dtype=torch.bfloat16 if DEVICE == "cuda" else torch.float32,
            device_map=DEVICE,
            trust_remote_code=True
        )
        base_model.config.use_cache = False

        model = PeftModel.from_pretrained(base_model, LORA_ADAPTER_ID)
        model.to(DEVICE)
        model.eval()
        
        # Activate Router
        lora_model = model.base_model.lora_model
        numeric_adapter_names = [k for k in lora_model.peft_config.keys() if k.isdigit()]
        if numeric_adapter_names: lora_model.set_adapter(numeric_adapter_names)
        
        print("✅ Model Ready!")
    except Exception as e:
        print(f"❌ Error: {e}")

# --- Generate Logic ---
def generate(messages, max_new_tokens, temperature, ):
    input_ids = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt", max_length=MAX_SEQ_LEN
    ).to(DEVICE)


    with torch.no_grad():
        outputs = model.generate(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=0.9,
            pad_token_id=tokenizer.pad_token_id,
            top_k=50,
        )
    
    seq_len = input_ids.shape[1]
    return tokenizer.decode(outputs[0][seq_len:], skip_special_tokens=True).strip()

# --- Endpoints ---
@app.on_event("startup")
async def startup(): load_model()

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not model: raise HTTPException(503, "Model loading...")
    print(req.lang)
    
    # 1. Pilih System Prompt berdasarkan 'lang'
    sys_prompt = SYSTEM_PROMPT_ID if req.lang == "id" else SYSTEM_PROMPT_EN
    
    # 2. Susun Pesan
    messages = [{"role": "system", "content": sys_prompt}]
    for m in req.history: messages.append({"role": m.role, "content": m.content})
    # messages.append({"role": "user", "content": req.message})
    print(messages)
    # 3. Generate
    res = generate(messages, MAX_NEW_TOKENS, TEMPERATURE)
    return ChatResponse(response=res)

# Serve Frontend
if os.path.exists("web"):
    app.mount("/web", StaticFiles(directory="web"), name="static")
    @app.get("/")
    def index(): return FileResponse("web/index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)