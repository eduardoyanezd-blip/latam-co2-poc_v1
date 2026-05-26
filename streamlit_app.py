import streamlit as st
import requests

# 1. CONFIGURACIÓN VISUAL Y ESTILOS LATAM
st.set_page_config(page_title="LATAM CO2 Engine - Consolidado", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f3f3f3; }
    .stButton>button { background-color: #eb192e; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    .metric-box { background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #1b0088; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.image("https://s.latamairlines.com/images/boreal/collections/v1/logos/latam/DescriptivePositive.svg", width=200)
st.title(" 🌱  Calculadora CO2 - Impacto Total Itinerario")

# --- FUNCIONES DE API ---
def get_atpco_token():
    url = "https://gold.apis.atpco.net/oauth/gettoken"
    # Credenciales según el estándar de autenticación definido [cite: 16, 21, 22]
    data = {
        'client_id': 'b03c2dc1-e4a1-40d8-8f34-8ee1d829e444',
        'client_secret': 'c2R*k-unD=3Cj9!oqU8H5+|3?^6%A|jw',
        'grant_type': 'client_credentials'
    }
    try:
        r = requests.post(url, data=data)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def get_co2_data(segments, token):
    url = "https://gold.apis.atpco.net/routehappy/consolidated"
    headers = {
        'Authorization': f'Bearer {token}',
        'x-api-key': 'cfd595f6-15b6-41b9-a1a9-0b7c57d25412',
        'Content-Type': 'application/json'
    }
    # Se envía un único itinerario con múltiples segmentos [cite: 37, 40]
    body = {
        "control": {"features": ["co2_emissions"], "include_rq": True},
        "currency": "USD",
        "data": {"itineraries": [{"segments": segments}]}
    }
    try:
        r = requests.post(url, json=body, headers=headers)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

# --- GESTIÓN DE ESTADO ---
if 'segmentos' not in st.session_state:
    st.session_state.segmentos = [{'dep': 'LSC', 'arr': 'SCL', 'date': '2026-06-30', 'flt': 103, 'cabin': 1}]

def reset_app():
    st.session_state.segmentos = [{'dep': 'LSC', 'arr': 'SCL', 'date': '2026-06-30', 'flt': 103, 'cabin': 1}]
    if 'resultado' in st.session_state:
        del st.session_state.resultado

# --- UI: FORMULARIO DINÁMICO ---
st.subheader("1. Configuración de Tramos")

CABIN_OPTIONS = {"Economy": 1, "Business": 2}

for i, s in enumerate(st.session_state.segmentos):
    with st.container():
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1.5])
        st.session_state.segmentos[i]['dep'] = col1.text_input(f"Origen {i+1}", s['dep'], key=f"dep_{i}").upper()
        st.session_state.segmentos[i]['arr'] = col2.text_input(f"Destino {i+1}", s['arr'], key=f"arr_{i}").upper()
        st.session_state.segmentos[i]['date'] = col3.text_input(f"Fecha {i+1}", s['date'], key=f"date_{i}")
        st.session_state.segmentos[i]['flt'] = col4.number_input(f"Vuelo # {i+1}", value=s['flt'], key=f"flt_{i}")
        
        seleccion_cabina = col5.selectbox(
            f"Cabina {i+1}", 
            options=list(CABIN_OPTIONS.keys()),
            index=0 if s['cabin'] == 1 else 1,
            key=f"cabin_{i}"
        )
        st.session_state.segmentos[i]['cabin'] = CABIN_OPTIONS[seleccion_cabina]

col_actions = st.columns([1, 1, 4])
if col_actions[0].button("➕ Agregar Tramo"):
    st.session_state.segmentos.append({'dep': '', 'arr': '', 'date': '2026-06-30', 'flt': 100, 'cabin': 1})
    st.rerun()

if col_actions[1].button("🔄 Reestablecer", on_click=reset_app):
    st.rerun()

st.divider()

# --- EJECUCIÓN Y CÁLCULO CONSOLIDADO ---
if st.button("🚀 CALCULAR TOTAL ITINERARIO"):
    with st.spinner('Solicitando cálculo consolidado a ATPCO...'):
        token_json, t_status = get_atpco_token()

        if t_status != 200:
            st.error(f"Error de Autenticación")
            st.json(token_json)
        else:
            token = token_json.get('access_token')
            
            # Construcción del arreglo de segmentos para enviar a la API [cite: 64]
            api_segments = []
            for s in st.session_state.segmentos:
                api_segments.append({
                    "dep": s['dep'], 
                    "arr": s['arr'], 
                    "date": s['date'], 
                    "cxr": "LA", 
                    "fltno": int(s['flt']), 
                    "cabin": s['cabin']
                })

            co2_json, c_status = get_co2_data(api_segments, token)

            if c_status == 200 and 'data' in co2_json:
                try:
                    # Extracción directa del valor total consolidado del itinerario 
                    itinerary = co2_json['data']['itineraries'][0]
                    emisiones_totales = co2_json['itineraries'][0]['data']['co2_emissions']
                    
                    #emisiones_totales = itinerary.get('co2_emissions')
                    
                    # Manejo de ruta alternativa de respuesta si es necesario 
                    if emisiones_totales is None and 'data' in itinerary:
                        emisiones_totales = itinerary['data'].get('co2_emissions')

                    if emisiones_totales is not None:
                        # Cálculo del costo financiero consolidado
                        toneladas = emisiones_totales #/ 1000
                        costo_usd = toneladas * 0.01

                        st.balloons()
                        st.subheader("2. Resultado Consolidado del Viaje")
                        
                        res_col1, res_col2 = st.columns(2)
                        with res_col1:
                            st.markdown(f"""<div class='metric-box'>
                                <p style='color: #1b0088; margin-bottom: 0;'>Impacto Total</p>
                                <h2 style='margin-top: 0;'>{emisiones_totales:,.2f} kg CO2</h2>
                            </div>""", unsafe_allow_html=True)
                        
                        with res_col2:
                            st.markdown(f"""<div class='metric-box'>
                                <p style='color: #eb192e; margin-bottom: 0;'>Compensación Total</p>
                                <h2 style='margin-top: 0;'>${costo_usd:,.4f} USD</h2>
                            </div>""", unsafe_allow_html=True)
                        
                        st.info("Este valor representa la suma total de emisiones para todos los tramos ingresados proporcionada por ATPCO.")
                    else:
                        st.warning("No se encontraron emisiones en la respuesta consolidada.")

                except Exception as e:
                    st.error(f"Error procesando la respuesta consolidada: {e}")
            else:
                st.error(f"Error en la API de CO2 (Status {c_status})")

            # Sección de auditoría técnica siempre disponible [cite: 83]
            with st.expander("🔍 Ver Respuesta Cruda (Validación Técnica)"):
                st.json(co2_json)

