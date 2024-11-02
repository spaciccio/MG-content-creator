import os
import json
import io
import sys
import subprocess
import numpy as np
sys.path.append(os.path.join(os.path.expanduser("~"), "AppData/Local/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/local-packages/Python312/site-packages"))
from flask import Flask, request, send_file, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import concatenate_videoclips, ImageClip, CompositeVideoClip
from moviepy.video.fx import all as vfx
sys.path.append(os.path.join(os.path.dirname(__file__), 'public'))
from funz import ffmpeg_write_video_byme
from flask_cors import CORS


V = [None] * 5
immagini = []
progress = None



import json
import requests
import logging

import os
import subprocess as sp

import numpy as np
from proglog import proglog

from moviepy.compat import DEVNULL, PY3
from moviepy.config import get_setting
import logging

import requests
class FFMPEG_VideoWriter:
    """ A class for FFMPEG-based video writing.

    A class to write videos using ffmpeg. ffmpeg will write in a large
    choice of formats.

    Parameters
    -----------

    filename
      Any filename like 'video.mp4' etc. but if you want to avoid
      complications it is recommended to use the generic extension
      '.avi' for all your videos.

    size
      Size (width,height) of the output video in pixels.

    fps
      Frames per second in the output video file.

    codec
      FFMPEG codec. It seems that in terms of quality the hierarchy is
      'rawvideo' = 'png' > 'mpeg4' > 'libx264'
      'png' manages the same lossless quality as 'rawvideo' but yields
      smaller files. Type ``ffmpeg -codecs`` in a terminal to get a list
      of accepted codecs.

      Note for default 'libx264': by default the pixel format yuv420p
      is used. If the video dimensions are not both even (e.g. 720x405)
      another pixel format is used, and this can cause problem in some
      video readers.

    audiofile
      Optional: The name of an audio file that will be incorporated
      to the video.

    preset
      Sets the time that FFMPEG will take to compress the video. The slower,
      the better the compression rate. Possibilities are: ultrafast,superfast,
      veryfast, faster, fast, medium (default), slow, slower, veryslow,
      placebo.

    bitrate
      Only relevant for codecs which accept a bitrate. "5000k" offers
      nice results in general.

    withmask
      Boolean. Set to ``True`` if there is a mask in the video to be
      encoded.

    """

    def __init__(self, filename, size, fps, codec="libx264", audiofile=None,
                 preset="medium", bitrate=None, withmask=False,
                 logfile=None, threads=None, ffmpeg_params=None):

        if logfile is None:
            logfile = sp.PIPE

        self.filename = filename
        self.codec = codec
        self.ext = self.filename.split(".")[-1]

        # order is important
        cmd = [
            get_setting("FFMPEG_BINARY"),
            '-y',
            '-loglevel', 'error' if logfile == sp.PIPE else 'info',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-s', '%dx%d' % (size[0], size[1]),
            '-pix_fmt', 'rgba' if withmask else 'rgb24',
            '-r', '%.02f' % fps,
            '-an', '-i', '-'
        ]
        if audiofile is not None:
            cmd.extend([
                '-i', audiofile,
                '-acodec', 'copy'
            ])
        cmd.extend([
            '-vcodec', codec,
            '-preset', preset,
        ])
        if ffmpeg_params is not None:
            cmd.extend(ffmpeg_params)
        if bitrate is not None:
            cmd.extend([
                '-b', bitrate
            ])

        if threads is not None:
            cmd.extend(["-threads", str(threads)])

        if ((codec == 'libx264') and
                (size[0] % 2 == 0) and
                (size[1] % 2 == 0)):
            cmd.extend([
                '-pix_fmt', 'yuv420p'
            ])
        cmd.extend([
            filename
        ])

        popen_params = {"stdout": DEVNULL,
                        "stderr": logfile,
                        "stdin": sp.PIPE}

        # This was added so that no extra unwanted window opens on windows
        # when the child process is created
        if os.name == "nt":
            popen_params["creationflags"] = 0x08000000  # CREATE_NO_WINDOW

        self.proc = sp.Popen(cmd, **popen_params)


    def write_frame(self, img_array):
        """ Writes one frame in the file."""
        try:
            if PY3:
               self.proc.stdin.write(img_array.tobytes())
            else:
               self.proc.stdin.write(img_array.tostring())
        except IOError as err:
            _, ffmpeg_error = self.proc.communicate()
            error = (str(err) + ("\n\nMoviePy error: FFMPEG encountered "
                                 "the following error while writing file %s:"
                                 "\n\n %s" % (self.filename, str(ffmpeg_error))))

            if b"Unknown encoder" in ffmpeg_error:

                error = error+("\n\nThe video export "
                  "failed because FFMPEG didn't find the specified "
                  "codec for video encoding (%s). Please install "
                  "this codec or change the codec when calling "
                  "write_videofile. For instance:\n"
                  "  >>> clip.write_videofile('myvid.webm', codec='libvpx')")%(self.codec)

            elif b"incorrect codec parameters ?" in ffmpeg_error:

                 error = error+("\n\nThe video export "
                  "failed, possibly because the codec specified for "
                  "the video (%s) is not compatible with the given "
                  "extension (%s). Please specify a valid 'codec' "
                  "argument in write_videofile. This would be 'libx264' "
                  "or 'mpeg4' for mp4, 'libtheora' for ogv, 'libvpx for webm. "
                  "Another possible reason is that the audio codec was not "
                  "compatible with the video codec. For instance the video "
                  "extensions 'ogv' and 'webm' only allow 'libvorbis' (default) as a"
                  "video codec."
                  )%(self.codec, self.ext)

            elif  b"encoder setup failed" in ffmpeg_error:

                error = error+("\n\nThe video export "
                  "failed, possibly because the bitrate you specified "
                  "was too high or too low for the video codec.")

            elif b"Invalid encoder type" in ffmpeg_error:

                error = error + ("\n\nThe video export failed because the codec "
                  "or file extension you provided is not a video")

            print(f"FFMPEG errore :{ffmpeg_error}")
            raise IOError(error)

    def close(self):
        if self.proc:
            self.proc.stdin.close()
            if self.proc.stderr is not None:
                self.proc.stderr.close()
            self.proc.wait()

        self.proc = None

    # Support the Context Manager protocol, to ensure that resources are cleaned up.

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        
def update_label(label, logfile):
    with open(logfile, 'r') as f:
        line = f.readline()
        label.config(text=line)
        


