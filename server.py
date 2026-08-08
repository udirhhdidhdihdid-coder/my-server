import os
from flask import Flask, jsonify, request
import random

app = Flask(__name__)

# متغيرات لحفظ حالة الكود، الربط، وقائمة التطبيقات مؤقتاً
current_data = {
    "code": "000000",
    "linked": False,
    "apps": "لا توجد تطبيقات مرفوعة بعد"
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

# مسار ليقوم الابن برفع قائمة التطبيقات المثبتة
@app.route('/upload-apps', methods=['POST'])
def upload_apps():
    data = request.json
    if data and "apps" in data:
        current_data["apps"] = data["apps"]
        return jsonify({"success": True, "message": "تم حفظ التطبيقات"})
    return jsonify({"success": False, "message": "خطأ بالبيانات"}), 400

# مسار ليقوم الأب بجلب قائمة تطبيقات الابن
@app.route('/get-apps', methods=['GET'])
def get_apps():
    return jsonify({
        "success": True,
        "apps": current_data["apps"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
