from flask import Flask, jsonify, request, send_file
import random
import os
import json
import time
import threading
import tempfile
import shutil
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import yt_dlp


# =========================================================
# إنشاء Flask App
# =========================================================

app = Flask(__name__)


# =========================================================
# إعدادات السيرفر
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
# User-Agent
# =========================================================

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10; K) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/131.0.0.0 Mobile Safari/537.36"
)


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

        print("Load error:", str(e))


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

        print("Save error:", str(e))

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
            "5.0",

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
# توليد كود
# =========================================================

@app.route("/generate-code", methods=["GET"])
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

@app.route("/verify-code", methods=["GET"])
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
# حالة الربط
# =========================================================

@app.route("/check-status", methods=["GET"])
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
# حفظ الرابط
# =========================================================

@app.route("/save-link", methods=["GET", "POST"])
def save_link():

    url = ""

    if request.method == "GET":

        url = request.args.get(
            "url",
            ""
        ).strip()

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

    if not url:

        return jsonify({

            "success": False,

            "message":
                "لم يتم إرسال الرابط"

        }), 400

    if not (
        url.startswith("http://")
        or
        url.startswith("https://")
    ):

        return jsonify({

            "success": False,

            "message":
                "الرابط غير صالح"

        }), 400

    with lock:

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

        current_data["links"].append({

            "url":
                url,

            "created_at":
                int(time.time())

        })

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

@app.route("/links", methods=["GET"])
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

@app.route("/clear-links", methods=["GET", "POST"])
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

@app.route("/status", methods=["GET"])
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
                    current_data["links"]
                ),

            "time":
                int(time.time())

        })


# =========================================================
# التحقق من TikTok / Instagram
# =========================================================

def is_allowed_video_url(video_url):

    try:

        parsed = urlparse(video_url)

        hostname = (
            parsed.netloc
            .lower()
            .split(":")[0]
        )

        allowed_hosts = [

            "tiktok.com",
            "www.tiktok.com",
            "vt.tiktok.com",
            "vm.tiktok.com",

            "instagram.com",
            "www.instagram.com"

        ]

        for host in allowed_hosts:

            if (
                hostname == host
                or
                hostname.endswith("." + host)
            ):

                return True

        return False

    except Exception:

        return False


# =========================================================
# تنظيف الرابط
# =========================================================

def clean_video_url(video_url):

    if not video_url:
        return ""

    video_url = video_url.strip()

    video_url = (
        video_url
        .replace('"', "")
        .replace("'", "")
        .replace(")", "")
        .replace("]", "")
        .replace("}", "")
        .replace(",", "")
        .replace("،", "")
    )

    return video_url.strip()


# =========================================================
# حل الرابط المختصر
# =========================================================

def resolve_short_url(video_url):

    video_url = clean_video_url(video_url)

    try:

        req = Request(

            video_url,

            headers={

                "User-Agent":
                    USER_AGENT,

                "Accept":
                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",

                "Accept-Language":
                    "ar,en-US;q=0.9,en;q=0.8"

            }

        )

        response = urlopen(
            req,
            timeout=20
        )

        final_url = response.geturl()

        response.close()

        if final_url:

            print(
                "Original URL:",
                video_url
            )

            print(
                "Resolved URL:",
                final_url
            )

            return final_url

    except Exception as e:

        print(
            "Resolve URL error:",
            str(e)
        )

    return video_url


# =========================================================
# تحميل الفيديو
# =========================================================

@app.route("/download-video", methods=["GET"])
def download_video():

    video_url = request.args.get(
        "url",
        ""
    ).strip()

    if not video_url:

        return jsonify({

            "success": False,

            "message":
                "لم يتم إرسال الرابط"

        }), 400


    # تنظيف الرابط

    video_url = clean_video_url(
        video_url
    )


    # التحقق من الموقع

    if not is_allowed_video_url(
        video_url
    ):

        return jsonify({

            "success": False,

            "message":
                "الرابط ليس TikTok أو Instagram"

        }), 400


    # حل الرابط المختصر

    resolved_url = resolve_short_url(
        video_url
    )


    # التحقق مرة ثانية

    if not is_allowed_video_url(
        resolved_url
    ):

        resolved_url = video_url


    print(
        "Download request:"
    )

    print(
        "URL:",
        video_url
    )

    print(
        "Resolved:",
        resolved_url
    )


    # =====================================================
    # مجلد مؤقت
    # =====================================================

    temp_dir = tempfile.mkdtemp(
        prefix="ahmed_video_"
    )


    output_template = os.path.join(
        temp_dir,
        "%(id)s.%(ext)s"
    )


    try:

        # =================================================
        # إعدادات yt-dlp
        # =================================================

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
                3,

            "fragment_retries":
                3,

            "http_headers": {

                "User-Agent":
                    USER_AGENT,

                "Accept-Language":
                    "ar,en-US;q=0.9,en;q=0.8",

                "Referer":
                    "https://www.tiktok.com/"

            },

            "nocheckcertificate":
                True

        }


        # =================================================
        # تشغيل yt-dlp
        # =================================================

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            info = ydl.extract_info(
                resolved_url,
                download=True
            )

            downloaded = ydl.prepare_filename(
                info
            )


        # =================================================
        # البحث عن الملف
        # =================================================

        if not os.path.exists(
            downloaded
        ):

            files = os.listdir(
                temp_dir
            )

            if not files:

                return jsonify({

                    "success": False,

                    "message":
                        "yt-dlp لم ينتج ملف فيديو"

                }), 500

            downloaded = os.path.join(
                temp_dir,
                files[0]
            )


        # =================================================
        # التأكد من الملف
        # =================================================

        if not os.path.exists(
            downloaded
        ):

            return jsonify({

                "success": False,

                "message":
                    "لم يتم العثور على الفيديو"

            }), 500


        file_size = os.path.getsize(
            downloaded
        )


        if file_size <= 0:

            return jsonify({

                "success": False,

                "message":
                    "ملف الفيديو فارغ"

            }), 500


        filename = os.path.basename(
            downloaded
        )


        print(
            "Video downloaded:",
            filename
        )

        print(
            "Size:",
            file_size
        )


        # =================================================
        # إرسال الفيديو
        # =================================================

        response = send_file(

            downloaded,

            as_attachment=False,

            download_name=filename,

            mimetype="video/mp4"

        )


        # =================================================
        # تنظيف الملفات
        # =================================================

        @response.call_on_close
        def cleanup():

            try:

                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True
                )

            except Exception:
                pass


        return response


    except Exception as e:

        error_text = str(e)

        print(
            "================================"
        )

        print(
            "Video download error:"
        )

        print(
            error_text
        )

        print(
            "================================"
        )


        try:

            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

        except Exception:
            pass


        return jsonify({

            "success": False,

            "message":
                "تعذر تحميل الفيديو",

            "error":
                error_text

        }), 500


# =========================================================
# تشغيل السيرفر محلياً
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(

        host="0.0.0.0",

        port=port,

        debug=False

                )
