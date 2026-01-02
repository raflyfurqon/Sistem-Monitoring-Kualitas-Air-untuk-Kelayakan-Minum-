import numpy as np


# =============================
# FUNGSI KEANGGOTAAN FUZZY (TRAPEZOIDAL)
# =============================

def trapmf(x, params):
    """
    Trapezoidal membership function
    params = [a, b, c, d] dimana a <= b <= c <= d
    """
    a, b, c, d = params
    if x < a or x > d:
        return 0.0
    elif a <= x <= b:
        return (x - a) / (b - a) if b != a else 1.0
    elif b < x < c:
        return 1.0
    elif c <= x <= d:
        return (d - x) / (d - c) if d != c else 1.0
    else:
        return 0.0


# =============================
# FUZZIFIKASI PARAMETER
# =============================

def fuzzifikasi_ph(ph):
    """
    Fuzzifikasi pH berdasarkan himpunan fuzzy trapezoidal
    Sesuai dokumentasi: Tabel 1 - Klasifikasi Tingkat pH
    """
    membership = {}
    
    # Asam: pH ≤ 6.5 (Tidak Layak)
    membership['Asam'] = trapmf(ph, [0, 0, 6.5, 6.6])
    
    # Sedikit Asam: 6.6 <= pH <= 6.9 (Cukup)
    membership['Sedikit Asam'] = trapmf(ph, [6.5, 6.6, 6.9, 7.0])
    
    # Netral: pH = 7.0 (Optimal)
    membership['Netral'] = trapmf(ph, [6.9, 7.0, 7.0, 7.1])
    
    # Sedikit Basa: 7.1 <= pH <= 8.5 (Cukup)
    membership['Sedikit Basa'] = trapmf(ph, [7.0, 7.1, 8.5, 8.6])
    
    # Basa: pH ≥ 8.6 (Tidak Layak)
    membership['Basa'] = trapmf(ph, [8.5, 8.6, 14, 14])
        
    return membership


def fuzzifikasi_tds(tds):
    """
    Fuzzifikasi TDS berdasarkan himpunan fuzzy trapezoidal
    """
    membership = {}
    
    membership['Sempurna'] = trapmf(tds, [0, 0, 300, 301])
    membership['Baik'] = trapmf(tds, [300, 301, 600, 601])
    membership['Cukup'] = trapmf(tds, [600, 601, 900, 901])
    membership['Buruk'] = trapmf(tds, [900, 901, 1199, 1200])
    membership['Tidak Diterima'] = trapmf(tds, [1199, 1200, 2000, 2000])
    
    return membership


def fuzzifikasi_kekeruhan(ntu):
    """
    Fuzzifikasi Kekeruhan berdasarkan himpunan fuzzy trapezoidal
    """
    membership = {}
    
    membership['Sempurna'] = trapmf(ntu, [0, 0, 1.0, 1.1])
    membership['Baik'] = trapmf(ntu, [1.0, 1.1, 5.0, 5.1])
    membership['Cukup'] = trapmf(ntu, [5.0, 5.1, 25.0, 25.1])
    membership['Buruk'] = trapmf(ntu, [25.0, 25.1, 100.0, 100.1])
    membership['Tidak Diterima'] = trapmf(ntu, [100.0, 100.1, 300.0, 300.0])
    
    return membership


# =============================
# DEFUZZIFIKASI OUTPUT
# =============================

def defuzzifikasi_output(firing_strength):
    """
    Defuzzifikasi menggunakan himpunan fuzzy output trapezoidal
    """
    output_params = {
        'Tidak Layak': [0, 0, 40, 50],
        'Cukup Layak': [40, 50, 70, 80],
        'Layak': [70, 80, 100, 100]
    }
    
    numerator = 0
    denominator = 0
    
    x_range = np.linspace(0, 100, 1000)
    
    for x in x_range:
        membership_agregat = 0
        for status, strength in firing_strength.items():
            if strength > 0:
                membership_at_x = trapmf(x, output_params[status])
                membership_agregat = max(membership_agregat, min(strength, membership_at_x))
        
        numerator += x * membership_agregat
        denominator += membership_agregat
    
    if denominator == 0:
        return 50
    
    return numerator / denominator


