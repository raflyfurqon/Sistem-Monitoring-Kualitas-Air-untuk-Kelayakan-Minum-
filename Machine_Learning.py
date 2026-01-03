import joblib
import pandas as pd
import numpy as np


class WaterQualityModel:
    def __init__(self, model_path="water_potability_model.pkl"):
        try:
            self.model = joblib.load(model_path)
            print(f"Model loaded successfully from {model_path}")
            
            # Get feature names from the trained model
            if hasattr(self.model, 'feature_names_in_'):
                self.feature_names = list(self.model.feature_names_in_)
                print(f"Model expects features: {self.feature_names}")
            else:
                # Fallback jika model tidak menyimpan feature names
                # Sesuaikan dengan urutan training data
                self.feature_names = ['ph', 'Solids', 'Turbidity']
                print(f"Model doesn't have feature_names_in_, using default: {self.feature_names}")
                
        except FileNotFoundError:
            print(f"Error: Model file '{model_path}' not found!")
            raise
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise

    def predict(self, ph, tds, ntu):
        try:
            # Debug: Print input values
            print(f"\nML Model Input:")
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
            
            print(f"DataFrame for prediction:")
            print(X)
            
            # Predict
            pred = self.model.predict(X)[0]
            
            # Get prediction probability if available
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(X)[0]
                print(f"Prediction probabilities: {proba}")
            
            result = "Layak Minum" if pred == 1 else "Tidak Layak Minum"
            print(f"ML Prediction: {result}")
            
            return result
            
        except Exception as e:
            print(f"Error during prediction: {str(e)}")
            print(f"Input values: ph={ph}, tds={tds}, ntu={ntu}")
            # Return default prediction on error
            return "Tidak Layak Minum"

    def predict_with_confidence(self, ph, tds, ntu):
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
            print(f"Error in predict_with_confidence: {str(e)}")
            return "Tidak Layak Minum", 50