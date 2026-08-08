import os
from flask import Flask, jsonify, request
import random

app = Flask(__name__)

# متغيرات لحفظ حالة الكود والربط مؤقتاً
current_data = {
    "code": "000000",
    "linked": False
}

@app.route('/generate-code', methods=['GET'])
def generate_code():
    code = str(random.randint(100000, 999999))
    current_data["code"] = code
    current_data["linked"] = False  # إعادة تعيين الحالة عند إنشاء كود جديد
    return jsonify({
        "success": True,
        "code": code
    })

# مسار يتحقق من الكود ويربط الجهاز (يستخدمه الأب)
@app.route('/verify-code', methods=['GET'])
def verify_code():
    code_param = request.args.get('code')
    if code_param == current_data["code"]:
        current_data["linked"] = True
        return jsonify({"success": True, "message": "تم الربط"})
    return jsonify({"success": False, "message": "كود خطأ"}), 400

# مسار يفحصه الابن دورياً لمعرفة هل تم الربط؟
@app.route('/check-status', methods=['GET'])
def check_status():
    return jsonify({
        "linked": current_data["linked"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
