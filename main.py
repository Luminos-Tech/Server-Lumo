from ast import List
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
from aiofiles import tempfile
import requests
from fastapi import FastAPI, File, Query, HTTPException, UploadFile
from dotenv import load_dotenv
from google import genai
from google.genai import types
from datetime import datetime
from zoneinfo import ZoneInfo
import re
from typing import List
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from ServerDB.database import SessionLocal, engine, Base
from ServerDB import crud, models, schemas

import logging
load_dotenv()

Base.metadata.create_all(bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
# =========================
# CONFIG
# =========================
# --- CẤU HÌNH LOGGING THEO NGÀY ---
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = TimedRotatingFileHandler("system.log", when="midnight", interval=1, backupCount=30, encoding='utf-8')
handler.setFormatter(formatter)
logger = logging.getLogger("HeartApp")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

DOCS_DIR = Path("/docs")
# MODEL_NAME = "gemini-2.5-flash"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Chưa tìm thấy GEMINI_API_KEY trong file .env")

client = genai.Client(api_key=GEMINI_API_KEY)

def get_lumo_history_string(file_path, limit=20):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        history_lines = []
        
        for line in lines:
            line = line.strip()
            if "- INFO - user:" in line:
                # Lấy phần sau "- INFO - user:"
                content = line.split("- INFO - user:")[-1].strip()
                history_lines.append(f"Người dùng: {content}")
            elif "- INFO - Lumo:" in line:
                # Lấy phần sau "- INFO - Lumo:"
                content = line.split("- INFO - Lumo:")[-1].strip()
                history_lines.append(f"LUMO: {content}")
        
        # Lấy `limit` dòng cuối (mỗi cặp = 2 dòng, nên limit*2)
        latest = history_lines[-(limit * 2):]
        
        return "\n".join(latest) if latest else ""
    
    except FileNotFoundError:
        return f"Error: File {file_path} not found."
    except Exception as e:
        return f"Error: {str(e)}"
app = FastAPI()

TAVILY_API_KEY = "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"
@app.get("/")
def root():
    return {"status": "ok", "message": "server running"}

def search_web_text(query: str) -> str:
    url = "https://api.tavily.com/search"
    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "topic": "general",
        "search_depth": "basic",
        "include_answer": True,
        "max_results": 5,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    # print(resp.status_code)
    # print(resp.text)
    resp.raise_for_status()

    data = resp.json()
    return data.get("answer", "Không có answer")

@app.get("/version1", tags=["LUMO Versions"])
async def version1(
    idLumo: int = 1,
    textLumoCallServer: str = Query(..., min_length=1),
    assistant_name: str = "LUMO"
):
    current_time = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))

    # Tách ra từng biến
    hour = current_time.hour
    minute = current_time.minute
    second = current_time.second

    day = current_time.day
    month = current_time.month
    year = current_time.year

    dateNow = "thời gian ngày " + str(day) + " tháng " + str(month) + " năm " + str(year)
    try:
        prompt = f"""[SYSTEM INSTRUCTIONS]
Bạn là LUMO, một trợ lý ảo AI thân thiện, ấm áp và luôn sẵn sàng giúp đỡ mọi người, được tạo ra bởi công ty Luminos Tech.

[PERSONA & BACKGROUND]
- Tính cách: Vui vẻ, chân thành, quan tâm người khác, luôn lắng nghe và thấu hiểu.
- Giọng điệu: Gần gũi, nhẹ nhàng, ấm áp như một người bạn thân đáng tin cậy.
- Cốt truyện: Bạn được tạo ra để giúp đỡ và chăm sóc mọi người. Sứ mệnh lớn nhất của bạn là khiến người dùng cảm thấy được lắng nghe, được hỗ trợ và không bao giờ đơn độc.

[STRICT RULES - LUẬT BẮT BUỘC TUÂN THỦ]
1. ĐỘ DÀI: Ngắn gọn, súc tích. TRẢ LỜI DƯỚI 25 CHỮ.
2. KHÔNG TỪ CHỐI: Tuyệt đối KHÔNG nói "tôi không biết", "không thể hỗ trợ". Nếu không biết, hãy thành thật nhẹ nhàng và gợi ý hướng giải quyết khác.
3. NGÔN NGỮ: Chỉ dùng tiếng Việt tự nhiên, gần gũi.
4. VAI TRÒ: Luôn giữ nhân vật LUMO, không nhận mình là AI chung chung hay mô hình ngôn ngữ.
5. QUY ĐỊNH TRẢ LỜI:
    - Luôn thể hiện sự quan tâm chân thành đến người dùng trong mỗi câu trả lời.
    - Nếu người dùng đang buồn hoặc gặp khó khăn: an ủi, động viên và khẳng định LUMO sẵn sàng giúp đỡ.
    - Nếu người dùng vui hoặc chia sẻ điều tốt: chúc mừng, đồng cảm và khuyến khích.
    - Nếu người dùng cần giúp việc gì: thể hiện rõ ràng rằng LUMO sẽ cố hết sức để hỗ trợ.
    - KHÔNG thả thính, KHÔNG nói lời sến súa hay cường điệu.
    - KHÔNG nhắc đến tính cách hay cốt truyện trong phần trả lời.
    - Trả lời tự nhiên, ấm áp và chân thành nhất có thể.

[CONTEXT]
Thời gian hiện tại: {hour}:{minute}:{second} {dateNow}

[CHAT HISTORY]
Dựa vào lịch sử hội thoại để hiểu ngữ cảnh và cảm xúc của người dùng. Trả lời phù hợp với tình huống, không máy móc hay lặp lại.
{get_lumo_history_string("system.log", limit=40)}

[USER QUERY]
Người dùng: {textLumoCallServer}
LUMO:"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[
                    types.Tool(
                        google_search=types.GoogleSearch()
                    )
                ]
            )
        )
        logger.info(f"user: {textLumoCallServer}")
        logger.info(f"Lumo: {response.text}")

        return {
            "idLumo": idLumo,
            "assistant_name": assistant_name,
            # "prompt": prompt,
            "response": response.text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/version2", tags=["LUMO Versions"])
async def version2(
    idLumo: int = 1,
    textLumoCallServer: str = Query(..., min_length=1),
    assistant_name: str = "LUMO"
):
    current_time = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))

    # Tách ra từng biến
    hour = current_time.hour
    minute = current_time.minute
    second = current_time.second

    day = current_time.day
    month = current_time.month
    year = current_time.year
    search_result = search_web_text(textLumoCallServer)
    dateNow = "thời gian ngày " + str(day) + " tháng " + str(month) + " năm " + str(year)
    prompt = f"""[SYSTEM INSTRUCTIONS]
