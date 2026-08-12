from flask import Flask, jsonify, request
import random
import os
import json
import time
import threading
from urllib.parse import urlparse

app = Flask(__name__)

# =========================================================
# إعدادات
# =========================================================

DATA_FILE = "server_data.json"

lock = threading.Lock()

current_data = {
    "code": "000000",
    "linked": False,
    "apps": "لا توجد تطبيقات مرفوعة بعد",
    "links": []
}


# =========================================================
# تحميل البيانات
# =========================================================

def load_data():

    global current_data

    try:

        if os.path.exists(DATA_FILE):

            with open(
                DATA_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                saved = json.load(file)

                if isinstance(saved, dict):

                    current_data.update(saved)

                    if not isinstance(
                        current_data.get("links"),
                        list
                    ):
                        current_data["links"] = []

    except Exception as e:

        print("Load error:", e)


# =========================================================
# حفظ البيانات
# =========================================================

def save_data():

    try:

        temp_file = DATA_FILE + ".tmp"

        with open(
            temp_file,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                current_data,
                file,
                ensure_ascii=False,
                indent=2
            )

        os.replace(
            temp_file,
            DATA_FILE
        )

        return True

    except Exception as e:

        print("Save error:", e)

        return False


load_data()


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({

        "success": True,

        "service":
            "Ahmed Khaled Server",

        "status":
            "online",

        "version":
            "3.0",

        "routes": [

            "/",

            "/generate-code",

            "/verify-code",

            "/check-status",

            "/save-link",

            "/links",

            "/clear-links",

            "/status"
        ]
    })


# =========================================================
# إنشاء كود جديد
# =========================================================

@app.route(
    "/generate-code",
    methods=["GET"]
)
def generate_code():

    with lock:

        code = str(
            random.randint(
                100000,
                999999
            )
        )

        current_data["code"] = code

        current_data["linked"] = False

        # -------------------------------------------------
        # إنشاء رابط تحقق للكود
        # -------------------------------------------------

        verify_link = (
            request.host_url.rstrip("/")
            + "/verify-code?code="
            + code
        )

        # -------------------------------------------------
        # إزالة رابط الكود السابق
        # حتى لا تتراكم الأكواد القديمة
        # -------------------------------------------------

        new_links = []

        for item in current_data.get(
            "links",
            []
        ):

            if not isinstance(item, dict):
                continue

            if item.get(
                "type"
            ) == "generated_code":

                continue

            new_links.append(item)

        current_data["links"] = new_links

        # -------------------------------------------------
        # حفظ رابط الكود الجديد
        # -------------------------------------------------

        code_link = {

            "type":
                "generated_code",

            "code":
                code,

            "url":
                verify_link,

            "created_at":
                int(time.time())
        }

        current_data["links"].append(
            code_link
        )

        saved = save_data()

    if not saved:

        return jsonify({

            "success": False,

            "message":
                "تم إنشاء الكود لكن فشل حفظه"
        }), 500

    return jsonify({

        "success":
            True,

        "code":
            code,

        "url":
            verify_link,

        "message":
            "تم إنشاء وحفظ كود الربط"
    })


# =========================================================
# التحقق من الكود
# =========================================================

@app.route(
    "/verify-code",
    methods=["GET"]
)
def verify_code():

    code_param = request.args.get(
        "code",
        ""
    ).strip()

    if not code_param:

        return jsonify({

            "success":
                False,

            "message":
                "لم يتم إرسال الكود"
        }), 400

    with lock:

        if code_param == current_data["code"]:

            current_data["linked"] = True

            save_data()

            return jsonify({

                "success":
                    True,

                "message":
                    "تم الربط بنجاح",

                "code":
                    code_param
            })

    return jsonify({

        "success":
            False,

        "message":
            "الكود غير صحيح"
    }), 400


# =========================================================
# فحص حالة الربط
# =========================================================

@app.route(
    "/check-status",
    methods=["GET"]
)
def check_status():

    with lock:

        return jsonify({

            "success":
                True,

            "linked":
                current_data["linked"],

            "code":
                current_data["code"]
        })


# =========================================================
# التحقق من الرابط
# =========================================================

def valid_url(url):

    try:

        parsed = urlparse(url)

        return (
            parsed.scheme in [
                "http",
                "https"
            ]
            and
            bool(parsed.netloc)
        )

    except Exception:

        return False


# =========================================================
# حفظ رابط
# =========================================================

@app.route(
    "/save-link",
    methods=["GET", "POST"]
)
def save_link():

    url = ""

    # -------------------------------------------------
    # GET
    # -------------------------------------------------

    if request.method == "GET":

        url = request.args.get(
            "url",
            ""
        ).strip()

    # -------------------------------------------------
    # POST
    # -------------------------------------------------

    elif request.method == "POST":

        try:

            data = request.get_json(
                silent=True
            )

            if isinstance(
                data,
                dict
            ):

                url = str(
                    data.get(
                        "url",
                        ""
                    )
                ).strip()

        except Exception:

            url = ""

    # -------------------------------------------------
    # فحص الرابط
    # -------------------------------------------------

    if not url:

        return jsonify({

            "success":
                False,

            "message":
                "لم يتم إرسال الرابط"
        }), 400

    if not valid_url(url):

        return jsonify({

            "success":
                False,

            "message":
                "الرابط غير صالح"
        }), 400

    with lock:

        # -------------------------------------------------
        # منع التكرار
        # -------------------------------------------------

        for item in current_data.get(
            "links",
            []
        ):

            if not isinstance(
                item,
                dict
            ):
                continue

            if item.get(
                "url"
            ) == url:

                return jsonify({

                    "success":
                        True,

                    "message":
                        "الرابط موجود مسبقاً",

                    "url":
                        url,

                    "duplicate":
                        True,

                    "count":
                        len(
                            current_data["links"]
                        )
                })

        # -------------------------------------------------
        # إنشاء سجل
        # -------------------------------------------------

        link_data = {

            "type":
                "saved_link",

            "url":
                url,

            "created_at":
                int(time.time())
        }

        current_data["links"].append(
            link_data
        )

        saved = save_data()

        if not saved:

            return jsonify({

                "success":
                    False,

                "message":
                    "فشل حفظ الرابط"
            }), 500

        return jsonify({

            "success":
                True,

            "message":
                "تم حفظ الرابط بالسيرفر",

            "url":
                url,

            "count":
                len(
                    current_data["links"]
                )
        })


# =========================================================
# عرض جميع الروابط
# =========================================================

@app.route(
    "/links",
    methods=["GET"]
)
def get_links():

    with lock:

        links = current_data.get(
            "links",
            []
        )

        return jsonify({

            "success":
                True,

            "count":
                len(links),

            "current_code":
                current_data.get(
                    "code",
                    ""
                ),

            "linked":
                current_data.get(
                    "linked",
                    False
                ),

            "links":
                links
        })


# =========================================================
# حذف جميع الروابط
# =========================================================

@app.route(
    "/clear-links",
    methods=[
        "GET",
        "POST"
    ]
)
def clear_links():

    with lock:

        current_data["links"] = []

        save_data()

    return jsonify({

        "success":
            True,

        "message":
            "تم حذف جميع الروابط"
    })


# =========================================================
# معلومات السيرفر
# =========================================================

@app.route(
    "/status",
    methods=["GET"]
)
def server_status():

    with lock:

        return jsonify({

            "success":
                True,

            "service":
                "Ahmed Khaled Server",

            "online":
                True,

            "linked":
                current_data["linked"],

            "current_code":
                current_data["code"],

            "links_count":
                len(
                    current_data["links"]
                ),

            "time":
                int(time.time())
        })


# =========================================================
# تشغيل Render
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print(
        "Ahmed Khaled Server started"
    )

    print(
        "Port:",
        port
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
        )
