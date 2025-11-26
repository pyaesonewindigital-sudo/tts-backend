from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import edge_tts
import asyncio
import os
import shutil
from pydub import AudioSegment
from gtts import gTTS  # Google TTS ထပ်ထည့်ထားသည်

app = FastAPI()

os.makedirs("temp", exist_ok=True)

def time_to_ms(time_str):
    h, m, s = time_str.split(':')
    s, ms = s.split(',')
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)

def parse_srt(content):
    blocks = content.strip().split('\n\n')
    parsed_data = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            time_line = lines[1]
            if '-->' in time_line:
                start_str, _ = time_line.split(' --> ')
                start_ms = time_to_ms(start_str.strip())
                text = " ".join(lines[2:])
                parsed_data.append({"start": start_ms, "text": text})
    return parsed_data

# Google TTS ဖြင့် အသံထုတ်သည့် Function (Fallback)
def generate_gtts(text, filename):
    tts = gTTS(text=text, lang='my')
    tts.save(filename)

@app.post("/generate-srt")
async def generate_from_srt(
    file: UploadFile = File(...), 
    gender: str = Form("male")
):
    content = (await file.read()).decode("utf-8")
    srt_data = parse_srt(content)
    
    voice = "my-MM-ThihaNeural" if gender == "male" else "my-MM-NularNeural"
    
    final_audio = AudioSegment.empty()
    
    for i, item in enumerate(srt_data):
        text = item['text']
        start_ms = item['start']
        temp_file = f"temp/segment_{i}.mp3"
        
        # --- HYBRID LOGIC START ---
        try:
            # Plan A: edge-tts ကို အရင်စမ်းမယ်
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_file)
            
            # File size 0 ဖြစ်နေရင် (Block ခံရရင်) Error တက်အောင်လုပ်မယ်
            if os.path.getsize(temp_file) == 0:
                raise Exception("Empty audio file from Edge TTS")
                
        except Exception as e:
            print(f"Segment {i}: EdgeTTS failed ({e}). Switching to Google TTS.")
            # Plan B: Google TTS ကို ပြောင်းသုံးမယ်
            generate_gtts(text, temp_file)
        # --- HYBRID LOGIC END ---

        # Audio Processing
        try:
            segment_audio = AudioSegment.from_mp3(temp_file)
            current_duration = len(final_audio)
            silence_gap = start_ms - current_duration
            
            if silence_gap > 0:
                final_audio += AudioSegment.silent(duration=silence_gap)
            
            final_audio += segment_audio
            os.remove(temp_file)
        except Exception as e:
            print(f"Audio processing error at {i}: {e}")

    output_filename = "temp/final_output.mp3"
    final_audio.export(output_filename, format="mp3")
    
    return FileResponse(output_filename, media_type="audio/mpeg", filename="output.mp3")
