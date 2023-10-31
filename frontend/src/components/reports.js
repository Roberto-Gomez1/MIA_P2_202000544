import React, { useState, useEffect } from 'react';
function Reports_Card() {
  const [reportNames, setReportNames] = useState([]);
  const apiUrl = process.env.REACT_APP_API_URL;

  useEffect(() => {
    // Realiza la solicitud GET para obtener la lista de nombres de informes
    const fetchReportNames = async () => {
      try {
        const response = await fetch(apiUrl + '/reporte', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        const data = await response.json();
        setReportNames(data.mensaje);
        console.log(data.mensaje);
        console.log("Lista"+reportNames)
      } catch (error) {
        console.error(`Error en la solicitud: ${error}`);
      }
    };

    fetchReportNames();
  }, []);

  return (
    <div className="card mt-4">
      <h5 className="card-header">
        <div className='d-flex justify-content-between'>
            <p>Imagenes</p>
        </div>
      </h5>
      <div className="card-body">
          {reportNames.map((reportName, index) => (
            <center>
              <div key={index}>
                <p>{reportName}</p>
                <img src={`https://mia-p2-202000544.s3.us-east-2.amazonaws.com/Reportes/${reportName}`} class="img-fluid" alt="..."></img>
                </div>
          </center>
          ))}
      </div>
    </div>
  );
}

export default Reports_Card;
