import React, { useState, useRef } from 'react';

function Card() {

    const [results, setResults] = useState('');
    const [commands, setCommands] = useState('');
    const [isPaused, setIsPaused] = useState(false);
    const [isDelete, setIsDelete] = useState(false);
    const [commands_list, setCommands_list] = useState([]);
    const textAreaRef = useRef(null);
    const apiUrl = process.env.REACT_APP_API_URL;

  
    const handleFileChange = (e) => {
      const file = e.target.files[0];
      const reader = new FileReader();
  
      reader.onload = (event) => {
        setCommands(event.target.result);
      };
  
      if (file) {
        reader.readAsText(file);
      }
    };

    const handleTextAreaKeyPress = (event) => {
        if (event.key === 'Enter') {
            if(isPaused){
                sendCommands(commands_list);
            }
        }
        else if(event.key === 's'){
            if(isDelete){
                sendCommands(commands_list);
            }
        }
        else if(event.key === 'n'){
            if(isDelete){
                setResults(prevResults => prevResults + `>>>> RMDISK: Eliminacion del disco cancelada correctamente <<<<\n`);
                for (let i = 0; i < commands_list.length; i++) {
                    const command = commands_list[i].trim();
                    if (command.startsWith('rrmdisk')) {
                        setCommands_list(commands_list.slice(i+1, commands_list.length));
                        commands_list[i] = ""
                        break;
                    }
                }   
                sendCommands(commands_list);
            }
        }
        
    };

    const sendCommands = async (commands) => {
        for (let i = 0; i < commands.length; i++) {
            const command = commands[i].trim();
        
            if (command) { // Evita enviar líneas en blanco
                setCommands_list(commands.slice(i+1, commands.length));
                if(command == 'pause'){
                    setIsPaused(true);
                    setResults(prevResults => prevResults + `Presiona "Enter" para continuar\n`);
                    break;
                }
                else if(command.startsWith('rmdisk')){
                    setIsDelete(true);
                    setResults(prevResults => prevResults + `¿Está seguro que desea eliminar el disco? (S/N): \n`);
                    commands[i] = "r"+command;
                    setCommands_list(commands.slice(i, commands.length));
                    break;
                }
                try {
                    const response = await fetch(apiUrl +'/execute', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ command }),
                    });
            
                    const data = await response.json();
                    setResults(prevResults => prevResults + `${data.mensaje}\n`);
                } catch (error) {
                    console.error(`Error en la solicitud ${i + 1}: ${error}`);
                }
            }
        }
    };

    const handleSubmit = () => {
        //Para enfocar el textarea
        textAreaRef.current.focus();
        //Para limpiar el textarea
        setResults('');
        //Para dividir los comandos por salto de línea
        const commandLines = commands.split('\n');
        //Actualizamos la lista de comandos y enviamos los comandos
        setCommands_list(commandLines);
        sendCommands(commandLines);
    };


  return (
    <div className="card-mt-4">
      <h5 className="card-header">
        <div className='d-flex justify-content-between'>
            <p>Consola de Archivos</p>
            <div>
                <input class="form-control" type="file" id="formFile" onChange={handleFileChange}></input>
            </div>
        </div>
      </h5>
      <div className="card-body">
        <div className="d-flex flex-row-reverse">
        </div>
        <div className="mb-3">
            <label className="form-label">Codigo a analizar</label>
            <textarea 
                className="form-control" 
                placeholder="Deposito de comandos" 
                style={{height: 200}}
                value={commands}
                onChange={(e) => setCommands(e.target.value)}
            ></textarea>
        </div>
        <div className="mb-3">
            <label className="form-label">Consola de Salida</label>
            <textarea 
                className="form-control" 
                placeholder="Resulado de la ejecución" 
                readOnly
                ref={textAreaRef}
                style={{height: 200}} 
                value={results}
                onKeyDown={handleTextAreaKeyPress}
            ></textarea>
        </div>
        <button className="btn btn-primary mt-3" onClick={handleSubmit}>Enviar</button>
      </div>
    </div>
  );
}

export default Card;
