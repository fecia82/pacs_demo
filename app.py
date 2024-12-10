import streamlit as st
import random
import time
import datetime
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Simulación PACS XA", layout="wide")

st.title("Búsqueda y Descarga Masiva de Estudios XA desde PACS")
st.markdown("### Prueba de Concepto")

st.write("""
Esta es una **simulación** de un sistema PACS. Todos los datos, tiempos de búsqueda y descargas son generados aleatoriamente.

Flujo:
1. Configura la conexión al PACS.
2. Introduce la lista de Números de Historia Clínica.
3. Especifica el rango de fechas de búsqueda.
4. Presiona "Buscar Estudios".
5. Si se encuentran resultados, aparecerá la tabla con los estudios.
6. Selecciona cuáles descargar.
7. Pulsa "Descargar Seleccionados (Simulación)" (debajo de la tabla) y observa el progreso.

La terminal mostrará los comandos que se 'enviarían' al PACS.
""")

# Script para pitido al finalizar descarga
st.markdown("""
<script>
var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function beep() {
    var oscillator = audioCtx.createOscillator();
    var gainNode = audioCtx.createGain();
    oscillator.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    oscillator.type = 'sine';
    oscillator.frequency.value = 1000;
    oscillator.start();
    setTimeout(function(){ oscillator.stop(); }, 300);
}
function playBeep() {
    beep();
}
</script>
""", unsafe_allow_html=True)

def generar_estudios(pid, start_date, end_date):
    delta = end_date - start_date
    rand_days = random.randint(0, max(delta.days,0))
    fecha_estudio = (start_date + datetime.timedelta(days=rand_days)).strftime("%Y-%m-%d")

    nombres = ["Juan Pérez", "María López", "Carlos García", "Ana Rodríguez", "Luis Gómez"]
    nombre = random.choice(nombres)
    num_estudios = random.choices([1,2,3,4], weights=[0.6,0.2,0.1,0.1])[0]

    estudios = []
    for i in range(num_estudios):
        modalidad = "XA"
        num_imagenes = random.randint(50, 300)
        num_secuencias = random.randint(1, 5)
        tam_imagenes_mb = num_imagenes * 0.5
        tam_secuencias_mb = num_secuencias * 15
        estudios.append({
            "PatientID": pid,
            "PatientName": nombre,
            "StudyDate": fecha_estudio,
            "Modalidad": modalidad,
            "NumImages": num_imagenes,
            "NumSequences": num_secuencias,
            "ImagesMB": tam_imagenes_mb,
            "SequencesMB": tam_secuencias_mb
        })
    return estudios

# Estado
if "resultados" not in st.session_state:
    st.session_state.resultados = []
if "patient_ids" not in st.session_state:
    st.session_state.patient_ids = []
if "comandos_log" not in st.session_state:
    st.session_state.comandos_log = []
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "seleccionados" not in st.session_state:
    st.session_state.seleccionados = []

# Datos de conexión
st.subheader("Datos de Conexión PACS")
with st.expander("Configurar Conexión", expanded=True):
    col_conn1, col_conn2, col_conn3 = st.columns(3)
    pacs_ip = col_conn1.text_input("IP del PACS:", value="192.168.1.100")
    pacs_port = col_conn2.text_input("Puerto del PACS:", value="104")
    pacs_aet = col_conn3.text_input("AE Title del PACS:", value="AE_TITLE_PACS")

    col_conn4, col_conn5 = st.columns(2)
    local_aet = col_conn4.text_input("AE Title Local:", value="AE_TITLE_LOCAL")
    dest_aet = col_conn5.text_input("AE Title Destino:", value="AE_TITLE_DESTINO")

    # Cambiamos la ruta de ejemplo a C:\PACS_demo
    dest_path = st.text_input("Directorio de destino:", value="C:\\PACS_demo")

st.subheader("Búsqueda de Estudios")
st.write("Introduce la lista de Números de Historia Clínica (solo números, uno por línea):")
patient_ids_input = st.text_area("Números de Historia Clínica:", value="123456\n234567\n345678\n456789\n567890")

st.write("Selecciona el rango de fechas para la búsqueda de estudios:")
col_dates = st.columns(2)
start_date = col_dates[0].date_input("Fecha inicio:", datetime.date.today() - datetime.timedelta(days=30))
end_date = col_dates[1].date_input("Fecha fin:", datetime.date.today())