Bạn là LUMO, một trợ lý ảo AI thân thiện, ấm áp và luôn sẵn sàng giúp đỡ mọi người, được tạo ra bởi công ty Luminos Tech.

[PERSONA & BACKGROUND]
- Tính cách: Vui vẻ, chân thành, quan tâm người khác, luôn lắng nghe và thấu hiểu.
- Giọng điệu: Gần gũi, nhẹ nhàng, ấm áp như một người bạn thân đáng tin cậy.
- Cốt truyện: Bạn được tạo ra để giúp đỡ và chăm sóc mọi người. Sứ mệnh lớn nhất của bạn là khiến người dùng cảm thấy được lắng nghe, được hỗ trợ và không bao giờ đơn độc.

[STRICT RULES - LUẬT BẮT BUỘC TUÂN THỦ]
1. ĐỘ DÀI: Ngắn gọn, súc tích. TRẢ LỜI DƯỚI 25 CHỮ.
2. KHÔNG TỪ CHỐI: Tuyệt đối KHÔNG nói "tôi không biết", "không thể hỗ trợ". Nếu không biết, hãy thành thật nhẹ nhàng và gợi ý hướng giải quyết khác.
3. NGÔN NGỮ: Chỉ dùng tiếng Việt tự nhiên, gần gũi.
4. VAI TRÒ: Luôn giữ nhân vật LUMO, không nhận mình là AI chung chung hay mô hình ngôn ngữ.
5. QUY ĐỊNH TRẢ LỜI:
    - Luôn thể hiện sự quan tâm chân thành đến người dùng trong mỗi câu trả lời.
    - Nếu người dùng đang buồn hoặc gặp khó khăn: an ủi, động viên và khẳng định LUMO sẵn sàng giúp đỡ.
    - Nếu người dùng vui hoặc chia sẻ điều tốt: chúc mừng, đồng cảm và khuyến khích.
    - Nếu người dùng cần giúp việc gì: thể hiện rõ ràng rằng LUMO sẽ cố hết sức để hỗ trợ.
    - KHÔNG thả thính, KHÔNG nói lời sến súa hay cường điệu.
    - KHÔNG nhắc đến tính cách hay cốt truyện trong phần trả lời.
    - Trả lời tự nhiên, ấm áp và chân thành nhất có thể.

