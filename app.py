import streamlit as st
import json
import re
import os
import requests

class JSONFormGenerator:
    def __init__(self, schema_path: str, historial_path: str = "historial.json"):
        self.schema_path = schema_path
        self.historial_path = historial_path
        self.schema = self.load_schema()
        self.data = {}
        self.errores = {}

    def load_schema(self) -> dict:
        """Carga el esquema desde un archivo JSON."""
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def validar_regex(self, campo: str, valor: str, regex: str) -> bool:
        """Valida un campo de texto usando una expresión regular."""
        if not re.fullmatch(regex, valor):
            self.errores[campo] = f"Formato inválido para '{campo}'"
            return False
        return True

    def render_form(self):
        """Genera los campos del formulario según el esquema JSON."""
        st.title("🧩 Formulario dinámico con validaciones, historial y envío remoto")

        for campo, opciones in self.schema.items():
            tipo = opciones.get("tipo")
            placeholder = opciones.get("placeholder", "")
            regex = opciones.get("regex")

            if tipo == "texto":
                valor = st.text_input(campo.capitalize(), placeholder=placeholder)
                if valor and regex:
                    self.validar_regex(campo, valor, regex)
                self.data[campo] = valor

            elif tipo == "numero":
                minimo = opciones.get("min", 0)
                maximo = opciones.get("max", 100)
                self.data[campo] = st.number_input(campo.capitalize(), min_value=minimo, max_value=maximo, step=1)

            elif tipo == "booleano":
                self.data[campo] = st.checkbox(campo.capitalize())

            elif tipo == "lista":
                texto = st.text_input(f"{campo.capitalize()} (separado por comas)", placeholder=placeholder)
                lista = [i.strip() for i in texto.split(",") if i.strip()]
                self.data[campo] = lista

            else:
                st.warning(f"Tipo no reconocido: {tipo}")

    def guardar_historial(self):
        """Guarda el JSON actual en el historial."""
        historial = []
        if os.path.exists(self.historial_path):
            with open(self.historial_path, "r", encoding="utf-8") as f:
                try:
                    historial = json.load(f)
                except json.JSONDecodeError:
                    pass

        historial.append(self.data)

        with open(self.historial_path, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=2, ensure_ascii=False)

    def eliminar_entrada_historial(self, index: int):
        """Elimina una entrada específica del historial."""
        if os.path.exists(self.historial_path):
            with open(self.historial_path, "r", encoding="utf-8") as f:
                historial = json.load(f)

            if 0 <= index < len(historial):
                del historial[index]

                with open(self.historial_path, "w", encoding="utf-8") as f:
                    json.dump(historial, f, indent=2, ensure_ascii=False)
                st.experimental_rerun()

    def render_output(self):
        """Muestra el JSON generado y errores si existen."""
        st.markdown("---")

        if self.errores:
            st.error("❌ Errores en el formulario:")
            for campo, mensaje in self.errores.items():
                st.markdown(f"- **{campo}**: {mensaje}")
        else:
            st.success("✅ JSON válido generado")
            st.subheader("📄 Resultado JSON")
            st.json(self.data)

            if st.button("💾 Guardar en historial"):
                self.guardar_historial()
                st.success("Guardado en historial correctamente.")

            st.download_button(
                label="⬇️ Descargar JSON",
                data=json.dumps(self.data, indent=2),
                file_name="resultado.json",
                mime="application/json"
            )

            with st.expander("📡 Enviar JSON a una URL externa"):
                with st.form("formulario_post_url"):
                    url = st.text_input("Ingresá la URL donde enviar el JSON:", placeholder="https://api.tuservidor.com/datos")
                    enviar = st.form_submit_button("🚀 Enviar")

                    if enviar:
                        if url:
                            try:
                                response = requests.post(url, json=self.data)
                                if response.status_code == 200:
                                    st.success("✅ Datos enviados correctamente.")
                                else:
                                    st.warning(f"⚠️ Error al enviar: Código {response.status_code}")
                            except Exception as e:
                                st.error(f"❌ Fallo al enviar: {e}")
                        else:
                            st.warning("⚠️ Debés ingresar una URL válida.")

    def mostrar_historial(self):
        """Muestra los formularios guardados en historial.json."""
        st.markdown("---")
        st.subheader("📚 Historial de formularios anteriores")

        if os.path.exists(self.historial_path):
            with open(self.historial_path, "r", encoding="utf-8") as f:
                try:
                    historial = json.load(f)
                except json.JSONDecodeError:
                    historial = []
        else:
            historial = []

        if not historial:
            st.info("No hay historial guardado aún.")
            return

        for i, entry in enumerate(historial[::-1]):
            real_index = len(historial) - 1 - i
            with st.expander(f"Formulario #{real_index + 1}"):
                st.json(entry)
                if st.button(f"🗑️ Eliminar este formulario", key=f"del_{real_index}"):
                    self.eliminar_entrada_historial(real_index)

    def run(self):
        self.render_form()
        self.render_output()
        self.mostrar_historial()


if __name__ == "__main__":
    app = JSONFormGenerator("esquema.json")
    app.run()
