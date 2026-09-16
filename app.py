import streamlit as st
import yt_dlp
import google.generativeai as genai
import os
import json
import time

# --- PENGATURAN TAMPILAN HALAMAN ---
st.set_page_config(page_title="AI Music Analyzer", layout="wide")

# --- MENGAMBIL API KEY ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("API Key belum dipasang. Silakan cek Advanced Settings di Streamlit.")

# --- FUNGSI UNTUK DOWNLOAD AUDIO DARI YOUTUBE ---
def download_youtube_audio(url):
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': 'lagu_sementara.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        # INI ADALAH TRIK BARU: Menyamar sebagai HP Android untuk menghindari pemblokiran YouTube
        'extractor_args': {'youtube': ['player_client=android']} 
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = f"lagu_sementara.{info['ext']}"
        return filename

# --- FUNGSI UNTUK MENGANALISA LAGU DENGAN GEMINI AI ---
def analyze_audio(file_path):
    uploaded_file = genai.upload_file(path=file_path)
    time.sleep(3) 
    model = genai.GenerativeModel('gemini-1.5-pro')
    instruksi = """
    Dengarkan audio ini dan lakukan analisa musik. 
    Kembalikan hasil analisamu dalam format JSON yang valid (tanpa teks lain) dengan format persis seperti ini:
    {
      "genre": "Nama genre (contoh: Ambient / New Age)",
      "tempo": "Perkiraan tempo (contoh: 60 BPM)",
      "mood": "Kata sifat mood (contoh: Calming, Serene, Peaceful)",
      "instrumen": "Instrumen yang paling dominan (contoh: Melodi: Acoustic Guitar; Pad: Synth pad)",
      "vokal": "Sebutkan apakah Instrumental Only atau ada Vokal",
      "prompt_suno": "Buatkan prompt bahasa Inggris untuk AI Music Generator (seperti Suno/Udio) yang mendeskripsikan secara detail instrumen, mood, tempo, dan gaya lagu ini, tanpa lirik."
    }
    """
    response = model.generate_content([uploaded_file, instruksi])
    genai.delete_file(uploaded_file.name)
    return response.text

# --- TAMPILAN APLIKASI ---
st.title("🎵 AI Music Analyzer & Prompt Generator")
st.markdown("Masukkan link YouTube, dan AI akan membongkar elemen musiknya untuk dijadikan *Prompt*.")

youtube_url = st.text_input("Link YouTube", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Analisis", type="primary"):
    if youtube_url:
        with st.spinner("Sedang mengunduh lagu dan menganalisa (ini bisa memakan waktu 1-2 menit)..."):
            try:
                file_audio = download_youtube_audio(youtube_url)
                hasil_mentah = analyze_audio(file_audio)
                
                if "```json" in hasil_mentah:
                    hasil_mentah = hasil_mentah.replace("```json\n", "").replace("\n```", "")
                
                hasil_json = json.loads(hasil_mentah)
                
                if os.path.exists(file_audio):
                    os.remove(file_audio)

                st.success("Analisa selesai!")
                st.divider()

                col1, col2 = st.columns([1, 1])

                with col1:
                    st.subheader("Hasil Breakdown")
                    st.write("**Genre terdeteksi**")
                    st.write(hasil_json.get("genre", "-"))
                    
                    st.write("**Perkiraan tempo**")
                    st.write(hasil_json.get("tempo", "-"))
                    
                    st.write("**Mood**")
                    st.write(hasil_json.get("mood", "-"))
                    
                    st.write("**Instrumen dominan**")
                    st.write(hasil_json.get("instrumen", "-"))
                    
                    st.write("**Vokal**")
                    st.write(hasil_json.get("vokal", "-"))
                    
                    st.caption("Breakdown ini mendeskripsikan gaya musik secara umum — bukan menyalin lirik atau meniru vokal artis aslinya.")

                with col2:
                    st.subheader("Prompt Preview")
                    st.info(hasil_json.get("prompt_suno", "Prompt gagal dibuat."))
                    st.markdown("*(Prompt di atas siap di-*copy* ke Suno atau Flow Music)*")
                    
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
    else:
        st.warning("Mohon masukkan link YouTube terlebih dahulu.")