# =============================
# SISTEM INFERENSI FUZZY
# =============================

def fuzzy_inference(ph, tds, ntu):
    """
    Sistem inferensi fuzzy untuk evaluasi kualitas air
    """
    
    details = {}
    
    # 1. FUZZIFIKASI
    ph_membership = fuzzifikasi_ph(ph)
    tds_membership = fuzzifikasi_tds(tds)
    ntu_membership = fuzzifikasi_kekeruhan(ntu)
    
    details['ph_membership'] = ph_membership
    details['tds_membership'] = tds_membership
    details['ntu_membership'] = ntu_membership
    
    # 2. INFERENSI FUZZY
    firing_strength = {
        'Tidak Layak': 0,
        'Cukup Layak': 0,
        'Layak': 0
    }
    
    rules_fired = []
    
    # --- ATURAN TIDAK LAYAK MINUM (R1-R6) ---
    
    r1 = ph_membership['Asam']
    if r1 > 0:
        firing_strength['Tidak Layak'] = max(firing_strength['Tidak Layak'], r1)
        rules_fired.append(('R1', r1, 'pH Asam'))
    
    r2 = ph_membership['Basa']
    if r2 > 0:
        firing_strength['Tidak Layak'] = max(firing_strength['Tidak Layak'], r2)
        rules_fired.append(('R2', r2, 'pH Basa'))
    
    r3 = tds_membership['Buruk']
    if r3 > 0:
        firing_strength['Tidak Layak'] = max(firing_strength['Tidak Layak'], r3)
        rules_fired.append(('R3', r3, 'TDS Buruk'))
    
    r4 = tds_membership['Tidak Diterima']
    if r4 > 0:
        firing_strength['Tidak Layak'] = max(firing_strength['Tidak Layak'], r4)
        rules_fired.append(('R4', r4, 'TDS Tidak Diterima'))
    
    r5 = ntu_membership['Buruk']
    if r5 > 0:
        firing_strength['Tidak Layak'] = max(firing_strength['Tidak Layak'], r5)
        rules_fired.append(('R5', r5, 'Kekeruhan Buruk'))
    
    r6 = ntu_membership['Tidak Diterima']
    if r6 > 0:
        firing_strength['Tidak Layak'] = max(firing_strength['Tidak Layak'], r6)
        rules_fired.append(('R6', r6, 'Kekeruhan Tidak Diterima'))
    
    # --- ATURAN CUKUP LAYAK MINUM (R7-R16) ---
    
    r7 = min(ph_membership['Sedikit Asam'], tds_membership['Cukup'], ntu_membership['Cukup'])
    if r7 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r7)
        rules_fired.append(('R7', r7, 'pH Sedikit Asam, TDS Cukup, Kekeruhan Cukup'))
    
    r8 = min(ph_membership['Sedikit Basa'], tds_membership['Cukup'], ntu_membership['Cukup'])
    if r8 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r8)
        rules_fired.append(('R8', r8, 'pH Sedikit Basa, TDS Cukup, Kekeruhan Cukup'))
    
    r9 = min(ph_membership['Netral'], tds_membership['Cukup'], ntu_membership['Baik'])
    if r9 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r9)
        rules_fired.append(('R9', r9, 'pH Netral, TDS Cukup, Kekeruhan Baik'))
    
    r10 = min(ph_membership['Netral'], tds_membership['Baik'], ntu_membership['Cukup'])
    if r10 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r10)
        rules_fired.append(('R10', r10, 'pH Netral, TDS Baik, Kekeruhan Cukup'))   

    r11 = min(ph_membership['Sedikit Asam'], tds_membership['Baik'], ntu_membership['Baik'])
    if r11 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r11)
        rules_fired.append(('R11', r11, 'pH Sedikit Asam, TDS Baik, Kekeruhan Baik'))
    
    r12 = min(ph_membership['Sedikit Basa'], tds_membership['Baik'], ntu_membership['Baik'])
    if r12 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r12)
        rules_fired.append(('R12', r12, 'pH Sedikit Basa, TDS Baik, Kekeruhan Baik'))

    r13 = min(ph_membership['Sedikit Asam'], tds_membership['Baik'], ntu_membership['Sempurna'])
    if r13 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r13)
        rules_fired.append(('R13', r13, 'pH Sedikit Asam, TDS Baik, Kekeruhan Sempurna'))

    r14 = min(ph_membership['Sedikit Basa'], tds_membership['Baik'], ntu_membership['Sempurna'])
    if r14 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r14)
        rules_fired.append(('R14', r14, 'pH Sedikit Basa, TDS Baik, Kekeruhan Sempurna'))

    r15 = min(ph_membership['Sedikit Asam'], tds_membership['Sempurna'], ntu_membership['Baik'])
    if r15 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r15)
        rules_fired.append(('R15', r15, 'pH Sedikit Asam, TDS Sempurna, Kekeruhan Baik'))

    r16 = min(ph_membership['Sedikit Basa'], tds_membership['Sempurna'], ntu_membership['Baik'])
    if r16 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r16)
        rules_fired.append(('R16', r16, 'pH Sedikit Basa, TDS Sempurna, Kekeruhan Baik'))

    # --- ATURAN LAYAK MINUM (R17-R22) ---

    r17 = min(ph_membership['Sedikit Asam'], tds_membership['Sempurna'], ntu_membership['Sempurna'])
    if r17 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r17)
        rules_fired.append(('R17', r17, 'pH Sedikit Asam, TDS Sempurna, Kekeruhan Sempurna'))

    r18 = min(ph_membership['Sedikit Basa'], tds_membership['Sempurna'], ntu_membership['Sempurna'])
    if r18 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r18)
        rules_fired.append(('R18', r18, 'pH Sedikit Basa, TDS Sempurna, Kekeruhan Sempurna'))

    r19 = min(ph_membership['Netral'], tds_membership['Sempurna'], ntu_membership['Sempurna'])
    if r19 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r19)
        rules_fired.append(('R19', r19, 'pH Netral, TDS Sempurna, Kekeruhan Sempurna'))

    r20 = min(ph_membership['Netral'], tds_membership['Baik'], ntu_membership['Baik'])
    if r20 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r20)
        rules_fired.append(('R20', r20, 'pH Netral, TDS Baik, Kekeruhan Baik'))

    r21 = min(ph_membership['Netral'], tds_membership['Sempurna'], ntu_membership['Baik'])
    if r21 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r21)
        rules_fired.append(('R21', r21, 'pH Netral, TDS Sempurna, Kekeruhan Baik'))

    r22 = min(ph_membership['Netral'], tds_membership['Baik'], ntu_membership['Sempurna'])
    if r22 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r22)
        rules_fired.append(('R22', r22, 'pH Netral, TDS Baik, Kekeruhan Sempurna'))
        
    details['firing_strength'] = firing_strength
    details['rules_fired'] = rules_fired
    
    has_active_rules = len(rules_fired) > 0
    
    # 3. DEFUZZIFIKASI
    if has_active_rules:
        score = defuzzifikasi_output(firing_strength)
        
        max_strength = max(firing_strength.values())
        if max_strength == 0:
            status = "Cukup Layak Minum"
        else:
            for s, strength in firing_strength.items():
                if strength == max_strength:
                    if s == 'Tidak Layak':
                        status = "Tidak Layak Minum"
                    elif s == 'Cukup Layak':
                        status = "Cukup Layak Minum"
                    else:
                        status = "Layak Minum"
                    break
    else:
        status = "Tidak Layak Minum"
        score = 0
    
    details['score'] = score
    details['status'] = status
    details['has_active_rules'] = has_active_rules
    
    return status, score, details, has_active_rules


