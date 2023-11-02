from flask import Flask, jsonify, request
from flask_cors import CORS
from Comands.command import *
import re

import time

app = Flask(__name__)
CORS(app)
lista_nombres=[]
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
            message = Disk.command_mkdisk(size, path, unit, fit)
            nombre_reporte_disk = Disk.reporte_Disk(path)
            nombre_reporte_mbr = Disk.reporte_MBR(path)
            if nombre_reporte_disk not in lista_nombres:
                lista_nombres.append(nombre_reporte_disk)

            if nombre_reporte_mbr not in lista_nombres:
                lista_nombres.append(nombre_reporte_mbr)

    elif words[0] == 'rrmdisk':
        path = None
        for word in words:
            if word.startswith('-path='):
                path = word[6:]
                path = path.replace('"', '')

        if path is None:
            message = "Faltan parametros obligatorios"
        else:
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
            message = Disk.command_fdisk(size,path,unit,fit,tipo,name)
            nombre_reporte_disk = Disk.reporte_Disk(path)
            nombre_reporte_mbr = Disk.reporte_MBR(path)
            if nombre_reporte_disk not in lista_nombres:
                lista_nombres.append(nombre_reporte_disk)

            if nombre_reporte_mbr not in lista_nombres:
                lista_nombres.append(nombre_reporte_mbr)

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
            message = Disk.command_mount(path,name)
    elif words[0].startswith('#'):
        message = ""
    else:
        message = "Comando no reconocido"

    respuesta = {
        'estado': 'OK',
        'mensaje': message,
    }

    # Esperamos 1 segundo, para simular proceso de ejecución
    time.sleep(1)

    return jsonify(respuesta)

@app.route('/hola', methods=['GET'])
def hola():
    return jsonify({'message': 'Hola Mundo'})

@app.route('/reporte', methods=['GET'])
def reporte():
    respuesta = {
        'estado': 'OK',
        'mensaje': lista_nombres,
    }
    time.sleep(1)
    return jsonify(respuesta)

if __name__ == '__main__':
    app.run(debug=True)