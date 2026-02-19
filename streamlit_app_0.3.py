import streamlit as st
from PIL import Image
import io
import zipfile
from datetime import datetime

st.set_page_config(page_title="Batch Bildgrößen ändern", page_icon="🖼️", layout="wide")

st.title("🖼️ Batch Bildgrößen ändern")
st.markdown("Laden Sie mehrere Bilder hoch und ändern Sie deren Größe auf einmal!")

# Sidebar für Einstellungen
st.sidebar.header("⚙️ Einstellungen")

resize_mode = st.sidebar.radio(
    "Größenanpassung:",
    ["Feste Breite", "Feste Höhe", "Feste Breite & Höhe", "Prozent"]
)

if resize_mode == "Feste Breite":
    width = st.sidebar.number_input("Breite (Pixel)", min_value=1, value=800, step=50)
    height = None
elif resize_mode == "Feste Höhe":
    height = st.sidebar.number_input("Höhe (Pixel)", min_value=1, value=600, step=50)
    width = None
elif resize_mode == "Feste Breite & Höhe":
    width = st.sidebar.number_input("Breite (Pixel)", min_value=1, value=800, step=50)
    height = st.sidebar.number_input("Höhe (Pixel)", min_value=1, value=600, step=50)
else:  # Prozent
    percent = st.sidebar.slider("Skalierung (%)", min_value=10, max_value=200, value=50)
    width = None
    height = None

quality = st.sidebar.slider("JPEG Qualität", min_value=1, max_value=100, value=85)
output_format = st.sidebar.selectbox("Ausgabeformat", ["Original beibehalten", "JPEG", "PNG", "WEBP"])

# File Upload
uploaded_files = st.file_uploader(
    "Bilder hochladen (mehrere möglich)",
    type=["jpg", "jpeg", "png", "webp", "bmp"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} Bild(er) hochgeladen")
    
    # Preview der Originalbilder
    st.subheader("📸 Hochgeladene Bilder")
    cols = st.columns(min(4, len(uploaded_files)))
    for idx, uploaded_file in enumerate(uploaded_files[:4]):
        with cols[idx]:
            img = Image.open(uploaded_file)
            st.image(img, caption=uploaded_file.name, use_container_width=True)
    
    if len(uploaded_files) > 4:
        st.info(f"... und {len(uploaded_files) - 4} weitere Bilder")
    
    # Verarbeiten Button
    if st.button("🚀 Bilder verarbeiten", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # ZIP-File im Speicher erstellen
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for idx, uploaded_file in enumerate(uploaded_files):
                try:
                    # Bild öffnen
                    img = Image.open(uploaded_file)
                    original_format = img.format
                    
                    # Größe berechnen
                    if resize_mode == "Prozent":
                        new_width = int(img.width * percent / 100)
                        new_height = int(img.height * percent / 100)
                    elif resize_mode == "Feste Breite":
                        new_width = width
                        new_height = int(img.height * (width / img.width))
                    elif resize_mode == "Feste Höhe":
                        new_height = height
                        new_width = int(img.width * (height / img.height))
                    else:  # Feste Breite & Höhe
                        new_width = width
                        new_height = height
                    
                    # Größe ändern
                    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Format bestimmen
                    if output_format == "Original beibehalten":
                        save_format = original_format if original_format else "PNG"
                    else:
                        save_format = output_format
                    
                    # EINFACHER Dateiname - einfach nummeriert
                    extension = save_format.lower()
                    if extension == "jpeg":
                        extension = "jpg"
                    new_filename = f"image_{idx+1:03d}_resized.{extension}"
                    
                    # In Speicher speichern
                    img_buffer = io.BytesIO()
                    
                    if save_format.upper() in ["JPEG", "JPG"]:
                        # RGB konvertieren für JPEG
                        if resized_img.mode in ("RGBA", "P", "LA"):
                            rgb_img = Image.new("RGB", resized_img.size, (255, 255, 255))
                            if resized_img.mode == "P":
                                resized_img = resized_img.convert("RGBA")
                            rgb_img.paste(resized_img, mask=resized_img.split()[-1] if resized_img.mode == "RGBA" else None)
                            resized_img = rgb_img
                        resized_img.save(_sanitize_filename(img_buffer), format="JPEG", quality=quality, optimize=True)
                    else:
                        resized_img.save(_sanitize_filename(img_buffer), format=save_format)
                    
                    # Zum ZIP hinzufügen
                    zip_file.writestr(new_filename, img_buffer.getvalue())
                    
                    # Progress aktualisieren
                    progress = (idx + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    status_text.text(f"Verarbeite Bild {idx + 1} von {len(uploaded_files)}")
                    
                except Exception as e:
                    st.error(f"❌ Fehler bei Bild {idx+1}: {str(e)}")
        
        progress_bar.progress(1.0)
        status_text.text("✅ Fertig!")
        
        # Download Button
        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.download_button(
            label="📥 Alle Bilder als ZIP herunterladen",
            data=zip_buffer,
            file_name=f"resized_images_{timestamp}.zip",
            mime="application/zip",
            type="primary"
        )
        
        st.balloons()

else:
    st.info("👆 Laden Sie Bilder hoch, um zu starten")

# Footer
st.markdown("---")
st.markdown("💡 **Tipp:** Sie können mehrere Bilder gleichzeitig auswählen!")