# =============================
# FUNGSI EVALUASI LENGKAP
# =============================

def calculate_confidence(status, firing_strength, rules_fired, ph, tds, ntu, ph_membership, tds_membership, ntu_membership, ml_result=None, es_result=None):
    """
    SISTEM CONFIDENCE BARU (UPDATED):
    
    ATURAN KHUSUS R1-R6 (Tidak Layak Minum):
    - Jika R1-R6 aktif DAN ML = "Tidak Layak Minum" → Confidence = 0% (keduanya setuju air berbahaya)
    - Jika R1-R6 aktif DAN ML = "Layak Minum" → Confidence = 25% (hanya ML yang "berani" bilang layak)
    - Ini adalah ALARM BAHAYA dengan exception untuk ML yang berbeda pendapat
    
    ML contribution (0-25%):
    - ML = ES Status → 25% (ML setuju dengan ES)
    - ML ≠ ES Status → 0% untuk status Cukup/Tidak Layak
    - ML = "Layak" saat R1-R6 aktif → 25% (ML berani berbeda pendapat)
    
    ES contribution (0-75%):
    - Status "Layak Minum" → 0-75% (base + bonus)
    - Status "Cukup Layak Minum" → 0-50% (base + bonus, max lebih rendah)
    - Status "Tidak Layak Minum" → 0%
    
    Total: ML + ES (max 100%)
    """
    
    # === CEK RULE R1-R6 (ALARM BAHAYA) ===
    danger_rules = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6']
    active_danger_rules = [r[0] for r in rules_fired if r[0] in danger_rules]
    
    if active_danger_rules:
        rule_names = ', '.join(active_danger_rules)
        
        # KASUS KHUSUS: Jika ML bilang "Layak Minum" saat R1-R6 aktif
        if ml_result is not None and ml_result.strip() == "Layak Minum":
            confidence = 25
            explanation = f"""
Perhitungan Confidence (Sistem Baru):
⚠️ ALARM BAHAYA AKTIF: {rule_names}
• Rule R1-R6 mendeteksi parameter berbahaya
• TETAPI ML memprediksi: "Layak Minum"
• ML berani berbeda pendapat dengan ES → +25%
• ES contribution: 0% (alarm bahaya)
• TOTAL: 25% (HANYA DARI ML - TETAP WASPADAI ALARM ES)

⚠️ CATATAN PENTING: 
Meskipun ML memprediksi "Layak Minum", sistem pakar mendeteksi 
parameter yang melewati batas aman. Disarankan untuk berhati-hati 
dan memverifikasi dengan pengukuran ulang atau sumber lain.
"""
            return confidence, explanation
        
        # KASUS NORMAL: ML setuju dengan ES atau ML bilang lebih buruk
        else:
            confidence = 0
            explanation = f"""
Perhitungan Confidence (Sistem Baru):
⚠️ ALARM BAHAYA AKTIF: {rule_names}
• Rule R1-R6 adalah alarm keamanan
• ML prediction: {ml_result if ml_result else 'N/A'}
• Confidence MUTLAK: 0%
• ML contribution: 0% (setuju dengan alarm atau lebih pesimis)
• ES contribution: 0% (alarm bahaya)
• TOTAL: 0% (TIDAK ADA KEPERCAYAAN - AIR BERBAHAYA)
"""
            return confidence, explanation
    
    ml_confidence = 0
    es_confidence = 0
    
    # === KOMPONEN ML (0% atau 25%) ===
    if ml_result is not None and es_result is not None:
        ml_normalized = ml_result.strip()
        es_normalized = es_result.strip()
        
        if ml_normalized == es_normalized:
            ml_confidence = 25
            ml_note = f"ML SETUJU dengan ES ({ml_normalized}) → +25%"
        else:
            ml_confidence = 0
            ml_note = f"ML TIDAK SETUJU dengan ES (ML: {ml_normalized}, ES: {es_normalized}) → 0%"
    else:
        ml_note = "ML tidak tersedia"
    
    # === KOMPONEN ES (0-75%) ===
    if status == "Layak Minum":
        base_es = 40
        max_es = 75
        
        max_firing_strength = max(firing_strength.values()) if firing_strength else 0
        strength_bonus = int(max_firing_strength * 10)
        
        quality_adjustment = 0
        
        if 6.95 <= ph <= 7.05:
            quality_adjustment += 3
        elif 6.8 <= ph <= 7.2:
            quality_adjustment += 2
        elif 6.5 <= ph <= 8.5:
            quality_adjustment += 1
        
        if tds <= 300:
            quality_adjustment += 3
        elif tds <= 500:
            quality_adjustment += 2
        elif tds <= 600:
            quality_adjustment += 1
        
        if ntu <= 1:
            quality_adjustment += 4
        elif ntu <= 3:
            quality_adjustment += 3
        elif ntu <= 5:
            quality_adjustment += 2
        
        rule_specificity_bonus = 0
        priority_rules = ['R19', 'R20', 'R21', 'R22']
        high_priority_rules = ['R17', 'R18']
        
        for rule_name, strength, condition in rules_fired:
            if rule_name in priority_rules:
                rule_specificity_bonus = max(rule_specificity_bonus, 15)
            elif rule_name in high_priority_rules:
                rule_specificity_bonus = max(rule_specificity_bonus, 10)
        
        es_confidence = base_es + strength_bonus + quality_adjustment + rule_specificity_bonus
        es_confidence = max(0, min(max_es, es_confidence))
        
        explanation_detail = f"""
  - Base ES (Layak Minum): {base_es}%
  - Firing Strength: +{strength_bonus}% (μ={max_firing_strength:.3f})
  - Parameter Quality: +{quality_adjustment}%
    · pH {ph:.2f}: {'optimal' if 6.95 <= ph <= 7.05 else 'baik' if 6.5 <= ph <= 8.5 else 'buruk'}
    · TDS {tds:.1f}: {'optimal' if tds <= 300 else 'baik' if tds <= 600 else 'cukup'}
    · NTU {ntu:.2f}: {'optimal' if ntu <= 1 else 'baik' if ntu <= 5 else 'cukup'}
  - Rule Specificity: +{rule_specificity_bonus}%"""
    
    elif status == "Cukup Layak Minum":
        base_es = 25
        max_es = 50
        
        max_firing_strength = max(firing_strength.values()) if firing_strength else 0
        strength_bonus = int(max_firing_strength * 10)
        
        quality_adjustment = 0
        
        if 6.95 <= ph <= 7.05:
            quality_adjustment += 2
        elif 6.8 <= ph <= 7.2:
            quality_adjustment += 1
        
        if tds <= 300:
            quality_adjustment += 2
        elif tds <= 500:
            quality_adjustment += 1
        
        if ntu <= 1:
            quality_adjustment += 1
        
        rule_specificity_bonus = 0
        medium_priority_rules = ['R11', 'R12', 'R13', 'R14', 'R15', 'R16']
        
        for rule_name, strength, condition in rules_fired:
            if rule_name in medium_priority_rules:
                rule_specificity_bonus = max(rule_specificity_bonus, 10)
            else:
                rule_specificity_bonus = max(rule_specificity_bonus, 5)
        
        es_confidence = base_es + strength_bonus + quality_adjustment + rule_specificity_bonus
        es_confidence = max(0, min(max_es, es_confidence))
        
        explanation_detail = f"""
  - Base ES (Cukup Layak): {base_es}%
  - Firing Strength: +{strength_bonus}% (μ={max_firing_strength:.3f})
  - Parameter Quality: +{quality_adjustment}%
  - Rule Specificity: +{rule_specificity_bonus}%"""
    
    else:  # "Tidak Layak Minum"
        es_confidence = 0
        explanation_detail = "  - Base ES (Tidak Layak): 0% (tidak ada kontribusi)"
    
    # === TOTAL CONFIDENCE ===
    confidence = ml_confidence + es_confidence
    confidence = max(0, min(100, confidence))
    
    explanation = f"""
Perhitungan Confidence (Sistem Baru):
• Komponen ML (0% atau 25%): {ml_confidence}%
  {ml_note}
• Komponen ES (0-75%): {es_confidence}%
{explanation_detail}
• TOTAL: {confidence}% ({ml_confidence}% ML + {es_confidence}% ES)
"""
    
    return confidence, explanation


