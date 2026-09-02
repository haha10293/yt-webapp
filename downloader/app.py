import os
import uuid
import threading
import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from yt_dlp import YoutubeDL
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from yt_dlp.utils import DownloadError
from concurrent.futures import ThreadPoolExecutor

# 一時保存用のフォルダがなければ作成
DOWNLOAD_DIR = "/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
# ロック用
lock = threading.Lock()
# 最大待機人数
MAX_WAITING = 5
MAX_DOWNLOAD_WORKERS = 3
# ダウロード要求が４人以上の場合、四人目以降は空きが出るまで待機
executor = ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) # 同時DL可能数

app = FastAPI()

# 公開用の設定追加
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:3000"
)

app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],  # ← 追加
)

# メモリ上に進捗情報を保持
progress_store = {}

# 事前に設定可能なファイル形式・解像度を取得
class FormatRequest(BaseModel):
    url: str                  # URL格納

# 動画ダウンロード用
class DownloadRequest(BaseModel):
    url: str                  # URL格納
    format_id: str            # ファイル形式

@app.post("/download")
def download(req: DownloadRequest):
    task_id = str(uuid.uuid4())
    filename = task_id
    filepath = os.path.join(DOWNLOAD_DIR, filename + ".%(ext)s")
    
    # 現在の実行＋待機人数を算出
    with lock:
        active_tasks = sum(
            1 for t in progress_store.values()
            if t["status"] in ["waiting", "downloading", "postprocessing"]
        )
    # 現在の実行＋待機人数が最大実行＋待機人数よりおおければエラーを出す
    if active_tasks >= (MAX_WAITING + MAX_DOWNLOAD_WORKERS):
        raise HTTPException(
            status_code=429,
            detail="Server busy"
        )

    with lock:
        progress_store[task_id] = {
            "percent": 0,
            "status": "waiting"
        }
    
    executor.submit(run_download, req, task_id, filepath)

    return {"filename": filename, "task_id": task_id}

# ダウンロード処理用関数
def run_download(req, task_id, filepath):
    with lock:
        progress_store[task_id]["status"] = "downloading"
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent_str = d.get("_percent_str")
            if percent_str:
                try:
                    percent = float(percent_str.replace("%", "").strip())
                except ValueError:
                    return
                with lock:
                    progress_store[task_id]["percent"] = int(percent)
        elif d['status'] == 'finished':
            print("DOWNLOAD FINISHED, MERGING...")
            with lock:
                progress_store[task_id]["status"] = "postprocessing"
                progress_store[task_id]["percent"] = 100

    ydl_opts = {
        # 映像と音声の合成 or 映像のみ or 音声のみ
        "format": f"{req.format_id}+bestaudio/{req.format_id}/best",
        "outtmpl": filepath,
        "merge_output_format": "mp4", # 結合時のデータ形式をmp4に固定。
        "noplaylist": True,
        "progress_hooks": [progress_hook],
        # 接続を切られたときに再問合せする回数
        "retries": 10,
        "fragment_retries": 10,
        # チャンクサイズを指定
        "http_chunk_size": 10485760,
        # 並列ダウンロードをなしにする
        "concurrent_fragment_downloads": 1,
        # youtubeのjsチャレンジ用
        "js_runtimes": {"deno": {}},
        "remote_components": ["ejs:github"]
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # ydl.download([req.url])
            info = ydl.extract_info(req.url, download=True)
            # 
            if "requested_downloads" in info and info["requested_downloads"]:
                ext = info["requested_downloads"][0].get("ext", "mp4")
            else:
                ext = info.get("ext", "mp4")
        with lock:
            progress_store[task_id]["status"] = "finished"
            progress_store[task_id]["percent"] = 100
            progress_store[task_id]["ext"] = ext
    except DownloadError:
        with lock:
            progress_store[task_id]["status"] = "error"
            progress_store[task_id]["percent"] = -1
            threading.Thread(target=cleanup_task, args=(task_id,), daemon=True).start()
# エラーステータスクリア用関数
def cleanup_task(task_id):
    time.sleep(60)
    with lock:
        progress_store.pop(task_id, None)


# ダウンロード進捗を返すAPI
@app.get("/progress/{task_id}")
def get_progress(task_id: str):
    # start = time.time()    APIの時間測定用
    with lock:
        task = progress_store.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        waiting_count = sum(
            1
            for t_id, t in progress_store.items()
            if t["status"] == "waiting" and t_id != task_id
        )
    # end = time.time()
    # print(f"/progress took {(end - start) * 1000:.2f} ms")
    # return progress_store[task_id]
    return {
        "percent": task["percent"],
        "status": task["status"],
        "waiting_count": waiting_count
    }

# ダウンロードファイル取得API
@app.get("/file/{task_id}")
def get_file(task_id: str, background_tasks: BackgroundTasks):
    with lock:
        task = progress_store.get(task_id)
        if not task or task["status"] != "finished":
            raise HTTPException(status_code=400, detail="Not finished")
        ext = task.get("ext", "mp4")
    filename = f"{task_id}.{ext}"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    response = FileResponse(
        filepath,
        media_type="application/octet-stream",
        filename=filename
    )
    
    # 一時保存データ削除
    background_tasks.add_task(os.remove, filepath)

    with lock:
        progress_store.pop(task_id, None)

    return response

@app.post("/formats")
def get_formats(req: FormatRequest):
    with YoutubeDL({"quiet": True, "js_runtimes": {"deno": {}},"remote_components": ["ejs:github"]}) as ydl:
        info_dict = ydl.extract_info(req.url, download=False)
        
    if info_dict.get("_type") == "playlist":
        info_dict = info_dict["entries"][0]

    if not info_dict or "formats" not in info_dict:
        raise HTTPException(
            status_code=400,
            detail="Could not extract video formats"
        )

    # データ形式のリスト
    formats_list = []
    for f in info_dict["formats"]:
        print("ファイルサイズ＝＝＝＝＝＝＝＝＝", flush=True)
        print(f.get("filesize"), flush=True)
        print(f.get("filesize_approx"), flush=True)
        print("ファイルサイズ＝＝＝＝＝＝＝＝＝", flush=True)

        # ファイルサイズが取得できない場合はリストに追加しない。
        if f.get("filesize") is None and f.get("filesize_approx") is None:
            continue
        # 今回はmp4の形式のデータだけ選択肢として表示する。
        if f.get("ext") != "mp4":
            continue
        if f.get("filesize") is None:
            fsize = f.get("filesize")
        else:
            fsize = f.get("filesize_approx")

        # 動画 or 音声
        kind = "audio" if f.get("vcodec") == "none" else "video"

        # ファイルサイズとデータ形式も追加
        formats_list.append({
            "format_id": f["format_id"],
            "ext": f["ext"],
            "has_audio": f.get("acodec") not in (None, "none"),
            "resolution": f.get("resolution") or "audio only",
            "fps": f.get("fps"),
            "note": f.get("format_note"),
            "kind": kind,
            "filesize": fsize  # バイト単位
        })

    return {"title": info_dict["title"], "thumbnail": info_dict["thumbnail"], "formats": formats_list}

# FastAPI終了時に閉じる
@app.on_event("shutdown")
def shutdown_event():
    executor.shutdown(wait=False)


