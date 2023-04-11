import shutil
import sounddevice as sd
import soundfile as sf
import os
import io
import uuid
import requests
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from keras.utils import normalize
from keras.models import load_model
from typing import List
import librosa
from PIL import Image
import cv2
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import time
from fastapi import FastAPI, UploadFile, File, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from keras.utils import normalize
import plotly.graph_objects as go
from fastapi.templating import Jinja2Templates
import starlette.status as status

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = './'

# loading our model
model = load_model('../project/voice_model_20epochs.h5')
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

#global variables
result = ''


def record_and_save_spectrogram(audio_file):
    if not os.path.exists(os.path.join(OUTPUT_DIR, 'audio-images-recorded')):
        os.mkdir(os.path.join(OUTPUT_DIR, 'audio-images-recorded'))
    sr = 22050
    # Load audio data from file-like object
    try:
        audio_data, _ = librosa.load(audio_file, sr=sr, mono=True)
        print('got you')
    except Exception as e:
        print(f'Error loading audio data: {e}')
        return None

    # Convert audio to spectrogram
    S = librosa.feature.melspectrogram(y=audio_data, sr=sr)
    S_db = librosa.amplitude_to_db(S, ref=np.max)

    # Save spectrogram as PNG
    timestamp = time.strftime("%Y-%m-%d-%H:%M:%S")
    file_path = os.path.join(OUTPUT_DIR, 'audio-images-recorded', f'spectrogram_{timestamp}.png')
    plt.figure(figsize=(1.9, 1.9))
    librosa.display.specshow(S_db, cmap='viridis', sr=sr)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(file_path, bbox_inches='tight', pad_inches=0)
    plt.close()
    print(f'Spectrogram saved to {file_path}')
    return file_path



@app.get("/", response_class=HTMLResponse)
def record(request: Request):
    return templates.TemplateResponse("index.html",{"request": request})


@app.route("/record", methods=["POST", "GET"])
def record(request: Request):
    return templates.TemplateResponse("rec.html",{"request": request})





@app.post("/recording")
async def recording(request: Request):
    # convert the audio data to a spectrogram image using record_and_save_spectrogram
    audio_blob = await request.body()
    filename = uuid.uuid4().hex
    with open(f'./static/wav/{filename}.wav', 'wb') as f:
        f.write(audio_blob)
    target = record_and_save_spectrogram(f'./static/wav/{filename}.wav')

    # load the spectrogram image using OpenCV
    h = []
    myrec = cv2.imread(target)
    myrec = Image.fromarray(myrec, 'RGB')
    h.append(np.array(myrec))

    h = np.array(h)
    h = normalize(h, axis=1)

    img = h[0]
    # Expand dims so the input is (num images, x, y, c)
    input_img = np.expand_dims(img, axis=0) 
    # Make the prediction
    per = model.predict(input_img)
    print(per)

    global result
    result = per

    os.remove(f'./static/wav/{filename}.wav')

    


@app.get("/results", response_class=HTMLResponse)
def results():
    # data = await record()
    # print(data)
    global result
    if result:
        data = float(result)
        labels = ["Male", "Female"]
        values = [data, 1 - data]
        colors = ["lightcyan", "pink"]
        # Generate the pie chart using Plotly
        fig = go.Figure(data=[go.Pie(labels=labels, values=values,marker = dict(colors = colors), hole=.4)] ,layout=go.Layout(width=680, height=680))
        fig.update_traces(hoverinfo='label+percent', textinfo='label', textfont_size=12,textposition='inside')
        # Set the layout of the chart
        fig.update_layout(annotations=[],showlegend=False)

        # Convert the chart to an HTML div string
        div = fig.to_html(full_html=False)

        result = ''

        return  f"""
                <div style="width: 88%;
                    margin:auto;
                    padding:15px 0;
                    display:flex;
                    align-items: center;
                    justify-content: space-between;
                ">
                    <a href="/">
                        <img src="/static/recogen.png" style=" width: 200px; cursor:pointer;">
                    </a>
                </div>
                <div style="display: flex; justify-content: center; align-items: center; height: 70vh;)">
                    <div class='main-container'>
                        {div}
                    </div>
                </div>
                
                """
    else:
        response = RedirectResponse(url='/record')
        return response


@app.get("/api", response_class=HTMLResponse)
def api():
    global result
    if result:
        return 'True'
    return 'False'
