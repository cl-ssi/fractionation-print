import sys
import json
import win32print
import socket
import logging
from logging.handlers import RotatingFileHandler
from rut_chile import format_rut_without_dots
from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

app = Flask(__name__)
CORS(app, resources={
    r"/print": {
        "origins": "*",                # Permite cualquier origen [[2]]
        "methods": ["POST", "OPTIONS"],# Habilita métodos necesarios
        "allow_headers": ["*"],        # Permite todos los headers
        "supports_credentials": False   # Si necesitas cookies/autenticación
    }
})

# Configuración de logging
handler = RotatingFileHandler('error.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.ERROR)
app.logger.addHandler(handler)

MAPPING = {
    'nombre': 'nombre',
    'rut': 'rut',
    'dci': 'dci',
    'forma': 'forma',
    'via': 'via',
    'dosis': 'dosis',
    'cantidad': 'cantidad',
    'correlativo': 'correlativo',
    'registro': 'registro',
    'lote': 'lote',
    'vence': 'vence',
    'farmacia': 'farmacia',
    'numero_farmacia': 'numero_farmacia',
    'direccion_farmacia': 'direccion_farmacia'
}

def get_zpl(dosificacion, nombre, rut, dci, forma, via, dosis, cantidad, correlativo, registro, lote, vence, farmacia, numero_farmacia, direccion_farmacia):
    return f"""
\x10CT~~CD,~CC^~CT~
^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR6,6~SD15^JUS^LRN^CI0^XZ
^XA
^MMT
^PW448
^LL0320
^LS0
^FT442,265^A0I,25,24^FH\\^FD{nombre}^FS
^FT158,264^A0I,25,24^FH\\^FD{format_rut_without_dots(rut)}^FS
^FT442,210^A0I,25,24^FH\\^FD{dci}^FS
^FT241,210^A0I,25,24^FH\\^FD{forma}^FS
^FT77,210^A0I,25,24^FH\\^FD{dosis}^FS
^FT442,185^A0I,17,16^FH\\^FDDCI (PRINCIPIO ACTIVO)^FS
^FT241,185^A0I,17,16^FH\\^FDF.FARMACEUTICA^FS
^FT77,185^A0I,17,16^FH\\^FDDOSIS^FS
^FT442,99^A0I,25,24^FH\\^FD{registro}^FS
^FT261,99^A0I,25,24^FH\\^FD{lote}^FS
^FT92,99^A0I,25,24^FH\\^FD{vence}^FS
^FT442,74^A0I,17,16^FH\\^FDN\\A7 REG. SANITARIO^FS
^FT261,74^A0I,17,16^FH\\^FDN\\A7 LOTE/SERIE^FS
^FT92,74^A0I,17,16^FH\\^FDFECHA VENC.^FS
^FT339,300^A0I,20,19^FH\\^FDCORRELATIVO N\\A7^FS
^FT441,128^A0I,17,16^FH\\^FDDOSIFICACION^FS
^FT175,128^A0I,17,16^FH\\^FDCANTIDAD^FS
^FT78,128^A0I,17,16^FH\\^FDVIA ADM^FS
^FT175,153^A0I,25,24^FH\\^FD{cantidad}^FS
^FT78,153^A0I,25,24^FH\\^FD{via}^FS
^FT441,153^A0I,25,24^FH\\^FD{dosificacion}^FS
^FT441,239^A0I,17,16^FH\\^FDNOMBRE PACIENTE^FS
^FT158,239^A0I,17,16^FH\\^FDRUT^FS
^FT186,297^A0I,23,21^FH\\^FD{correlativo}^FS
^FT442,51^A0I,17,14^FH\\^FD{farmacia}. {numero_farmacia}. {direccion_farmacia}.^FS
^FT398,36^A0I,14,12^FB349,1,0,C^FH\\^FDPara mayor informaci\\A2n, consulte a su prescriptor o Q. Farmac\\82utico. ^FS
^FT398,19^A0I,14,12^FB349,1,0,C^FH\\^FDVisite www.ispch.cl y www.minsal.cl^FS
^FO173,259^GB271,0,3^FS
^FO5,258^GB153,0,3^FS
^FO259,204^GB183,0,3^FS
^FO5,205^GB72,0,3^FS
^FO85,205^GB156,0,3^FS
^FO89,148^GB86,0,3^FS
^FO6,148^GB72,0,3^FS
^FO293,93^GB149,0,3^FS
^FO128,93^GB133,0,3^FS
^FO6,93^GB86,0,3^FS
^FO185,147^GB256,0,3^FS
^PQ1,0,1,Y^XZ
"""

def print_labels(lines, dosificaciones, config):
    conn = config.get("conn", "network")
    printer_name = config.get("printer_name", "zebra")
    host = config.get("host", "192.168.1.23")
    port = config.get("port", 9100)

    if conn == "usb":
        printer = win32print.OpenPrinter(printer_name)
        win32print.StartDocPrinter(printer, 1, ('MonkeyPrint', None, 'RAW'))
    elif conn == "network":
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
    else:
        raise ValueError("Invalid connection type")

    for line, dosificacion in zip(lines, dosificaciones):
        fields = {key: line[value] for key, value in MAPPING.items()}
        fields['rut'] = format_rut_without_dots(fields['rut'])        
        zpl = get_zpl(dosificacion, **fields)

        if conn == "usb":
            win32print.StartPagePrinter(printer)
            win32print.WritePrinter(printer, zpl.encode())
            win32print.EndPagePrinter(printer)
        elif conn == "network":
            sock.send(zpl.encode())

    if conn == "usb":
        win32print.EndDocPrinter(printer)
        win32print.ClosePrinter(printer)
    elif conn == "network":
        sock.close()
        
@app.route('/', methods=["GET"])
def index1():
    return 'hi'

@app.route('/print', methods=['POST'])
def print_endpoint():
    try:        
        raw_data = request.data.decode('utf-8')        
        data = json.loads(raw_data)  # Parsear JSON manualmente
        lines = data['lines']        
        dosificaciones = data['dosificaciones']
        config = data.get('config', {})
        required_keys = MAPPING.values()
        for line in lines:
            missing = [key for key in required_keys if key not in line]
            if missing:
                raise ValueError(f"Faltan campos en 'lines': {missing}")

        if len(lines) != len(dosificaciones):
            return jsonify({"error": "Number of lines and dosificaciones must match"}), 400

        print_labels(lines, dosificaciones, config)
        return jsonify({"message": "Printing successful"}), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format"}), 400
    except Exception as e:
        app.logger.error(f"Error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal Server Error"}), 500

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5050, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("Servidor detenido.")
    except Exception as e:
        app.logger.error(f"Error crítico: {str(e)}")