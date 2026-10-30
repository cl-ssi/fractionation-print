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

# Ancho aproximado de cada caracter en la fuente 0 de Zebra, como fraccion del ancho de fuente.
# Es una estimacion conservadora: si el texto no cabe se recorta con "..."
NARROW_CHARS = set(" .,:;'!|-/()[]Iijlft1")
WIDE_CHARS = set("MW@%mw")

def text_width(text, font_width):
    total = 0
    for c in text:
        if c in NARROW_CHARS:
            total += 0.35
        elif c in WIDE_CHARS:
            total += 0.85
        elif c.isupper() or c.isdigit():
            total += 0.6
        else:
            total += 0.5
    return total * font_width

def fit(text, max_width, font_width=24):
    text = str(text).strip()
    if text_width(text, font_width) <= max_width:
        return text
    while text and text_width(text + '...', font_width) > max_width:
        text = text[:-1]
    return text.rstrip() + '...'

def column_widths(needs, total):
    # Reparte el ancho segun lo que necesita cada columna: las que necesitan
    # menos que su parte justa reciben solo eso, el resto se reparte entre las demas.
    if sum(needs) <= total:
        extra = (total - sum(needs)) / len(needs)
        return [int(n + extra) for n in needs]
    widths = [0] * len(needs)
    pending = list(range(len(needs)))
    remaining = total
    while pending:
        share = remaining / len(pending)
        small = [i for i in pending if needs[i] <= share]
        if not small:
            break
        for i in small:
            widths[i] = needs[i]
            remaining -= needs[i]
            pending.remove(i)
    for i in pending:
        widths[i] = remaining / len(pending)
    return [int(w) for w in widths]

def zpl_row(value_y, columns, left=6, right=442, gap=8):
    # columns: lista de (valor, rotulo_zpl, rotulo_texto)
    needs = [max(text_width(str(value).strip(), 24), text_width(label_text, 16)) + 4
             for value, _, label_text in columns]
    widths = column_widths(needs, right - left - gap * (len(columns) - 1))
    out = []
    x = left
    for (value, label_zpl, _), width in zip(columns, widths):
        out.append(f"^FT{448 - x},{value_y}^A0I,25,24^FH\\^FD{fit(value, width)}^FS")
        out.append(f"^FT{448 - x},{value_y - 25}^A0I,17,16^FH\\^FD{label_zpl}^FS")
        out.append(f"^FO{448 - x - width},{value_y - 6}^GB{width},0,3^FS")
        x += width + gap
    return "\n".join(out)

def get_zpl(dosificacion, nombre, rut, dci, forma, via, dosis, cantidad, correlativo, registro, lote, vence, farmacia, numero_farmacia, direccion_farmacia):
    fila_dosis = zpl_row(153, [
        (dosis, "DOSIS", "DOSIS"),
        (dosificacion, "DOSIFICACION", "DOSIFICACION"),
        (cantidad, "CANTIDAD", "CANTIDAD"),
        (via, "VIA ADM", "VIA ADM"),
    ])
    fila_registro = zpl_row(99, [
        (registro, "N\\A7 REG. SANITARIO", "No REG. SANITARIO"),
        (lote, "N\\A7 LOTE/SERIE", "No LOTE/SERIE"),
        (vence, "FECHA VENC.", "FECHA VENC."),
    ])
    farmacia_linea = f"{farmacia}. {numero_farmacia}. {direccion_farmacia}."
    return f"""
\x10CT~~CD,~CC^~CT~
^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA^PR6,6~SD15^JUS^LRN^CI0^XZ
^XA
^MMT
^PW448
^LL0320
^LS0
^FT339,300^A0I,20,19^FH\\^FDCORRELATIVO N\\A7^FS
^FT186,297^A0I,23,21^FH\\^FD{fit(correlativo, 180, 21)}^FS
^FT442,265^A0I,25,24^FH\\^FD{fit(nombre, 269)}^FS
^FT158,264^A0I,25,24^FH\\^FD{fit(format_rut_without_dots(rut), 152)}^FS
^FT441,239^A0I,17,16^FH\\^FDNOMBRE PACIENTE^FS
^FT158,239^A0I,17,16^FH\\^FDRUT^FS
^FO173,259^GB271,0,3^FS
^FO5,258^GB153,0,3^FS
^FT442,210^A0I,25,24^FH\\^FD{fit(dci, 257)}^FS
^FT177,210^A0I,25,24^FH\\^FD{fit(forma, 171)}^FS
^FT442,185^A0I,17,16^FH\\^FD{fit("DCI (PRINCIPIO ACTIVO)", 257, 16)}^FS
^FT177,185^A0I,17,16^FH\\^FD{fit("F.FARMACEUTICA", 171, 16)}^FS
^FO185,204^GB257,0,3^FS
^FO6,204^GB171,0,3^FS
{fila_dosis}
{fila_registro}
^FT442,51^A0I,17,14^FH\\^FD{fit(farmacia_linea, 436, 14)}^FS
^FT398,36^A0I,14,12^FB349,1,0,C^FH\\^FDPara mayor informaci\\A2n, consulte a su prescriptor o Q. Farmac\\82utico. ^FS
^FT398,19^A0I,14,12^FB349,1,0,C^FH\\^FDVisite www.ispch.cl y www.minsal.cl^FS
^PQ1,0,1,Y^XZ
"""

def print_labels(lines, dosificaciones, config):
    conn = config.get("conn", "network")
    printer_name = config.get("printer_name", "zebra")
    host = config.get("host", "192.168.1.23")
    port = config.get("port", 9100)

    if conn == "usb":
        printer = win32print.OpenPrinter(printer_name)
        try:
            win32print.StartDocPrinter(printer, 1, ('MonkeyPrint', None, 'RAW'))
        except Exception:
            win32print.ClosePrinter(printer)
            raise
    elif conn == "network":
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((host, port))
        except Exception:
            sock.close()
            raise
    else:
        raise ValueError("Invalid connection type")

    try:
        for line, dosificacion in zip(lines, dosificaciones):
            fields = {key: line[value] for key, value in MAPPING.items()}
            fields['rut'] = format_rut_without_dots(fields['rut'])        
            zpl = get_zpl(dosificacion, **fields)

            if conn == "usb":
                win32print.StartPagePrinter(printer)
                win32print.WritePrinter(printer, zpl.encode())
                win32print.EndPagePrinter(printer)
            elif conn == "network":
                sock.sendall(zpl.encode())
    finally:
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
        app.run(host='0.0.0.0', port=5050, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("Servidor detenido.")
    except Exception as e:
        app.logger.error(f"Error crítico: {str(e)}")