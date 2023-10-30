from flask import Flask, jsonify, request
from flask_cors import CORS
from Comands.command import *
import re

import time

app = Flask(__name__)
CORS(app)

@app.route('/execute', methods=['POST'])
def get_first_word():
    data = request.get_json()
    message = data.get('command', '')

    words = message.split()

    if words[0] == 'mkdisk':
        size, unit, path, fit = None, None, None, None
        for word in words:
            if word.startswith('-size='):
                size = word[6:]
                size= int(size)
            elif word.startswith('-unit='):
                unit = word[6:]
            elif word.startswith('-path='):
                path = word[6:]
                path = path.replace('"', '')
            elif word.startswith('-fit='):
                fit = word[5:]
        
        unit = unit if unit != None else 'M'
        fit = fit if fit != None else 'FF'
        if size is None or path is None:
            message = "Faltan parametros obligatorios"
        else:
            if path.startswith('.'):
                path = path[1:]
            path = "./frontend/src/Archivos" + path
            print("mkdisk "+path)
            message = Disk.command_mkdisk(size, path, unit, fit)

    elif words[0] == 'rrmdisk':
        path = None
        for word in words:
            if word.startswith('-path='):
                path = word[6:]
                path = path.replace('"', '')

        if path is None:
            message = "Faltan parametros obligatorios"
        else:
            if path.startswith('.'):
                path = path[1:]
            path = "./frontend/src/Archivos" + path
            print("rmdisk "+path)
            message = Disk.command_rmdisk(path)

    elif words[0] == 'fdisk':
        size,path,name,unit,tipo,fit = None,None,None,None,None,None
        for word in words:
            if word.startswith('-size='):
                size = word[6:]
                size= int(size)
            elif word.startswith('-path='):
                path = word[6:]
                path = path.replace('"', '')
            elif word.startswith('-name='):
                name = word[6:]
                name = name.replace('"', '')
            elif word.startswith('-unit='):
                unit = word[6:]
            elif word.startswith('-type='):
                tipo = word[6:]
            elif word.startswith('-fit='):
                fit = word[5:]
        
        unit = unit if unit != None else 'K'
        tipo = tipo if tipo != None else 'P'
        fit = fit if fit != None else 'WF'

        if size is None or path is None or name is None:
            message = "Faltan parametros obligatorios"
        else:
            if path.startswith('.'):
                path = path[1:]
            path = "./frontend/src/Archivos" + path
            print("fdisk "+path)
            message = Disk.command_fdisk(size,path,unit,fit,tipo,name)
            Disk.reporte_Disk(path)
            Disk.reporte_MBR(path)

    elif words[0] == 'mount':
        path,name = None,None
        for word in words:
            if word.startswith('-path='):
                path = word[6:]
                path = path.replace('"', '')
            elif word.startswith('-name='):
                name = word[6:]
                name = name.replace('"', '')

        if path is None or name is None:
            message = "Faltan parametros obligatorios"
        else:
            if path.startswith('.'):
                path = path[1:]
            path = "./frontend/src/Archivos" + path
            print("mount "+path)
            message = Disk.command_mount(path,name)
    elif words.startswith('#'):
        message = ""

    respuesta = {
        'estado': 'OK',
        'mensaje': message,
    }

    # Esperamos 1 segundo, para simular proceso de ejecución
    time.sleep(1)

    return jsonify(respuesta)

if __name__ == '__main__':
    app.run(debug=True)