# Botón para buscar estudios
buscar = st.button("Buscar Estudios")

# Barra lateral de progreso
st.sidebar.title("Progreso de Operaciones")
st.sidebar.write("#### Progreso de Búsqueda")
sidebar_busqueda_label = st.sidebar.empty()
sidebar_busqueda_progress = st.sidebar.progress(0)

st.sidebar.write("#### Descarga Global")
sidebar_descarga_global_label = st.sidebar.empty()
sidebar_descarga_global_progress = st.sidebar.progress(0)
sidebar_descarga_global_info = st.sidebar.empty()

st.sidebar.write("#### Descarga Estudio Actual")
sidebar_descarga_estudio_label = st.sidebar.empty()
sidebar_descarga_estudio_progress = st.sidebar.progress(0)
sidebar_descarga_estudio_info = st.sidebar.empty()

st.subheader("Terminal (Comandos Simulados)")
terminal_placeholder = st.empty()

def log_comando(cmd):
    st.session_state.comandos_log.append(cmd)
    terminal_text = "\n".join(st.session_state.comandos_log)
    terminal_placeholder.code(terminal_text, language='bash')

# Lógica de búsqueda
if buscar:
    st.session_state.patient_ids = [line.strip() for line in patient_ids_input.split("\n") if line.strip()]
    if not st.session_state.patient_ids:
        st.warning("No se proporcionaron Números de Historia Clínica.")
    else:
        st.write("**Buscando...** Por favor espera un momento.")
        time.sleep(0.5)

        resultados = []
        total_pids = len(st.session_state.patient_ids)
        sidebar_busqueda_progress.progress(0)
        sidebar_busqueda_label.write("0% completado")

        # Reiniciamos el estado de resultados y comandos
        st.session_state.resultados = []
        st.session_state.df = pd.DataFrame()
        st.session_state.seleccionados = []
        st.session_state.comandos_log = []

        for i, pid in enumerate(st.session_state.patient_ids, start=1):
            cmd = f"findscu -c {pacs_aet}@{pacs_ip}:{pacs_port} -r StudyInstanceUID -m PatientID={pid} -m ModalitiesInStudy=XA"
            log_comando(cmd)

            st.write(f"Buscando estudios para **NHC: {pid}**...")
            time.sleep(random.uniform(0.5, 1.5))  
            est = generar_estudios(pid, start_date, end_date)
            resultados.extend(est)

            pct_busqueda = int((i/total_pids)*100)
            sidebar_busqueda_progress.progress(pct_busqueda)
            sidebar_busqueda_label.write(f"{pct_busqueda}% completado")

        if resultados:
            st.session_state.resultados = resultados
            df = pd.DataFrame(resultados, columns=["PatientID", "PatientName", "StudyDate",
                                                   "Modalidad", "NumImages", "NumSequences", "ImagesMB", "SequencesMB"])
            st.session_state.df = df.copy()

            st.success("Búsqueda completada. Tabla generada a continuación.")
        else:
            st.info("No se encontraron estudios XA (simulación).")