def hybrid_decision(ph, tds, ntu, ml_result):
    """
    Hybrid decision system: menggabungkan ML dan ES dengan voting logic
    """
    
    es_status, score, details, has_active_rules = fuzzy_inference(ph, tds, ntu)
    
    if ml_result == es_status:
        final_status = ml_result
        decision_note = "✅ ML dan ES setuju"
    
    elif ml_result == "Tidak Layak Minum" and es_status == "Layak Minum":
        final_status = "Layak Minum"
        decision_note = "⚖️ ES diprioritaskan (rule-based lebih spesifik untuk kondisi Layak)"
    
    elif ml_result == "Tidak Layak Minum" and es_status == "Cukup Layak Minum":
        final_status = "Cukup Layak Minum"
        decision_note = "⚖️ ES diprioritaskan (rule-based lebih spesifik untuk kondisi Cukup Layak)"
    
    elif ml_result == "Layak Minum" and es_status == "Cukup Layak Minum":
        final_status = "Cukup Layak Minum"
        decision_note = "⚖️ ES diprioritaskan (rule-based lebih spesifik untuk kondisi Cukup Layak)"
    
    elif ml_result == "Layak Minum" and es_status == "Tidak Layak Minum":
        final_status = "Tidak Layak Minum"
        decision_note = "⚠️ Prioritas keamanan (ES mendeteksi kondisi tidak aman)"
    
    else:
        final_status = es_status
        decision_note = "⚖️ Menggunakan hasil ES"
    
    return final_status, es_status, ml_result, decision_note, details, has_active_rules


