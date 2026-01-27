import os
import json
import time
import subprocess
from typing import List, Dict, Any, Optional
import torch
import threading
from datetime import datetime

# 导入BiliVox核心模块
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from core.downloader import BiliDownloader
from core.transcriber import BiliTranscriber
from core.llm_processor import BiliLLMProcessor
from core.bibigpt_client import BibiGPTClient
import yaml


class BiliVoxManager:
    """BiliVox管理器，处理后端核心逻辑"""
    
    def __init__(self):
        """初始化BiliVox管理器"""
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.repo_root = repo_root
        self.config_path = os.path.join(repo_root, 'config.yaml')
        self.history_path = os.path.join(repo_root, 'history.json')
        self.output_dir = os.path.join(repo_root, 'output')
        self.monitor_state_path = os.path.join(repo_root, 'monitor_state.json')
        self._monitor_lock = threading.Lock()
        self.last_diagnostics_task_id = None
        
        # 加载配置
        self.load_config()
        
        # 状态变量
        self.status = '空闲'  # 空闲/运行中/错误
        self.progress = 0
        self.logs = []
        self.gpu_usage = 0
        self.gpu_memory = 0
        self.cpu_usage = 0
        self.memory_usage = 0
        self._psutil_missing_logged = False
        self.last_saved_task_id = None
        self.last_saved_path = None
        self.last_saved_name = None
        self.last_saved_at = None
        self.current_task_id = None
        self.current_up_name = None
        self.current_title = None
        self.processing_thread = None
        self.stop_event = threading.Event()
        
        # 加载历史记录
        self.load_history()
        
        # 初始化BiliVox核心模块
        self.init_bilivox()

        try:
            import psutil
            psutil.cpu_percent(interval=None)
        except Exception:
            pass
    
    def init_bilivox(self):
        """初始化BiliVox核心模块"""
        try:
            # 只初始化下载器，延迟初始化转录器和LLM处理器
            self.downloader = BiliDownloader(self.config)
            self.transcriber = None
            self.llm_processor = None
            self.bibigpt_client = None
            self._log('核心模块初始化完成（延迟加载模型）')
        except Exception as e:
            self.status = '错误'
            self._log(f'初始化失败: {e}')
    
    def _load_models(self):
        """加载模型"""
        if self._get_pipeline_mode() == "local":
            if self.transcriber is None:
                try:
                    self._log('正在加载 Whisper 模型...')
                    self.transcriber = BiliTranscriber(self.config)
                    device = self.config.get('transcribe', {}).get('device')
                    model_name = self.config.get('transcribe', {}).get('model_name')
                    compute_type = self.config.get('transcribe', {}).get('compute_type')
                    batch_size = self.config.get('transcribe', {}).get('batch_size')
                    self._log(f'Whisper 模型加载完成（model={model_name}, device={device}, compute={compute_type}, batch={batch_size}）')
                except Exception as e:
                    self.status = '错误'
                    self._log(f'加载Whisper模型失败: {e}')

        try:
            from dotenv import load_dotenv
            load_dotenv(override=False)
        except Exception:
            pass

        if self._get_pipeline_mode() == "local":
            if self.llm_processor is not None and getattr(self.llm_processor, "client", None) is None:
                reason = str(getattr(self.llm_processor, "disabled_reason", "") or "")
                if "未配置 OPENAI_API_KEY" in reason and (os.getenv("OPENAI_API_KEY") or "").strip():
                    self.llm_processor = None

            if self.llm_processor is None:
                try:
                    self._log('正在初始化LLM处理器...')
                    self.llm_processor = BiliLLMProcessor(self.config)
                    if getattr(self.llm_processor, "client", None) is None:
                        reason = getattr(self.llm_processor, "disabled_reason", None)
                        if reason:
                            self._log(f'LLM 未启用：{reason}')
                        else:
                            self._log('LLM 未启用：将仅输出原始转录文本')
                    else:
                        self._log('LLM处理器初始化完成')
                except Exception as e:
                    self.llm_processor = None
                    self._log(f'初始化LLM处理器失败（将仅输出原始转录文本）: {e}')

    def _get_pipeline_mode(self) -> str:
        try:
            pipeline = self.config.get("pipeline", {}) if isinstance(self.config, dict) else {}
            mode = str(pipeline.get("mode") or "local").strip().lower()
            return mode or "local"
        except Exception:
            return "local"

    def _get_bibigpt_client(self) -> BibiGPTClient:
        if getattr(self, "bibigpt_client", None) is None:
            self.bibigpt_client = BibiGPTClient()
        return self.bibigpt_client

    def _build_markdown_from_bibigpt(self, bibigpt_payload: Dict[str, Any], video: Dict[str, Any]) -> str:
        summary = str(bibigpt_payload.get("summary") or "").strip()
        if not summary:
            raise ValueError("BibiGPT 未返回 summary")
        title = video.get("title") or ""
        bv_id = video.get("bv_id") or video.get("id") or ""
        url = video.get("url") or ""
        frontmatter = [
            "---",
            f"title: {title}",
            f"bv: {bv_id}",
            f"url: {url}",
            "source: bibigpt",
            "---",
            "",
        ]
        return "\n".join(frontmatter) + summary.strip() + "\n"

    def _summarize_with_bibigpt(self, url: str, video: Dict[str, Any], progress_fn, max_wait_sec: float = 1800.0) -> tuple[str, int]:
        client = self._get_bibigpt_client()
        created = client.create_summary_task(url)
        task_id = str(created.get("taskId") or "").strip()
        if not task_id:
            raise ValueError(f"BibiGPT 创建任务失败：{created}")

        started_at = time.time()
        last_log_ts = 0.0
        last_status = ""
        while True:
            if self.stop_event.is_set():
                raise ValueError("已停止")
            elapsed = time.time() - started_at
            if elapsed > float(max_wait_sec):
                raise TimeoutError(f"BibiGPT 任务超时（{int(max_wait_sec)}s）：taskId={task_id}")

            payload = client.get_summary_task_status(task_id, include_detail=False)
            status = str(payload.get("status") or "").strip()
            low = status.lower()
            if status and status != last_status and (time.time() - last_log_ts > 2.0):
                last_status = status

            if payload.get("summary"):
                md = self._build_markdown_from_bibigpt(payload, video)
                return md, int(elapsed)

            if low in ("failed", "error", "canceled", "cancelled"):
                raise ValueError(payload.get("message") or f"BibiGPT 任务失败：status={status}")

            if progress_fn:
                try:
                    progress_fn(elapsed)
                except Exception:
                    pass

            if time.time() - last_log_ts > 12.0:
                last_log_ts = time.time()
                self._log(f'BibiGPT 总结中... 已运行 {int(elapsed)}s（status={status or "unknown"}）')

            time.sleep(3.0)
    
    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            if not isinstance(self.config, dict):
                self.config = {}
            if 'pipeline' not in self.config or not isinstance(self.config.get('pipeline'), dict):
                self.config['pipeline'] = {'mode': 'local'}
            else:
                self.config['pipeline'].setdefault('mode', 'local')
        except Exception as e:
            # 使用默认配置
            self.config = {
                'up_list': [],
                'pipeline': {
                    'mode': 'local'
                },
                'download': {
                    'temp_dir': 'temp',
                    'output_dir': 'output',
                    'audio_format': 'm4a',
                    'ffmpeg_location': '',
                    'cookiefile': '',
                    'cookies_from_browser': '',
                    'headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    }
                },
                'transcribe': {
                    'model_name': 'large-v3',
                    'compute_type': 'float16',
                    'device': 'cuda',
                    'batch_size': 24
                },
                'llm': {
                    'enabled': True,
                    'system_prompt': '你是一个知识库整理专家。请忽略口语废话（如求三连、开场白），提取视频核心逻辑、关键论据和数据。输出格式为 Markdown，包含 Frontmatter（元数据）。',
                    'temperature': 0.3,
                    'max_tokens': 4096
                }
            }
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
        except Exception as e:
            self.logs.append(f'保存配置失败: {e}')
    
    def load_history(self):
        """加载历史记录"""
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            else:
                self.history = []
        except Exception as e:
            self.history = []
    
    def save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logs.append(f'保存历史记录失败: {e}')
    
    def get_config(self):
        """获取完整配置"""
        return {
            'upList': [
                {"name": str(i.get("name", "")), "uid": str(i.get("uid", ""))}
                for i in (self.config.get('up_list', []) or [])
                if isinstance(i, dict)
            ],
            'pipeline': self.config.get('pipeline', {}),
            'download': self.config.get('download', {}),
            'transcribe': self.config.get('transcribe', {}),
            'llm': self.config.get('llm', {})
        }
    
    def update_config(self, config_data):
        """更新完整配置"""
        up_list = []
        for item in (config_data.get('upList', []) or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get('name', '') or '').strip()
            uid = str(item.get('uid', '') or '').strip()
            if not uid:
                continue
            up_list.append({'name': name or f'UID {uid}', 'uid': uid})
        self.config['up_list'] = up_list
        
        # 更新下载配置
        if 'download' in config_data and isinstance(config_data.get('download'), dict):
            if 'download' not in self.config or not isinstance(self.config.get('download'), dict):
                self.config['download'] = {}
            self.config['download'].update(config_data['download'])

        if 'pipeline' in config_data and isinstance(config_data.get('pipeline'), dict):
            if 'pipeline' not in self.config or not isinstance(self.config.get('pipeline'), dict):
                self.config['pipeline'] = {}
            self.config['pipeline'].update(config_data['pipeline'])
            
        # 更新转录配置
        if 'transcribe' in config_data and isinstance(config_data.get('transcribe'), dict):
            if 'transcribe' not in self.config or not isinstance(self.config.get('transcribe'), dict):
                self.config['transcribe'] = {}
            incoming = dict(config_data.get('transcribe') or {})
            if 'batch_size' in incoming:
                raw = incoming.get('batch_size')
                try:
                    batch_size = int(raw)
                except Exception:
                    raise Exception('批处理大小必须是整数（范围：1~128）')
                if batch_size < 1 or batch_size > 128:
                    raise Exception('批处理大小范围：1~128')
                incoming['batch_size'] = batch_size
            self.config['transcribe'].update(incoming)
            
        # 更新LLM配置
        if 'llm' in config_data and isinstance(config_data.get('llm'), dict):
            if 'llm' not in self.config or not isinstance(self.config.get('llm'), dict):
                self.config['llm'] = {}
            self.config['llm'].update(config_data['llm'])
            
        self.save_config()
        # 重新初始化BiliVox模块
        self.init_bilivox()
    
    def start_processing(self):
        """开始处理任务"""
        if self.status == '运行中':
            return
        
        self.status = '运行中'
        self.progress = 0
        self.logs = []
        self.stop_event.clear()
        
        # 启动处理线程
        self.processing_thread = threading.Thread(target=self._process_task, kwargs={})
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def start_processing_for_up(self, up: Dict[str, Any], force: bool = False, max_videos: int | None = None, task_id: str | None = None):
        if self.status == '运行中':
            raise Exception('系统正忙：已有任务在运行')

        self.status = '运行中'
        self.progress = 0
        self.logs = []
        self.stop_event.clear()

        self.processing_thread = threading.Thread(
            target=self._process_task,
            kwargs={"up_list_override": [up], "force": force, "max_videos": max_videos, "task_id": task_id},
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def start_processing_for_video(self, up_name: str, video: Dict[str, Any], force: bool = False, task_id: str | None = None):
        if self.status == '运行中':
            raise Exception('系统正忙：已有任务在运行')

        self.status = '运行中'
        self.progress = 0
        self.logs = []
        self.stop_event.clear()
        self.current_task_id = task_id
        self.current_up_name = up_name
        self.current_title = video.get('title')

        self.processing_thread = threading.Thread(
            target=self._process_single_video,
            kwargs={"up_name": up_name, "video": video, "force": force, "task_id": task_id},
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def stop_processing(self):
        """停止处理任务"""
        if self.status != '运行中':
            return
        
        self.stop_event.set()
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        
        self.status = '空闲'
        self.current_task_id = None
        self.current_up_name = None
        self.current_title = None
        self._log('任务已停止')
    
    def _process_task(self, up_list_override: List[Dict[str, Any]] | None = None, force: bool = False, max_videos: int | None = None, task_id: str | None = None):
        """处理任务的线程函数"""
        try:
            # 加载模型
            self._log('开始处理任务，加载必要的模型...')
            self._load_models()
            
            # 检查模型加载状态
            if self.status == '错误':
                self._log('模型加载失败，停止处理任务')
                self.status = '空闲'
                return
            
            up_list = up_list_override if up_list_override is not None else self.config.get('up_list', [])
            total_up = len(up_list)
            processed_up = 0
            
            for up in up_list:
                if self.stop_event.is_set():
                    break
                
                up_name = up['name']
                up_uid = up['uid']
                self.current_task_id = task_id
                self.current_up_name = up_name
                self.current_title = None
                
                self._log(f'开始处理 UP 主: {up_name}')
                
                # 获取视频列表
                videos = self.downloader.get_video_list(up_uid)
                if not videos:
                    self._log(f'获取视频列表失败: {up_name}')
                    processed_up += 1
                    self.progress = int((processed_up / total_up) * 100)
                    continue
                if max_videos and int(max_videos) > 0:
                    videos = videos[: int(max_videos)]
                
                total_videos = len(videos)
                processed_videos = 0
                
                for video in videos:
                    if self.stop_event.is_set():
                        break
                    
                    try:
                        # 检查是否需要处理
                        if not force and not self._should_process_video(video, up_name):
                            existing = self._find_existing_markdown_for_video(video, up_name)
                            if existing:
                                self.last_saved_task_id = task_id
                                self.last_saved_path = existing
                                self.last_saved_name = os.path.basename(existing)
                                self.last_saved_at = int(time.time())
                                self._add_history(up_name, video.get('title', '未知'), '成功', task_id=task_id, file_path=existing, detail='检测到已有文档，已跳过', duration_sec=0)
                            else:
                                self._add_history(up_name, video.get('title', '未知'), '失败', task_id=task_id, file_path=None, detail='检测到已有文档但未能定位产物', duration_sec=0)
                            processed_videos += 1
                            continue
                        
                        title = video.get('title', '未知')
                        bv_id = video.get('bv_id', '未知')
                        self.current_title = title
                        self._log(f'开始处理视频: {title}（BV: {bv_id}）')
                        self._set_progress(processed_up, total_up, processed_videos, total_videos, 0.02)

                        if self._get_pipeline_mode() == "bibigpt":
                            t0 = time.time()
                            self._log('BibiGPT 总结中...')
                            url = video.get("url") or ""
                            if url and not str(url).startswith("http") and bv_id:
                                url = f"https://www.bilibili.com/video/{bv_id}"
                            if not url and bv_id:
                                url = f"https://www.bilibili.com/video/{bv_id}"

                            def _bibigpt_progress(elapsed):
                                stage = 0.02 + 0.93 * min(1.0, float(elapsed) / 900.0)
                                self._set_progress(processed_up, total_up, processed_videos, total_videos, stage)

                            try:
                                markdown_content, bibigpt_sec = self._summarize_with_bibigpt(url, video, _bibigpt_progress, max_wait_sec=1800.0)
                            except Exception as e:
                                self._log(f'BibiGPT 总结失败，已跳过: {e}')
                                self._add_history(up_name, title, '失败', task_id=task_id, file_path=None, detail=f'BibiGPT 总结失败: {e}', duration_sec=int(time.time() - t0), llm_sec=int(time.time() - t0))
                                continue

                            self._log(f'BibiGPT 总结完成（耗时 {int(time.time() - t0)}s）')
                            self._set_progress(processed_up, total_up, processed_videos, total_videos, 0.95)

                            saved_relpath = self._save_markdown(video, markdown_content, up_name, task_id=task_id)
                            if saved_relpath:
                                self._add_history(up_name, title, '成功', task_id=task_id, file_path=saved_relpath, detail='BibiGPT 处理完成', duration_sec=bibigpt_sec, llm_sec=bibigpt_sec)
                                self._log(f'处理成功: {video["title"]}')
                            else:
                                self._add_history(up_name, title, '失败', task_id=task_id, file_path=None, detail='保存文件失败', duration_sec=bibigpt_sec, llm_sec=bibigpt_sec)
                                self._log(f'处理失败: {video["title"]}')
                            continue

                        # 下载音频
                        t0 = time.time()
                        self._log('下载音频中...')
                        last_hook_ts = 0.0
                        def _dl_hook(p):
                            nonlocal last_hook_ts
                            now = time.time()
                            if now - last_hook_ts < 0.4:
                                return
                            last_hook_ts = now
                            try:
                                percent = float(p.get("percent") or 0.0)
                            except Exception:
                                percent = 0.0
                            stage = 0.02 + (0.10 * max(0.0, min(100.0, percent)) / 100.0)
                            self._set_progress(processed_up, total_up, processed_videos, total_videos, stage)

                        try:
                            audio_path = self.downloader.download_audio(video.get('url'), video.get('bv_id'), progress_callback=_dl_hook)
                        except Exception as e:
                            self._log(f'下载音频失败，已跳过: {e}')
                            self._add_history(up_name, title, '失败', task_id=task_id, file_path=None, detail=f'下载音频失败: {e}', duration_sec=int(time.time() - t0))
                            continue
                        self._log(f'下载完成（耗时 {int(time.time() - t0)}s）')
                        download_sec = int(time.time() - t0)
                        self._set_progress(processed_up, total_up, processed_videos, total_videos, 0.12)
                        
                        # 转录音频
                        t0 = time.time()
                        self._log('转录中（Whisper）...')
                        done_event = threading.Event()
                        heartbeat_last_log = 0.0
                        asr_progress = {"frac": 0.0, "ts": time.time()}
                        clip_seconds = 30.0 if (task_id and str(task_id).startswith("diagnostics-")) else None

                        def _asr_cb(frac, meta):
                            now = time.time()
                            asr_progress["ts"] = now
                            if isinstance(frac, (int, float)):
                                asr_progress["frac"] = max(asr_progress["frac"], float(frac))

                        def _asr_heartbeat():
                            nonlocal heartbeat_last_log
                            start = time.time()
                            while (not done_event.is_set()) and (not self.stop_event.is_set()):
                                elapsed = time.time() - start
                                frac = float(asr_progress.get("frac") or 0.0)
                                stage = 0.12 + (0.68 * (min(1.0, frac) if frac > 0 else min(1.0, elapsed / 120.0)))
                                self._set_progress(processed_up, total_up, processed_videos, total_videos, stage)
                                if time.time() - heartbeat_last_log > 12:
                                    heartbeat_last_log = time.time()
                                    self._log(f'转录中（Whisper）... 已运行 {int(elapsed)}s')
                                if elapsed > 1800 and float(asr_progress.get("frac") or 0.0) <= 0:
                                    self.stop_event.set()
                                    break
                                time.sleep(1.0)

                        hb_thread = threading.Thread(target=_asr_heartbeat, daemon=True)
                        hb_thread.start()
                        try:
                            transcript = self.transcriber.transcribe(audio_path, progress_callback=_asr_cb, stop_event=self.stop_event, clip_seconds=clip_seconds)
                        except Exception as e:
                            done_event.set()
                            try:
                                hb_thread.join(timeout=2)
                            except Exception:
                                pass
                            self._log(f'转录失败，已跳过: {e}')
                            self.downloader.cleanup(audio_path)
                            self._add_history(up_name, title, '失败', task_id=task_id, file_path=None, detail=f'转录失败: {e}', duration_sec=download_sec + int(time.time() - t0), download_sec=download_sec, asr_sec=int(time.time() - t0))
                            continue
                        done_event.set()
                        try:
                            hb_thread.join(timeout=2)
                        except Exception:
                            pass
                        self._log(f'转录完成（耗时 {int(time.time() - t0)}s）')
                        asr_sec = int(time.time() - t0)
                        self._set_progress(processed_up, total_up, processed_videos, total_videos, 0.80)
                        
                        # AI整理
                        t0 = time.time()
                        self._log('AI 整理中（LLM）...')
                        markdown_content = self.llm_processor.process_transcript(transcript, video)
                        if not markdown_content:
                            self._log('AI 整理失败，已跳过')
                            self.downloader.cleanup(audio_path)
                            self._add_history(up_name, title, '失败', task_id=task_id, file_path=None, detail='AI 整理失败', duration_sec=download_sec + asr_sec + int(time.time() - t0), download_sec=download_sec, asr_sec=asr_sec, llm_sec=int(time.time() - t0))
                            continue
                        self._log(f'AI 整理完成（耗时 {int(time.time() - t0)}s）')
                        llm_sec = int(time.time() - t0)
                        self._set_progress(processed_up, total_up, processed_videos, total_videos, 0.95)
                        
                        # 保存Markdown
                        saved_relpath = self._save_markdown(video, markdown_content, up_name, task_id=task_id)
                        if saved_relpath:
                            # 记录历史
                            self._add_history(up_name, title, '成功', task_id=task_id, file_path=saved_relpath, detail='处理完成', duration_sec=download_sec + asr_sec + llm_sec, download_sec=download_sec, asr_sec=asr_sec, llm_sec=llm_sec)
                            self._log(f'处理成功: {video["title"]}')
                        else:
                            self._add_history(up_name, title, '失败', task_id=task_id, file_path=None, detail='保存文件失败', duration_sec=download_sec + asr_sec + llm_sec, download_sec=download_sec, asr_sec=asr_sec, llm_sec=llm_sec)
                            self._log(f'处理失败: {video["title"]}')
                        
                        # 清理临时文件
                        self.downloader.cleanup(audio_path)
                        
                    except Exception as e:
                        self._log(f'处理视频出错: {e}')
                        self._add_history(up_name, video.get('title', '未知'), '失败', task_id=task_id, file_path=None, detail=str(e))
                    finally:
                        processed_videos += 1
                        self._set_progress(processed_up, total_up, processed_videos, total_videos, 1.0)
                
                processed_up += 1
                self.progress = int((processed_up / total_up) * 100)
            
            self.status = '空闲'
            self.current_task_id = None
            self.current_up_name = None
            self.current_title = None
            self._log('任务处理完成')
            
        except Exception as e:
            self.status = '错误'
            self._log(f'处理任务出错: {e}')

    def _find_existing_markdown_for_video(self, video: Dict[str, Any], up_name: str) -> str | None:
        try:
            up_output_dir = os.path.join(self.output_dir, up_name)
            if not os.path.exists(up_output_dir):
                return None

            bv_id = video.get('bv_id') or ''
            title = video.get('title', '') or ''
            for file in os.listdir(up_output_dir):
                if not file.endswith('.md'):
                    continue
                if (bv_id and bv_id in file) or (title and title in file):
                    return os.path.join(up_name, file)
        except Exception:
            return None
        return None

    def _process_single_video(self, up_name: str, video: Dict[str, Any], force: bool = False, task_id: str | None = None):
        try:
            self._log('开始处理任务，加载必要的模型...')
            self._load_models()
            if self.status == '错误':
                self._log('模型加载失败，停止处理任务')
                self.status = '空闲'
                self.current_task_id = None
                self.current_up_name = None
                self.current_title = None
                return

            if not force and not self._should_process_video(video, up_name):
                existing = self._find_existing_markdown_for_video(video, up_name)
                if existing:
                    self.last_saved_task_id = task_id
                    self.last_saved_path = existing
                    self.last_saved_name = os.path.basename(existing)
                    self.last_saved_at = int(time.time())
                    self._add_history(up_name, video.get('title', '未知'), '成功', task_id=task_id, file_path=existing, detail='检测到已有文档，已跳过', duration_sec=0)
                    self._log('检测到已有文档，已绑定产物并跳过处理')
                else:
                    self._add_history(up_name, video.get('title', '未知'), '失败', task_id=task_id, file_path=None, detail='检测到已有文档，但未能定位产物文件', duration_sec=0)
                    self._log('检测到已有文档，但未能定位产物文件')
                self.status = '空闲'
                self.current_task_id = None
                self.current_up_name = None
                self.current_title = None
                return

            title = video.get('title', '未知')
            bv_id = video.get('bv_id', '未知')
            self._log(f'开始处理视频: {title}（BV: {bv_id}）')
            self.progress = 2

            t0 = time.time()
            self._log('下载音频中...')
            last_hook_ts = 0.0
            def _dl_hook(p):
                nonlocal last_hook_ts
                now = time.time()
                if now - last_hook_ts < 0.4:
                    return
                last_hook_ts = now
                try:
                    percent = float(p.get("percent") or 0.0)
                except Exception:
                    percent = 0.0
                self.progress = 2 + int(10 * max(0.0, min(100.0, percent)) / 100.0)

            try:
                audio_path = self.downloader.download_audio(video.get('url'), video.get('bv_id'), progress_callback=_dl_hook)
            except Exception as e:
                self._log(f'下载音频失败: {e}')
                self._add_history(up_name, title, '失败', task_id=task_id, file_path=None, detail=f'下载音频失败: {e}', duration_sec=int(time.time() - t0))
                self.status = '空闲'
                self.current_task_id = None
                self.current_up_name = None
                self.current_title = None
                return
            self._log(f'下载完成（耗时 {int(time.time() - t0)}s）')
            download_sec = int(time.time() - t0)
            self.progress = 12

            t0 = time.time()
            self._log('转录中（Whisper）...')
            done_event = threading.Event()
            heartbeat_last_log = 0.0
            asr_progress = {"frac": 0.0, "ts": time.time()}
            clip_seconds = 30.0 if (task_id and str(task_id).startswith("diagnostics-")) else None

            def _asr_cb(frac, meta):
                now = time.time()
                asr_progress["ts"] = now
                if isinstance(frac, (int, float)):
                    asr_progress["frac"] = max(asr_progress["frac"], float(frac))

            def _asr_heartbeat():
                nonlocal heartbeat_last_log
                start = time.time()
                while (not done_event.is_set()) and (not self.stop_event.is_set()):
                    elapsed = time.time() - start
                    frac = float(asr_progress.get("frac") or 0.0)
                    if frac > 0:
                        self.progress = max(self.progress, 12 + int(68 * min(1.0, frac)))
                    else:
                        self.progress = max(self.progress, 12 + int(min(67, elapsed)))
                    if time.time() - heartbeat_last_log > 12:
                        heartbeat_last_log = time.time()
                        self._log(f'转录中（Whisper）... 已运行 {int(elapsed)}s')
                    if elapsed > 1800 and float(asr_progress.get("frac") or 0.0) <= 0:
                        self.stop_event.set()
                        break
                    time.sleep(1.0)

            hb_thread = threading.Thread(target=_asr_heartbeat, daemon=True)
            hb_thread.start()
            try:
                transcript = self.transcriber.transcribe(audio_path, progress_callback=_asr_cb, stop_event=self.stop_event, clip_seconds=clip_seconds)
            except Exception as e:
                done_event.set()
                try:
                    hb_thread.join(timeout=2)
                except Exception:
                    pass
                self._log(f'转录失败: {e}')
                self.downloader.cleanup(audio_path)
                asr_sec = int(time.time() - t0)
                self._add_history(up_name, title, '失败', task_id=task_id, file_path=None, detail=f'转录失败: {e}', duration_sec=download_sec + asr_sec, download_sec=download_sec, asr_sec=asr_sec)
                self.status = '空闲'
                self.current_task_id = None
                self.current_up_name = None
                self.current_title = None
                return
            done_event.set()
            try:
                hb_thread.join(timeout=2)
            except Exception:
                pass
            self._log(f'转录完成（耗时 {int(time.time() - t0)}s）')
            asr_sec = int(time.time() - t0)
            self.progress = 80

            t0 = time.time()
            self._log('AI 整理中（LLM）...')
            markdown_content = self.llm_processor.process_transcript(transcript, video)
            if not markdown_content:
                self._log('AI 整理失败')
                self.downloader.cleanup(audio_path)
                llm_sec = int(time.time() - t0)
                self._add_history(up_name, title, '失败', task_id=task_id, file_path=None, detail='AI 整理失败', duration_sec=download_sec + asr_sec + llm_sec, download_sec=download_sec, asr_sec=asr_sec, llm_sec=llm_sec)
                self.status = '空闲'
                self.current_task_id = None
                self.current_up_name = None
                self.current_title = None
                return
            self._log(f'AI 整理完成（耗时 {int(time.time() - t0)}s）')
            llm_sec = int(time.time() - t0)
            self.progress = 95

            saved_relpath = self._save_markdown(video, markdown_content, up_name, task_id=task_id)
            if saved_relpath:
                self._add_history(up_name, title, '成功', task_id=task_id, file_path=saved_relpath, detail='处理完成', duration_sec=download_sec + asr_sec + llm_sec, download_sec=download_sec, asr_sec=asr_sec, llm_sec=llm_sec)
                self._log('保存完成')
            else:
                self._add_history(up_name, title, '失败', task_id=task_id, file_path=None, detail='保存文件失败', duration_sec=download_sec + asr_sec + llm_sec, download_sec=download_sec, asr_sec=asr_sec, llm_sec=llm_sec)
                self._log('保存失败')
            self.progress = 100

            self.downloader.cleanup(audio_path)
            self.status = '空闲'
            self.current_task_id = None
            self.current_up_name = None
            self.current_title = None
            self._log('任务处理完成')
        except Exception as e:
            self.status = '错误'
            self._log(f'处理任务出错: {e}')
    
    def _should_process_video(self, video, up_name):
        """检查是否需要处理视频"""
        up_output_dir = os.path.join(self.output_dir, up_name)
        if not os.path.exists(up_output_dir):
            os.makedirs(up_output_dir, exist_ok=True)
        
        bv_id = video.get('bv_id')
        title = video.get('title', '')
        
        for file in os.listdir(up_output_dir):
            if file.endswith('.md') and (bv_id in file or title in file):
                return False
        
        return True
    
    def _save_markdown(self, video, content, up_name, task_id: str | None = None):
        """保存Markdown文件"""
        try:
            up_output_dir = os.path.join(self.output_dir, up_name)
            os.makedirs(up_output_dir, exist_ok=True)
            
            upload_date = video.get('upload_date', '')
            title = video.get('title', '')
            
            # 清理文件名
            safe_title = ''.join(c for c in title if c not in '\\/:*?"<>|')
            
            if upload_date:
                # 转换日期格式：YYYYMMDD → YYYY-MM-DD
                if len(upload_date) == 8:
                    date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
                else:
                    date_str = upload_date
                filename = f"[{date_str}] {safe_title}.md"
            else:
                filename = f"{safe_title}.md"
            
            file_path = os.path.join(up_output_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            relpath = os.path.join(up_name, filename)
            self.last_saved_task_id = task_id
            self.last_saved_path = relpath
            self.last_saved_name = filename
            self.last_saved_at = int(time.time())

            return relpath
        except Exception as e:
            self._log(f'保存文件失败: {e}')
            return None
    
    def _add_history(self, up_name, title, status, task_id: str | None = None, file_path: str | None = None, detail: str | None = None, duration_sec: int | None = None, download_sec: int | None = None, asr_sec: int | None = None, llm_sec: int | None = None):
        """添加历史记录"""
        record = {
            'upName': up_name,
            'title': title,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': status,
            'taskId': task_id,
            'filePath': file_path,
            'detail': detail,
            'durationSec': duration_sec,
            'downloadSec': download_sec,
            'asrSec': asr_sec,
            'llmSec': llm_sec,
        }
        self.history.append(record)
        # 只保留最近100条记录
        if len(self.history) > 100:
            self.history = self.history[-100:]
        self.save_history()
    
    def get_up_info(self, url: str) -> Dict:
        """解析UP主信息"""
        try:
            return self.downloader.get_up_info(url)
        except Exception as e:
            self._log(f"解析UP主信息失败: {e}")
            raise e

    def add_monitor_target(self, raw: str) -> Dict[str, Any]:
        info = self.get_up_info(raw)
        uid = str(info.get("uid") or "").strip()
        name = str(info.get("name") or "").strip()
        if not uid or not uid.isdigit():
            raise Exception("解析失败：未获取到有效 UID")
        if not name:
            name = f"UID {uid}"

        up_list: List[Dict[str, str]] = list(self.config.get("up_list") or [])
        existing = None
        for u in up_list:
            if str(u.get("uid") or "").strip() == uid:
                existing = u
                break

        added = False
        if existing is None:
            up_list.append({"name": name, "uid": uid})
            added = True
        else:
            if not str(existing.get("name") or "").strip() and name:
                existing["name"] = name

        self.config["up_list"] = up_list
        self.save_config()
        return {"added": added, "up": {"name": name, "uid": uid}, "upList": up_list}

    def remove_monitor_target(self, uid: str) -> Dict[str, Any]:
        uid = str(uid or "").strip()
        if not uid:
            raise Exception("无效的 UID")
        up_list: List[Dict[str, str]] = list(self.config.get("up_list") or [])
        next_list = [u for u in up_list if str(u.get("uid") or "").strip() != uid]
        removed = len(next_list) != len(up_list)
        self.config["up_list"] = next_list
        self.save_config()
        return {"removed": removed, "upList": next_list}

    def monitor_poll(self, max_per_up: int = 1) -> Dict[str, Any]:
        max_per_up = int(max_per_up or 1)
        if max_per_up <= 0:
            max_per_up = 1
        if max_per_up > 5:
            max_per_up = 5

        now_ts = int(time.time())
        events: List[Dict[str, Any]] = []

        with self._monitor_lock:
            state: Dict[str, Any] = {"lastSeen": {}, "checkedAt": None}
            try:
                if os.path.exists(self.monitor_state_path):
                    with open(self.monitor_state_path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    if isinstance(loaded, dict):
                        state.update(loaded)
            except Exception:
                state = {"lastSeen": {}, "checkedAt": None}

            last_seen: Dict[str, str] = dict(state.get("lastSeen") or {})
            for up in list(self.config.get("up_list") or []):
                uid = str(up.get("uid") or "").strip()
                up_name = str(up.get("name") or "").strip() or f"UID {uid}"
                if not uid:
                    continue
                try:
                    raw_videos = self.downloader.get_video_list(uid) or []
                except Exception:
                    continue

                candidates = []
                for v in raw_videos:
                    bv_id = str(v.get("bv_id") or v.get("id") or "").strip()
                    if not bv_id:
                        continue
                    upload_date = str(v.get("upload_date") or "").strip()
                    url = str(v.get("url") or "").strip()
                    if url and not url.startswith("http"):
                        url = f"https://www.bilibili.com/video/{bv_id}"
                    if not url:
                        url = f"https://www.bilibili.com/video/{bv_id}"
                    candidates.append(
                        {
                            "bvId": bv_id,
                            "title": v.get("title"),
                            "url": url,
                            "uploadDate": upload_date or None,
                            "duration": v.get("duration"),
                        }
                    )

                candidates.sort(key=lambda x: str(x.get("uploadDate") or ""), reverse=True)
                if not candidates:
                    continue

                prev = str(last_seen.get(uid) or "").strip()
                if not prev:
                    last_seen[uid] = candidates[0]["bvId"]
                    continue

                new_items: List[Dict[str, Any]] = []
                for item in candidates:
                    if item["bvId"] == prev:
                        break
                    new_items.append(item)
                    if len(new_items) >= max_per_up:
                        break

                if new_items:
                    last_seen[uid] = new_items[0]["bvId"]
                    events.append({"uid": uid, "name": up_name, "videos": new_items})

            state["lastSeen"] = last_seen
            state["checkedAt"] = now_ts
            try:
                with open(self.monitor_state_path, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

        return {"checkedAt": now_ts, "events": events}

    def get_status(self):
        """获取状态"""
        # 更新GPU状态
        self._update_gpu_status()
        self._update_system_status()
        
        return {
            'status': self.status,
            'progress': self.progress,
            'logs': self.logs,
            'gpuUsage': self.gpu_usage,
            'gpuMemory': self.gpu_memory,
            'cpuUsage': self.cpu_usage,
            'memoryUsage': self.memory_usage,
            'lastSavedTaskId': self.last_saved_task_id,
            'lastSavedPath': self.last_saved_path,
            'lastSavedName': self.last_saved_name,
            'lastSavedAt': self.last_saved_at,
            'currentTaskId': self.current_task_id,
            'currentUpName': self.current_up_name,
            'currentTitle': self.current_title,
        }

    def get_selfcheck(self):
        import shutil
        import inspect

        download_cfg = self.config.get("download", {}) if isinstance(self.config, dict) else {}
        transcribe_cfg = self.config.get("transcribe", {}) if isinstance(self.config, dict) else {}
        llm_cfg = self.config.get("llm", {}) if isinstance(self.config, dict) else {}

        ffmpeg_location = (
            download_cfg.get("ffmpeg_location")
            or download_cfg.get("ffmpegLocation")
            or os.getenv("BILIVOX_FFMPEG_LOCATION")
            or os.getenv("FFMPEG_LOCATION")
            or ""
        )
        ffmpeg_location = str(ffmpeg_location or "").strip()

        ffmpeg_path = None
        ffprobe_path = None
        if ffmpeg_location:
            if os.path.isdir(ffmpeg_location):
                ffmpeg_path = os.path.join(ffmpeg_location, "ffmpeg.exe")
                ffprobe_path = os.path.join(ffmpeg_location, "ffprobe.exe")
            elif os.path.isfile(ffmpeg_location):
                ffmpeg_path = ffmpeg_location
                ffprobe_path = os.path.join(os.path.dirname(ffmpeg_location), "ffprobe.exe")

        ffmpeg_resolved = ffmpeg_path if ffmpeg_path and os.path.exists(ffmpeg_path) else shutil.which("ffmpeg")
        ffprobe_resolved = ffprobe_path if ffprobe_path and os.path.exists(ffprobe_path) else shutil.which("ffprobe")

        cookiefile = str(download_cfg.get("cookiefile") or "").strip()
        cookies_from_browser = str(download_cfg.get("cookies_from_browser") or "").strip()

        llm_enabled = bool(llm_cfg.get("enabled", True))
        openai_key_present = bool((os.getenv("OPENAI_API_KEY") or "").strip())
        openai_base_url = (os.getenv("OPENAI_BASE_URL") or "").strip()
        model_name = (os.getenv("MODEL_NAME") or "").strip()

        fw_version = None
        transcribe_sig = None
        vad_sig = None
        try:
            import faster_whisper
            from faster_whisper import WhisperModel
            fw_version = getattr(faster_whisper, "__version__", None)
            transcribe_sig = str(inspect.signature(WhisperModel.transcribe))
            try:
                from faster_whisper.vad import VadOptions
                vad_sig = str(inspect.signature(VadOptions))
            except Exception:
                vad_sig = None
        except Exception:
            fw_version = None

        try:
            import yt_dlp
            ydl_version = getattr(yt_dlp, "__version__", None)
            if not ydl_version:
                try:
                    from yt_dlp import version as _yv
                    ydl_version = getattr(_yv, "__version__", None) or getattr(_yv, "release_git_head", None)
                except Exception:
                    ydl_version = None
        except Exception:
            ydl_version = None

        return {
            "download": {
                "ffmpegLocation": ffmpeg_location,
                "ffmpeg": {"found": bool(ffmpeg_resolved), "path": ffmpeg_resolved},
                "ffprobe": {"found": bool(ffprobe_resolved), "path": ffprobe_resolved},
                "cookiefile": {"value": cookiefile, "exists": bool(cookiefile and os.path.isfile(cookiefile))},
                "cookiesFromBrowser": cookies_from_browser,
                "ytDlpVersion": ydl_version,
            },
            "transcribe": {
                "modelName": transcribe_cfg.get("model_name"),
                "device": transcribe_cfg.get("device"),
                "computeType": transcribe_cfg.get("compute_type"),
                "batchSize": transcribe_cfg.get("batch_size"),
                "fasterWhisperVersion": fw_version,
                "transcribeSignature": transcribe_sig,
                "vadOptionsSignature": vad_sig,
            },
            "llm": {
                "enabled": llm_enabled,
                "openaiKeyPresent": openai_key_present,
                "openaiBaseUrl": openai_base_url,
                "modelName": model_name,
            },
            "runtime": {
                "python": sys.version.split()[0],
                "cwd": os.getcwd(),
                "repoRoot": self.repo_root,
            },
        }

    def start_diagnostics(self, uid: str | None = None, up_name: str | None = None, force: bool = True):
        if self.status == '运行中':
            raise Exception('系统正忙：已有任务在运行')

        selected_uid = str(uid or "").strip()
        selected_up_name = str(up_name or "").strip()
        if not selected_uid:
            up_list = self.config.get("up_list", []) if isinstance(self.config, dict) else []
            if not up_list:
                raise Exception("未配置 UP 列表：请先在配置中心添加一个 UP")
            for item in up_list:
                item = item or {}
                candidate_uid = str(item.get("uid") or "").strip()
                if not candidate_uid:
                    continue
                try:
                    raw = self.downloader.get_video_list(candidate_uid)
                except Exception:
                    continue
                if raw:
                    selected_uid = candidate_uid
                    selected_up_name = str(item.get("name") or "").strip()
                    break
        if not selected_uid:
            raise Exception("无效的 UID")

        if not selected_up_name:
            selected_up_name = f"UID_{selected_uid}"

        raw = self.downloader.get_video_list(selected_uid)
        if not raw:
            raise Exception("获取视频列表失败：请检查 UID / Cookie 配置 / 网络")

        video = raw[0]
        bv_id = video.get("bv_id") or video.get("id") or ""
        title = video.get("title") or bv_id or "未知"
        url = video.get("url") or ""
        if url and not str(url).startswith("http") and bv_id:
            url = f"https://www.bilibili.com/video/{bv_id}"
        if not url and bv_id:
            url = f"https://www.bilibili.com/video/{bv_id}"

        import uuid
        task_id = f"diagnostics-{uuid.uuid4().hex[:12]}"
        self.last_diagnostics_task_id = task_id

        payload_video = {
            "bv_id": bv_id,
            "title": title,
            "url": url,
            "upload_date": video.get("upload_date"),
            "duration": video.get("duration"),
        }
        self.start_processing_for_video(selected_up_name, payload_video, force=bool(force), task_id=task_id)

        return {
            "taskId": task_id,
            "uid": selected_uid,
            "upName": selected_up_name,
            "bvId": bv_id,
            "title": title,
            "url": url,
        }

    def get_diagnostics_report(self, task_id: str | None = None):
        tid = str(task_id or "").strip()
        if not tid:
            tid = str(self.last_diagnostics_task_id or "").strip()
        if not tid:
            raise Exception("缺少 taskId")

        record = None
        for r in reversed(self.history or []):
            if r.get("taskId") == tid:
                record = r
                break

        running = self.status == "运行中" and self.current_task_id == tid
        done = bool(record) and (not running)

        return {
            "taskId": tid,
            "running": running,
            "done": done,
            "record": record,
            "status": self.status,
            "progress": self.progress,
        }

    def delete_markdown(self, path: str):
        requested = self._resolve_output_markdown_path(path)
        os.remove(requested)

    def get_output_for_task(self, task_id: str):
        if not task_id or not isinstance(task_id, str):
            raise Exception('无效的任务ID')
        for record in reversed(self.history):
            if record.get('taskId') != task_id:
                continue
            file_path = record.get('filePath')
            if file_path:
                requested = self._resolve_output_markdown_path(file_path)
                return {
                    "path": file_path,
                    "name": os.path.basename(requested),
                }
        raise Exception('未找到该任务的产物文件')

    def _log(self, message: str):
        ts = datetime.now().strftime('%H:%M:%S')
        self.logs.append(f'[{ts}] {message}')
        if len(self.logs) > 800:
            self.logs = self.logs[-800:]

    def _set_progress(self, processed_up: int, total_up: int, processed_videos: int, total_videos: int, stage: float):
        try:
            if total_up <= 0:
                self.progress = 0
                return
            stage = max(0.0, min(1.0, float(stage)))
            up_base = processed_up / total_up
            if total_videos <= 0:
                self.progress = int(up_base * 100)
                return
            per_video = (processed_videos + stage) / total_videos
            overall = up_base + (per_video / total_up)
            self.progress = int(max(0.0, min(1.0, overall)) * 100)
        except Exception:
            return

    def _update_system_status(self):
        try:
            import psutil
            self.cpu_usage = int(psutil.cpu_percent(interval=None))
            self.memory_usage = int(psutil.virtual_memory().percent)
        except Exception:
            self.cpu_usage = 0
            self.memory_usage = 0
            if not self._psutil_missing_logged:
                self._psutil_missing_logged = True
                self._log('系统资源采样不可用：缺少 psutil（可忽略，不影响转录/生成）')
    
    def _update_gpu_status(self):
        """更新GPU状态"""
        try:
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                total_mem = 0
                total_used = 0
                
                # 累加所有可见GPU的显存
                for i in range(device_count):
                    props = torch.cuda.get_device_properties(i)
                    allocated = torch.cuda.memory_allocated(i)
                    reserved = torch.cuda.memory_reserved(i)
                    
                    total_mem += props.total_memory
                    total_used += reserved  # 使用 reserved 而不是 allocated，更能反映实际占用（包括缓存）
                
                if total_mem > 0:
                    self.gpu_memory = int(total_used / 1024 / 1024)
                    self.gpu_usage = int((total_used / total_mem) * 100)
                else:
                    self.gpu_usage = 0
                    self.gpu_memory = 0
            else:
                self.gpu_usage = 0
                self.gpu_memory = 0
        except Exception:
            self.gpu_usage = 0
            self.gpu_memory = 0
    
    def get_history(self):
        """获取历史记录"""
        return self.history
    
    def get_files(self):
        """获取文件列表"""
        up_list = []
        files = []
        
        if not os.path.exists(self.output_dir):
            return {'upList': up_list, 'files': files}
        
        # 获取UP主列表
        for item in os.listdir(self.output_dir):
            item_path = os.path.join(self.output_dir, item)
            if os.path.isdir(item_path):
                up_list.append(item)
                
                # 获取该UP主的文件
                for file in os.listdir(item_path):
                    if file.endswith('.md'):
                        file_path = os.path.join(item, file)
                        absolute_path = os.path.join(item_path, file)
                        try:
                            modified_ts = int(os.path.getmtime(absolute_path))
                        except Exception:
                            modified_ts = None
                        # 提取日期
                        date = '未知'
                        if file.startswith('['):
                            date_part = file.split(']')[0][1:]
                            if len(date_part) == 10:
                                date = date_part
                        
                        files.append({
                            'up': item,
                            'name': file,
                            'path': file_path,
                            'date': date,
                            'modifiedTs': modified_ts,
                        })
        
        return {'upList': up_list, 'files': files}
    
    def get_file_content(self, path):
        """获取文件内容"""
        requested = self._resolve_output_markdown_path(path)
        with open(requested, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content

    def get_file_path_for_download(self, path):
        requested = self._resolve_output_markdown_path(path)
        filename = os.path.basename(requested)
        return requested, filename

    def _resolve_output_markdown_path(self, path):
        if not path or not isinstance(path, str):
            raise Exception('无效的文件路径')

        if len(path) > 512:
            raise Exception('文件路径过长')

        output_root = os.path.abspath(self.output_dir)
        requested = os.path.abspath(os.path.join(output_root, path))

        if not requested.startswith(output_root + os.sep) and requested != output_root:
            raise Exception('非法路径')

        if not requested.endswith('.md'):
            raise Exception('不支持的文件类型')

        if not os.path.exists(requested):
            raise Exception('文件不存在')

        return requested

    def batch_download_files(self, file_paths: List[str]):
        """批量下载文件，返回 zip 流"""
        import io
        import zipfile
        from datetime import datetime

        if not file_paths:
            raise Exception("未选择任何文件")

        # 验证所有文件路径
        valid_files = []
        for path in file_paths:
            try:
                abs_path = self._resolve_output_markdown_path(path)
                valid_files.append((abs_path, path)) # (绝对路径, 相对路径/归档内路径)
            except Exception:
                continue

        if not valid_files:
            raise Exception("没有可下载的有效文件")

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for abs_path, rel_path in valid_files:
                # 使用路径中的文件名，或者保留相对目录结构
                # 这里保留相对目录结构（例如 up_name/file.md）
                zip_file.write(abs_path, rel_path)

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bilivox_batch_{timestamp}.zip"
        
        return zip_buffer, filename