# Mostrar tabla si hay resultados
if not st.session_state.df.empty:
    st.markdown("#### Selecciona los estudios a descargar:")
    header_cols = st.columns([0.7,1,1,1,1,1,1,1])
    header_cols[0].write("Descargar")
    header_cols[1].write("NHC")
    header_cols[2].write("Fecha")
    header_cols[3].write("Modalidad")
    header_cols[4].write("Imágenes (MB)")
    header_cols[5].write("Secuencias (MB)")
    header_cols[6].write("MB Imágenes")
    header_cols[7].write("MB Secuencias")

    seleccionados = []
    for index, row in st.session_state.df.iterrows():
        row_cols = st.columns([0.7,1,1,1,1,1,1,1])
        checkbox_key = f"select_{row['PatientID']}_{row['StudyDate']}_{index}"
        seleccion = row_cols[0].checkbox(" ", value=True, key=checkbox_key, label_visibility="hidden")
        row_cols[1].write(row["PatientID"])
        row_cols[2].write(row["StudyDate"])
        row_cols[3].write(row["Modalidad"])
        row_cols[4].write(f"{row['NumImages']} ({int(row['ImagesMB'])}MB)")
        row_cols[5].write(f"{row['NumSequences']} ({int(row['SequencesMB'])}MB)")
        row_cols[6].write(int(row["ImagesMB"]))
        row_cols[7].write(int(row["SequencesMB"]))

        if seleccion:
            seleccionados.append(index)

    st.session_state.seleccionados = seleccionados

    # Botón de descargar debajo de la tabla
    descargar = st.button("Descargar Seleccionados (Simulación)")

    # Lógica de descarga
    if descargar:
        df = st.session_state.df
        seleccionados = st.session_state.seleccionados
        estudios_a_descargar = df.iloc[seleccionados].to_dict('records') if seleccionados else []

        if not estudios_a_descargar:
            st.warning("No se ha seleccionado ningún estudio para descargar.")
        else:
            descarga_title_placeholder = st.empty()
            descarga_title_placeholder.subheader("Descarga en Progreso (Simulación)")

            total_estudios = len(estudios_a_descargar)
            total_imagenes = sum(r['NumImages'] for r in estudios_a_descargar)
            total_secuencias = sum(r['NumSequences'] for r in estudios_a_descargar)
            total_images_mb = sum(r['ImagesMB'] for r in estudios_a_descargar)
            total_sequences_mb = sum(r['SequencesMB'] for r in estudios_a_descargar)

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

            for j, r in enumerate(estudios_a_descargar, start=1):
                cmd = (f"movescu -c {pacs_aet}@{pacs_ip}:{pacs_port} "
                       f"-aet {local_aet} -aem {dest_aet} "
                       f"-m StudyInstanceUID={r['StudyDate']}")
                log_comando(cmd)

                estudio_actual_placeholder.write(f"Descargando estudio de NHC {r['PatientID']} (Fecha: {r['StudyDate']}) en {dest_path}...")

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
                    f"Estudio: NHC {r['PatientID']} - Fecha: {r['StudyDate']}\n"
                    f"Imágenes (estudio): 0/{num_imagenes} (0MB/{int(images_mb)}MB)\n"
                    f"Secuencias (estudio): {num_secuencias_estudio} ({int(sequences_mb)}MB)"
                )

                for c in range(chunks):
                    if downloaded + chunk_size > num_imagenes:
                        chunk_download = num_imagenes - downloaded
                    else:
                        chunk_download = chunk_size

                    time_per_image = random.uniform(0.02, 0.05)  
                    time.sleep(time_per_image * chunk_download)

                    downloaded += chunk_download
                    pct_estudio = int((downloaded / num_imagenes) * 100)
                    sidebar_descarga_estudio_progress.progress(pct_estudio)
                    sidebar_descarga_estudio_label.write(f"{pct_estudio}% completado")

                    mb_descargadas_estudio = (downloaded / num_imagenes) * images_mb
                    sidebar_descarga_estudio_info.write(
                        f"Estudio: NHC {r['PatientID']} - Fecha: {r['StudyDate']}\n"
                        f"Imágenes (estudio): {downloaded}/{num_imagenes} ({int(mb_descargadas_estudio)}/{int(images_mb)}MB)\n"
                        f"Secuencias (estudio): {num_secuencias_estudio} ({int(sequences_mb)}MB)"
                    )

                st.success(
                    f"Estudio de NHC {r['PatientID']} (Fecha: {r['StudyDate']}) descargado correctamente. "
                    f"({r['NumImages']} imágenes, {r['NumSequences']} secuencias, {int(images_mb + sequences_mb)}MB aprox)"
                )

                st.markdown("<script>playBeep();</script>", unsafe_allow_html=True)

                estudios_descargados += 1
                imagenes_descargadas_global += r['NumImages']
                secuencias_descargadas_global += r['NumSequences']
                mb_imagenes_descargadas += images_mb
                mb_secuencias_descargadas += sequences_mb

                global_pct = int((estudios_descargados / total_estudios) * 100)
                sidebar_descarga_global_progress.progress(global_pct)
                sidebar_descarga_global_label.write(f"{global_pct}% completado")
                sidebar_descarga_global_info.write(
                    f"Estudios: {estudios_descargados}/{total_estudios}\n"
                    f"Imágenes: {int(imagenes_descargadas_global)}/{int(total_imagenes)} ({int(mb_imagenes_descargadas)}/{int(total_images_mb)}MB)\n"
                    f"Secuencias: {secuencias_descargadas_global}/{total_secuencias} ({int(mb_secuencias_descargadas)}/{int(total_sequences_mb)}MB)"
                )

            st.success("Todas las descargas han finalizado.")

# Si no hay df cargado, no se muestra la tabla ni el botón de descargar
