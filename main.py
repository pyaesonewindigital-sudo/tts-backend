from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import edge_tts
import asyncio
import os
import shutil
from pydub import AudioSegment

app = FastAPI()

# Temp Folder ဖန်တီးခြင်း
os.makedirs("temp", exist_ok=True)

# SRT Time (00:00:05,123) ကို Milliseconds ပြောင်းပေးသည့် Function
def time_to_ms(time_str):
    h, m, s = time_str.split(':')
    s, ms = s.split(',')
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)

# SRT ဖိုင်ကို ဖတ်ပြီး List အဖြစ် ပြောင်းခြင်း
def parse_srt(content):
    blocks = content.strip().split('\n\n')
    parsed_data = []
    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            # Time line: 00:00:01,000 --> 00:00:04,000
            time_line = lines[1]
            if '-->' in time_line:
                start_str, _ = time_line.split(' --> ')
                start_ms = time_to_ms(start_str.strip())
                text = " ".join(lines[2:]) # စာသားများယူမည်
                parsed_data.append({"start": start_ms, "text": text})
    return parsed_data

@app.get("/")
def read_root():
    return {"status": "TTS Service is Running with FFmpeg!"}

@app.post("/generate-srt")
async def generate_from_srt(
    file: UploadFile = File(...), 
    gender: str = Form("male")
):
    # ၁. Upload တင်လာသော SRT ဖိုင်ကို ဖတ်မည်
    content = (await file.read()).decode("utf-8")
    srt_data = parse_srt(content)
    
    # အသံရွေးချယ်ခြင်း
    voice = "my-MM-ThihaNeural" if gender == "male" else "my-MM-NularNeural"
    
    # ၂. Base Audio အလွတ်တစ်ခု တည်ဆောက်မည်
    final_audio = AudioSegment.empty()
    
    # ၃. SRT တစ်ကြောင်းချင်းစီကို Loop ပတ်ပြီး အသံထုတ်မည်
    for i, item in enumerate(srt_data):
        text = item['text']
        start_ms = item['start']
        
        # ယာယီဖိုင်နာမည်
        temp_file = f"temp/segment_{i}.mp3"
        
        try:
            # edge-tts ဖြင့် အသံထုတ်ခြင်း
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_file)
            
            # အသံဖိုင် ပြန်ဖတ်ခြင်း
            segment_audio = AudioSegment.from_mp3(temp_file)
            
            # Silence တွက်ချက်ခြင်း (SRT အချိန်အတိုင်းဖြစ်စေရန်)
            current_duration = len(final_audio)
            silence_gap = start_ms - current_duration
            
            # လိုအပ်လျှင် Silence ထည့်၊ မလိုအပ်လျှင် (Overlap ဖြစ်လျှင်) ဒီအတိုင်းဆက်
            if silence_gap > 0:
                final_audio += AudioSegment.silent(duration=silence_gap)
            
            # အသံဖိုင် ပေါင်းထည့်ခြင်း
            final_audio += segment_audio
            
            # ယာယီဖိုင် ဖျက်ခြင်း
            os.remove(temp_file)
            
        except Exception as e:
            print(f"Error at segment {i}: {e}")
            continue

    # ၄. နောက်ဆုံးရလဒ်ကို Save ပြီး ပြန်ပို့မည်
    output_filename = "temp/final_output.mp3"
    final_audio.export(output_filename, format="mp3")
    
    return FileResponse(output_filename, media_type="audio/mpeg", filename="output.mp3")