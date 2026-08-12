from flask import Flask, jsonify, request
import random

app = Flask(__name__)

current_data = {
    "code": "000000",
    "linked": False,
    "apps": "لا توجد تطبيقات مرفوعة بعد"
}


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "service": "Ahmed Khaled Server",
        "status": "online"
    })


@app.route("/generate-code", methods=["GET"])
def generate_code():
    code = str(random.randint(100000, 999999))

    current_data["code"] = code
    current_data["linked"] = False

    return jsonify({
        "success": True,
        "code": code
    })


@app.route("/verify-code", methods=["GET"])
def verify_code():
    code_param = request.args.get("code", "").strip()

    if code_param == current_data["code"]:
        current_data["linked"] = True

        return jsonify({
            "success": True,
            "message": "تم الربط"
        })

    return jsonify({
        "success": False,
        "message": "كود خطأ"
    }), 400


@app.route("/check-status", methods=["GET"])
def check_status():
    return jsonify({
        "success": True,
        "linked": current_data["linked"],
        "code": current_data["code"]
    })


@app.route("/social-link", methods=["POST"])
def social_link():
    data = request.get_json(silent=True) or {}

    link = str(data.get("link", "")).strip()

    if not link:
        return jsonify({
            "success": False,
            "message": "الرابط فارغ"
        }), 400

    link_lower = link.lower()

    if "instagram.com" in link_lower:
        platform = "Instagram"

    elif "tiktok.com" in link_lower:
        platform = "TikTok"

    else:
        return jsonify({
            "success": False,
            "message": "الرابط غير مدعوم"
        }), 400

    return jsonify({
        "success": True,
        "platform": platform,
        "link": link,
        "message": "تم استلام الرابط"
    })


if __name__ == "__main__":
    port = 10000

    app.run(
        host="0.0.0.0",
        port=port
    )