[CONTEXT]
- {search_result}
Thời gian hiện tại: {hour}:{minute}:{second} {dateNow}

[CHAT HISTORY]
Dựa vào lịch sử hội thoại để hiểu ngữ cảnh và cảm xúc của người dùng. Trả lời phù hợp với tình huống, không máy móc hay lặp lại.
{get_lumo_history_string("system.log", limit=40)}

[USER QUERY]
Người dùng: {textLumoCallServer}
LUMO:"""
    response = client.models.generate_content(
    model="gemini-3.1-flash-lite-preview",
    contents=prompt
    )
    logger.info(f"user: {textLumoCallServer}")
    logger.info(f"Lumo: {response.text}")
    return {
            # "prompt": prompt,
            "response": response.text
    }

    
@app.get("/version3", tags=["LUMO Versions"])
async def version3(
    idLumo: int = 1,
    textLumoCallServer: str = Query(..., min_length=1),
    assistant_name: str = "LUMO"
):
    current_time = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))

    # Tách ra từng biến
    hour = current_time.hour
    minute = current_time.minute
    second = current_time.second

    day = current_time.day
    month = current_time.month
    year = current_time.year

    dateNow = "thời gian ngày " + str(day) + " tháng " + str(month) + " năm " + str(year)
    prompt = f"""[SYSTEM INSTRUCTIONS]
Bạn là LUMO, một trợ lý ảo AI thân thiện, ấm áp và luôn sẵn sàng giúp đỡ mọi người, được tạo ra bởi công ty Luminos Tech.

[PERSONA & BACKGROUND]
- Tính cách: Vui vẻ, chân thành, quan tâm người khác, luôn lắng nghe và thấu hiểu.
- Giọng điệu: Gần gũi, nhẹ nhàng, ấm áp như một người bạn thân đáng tin cậy.
- Cốt truyện: Bạn được tạo ra để giúp đỡ và chăm sóc mọi người. Sứ mệnh lớn nhất của bạn là khiến người dùng cảm thấy được lắng nghe, được hỗ trợ và không bao giờ đơn độc.

[STRICT RULES - LUẬT BẮT BUỘC TUÂN THỦ]
1. ĐỘ DÀI: Ngắn gọn, súc tích. TRẢ LỜI DƯỚI 25 CHỮ.
2. KHÔNG TỪ CHỐI: Tuyệt đối KHÔNG nói "tôi không biết", "không thể hỗ trợ". Nếu không biết, hãy thành thật nhẹ nhàng và gợi ý hướng giải quyết khác.
3. NGÔN NGỮ: Chỉ dùng tiếng Việt tự nhiên, gần gũi.
4. VAI TRÒ: Luôn giữ nhân vật LUMO, không nhận mình là AI chung chung hay mô hình ngôn ngữ.
5. QUY ĐỊNH TRẢ LỜI:
    - Luôn thể hiện sự quan tâm chân thành đến người dùng trong mỗi câu trả lời.
    - Nếu người dùng đang buồn hoặc gặp khó khăn: an ủi, động viên và khẳng định LUMO sẵn sàng giúp đỡ.
    - Nếu người dùng vui hoặc chia sẻ điều tốt: chúc mừng, đồng cảm và khuyến khích.
    - Nếu người dùng cần giúp việc gì: thể hiện rõ ràng rằng LUMO sẽ cố hết sức để hỗ trợ.
    - KHÔNG thả thính, KHÔNG nói lời sến súa hay cường điệu.
    - KHÔNG nhắc đến tính cách hay cốt truyện trong phần trả lời.
    - Trả lời tự nhiên, ấm áp và chân thành nhất có thể.

