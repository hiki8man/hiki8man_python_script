import ffmpeg
import re
import json
from pathlib import Path
from dataclasses import dataclass
import psutil
import threading
from collections.abc import Callable

JSON = re.compile(r'\{[\s\S]*?\}')

FFMPEG_PATH = Path().joinpath("ffmpeg","ffmpeg.exe")
FFPROBE_PATH = Path().joinpath("ffmpeg","ffprobe.exe")

def watch_parent():
    import time
    import os
    process = psutil.Process(os.getppid())
    while process.is_running():
        time.sleep(1)
    me = psutil.Process()
    for children in me.children(recursive=True):
        children.kill()

threading.Thread(target=watch_parent, daemon=True).start()

class FFmpegConvert:
    def __init__(self):
        pass

class FFmpegProcess:
    def __init__(self, ffmpeg_path:Path|str = "ffmpeg", ffprobe_path:Path|str = "ffprobe") -> None:
        self.ffmpeg_path:Path|str = ffmpeg_path
        self.ffprobe_path:Path|str = ffprobe_path

        self.in_time_us: int = 0
        self.out_time_us: int = -1
        self.on_progress: bool = False

    def start(self, ffmpeg_object, file_path:Path) -> str:
        
        self.reset_progress()

        self.in_time_us = self.get_time(file_path)

        process = ffmpeg.run_async(
            ffmpeg_object,
            cmd = f"{self.ffmpeg_path}",
            pipe_stdout=True,
            pipe_stderr=True,
        )


        stderr_list:list[str] = []

        for line in process.stderr: # type:ignore
            line_str = line.decode('utf-8', errors='ignore').strip()

            self.update_progress(line_str)
            stderr_list.append(line_str)

        return ''.join(stderr_list)
    def update_progress(self,line_str:str):
        try:
            key, value = line_str.split('=', 1)
            match key:
                case 'out_time_us':
                    self.out_time_us = int(value)
                case 'progress':
                    if value == "continue":
                        self.on_progress = True
                    elif value == "end":
                        self.on_progress = False
                        self.out_time_us = self.in_time_us if self.out_time_us > self.in_time_us else self.out_time_us
                    else:
                        raise ValueError(f"Invalid progress value: {value}")
                
                    self.process_func()
        except ValueError:
            return 
                
    def reset_progress(self):
        self.in_time_us: int = 0

        self.out_time_us: int = -1
        self.on_progress: bool = False

    def get_time(self, file_path: Path) -> int:
        info = ffmpeg.probe(
            file_path,
            cmd=f"{self.ffprobe_path}"
        ) 
        return int(float(info['format']['duration']) * 1000 * 1000)
    
    def process_func(self):

        if self.on_progress:
            from datetime import timedelta
            process = self.out_time_us / self.in_time_us
            print(f"\r{process:.2%}", end="", flush=True)
        elif self.out_time_us == self.in_time_us and self.in_time_us > 0:
            process = self.out_time_us / self.in_time_us
            print("\r100.00%")
    
ffmpeg_process = FFmpegProcess(FFMPEG_PATH, FFPROBE_PATH)

def audio_convert(input_path: Path, output_path: Path= Path("output.ogg")):
    
    input_stream = ffmpeg.input(input_path)
    
    audio_1pass = input_stream.audio.filter(
        filter_name='loudnorm',
        I=-10.8,
        TP=-0.5,
        print_format='json'
    )

    process = ffmpeg.output(
        audio_1pass,
        "",
        f='null'
    )

    process = process.global_args(
        "-hide_banner",
        '-loglevel', 'info',
        '-nostats')

    stderr_output = ffmpeg_process.start(process, input_path)
    match = JSON.search(stderr_output)

    if match:
        data = json.loads(match.group(0))
    else:
        raise ValueError("No JSON output found.")
    
    audio_2pass = input_stream.audio.filter(
        filter_name='loudnorm',
        I=-10.8,
        TP=-0.5,
        measured_I=data['input_i'],
        measured_TP=data['input_tp'],
        measured_LRA=data['input_lra'],
        measured_thresh=data['input_thresh'],
        offset=data["target_offset"]
    )
    output = ffmpeg.output(
        audio_2pass,
        str(output_path),
        acodec='libvorbis',
        aq=6,
        ar=44100,
    ).overwrite_output()
    
    process = output.global_args(
        '-progress', 'pipe:2',
        "-hide_banner", 
        '-loglevel', 'info',
        '-nostats')

    stderr_output = ffmpeg_process.start(process, input_path)
    
audio_convert(Path("output.ogg"), Path("output2.ogg"))
pass