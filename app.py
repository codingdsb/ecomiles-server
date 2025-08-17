from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import model

load_dotenv()

app = Flask(__name__)

PORT = os.getenv("PORT")
PROD = os.getenv("PROD", "false").lower() == "true"



@app.route("/api/get-route", methods=["POST"])
def get_route():
    
    try:
        data = request.get_json()
        print(f"\n\nDATA\n{type(data)}\n{data}\n\n")
        route = model.get_route(
            start_lat=data["source"]["lat"],
            start_lon=data["source"]["long"],
            end_lat=data["destination"]["lat"],
            end_lon=data["destination"]["long"],
            date=data["date"],
            month=data["month"],
            hour=data["hour"],
            weekday=int(1<=data["day"]<=5),
            weekend=int(6<=data["day"]<=7)
        )
        print(f"\n\nROUTE\n{route}\n\n")
    
        return jsonify(route)
    except Exception as e:
        print("\nCustom Error:\n")
        print(e, "\n\n")
        return jsonify({"hello": "world"})
    

if __name__ == "__main__":
    app.run(port=PORT, debug=(not PROD))