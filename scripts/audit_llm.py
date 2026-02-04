import os
import sys
import yaml
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core classes
try:
    from core.llm_processor import BiliLLMProcessor
except ImportError:
    # Try importing assuming we are in project root
    sys.path.append(os.getcwd())
    from core.llm_processor import BiliLLMProcessor

def audit_llm_config():
    print("=== BiliVox LLM Configuration Audit ===")
    
    # 1. Check .env
    print("\n[1] Environment Variables (.env check):")
    load_dotenv()
    env_key = os.getenv("OPENAI_API_KEY")
    env_base = os.getenv("OPENAI_BASE_URL")
    env_model = os.getenv("MODEL_NAME")
    
    print(f"  OPENAI_API_KEY: {'[PRESENT]' if env_key else '[MISSING]'}")
    if env_key:
        print(f"    -> Masked: {env_key[:4]}...{env_key[-4:]}")
    print(f"  OPENAI_BASE_URL: {env_base}")
    print(f"  MODEL_NAME: {env_model}")

    # 2. Check config.yaml
    print("\n[2] config.yaml Configuration:")
    config_path = "config.yaml"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        
        llm_cfg = cfg.get("llm", {})
        pipeline_cfg = cfg.get("pipeline", {})
        
        print(f"  pipeline.mode: {pipeline_cfg.get('mode')}")
        print(f"  llm.enabled: {llm_cfg.get('enabled')}")
        print(f"  llm.max_tokens: {llm_cfg.get('max_tokens')}")
        print(f"  llm.temperature: {llm_cfg.get('temperature')}")
        print(f"  llm.system_prompt (preview): {str(llm_cfg.get('system_prompt', ''))[:50]}...")
    else:
        print("  [ERROR] config.yaml not found!")
        cfg = {}

    # 3. Runtime Initialization Check
    print("\n[3] BiliLLMProcessor Runtime Initialization:")
    try:
        processor = BiliLLMProcessor(cfg)
        
        print(f"  Initialization Status: {'SUCCESS' if processor.client else 'FAILED'}")
        if processor.disabled_reason:
            print(f"  Disabled Reason: {processor.disabled_reason}")
        
        if processor.client:
            print(f"  Client Base URL: {processor.client.base_url}")
            print(f"  Client API Key: {'[PRESENT]' if processor.client.api_key else '[MISSING]'}")
            print(f"  Active Model: {processor.model_name}")
            
            # Heuristic check for DeepSeek
            base_url_str = str(processor.client.base_url).lower()
            if "deepseek" in base_url_str or "siliconflow" in base_url_str:
                 print("  [VERIFIED] Connection points to DeepSeek/SiliconFlow infrastructure.")
            elif "openai.com" in base_url_str:
                 print("  [WARNING] Connection points to default OpenAI infrastructure.")
            else:
                 print(f"  [INFO] Custom infrastructure: {base_url_str}")
                 
    except Exception as e:
        print(f"  [CRITICAL] Runtime initialization crashed: {e}")

if __name__ == "__main__":
    audit_llm_config()
