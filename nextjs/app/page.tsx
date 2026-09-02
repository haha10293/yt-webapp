"use client";
import { useState, useEffect } from "react";

// 公開用の設定
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [url, setUrl] = useState("");
  const [formats, setFormats] = useState<any[]>([]);
  const [selectedFormat, setSelectedFormat] = useState("");
  const [thumbnail, setThumbnail] = useState("");
  const [title, setTitle] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [waitingCount, setWaitingCount] = useState(0);
  const [status, setStatus] = useState("idle");
  const [loading, setLoading] = useState(false);
  const [formating, setFormating] = useState(false);

  // フォーマット取得
  const fetchFormats = async () => {
    if (formating || loading || taskId) return; // 既に処理中なら無視（二重送信防止）
    setFormating(true)
    try {
      const res = await fetch(`${API_URL}/formats`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      // エラー対応
      if (!res.ok) {
        alert("Server busy or download failed");
        setFormating(false);
        return;
      }
      
      const data = await res.json();

      setFormats(data.formats);
      setTitle(data.title);
      setThumbnail(data.thumbnail);
    } finally {
      setFormating(false)
    }    
  };

  // ダウンロード処理
  const handleDownload = async () => {
    if (!selectedFormat) return;
    if (loading || taskId) return;  // すでにダウンロード中なら無視（二重送信防止）

    setLoading(true);
    setProgress(0);

    // サーバ側 DownLoadRequestに合わせてキー名を統一
    const res = await fetch(`${API_URL}/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url,
        format_id: selectedFormat, // FastAPI側もformat_idに統一
      }),
    });
    // エラー対応
    if (!res.ok) {
      alert("Server busy or download failed");
      setLoading(false);
      setTaskId(null); // ← ここでクリア
      return;
    }

    const data = await res.json();
    setTaskId(data.task_id); // タスクIDを保存
  };

  // 進捗問い合わせ
  useEffect(() => {
    let interval: number;
    if (taskId) {
      interval = window.setInterval(async () => {
        const res = await fetch(`${API_URL}/progress/${taskId}`);
        // エラー対応
        if (!res.ok) {
          alert("Server busy or download failed");
          setLoading(false);
          setTaskId(null); // ← ここでクリア
          return;
        }
        const data = await res.json();
        setProgress(data.percent);
        setStatus(data.status);
        setWaitingCount(data.waiting_count);

        if (data.status === "finished") {
          clearInterval(interval)

          // ダウンロード完了後にファイル取得
          let fileRes;
          for (let i = 0; i < 3; i++) {
            fileRes = await fetch(`${API_URL}/file/${taskId}`);
            if (fileRes.ok) break;
            await new Promise(r => setTimeout(r, 500));
          }
          if (!fileRes || !fileRes.ok) {
            alert("ファイル取得に失敗しました");
            setLoading(false);
            setTaskId(null); // ← ここでクリア
            return;
          }

          const disposition = fileRes.headers.get("Content-Disposition");
          let filename = "download";

          if (disposition && disposition.includes("filename=")) {
            filename = disposition
              .split("filename=")[1]
              .replace(/"/g, "");
          }

          const blob = await fileRes.blob();

          const downloadUrl = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = downloadUrl;
          a.download = filename;
          a.click();

          setLoading(false);
          setTaskId(null); // ← ここでクリア
        };

        if (data.status === "error") {
          clearInterval(interval);
          setLoading(false);
          setTaskId(null); // ← ここでクリア
          alert("ダウンロードに失敗しました");
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [taskId]);

  return (
    <main style={{ padding: 40 }}>
      <h1>Web Video Downloader</h1>

      <div>
        <input
          type="text"
          placeholder="動画URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          style={{ width: 400 }}
        />
        <button onClick={fetchFormats} disabled={formating || loading}>
          {formating ? "抽出中..." : "抽出"}
        </button>
      </div>

      {/* タイトルとサムネ表示 */}
      {title && (
        <div style={{ marginTop: 20 }}>
          <h2>{title}</h2>
          {thumbnail && <img src={thumbnail} width="300" />}
        </div>
      )}

      {formats.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <label>フォーマット選択: </label>
          <select
            value={selectedFormat}
            onChange={(e) => setSelectedFormat(e.target.value)}
          >
            <option value="">選択してください</option>
            {formats.map((f, i) => (
              <option key={i} value={f.format_id}>
                {f.kind === "audio" ? "🎵 Audio" : f.has_audio ? "🎞️ Multimedia" : "🎬 Video"} /{" "}
                {f.resolution} / {f.ext} / {f.fps ? f.fps + "fps" : "-"} /{" "}
                {f.filesize ? (f.filesize / 1024 / 1024).toFixed(2) + "MB" : "Unknown"}
              </option>
            ))}
          </select>
        </div>
      )}

      <div>
        {status === "idle" && "idle..."}
        {status === "waiting" && `Waiting...(あと${waitingCount}件)`}
        {status === "downloading" && `Downloading ${progress}%`}
        {status === "postprocessing" && "Processing video..."}
        {status === "finished" && "Finished"}
      </div>

      <div style={{ marginTop: 20 }}>
        <button onClick={handleDownload} disabled={loading || !selectedFormat}>
          {loading ? "ダウンロード中..." : "ダウンロード"}
        </button>
        {loading && (
          <div style={{ width: 400, height: 20, border: "1px solid #5AFF19", marginTop: 10 }}>
            <div
              style={{
                width: `${progress}%`,
                height: "100%",
                backgroundColor: "green",
                transition: "width 0.2s linear",
              }}
            />
          </div>
        )}
      </div>
    </main>
  );
}
