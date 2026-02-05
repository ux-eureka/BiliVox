from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
from core.bilivox_manager import BiliVoxManager
from fastapi import Query
from api.auth import require_api_key
from fastapi.responses import FileResponse as FastAPIFileResponse, StreamingResponse
from pydantic import Field
from pydantic import BaseModel as _BaseModel

# 创建路由器
router = APIRouter()

# 全局BiliVox管理器实例
bilivox_manager = None

# 依赖项：获取BiliVox管理器
async def get_bilivox_manager():
    global bilivox_manager
    if bilivox_manager is None:
        bilivox_manager = BiliVoxManager()
    return bilivox_manager

# 配置模型
class UpItem(BaseModel):
    name: str
    uid: str | int

class ConfigModel(BaseModel):
    upList: List[UpItem]
    download: Dict[str, Any]
    transcribe: Dict[str, Any]
    llm: Dict[str, Any]

class MonitorAddRequest(BaseModel):
    input: str = Field(..., description="UP 主主页链接或 UID")

class MonitorPollRequest(BaseModel):
    maxPerUp: int | None = Field(default=1, description="每个 UP 最多返回新稿数（1-5）")

# 状态响应模型
class StatusResponse(BaseModel):
    status: str
    progress: int
    queueSize: int = 0
    logs: List[str]
    gpuUsage: int
    gpuMemory: int
    cpuUsage: int
    memoryUsage: int
    lastSavedTaskId: str | None = None
    lastSavedPath: str | None = None
    lastSavedName: str | None = None
    lastSavedAt: int | None = None
    currentTaskId: str | None = None
    currentUpName: str | None = None
    currentTitle: str | None = None

# 历史记录响应模型
class HistoryResponse(BaseModel):
    upName: str
    title: str | None = None
    timestamp: str
    status: str
    taskId: str | None = None
    filePath: str | None = None
    detail: str | None = None
    durationSec: int | None = None
    downloadSec: int | None = None
    asrSec: int | None = None
    llmSec: int | None = None

class TerminateBatchRequest(_BaseModel):
    taskIds: List[str]

class TaskStatusResponse(_BaseModel):
    taskId: str
    status: str

# 文件响应模型
class FileItem(BaseModel):
    up: str
    name: str
    path: str
    date: str
    bv: Optional[str] = None
    videoName: str
    title: str
    uid: Optional[str] = None
    modifiedTs: Optional[int] = None

# 文件列表响应模型
class FilesListResponse(BaseModel):
    upList: List[str]
    files: List[FileItem]

class StartUpTaskRequest(BaseModel):
    uid: str = Field(..., description="UP 主 UID")
    name: str = Field(..., description="UP 主名称（用于输出目录匹配）")
    url: str | None = Field(default=None, description="可选：UP 主主页 URL（仅用于日志）")
    taskId: str | None = Field(default=None, description="前端任务ID，用于绑定产物与下载")
    force: bool = Field(default=False, description="是否强制重新处理（忽略已存在文档）")
    maxVideos: int | None = Field(default=None, description="限制处理视频数量（为空表示全部）")

class TaskOutputResponse(BaseModel):
    path: str
    name: str

class VideoItem(BaseModel):
    bvId: str
    title: str | None = None
    url: str
    uploadDate: str | None = None
    duration: int | None = None
    uploader: str | None = None

class UpVideosResponse(BaseModel):
    uid: str
    videos: List[VideoItem]

class StartVideoTaskRequest(BaseModel):
    taskId: str
    upName: str
    force: bool = Field(default=False, description="是否强制重新处理")
    video: VideoItem

class DeleteFileRequest(BaseModel):
    path: str

# 获取配置
@router.get("/config")
async def get_config(bilivox: BiliVoxManager = Depends(get_bilivox_manager)):
    return bilivox.get_config()

