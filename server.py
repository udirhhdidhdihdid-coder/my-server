from flask import Flask, jsonify, request, send_file
import random
import os
import json
import time
import threading
import tempfile
import shutil
import yt_dlp
from urllib.parse import urlparse

app = Flask(__name__)

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

                    if "links" not in current_data:
                        current_data["links"] = []

    except Exception as e:

        print(
            "Load error:",
            str(e)
        )


# =========================================================
# حفظ البيانات
# =========================================================

def save_data():

    try:

        with open(
            DATA_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                current_data,
                file,
                ensure_ascii=False,
                indent=2
            )

        return True

    except Exception as e:

        print(
            "Save error:",
            str(e)
        )

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
            "4.0",

        "routes": [

            "/",

            "/generate-code",

            "/verify-code",

            "/check-status",

            "/save-link",

            "/links",

            "/clear-links",

            "/status",

            "/download-video"

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

        save_data()

    return jsonify({

        "success": True,

        "code": code

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

    with lock:

        if code_param == current_data["code"]:

            current_data["linked"] = True

            save_data()

            return jsonify({

                "success": True,

                "message":
                    "تم الربط بنجاح"

            })

    return jsonify({

        "success": False,

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

            "success": True,

            "linked":
                current_data["linked"],

            "code":
                current_data["code"]

        })


# =========================================================
# التحقق من الرابط
# =========================================================

def valid_http_url(url):

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

    # -----------------------------------------------------
    # GET
    # -----------------------------------------------------

    if request.method == "GET":

        url = request.args.get(
            "url",
            ""
        ).strip()

    # -----------------------------------------------------
    # POST
    # -----------------------------------------------------

    else:

        try:

            data = request.get_json(
                silent=True
            )

            if isinstance(data, dict):

                url = str(
                    data.get(
                        "url",
                        ""
                    )
                ).strip()

        except Exception:

            url = ""

    # -----------------------------------------------------
    # فحص الرابط
    # -----------------------------------------------------

    if not url:

        return jsonify({

            "success": False,

            "message":
                "لم يتم إرسال الرابط"

        }), 400

    if not valid_http_url(url):

        return jsonify({

            "success": False,

            "message":
                "الرابط غير صالح"

        }), 400

    # -----------------------------------------------------
    # حفظ الرابط
    # -----------------------------------------------------

    with lock:

        if "links" not in current_data:

            current_data["links"] = []

        # منع التكرار

        for item in current_data["links"]:

            if item.get("url") == url:

                return jsonify({

                    "success": True,

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

        # إضافة الرابط

        link_data = {

            "url":
                url,

            "created_at":
                int(time.time())

        }

        current_data["links"].append(
            link_data
        )

        save_data()

        return jsonify({

            "success": True,

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
# عرض الروابط
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

            "success": True,

            "count":
                len(links),

            "links":
                links

        })


# =========================================================
# حذف الروابط
# =========================================================

@app.route(
    "/clear-links",
    methods=["GET", "POST"]
)
def clear_links():

    with lock:

        current_data["links"] = []

        save_data()

    return jsonify({

        "success": True,

        "message":
            "تم حذف جميع الروابط"

    })


# =========================================================
# حالة السيرفر
# =========================================================

@app.route(
    "/status",
    methods=["GET"]
)
def server_status():

    with lock:

        return jsonify({

            "success": True,

            "service":
                "Ahmed Khaled Server",

            "online":
                True,

            "linked":
                current_data["linked"],

            "links_count":
                len(
                    current_data.get(
                        "links",
                        []
                    )
                ),

            "time":
                int(time.time())

        })


# =========================================================
# فحص رابط TikTok / Instagram
# =========================================================

def is_supported_video_url(video_url):

    allowed_hosts = [

        "tiktok.com",
        "www.tiktok.com",
        "vm.tiktok.com",
        "vt.tiktok.com",

        "instagram.com",
        "www.instagram.com"

    ]

    try:

        parsed = urlparse(
            video_url
        )

        hostname = (
            parsed.netloc
            .lower()
            .split(":")[0]
        )

        for host in allowed_hosts:

            if (
                hostname == host
                or
                hostname.endswith(
                    "." + host
                )
            ):

                return True

        return False

    except Exception:

        return False


# =========================================================
# تحميل فيديو
# =========================================================

@app.route(
    "/download-video",
    methods=["GET"]
)
def download_video():

    video_url = request.args.get(
        "url",
        ""
    ).strip()

    # -----------------------------------------------------
    # فحص الرابط
    # -----------------------------------------------------

    if not video_url:

        return jsonify({

            "success": False,

            "message":
                "لم يتم إرسال الرابط"

        }), 400

    if not valid_http_url(video_url):

        return jsonify({

            "success": False,

            "message":
                "الرابط غير صالح"

        }), 400

    if not is_supported_video_url(
        video_url
    ):

        return jsonify({

            "success": False,

            "message":
                "الرابط يجب أن يكون TikTok أو Instagram"

        }), 400

    # -----------------------------------------------------
    # حفظ الرابط
    # -----------------------------------------------------

    try:

        with lock:

            if "links" not in current_data:

                current_data["links"] = []

            exists = False

            for item in current_data["links"]:

                if item.get("url") == video_url:

                    exists = True

                    break

            if not exists:

                current_data["links"].append({

                    "url":
                        video_url,

                    "created_at":
                        int(time.time())

                })

                save_data()

    except Exception as e:

        print(
            "Save video link error:",
            str(e)
        )

    # -----------------------------------------------------
    # مجلد مؤقت
    # -----------------------------------------------------

    temp_dir = tempfile.mkdtemp(
        prefix="ahmed_video_"
    )

    output_template = os.path.join(
        temp_dir,
        "%(id)s.%(ext)s"
    )

    downloaded = None

    try:

        # -------------------------------------------------
        # إعداد yt-dlp
        # -------------------------------------------------

        options = {

            "outtmpl":
                output_template,

            "format":
                "best[ext=mp4]/best",

            "noplaylist":
                True,

            "quiet":
                True,

            "no_warnings":
                True,

            "restrictfilenames":
                True,

            "socket_timeout":
                30,

            "retries":
                2,

            "fragment_retries":
                2,

            "merge_output_format":
                "mp4"

        }

        print(
            "Downloading video:"
        )

        print(
            video_url
        )

        # -------------------------------------------------
        # تحميل الفيديو
        # -------------------------------------------------

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            info = ydl.extract_info(
                video_url,
                download=True
            )

            downloaded = (
                ydl.prepare_filename(
                    info
                )
            )

        # -------------------------------------------------
        # البحث عن الملف إذا تغير الامتداد
        # -------------------------------------------------

        if (
            downloaded is None
            or
            not os.path.exists(
                downloaded
            )
        ):

            files = os.listdir(
                temp_dir
            )

            video_files = []

            for file_name in files:

                file_path = os.path.join(
                    temp_dir,
                    file_name
                )

                if os.path.isfile(
                    file_path
                ):

                    video_files.append(
                        file_path
                    )

            if not video_files:

                return jsonify({

                    "success": False,

                    "message":
                        "تم التحميل لكن لم يتم العثور على ملف الفيديو"

                }), 500

            downloaded = video_files[0]

        # -------------------------------------------------
        # فحص حجم الملف
        # -------------------------------------------------

        if (
            not os.path.isfile(
                downloaded
            )
            or
            os.path.getsize(
                downloaded
            ) <= 0
        ):

            return jsonify({

                "success": False,

                "message":
                    "ملف الفيديو فارغ"

            }), 500

        # -------------------------------------------------
        # اسم الملف
        # -------------------------------------------------

        filename = os.path.basename(
            downloaded
        )

        # -------------------------------------------------
        # إرسال الفيديو
        # -------------------------------------------------

        response = send_file(

            downloaded,

            as_attachment=False,

            download_name=filename,

            mimetype="video/mp4"

        )

        # -------------------------------------------------
        # حذف المجلد بعد انتهاء الاستجابة
        # -------------------------------------------------

        @response.call_on_close
        def cleanup():

            try:

                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True
                )

            except Exception as e:

                print(
                    "Cleanup error:",
                    str(e)
                )

        return response

    except Exception as e:

        print(
            "Video download error:"
        )

        print(
            str(e)
        )

        return jsonify({

            "success": False,

            "message":
                "تعذر تحميل الفيديو",

            "error":
                str(e)

        }), 500

    finally:

        # لا نحذف هنا لأن send_file
        # يحتاج الملف أثناء الإرسال

        pass


# =========================================================
# تشغيل السيرفر
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