global percentuale
def ffmpeg_write_video_byme(clip, filename, fps, codec="libx264", bitrate=None,
                            preset="medium", withmask=False, write_logfile=False,
                            audiofile=None, verbose=True, threads=None, ffmpeg_params=None,
                            logger='bar'):
    """ Write the clip to a videofile. See VideoClip.write_videofile for details
    on the parameters.
    """
    logging.info(proglog.default_bar_logger(logger))

    if write_logfile:
        logfile = open(filename + ".log", 'w+')
    else:
        logfile = None
    logging.info('Moviepy - Writing video %s\n' % filename)

    with FFMPEG_VideoWriter(filename, clip.size, fps, codec=codec,
                            preset=preset, bitrate=bitrate, logfile=logfile,
                            audiofile=audiofile, threads=threads,
                            ffmpeg_params=ffmpeg_params) as writer:

        nframes = int(clip.duration * fps)
        frame_count = 0
        percentuale = 0
        for t, frame in clip.iter_frames(logger=logger, with_times=True,
                                         fps=fps, dtype="uint8"):

            frame_count += 1
            percentuale = round((frame_count / nframes) * 100)
            logging.info(percentuale)
            

            

            if withmask:
                mask = (255 * clip.mask.get_frame(t))
                if mask.dtype != "uint8":
                    mask = mask.astype("uint8")
                frame = np.dstack([frame, mask])
            writer.write_frame(frame)

    if write_logfile:
        logfile.close()
    logging.info('Moviepy - Done !')

