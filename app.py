from flask import Flask, render_template, request, jsonify
import joblib
import re
import traceback
import os
import numpy as np

app = Flask(__name__)

# ==========================================================
# 1. FIX PATH ABSOLUT DINAMIS (ANTI FILE NOT FOUND / CWD BUG)
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TFIDF_PATH = os.path.join(BASE_DIR, 'tfidf_vectorizer.pkl')
MODEL_PATH = os.path.join(BASE_DIR, 'svm_model.pkl')

tfidf = None
nb_model = None

print("Menginisialisasi pemuatan objek model biner melalui path absolut...")
try:
    if os.path.exists(TFIDF_PATH) and os.path.exists(MODEL_PATH):
        tfidf = joblib.load(TFIDF_PATH)
        nb_model = joblib.load(MODEL_PATH) 
        print("✅ SUCCESS: Model dan Vectorizer berhasil dimuat ke dalam memori.")
    else:
        if not os.path.exists(TFIDF_PATH):
            print(f"❌ ERROR: File '{TFIDF_PATH}' TIDAK DITEMUKAN!")
        if not os.path.exists(MODEL_PATH):
            print(f"❌ ERROR: File '{MODEL_PATH}' TIDAK DITEMUKAN!")
except Exception as e:
    print("❌ ERROR SAAT LOAD FILE .PKL:")
    traceback.print_exc()

def clean_text(text):
    if not text:
        return ""
    text = str(text).lower() 
    text = re.sub(r'[^a-z0-9\s]', '', text) 
    return text

# ==========================================================
# 2. CORE PARSER ENGINE FOR MULTI-PLATFORM
# ==========================================================
def parse_shopee_reviews(raw_text):
    """
    Memproses teks hasil copy-paste massal dari platform Shopee.
    Membuang username, timestamp, variasi produk, durasi video, dan sisa angka interaksi UI.
    """
    if not raw_text:
        return []
        
    if '|' in raw_text and not re.search(r'\d{4}-\d{2}-\d{2}', raw_text):
        return [part.strip() for part in raw_text.split('|') if part.strip()]

    timestamp_pattern = r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}'
    blocks = re.split(timestamp_pattern, raw_text)
    review_blocks = blocks[1:] if len(blocks) > 1 else blocks
    
    reviews = []
    for block in review_blocks:
        if not block.strip():
            continue
            
        block_clean = re.sub(r'\d+:\d+', '', block)
        lines = block_clean.split('\n')
        cleaned_lines = []
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.isdigit():
                continue
            if ' ' not in line_str and len(line_str) < 20 and not line_str.endswith(':'):
                if not re.match(r'^(bagus|mantap|oke|ok|keren|top|asli)$', line_str, re.IGNORECASE):
                    continue
            cleaned_lines.append(line_str)
                
        final_text = " ".join(cleaned_lines).strip()
        if final_text:
            reviews.append(final_text)
            
    return reviews

def parse_tokopedia_reviews(raw_text):
    """
    Memproses teks hasil copy-paste massal dari platform Tokopedia.
    Membuang sensor nama, metadata variasi, tombol Tutup Ulasan, teks orang terbantu, 
    label waktu relatif, serta teks sampah media review.
    Menghasilkan list berisi ulasan individual yang bersih.
    """
    if not raw_text:
        return []

    # 1. PRE-CLEANING: Bersihkan teks sampah sistem global Tokopedia yang sering ikut tercopas
    raw_text = re.sub(r'Ulasan Pilihan\s*Menampilkan[^\n]*', '', raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r'Foto\s*Review\s*Produk', '', raw_text, flags=re.IGNORECASE)
    
    # 2. STRATEGI RE-SPLIT ADVANCED:
    # Kita pecah ulasan berdasarkan nama pengguna anonim Tokopedia yang lebih fleksibel.
    raw_blocks = re.split(r'(?:\n|^)\s*[A-Za-z0-9]\*+[A-Za-z0-9]\s*(?:\r?\n|$)', raw_text)
    
    reviews = []
    for block in raw_blocks:
        if not block.strip():
            continue
            
        # Hapus informasi baris varian produk (Contoh: "Varian: Bright Radiance" atau "Varian: Default")
        block_clean = re.sub(r'^\s*Varian:[^\n]*\n?', '', block.strip(), flags=re.IGNORECASE)
        
        # Potong komponen interaksi UI bawah web Tokopedia yang ikut tersalin di ujung ulasan
        block_clean = re.split(r'Tutup Ulasan', block_clean, flags=re.IGNORECASE)[0]
        block_clean = re.split(r'\d+\s+orang\s+terbantu', block_clean, flags=re.IGNORECASE)[0]
        block_clean = re.split(r'Membantu', block_clean, flags=re.IGNORECASE)[0]
        
        # Split baris untuk menyaring sisa penanda waktu relatif
        lines = [line.strip() for line in block_clean.split('\n') if line.strip()]
        cleaned_lines = []
        
        for line in lines:
            # Buang baris keterangan waktu relatif (Contoh: "6 bulan lalu", "2 minggu lalu", "1 hari lalu")
            if re.match(r'^\s*\d+\s+(bulan|hari|minggu|tahun|jam|menit)\s+lalu\s*$', line, re.IGNORECASE):
                continue
            cleaned_lines.append(line)
            
        # Gabungkan sisa baris ulasan mentah menjadi satu paragraf kalimat utuh
        final_text = " ".join(cleaned_lines).strip()
        
        # Validasi akhir: Pastikan teks bukan string kosong dan bukan sisa kata interaksi yang tertinggal
        if final_text and len(final_text) > 3:
            if not re.match(r'^(terbantu|bulan lalu|hari lalu|minggu lalu)$', final_text, re.IGNORECASE):
                reviews.append(final_text)
            
    return reviews

