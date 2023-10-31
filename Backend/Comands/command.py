import random
import os
import time
import struct
import os
import Struct.Structs
import graphviz as gv
from Global.Global import mounted_partitions
from dotenv import load_dotenv
import boto3

load_dotenv()
aws_access_key_id= os.getenv("AWS_KEY_ID")
aws_secret_access_key= os.getenv("AWS_SECRET_KEY")
bucket_name = "mia-p2-202000544"
lista_nombres= ""

class Disk:
    def __init__(self):
        pass

    def command_mkdisk(size, path, unit, fit):
        disco = Struct.Structs.MBR()
        try:
            if unit == "K":
                total_size = 1024 * size
            elif unit == "M":
                total_size = 1024 * 1024 * size
            else:
                message=("Error: Unidad no válida")
                return message
            if size <= 0:
                message=("Error: El parámetro size del comando MKDISK debe ser mayor a 0")
                return message

            fit = fit
            disco.mbr_tamano = total_size
            disco.mbr_fecha_creacion = int(time.time())
            disco.disk_fit = fit
            disco.mbr_disk_signature = random.randint(100, 9999)

            if os.path.exists(path):
                message=("Error: Disco ya existente en la ruta: " + path)
                return message

            folder_path = os.path.dirname(path)
            os.makedirs(folder_path, exist_ok=True)

            disco.mbr_Partition_1 = Struct.Structs.Particion()
            disco.mbr_Partition_2 = Struct.Structs.Particion()
            disco.mbr_Partition_3 = Struct.Structs.Particion()
            disco.mbr_Partition_4 = Struct.Structs.Particion()

            if path.startswith('"'):
                path = path[1:-1]

            if not path.endswith(".dsk"):
                message=(
                    "Error: Extensión de archivo no válida para la creación del Disco."
                )
                return message

            try:
                with open(path, "w+b") as file:
                    file.write(b"\x00")
                    file.seek(total_size - 1)
                    file.write(b"\x00")
                    file.seek(0)
                    file.write(bytes(disco))
                message = '>>>> MKDISK: Disco creado exitosamente <<<<'
            except Exception as e:
                print(e)
                message=("Error: Error al crear el disco en la ruta: " + path)
        except ValueError:
            message=(
                "Error: El parámetro size del comando MKDISK debe ser un número entero"
            )
        return message

    def command_rmdisk(path):
        if path.startswith('"') and path.endswith('"'):
            path = path[1:-1]
        try:
            if os.path.isfile(path):
                if not path.endswith(".dsk"):
                    message=(
                        "Error: Extensión de archivo no válida para la eliminación del Disco."
                    )
                os.remove(path)
                message = ">>>> RMDISK: Disco eliminado exitosamente <<<<"
                return message
            else:
                message=("El disco no existe en la ruta indicada.")
        except Exception as e:
            message=("Error al intentar eliminar el disco: " + str(e))
            return message

    def command_fdisk(size, path, unit, fit, tipo, name):
        try:
            if unit == "B":
                total_size = size
            elif unit == "K":
                total_size = 1024 * size
            elif unit == "M":
                total_size = 1024 * 1024 * size
            else:
                message=("-unit no contiene los valores esperados...")
                return message

            if size <= 0:
                message=("-size debe de ser mayor que 0")
                return message
        
            if fit.lower() != "bf" and fit.lower() != "ff" and fit.lower() != "wf":
                message=("-fit no contiene los valores esperados...")
                return message
            
            if tipo.lower() != "p" and tipo.lower() != "e" and tipo.lower() != "l":
                message=("-type no contiene los valores esperados...")
                return message
            if not os.path.exists(path):
                message=("Error: No existe el disco en la ruta: "+path)
                return message
            try:
                mbr = Struct.Structs.MBR()
                with open(path, "rb") as file:
                    mbr_data = file.read()
                    mbr.mbr_tamano = struct.unpack("<i", mbr_data[:4])[0]
                    mbr.mbr_fecha_creacion = struct.unpack("<i", mbr_data[4:8])[0]
                    mbr.mbr_disk_signature = struct.unpack("<i", mbr_data[8:12])[0]
                    mbr.disk_fit = mbr_data[12:14].decode('utf-8')
                    
                    partition_size = struct.calcsize("<iii16s")*4
                    partition_data = mbr_data[14:14 + partition_size]
                    mbr.mbr_Partition_1.__setstate__(partition_data[0:28]) 
                    mbr.mbr_Partition_2.__setstate__(partition_data[28:56]) 
                    mbr.mbr_Partition_3.__setstate__(partition_data[56:84]) 
                    mbr.mbr_Partition_4.__setstate__(partition_data[84:112])
            except Exception as e:
                print(e)

            partitions = [mbr.mbr_Partition_1, mbr.mbr_Partition_2, mbr.mbr_Partition_3, mbr.mbr_Partition_4]
            size_elim = []
            for particion in partitions:
                if(particion.part_status == "D"):
                    size_elim.append(particion.part_size)
            for particion in partitions:
                if(particion.part_type == "E" and tipo == "E"):
                    message=("Ya existe una particion extendida")
                    return message
                elif(particion.part_type == "P" and tipo == "P"):
                    if(particion.part_name == name):
                        message=(f"Error: Particion Primaria con nombre "+name+" ya existente")
                        return message
            conteo_particiones = 0
            for particion in partitions:
                if (particion.part_type == "P" or particion.part_type == "E") and particion.part_status == "1":
                    conteo_particiones += 1
            if conteo_particiones == 4 and tipo != "L":
                message=("Error: Ya existen 4 particiones")
                return message
            mbr_size = 14 + struct.calcsize("<iii16s")*4
            if mbr.disk_fit == "FF":
                aux_size = mbr_size
                for particion in partitions:
                    if tipo == "P":
                        if particion.part_status == "1":
                            aux_size += particion.part_size
                        elif particion.part_status == "0":
                            particion.part_status = "1"
                            particion.part_type = tipo
                            particion.part_fit = fit
                            particion.part_size = total_size
                            particion.part_name = name
                            particion.part_start = aux_size
                            aux_size += total_size
                            break
                        elif particion.part_status == "D":
                            size_elim = size_elim[0]
                            if size_elim >= total_size:
                                particion.part_status = "1"
                                particion.part_type = tipo
                                particion.part_fit = fit
                                particion.part_size = total_size
                                particion.part_name = name
                                particion.part_start = aux_size
                                aux_size += total_size
                                break
                            else:
                                message=("Error: espacio insuficiente")
                                return message
                    elif tipo == "E":
                        ebr = Struct.Structs.EBR()
                        if particion.part_status == "1":
                            aux_size += particion.part_size
                        elif particion.part_status == "0":
                            particion.part_status = "1"
                            particion.part_type = tipo
                            particion.part_fit = fit
                            particion.part_size = total_size
                            particion.part_name = name
                            particion.part_start = aux_size

                            ebr.part_status = "0"
                            ebr.part_fit = 'WF'
                            ebr.part_size = 0
                            ebr.part_name = 'null'
                            ebr.part_start = aux_size
                            ebr.part_next = -1
                            aux_size += total_size
                            break
                        elif particion.part_status == "D":
                            size_elim = size_elim[0]
                            if size_elim >= total_size:
                                particion.part_status = "1"
                                particion.part_type = tipo
                                particion.part_fit = fit
                                particion.part_size = total_size
                                particion.part_name = name
                                particion.part_start = aux_size

                                ebr.part_status = "0"
                                ebr.part_fit = 'WF'
                                ebr.part_size = 0
                                ebr.part_name = 'null'
                                ebr.part_start = aux_size
                                ebr.part_next = -1
                                aux_size += total_size

                                break
                            else:
                                message=("Error: espacio insuficiente")
                                return message
                    elif tipo == "L":
                        exis=False
                        for particion in partitions:
                            if particion.part_type == "E":
                                exis=True
                                message = Disk.crearLogicas(particion.part_start, total_size, path, name, mbr.disk_fit,fit,particion.part_size)
                                return message
                        if not exis:
                            message=("No existe particion extendida")
                            return message
                        
            elif mbr.disk_fit == "BF":
                aux_size = mbr_size
                for particion in partitions:
                    if tipo == "P":
                        if particion.part_status == "1":
                            aux_size += particion.part_size
                        elif particion.part_status == "0":
                            particion.part_status = "1"
                            particion.part_type = tipo
                            particion.part_fit = fit
                            particion.part_size = total_size
                            particion.part_name = name
                            particion.part_start = aux_size
                            aux_size += total_size
                            break
                        elif particion.part_status == "D":
                            size_elim.sort()
                            size_elim = size_elim[0]
                            if size_elim >= total_size:
                                particion.part_status = "1"
                                particion.part_type = tipo
                                particion.part_fit = fit
                                particion.part_size = total_size
                                particion.part_name = name
                                particion.part_start = aux_size
                                aux_size += total_size
                                break
                            else:
                                message=("Error: espacio insuficiente")
                                return message
                    elif tipo == "E":
                        ebr = Struct.Structs.EBR()
                        if particion.part_status == "1":
                            aux_size += particion.part_size
                        elif particion.part_status == "0":
                            particion.part_status = "1"
                            particion.part_type = tipo
                            particion.part_fit = fit
                            particion.part_size = total_size
                            particion.part_name = name
                            particion.part_start = aux_size

                            ebr.part_status = "0"
                            ebr.part_fit = 'WF'
                            ebr.part_size = 0
                            ebr.part_name = 'null'
                            ebr.part_start = aux_size
                            ebr.part_next = -1
                            aux_size += total_size
                            break
                        elif particion.part_status == "D":
                            size_elim.sort()
                            size_elim = size_elim[0]
                            if size_elim >= total_size:
                                particion.part_status = "1"
                                particion.part_type = tipo
                                particion.part_fit = fit
                                particion.part_size = total_size
                                particion.part_name = name
                                particion.part_start = aux_size
                                
                                ebr.part_status = "0"
                                ebr.part_fit = 'WF'
                                ebr.part_size = 0
                                ebr.part_name = 'null'
                                ebr.part_start = aux_size
                                ebr.part_next = -1
                                aux_size += total_size
                                break
                            else:
                                message=("Error: espacio insuficiente")
                                return message        
                    elif tipo == "L":
                        exis=False
                        for particion in partitions:
                            if particion.part_type == "E":
                                exis=True
                                message = Disk.crearLogicas(particion.part_start, total_size, path, name, mbr.disk_fit,fit,particion.part_size)
                                return message
                        if not exis:
                            message=("No existe particion extendida")
                            return message
            elif mbr.disk_fit == "WF":
                ebr = Struct.Structs.EBR()
                aux_size = mbr_size
                for particion in partitions:
                    if tipo == "P":
                        if particion.part_status == "1":
                            aux_size += particion.part_size
                        elif particion.part_status == "0":
                            particion.part_status = "1"
                            particion.part_type = tipo
                            particion.part_fit = fit
                            particion.part_size = total_size
                            particion.part_name = name
                            particion.part_start = mbr_size + aux_size
                            aux_size += total_size
                            break
                        elif particion.part_status == "D":
                            size_elim.sort(reverse=True)
                            size_elim = size_elim[0]
                            if size_elim >= total_size:
                                particion.part_status = "1"
                                particion.part_type = tipo
                                particion.part_fit = fit
                                particion.part_size = total_size
                                particion.part_name = name
                                particion.part_start = mbr_size + aux_size
                                aux_size += total_size
                                break
                            else:
                                message=("Error: espacio insuficiente")
                                return message     

                    elif tipo == "E":
                        if particion.part_status == "1":
                            aux_size += particion.part_size
                        elif particion.part_status == "0":
                            particion.part_status = "1"
                            particion.part_type = tipo
                            particion.part_fit = fit
                            particion.part_size = total_size
                            particion.part_name = name
                            particion.part_start = mbr_size + aux_size

                            ebr.part_status = "0"
                            ebr.part_fit = 'WF'
                            ebr.part_size = 0
                            ebr.part_name = 'null'
                            ebr.part_start = aux_size
                            ebr.part_next = -1
                            aux_size += total_size
                            break
                        elif particion.part_status == "D":
                            size_elim.sort(reverse=True)
                            size_elim = size_elim[0]
                            if size_elim >= total_size:
                                particion.part_status = "1"
                                particion.part_type = tipo
                                particion.part_fit = fit
                                particion.part_size = total_size
                                particion.part_name = name
                                particion.part_start = mbr_size + aux_size

                                ebr.part_status = "0"
                                ebr.part_fit = 'WF'
                                ebr.part_size = 0
                                ebr.part_name = 'null'
                                ebr.part_start = aux_size
                                ebr.part_next = -1
                                aux_size += total_size
                                break
                            else:
                                message=("Error: espacio insuficiente")
                                return message     
                    elif tipo == "L":
                        exis=False
                        for particion in partitions:
                            if particion.part_type == "E":
                                exis=True
                                message = Disk.crearLogicas(particion.part_start, total_size, path, name, mbr.disk_fit,fit,particion.part_size)
                                return message
                        if not exis:
                            message=("No existe particion extendida")
                            return message
            
            try:
                with open(path, "rb+") as bfile:
                    bfile.write(mbr.__bytes__())
                    if tipo.lower() == "p":
                        message=("FDISK", "Particion primaria:",name,"creada correctamente")
                        return message
                    elif tipo.lower() == "e":
                        bfile.seek(ebr.part_start, 0)
                        bfile.write(ebr.__bytes__())
                        message=("FDISK", "partición extendida:", name, "creada correctamente")
                        return message
            except Exception as e:
                message=("Error: Error al crear el disco en la ruta: "+path)

        except ValueError as e: 
            message=("FDISK", "-size debe ser un entero")
        except Exception as e: 
            message=("FDISK", str(e))
        return message
        
    def crearLogicas(start, size, path, name, fit_disco,fit, size_completo):
        nlogicas= Struct.Structs.EBR()
        tmp= Struct.Structs.EBR()
        proceso=0
        tmp_inicio= start
        list_logicas=[]
        bandera= True
        try:
            with open(path, "rb") as file:
                while bandera:
                    file.seek(start)
                    ebr_data = file.read()
                    nlogicas.__setstate__(ebr_data)
                    auxiliar = Struct.Structs.EBR()
                    auxiliar.__setstate__(ebr_data)
                    list_logicas.append(auxiliar)
                    if nlogicas.part_name == name:
                        message=("Ya existe una particion logica con el nombre",name)
                        return message
                    if nlogicas.part_next == -1:
                        bandera = False
                    else:
                        proceso+= nlogicas.part_size
                        start = nlogicas.part_next 
        except Exception as e:
            message=("Ha ocurrido un error al crear la particion logica",e)
            return message
        
        if size_completo < proceso + size:
            message=("Error: espacio insuficiente para la particion logica")
            return message
        size_elim=[]
        for particion in list_logicas:
            if particion.part_status == 'D':
                size_elim.append(particion.part_size)

        if fit_disco == "FF":
            for particion in list_logicas:
                if(particion.part_status == "0"):
                    nlogicas.part_status= '1'
                    nlogicas.part_fit = fit
                    nlogicas.part_start = tmp_inicio
                    nlogicas.part_size = size
                    nlogicas.part_next = tmp_inicio + size
                    nlogicas.part_name = name
                    break
                elif(particion.part_status == "1"):
                    tmp_inicio += particion.part_size
                elif(particion.part_status == "D"):
                    size_elim = size_elim[0]
                    if size_elim >= size:
                        nlogicas.part_status= '1'
                        nlogicas.part_fit = fit
                        nlogicas.part_start = tmp_inicio
                        nlogicas.part_size = size
                        nlogicas.part_next = tmp_inicio + size
                        nlogicas.part_name = name
                        break
                    else:
                        message=("Error: espacio insuficiente para la particion logica")
                        return message
        elif fit_disco == "BF":
            for particion in list_logicas:
                if(particion.part_status == "0"):
                    nlogicas.part_status= '1'
                    nlogicas.part_fit = fit
                    nlogicas.part_start = tmp_inicio
                    nlogicas.part_size = size
                    nlogicas.part_next = tmp_inicio + size
                    nlogicas.part_name = name
                    break
                elif(particion.part_status == "1"):
                    tmp_inicio += particion.part_size
                elif(particion.part_status == "D"):
                    size_elim.sort()
                    size_elim = size_elim[0]
                    if size_elim >= size:
                        nlogicas.part_status= '1'
                        nlogicas.part_fit = fit
                        nlogicas.part_start = tmp_inicio
                        nlogicas.part_size = size
                        nlogicas.part_next = tmp_inicio + size
                        nlogicas.part_name = name
                        break
                    else:
                        message=("Error: espacio insuficiente para la particion logica")
                        return message
        elif fit_disco == "WF":
            for particion in list_logicas:
                if(particion.part_status == "0"):
                    nlogicas.part_status= '1'
                    nlogicas.part_fit = fit
                    nlogicas.part_start = tmp_inicio
                    nlogicas.part_size = size
                    nlogicas.part_next = tmp_inicio + size
                    nlogicas.part_name = name
                    break
                elif(particion.part_status == "1"):
                    tmp_inicio += particion.part_size
                elif(particion.part_status == "D"):
                    size_elim.sort(reverse=True)
                    size_elim = size_elim[0]
                    if size_elim >= size:
                        nlogicas.part_status= '1'
                        nlogicas.part_fit = fit
                        nlogicas.part_start = tmp_inicio
                        nlogicas.part_size = size
                        nlogicas.part_next = tmp_inicio + size
                        nlogicas.part_name = name
                        break
                    else:
                        message=("Error: espacio insuficiente para la particion logica")
                        return message
                    
        tmp.part_status = '0'
        tmp.part_fit = 'WF'
        tmp.part_start = nlogicas.part_next
        tmp.part_size = 0
        tmp.part_next = -1
        tmp.part_name = ''
        try:
            with open(path, "rb+") as file:
                file.seek(tmp_inicio)
                file.write(nlogicas.__bytes__())
                file.seek(tmp_inicio + size)
                file.write(tmp.__bytes__())
                message=(f"FDISK","Partición logica", name, "creada exitosamente")
                return message
        except Exception as e:
            print(e)
            message=("Error: Error al crear la partición en el disco: "+path)

    def command_fdisk_delete(path, name):
        if not os.path.exists(path):
                raise RuntimeError("Error: No existe el disco en la ruta: "+path)
                return
        try:
            mbr = Struct.Structs.MBR()
            with open(path, "rb") as file:
                mbr_data = file.read()
                mbr.mbr_tamano = struct.unpack("<i", mbr_data[:4])[0]
                mbr.mbr_fecha_creacion = struct.unpack("<i", mbr_data[4:8])[0]
                mbr.mbr_disk_signature = struct.unpack("<i", mbr_data[8:12])[0]
                mbr.disk_fit = mbr_data[12:14].decode('utf-8')
                
                partition_size = struct.calcsize("<iii16s")*4
                partition_data = mbr_data[14:14 + partition_size]
                mbr.mbr_Partition_1.__setstate__(partition_data[0:28]) 
                mbr.mbr_Partition_2.__setstate__(partition_data[28:56]) 
                mbr.mbr_Partition_3.__setstate__(partition_data[56:84]) 
                mbr.mbr_Partition_4.__setstate__(partition_data[84:112])
        except Exception as e:
            print(e)

        partitions = [mbr.mbr_Partition_1, mbr.mbr_Partition_2, mbr.mbr_Partition_3, mbr.mbr_Partition_4]
        for particion in partitions:
            if(particion.part_type == "E"):
                if(particion.part_name== name):
                    with open(path, "rb+") as file:
                        file.seek(particion.part_start)
                        file.write(b'\x00'*particion.part_size)
                    particion.part_status = "D"
                    particion.part_fit = "WF"
                    particion.part_size = 0
                    particion.part_start = 0
                    particion.part_name = ""
                    particion.part_type = "P"
                    break
                start=particion.part_start
                nlogicas= Struct.Structs.EBR()
                bandera= True
                try:
                    with open(path, "rb+") as file:
                        while bandera:
                            file.seek(start)
                            ebr_data = file.read()
                            nlogicas.__setstate__(ebr_data)
                            if nlogicas.part_name == name:
                                principio = nlogicas.part_start
                                file.seek(start)
                                file.write(b'\x00'*nlogicas.part_size)
                                
                                start = nlogicas.part_next
                                nlogicas.part_status = 'D'
                                nlogicas.part_fit = 'WF'
                                nlogicas.part_start = 0
                                nlogicas.part_size = 0
                                nlogicas.part_next = -1
                                nlogicas.part_name = ''

                                file.seek(principio)
                                file.write(nlogicas.__bytes__())
                                print("FDISK","Particion logica",name,"eliminada exitosamente")
                                return
                            if nlogicas.part_next == -1:
                                bandera = False
                            else:
                                start = nlogicas.part_next 
                except Exception as e:
                    print("Ha ocurrido un error al eliminar la particion logica",e)
            elif(particion.part_type == 'P'):
                if(particion.part_name== name):
                    with open(path, "rb+") as file:
                        file.seek(particion.part_start)
                        file.write(b'\x00'*particion.part_size)
                    particion.part_status = "D"
                    particion.part_fit = "WF"
                    particion.part_size = 0
                    particion.part_start = 0
                    particion.part_name = ""
                    particion.part_type = "P"
        try:
            with open(path, "rb+") as file:
                file.write(mbr.__bytes__())
                print("FDISK","Particion",name,"eliminada exitosamente")
        except Exception as e:
            print("Error: Error al crear el disco en la ruta: "+path)
    
    def command_mount(path, name):
        particiones = Disk.leer_archivo(path)
        lista_nombres = []
        index = 0
        for particion in particiones:
            index += 1
            if particion.part_name == name:
                break
        for particion in particiones:
            lista_nombres.append(particion.part_name)

        if name not in lista_nombres:
            message=("Error: No existe partición con el nombre: "+name)
            return message
        else:
            nombre_disco = os.path.splitext(os.path.basename(path))[0]
            carnet = '44'
            id = carnet + str(index) + nombre_disco 
            
            if id in mounted_partitions:
                message=("Error: La partición ya se encuentra montada.\n")
                message = message + ("Particiones montadas: ")
                for i in mounted_partitions:
                    message= message + (i+", ")
                return message
            else:
                mounted_partitions.append(id)
                message=("Particion montada exitosamente con el id: "+id+"\n")
                message = message + ("Particiones montadas: ")
                for i in mounted_partitions:
                    message= message + (i+", ")
        return message

    def command_unmount(id):
        if id not in mounted_partitions:
            print("Error: No existe una partición montada con el id: "+id)
            return
        else:
            mounted_partitions.remove(id)
            print("Partición desmontada exitosamente.")
            for i in mounted_partitions:
                print("\t\t"+i)
        return mounted_partitions

    def leer_archivo(path):
        if not os.path.exists(path):
                message=("Error: No existe el disco en la ruta: "+path)
                return message
        try:
            mbr = Struct.Structs.MBR()
            with open(path, "rb") as file:
                mbr_data = file.read()
                mbr.mbr_tamano = struct.unpack("<i", mbr_data[:4])[0]
                mbr.mbr_fecha_creacion = struct.unpack("<i", mbr_data[4:8])[0]
                mbr.mbr_disk_signature = struct.unpack("<i", mbr_data[8:12])[0]
                mbr.disk_fit = mbr_data[12:14].decode('utf-8')
                
                partition_size = struct.calcsize("<iii16s")*4
                partition_data = mbr_data[14:14 + partition_size]
                mbr.mbr_Partition_1.__setstate__(partition_data[0:28]) 
                mbr.mbr_Partition_2.__setstate__(partition_data[28:56]) 
                mbr.mbr_Partition_3.__setstate__(partition_data[56:84]) 
                mbr.mbr_Partition_4.__setstate__(partition_data[84:112])
        except Exception as e:
            print(e)

        partitions = [mbr.mbr_Partition_1, mbr.mbr_Partition_2, mbr.mbr_Partition_3, mbr.mbr_Partition_4]
        lista_particiones = []
        for particion in partitions:
                lista_particiones.append(particion)

        return lista_particiones

    def imp(path):
        try:
            mbr = Struct.Structs.MBR()
            with open(path, "rb") as file:
                mbr_data = file.read()
                mbr.mbr_tamano = struct.unpack("<i", mbr_data[:4])[0]
                mbr.mbr_fecha_creacion = struct.unpack("<i", mbr_data[4:8])[0]
                mbr.mbr_disk_signature = struct.unpack("<i", mbr_data[8:12])[0]
                mbr.disk_fit = mbr_data[12:14].decode('utf-8')
                    
                partition_size = struct.calcsize("<iii16s")*4
                partition_data = mbr_data[14:14 + partition_size]
                mbr.mbr_Partition_1.__setstate__(partition_data[0:28]) 
                mbr.mbr_Partition_2.__setstate__(partition_data[28:56]) 
                mbr.mbr_Partition_3.__setstate__(partition_data[56:84]) 
                mbr.mbr_Partition_4.__setstate__(partition_data[84:112])
                print("TamaÃ±o: "+str(mbr.mbr_tamano))
                print("Fecha: "+str(mbr.mbr_fecha_creacion))
                print("Signature: "+str(mbr.mbr_disk_signature))
                print("Fit: "+str(mbr.disk_fit))
                print("Particion 1:")
                print("\tStatus: "+str(mbr.mbr_Partition_1.part_status))
                print("\tType: "+str(mbr.mbr_Partition_1.part_type))
                print("\tFit: "+str(mbr.mbr_Partition_1.part_fit))
                print("\tStart: "+str(mbr.mbr_Partition_1.part_start))
                print("\tSize: "+str(mbr.mbr_Partition_1.part_size))
                print("\tName: "+str(mbr.mbr_Partition_1.part_name))
                print("Particion 2:")
                print("\tStatus: "+str(mbr.mbr_Partition_2.part_status))
                print("\tType: "+str(mbr.mbr_Partition_2.part_type))
                print("\tFit: "+str(mbr.mbr_Partition_2.part_fit))
                print("\tStart: "+str(mbr.mbr_Partition_2.part_start))
                print("\tSize: "+str(mbr.mbr_Partition_2.part_size))
                print("\tName: "+str(mbr.mbr_Partition_2.part_name))
                print("Particion 3:")
                print("\tStatus: "+str(mbr.mbr_Partition_3.part_status))
                print("\tType: "+str(mbr.mbr_Partition_3.part_type))
                print("\tFit: "+str(mbr.mbr_Partition_3.part_fit))
                print("\tStart: "+str(mbr.mbr_Partition_3.part_start))
                print("\tSize: "+str(mbr.mbr_Partition_3.part_size))
                print("\tName: "+str(mbr.mbr_Partition_3.part_name))
                print("Particion 4:")
                print("\tStatus: "+str(mbr.mbr_Partition_4.part_status))
                print("\tType: "+str(mbr.mbr_Partition_4.part_type))
                print("\tFit: "+str(mbr.mbr_Partition_4.part_fit))
                print("\tStart: "+str(mbr.mbr_Partition_4.part_start))
                print("\tSize: "+str(mbr.mbr_Partition_4.part_size))
                print("\tName: "+str(mbr.mbr_Partition_4.part_name))
        except Exception as e:
            print(e)

    def reporte_MBR(path):
        try:
            if not os.path.exists(path):
                    message=("Error: No existe el disco en la ruta: "+path)
                    return message
            nombre_archivo = path.split('/')[-1]
            nombre_archivo = nombre_archivo.split('.')[0]

            try:
                mbr = Struct.Structs.MBR()
                with open(path, "rb") as file:
                    mbr_data = file.read()
                    mbr.mbr_tamano = struct.unpack("<i", mbr_data[:4])[0]
                    mbr.mbr_fecha_creacion = struct.unpack("<i", mbr_data[4:8])[0]
                    mbr.mbr_disk_signature = struct.unpack("<i", mbr_data[8:12])[0]
                    mbr.disk_fit = mbr_data[12:14].decode('utf-8')
                    
                    partition_size = struct.calcsize("<iii16s")*4
                    partition_data = mbr_data[14:14 + partition_size]
                    mbr.mbr_Partition_1.__setstate__(partition_data[0:28]) 
                    mbr.mbr_Partition_2.__setstate__(partition_data[28:56]) 
                    mbr.mbr_Partition_3.__setstate__(partition_data[56:84]) 
                    mbr.mbr_Partition_4.__setstate__(partition_data[84:112])
            except Exception as e:
                pass
                
            partitions = [mbr.mbr_Partition_1, mbr.mbr_Partition_2, mbr.mbr_Partition_3, mbr.mbr_Partition_4]
            graph = gv.Digraph('G', format='jpg')
            graphviz = ''
            graphviz += 'node [shape=plaintext];\n'
            graphviz += 'table [label=<\n'
            graphviz += '<table border="1" cellborder="1" cellspacing="0">\n'
            graphviz += '<tr> \n <td colspan="4" bgcolor="lightblue">Reporte de MBR</td>\n</tr>\n'
            graphviz += f'<tr>\n <td>mbr_tamano</td>\n<td>{str(mbr.mbr_tamano)}</td>\n </tr>\n'
            graphviz += f'<tr>\n <td>mbr_fecha</td>\n<td>{str(mbr.mbr_fecha_creacion)}</td>\n </tr>\n'
            graphviz += f'<tr>\n <td>mbr_asignature</td>\n<td>{str(mbr.mbr_disk_signature)}</td>\n </tr>\n'
            graphviz += f'<tr>\n <td>mbr_fit</td>\n<td>{mbr.disk_fit}</td>\n </tr>\n'
            for particion in partitions:
                if particion.part_type == "E":
                    graphviz += '<tr> \n <td colspan="4" bgcolor="lightblue">Particion Extendida</td>\n</tr>\n'
                    graphviz += f'<tr>\n <td>part_status</td>\n<td>{particion.part_status}</td>\n </tr>\n'
                    graphviz += f'<tr>\n <td>part_type</td>\n<td>{particion.part_type}</td>\n </tr>\n'
                    graphviz += f'<tr>\n <td>part_fit</td>\n<td>{particion.part_fit}</td>\n </tr>\n'
                    graphviz += f'<tr>\n <td>part_start</td>\n<td>{particion.part_start}</td>\n </tr>\n'
                    graphviz += f'<tr>\n <td>part_size</td>\n<td>{particion.part_size}</td>\n </tr>\n'
                    graphviz += f'<tr>\n <td>part_name</td>\n<td>{particion.part_name}</td>\n </tr>\n'

                    nlogicas= Struct.Structs.EBR()
                    bandera = True
                    start = particion.part_start
                    try:
                        with open(path, "rb") as file:
                            while bandera:
                                file.seek(start)
                                ebr_data = file.read()
                                nlogicas.__setstate__(ebr_data)
                                if nlogicas.part_next == -1:
                                    graphviz += '<tr> \n <td colspan="4" bgcolor="red">Particion Logica</td>\n</tr>\n'
                                    graphviz += f'<tr>\n <td>part_status</td>\n<td>{nlogicas.part_status}</td>\n </tr>\n'
                                    graphviz += f'<tr>\n <td>part_next</td>\n<td>{nlogicas.part_next}</td>\n </tr>\n'
                                    graphviz += f'<tr>\n <td>part_fit</td>\n<td>{nlogicas.part_fit}</td>\n </tr>\n'
                                    graphviz += f'<tr>\n <td>part_start</td>\n<td>{nlogicas.part_start}</td>\n </tr>\n'
                                    graphviz += f'<tr>\n <td>part_size</td>\n<td>{nlogicas.part_size}</td>\n </tr>\n'
                                    graphviz += f'<tr>\n <td>part_name</td>\n<td>{nlogicas.part_name}</td>\n </tr>\n'
                                    bandera = False
                                else:
                                    graphviz += '<tr> \n <td colspan="4" bgcolor="red">Particion Logica</td>\n</tr>\n'
                                    graphviz += f'<tr>\n <td>part_status</td>\n<td>{nlogicas.part_status}</td>\n </tr>\n'
                                    graphviz += f'<tr>\n <td>part_next</td>\n<td>{nlogicas.part_next}</td>\n </tr>\n'
                                    graphviz += f'<tr>\n <td>part_fit</td>\n<td>{nlogicas.part_fit}</td>\n </tr>\n'
                                    graphviz += f'<tr>\n <td>part_start</td>\n<td>{nlogicas.part_start}</td>\n </tr>\n'
                                    graphviz += f'<tr>\n <td>part_size</td>\n<td>{nlogicas.part_size}</td>\n </tr>\n'
                                    graphviz += f'<tr>\n <td>part_name</td>\n<td>{nlogicas.part_name}</td>\n </tr>\n'
                                    start = nlogicas.part_next 
                    except Exception as e:
                        pass
                else:
                    graphviz += '<tr> \n <td colspan="4" bgcolor="lightblue">Particion Primaria</td>\n</tr>\n'
                    graphviz += f'<tr>\n <td>part_status</td>\n<td>{particion.part_status}</td>\n </tr>\n'
                    graphviz += f'<tr>\n <td>part_type</td>\n<td>{particion.part_type}</td>\n </tr>\n'
                    graphviz += f'<tr>\n <td>part_fit</td>\n<td>{particion.part_fit}</td>\n </tr>\n'
                    graphviz += f'<tr>\n <td>part_start</td>\n<td>{particion.part_start}</td>\n </tr>\n'
                    graphviz += f'<tr>\n <td>part_size</td>\n<td>{particion.part_size}</td>\n </tr>\n'
                    graphviz += f'<tr>\n <td>part_name</td>\n<td>{particion.part_name}</td>\n </tr>\n'

            graphviz += '</table>\n'
            graphviz += '>,];\n'

            graph.body.append(graphviz)

            # Guardar el gráfico como una imagen PNG
            graph.render(filename=os.path.join("./Reportes","ReporteMBR_"+nombre_archivo))
            try:
                s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
                s3.upload_file("./Reportes/ReporteMBR_"+nombre_archivo+".jpg", bucket_name,"Reportes/"+"ReporteMBR_"+ nombre_archivo+".jpg")
                lista_nombres =("ReporteMBR_"+ nombre_archivo+".jpg")
                return lista_nombres
            except Exception as e:
                print(e)
                pass

        except Exception as e:
            pass

    def reporte_Disk(path):
        try:
            if not os.path.exists(path):
                    message=("Error: No existe el disco en la ruta: "+path)
                    return message
            nombre_archivo = path.split('/')[-1]
            nombre_archivo = nombre_archivo.split('.')[0]
            try:
                mbr = Struct.Structs.MBR()
                with open(path, "rb") as file:
                    mbr_data = file.read()
                    mbr.mbr_tamano = struct.unpack("<i", mbr_data[:4])[0]
                    mbr.mbr_fecha_creacion = struct.unpack("<i", mbr_data[4:8])[0]
                    mbr.mbr_disk_signature = struct.unpack("<i", mbr_data[8:12])[0]
                    mbr.disk_fit = mbr_data[12:14].decode('utf-8')
                    
                    partition_size = struct.calcsize("<iii16s")*4
                    partition_data = mbr_data[14:14 + partition_size]
                    mbr.mbr_Partition_1.__setstate__(partition_data[0:28]) 
                    mbr.mbr_Partition_2.__setstate__(partition_data[28:56]) 
                    mbr.mbr_Partition_3.__setstate__(partition_data[56:84]) 
                    mbr.mbr_Partition_4.__setstate__(partition_data[84:112])
            except Exception as e:
                pass

            
            total = mbr.mbr_tamano
            mbr_size = 14 + struct.calcsize("<iii16s")*4
            partitions = [mbr.mbr_Partition_1, mbr.mbr_Partition_2, mbr.mbr_Partition_3, mbr.mbr_Partition_4]
            graph = gv.Digraph('G', format='jpg')
            graphviz = ''
            graphviz += 'node [shape=plaintext];\n'
            graphviz += 'table [label=<\n'
            graphviz += '<table border="1" cellborder="1" cellspacing="3">\n'
            graphviz += '<tr> \n<td colspan="4">MBR</td>\n'

            for particion in partitions:
                if particion.part_type == "E":
                    porcentaje = particion.part_size * 100 / total
                    graphviz += '<td colspan="4">\n'
                    graphviz += '<table border="20" cellborder="1" cellspacing="0">\n'
                    graphviz += f'<tr> \n <td colspan="2"> Extendida {porcentaje}% del disco</td>\n</tr>\n'

                    nlogicas= Struct.Structs.EBR()
                    bandera = True
                    start = particion.part_start
                    graphviz+='<tr>\n'
                    size_logicas=0
                    try:
                        with open(path, "rb") as file:
                            while bandera:
                                file.seek(start)
                                ebr_data = file.read()
                                nlogicas.__setstate__(ebr_data)
                                if nlogicas.part_next == -1:
                                    if nlogicas.part_status == "D":
                                        porcentaje = nlogicas.part_size * 100 / total
                                        graphviz += f'<td> Libre {porcentaje}% del disco</td>\n'
                                        size_logicas += nlogicas.part_size
                                    else:
                                        
                                        porcentaje = (particion.part_size - size_logicas) * 100 / total
                                        graphviz += f'<td > Libre {porcentaje}% del disco</td>\n'
                                        
                                    bandera = False
                                else:
                                    graphviz += '<td> EBR </td>\n'
                                    porcentaje = nlogicas.part_size * 100 / total
                                    graphviz += f'<td> Logica {porcentaje}% del disco</td>\n'
                                    size_logicas += nlogicas.part_size
                                    start = nlogicas.part_next 
                    except Exception as e:
                        pass
                    graphviz+='</tr>\n'
                    graphviz+='</table>\n'
                    graphviz += '</td>\n'
                else:
                    if particion.part_status == "D":
                        porcentaje = particion.part_size * 100 / total
                        graphviz += f'<td colspan="4">Libre {porcentaje}% del disco</td>\n'
                    else:
                        porcentaje = particion.part_size * 100 / total
                        graphviz += f'<td colspan="4">Primaria {porcentaje}% del disco</td>\n'

            graphviz += '</tr>\n'
            graphviz += '</table>\n'
            graphviz += '>,];\n'

            graph.body.append(graphviz)

            # Guardar el gráfico como una imagen PNG
            graph.render(filename=os.path.join("./Reportes","ReporteDisk_"+nombre_archivo))
            try:
                s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
                s3.upload_file("./Reportes/ReporteDisk_"+nombre_archivo+".jpg", bucket_name,"Reportes/"+"ReporteDisk_"+ nombre_archivo+".jpg")
                lista_nombres=("ReporteDisk_"+ nombre_archivo+".jpg")
                return lista_nombres
            except Exception as e:
                print(e)
                pass
        except Exception as e:
            pass

    
