from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import os
from dotenv import load_dotenv
import logging

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="NCHC LLM Wrapper API",
    description="FastAPI 封裝 NCHC Chat Completions API",
    version="1.0.0"
)

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 模型
class Message(BaseModel):
    role: str = Field(..., description="訊息角色: system, user, assistant")
    content: str = Field(..., description="訊息內容")

class ChatCompletionRequest(BaseModel):
    model: str = Field("Llama-4-Maverick-17B-128E-Instruct-FP8", description="使用的模型名稱")
    messages: List[Message] = Field(..., description="對話歷史")
    max_tokens: Optional[int] = Field(100000, description="最大 token 數量")
    temperature: Optional[float] = Field(0.7, description="溫度參數 (0-1)")
    top_p: Optional[float] = Field(None, description="Top-p 參數")
    frequency_penalty: Optional[float] = Field(None, description="頻率懲罰")
    presence_penalty: Optional[float] = Field(None, description="存在懲罰")

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, Any]

class SimpleChatRequest(BaseModel):
    message: str = Field(..., description="使用者訊息")
    system_prompt: Optional[str] = Field("你是一個樂於助人的助手。請使用中文繁體，不要使用任何簡體中文。", description="系統提示詞")
    model: Optional[str] = Field("Llama-4-Maverick-17B-128E-Instruct-FP8", description="使用的模型")

class SimpleChatResponse(BaseModel):
    response: str
    model: str
    usage: Dict[str, Any]

# 設定
NCHC_API_BASE_URL = "https://portal.genai.nchc.org.tw/api/v1"
API_KEY = os.getenv("NCHC_API_KEY")

if not API_KEY:
    logger.warning("NCHC_API_KEY 環境變數未設定")

async def get_api_key():
    """取得 API Key"""
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API Key 未設定，請設定 NCHC_API_KEY 環境變數"
        )
    return API_KEY

@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "NCHC LLM Wrapper API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "api_key_configured": bool(API_KEY)}

@app.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    api_key: str = Depends(get_api_key)
):
    """
    完整的 Chat Completions API 端點
    直接轉發到 NCHC API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NCHC_API_BASE_URL}/chat/completions",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json=request.dict(exclude_none=True),
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"NCHC API 錯誤: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"NCHC API 錯誤: {response.text}"
                )
            
            return response.json()
            
    except httpx.TimeoutException:
        logger.error("請求超時")
        raise HTTPException(status_code=408, detail="請求超時")
    except httpx.RequestError as e:
        logger.error(f"請求錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"請求錯誤: {str(e)}")
    except Exception as e:
        logger.error(f"未預期錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"未預期錯誤: {str(e)}")

@app.post("/chat/simple", response_model=SimpleChatResponse)
async def simple_chat(
    request: SimpleChatRequest,
    api_key: str = Depends(get_api_key)
):
    """
    簡化的聊天端點
    只需要提供使用者訊息，自動處理對話格式
    """
    try:
        # 建立訊息列表
        messages = []
        
        # 添加系統訊息
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        # 添加使用者訊息
        messages.append({
            "role": "user",
            "content": request.message
        })
        
        # 準備請求
        chat_request = {
            "model": request.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NCHC_API_BASE_URL}/chat/completions",
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                },
                json=chat_request,
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"NCHC API 錯誤: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"NCHC API 錯誤: {response.text}"
                )
            
            result = response.json()
            
            # 提取回應內容
            if result.get("choices") and len(result["choices"]) > 0:
                assistant_message = result["choices"][0]["message"]["content"]
            else:
                assistant_message = "無法生成回應"
            
            return SimpleChatResponse(
                response=assistant_message,
                model=request.model,
                usage=result.get("usage", {})
            )
            
    except httpx.TimeoutException:
        logger.error("請求超時")
        raise HTTPException(status_code=408, detail="請求超時")
    except httpx.RequestError as e:
        logger.error(f"請求錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"請求錯誤: {str(e)}")
    except Exception as e:
        logger.error(f"未預期錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"未預期錯誤: {str(e)}")

@app.get("/models")
async def list_models():
    """取得可用模型列表"""
    return {
        "models": [
            {
                "id": "Llama-4-Maverick-17B-128E-Instruct-FP8",
                "name": "Llama-4-Maverick-17B-128E-Instruct-FP8",
                "description": "Llama-4-Maverick-17B-128E-Instruct-FP8"
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