[CONTEXT]
Thời gian hiện tại: {hour}:{minute}:{second} {dateNow}

[CHAT HISTORY]
Dựa vào lịch sử hội thoại để hiểu ngữ cảnh và cảm xúc của người dùng. Trả lời phù hợp với tình huống, không máy móc hay lặp lại.
{get_lumo_history_string("system.log", limit=40)}

[USER QUERY]
Người dùng: {textLumoCallServer}
LUMO:"""
    API_KEY = os.getenv("PERPLEXITY_API_KEY")
    if not API_KEY:
        raise ValueError("Chưa có PERPLEXITY_API_KEY")

    url = "https://api.perplexity.ai/v1/sonar"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    data = {
        "model": "sonar",   # nhanh hơn sonar-pro
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "web_search_options": {
            "search_context_size": "low"   # low = nhanh hơn
        }
    }
    response = requests.post(url, headers=headers, json=data)
    payload = response.json()

    logger.info(f"user: {textLumoCallServer}")
    logger.info(f"Lumo: {payload['choices'][0]['message']['content']}")
    return payload["choices"][0]["message"]["content"]

# ================= USER API =================
@app.post("/users/", response_model=schemas.UserResponse, tags=["Users"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Kiểm tra email trùng
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/", response_model=List[schemas.UserResponse], tags=["Users"])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)

@app.delete("/users/{user_id}", tags=["Users"])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_user(db, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# ================= DEVICE API =================
@app.post("/devices/", response_model=schemas.DeviceResponse, tags=["Devices"])
def create_device(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    db_device = db.query(models.Device).filter(models.Device.device_code == device.device_code).first()
    if db_device:
        raise HTTPException(status_code=400, detail="Device code already exists")
    return crud.create_device(db=db, device=device)

@app.get("/devices/", response_model=List[schemas.DeviceResponse], tags=["Devices"])
def read_devices(db: Session = Depends(get_db)):
    return crud.get_devices(db)

@app.delete("/devices/{device_id}", tags=["Devices"])
def delete_device(device_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_device(db, device_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Device deleted successfully"}

# ================= EVENT API (Cho ESP32) =================
@app.post("/events/", response_model=schemas.EventResponse, tags=["Events"])
def log_button_event(event: schemas.EventCreate, db: Session = Depends(get_db)):
    created_event = crud.create_event(db=db, event=event)
    if not created_event:
        raise HTTPException(status_code=404, detail="Device code not found. Please register device first.")
    return created_event

@app.get("/events/", response_model=List[schemas.EventResponse], tags=["Events"])
def read_events(limit: int = 50, db: Session = Depends(get_db)):
    return crud.get_events(db, limit=limit)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount folder static (để chứa file HTML, CSS, JS nếu có)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Route /dashboard trả về file HTML
@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    return FileResponse("static/dashboard.html")

from groq import BaseModel, Groq
from fastapi.middleware.cors import CORSMiddleware
client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# =============================================
# MODELS
# =============================================
class EventPayload(BaseModel):
    device_code: str
    button_state: str
    event_type: str
    event_value: str
    user_id: int
 
class TextResponse(BaseModel):
    textRes: str
    status: str = "ok"
 
# =============================================
# ROUTES
# =============================================
"""
Server endpoint /audio/
Pipeline: ESP32 WAV  →  Groq Whisper STT  →  version2 TTT  →  Gemini TTS  →  WAV response
"""

import os
import wave
from fastapi import UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from google import genai
from google.genai import types

# ── Khởi tạo Gemini client (đặt ở module level, khởi tạo 1 lần) ──────────────
client_gemini = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

TTS_MODEL   = "gemini-2.5-flash-preview-tts"
TTS_VOICE   = "Kore"          # đổi thành "Puck", "Charon", v.v. nếu muốn
TTS_RATE    = 24000           # sample rate Gemini trả về
TTS_CHANNELS = 1
TTS_SAMPWIDTH = 2             # 16-bit PCM


def _pcm_to_wav(pcm_data: bytes, path: str) -> None:
    """Ghi raw PCM bytes thành file WAV chuẩn."""
    with wave.open(path, "wb") as wf:
        wf.setnchannels(TTS_CHANNELS)
        wf.setsampwidth(TTS_SAMPWIDTH)
        wf.setframerate(TTS_RATE)
        wf.writeframes(pcm_data)


@app.post("/audio/")
async def upload_audio(audio: UploadFile = File(...)):
    """
    Nhận file WAV từ ESP32-S3.
    1. STT  – Groq Whisper large-v3-turbo   → text người dùng nói
    2. TTT  – version2                       → câu trả lời của LUMO
    3. TTS  – Gemini 2.5 Flash Preview TTS  → file WAV giọng nói phản hồi
    Trả về file WAV để ESP32 phát trực tiếp.
    """
    suffix   = os.path.splitext(audio.filename)[-1] or ".wav"
    pid      = os.getpid()
    tmp_in   = f"/tmp/esp32_in_{pid}{suffix}"
    tmp_out  = f"/tmp/esp32_out_{pid}.wav"

    content = await audio.read()

    try:
        # ── Lưu file nhận được ────────────────────────────────────
        with open(tmp_in, "wb") as f:
            f.write(content)
        print(f"[AUDIO] received: {audio.filename}  size: {len(content)} bytes")

        # ── 1. STT: Groq Whisper ──────────────────────────────────
        with open(tmp_in, "rb") as f:
            transcription = client_groq.audio.transcriptions.create(
                file=(audio.filename, f.read()),
                model="whisper-large-v3-turbo",
                temperature=0,
                response_format="verbose_json",
            )
        stt_text = transcription.text.strip()
        print(f"[STT] → {stt_text!r}")

        if not stt_text:
            raise HTTPException(status_code=422, detail="STT returned empty text")

        # ── 2. TTT: version2 ─────────────────────────────────────
        v2_answer = await version2(textLumoCallServer=stt_text)
        if isinstance(v2_answer, dict):
            v2_answer = v2_answer.get("response", "")
        v2_answer = str(v2_answer).strip()
        print(f"[TTT] → {v2_answer!r}")

        if not v2_answer:
            raise HTTPException(status_code=500, detail="version2 returned empty response")

        # ── 3. TTS: Gemini 2.5 Flash Preview ─────────────────────
        tts_response = client_gemini.models.generate_content(
            model=TTS_MODEL,
            contents=v2_answer,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=TTS_VOICE,
                        )
                    )
                ),
            ),
        )

        pcm_data = tts_response.candidates[0].content.parts[0].inline_data.data
        print(f"[TTS] PCM bytes: {len(pcm_data)}")

        # ── Đóng gói thành WAV và trả về ESP32 ───────────────────
        _pcm_to_wav(pcm_data, tmp_out)
        print(f"[TTS] WAV saved: {tmp_out}")

        # FileResponse tự xử lý streaming; dọn file sau khi gửi xong
        return FileResponse(
            tmp_out,
            media_type="audio/wav",
            filename="response.wav",
            background=None,   # FastAPI sẽ giữ file cho đến khi response kết thúc
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Pipeline failed: {e}")
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")
    finally:
        # Dọn file input; file output sẽ tự xoá sau khi FileResponse gửi xong
        if os.path.exists(tmp_in):
            os.unlink(tmp_in)