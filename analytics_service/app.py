from flask import Flask, request, jsonify
import joblib
import numpy as np

app = Flask(__name__)
model = joblib.load("model.pkl")

@app.route("/predict", methods=["POST"])
def predict():
    basket = request.json.get("basket")
    if basket is None:
        return jsonify({"error": "Missing 'basket'"}), 400
    prediction = model.predict([basket])[0]
    return jsonify({"cluster": int(prediction)})
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

