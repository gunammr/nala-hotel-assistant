import streamlit as st
from dotenv import load_dotenv
import os
import shelve
# Menggunakan pustaka native Google Generative AI
import google.generativeai as genai

# --- Load Environment Variables ---
# Pastikan Anda memiliki GOOGLE_API_KEY di file .env Anda
load_dotenv()

# --- Page Configuration ---
st.set_page_config(page_title="Nala - Hotel Glaze Blooms Assistant", layout="wide")
st.title("🤖 Nala: Asisten Virtual Hotel Glaze Blooms")

# --- Constants ---
USER_AVATAR = "👤"
BOT_AVATAR = "🏨"

# --- Built-in Knowledge Base ---
KNOWLEDGE_BASE = """
# Basis Pengetahuan Hotel - Hotel Glaze Blooms, Bali

---

## 1. Informasi Umum Hotel
* **Nama Hotel:** Hotel Glaze Blooms
* **Alamat:** Jalan Sutera Ungu No. 12, Seminyak, Bali, Indonesia
* **Telepon:** +62 361 777 0456
* **Email:** reservations@glazeblooms.com
* **Waktu Check-in:** Mulai pukul 14:00 WITA.
* **Waktu Check-out:** Paling lambat pukul 12:00 WITA.
* **Late Check-out & Early Check-in:** Tergantung ketersediaan dan mungkin dikenakan biaya. Hubungi resepsionis.

---

## 2. Fasilitas Hotel
* **The Petal Plate Restaurant:** Buka 06:30 - 23:00 WITA. Menyajikan sarapan, makan siang, dan makan malam.
* **Azure Sky Bar (Rooftop):** Buka 16:00 - 23:00 WITA. Menyajikan koktail dan makanan ringan.
* **Kolam Renang Lagoon:** Buka 07:00 - 19:00 WITA.
* **Kolam Renang Rooftop:** Buka 09:00 - 19:00 WITA (khusus dewasa 18+).
* **Bloom Spa:** Buka 09:00 - 21:00 WITA. Reservasi disarankan.
* **Pusat Kebugaran (Gym):** Buka 06:00 - 22:00 WITA. Gratis untuk tamu.

---

## 3. Layanan untuk Tamu
* **Wi-Fi:** Gratis di seluruh area hotel. Nama Jaringan: `GlazeBlooms_Guest`. Password diberikan saat check-in.
* **Layanan Kamar (Room Service):** Tersedia 24 jam.
* **Layanan Concierge:** Membantu pemesanan tur, sewa kendaraan, dan reservasi restoran.
* **Antar-Jemput Bandara:** Tersedia dengan biaya tambahan. Pesan 24 jam sebelumnya.

---

## 4. Kebijakan
* **Merokok:** Dilarang di dalam kamar. Area merokok tersedia.
* **Hewan Peliharaan:** Tidak diperbolehkan.
"""

# --- Configure Gemini API ---
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    st.error(f"Gagal mengkonfigurasi API Gemini. Pastikan GOOGLE_API_KEY Anda benar. Error: {e}")

# --- Model Initialization ---
def get_gemini_model():
    """Initializes and returns the Gemini Pro model."""
    system_instruction = f"""
    Anda adalah asisten virtual yang ramah dan sangat membantu bernama 'Nala' untuk 'Hotel Glaze Blooms' di Bali.
    Tugas Anda adalah menjawab pertanyaan tamu HANYA berdasarkan informasi yang disediakan dalam basis pengetahuan di bawah ini.
    Jangan menjawab pertanyaan yang tidak berhubungan dengan hotel atau informasi yang diberikan.
    Jika jawaban tidak dapat ditemukan dalam basis pengetahuan, katakan dengan sopan, "Maaf, saya tidak dapat menemukan informasi mengenai hal itu."
    Selalu jawab dalam Bahasa Indonesia.

    --- BASIS PENGETAHUAN HOTEL ---
    {KNOWLEDGE_BASE}
    ---
    """
    generation_config = {
        "temperature": 0.9,        # Slightly more creative
        "top_p": 0.8,             # Optimized for the flash model
        "top_k": 40,              # Increased for better response variety
        "max_output_tokens": 1024, # Optimized for flash model
        "candidate_count": 1
    }
    # Menggunakan model Gemini 1.5 Flash
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE"
        }
    ]
    
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash-latest",
        generation_config=generation_config,
        safety_settings=safety_settings
    )

# --- Chat History Management ---
def load_chat_history():
    """Loads chat history from a shelve file."""
    with shelve.open("chat_history_nala_gemini") as db:
        # Mengembalikan format yang benar untuk Gemini API
        return db.get("messages", [])

def save_chat_history(messages):
    """Saves chat history to a shelve file."""
    with shelve.open("chat_history_nala_gemini") as db:
        db["messages"] = messages

# --- Initialize Session State ---
if "model" not in st.session_state:
    st.session_state.model = get_gemini_model()
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()
# Inisialisasi chat session
if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.model.start_chat(history=[])


# --- Sidebar for History Deletion ---
with st.sidebar:
    st.header("Pengaturan")
    if st.button("Hapus Riwayat Obrolan"):
        st.session_state.messages = []
        save_chat_history([])
        # Reset chat session
        st.session_state.chat_session = st.session_state.model.start_chat(history=[])
        st.rerun()

# --- Display Chat Messages ---
for message in st.session_state.messages:
    # Mengganti 'assistant' dengan 'model' untuk konsistensi dengan Gemini API
    role = "user" if message["role"] == "user" else "assistant"
    avatar = USER_AVATAR if role == "user" else BOT_AVATAR
    with st.chat_message(role, avatar=avatar):
        st.markdown(message["content"])

# --- Main Chat Interface ---
if prompt := st.chat_input("Apa yang ingin Anda tanyakan tentang Hotel Glaze Blooms?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        message_placeholder = st.empty()
        full_response = ""
        try:
            # Mengirim pesan dengan konteks
            system_context = """
            Anda adalah asisten virtual yang ramah dan sangat membantu bernama 'Nala' untuk 'Hotel Glaze Blooms' di Bali.
            Tugas Anda adalah menjawab pertanyaan tamu HANYA berdasarkan informasi yang disediakan dalam basis pengetahuan di bawah ini.
            Jangan menjawab pertanyaan yang tidak berhubungan dengan hotel atau informasi yang diberikan.
            Jika jawaban tidak dapat ditemukan dalam basis pengetahuan, katakan dengan sopan, "Maaf, saya tidak dapat menemukan informasi mengenai hal itu."
            Selalu jawab dalam Bahasa Indonesia.

            --- BASIS PENGETAHUAN HOTEL ---
            """ + KNOWLEDGE_BASE + "\n---"
            
            response = st.session_state.chat_session.send_message(
                f"{system_context}\n\nPertanyaan tamu: {prompt}",
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"Gagal menghubungi Google Gemini: {e}")
            full_response = "Maaf, terjadi kesalahan saat memproses permintaan Anda."
            message_placeholder.markdown(full_response)

    # Menambahkan respons model ke riwayat
    st.session_state.messages.append({"role": "model", "content": full_response})

# --- Save Chat History After Each Interaction ---
save_chat_history(st.session_state.messages)
