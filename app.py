import streamlit as st
import random
import time
import datetime
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Simulación PACS XA", layout="wide")

st.title("Búsqueda y Descarga Masiva de Estudios XA desde PACS (Demo Realista)")

st.write("Esta es una simulación. Todos los datos, tiempos de búsqueda y descargas son generados aleatoriamente.")
st.write("Se mostrarán los resultados a medida que se encuentren y las descargas mostrarán su progreso en tiempo real.")
st.write("También se mostrarán los comandos que se 'enviarían' al PACS, como si fuese una terminal.")
st.write("Al finalizar la descarga de cada estudio, se emite un sonido sintético (sin usar archivos externos).")

# Insertamos un script para generar un pitido con la Web Audio API
st.markdown("""
<script>
var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function beep(volume, frequency, type, duration) {
  var oscillator = audioCtx.createOscillator();
  var gainNode = audioCtx.createGain();
  oscillator.connect(gainNode);
  gainNode.connect(audioCtx.destination);
  gainNode.gain.value = volume;
  oscillator.frequency.value = frequency;
  oscillator.type = type;
  oscillator.start();
  setTimeout(function(){
    oscillator.stop();
  }, duration);
}
</script>
""", unsafe_allow_html=True)

# Datos de conexión al PACS (con valores de ejemplo)
st.subheader("Datos de conexión PACS")
col_conn1, col_conn2, col_conn3 = st.columns(3)
pacs_ip = col_conn1.text_input("IP del PACS:", value="192.168.1.100")
pacs_port = col_conn2.text_input("Puerto del PACS:", value="104")
pacs_aet = col_conn3.text_input("AE Title del PACS:", value="AE_TITLE_PACS")

col_conn4, col_conn5 = st.columns(2)
local_aet = col_conn4.text_input("AE Title Local:", value="AE_TITLE_LOCAL")
dest_aet = col_conn5.text_input("AE Title Destino:", value="AE_TITLE_DESTINO")

# Añadimos la ubicación de destino
dest_path = st.text_input("Directorio de destino:", value="/var/local/pacs_downloads")

# Entrada de PatientIDs
st.subheader("Datos de Búsqueda")
patient_ids_input = st.text_area("Lista de PatientID (uno por línea):")
col_actions = st.columns([1,2])
buscar = col_actions[0].button("Buscar Estudios")
descargar = col_actions[0].button("Descargar Todos (Simulación)")

col_left, col_right = st.columns([2,3])
resultados_placeholder = col_left.empty()

# Barra lateral para progreso
st.sidebar.title("Progreso de Operaciones")

# Búsqueda
st.sidebar.write("**Progreso de Búsqueda:**")
sidebar_busqueda_label = st.sidebar.empty()
sidebar_busqueda_progress = st.sidebar.progress(0)

# Descarga global
st.sidebar.write("**Descarga Global:**")
sidebar_descarga_global_label = st.sidebar.empty()
sidebar_descarga_global_progress = st.sidebar.progress(0)
sidebar_descarga_global_info = st.sidebar.empty()

# Descarga estudio actual
st.sidebar.write("**Descarga Estudio Actual:**")
sidebar_descarga_estudio_label = st.sidebar.empty()
sidebar_descarga_estudio_progress = st.sidebar.progress(0)
sidebar_descarga_estudio_info = st.sidebar.empty()

# Área de "terminal" de comandos
st.subheader("Terminal (Comandos Simulados)")
terminal_placeholder = col_right.empty()
comandos_log = ""

