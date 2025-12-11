"""
Kōhai AI - FastAPI Backend
Model: Qwen2.5-0.5B-Instruct with LoRA Adapter (X-LoRA Support)
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
import os
import uvicorn


# --- App Configuration ---
app = FastAPI(
    title="Kōhai AI",
    description="Bilingual AI Assistant (Indonesian/English)",
    version="1.0.0"
)

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request/Response Models ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str

# --- Model Configuration ---
BASE_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
LORA_ADAPTER_ID = "lumicero/Qwen2.5-bilingual-xlora"

# Generation parameters
MAX_SEQ_LEN = 512
MAX_NEW_TOKENS = 256
TEMPERATURE = 0.7
TOP_P = 0.9
TOP_K = 50

# --- Global Model Variables ---
model = None
tokenizer = None
DEVICE = "cpu"

# --- Load Model ---
def load_model():
    """Load the model using standard PEFT approach."""
    global model, tokenizer
    
    print(f"Using device: {DEVICE}")
    
    # 1. Load Tokenizer (from Base Model)
    print(f"Loading tokenizer from {BASE_MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL_ID,
        trust_remote_code=True,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"

    # 2. Load Base Model
    print(f"Loading base model: {BASE_MODEL_ID}...")
    torch_dtype = torch.float16 if DEVICE == "cuda" else torch.float32
    
    base_model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch_dtype,
        device_map=DEVICE,
        trust_remote_code=True,
    )
    base_model.config.use_cache = False

    # 3. Load LoRA Adapter
    print(f"Loading adapter: {LORA_ADAPTER_ID}...")
    model = PeftModel.from_pretrained(
        base_model,
        LORA_ADAPTER_ID,
    )
    model.eval()

    # 4. X-LoRA Activation (Optional/Safety Check)
    # Kode temanmu menyarankan ini untuk memastikan adapter X-LoRA aktif
    try:
        if hasattr(model, 'base_model') and hasattr(model.base_model, 'lora_model'):
            lora_model = model.base_model.lora_model
            if hasattr(lora_model, 'peft_config'):
                numeric_adapter_names = [k for k in lora_model.peft_config.keys() if k.isdigit()]
                if numeric_adapter_names:
                    print(f"Activating X-LoRA adapters: {numeric_adapter_names}")
                    lora_model.set_adapter(numeric_adapter_names)
    except Exception as e:
        print(f"Note: Standard adapter loading used ({e})")

    print("✓ Model loaded successfully!")

# --- Generate Response ---
def generate_response(message: str, history: List[ChatMessage] = []) -> str:
    """Generate a response from the model."""
    global model, tokenizer
    
    # Build conversation messages
    messages = []
    
    # System prompt
    messages.append({
        "role": "system",
        "content": "Anda adalah Waguri AI, asisten AI yang ramah dan membantu. Anda fasih berbahasa Indonesia dan Inggris. Jawab pertanyaan dengan jelas, singkat, dan informatif."
    })
    
    # Add chat history
    for msg in history[-6:]:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    # Add current message
    messages.append({
        "role": "user",
        "content": message
    })
    
    # Apply chat template
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Tokenize
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=MAX_SEQ_LEN
    )
    
    # Move to device
    inputs = {k: v.to(DEVICE) for k, v in inputs.items()}
    
    # Generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            top_k=TOP_K,
            do_sample=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    # Decode response
    generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True)
    
    return response.strip()

# --- API Endpoints ---
@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    load_model()

@app.get("/")
async def root():
    """Serve the frontend."""
    return FileResponse("web/index.html")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint."""
    try:
        response = generate_response(request.message, request.history)
        return ChatResponse(response=response)
    except Exception as e:
        print(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "device": DEVICE
    }

# --- Mount Static Files ---
app.mount("/web", StaticFiles(directory="web"), name="static")

# --- Main Entry Point ---
if __name__ == "__main__":
    print("\n" + "="*50)
    print("  🍰 Waguri AI - Starting Server (X-LoRA Mode)...")
    print("="*50 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
