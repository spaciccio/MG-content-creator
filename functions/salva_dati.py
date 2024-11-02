import json
import os
import io
from PIL import Image
from flask import jsonify
from main import crea_video  # Assicurati di importare la tua funzione crea_video dal modulo corretto

def handler(event, context):
    body = json.loads(event['body'])
    V = [None] * 5
    V[0] = body['dati'][0]
    V[1] = body['dati'][1]
    V[2] = body['dati'][2]
    V[3] = body['dati'][3]
    V[4] = body['dati'][4]
    
    nome_file = V[4]
    selected_audio = body['canzone']
    file_immagini = body['immagini']  # Assicurati che le immagini siano gestite correttamente nel formato richiesto

    immagini = []
    for file_immagine in file_immagini:
        immagine = Image.open(io.BytesIO(file_immagine.read()))
        immagini.append(immagine)

    ordine_immagini = list(map(int, body['entries'].split(',')))
    immagini_ordinate = [None] * (len(immagini) + 1)

    for idx, ordine in enumerate(ordine_immagini):
        if ordine < len(immagini_ordinate):
            immagini_ordinate[ordine] = immagini[idx]
        else:
            print(f"Indice {ordine} fuori dal range della lista immagini_ordinate")

    immagini_ordinate = [img for img in immagini_ordinate if img is not None]
    crea_video(immagini_ordinate, nome_file)
    

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'success'})
    }