def generar_estudios(pid):
    nombres = ["Juan Pérez", "María López", "Carlos García", "Ana Rodríguez", "Luis Gómez"]
    nombre = random.choice(nombres)
    # Entre 1 y 4 estudios, mayor probabilidad de tener 1
    num_estudios = random.choices([1,2,3,4], weights=[0.6,0.2,0.1,0.1])[0]

    estudios = []
    for i in range(num_estudios):
        uid = f"1.2.840.113619.{random.randint(1000,9999)}.{random.randint(100000,999999)}_{pid}_EstudioXA_{i+1}"
        fecha_estudio = (datetime.datetime.now() - datetime.timedelta(days=random.randint(1,365))).strftime("%Y-%m-%d")
        modalidad = "XA"
        num_imagenes = random.randint(50, 300)
        num_secuencias = random.randint(1, 5)
        # Asumimos 0.5 MB por imagen y 15 MB por secuencia para el tamaño
        tam_imagenes_mb = num_imagenes * 0.5
        tam_secuencias_mb = num_secuencias * 15
        estudios.append({
            "PatientID": pid,
            "PatientName": nombre,
            "StudyInstanceUID": uid,
            "StudyDate": fecha_estudio,
            "Modality": modalidad,
            "NumImages": num_imagenes,
            "NumSequences": num_secuencias,
            "ImagesMB": tam_imagenes_mb,
            "SequencesMB": tam_secuencias_mb
        })
    return estudios

# Guardamos el estado en session_state
if "resultados" not in st.session_state:
    st.session_state.resultados = []
if "patient_ids" not in st.session_state:
    st.session_state.patient_ids = []

if buscar:
    # Reseteamos estado
    st.session_state.resultados = []
    st.session_state.patient_ids = [line.strip() for line in patient_ids_input.split("\n") if line.strip()]

    if not st.session_state.patient_ids:
        st.warning("No se proporcionaron PatientIDs.")
    else:
        st.write("**Buscando...** Por favor espera.")
        time.sleep(1)  # Simula retardo inicial

        resultados = []
        total_pids = len(st.session_state.patient_ids)

        df = pd.DataFrame(columns=["PatientID", "PatientName", "StudyInstanceUID", 
                                   "StudyDate", "Modality", "NumImages", "NumSequences", "ImagesMB", "SequencesMB"])
        resultados_placeholder.table(df)

        for i, pid in enumerate(st.session_state.patient_ids, start=1):
            comando_find = f"findscu -c {pacs_aet}@{pacs_ip}:{pacs_port} -r StudyInstanceUID -m PatientID={pid} -m ModalitiesInStudy=XA"
            comandos_log += f"{comando_find}\n"
            terminal_placeholder.code(comandos_log, language='bash')

            st.write(f"Buscando estudios para PatientID: {pid}...")
            time.sleep(random.uniform(0.5, 1.5))  
            est = generar_estudios(pid)
            resultados.extend(est)

            pct_busqueda = int((i/total_pids)*100)
            sidebar_busqueda_progress.progress(pct_busqueda)
            sidebar_busqueda_label.write(f"{pct_busqueda}% completado")

            if resultados:
                df = pd.DataFrame(resultados, columns=["PatientID", "PatientName", "StudyInstanceUID", 
                                                       "StudyDate", "Modality", "NumImages", "NumSequences", "ImagesMB", "SequencesMB"])
                resultados_placeholder.table(df)

        if resultados:
            st.session_state.resultados = resultados
            st.success("Búsqueda completada.")
        else:
            st.info("No se encontraron estudios XA (simulación).")