def evaluate_water_quality(ph, tds, ntu, ml_result=None):
    """
    Evaluasi kualitas air menggunakan Fuzzy Logic (Trapezoidal)
    """
    
    explanations = []
    
    if ml_result is not None:
        final_status, es_status, ml_status, decision_note, details, has_active_rules = hybrid_decision(ph, tds, ntu, ml_result)
        score = details['score']
    else:
        es_status, score, details, has_active_rules = fuzzy_inference(ph, tds, ntu)
        final_status = es_status
        ml_status = None
        decision_note = None
    
    explanations.append(f"pH = {ph}")
    explanations.append(f"TDS = {tds} mg/L")
    explanations.append(f"Kekeruhan = {ntu} NTU")
    
    ph_sig = [f"{k}: {v:.3f}" for k, v in details['ph_membership'].items() if v > 0]
    if ph_sig:
        explanations.append(f"\npH Fuzzy: {', '.join(ph_sig)}")
    
    tds_sig = [f"{k}: {v:.3f}" for k, v in details['tds_membership'].items() if v > 0]
    if tds_sig:
        explanations.append(f"TDS Fuzzy: {', '.join(tds_sig)}")
    
    ntu_sig = [f"{k}: {v:.3f}" for k, v in details['ntu_membership'].items() if v > 0]
    if ntu_sig:
        explanations.append(f"Kekeruhan Fuzzy: {', '.join(ntu_sig)}")
    
    if not has_active_rules:
        explanations.append("\n❌ Tidak ada aturan sistem pakar yang aktif")
        explanations.append("Kombinasi parameter tidak memenuhi kriteria keamanan apapun")
        
        # Confidence calculation untuk no rules
        if ml_result is not None:
            if ml_result == "Layak Minum":
                confidence = 25
                explanations.append(f"\n⚠️ Confidence: {confidence}% (hanya dari ML yang memprediksi Layak, ES tidak aktif)")
            else:
                confidence = 0
                explanations.append(f"\n⚠️ Confidence: {confidence}% (ML setuju dengan kondisi tidak pasti, tidak ada kontribusi)")
        else:
            confidence = 0
        
        return final_status, explanations, confidence, has_active_rules
    
    if details['rules_fired']:
        explanations.append("\n✅ Aturan Aktif:")
        for rule_name, strength, condition in details['rules_fired']:
            explanations.append(f"  {rule_name} (μ={strength:.3f}): {condition}")
    
    explanations.append("\nFiring Strength:")
    for status_label, strength in details['firing_strength'].items():
        if strength > 0:
            explanations.append(f"  {status_label}: {strength:.3f}")
    
    confidence, confidence_explanation = calculate_confidence(
        final_status,
        details['firing_strength'], 
        details['rules_fired'],
        ph, tds, ntu,
        details['ph_membership'],
        details['tds_membership'],
        details['ntu_membership'],
        ml_result,
        es_status
    )
    
    explanations.append(f"\nDefuzzifikasi Score: {score:.2f}")
    
    if ml_result is not None:
        explanations.append(f"\n🤖 Prediksi ML: {ml_status}")
        explanations.append(f"🧠 Prediksi ES: {es_status}")
        explanations.append(f"⚖️ Keputusan: {decision_note}")
        explanations.append(f"🎯 Status Final: {final_status}")
    else:
        explanations.append(f"Status Akhir: {final_status}")
    
    explanations.append(confidence_explanation)
    
    return final_status, explanations, confidence, has_active_rules


