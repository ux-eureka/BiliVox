import torch
import os
import inspect
from faster_whisper import WhisperModel
from typing import List, Dict, Optional


class BiliTranscriber:
    """Bilibili 视频转录器"""
    
    def __init__(self, config: Dict):
        """
        初始化转录器
        
        Args:
            config: 配置字典，包含转录相关设置
        """
        self.config = config if isinstance(config, dict) else {}
        transcribe_cfg = self.config.get('transcribe', {}) if isinstance(self.config, dict) else {}
        self.model_name = transcribe_cfg['model_name']
        self.compute_type = transcribe_cfg['compute_type']
        self.device = transcribe_cfg['device']
        raw_batch_size = transcribe_cfg['batch_size']
        try:
            self.batch_size = int(raw_batch_size)
        except Exception:
            raise ValueError('批处理大小必须是整数（范围：1~128）')
        if self.batch_size < 1 or self.batch_size > 128:
            raise ValueError('批处理大小范围：1~128')

        download_cfg = config.get('download', {}) if isinstance(config, dict) else {}
        self.ffmpeg_location = (
            download_cfg.get('ffmpeg_location')
            or download_cfg.get('ffmpegLocation')
            or os.getenv("BILIVOX_FFMPEG_LOCATION")
            or os.getenv("FFMPEG_LOCATION")
        )
        self._ensure_ffmpeg_in_path(self.ffmpeg_location)
        
        # 只在初始化时加载一次模型
        print(f"正在加载 Whisper 模型: {self.model_name} (设备: {self.device}, 计算类型: {self.compute_type})")
        self.model = WhisperModel(
            model_size_or_path=self.model_name,
            device=self.device,
            compute_type=self.compute_type,
            device_index=0,
            local_files_only=False  # 允许从缓存或下载加载
        )
        print("模型加载完成！")

    def _ensure_ffmpeg_in_path(self, ffmpeg_location: str | None):
        loc = str(ffmpeg_location or "").strip()
        if not loc:
            return
        if os.path.isfile(loc):
            ffmpeg_dir = os.path.dirname(loc)
        else:
            ffmpeg_dir = loc
        if not ffmpeg_dir or not os.path.isdir(ffmpeg_dir):
            return
        current = os.environ.get("PATH", "")
        parts = [p.strip() for p in current.split(os.pathsep) if p.strip()]
        if ffmpeg_dir not in parts:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + current
    
    def transcribe(self, audio_path: str, progress_callback=None, stop_event=None, clip_seconds: float | None = None) -> Optional[str]:
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            转录后的文本，失败返回None
        """
        try:
            vad_kwargs = {
                "threshold": 0.6,
                "min_speech_duration_ms": 250,
                "max_speech_duration_s": 30,
                "min_silence_duration_ms": 200,
                "speech_pad_ms": 300,
                "window_size_samples": 1024,
                "speech_threshold": 0.6,
                "silence_threshold": 0.3,
            }
            try:
                from faster_whisper.vad import VadOptions
                vad_sig = inspect.signature(VadOptions)
                vad_accepted = set(vad_sig.parameters.keys())
                vad_kwargs = {k: v for k, v in vad_kwargs.items() if k in vad_accepted}
            except Exception:
                vad_kwargs = {k: v for k, v in vad_kwargs.items() if k in ("threshold", "min_speech_duration_ms", "max_speech_duration_s", "min_silence_duration_ms", "speech_pad_ms")}

            clip_seconds_value = None
            try:
                if clip_seconds is not None:
                    clip_seconds_value = float(clip_seconds)
            except Exception:
                clip_seconds_value = None

            wanted_kwargs = {
                "audio": audio_path,
                "batch_size": self.batch_size,
                "beam_size": self.config.get('transcribe', {}).get('beam_size', 5),
                "best_of": 5,
                "patience": 1.0,
                "length_penalty": 1.0,
                "suppress_tokens": [-1],
                "initial_prompt": None,
                "condition_on_previous_text": True,
                "fp16": True if self.compute_type == 'float16' else False,
                "language": None,
                "task": "transcribe",
                "vad_filter": True,
                "vad_parameters": vad_kwargs,
                "clip_timestamps": [0.0, clip_seconds_value] if clip_seconds_value and clip_seconds_value > 0 else None,
            }

            sig = inspect.signature(self.model.transcribe)
            accepted = set(sig.parameters.keys())
            call_kwargs = {k: v for k, v in wanted_kwargs.items() if k in accepted and v is not None}
            segments, info = self.model.transcribe(**call_kwargs)
            
            # 构建转录文本，包含时间戳
            transcript = []
            duration = None
            try:
                duration = getattr(info, "duration", None) or getattr(info, "audio_duration", None)
            except Exception:
                duration = None
            for segment in segments:
                if stop_event is not None and getattr(stop_event, "is_set", None) and stop_event.is_set():
                    raise ValueError("已停止")
                start_time = self._format_time(segment.start)
                end_time = self._format_time(segment.end)
                if progress_callback:
                    try:
                        end_s = float(getattr(segment, "end", 0.0) or 0.0)
                    except Exception:
                        end_s = 0.0
                    frac = None
                    try:
                        if duration and float(duration) > 0:
                            frac = max(0.0, min(1.0, end_s / float(duration)))
                    except Exception:
                        frac = None
                    try:
                        progress_callback(frac, {"end": end_s, "duration": duration})
                    except Exception:
                        pass
                transcript.append(f"[{start_time} -> {end_time}] {segment.text}")
            
            return '\n'.join(transcript)
            
        except Exception as e:
            msg = str(e or "").strip()
            low = msg.lower()
            if "ffmpeg" in low and "not found" in low:
                raise ValueError("转录失败：未检测到 FFmpeg。请安装 FFmpeg 并加入 PATH，或在配置里填写 download.ffmpeg_location（指向 ffmpeg.exe 或其所在目录）。") from e
            if "已停止" in msg:
                raise e
            raise ValueError(f"转录失败: {msg}") from e
    
    def _format_time(self, seconds: float) -> str:
        """
        格式化时间
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的时间字符串 (HH:MM:SS)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def __del__(self):
        """
        析构函数，释放模型资源
        """
        try:
            if hasattr(self, 'model'):
                # 清除模型占用的显存
                del self.model
                # 强制垃圾回收
                import gc
                gc.collect()
                # 清除CUDA缓存
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
        except Exception as e:
            print(f"释放模型资源失败: {e}")
