from flask import Flask, jsonify, request
import random
import time
import re

app = Flask(__name__)

current_data = {
    "code": "000000",
    "linked": False,
    "apps": "لا توجد تطبيقات مرفوعة بعد",
    "links": []
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
        "code": current_data["code"],
        "linked": current_data["linked"]
    })


@app.route("/add-link", methods=["GET", "POST"])
def add_link():

    url = ""

    if request.method == "POST":

        data = request.get_json(silent=True) or {}

        url = str(
            data.get("url", "")
        ).strip()

    else:

        url = request.args.get(
            "url",
            ""
        ).strip()

    if not url:

        return jsonify({
            "success": False,
            "message": "الرابط فارغ"
        }), 400

    if not re.match(
        r"^https?://",
        url,
        re.IGNORECASE
    ):

        return jsonify({
            "success": False,
            "message":
                "الرابط يجب أن يبدأ بـ http:// أو https://"
        }), 400

    item = {
        "url": url,
        "created_at": int(time.time())
    }

    current_data["links"].append(item)

    return jsonify({
        "success": True,
        "message": "تم حفظ الرابط",
        "link": item
    })


@app.route("/links", methods=["GET"])
def get_links():

    return jsonify({
        "success": True,
        "count": len(
            current_data["links"]
        ),
        "links":
            current_data["links"]
    })


@app.route("/clear-links", methods=["GET", "POST"])
def clear_links():

    current_data["links"] = []

    return jsonify({
        "success": True,
        "message":
            "تم حذف جميع الروابط"
    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000
    )