# 更新配置
@router.post("/config")
async def update_config(
    config: ConfigModel,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    payload = config.model_dump()
    try:
        payload["upList"] = [{"name": u.name, "uid": str(u.uid)} for u in config.upList]
    except Exception:
        pass
    bilivox.update_config(payload)
    return {"message": "配置更新成功"}

@router.post("/monitor/targets")
async def add_monitor_target(
    req: MonitorAddRequest,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        return bilivox.add_monitor_target(req.input)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/monitor/targets/{uid}")
async def remove_monitor_target(
    uid: str,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        return bilivox.remove_monitor_target(uid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/monitor/poll")
async def poll_monitor(
    req: MonitorPollRequest,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        return bilivox.monitor_poll(max_per_up=req.maxPerUp or 1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 开始处理
@router.post("/start")
async def start_processing(
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    bilivox.start_processing()
    return {"message": "开始处理任务"}

@router.post("/task/start")
async def start_up_task(
    req: StartUpTaskRequest,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    up = {"name": req.name, "uid": req.uid}
    try:
        bilivox.start_processing_for_up(up, force=req.force, max_videos=req.maxVideos, task_id=req.taskId)
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"message": "开始处理任务"}

@router.delete("/task/{task_id}/terminate")
async def terminate_task(
    task_id: str,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        result = bilivox.terminate_task(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/task/batch-terminate")
async def batch_terminate(
    req: TerminateBatchRequest,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        result = bilivox.batch_terminate_tasks(req.taskIds or [])
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        result = bilivox.get_task_status(task_id)
        return TaskStatusResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/task/output", response_model=TaskOutputResponse)
async def get_task_output(
    taskId: str,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        data = bilivox.get_output_for_task(taskId)
        return TaskOutputResponse(**data)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/video/start")
async def start_video_task(
    req: StartVideoTaskRequest,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    video = {
        "bv_id": req.video.bvId,
        "title": req.video.title,
        "url": req.video.url,
        "upload_date": req.video.uploadDate,
        "duration": req.video.duration,
        "uploader": req.video.uploader,
    }
    try:
        bilivox.start_processing_for_video(req.upName, video, force=req.force, task_id=req.taskId)
    except Exception as e:
        raise HTTPException(status_code=409, detail=str(e))
    return {"message": "开始处理任务"}

# 停止处理
@router.post("/stop")
async def stop_processing(
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    bilivox.stop_processing()
    return {"message": "停止处理任务"}

# 获取状态
@router.get("/status", response_model=StatusResponse)
async def get_status(bilivox: BiliVoxManager = Depends(get_bilivox_manager)):
    status_data = bilivox.get_status()
    return StatusResponse(**status_data)

@router.get("/selfcheck")
async def selfcheck(bilivox: BiliVoxManager = Depends(get_bilivox_manager)):
    return bilivox.get_selfcheck()

# 获取历史记录
@router.get("/history", response_model=List[HistoryResponse])
async def get_history(bilivox: BiliVoxManager = Depends(get_bilivox_manager)):
    return bilivox.get_history()

# 获取文件列表
@router.get("/files", response_model=FilesListResponse)
async def get_files(bilivox: BiliVoxManager = Depends(get_bilivox_manager)):
    files_data = bilivox.get_files()
    return FilesListResponse(**files_data)

@router.get("/videos", response_model=UpVideosResponse)
async def get_up_videos(uid: str, bilivox: BiliVoxManager = Depends(get_bilivox_manager)):
    try:
        raw = bilivox.downloader.get_video_list(uid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    videos: List[VideoItem] = []
    for v in raw or []:
        bv_id = v.get('bv_id') or v.get('id') or ''
        title = v.get('title')
        url = v.get('url') or ''
        if url and not str(url).startswith('http'):
            if bv_id:
                url = f'https://www.bilibili.com/video/{bv_id}'
        if not url and bv_id:
            url = f'https://www.bilibili.com/video/{bv_id}'
        videos.append(
            VideoItem(
                bvId=bv_id,
                title=title,
                url=url,
                uploadDate=v.get('upload_date'),
                duration=v.get('duration'),
            )
        )
    return UpVideosResponse(uid=uid, videos=videos)

@router.get("/video_meta")
async def get_video_meta(bvid: str, bilivox: BiliVoxManager = Depends(get_bilivox_manager)):
    try:
        return bilivox.downloader.get_video_meta(bvid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 获取文件内容
@router.get("/output")
async def get_file_content(
    path: str,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        content = bilivox.get_file_content(path)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/download")
async def download_file(
    path: str,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        file_path, filename = bilivox.get_file_path_for_download(path)
        return FastAPIFileResponse(path=file_path, filename=filename, media_type="text/markdown")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/file/delete")
async def delete_markdown_file(
    req: DeleteFileRequest,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        bilivox.delete_markdown(req.path)
        return {"message": "已删除"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

class BatchDownloadRequest(BaseModel):
    files: List[str]

@router.post("/files/batch-download")
async def batch_download_files(
    req: BatchDownloadRequest,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        zip_stream, filename = bilivox.batch_download_files(req.files)
        return StreamingResponse(
            zip_stream,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

class BatchDeleteRequest(BaseModel):
    files: List[str]

class LLMPresetItem(BaseModel):
    id: str | None = None
    name: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=200)
    api_base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None

class PresetsImportRequest(BaseModel):
    presets: List[LLMPresetItem]

@router.get("/llm/presets")
async def get_llm_presets(bilivox: BiliVoxManager = Depends(get_bilivox_manager)):
    return bilivox.get_llm_presets()

@router.post("/llm/presets")
async def add_llm_preset(
    preset: LLMPresetItem, 
    bilivox: BiliVoxManager = Depends(get_bilivox_manager), 
    _: None = Depends(require_api_key)
):
    try:
        return bilivox.add_llm_preset(preset.model_dump())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/llm/presets/{preset_id}")
async def update_llm_preset(
    preset_id: str, 
    preset: LLMPresetItem, 
    bilivox: BiliVoxManager = Depends(get_bilivox_manager), 
    _: None = Depends(require_api_key)
):
    try:
        return bilivox.update_llm_preset(preset_id, preset.model_dump(exclude_unset=True))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/llm/presets/{preset_id}")
async def delete_llm_preset(
    preset_id: str, 
    bilivox: BiliVoxManager = Depends(get_bilivox_manager), 
    _: None = Depends(require_api_key)
):
    try:
        bilivox.delete_llm_preset(preset_id)
        return {"message": "已删除"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/llm/presets/import")
async def import_llm_presets(
    req: PresetsImportRequest,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager), 
    _: None = Depends(require_api_key)
):
    try:
        raw_list = [p.model_dump() for p in req.presets]
        count = bilivox.batch_import_presets(raw_list)
        return {"message": f"成功导入 {count} 个预设"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/files/batch-delete")
async def batch_delete_files(
    req: BatchDeleteRequest,
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        count, errors = bilivox.batch_delete_files(req.files)
        return {"message": f"已删除 {count} 个文件", "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/files/batch-merge")
async def batch_merge_files(
    req: BatchDownloadRequest, # 复用 BatchDownloadRequest (files list)
    bilivox: BiliVoxManager = Depends(get_bilivox_manager),
    _: None = Depends(require_api_key),
):
    try:
        stream, filename = bilivox.batch_merge_files(req.files)
        return StreamingResponse(
            stream,
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 解析UP主信息
@router.get("/up_info")
async def get_up_info(url: str, bilivox: BiliVoxManager = Depends(get_bilivox_manager)):
    try:
        info = bilivox.get_up_info(url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/auth_status")
async def auth_status():
    enabled = bool(os.getenv("BILIVOX_API_KEY", "").strip())
    return {"enabled": enabled}


@router.get("/select_folder")
async def select_folder(
    title: str = Query("选择文件夹"),
    initial: str | None = Query(None),
    _: None = Depends(require_api_key),
):
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"当前环境不支持打开系统对话框: {e}")

    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    try:
        directory = filedialog.askdirectory(title=title, initialdir=initial or os.getcwd(), mustexist=True)
    finally:
        try:
            root.destroy()
        except Exception:
            pass

    if not directory:
        return {"path": None}

    if not os.path.isdir(directory):
        raise HTTPException(status_code=400, detail="所选路径不是有效文件夹")

    if not os.access(directory, os.R_OK | os.X_OK):
        raise HTTPException(status_code=403, detail="无权限访问所选文件夹")

    return {"path": directory}


@router.get("/select_file")
async def select_file(
    title: str = Query("选择文件"),
    initial: str | None = Query(None),
    filetypes: str | None = Query(None, description="文件类型过滤，格式：label|*.ext;label2|*.ext2"),
    _: None = Depends(require_api_key),
):
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"当前环境不支持打开系统对话框: {e}")

    parsed_types = None
    if filetypes and isinstance(filetypes, str):
        items = []
        for raw_item in filetypes.split(";"):
            raw_item = raw_item.strip()
            if not raw_item:
                continue
            if "|" in raw_item:
                label, pattern = raw_item.split("|", 1)
                label = label.strip() or "文件"
                pattern = pattern.strip() or "*"
                items.append((label, pattern))
        if items:
            parsed_types = items

    root = tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", 1)
    try:
        path = filedialog.askopenfilename(
            title=title,
            initialdir=initial or os.getcwd(),
            filetypes=parsed_types,
        )
    finally:
        try:
            root.destroy()
        except Exception:
            pass

    if not path:
        return {"path": None}

    if not os.path.isfile(path):
        raise HTTPException(status_code=400, detail="所选路径不是有效文件")

    if not os.access(path, os.R_OK):
        raise HTTPException(status_code=403, detail="无权限读取所选文件")

    return {"path": path}
