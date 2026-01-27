import os
import yaml
import time
import re
from typing import List, Dict
from tqdm import tqdm
from colorama import init, Fore, Back, Style
from core.downloader import BiliDownloader
from core.transcriber import BiliTranscriber
from core.llm_processor import BiliLLMProcessor

# 初始化colorama
init(autoreset=True)


class BiliVox:
    """Bilibili UP主视频资料库构建工具"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        初始化BiliVox
        
        Args:
            config_path: 配置文件路径
        """
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 初始化各个模块
        self.downloader = BiliDownloader(self.config)
        self.transcriber = BiliTranscriber(self.config)
        self.llm_processor = BiliLLMProcessor(self.config)
        
        # 输出目录
        self.output_dir = self.config['download']['output_dir']
        os.makedirs(self.output_dir, exist_ok=True)
    
    def run(self):
        """运行主程序"""
        print(f"{Fore.GREEN}=== BiliVox 视频资料库构建工具 ==={Style.RESET_ALL}")
        print(f"{Fore.CYAN}正在处理 UP 主列表...{Style.RESET_ALL}")
        
        up_list = self.config['up_list']
        
        for up in up_list:
            up_name = up['name']
            up_uid = up['uid']
            
            print(f"\n{Fore.YELLOW}=== 处理 UP 主: {up_name} (UID: {up_uid}) ==={Style.RESET_ALL}")
            
            # 创建UP主输出目录
            up_output_dir = os.path.join(self.output_dir, up_name)
            os.makedirs(up_output_dir, exist_ok=True)
            
            # 获取视频列表
            videos = self._get_video_list_with_retry(up_uid)
            if not videos:
                print(f"{Fore.RED}获取视频列表失败，跳过此UP主{Style.RESET_ALL}")
                continue
            
            print(f"{Fore.GREEN}获取到 {len(videos)} 个视频{Style.RESET_ALL}")
            
            # 处理每个视频
            for video in tqdm(videos, desc=f"处理 {up_name} 的视频", unit="个"):
                try:
                    # 检查是否需要处理
                    if self._should_process_video(video, up_output_dir):
                        print(f"\n{Fore.CYAN}处理视频: {video['title']} (BV: {video['bv_id']}){Style.RESET_ALL}")
                        
                        # 下载音频
                        audio_path = self._download_audio_with_retry(video)
                        if not audio_path:
                            print(f"{Fore.RED}下载音频失败，跳过此视频{Style.RESET_ALL}")
                            continue
                        
                        # 转录音频
                        transcript = self.transcriber.transcribe(audio_path)
                        if not transcript:
                            print(f"{Fore.RED}转录失败，跳过此视频{Style.RESET_ALL}")
                            self.downloader.cleanup(audio_path)
                            continue
                        
                        # AI整理
                        markdown_content = self.llm_processor.process_transcript(transcript, video)
                        if not markdown_content:
                            print(f"{Fore.RED}AI整理失败，跳过此视频{Style.RESET_ALL}")
                            self.downloader.cleanup(audio_path)
                            continue
                        
                        # 保存Markdown
                        if self._save_markdown(video, markdown_content, up_output_dir):
                            print(f"{Fore.GREEN}保存成功: {video['title']}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.RED}保存失败，跳过此视频{Style.RESET_ALL}")
                        
                        # 清理临时文件
                        self.downloader.cleanup(audio_path)
                        
                    else:
                        print(f"{Fore.BLUE}跳过已处理的视频: {video['title']}{Style.RESET_ALL}")
                        
                except Exception as e:
                    print(f"{Fore.RED}处理视频时出错: {e}{Style.RESET_ALL}")
                    # 清理临时文件
                    if 'audio_path' in locals():
                        self.downloader.cleanup(audio_path)
                    continue
        
        print(f"\n{Fore.GREEN}=== 所有 UP 主处理完成 ==={Style.RESET_ALL}")
    
    def _get_video_list_with_retry(self, uid: str, max_retries: int = 3) -> List[Dict]:
        """
        带重试机制获取视频列表
        
        Args:
            uid: UP主UID
            max_retries: 最大重试次数
            
        Returns:
            视频列表
        """
        for i in range(max_retries):
            try:
                return self.downloader.get_video_list(uid)
            except Exception as e:
                print(f"{Fore.YELLOW}获取视频列表失败 (尝试 {i+1}/{max_retries}): {e}{Style.RESET_ALL}")
                if i < max_retries - 1:
                    time.sleep(2)
                else:
                    return []
    
    def _download_audio_with_retry(self, video: Dict, max_retries: int = 3) -> str:
        """
        带重试机制下载音频
        
        Args:
            video: 视频信息
            max_retries: 最大重试次数
            
        Returns:
            音频文件路径
        """
        for i in range(max_retries):
            try:
                return self.downloader.download_audio(video['url'], video['bv_id'])
            except Exception as e:
                print(f"{Fore.YELLOW}下载音频失败 (尝试 {i+1}/{max_retries}): {e}{Style.RESET_ALL}")
                if i < max_retries - 1:
                    time.sleep(2)
                else:
                    return None
    
    def _should_process_video(self, video: Dict, up_output_dir: str) -> bool:
        """
        检查是否需要处理视频
        
        Args:
            video: 视频信息
            up_output_dir: UP主输出目录
            
        Returns:
            是否需要处理
        """
        # 生成可能的文件名
        upload_date = video.get('upload_date', '')
        title = video.get('title', '')
        
        # 清理文件名
        safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
        
        # 检查是否存在类似的文件
        for file in os.listdir(up_output_dir):
            if file.endswith('.md'):
                # 检查文件名是否包含BV号或标题关键字
                if video['bv_id'] in file or any(keyword in file for keyword in safe_title.split()[:5]):
                    return False
        
        return True
    
    def _save_markdown(self, video: Dict, content: str, up_output_dir: str) -> bool:
        """
        保存Markdown文件
        
        Args:
            video: 视频信息
            content: Markdown内容
            up_output_dir: UP主输出目录
            
        Returns:
            是否保存成功
        """
        try:
            # 生成文件名
            upload_date = video.get('upload_date', '')
            title = video.get('title', '')
            
            # 清理文件名
            safe_title = re.sub(r'[\\/:*?"<>|]', '_', title)
            
            # 构建文件名
            if upload_date:
                # 转换日期格式：YYYYMMDD → YYYY-MM-DD
                if len(upload_date) == 8:
                    date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
                else:
                    date_str = upload_date
                filename = f"[{date_str}] {safe_title}.md"
            else:
                filename = f"{safe_title}.md"
            
            # 保存文件
            file_path = os.path.join(up_output_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}保存Markdown失败: {e}{Style.RESET_ALL}")
            return False


if __name__ == "__main__":
    try:
        bili_vox = BiliVox()
        bili_vox.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}用户中断程序{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}程序运行失败: {e}{Style.RESET_ALL}")
