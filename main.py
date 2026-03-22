from ast import List
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
import requests
from fastapi import FastAPI, Query, HTTPException
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