if descargar and st.session_state.resultados:
    resultados = st.session_state.resultados
    descarga_title_placeholder = st.empty()
    descarga_title_placeholder.subheader("Descarga en Progreso (Simulación)")

    total_estudios = len(resultados)
    total_imagenes = sum(r['NumImages'] for r in resultados)
    total_secuencias = sum(r['NumSequences'] for r in resultados)
    total_images_mb = sum(r['ImagesMB'] for r in resultados)
    total_sequences_mb = sum(r['SequencesMB'] for r in resultados)

    imagenes_descargadas_global = 0
    secuencias_descargadas_global = 0
    estudios_descargados = 0
    mb_imagenes_descargadas = 0.0
    mb_secuencias_descargadas = 0.0

    sidebar_descarga_global_progress.progress(0)
    sidebar_descarga_global_label.write("0% completado")
    sidebar_descarga_global_info.write(
        f"Estudios: 0/{total_estudios}\n"
        f"Imágenes: 0/{int(total_imagenes)} (0MB/{int(total_images_mb)}MB)\n"
        f"Secuencias: 0/{total_secuencias} (0MB/{int(total_sequences_mb)}MB)"
    )

    estudio_actual_placeholder = st.empty()

    for j, r in enumerate(resultados, start=1):
        comando_move = (f"movescu -c {pacs_aet}@{pacs_ip}:{pacs_port} "
                        f"-aet {local_aet} -aem {dest_aet} "
                        f"-m StudyInstanceUID={r['StudyInstanceUID']}")
        comandos_log += f"{comando_move}\n"
        terminal_placeholder.code(comandos_log, language='bash')

        estudio_actual_placeholder.write(f"Descargando estudio {r['StudyInstanceUID']} del paciente {r['PatientName']} en {dest_path}...")

        num_imagenes = r['NumImages']
        num_secuencias_estudio = r['NumSequences']
        images_mb = r['ImagesMB']
        sequences_mb = r['SequencesMB']

        downloaded = 0
        chunks = 10
        chunk_size = max(1, num_imagenes // chunks)

        sidebar_descarga_estudio_progress.progress(0)
        sidebar_descarga_estudio_label.write("0% completado")
        sidebar_descarga_estudio_info.write(
            f"Estudio: {r['StudyInstanceUID']}\n"
            f"Imágenes (estudio): 0/{num_imagenes} (0MB/{int(images_mb)}MB)\n"
            f"Secuencias (estudio): {num_secuencias_estudio} ({int(sequences_mb)}MB)"
        )

        # Tiempo proporcional al número de imágenes
        for c in range(chunks):
            if downloaded + chunk_size > num_imagenes:
                chunk_download = num_imagenes - downloaded
            else:
                chunk_download = chunk_size
            
            # tiempo por imagen
            time_per_image = random.uniform(0.02, 0.05)  
            time.sleep(time_per_image * chunk_download)

            downloaded += chunk_download
            pct_estudio = int((downloaded / num_imagenes) * 100)
            sidebar_descarga_estudio_progress.progress(pct_estudio)
            sidebar_descarga_estudio_label.write(f"{pct_estudio}% completado")

            # MB descargadas del estudio (imágenes)
            mb_descargadas_estudio = (downloaded / num_imagenes) * images_mb

            sidebar_descarga_estudio_info.write(
                f"Estudio: {r['StudyInstanceUID']}\n"
                f"Imágenes (estudio): {downloaded}/{num_imagenes} ({int(mb_descargadas_estudio)}/{int(images_mb)}MB)\n"
                f"Secuencias (estudio): {num_secuencias_estudio} ({int(sequences_mb)}MB)"
            )

        # Estudio completo
        st.success(f"Estudio {r['StudyInstanceUID']} descargado correctamente. "
                   f"({r['NumImages']} imágenes, {r['NumSequences']} secuencias, {int(images_mb+sequences_mb)}MB aprox)")
        
        # Emitimos el pitido con el script
        st.markdown("<script>beep(0.5, 440, 'square', 200);</script>", unsafe_allow_html=True)

        # Actualizamos conteos globales
        estudios_descargados += 1
        imagenes_descargadas_global += r['NumImages']
        secuencias_descargadas_global += r['NumSequences']
        mb_imagenes_descargadas += images_mb
        mb_secuencias_descargadas += sequences_mb

        global_pct = int((estudios_descargados/total_estudios)*100)
        sidebar_descarga_global_progress.progress(global_pct)
        sidebar_descarga_global_label.write(f"{global_pct}% completado")
        sidebar_descarga_global_info.write(
            f"Estudios: {estudios_descargados}/{total_estudios}\n"
            f"Imágenes: {int(imagenes_descargadas_global)}/{int(total_imagenes)} ({int(mb_imagenes_descargadas)}/{int(total_images_mb)}MB)\n"
            f"Secuencias: {secuencias_descargadas_global}/{total_secuencias} ({int(mb_secuencias_descargadas)}/{int(total_sequences_mb)}MB)"
        )

    st.success("Todas las descargas han finalizado.")