def get_recommendations(status, ph, tds, ntu):
    """
    Memberikan rekomendasi berdasarkan status kualitas air (umum untuk berbagai sumber)
    """
    recommendations = []
    
    if status == "Tidak Layak Minum":
        recommendations.append("❌ AIR TIDAK AMAN UNTUK DIMINUM")
        recommendations.append("• JANGAN konsumsi air ini dalam kondisi apapun")
        recommendations.append("")
        
        problems = []
        
        # Cek masalah pH
        if ph <= 6.5:
            problems.append(f"pH terlalu asam ({ph:.2f}) - risiko iritasi lambung")
        elif ph >= 8.6:
            problems.append(f"pH terlalu basa ({ph:.2f}) - risiko gangguan pencernaan")
        
        # Cek masalah TDS
        if tds >= 1200:
            problems.append(f"TDS sangat tinggi ({tds:.1f} mg/L) - kandungan mineral berlebihan")
        elif tds >= 901:
            problems.append(f"TDS tinggi ({tds:.1f} mg/L) - melebihi batas standar")
        
        # Cek masalah Kekeruhan
        if ntu > 100:
            problems.append(f"Kekeruhan sangat tinggi ({ntu:.2f} NTU) - risiko kontaminasi mikroba")
        elif ntu > 25:
            problems.append(f"Kekeruhan tinggi ({ntu:.2f} NTU) - tidak memenuhi standar")
        
        if problems:
            recommendations.append("**Masalah Terdeteksi:**")
            for problem in problems:
                recommendations.append(f"• {problem}")
            recommendations.append("")
        
        recommendations.append("**Tindakan:**")
        recommendations.append("• Hentikan konsumsi segera")
        recommendations.append("• Gunakan sumber air alternatif yang aman")
        recommendations.append("• Laporkan ke pihak terkait jika dari kemasan/distributor")
    
    elif status == "Cukup Layak Minum":
        recommendations.append("⚠️ AIR DAPAT DIMINUM DENGAN CATATAN")
        recommendations.append("• Kualitas memenuhi batas minimal namun belum optimal")
        recommendations.append("")
        
        notes = []
        
        # Cek pH
        if 6.6 <= ph <= 6.9:
            notes.append(f"pH sedikit asam ({ph:.2f}) - masih aman")
        elif 7.1 <= ph <= 8.5:
            notes.append(f"pH sedikit basa ({ph:.2f}) - masih aman")
        
        # Cek TDS
        if 601 <= tds <= 900:
            notes.append(f"TDS cukup tinggi ({tds:.1f} mg/L) - dapat diterima")
        elif 301 <= tds <= 600:
            notes.append(f"TDS baik ({tds:.1f} mg/L)")
        
        # Cek Kekeruhan
        if 5.1 <= ntu <= 25:
            notes.append(f"Kekeruhan cukup tinggi ({ntu:.2f} NTU)")
        elif 1.1 <= ntu <= 5:
            notes.append(f"Kekeruhan baik ({ntu:.2f} NTU)")
        
        if notes:
            recommendations.append("**Catatan:**")
            for note in notes:
                recommendations.append(f"• {note}")
            recommendations.append("")
        
        recommendations.append("**Saran:**")
        recommendations.append("• Aman untuk dikonsumsi sehari-hari")
        recommendations.append("• Pertimbangkan sumber dengan kualitas lebih baik")
        recommendations.append("• Monitor kualitas secara berkala")
    
    else:  # Layak Minum
        recommendations.append("✅ AIR AMAN DAN BERKUALITAS BAIK")
        recommendations.append("• Memenuhi standar WHO untuk air minum")
        recommendations.append("• Aman untuk konsumsi jangka panjang")
        recommendations.append("")
        
        recommendations.append("**Saran:**")
        recommendations.append("• Simpan di tempat sejuk dan bersih")
        recommendations.append("• Hindari paparan sinar matahari langsung")
        recommendations.append("• Lakukan pengecekan berkala untuk konsistensi")
    
    return recommendations
