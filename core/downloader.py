import os
import json
import re
import yt_dlp
from typing import List, Dict, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class BiliDownloader:
    """Bilibili 视频下载器"""
    
    def __init__(self, config: Dict):
        """
        初始化下载器
        
        Args:
            config: 配置字典，包含下载相关设置
        """
        self.temp_dir = config['download']['temp_dir']
        self.headers = config['download']['headers']
        self.audio_format = config['download']['audio_format']
        self.cookiefile = (
            config.get('download', {}).get('cookiefile')
            or config.get('download', {}).get('cookies_file')
            or config.get('download', {}).get('cookiesFile')
        )
        self.cookies_from_browser = (
            config.get('download', {}).get('cookies_from_browser')
            or config.get('download', {}).get('cookiesFromBrowser')
        )
        self.ffmpeg_location = (
            config.get('download', {}).get('ffmpeg_location')
            or config.get('download', {}).get('ffmpegLocation')
            or os.getenv("BILIVOX_FFMPEG_LOCATION")
            or os.getenv("FFMPEG_LOCATION")
        )
        
        # 确保临时目录存在
        os.makedirs(self.temp_dir, exist_ok=True)

    def _strip_ansi(self, text: str) -> str:
        return re.sub(r"\x1b\\[[0-9;]*m", "", str(text or ""))

    def _apply_ffmpeg_options(self, ydl_opts: Dict):
        loc = str(self.ffmpeg_location or "").strip()
        if not loc:
            return
        if os.path.exists(loc):
            ydl_opts["ffmpeg_location"] = loc
            return
        raise ValueError(f"FFmpeg 路径不存在：{loc}")

    def _apply_cookie_options(self, ydl_opts: Dict, cookies_from_browser: Optional[str] = None):
        cookiefile = str(self.cookiefile or "").strip()
        if cookiefile:
            if not os.path.exists(cookiefile):
                raise ValueError(f"Cookie 文件不存在：{cookiefile}")
            if not os.path.isfile(cookiefile):
                raise ValueError(f"Cookie 文件不是有效文件：{cookiefile}")
            if not os.access(cookiefile, os.R_OK):
                raise ValueError(f"无权限读取 Cookie 文件：{cookiefile}")
            ydl_opts["cookiefile"] = cookiefile
            return

        source = cookies_from_browser
        if source is None:
            v = self.cookies_from_browser
            if isinstance(v, bool):
                source = "chrome" if v else None
            elif isinstance(v, str) and v.strip():
                source = v.strip()
            else:
                source = None

        if source:
            ydl_opts["cookiesfrombrowser"] = (source,)

    def _should_try_browser_cookies(self, err: Exception) -> bool:
        msg = str(err or "")
        return "352" in msg or "rejected" in msg.lower() or "Request is rejected" in msg

    def _is_cookie_load_error(self, err: Exception) -> bool:
        msg = str(err or "")
        low = msg.lower()
        if "failed to load cookies" in low:
            return True
        if "cookiesfrombrowser" in low:
            return True
        if "user data" in msg or "User Data" in msg:
            return True
        if "cookie" in low and ("chromium" in low or "edge" in low or "chrome" in low):
            return True
        return False

    def _extract_info_with_retry(self, url: str, ydl_opts: Dict) -> Dict:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            if (not str(self.cookiefile or "").strip()) and self._should_try_browser_cookies(e) and "cookiesfrombrowser" not in ydl_opts:
                for browser in ("chrome", "edge"):
                    retry_opts = dict(ydl_opts)
                    self._apply_cookie_options(retry_opts, cookies_from_browser=browser)
                    try:
                        with yt_dlp.YoutubeDL(retry_opts) as ydl:
                            return ydl.extract_info(url, download=False)
                    except Exception:
                        continue
            raise

    def _extract_uid(self, raw: str) -> str:
        text = str(raw or "").strip()
        if not text:
            raise ValueError("输入为空")
        if re.fullmatch(r"\d+", text):
            return text

        normalized = text
        if not re.match(r"^https?://", normalized, re.IGNORECASE):
            normalized = "https://" + normalized

        parsed = urlparse(normalized)
        if parsed.netloc.lower().endswith("b23.tv"):
            try:
                req = Request(normalized, headers=self.headers)
                with urlopen(req, timeout=10) as resp:
                    normalized = resp.geturl()
            except Exception:
                pass

        patterns = [
            r"^https?://space\.bilibili\.com/(\d+)",
            r"^https?://www\.bilibili\.com/\d+",
            r"^https?://m\.bilibili\.com/space/(\d+)",
        ]
        for p in patterns:
            m = re.search(p, normalized, flags=re.IGNORECASE)
            if m and m.groups():
                uid = m.group(1)
                if uid:
                    return uid

        parsed2 = urlparse(normalized)
        host = (parsed2.netloc or "").lower()
        path = parsed2.path or ""
        if host.endswith("space.bilibili.com"):
            m = re.match(r"^/(\d+)(?:/|$)", path)
            if m:
                return m.group(1)
        if host.endswith("m.bilibili.com"):
            m = re.match(r"^/space/(\d+)(?:/|$)", path)
            if m:
                return m.group(1)

        raise ValueError("无法从链接中提取 UID")

    def _normalize_video_url(self, video_url: str | None, bv_id: str | None) -> str:
        raw = str(video_url or "").strip()
        bvid = str(bv_id or "").strip()
        if raw and re.match(r"^https?://", raw, re.IGNORECASE):
            return raw
        if raw and re.fullmatch(r"BV[0-9A-Za-z]+", raw):
            return f"https://www.bilibili.com/video/{raw}"
        if bvid and re.fullmatch(r"BV[0-9A-Za-z]+", bvid):
            return f"https://www.bilibili.com/video/{bvid}"
        if raw and raw.startswith("/video/") and bvid:
            return f"https://www.bilibili.com{raw}"
        if raw and raw:
            return raw
        raise ValueError("视频 URL 为空，无法下载")

    def _fetch_bilibili_acc_info(self, uid: str) -> Dict:
        api = f"https://api.bilibili.com/x/space/acc/info?mid={uid}&jsonp=jsonp"
        req = Request(api, headers=self.headers)
        with urlopen(req, timeout=10) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
        data = json.loads(payload or "{}")
        if not isinstance(data, dict) or data.get("code") != 0:
            raise ValueError("B 站接口返回异常")
        info = data.get("data") or {}
        return {
            "name": info.get("name"),
            "uid": uid,
            "face": info.get("face"),
            "desc": info.get("sign"),
        }
    
    def get_up_info(self, url: str) -> Dict:
        """
        获取UP主信息
        
        Args:
            url: UP主个人主页URL
            
        Returns:
            UP主信息字典
        """
        uid = self._extract_uid(url)
        space_url = f"https://space.bilibili.com/{uid}/video"
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'http_headers': self.headers,
            'playlist_items': '1',  # 只需要获取UP主基本信息，不需要所有视频
        }
        self._apply_cookie_options(ydl_opts)
        
        try:
            info = self._extract_info_with_retry(space_url, ydl_opts)

            first_entry = info.get('entries', [{}])[0] if info.get('entries') else {}

            name = info.get('uploader') or info.get('channel') or info.get('title')
            face = info.get('thumbnails', [{}])[-1].get('url') if info.get('thumbnails') else None
            desc = info.get('description')
            follower = info.get('subscriber_count')

            if not name:
                try:
                    api_info = self._fetch_bilibili_acc_info(uid)
                    name = api_info.get("name") or name
                    face = api_info.get("face") or face
                    desc = api_info.get("desc") or desc
                except Exception:
                    pass

            if not name:
                name = f"UID {uid}"

            return {
                'name': name,
                'uid': uid,
                'face': face,
                'follower': follower,
                'desc': desc,
                'latest_video': {
                    'title': first_entry.get('title'),
                    'pic': first_entry.get('thumbnails', [{}])[-1].get('url') if first_entry.get('thumbnails') else None,
                    'created': first_entry.get('upload_date')
                } if first_entry else None
            }
        except Exception:
            return {
                "name": f"UID {uid}",
                "uid": uid,
                "face": None,
                "follower": None,
                "desc": None,
                "latest_video": None,
            }

    def get_video_list(self, uid: str) -> List[Dict]:
        """
        获取UP主的视频列表
        
        Args:
            uid: UP主的UID
            
        Returns:
            视频列表，每个元素包含视频信息
        """
        # 构建Bilibili用户空间URL
        url = f'https://space.bilibili.com/{uid}/video'
        
        # yt-dlp 配置
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'http_headers': self.headers,
        }
        self._apply_cookie_options(ydl_opts)
        
        videos = []
        
        try:
            info = self._extract_info_with_retry(url, ydl_opts)
        except Exception as e:
            msg = str(e or '')
            if self._is_cookie_load_error(e):
                if str(self.cookiefile or "").strip():
                    raise ValueError('获取视频列表失败：无法加载 cookies.txt。请确认文件格式为 Netscape cookies.txt，且文件未损坏；或清空 cookiefile 改用浏览器来源。')
                raise ValueError('获取视频列表失败：无法从浏览器读取 Cookie。请先完全关闭 Chrome/Edge（含后台进程）后重试，或改用导出的 cookies.txt 并配置 download.cookiefile。')
            if '352' in msg:
                raise ValueError('获取视频列表失败：B 站请求被拒绝（352）。可在 config.yaml 配置 download.cookies_from_browser: chrome/edge 或提供 download.cookiefile。')
            raise ValueError(f'获取视频列表失败：{msg}')

        if 'entries' in info:
            for entry in info['entries']:
                if entry.get('__class__') == 'YoutubeDL' and 'entries' in entry:
                    for sub_entry in entry['entries']:
                        bv_id = sub_entry.get('id')
                        url = sub_entry.get('url')
                        if url and not str(url).startswith('http') and bv_id:
                            url = f'https://www.bilibili.com/video/{bv_id}'
                        if not url and bv_id:
                            url = f'https://www.bilibili.com/video/{bv_id}'
                        videos.append({
                            'bv_id': bv_id,
                            'title': sub_entry.get('title') or bv_id,
                            'url': url,
                            'upload_date': sub_entry.get('upload_date'),
                            'duration': sub_entry.get('duration'),
                            'uploader': sub_entry.get('uploader'),
                            'uid': sub_entry.get('uploader_id') or sub_entry.get('channel_id'),
                        })
                else:
                    bv_id = entry.get('id')
                    url = entry.get('url')
                    if url and not str(url).startswith('http') and bv_id:
                        url = f'https://www.bilibili.com/video/{bv_id}'
                    if not url and bv_id:
                        url = f'https://www.bilibili.com/video/{bv_id}'
                    videos.append({
                        'bv_id': bv_id,
                        'title': entry.get('title') or bv_id,
                        'url': url,
                        'upload_date': entry.get('upload_date'),
                        'duration': entry.get('duration'),
                        'uploader': entry.get('uploader'),
                        'uid': entry.get('uploader_id') or entry.get('channel_id'),
                    })
        
        return videos
    
    def download_audio(self, video_url: str, bv_id: str, progress_callback=None) -> Optional[str]:
        """
        下载视频的音频部分
        
        Args:
            video_url: 视频URL
            bv_id: BV号
            
        Returns:
            下载的音频文件路径，失败返回None
        """
        normalized_url = self._normalize_video_url(video_url, bv_id)

        # 构建输出文件名
        output_path = os.path.join(self.temp_dir, f"{bv_id}.{self.audio_format}")
        
        # yt-dlp 配置
        class _YdlLogger:
            def __init__(self):
                self.errors: list[str] = []
            def debug(self, msg):
                return
            def warning(self, msg):
                return
            def error(self, msg):
                try:
                    self.errors.append(str(msg))
                except Exception:
                    pass

        logger = _YdlLogger()
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.audio_format,
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self.temp_dir, f"{bv_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
            'http_headers': self.headers,
            'logger': logger,
        }
        self._apply_cookie_options(ydl_opts)
        self._apply_ffmpeg_options(ydl_opts)

        if progress_callback:
            def _hook(d):
                try:
                    if d.get('status') not in ('downloading', 'finished'):
                        return
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes') or 0
                    eta = d.get('eta')
                    if total and total > 0:
                        percent = max(0.0, min(100.0, (downloaded / total) * 100.0))
                    elif d.get('_percent_str'):
                        s = str(d.get('_percent_str')).strip().rstrip('%')
                        percent = float(s) if s else 0.0
                    else:
                        percent = 0.0
                    progress_callback({
                        "status": d.get('status'),
                        "percent": percent,
                        "downloaded_bytes": downloaded,
                        "total_bytes": total,
                        "eta": eta,
                    })
                except Exception:
                    return

            ydl_opts['progress_hooks'] = [_hook]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([normalized_url])
            
            # 检查文件是否存在
            if os.path.exists(output_path):
                return output_path
            else:
                # 可能扩展名不同，查找实际文件
                for file in os.listdir(self.temp_dir):
                    if file.startswith(bv_id):
                        return os.path.join(self.temp_dir, file)
        except Exception as e:
            detail = self._strip_ansi(str(e or "").strip())
            extra = ""
            try:
                if getattr(logger, "errors", None):
                    extra = " | " + " ; ".join([self._strip_ansi(x) for x in logger.errors[-3:]])
            except Exception:
                extra = ""
            combined = f"{detail}{extra}".strip()
            if "ffprobe and ffmpeg not found" in combined.lower():
                hint = "未检测到 FFmpeg。请安装 FFmpeg 并加入 PATH，或在配置里填写 download.ffmpeg_location（指向 ffmpeg.exe 或其所在目录）。"
                raise ValueError(f"下载音频失败: {combined} | {hint}") from e
            raise ValueError(f"下载音频失败: {combined}") from e
        
        raise ValueError("下载音频失败：未生成输出文件")

    def get_video_meta(self, bv_id: str) -> Dict:
        bvid = str(bv_id or "").strip()
        if not bvid:
            raise ValueError("无效的 BV 号")
        # 改用 view/detail 接口以获取更完整的元数据（包含 tags）
        api = f"https://api.bilibili.com/x/web-interface/view/detail?bvid={bvid}"
        req = Request(api, headers=self.headers)
        with urlopen(req, timeout=10) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
        data = json.loads(payload or "{}")
        if not isinstance(data, dict) or data.get("code") != 0:
            raise ValueError("B 站接口返回异常")
        
        # detail 接口的数据结构：data -> View, Card, Tags, Reply, Related
        detail = data.get("data") or {}
        info = detail.get("View") or {}
        tags_info = detail.get("Tags") or []
        
        duration = info.get("duration")
        owner = info.get("owner") or {}
        
        # 处理时间戳
        upload_date = None
        pubdate = info.get("pubdate")
        if pubdate:
            try:
                import time
                upload_date = time.strftime("%Y%m%d", time.localtime(pubdate))
            except Exception:
                pass

        # 提取标签
        tags = []
        if isinstance(tags_info, list):
            for t in tags_info:
                name = t.get("tag_name")
                if name:
                    tags.append(name)

        return {
            "bvId": bvid,
            "title": info.get("title"),
            "duration": duration,
            "owner": owner.get("name"),
            "owner_name": owner.get("name"),
            "uploader": owner.get("name"),
            "uid": str(owner.get("mid") or ""),
            "owner_id": str(owner.get("mid") or ""),
            "mid": str(owner.get("mid") or ""),
            "upload_date": upload_date,
            "tags": tags, # 新增 tags 字段
        }
    
    def cleanup(self, file_path: str):
        """
        清理临时文件
        
        Args:
            file_path: 要删除的文件路径
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"清理文件失败: {e}")