# ==========================================
# 3. ROUTE & ENDPOINT SINKRONISASI PIPELINE
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if tfidf is None or nb_model is None:
            return jsonify({
                'status': 'error', 
                'error': 'Model atau Vectorizer gagal di-load di server backend.'
            }), 500

        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'error': 'Payload JSON tidak terdeteksi oleh backend.'}), 400
            
        raw_input = data.get('review', '')
        platform = data.get('platform', 'shopee')
        
        if not str(raw_input).strip():
            return jsonify({'status': 'error', 'error': 'Teks input kosong.'}), 400

        if platform == "tokopedia":
            extracted_reviews = parse_tokopedia_reviews(raw_input)
        else:
            extracted_reviews = parse_shopee_reviews(raw_input)

        if not extracted_reviews:
            extracted_reviews = [raw_input.strip()]

        results = []
        classes = nb_model.classes_
        
        # PETA DEFINISI LABEL SINKRON TERHADAP IDENTIFIKASI NOTEBOOK & SKRIPSI FRONTEND
        label_map = {0: 'Negatif', 1: 'Netral', 2: 'Positif'}

        for review_text in extracted_reviews:
            cleaned = clean_text(review_text)
            if cleaned.strip() == '': 
                continue

            vec = tfidf.transform([cleaned])
            raw_pred = nb_model.predict(vec)[0]
            
            # Konversi nilai prediksi bertipe numpy.int64 ke label teks alfabet murni
            prediction_label = label_map.get(int(raw_pred), str(raw_pred))
            
            # Perhitungan probabilitas adaptif untuk arsitektur model LinearSVC
            if hasattr(nb_model, "predict_proba"):
                probs = nb_model.predict_proba(vec)[0]
            else:
                decision_scores = nb_model.decision_function(vec)[0]
                if len(classes) == 2:
                    exp_scores = np.exp([ -decision_scores, decision_scores ])
                    probs = exp_scores / np.sum(exp_scores)
                else:
                    exp_scores = np.exp(decision_scores - np.max(decision_scores)) 
                    probs = exp_scores / np.sum(exp_scores)
            
            # FIX SOLUSI AMAN: Typecasting key dictionary dari numpy.int64 menjadi string murni sentimen
            conf = {}
            for i in range(len(classes)):
                class_int_key = int(classes[i])
                str_label_key = label_map.get(class_int_key, str(class_int_key))
                conf[str_label_key] = round(float(probs[i]) * 100, 2)
            
            results.append({
                "original_review": review_text,
                "stars": None,
                "prediction": prediction_label,
                "confidence": conf
            })
            
        return jsonify({
            'status': 'success',
            'mode': 'link', 
            'platform': platform,
            'results': results
        })
            
    except Exception as e:
        print("\n=== ❌ FLASK BACKEND EXCEPTION ENCOUNTERED ===")
        traceback.print_exc()
        print("===============================================\n")
        return jsonify({'status': 'error', 'error': f'Internal Server Error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)