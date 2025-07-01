#!/usr/bin/env python3
"""
NCHC LLM Wrapper API 測試腳本
"""

import requests
import json
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# API 基礎 URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """測試健康檢查端點"""
    print("🔍 測試健康檢查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"錯誤: {e}")
        return False

def test_root():
    """測試根路徑"""
    print("\n🏠 測試根路徑...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"錯誤: {e}")
        return False

def test_models():
    """測試模型列表端點"""
    print("\n🤖 測試模型列表...")
    try:
        response = requests.get(f"{BASE_URL}/models")
        print(f"狀態碼: {response.status_code}")
        print(f"回應: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"錯誤: {e}")
        return False

def test_simple_chat():
    """測試簡化聊天端點"""
    print("\n💬 測試簡化聊天...")
    
    # 檢查 API Key 是否設定
    api_key = os.getenv("NCHC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("⚠️  API Key 未設定，跳過聊天測試")
        return True
    
    try:
        payload = {
            "message": "你好，請簡單介紹一下你自己",
            "system_prompt": "你是一個樂於助人的助手。",
            "model": "Llama3-TAIDE-LX-8B-Chat-Alpha1"
        }
        
        response = requests.post(
            f"{BASE_URL}/chat/simple",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"回應: {result['response'][:100]}...")
            print(f"模型: {result['model']}")
            print(f"使用量: {result['usage']}")
        else:
            print(f"錯誤回應: {response.text}")
        
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print("⏰ 請求超時")
        return False
    except Exception as e:
        print(f"錯誤: {e}")
        return False

def test_full_chat_completions():
    """測試完整聊天完成端點"""
    print("\n🔄 測試完整聊天完成...")
    
    # 檢查 API Key 是否設定
    api_key = os.getenv("NCHC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("⚠️  API Key 未設定，跳過聊天測試")
        return True
    
    try:
        payload = {
            "model": "Llama3-TAIDE-LX-8B-Chat-Alpha1",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一個樂於助人的助手。"
                },
                {
                    "role": "user",
                    "content": "請用一句話介紹台灣"
                }
            ],
            "max_tokens": 100,
            "temperature": 0.7
        }
        
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"回應 ID: {result.get('id', 'N/A')}")
            print(f"模型: {result.get('model', 'N/A')}")
            if result.get('choices'):
                content = result['choices'][0]['message']['content']
                print(f"內容: {content}")
            print(f"使用量: {result.get('usage', {})}")
        else:
            print(f"錯誤回應: {response.text}")
        
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print("⏰ 請求超時")
        return False
    except Exception as e:
        print(f"錯誤: {e}")
        return False

def main():
    """主測試函數"""
    print("🚀 開始測試 NCHC LLM Wrapper API")
    print("=" * 50)
    
    tests = [
        ("健康檢查", test_health_check),
        ("根路徑", test_root),
        ("模型列表", test_models),
        ("簡化聊天", test_simple_chat),
        ("完整聊天完成", test_full_chat_completions)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 執行測試: {test_name}")
        print("-" * 30)
        
        if test_func():
            print(f"✅ {test_name} 測試通過")
            passed += 1
        else:
            print(f"❌ {test_name} 測試失敗")
    
    print("\n" + "=" * 50)
    print(f"📊 測試結果: {passed}/{total} 通過")
    
    if passed == total:
        print("🎉 所有測試都通過了！")
    else:
        print("⚠️  部分測試失敗，請檢查設定和連線")

if __name__ == "__main__":
    main() 