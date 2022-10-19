from multiprocessing import Pool
from vosk import Model, KaldiRecognizer, SetLogLevel
import subprocess
import os
import json
import wave
import time

from config import INPUT_DIR, OUTPUT_DIR, MODEL_DIR, SAMPLE_RATE
from config import WAVE_MODE, FFMPEG_DIR, LOG_LEVEL, PRINTS_OFF

''' THE LAST HALTURA '''

printer = (print, lambda *_: None)[PRINTS_OFF]

FFMPEG_DIR = FFMPEG_DIR.strip()
SetLogLevel(LOG_LEVEL)

model = Model(MODEL_DIR)


def check_dirs():
    if not os.path.exists(INPUT_DIR):
        printer(f'{INPUT_DIR} no such directory, create..')
        os.mkdir(INPUT_DIR)
    if not os.path.exists(OUTPUT_DIR):
        printer(f'{OUTPUT_DIR} no such directory, create..')
        os.mkdir(OUTPUT_DIR)


def check_requirments():
    if WAVE_MODE:
        printer('You run this program in wav-only mode, to change it see WAVE_MODE in "config.py"')
        return 1
    elif any('ffmpeg' in v for v in os.environ.values()):
        printer('FFmpeg found in PATH! Continue...')
        return 0
    elif FFMPEG_DIR.strip():
        printer(f'Trying to use "{FFMPEG_DIR}" from "config.py"...')
        return 0
    else:
        printer('FFmpeg NOT found! This application requires FFmpeg!')
        printer('Please install FFmpeg on your device and add it to PATH')
        printer('or set FFMPEG_DIR in "config.py"!')
        printer('You can only continue working with wave files.')
        printer('If you want disable this notification set WAVE_MODE = True in "config.py".')
        input('Press "Enter" to proceed')
        return 1


def recognize(file):    
    process = subprocess.Popen([f'{FFMPEG_DIR or "ffmpeg"}', '-loglevel', 'quiet', '-i', f'{INPUT_DIR}/{file}', '-ar', f'{SAMPLE_RATE}', '-ac',
                                '1', '-f', f's{SAMPLE_RATE//1000}le', '-'], stdout=subprocess.PIPE)
    filename = file.split('.')[0]
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    with open(f'{OUTPUT_DIR}/{filename}.txt', 'w') as f:
        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                process.terminate()
                process.kill()
                break
            if rec.AcceptWaveform(data):
                temp = json.loads(rec.Result()).get('text', '')
                if temp.strip():
                    f.write(f'{temp}\n')

        f.write(json.loads(rec.FinalResult()).get('text', ''))


def recognize_wave(file):    
    filename = file.split('.')[0]
    wf = wave.open(f'{INPUT_DIR}/{file}', 'rb')
    rec = KaldiRecognizer(model, wf.getframerate())

    with open(f'{OUTPUT_DIR}{filename}.txt', 'w') as f:
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                temp = json.loads(rec.Result()).get('text', '')
                if temp.strip():
                    f.write(f'{temp}\n')

        f.write(json.loads(rec.FinalResult()).get('text', ''))


def main():
    check_dirs()   
    function = (recognize, recognize_wave)[check_requirments()]
    Pool().map(function, os.listdir(INPUT_DIR))


if __name__ == '__main__':
    t = time.time()
    main()
    printer(f'We did it for {time.time() - t} seconds')
    input('Press "Enter" to exit')
