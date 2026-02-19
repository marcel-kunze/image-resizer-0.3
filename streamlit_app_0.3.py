import streamlit as st
from PIL import Image
import io
import zipfile
from pathlib import Path

st.set_page_config(page_title="Bild-Resizer für 1200×1800px", page_icon="🖼️")

st.title("🖼️ Bild-Resizer für 1200×1800px")
st.markdown("""
Lade ein oder mehrere Bilder hoch. Die App erstellt für jedes Bild:
- Eine **1200×1800 Pixel** Arbeitsfläche mit weißem Hintergrund
- Das Bild wird **ohne Verzerrung** skaliert mit **100px Rand** (oben/unten oder links/rechts)
- Export als **JPG** mit Suffix **_1200x1800px**
""")

# Feste Zielgröße
CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 1800
MARGIN = 100

uploaded_files = st.file_uploader(
    "Bilder hochladen",
    type=["jpg", "jpeg", "png", "webp", "bmp"],
    accept_multiple_files=True
)

def process_image(img, original_filename):
    """
    Verarbeitet ein Bild:
    - Erstellt 1200×1800px weiße Arbeitsfläche
    - Skaliert Bild so dass entweder oben/unten ODER links/rechts 100px Rand bleibt
    - Zentriert das Bild
    - Gibt JPG zurück
    """
    # Originalgröße
    orig_width, orig_height = img.size
    
    # Verfügbarer Platz nach Abzug der Ränder
    # Bei Hochformat: links/rechts je 100px → verfügbare Breite = 1200 - 200 = 1000
    # Bei Querformat: oben/unten je 100px → verfügbare Höhe = 1800 - 200 = 1600
    
    # Zielgröße berechnen (ohne Verzerrung)
    # Das Bild soll so skaliert werden, dass EINER der Ränder genau 100px ist
    
    # Berechne Skalierungsfaktor für beide Dimensionen
    # Für Hochformat: Breite soll genau 1000px sein (1200 - 2*100)
    # Für Querformat: Höhe soll genau 1600px sein (1800 - 2*100)
    
    aspect_ratio = orig_width / orig_height
    canvas_aspect = CANVAS_WIDTH / CANVAS_HEIGHT  # 1200/1800 = 0.667
    
    if aspect_ratio > canvas_aspect:
        # Querformat: Breite ist limitierend
        # Bild soll links/rechts je 100px Rand haben
        new_width = CANVAS_WIDTH - 2 * MARGIN
        new_height = int(new_width / aspect_ratio)
    else:
        # Hochformat: Höhe ist limitierend
        # Bild soll oben/unten je 100px Rand haben
        new_height = CANVAS_HEIGHT - 2 * MARGIN
        new_width = int(new_height * aspect_ratio)
    
    # Bild skalieren
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Weiße Arbeitsfläche erstellen
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), "white")
    
    # Position berechnen (zentriert)
    x = (CANVAS_WIDTH - new_width) // 2
    y = (CANVAS_HEIGHT - new_height) // 2
    
    # Bild auf Canvas einfügen
    if img_resized.mode == 'RGBA':
        canvas.paste(img_resized, (x, y), img_resized)
    else:
        canvas.paste(img_resized, (x, y))
    
    # Als JPG speichern
    output = io.BytesIO()
    canvas.save(_sanitize_filename(output), format='JPEG', quality=95)
    output.seek(0)
    
    # Dateiname generieren
    stem = Path(original_filename).stem
    new_filename = f"{stem}_1200x1800px.jpg"
    
    return output, new_filename

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} Bild(er) hochgeladen")
    
    processed_images = []
    
    for uploaded_file in uploaded_files:
        try:
            img = Image.open(uploaded_file)
            output, new_filename = process_image(img, uploaded_file.name)
            processed_images.append((output, new_filename))
        except Exception as e:
            st.error(f"❌ Fehler bei {uploaded_file.name}: {e}")
    
    if processed_images:
        st.success(f"✅ {len(processed_images)} Bild(er) erfolgreich verarbeitet!")
        
        # Einzeldownload bei nur einem Bild
        if len(processed_images) == 1:
            output, filename = processed_images[0]
            st.download_button(
                label=f"📥 {filename} herunterladen",
                data=output.getvalue(),
                file_name=filename,
                mime="image/jpeg"
            )
        else:
            # ZIP erstellen bei mehreren Bildern
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for output, filename in processed_images:
                    zip_file.writestr(filename, output.getvalue())
            
            zip_buffer.seek(0)
            
            st.download_button(
                label=f"📥 Alle {len(processed_images)} Bilder als ZIP herunterladen",
                data=zip_buffer.getvalue(),
                file_name="resized_images_1200x1800px.zip",
                mime="application/zip"
            )
        
        # Vorschau
        st.subheader("🔍 Vorschau")
        cols = st.columns(min(3, len(processed_images)))
        for idx, (output, filename) in enumerate(processed_images[:3]):
            with cols[idx % 3]:
                st.image(output.getvalue(), caption=filename, use_container_width=True)
