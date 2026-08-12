from flask import Flask, jsonify, request
import random
import time

app = Flask(__name__)

# =========================================================
# البيانات المؤقتة
# =========================================================

current_data = {
    "code": "000000",
    "linked": False,
    "apps": [],
    "links": []
}


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "service": "Ahmed Khaled Server",
        "status": "online",
        "code": current_data["code"],
        "linked": current_data["linked"],
        "links_count": len(current_data["links"])
    })


# =========================================================
# إنشاء كود جديد
# =========================================================

@app.route("/generate-code", methods=["GET"])
def generate_code():

    code = str(
        random.randint(100000, 999999)
    )

    current_data["code"] = code
    current_data["linked"] = False

    return jsonify({
        "success": True,
        "code": code
    })


# =========================================================
# التحقق من الكود
# =========================================================

@app.route("/verify-code", methods=["GET"])
def verify_code():

    code_param = request.args.get(
        "code",
        ""
    ).strip()

    if code_param == current_data["code"]:

        current_data["linked"] = True

        return jsonify({
            "success": True,
            "message": "تم الربط بنجاح"
        })

    return jsonify({
        "success": False,
        "message": "كود خطأ"
    }), 400


# =========================================================
# فحص حالة الربط
# =========================================================

@app.route("/check-status", methods=["GET"])
def check_status():

    return jsonify({
        "success": True,
        "linked": current_data["linked"],
        "code": current_data["code"]
    })


# =========================================================
# استقبال رابط من البوت
# =========================================================

@app.route("/add-link", methods=["POST"])
def add_link():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "message": "لم يتم إرسال بيانات"
        }), 400

    link = str(
        data.get("url", "")
    ).strip()

    if not link:

        return jsonify({
            "success": False,
            "message": "الرابط فارغ"
        }), 400

    if not (
        link.startswith("http://")
        or
        link.startswith("https://")
    ):

        return jsonify({
            "success": False,
            "message": "الرابط غير صالح"
        }), 400

    item = {
        "url": link,
        "created_at": int(time.time())
    }

    current_data["links"].append(
        item
    )

    return jsonify({
        "success": True,
        "message": "تم حفظ الرابط",
        "url": link,
        "total_links": len(
            current_data["links"]
        )
    })


# =========================================================
# عرض الروابط
# =========================================================

@app.route("/links", methods=["GET"])
def get_links():

    return jsonify({
        "success": True,
        "count": len(
            current_data["links"]
        ),
        "links": current_data["links"]
    })


# =========================================================
# حذف جميع الروابط
# =========================================================

@app.route("/clear-links", methods=["POST"])
def clear_links():

    current_data["links"] = []

    return jsonify({
        "success": True,
        "message": "تم حذف جميع الروابط"
    })


# =========================================================
# تشغيل السيرفر
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
