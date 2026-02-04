import os
from typing import Optional, Dict
from dotenv import load_dotenv


class BiliLLMProcessor:
    """Bilibili 视频文本处理器"""
    
    def __init__(self, config: Dict):
        """
        初始化LLM处理器
        
        Args:
            config: 配置字典，包含LLM相关设置
        """
        # 加载环境变量
        load_dotenv()
        
        llm_cfg = config.get('llm', {}) if isinstance(config, dict) else {}
        self.enabled = bool(llm_cfg.get('enabled', True))
        self.system_prompt = llm_cfg.get('system_prompt') or '你是一个知识库整理专家。请忽略口语废话（如求三连、开场白），提取视频核心逻辑、关键论据和数据。输出格式为 Markdown，包含 Frontmatter（元数据）。'
        self.temperature = float(llm_cfg.get('temperature', 0.3))
        self.max_tokens = int(llm_cfg.get('max_tokens', 4096))
        self.disabled_reason = None
        
        # 初始化OpenAI客户端
        api_key = str(llm_cfg.get('api_key') or os.getenv('OPENAI_API_KEY') or '').strip()
        base_url = str(llm_cfg.get('api_base_url') or os.getenv('OPENAI_BASE_URL') or 'https://api.openai.com/v1').strip()
        model_name = str(llm_cfg.get('model_name') or os.getenv('MODEL_NAME') or 'gpt-4o-mini').strip()

        if base_url.endswith('/'):
            base_url = base_url[:-1]
        if base_url and not base_url.endswith('/v1') and 'openai.com' in base_url:
             # OpenAI 官方或兼容接口通常需要 /v1，但有些自定义接口可能不需要
             # 这里保留原有逻辑，但加上条件防止破坏非 /v1 结尾的自定义 URL
             base_url = base_url + '/v1'
        
        self.model_name = model_name
        self.client = None
        if not self.enabled:
            self.disabled_reason = "LLM 已禁用"
            return
        if not api_key:
            self.disabled_reason = "未配置 API Key，将仅输出原始转录文本"
            return

        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            self.client = None
            self.disabled_reason = f"LLM 初始化失败：{e}"
    
    def process_transcript(self, transcript: str, video_info: Dict) -> Optional[str]:
        """
        处理转录文本，生成结构化Markdown
        
        Args:
            transcript: 转录文本
            video_info: 视频信息字典
            
        Returns:
            生成的Markdown文本，失败返回None
        """
        try:
            fallback = self._build_fallback_markdown(transcript, video_info, reason=self.disabled_reason)
            if not self.enabled or self.client is None:
                return fallback

            # 构建用户提示词
            user_prompt = f"# 视频信息\n"
            user_prompt += f"标题: {video_info.get('title', '未知')}\n"
            user_prompt += f"BV号: {video_info.get('bv_id', '未知')}\n"
            user_prompt += f"发布日期: {video_info.get('upload_date', '未知')}\n"
            user_prompt += f"时长: {video_info.get('duration', '未知')}秒\n\n"
            user_prompt += "# 转录文本\n"
            
            # 检查文本长度，进行分段处理
            max_input_length = 15000  # 控制输入长度
            if len(transcript) > max_input_length:
                # 分段处理
                chunks = self._split_text(transcript, max_input_length)
                processed_chunks = []
                
                for i, chunk in enumerate(chunks):
                    chunk_prompt = user_prompt + chunk
                    processed_chunk = self._call_llm(chunk_prompt)
                    if processed_chunk:
                        processed_chunks.append(processed_chunk)
                
                # 合并处理结果
                if processed_chunks:
                    return '\n\n---\n\n'.join(processed_chunks)
                else:
                    return fallback
            else:
                # 完整处理
                full_prompt = user_prompt + transcript
                out = self._call_llm(full_prompt)
                return out or fallback
                
        except Exception as e:
            print(f"LLM处理失败: {e}")
            return self._build_fallback_markdown(transcript, video_info, reason=str(e))
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """
        调用LLM API
        
        Args:
            prompt: 提示词
            
        Returns:
            LLM返回的文本，失败返回None
        """
        try:
            if self.client is None:
                return None
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"调用LLM API失败: {e}")
            return None

    def _build_fallback_markdown(self, transcript: str, video_info: Dict, reason: str | None = None) -> str:
        title = str(video_info.get('title', '未知') or '未知').strip()
        bv = str(video_info.get('bv_id', '') or '').strip()
        upload_date = str(video_info.get('upload_date', '') or '').strip()
        duration = video_info.get('duration', '')
        url = str(video_info.get('url', '') or '').strip()

        frontmatter_lines = [
            "---",
            f"title: {title}",
        ]
        if bv:
            frontmatter_lines.append(f"bvid: {bv}")
            frontmatter_lines.append(f"bv: {bv}") # 冗余一个 bv 字段以兼容
        if upload_date:
            frontmatter_lines.append(f"upload_date: {upload_date}")
        if isinstance(duration, (int, float)) and duration:
            frontmatter_lines.append(f"duration_sec: {int(duration)}")
        if url:
            frontmatter_lines.append(f"url: {url}")
        
        # 尝试从 video_info 中获取 uid 和 author
        uid = str(video_info.get('uid', '') or '').strip()
        if not uid and video_info.get('owner_id'):
             uid = str(video_info.get('owner_id')).strip()
        if uid:
            frontmatter_lines.append(f"uid: {uid}")
            
        author = str(video_info.get('uploader') or video_info.get('owner') or '').strip()
        if author:
            frontmatter_lines.append(f"author: {author}")

        if reason:
            frontmatter_lines.append(f"llm: disabled ({reason})")
        frontmatter_lines.append("---")

        body = []
        body.append("# 原始转录")
        body.append("")
        body.append(str(transcript or '').strip())
        return "\n".join(frontmatter_lines + [""] + body).strip() + "\n"
    
    def _split_text(self, text: str, max_length: int) -> list:
        """
        分段文本
        
        Args:
            text: 原始文本
            max_length: 每段最大长度
            
        Returns:
            文本段列表
        """
        chunks = []
        current_chunk = []
        current_length = 0
        
        # 按行分割
        lines = text.split('\n')
        
        for line in lines:
            line_length = len(line) + 1  # 加换行符
            
            if current_length + line_length > max_length:
                # 保存当前段
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
        
        # 添加最后一段
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks
