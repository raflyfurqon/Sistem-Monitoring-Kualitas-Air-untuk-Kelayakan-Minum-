import joblib
import pandas as pd
import numpy as np


class WaterQualityModel:
    def __init__(self, model_path="water_potability_model.pkl"):
        """
        Initialize the water quality prediction model
        
        Args:
            model_path: Path to the saved model file
        """
        try:
            self.model = joblib.load(model_path)
            print(f"✅ Model loaded successfully from {model_path}")
            
            # Get feature names from the trained model
            if hasattr(self.model, 'feature_names_in_'):
                self.feature_names = list(self.model.feature_names_in_)
                print(f"📋 Model expects features: {self.feature_names}")
            else:
                # Fallback jika model tidak menyimpan feature names
                # Sesuaikan dengan urutan training data
                self.feature_names = ['ph', 'Solids', 'Turbidity']
                print(f"⚠️ Model doesn't have feature_names_in_, using default: {self.feature_names}")
                
        except FileNotFoundError:
            print(f"❌ Error: Model file '{model_path}' not found!")
            raise
        except Exception as e:
            print(f"❌ Error loading model: {str(e)}")
            raise

    def predict(self, ph, tds, ntu):
        """
        Predict water quality based on sensor readings
        
        Mapping:
        - ph (sensor)  -> ph (model) atau 'ph' kolom
        - tds (sensor) -> Solids (model) - Total Dissolved Solids
        - ntu (sensor) -> Turbidity (model) - Kekeruhan
        
        Args:
            ph: pH level (6.5-8.5 ideal)
            tds: Total Dissolved Solids in mg/L
            ntu: Turbidity in NTU
            
        Returns:
            str: "Layak Minum" or "Tidak Layak Minum"
        """
        try:
            # Debug: Print input values
            print(f"\n🔍 ML Model Input:")
            print(f"   pH  : {ph}")
            print(f"   TDS : {tds}")
            print(f"   NTU : {ntu}")
            
            # Create feature mapping based on model's expected features
            # Model biasanya dilatih dengan kolom: ph, Solids, Turbidity
            feature_mapping = {
                'ph': ph,
                'Solids': tds,  # TDS = Total Dissolved Solids
                'Turbidity': ntu  # NTU = Turbidity
            }
            
            # Buat DataFrame dengan urutan kolom sesuai model
            data = []
            for feature_name in self.feature_names:
                if feature_name in feature_mapping:
                    data.append(feature_mapping[feature_name])
                elif feature_name.lower() == 'ph':
                    data.append(ph)
                elif feature_name.lower() in ['solids', 'tds']:
                    data.append(tds)
                elif feature_name.lower() in ['turbidity', 'ntu']:
                    data.append(ntu)
                else:
                    # Jika ada feature lain yang tidak dikenali, isi dengan 0 atau NaN
                    print(f"⚠️ Unknown feature '{feature_name}', filling with median value")
                    data.append(0)
            
            X = pd.DataFrame([data], columns=self.feature_names)
            
            print(f"📊 DataFrame for prediction:")
            print(X)
            
            # Predict
            pred = self.model.predict(X)[0]
            
            # Get prediction probability if available
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                print(f"🎯 Prediction probabilities: {proba}")
            
            result = "Layak Minum" if pred == 1 else "Tidak Layak Minum"
            print(f"✅ ML Prediction: {result}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error during prediction: {str(e)}")
            print(f"   Input values: ph={ph}, tds={tds}, ntu={ntu}")
            # Return default prediction on error
            return "Tidak Layak Minum"

    def predict_with_confidence(self, ph, tds, ntu):
        """
        Predict with confidence score
        
        Returns:
            tuple: (prediction, confidence)
        """
        try:
            # Create input DataFrame
            feature_mapping = {
                'ph': ph,
                'Solids': tds,
                'Turbidity': ntu
            }
            
            data = [feature_mapping.get(fn, 0) for fn in self.feature_names]
            X = pd.DataFrame([data], columns=self.feature_names)
            
            # Get prediction
            pred = self.model.predict(X)[0]
            result = "Layak Minum" if pred == 1 else "Tidak Layak Minum"
            
            # Get confidence if model supports probability
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                confidence = int(max(proba) * 100)
            else:
                confidence = 85  # Default confidence
            
            return result, confidence
            
        except Exception as e:
            print(f"❌ Error in predict_with_confidence: {str(e)}")
            return "Tidak Layak Minum", 50


# Test the model if run directly
if __name__ == "__main__":
    print("=" * 60)
    print("TESTING WATER QUALITY ML MODEL")
    print("=" * 60)
    
    try:
        model = WaterQualityModel("water_potability_model.pkl")
        
        # Test cases
        test_cases = [
            (7.2, 120, 0.8, "Sempurna - pH netral, TDS rendah, jernih"),
            (6.8, 350, 8, "Cukup - pH sedikit asam, TDS sedang, agak keruh"),
            (5.5, 600, 15, "Buruk - pH asam, TDS tinggi, keruh"),
            (7, 30000, 3.5, "Baik - pH sedikit basa, TDS baik, jernih"),
        ]
        
        for i, (ph, tds, ntu, desc) in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"Test Case {i}: {desc}")
            print(f"{'='*60}")
            result = model.predict(ph, tds, ntu)
            print(f"Final Result: {result}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")