def bubble_sort(images, order):
    n = len(images)
    for i in range(n):
        for j in range(0, n-i-1):
            if order[j] > order[j+1]:
                order[j], order[j+1] = order[j+1], order[j]
                images[j], images[j+1] = images[j+1], images[j]


def create_text_image(text, font_path, font_size, image_path, color):
    img = Image.new('RGBA', (1920, 1080), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(font_path, font_size)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((img.width - 800), 70)
    draw.text(position, text, font=font, fill=color)
    img.save(image_path)
    

app = Flask(__name__, static_folder='.')
CORS(app)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'


def crea_video(immagini, nome_file):
    global V
    print("Stato iniziale di V:", V)

    imagemagick_path = r'C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe'
    cmd = [imagemagick_path, '-version']
    try:
        subprocess.run(cmd, check=True)
        print("ImageMagick funziona correttamente")
    except subprocess.CalledProcessError as e:
        print(f"Errore nell'esecuzione di ImageMagick: {e}")
    font_path = 'LeagueSpartan-Bold.otf'
    if not os.path.isfile(font_path):
        print(f"Il file del font {font_path} non esiste")
    else:
        print('funziona correttamente')
    clips = []
    for i, immagine in enumerate(immagini):
        print(f"Processing image {i}")
        img_resized = immagine.resize((1920, 1310))
        clip = ImageClip(np.array(img_resized), duration=3)
        
        if i != 0:  # Aggiungi un effetto di dissolvenza solo se non è la prima immagine
            clip = clip.fx(vfx.fadein, 1)  # Aggiungi un effetto di dissolvenza di 1 secondo all'inizio di ogni clip
            
        clips.append(clip)
    
    # Aggiungi l'immagine finale
    img_finale = Image.open('fine.png')
    img_finale_resized = img_finale.resize((1920, 1920))
    clip_finale = ImageClip(np.array(img_finale_resized), duration=3)
    clip_finale = clip_finale.fx(vfx.fadein, 1)
    clips.append(clip_finale)
    
    # Concateniamo le clip
    print(f"Number of clips: {len(clips)}")
     
    # Concateniamo le clip
    video = concatenate_videoclips(clips, method="compose")


    # Creiamo un'immagine blu
    img = Image.new('RGBA', (video.size[0], 150), color = (0, 0, 128, 0))
    
    img2 = Image.new('RGBA', (video.size[0], 1400), color = (0, 0, 128, 0))
    
    y_position = 190
    x_position = 980
    
    rect = Image.new('RGBA', (1000, 50), color = (239,124,0,255))
    rect_clip = ImageClip(np.array(rect), duration=video.duration-3).set_position((x_position, y_position))
    print('hello word')
    print("Stato di V prima dell'uso:", V)
    if V[0] is not None:
        create_text_image("€ " + V[0], font_path, 95, "text_image.png",(255,255,255))
    else:
        create_text_image("€ ", font_path, 95, "text_image.png",(255,255,255))
        
    text_image = ImageClip("text_image.png", duration=video.duration-3)
    text_image = text_image.set_position(lambda t: (0,0)).crossfadein(1)

    
    left_image = Image.open('metri.png')  # Sostituisci con il percorso della tua immagine
    left_image = left_image.resize((100, 100))  # Regola la dimensione come preferisci
    img.paste(left_image, (250, 0))  # Posiziona l'immagine a sinistra del testo
    if V[1] is not None:
        create_text_image( V[1], font_path, 70, "text_image1.png",(40, 60, 132))
    else:
        create_text_image("€ ", font_path, 70, "text_image1.png",(40, 60, 132))

    text_image1 = ImageClip("text_image1.png", duration=video.duration-3)
    text_image1 = text_image1.set_position((-750, 1550)).crossfadein(1)

    
    # Aggiungiamo un'immagine a sinistra del testo
    left_image1 = Image.open('piano.png')  
    left_image1 = left_image1.resize((100, 100))  
    img.paste(left_image1, (654, 0)) 
    
    if V[2] is not None:
        if 't' in V[2]:
            create_text_image("Piano " + V[2], font_path, 70, "text_image2.png",(40, 60, 132))
        else:
            create_text_image(V[2] + "° Piano ", font_path, 70, "text_image2.png",(40, 60, 132))
    else:
        create_text_image("° Piano ", font_path, 70, "text_image2.png",(40, 60, 132))

    text_image2 = ImageClip("text_image2.png", duration=video.duration-3)
    text_image2 = text_image2.set_position((7-370, 1550)).crossfadein(1)
    


    
    left_image2 = Image.open('vani.png')  
    left_image2 = left_image2.resize((100, 100))  
    img.paste(left_image2, (1275, 0))  
    
    if V[3] is not None:
        create_text_image( V[3]+' vani', font_path, 70, "text_image3.png",(40, 60, 132))
    else:
        create_text_image(" vani ", font_path, 70, "text_image3.png",(40, 60, 132))

    text_image3 = ImageClip("text_image3.png", duration=video.duration-3)
    text_image3 = text_image3.set_position((250, 1550)).crossfadein(1)

    sfondo = ImageClip('sfondo.png', duration=video.duration)
    
    # Convertiamo l'immagine PIL in una clip di MoviePy e la posizioniamo in basso
    img_clip = ImageClip(np.array(img), duration=video.duration-3).set_position(("center", "bottom"))
    img2_clip = ImageClip(np.array(img2), duration=video.duration-3).set_position((0, 0))

    # Sovrapponiamo il video all'immagine di sfondo, al testo e all'audio
    final_video = CompositeVideoClip([sfondo, video.set_position("center"), img_clip, rect_clip, img2_clip, text_image,text_image1,text_image2,text_image3])
    
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') if os.name == 'nt' else os.path.join(os.path.expanduser('~'), 'Desktop')
    global video_path
    video_path = os.path.join(desktop_path, nome_file + '.mp4')
    
    
    ffmpeg_write_video_byme(final_video, video_path, 30, codec="libx264", bitrate='5000k',preset="medium", withmask=False, write_logfile=False,
                audiofile=selected_audio, verbose=True, threads=None, ffmpeg_params=None,
                logger='bar')
    convert_audio_to_aac(video_path)
    print('finish')
    
    
def convert_audio_to_aac(input_file):
    global video_path 
    print('sono convert_audio')
    if not os.path.exists(input_file):
        print(f"Errore: il file {input_file} non esiste.")
        return
    temp_file = "temp.mp4"
    command = ['ffmpeg', '-i', input_file, '-c:v', 'libx264', '-profile:v', 'high', '-level:v', '3.1', '-vf', 'scale=1756:1756', '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'aac', '-b:a', '128k', temp_file]
    subprocess.run(command, check=True)
    os.remove(input_file)
    os.rename(temp_file, input_file)
    # Invia una richiesta al client per aggiornare la pagina
    return jsonify(message="Video finito")

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    immagini.append(filename)
    return redirect(url_for('index'))

@app.route('/get_percentage', methods=['GET'])
def get_percentage():
    
    return jsonify(percentuale)

@app.route('/salva_dati', methods=['POST'])
def salva_dati():
    global percentuale
    data = request.get_json()
    V = data.get('dati')
    selected_audio = data.get('canzone')
    
    file_immagini = request.files.getlist('immagini')
    immagini = []
    ordine_immagini = list(map(int, data.get('entries').split(',')))
    for file_immagine in file_immagini:
        immagine = Image.open(io.BytesIO(file_immagine.read()))
        immagini.append(immagine)
    
    immagini_ordinate = [None] * (len(immagini) + 1)
    for idx, ordine in enumerate(ordine_immagini):
        if ordine < len(immagini_ordinate):
            immagini_ordinate[ordine] = immagini[idx]
        else:
            print(f"Indice {ordine} fuori dal range della lista immagini_ordinate")
    
    immagini_ordinate = [img for img in immagini_ordinate if img is not None]
    crea_video(immagini_ordinate, V[4])
    
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run()