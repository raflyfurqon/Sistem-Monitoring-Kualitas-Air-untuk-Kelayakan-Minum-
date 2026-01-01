"""
Expert System for Water Quality Evaluation
Sistem Pakar dengan Fuzzy Logic (Trapezoidal) berbasis Standar WHO
VERSI DIPERBAIKI
"""

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
# SISTEM INFERENSI FUZZY - DIPERBAIKI
# =============================

def fuzzy_inference(ph, tds, ntu):
    """
    Sistem inferensi fuzzy untuk evaluasi kualitas air
    PERBAIKAN: Rule R11-R24 sekarang konsisten dengan dokumentasi
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
    
    # --- ATURAN CUKUP LAYAK MINUM (R7-R18) ---
    
    # R7: pH Sedikit Asam AND TDS Cukup AND Kekeruhan Cukup
    r7 = min(ph_membership['Sedikit Asam'], tds_membership['Cukup'], ntu_membership['Cukup'])
    if r7 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r7)
        rules_fired.append(('R7', r7, 'pH Sedikit Asam, TDS Cukup, Kekeruhan Cukup'))
    
    # R8: pH Sedikit Basa AND TDS Cukup AND Kekeruhan Cukup
    r8 = min(ph_membership['Sedikit Basa'], tds_membership['Cukup'], ntu_membership['Cukup'])
    if r8 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r8)
        rules_fired.append(('R8', r8, 'pH Sedikit Basa, TDS Cukup, Kekeruhan Cukup'))
    
    # R9: pH Netral AND TDS Cukup AND Kekeruhan Baik
    r9 = min(ph_membership['Netral'], tds_membership['Cukup'], ntu_membership['Baik'])
    if r9 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r9)
        rules_fired.append(('R9', r9, 'pH Netral, TDS Cukup, Kekeruhan Baik'))
    
    # R10: pH Netral AND TDS Baik AND Kekeruhan Cukup
    r10 = min(ph_membership['Netral'], tds_membership['Baik'], ntu_membership['Cukup'])
    if r10 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r10)
        rules_fired.append(('R10', r10, 'pH Netral, TDS Baik, Kekeruhan Cukup'))   

    # R11: pH Sedikit Asam AND TDS Baik AND Kekeruhan Baik
    r11 = min(ph_membership['Sedikit Asam'], tds_membership['Baik'], ntu_membership['Baik'])
    if r11 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r11)
        rules_fired.append(('R11', r11, 'pH Sedikit Asam, TDS Baik, Kekeruhan Baik'))
    
    # R12: pH Sedikit Basa AND TDS Baik AND Kekeruhan Baik
    r12 = min(ph_membership['Sedikit Basa'], tds_membership['Baik'], ntu_membership['Baik'])
    if r12 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r12)
        rules_fired.append(('R12', r12, 'pH Sedikit Basa, TDS Baik, Kekeruhan Baik'))

    # R13: pH Sedikit Asam AND TDS Baik AND Kekeruhan Sempurna
    r13 = min(ph_membership['Sedikit Asam'], tds_membership['Baik'], ntu_membership['Sempurna'])
    if r13 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r13)
        rules_fired.append(('R13', r13, 'pH Sedikit Asam, TDS Baik, Kekeruhan Sempurna'))

    # R14: pH Sedikit Basa AND TDS Baik AND Kekeruhan Sempurna
    r14 = min(ph_membership['Sedikit Basa'], tds_membership['Baik'], ntu_membership['Sempurna'])
    if r14 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r14)
        rules_fired.append(('R14', r14, 'pH Sedikit Basa, TDS Baik, Kekeruhan Sempurna'))

    # R15: pH Sedikit Asam AND TDS Sempurna AND Kekeruhan Baik
    r15 = min(ph_membership['Sedikit Asam'], tds_membership['Sempurna'], ntu_membership['Baik'])
    if r15 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r15)
        rules_fired.append(('R15', r15, 'pH Sedikit Asam, TDS Sempurna, Kekeruhan Baik'))

    # R16: pH Sedikit Basa AND TDS Sempurna AND Kekeruhan Baik
    r16 = min(ph_membership['Sedikit Basa'], tds_membership['Sempurna'], ntu_membership['Baik'])
    if r16 > 0:
        firing_strength['Cukup Layak'] = max(firing_strength['Cukup Layak'], r16)
        rules_fired.append(('R16', r16, 'pH Sedikit Basa, TDS Sempurna, Kekeruhan Baik'))

    # --- ATURAN LAYAK MINUM (R19-R24) ---

    # R17: pH Sedikit Asam AND TDS Sempurna AND Kekeruhan Sempurna
    r17 = min(ph_membership['Sedikit Asam'], tds_membership['Sempurna'], ntu_membership['Sempurna'])
    if r17 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r17)
        rules_fired.append(('R17', r17, 'pH Sedikit Asam, TDS Sempurna, Kekeruhan Sempurna'))

    # R18: pH Sedikit Basa AND TDS Sempurna AND Kekeruhan Sempurna
    r18 = min(ph_membership['Sedikit Basa'], tds_membership['Sempurna'], ntu_membership['Sempurna'])
    if r18 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r18)
        rules_fired.append(('R18', r18, 'pH Sedikit Basa, TDS Sempurna, Kekeruhan Sempurna'))

    # R19: pH Netral AND TDS Sempurna AND Kekeruhan Sempurna
    r19 = min(ph_membership['Netral'], tds_membership['Sempurna'], ntu_membership['Sempurna'])
    if r19 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r19)
        rules_fired.append(('R19', r19, 'pH Netral, TDS Sempurna, Kekeruhan Sempurna'))

    # R20: pH Netral AND TDS Baik AND Kekeruhan Baik
    r20 = min(ph_membership['Netral'], tds_membership['Baik'], ntu_membership['Baik'])
    if r20 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r20)
        rules_fired.append(('R20', r20, 'pH Netral, TDS Baik, Kekeruhan Baik'))

    # R21: pH Netral AND TDS Sempurna AND Kekeruhan Baik
    r21 = min(ph_membership['Netral'], tds_membership['Sempurna'], ntu_membership['Baik'])
    if r21 > 0:
        firing_strength['Layak'] = max(firing_strength['Layak'], r21)
        rules_fired.append(('R21', r21, 'pH Netral, TDS Sempurna, Kekeruhan Baik'))

    # R22: pH Netral AND TDS Baik AND Kekeruhan Sempurna
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
    Menghitung tingkat keyakinan (confidence)
    """
    
    if status == "Layak Minum":
        base_confidence = 90
    elif status == "Cukup Layak Minum":
        base_confidence = 75
    else:
        base_confidence = 50
    
    max_firing_strength = max(firing_strength.values())
    strength_bonus = int(max_firing_strength * 5)
    
    quality_adjustment = 0
    
    if 6.9 <= ph <= 7.1:
        quality_adjustment += 5
    elif 6.5 <= ph <= 8.5:
        quality_adjustment += 2
    elif ph < 6.0 or ph > 9.0:
        quality_adjustment -= 5
    
    if tds <= 300:
        quality_adjustment += 5
    elif tds <= 600:
        quality_adjustment += 2
    elif tds > 900:
        quality_adjustment -= 5
    
    if ntu <= 1:
        quality_adjustment += 5
    elif ntu <= 5:
        quality_adjustment += 2
    elif ntu > 25:
        quality_adjustment -= 5
    
    rule_specificity_bonus = 0
    for rule_name, strength, condition in rules_fired:
        if rule_name in ['R19', 'R20', 'R21', 'R22', 'R23', 'R24']:
            rule_specificity_bonus = max(rule_specificity_bonus, 5)
        elif rule_name in ['R15', 'R16', 'R17', 'R18']:
            rule_specificity_bonus = max(rule_specificity_bonus, 4)
        elif rule_name in ['R13', 'R14']:
            rule_specificity_bonus = max(rule_specificity_bonus, 3)
    
    ml_es_adjustment = 0
    ml_es_note = ""
    
    if ml_result is not None and es_result is not None:
        ml_normalized = ml_result.strip()
        es_normalized = es_result.strip()
        
        if ml_normalized == es_normalized:
            ml_es_adjustment = 5
            ml_es_note = "ML dan ES setuju → BONUS +5%"
        else:
            status_levels = {
                "Layak Minum": 2,
                "Cukup Layak Minum": 1,
                "Tidak Layak Minum": 0
            }
            
            ml_level = status_levels.get(ml_normalized, 0)
            es_level = status_levels.get(es_normalized, 0)
            level_difference = abs(ml_level - es_level)
            
            if level_difference == 1:
                ml_es_adjustment = -15
                ml_es_note = f"ML ({ml_normalized}) ≠ ES ({es_normalized}) → PENALTY -15%"
            elif level_difference == 2:
                ml_es_adjustment = -20
                ml_es_note = f"ML ({ml_normalized}) ≠ ES ({es_normalized}) → PENALTY -20%"
            else:
                ml_es_adjustment = -15
                ml_es_note = f"ML dan ES berbeda pendapat → PENALTY -15%"
    
    confidence = base_confidence + strength_bonus + quality_adjustment + rule_specificity_bonus + ml_es_adjustment
    confidence = max(0, min(100, confidence))
    
    explanation = f"""
Perhitungan Confidence:
• Base Confidence ({status}): {base_confidence}%
• Firing Strength Bonus: +{strength_bonus}% (μ={max_firing_strength:.3f})
• Parameter Quality Adjustment: {quality_adjustment:+d}%
  - pH {ph}: {'optimal' if 6.9 <= ph <= 7.1 else 'baik' if 6.5 <= ph <= 8.5 else 'buruk'}
  - TDS {tds}: {'optimal' if tds <= 300 else 'baik' if tds <= 600 else 'cukup' if tds <= 900 else 'buruk'}
  - NTU {ntu}: {'optimal' if ntu <= 1 else 'baik' if ntu <= 5 else 'cukup' if ntu <= 25 else 'buruk'}
• Rule Specificity Bonus: +{rule_specificity_bonus}%"""
    
    if ml_result is not None and es_result is not None:
        explanation += f"\n• ML-ES Agreement: {ml_es_adjustment:+d}% ({ml_es_note})"
    
    explanation += f"\n• TOTAL CONFIDENCE: {confidence}%\n"
    
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
        confidence = 40
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
    Memberikan rekomendasi berdasarkan status kualitas air
    """
    recommendations = []
    
    if status == "Tidak Layak Minum":
        recommendations.append("❌ AIR TIDAK AMAN UNTUK DIMINUM")
        
        if ph <= 6.5:
            recommendations.append("• Naikkan pH menggunakan soda abu atau baking soda")
        elif ph >= 8.6:
            recommendations.append("• Turunkan pH menggunakan asam sitrat atau cuka")
            
        if tds >= 1200:
            recommendations.append("• TDS sangat tinggi - gunakan filter RO (Reverse Osmosis)")
        elif tds >= 901:
            recommendations.append("• TDS tinggi - pertimbangkan sistem filtrasi")
            
        if ntu > 100:
            recommendations.append("• Kekeruhan sangat tinggi - hentikan penggunaan segera")
            recommendations.append("• Periksa sumber kontaminasi")
        elif ntu > 25:
            recommendations.append("• Lakukan filtrasi atau sedimentasi untuk mengurangi kekeruhan")
            recommendations.append("• Periksa sistem penyaringan")
    
    elif status == "Cukup Layak Minum":
        recommendations.append("⚠️ AIR DAPAT DIMINUM DENGAN CATATAN")
        recommendations.append("• Pertimbangkan untuk melakukan perebusan")
        
        if 6.6 <= ph <= 6.9 or 7.1 <= ph <= 8.5:
            recommendations.append("• Monitor pH secara berkala")
            
        if 601 <= tds <= 900:
            recommendations.append("• TDS agak tinggi, pertimbangkan filtrasi")
        elif 301 <= tds <= 600:
            recommendations.append("• TDS dalam batas wajar, namun monitoring tetap diperlukan")
            
        if 5.1 <= ntu <= 25:
            recommendations.append("• Gunakan filter sederhana untuk mengurangi kekeruhan")
        elif 1.1 <= ntu <= 5:
            recommendations.append("• Kekeruhan masih dapat diterima, monitor secara berkala")
    
    else:  # Layak Minum
        recommendations.append("✅ AIR AMAN UNTUK DIMINUM")
        recommendations.append("• Kualitas air memenuhi standar WHO")
        
        # Rekomendasi spesifik untuk Rule 19 (pH Sedikit Asam)
        if 6.6 <= ph <= 6.9:
            recommendations.append("• pH sedikit asam - pertimbangkan untuk menaikkan pH secara bertahap")
            recommendations.append("• Gunakan media alkali seperti kalsit atau baking soda dalam dosis rendah")
            recommendations.append("• Monitor pH agar tidak turun di bawah 6.5")
        
        # Rekomendasi spesifik untuk Rule 20 (pH Sedikit Basa)
        elif 7.1 <= ph <= 8.5:
            recommendations.append("• pH sedikit basa - pertimbangkan untuk menurunkan pH secara bertahap jika mendekati 8.5")
            recommendations.append("• Gunakan media asam alami seperti gambut atau asam sitrat dalam dosis rendah")
            recommendations.append("• Monitor pH agar tidak naik di atas 8.5")
        
        recommendations.append("• Tetap jaga kebersihan sumber air")
        recommendations.append("• Lakukan pemeriksaan rutin untuk memastikan kualitas tetap terjaga")
    
    return recommendations


# =============================
# FUNGSI KLASIFIKASI CRISP (BACKUP)
# =============================

def klasifikasi_ph(ph):
    """
    Klasifikasi pH berdasarkan standar WHO untuk air minum
    Sesuai dokumentasi: Tabel 1 - Klasifikasi Tingkat pH
    """
    if ph <= 6.5:
        return "Asam"
    elif 6.6 <= ph <= 6.9:
        return "Sedikit Asam"
    elif 6.95 <= ph <= 7.05:
        return "Netral"
    elif 7.1 <= ph <= 8.5:
        return "Sedikit Basa"
    else:
        return "Basa"


def klasifikasi_tds(tds):
    """
    Klasifikasi TDS (Total Dissolved Solids) dalam mg/L
    Sesuai dokumentasi: Tabel 2 - Klasifikasi Total Padatan Terlarut (TDS)
    """
    if tds <= 300:
        return "Sempurna"
    elif 301 <= tds <= 600:
        return "Baik"
    elif 601 <= tds <= 900:
        return "Cukup"
    elif 901 <= tds <= 1199:
        return "Buruk"
    else:
        return "Tidak Diterima"


def klasifikasi_kekeruhan(ntu):
    """
    Klasifikasi Kekeruhan (Turbidity) dalam NTU
    Sesuai dokumentasi: Tabel 3 - Klasifikasi Kekeruhan
    """
    if ntu <= 1:
        return "Sempurna"
    elif 1.1 <= ntu <= 5:
        return "Baik"
    elif 5.1 <= ntu <= 25.0:
        return "Cukup"
    elif 25.1 <= ntu <= 100:
        return "Buruk"
    else:
        return "Tidak Diterima"
