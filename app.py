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
    # Penyamaran ganda: Menggunakan profil Android + Browser Chrome
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': 'lagu_sementara.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'extractor_args': {
            'youtube': ['player_client=android', 'player_skip=webpage']
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return f"lagu_sementara.{info['ext']}"

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
st.markdown("Masukkan link YouTube untuk membongkar elemen musiknya.")

# --- FITUR UTAMA: LINK YOUTUBE ---
youtube_url = st.text_input("Link YouTube", placeholder="https://www.youtube.com/watch?v=...")
tombol_youtube = st.button("Analisis Lagu", type="primary")

st.write("") # Memberi sedikit jarak spasi

# --- FITUR CADANGAN: UPLOAD MANUAL (Disembunyikan) ---
with st.expander("Opsi Cadangan (Gunakan hanya jika link YouTube error/diblokir)"):
    uploaded_file = st.file_uploader("Unggah file lagu (MP3, WAV, M4A)", type=['mp3', 'wav', 'm4a'])
    tombol_upload = st.button("Analisis File Upload")

# --- LOGIKA EKSEKUSI ---
file_audio = None
siap_analisa = False
is_youtube = False

if tombol_youtube and youtube_url:
    siap_analisa = True
    is_youtube = True
elif tombol_upload and uploaded_file is not None:
    siap_analisa = True
    is_youtube = False

if siap_analisa:
    with st.spinner("Sedang memproses lagu dan menganalisa (ini bisa memakan waktu 1-2 menit)..."):
        try:
            if is_youtube:
                file_audio = download_youtube_audio(youtube_url)
            else:
                ekstensi = uploaded_file.name.split('.')[-1]
                file_audio = f"lagu_upload.{ekstensi}"
                with open(file_audio, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            hasil_mentah = analyze_audio(file_audio)
            
            if "```json" in hasil_mentah:
                hasil_mentah = hasil_mentah.replace("```json\n", "").replace("\n```", "")
            
            hasil_json = json.loads(hasil_mentah)
            
            # Hapus file audio sementara dari server
            if file_audio and os.path.exists(file_audio):
                os.remove(file_audio)

            st.success("Analisa selesai!")
            st.divider()

            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("Hasil Breakdown")
                st.write("**Genre terdeteksi:**")
                st.write(hasil_json.get("genre", "-"))
                
                st.write("**Perkiraan tempo:**")
                st.write(hasil_json.get("tempo", "-"))
                
                st.write("**Mood:**")
                st.write(hasil_json.get("mood", "-"))
                
                st.write("**Instrumen dominan:**")
                st.write(hasil_json.get("instrumen", "-"))
                
                st.write("**Vokal:**")
                st.write(hasil_json.get("vokal", "-"))
                
                st.caption("Breakdown ini mendeskripsikan gaya musik secara umum — bukan menyalin lirik atau meniru vokal artis aslinya.")

            with col2:
                st.subheader("Prompt Preview")
                st.info(hasil_json.get("prompt_suno", "Prompt gagal dibuat."))
                st.markdown("*(Prompt di atas siap di-*copy* ke Suno atau Flow Music)*")
                
        except Exception as e:
            if "403" in str(e) or "HTTP Error" in str(e):
                st.error("🚨 YouTube saat ini sedang memblokir akses dari server. Jangan khawatir, silakan klik 'Opsi Cadangan' di bawah untuk mengunggah lagunya secara manual.")
            else:
                st.error(f"Terjadi kesalahan sistem: {e}")
