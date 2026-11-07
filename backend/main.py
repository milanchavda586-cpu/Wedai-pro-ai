import os
import uuid
import subprocess
import tempfile

import imageio_ffmpeg
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

app = FastAPI(title="WEDAI PRO AI")

@app.get("/")
def home():
    return {
        "status": "online",
        "app": "WEDAI PRO AI",
        "message": "AI Video Editing Engine is running"
    }

@app.post("/edit")
async def edit_video(
    video: UploadFile = File(...),
    music: UploadFile = File(...),
    voice: str = Form("mute"),
    prompt: str = Form("")
):
    job_id = str(uuid.uuid4())

    with tempfile.TemporaryDirectory() as temp:
        video_path = os.path.join(temp, "input_video")
        music_path = os.path.join(temp, "input_music")
        output_path = os.path.join(temp, "edited_video.mp4")

        with open(video_path, "wb") as f:
            f.write(await video.read())

        with open(music_path, "wb") as f:
            f.write(await music.read())

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

        command = [ffmpeg, "-y", "-i", video_path,
                   "-stream_loop", "-1", "-i", music_path]

        if voice == "keep":
            command += [
                "-filter_complex",
                "[0:a]volume=0.35[original];"
                "[1:a]volume=0.75[music];"
                "[original][music]amix=inputs=2:duration=first[audio]",
                "-map", "0:v:0",
                "-map", "[audio]"
            ]
        else:
            command += [
                "-map", "0:v:0",
                "-map", "1:a:0"
            ]

        command += [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]

        try:
            subprocess.run(
                command,
                check=True,
                capture_output=True,
                timeout=900
            )
        except Exception as error:
            raise HTTPException(
                status_code=500,
                detail="Video editing failed. Please try again."
            )

        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename="WEDAI_PRO_EDITED.mp4",
            background=None
      )
