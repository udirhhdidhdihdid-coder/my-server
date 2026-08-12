from flask import Flask, jsonify, request, send_file
import random
import os
import json
import time
import threading
import tempfile
import uuid
import yt_dlp

app = Flask(__name__)

DATA_FILE = "server_data.json"
lock = threading.Lock()

current_data = {
    "code": "000000",
    "linked": False,
    "apps": "لا توجد تطبيقات مرفوعة بعد",
    "links": []
}


def load_data():
    global current_data

    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                saved = json.load(file)

                if isinstance(saved, dict):
                    current_data.update(saved)

                    if "links" not in current_data:
                        current_data["links"] = []

    except Exception as e:
        print("Load error:", e)


def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump(
                current_data,
                file,
                ensure_ascii=False,
                indent=2
            )

        return True

    except Exception as e:
        print("Save error:", e)
        return False


load_data()


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "service": "Ahmed Khaled Server",
        "status": "online",
        "version": "3.0",
        "routes": [
            "/",
            "/generate-code",
            "/verify-code",
            "/check-status",
            "/save-link",
            "/links",
            "/clear-links",
            "/download-video"
        ]
    })


@app.route("/generate-code", methods=["GET"])
def generate_code():

    with lock:

        code = str(random.randint(100000, 999999))

        current_data["code"] = code
        current_data["linked"] = False

        save_data()

    return jsonify({
        "success": True,
        "code": code
    })


@app.route("/verify-code", methods=["GET"])
def verify_code():

    code_param = request.args.get("code", "").strip()

    with lock:

        if code_param == current_data["code"]:

            current_data["linked"] = True

            save_data()

            return jsonify({
                "success": True,
                "message": "تم الربط بنجاح"
            })

    return jsonify({
        "success": False,
        "message": "الكود غير صحيح"
    }), 400


@app.route("/check-status", methods=["GET"])
def check_status():

    with lock:

        return jsonify({
            "success": True,
            "linked": current_data["linked"],
            "code": current_data["code"]
        })


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

            data = request.get_json(silent=True)

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
            "message": "لم يتم إرسال الرابط"
        }), 400

    if not (
        url.startswith("http://")
        or
        url.startswith("https://")
    ):

        return jsonify({
            "success": False,
            "message": "الرابط غير صالح"
        }), 400

    with lock:

        for item in current_data["links"]:

            if item.get("url") == url:

                return jsonify({
                    "success": True,
                    "message": "الرابط موجود مسبقاً",
                    "url": url,
                    "duplicate": True,
                    "count": len(current_data["links"])
                })

        current_data["links"].append({
            "url": url,
            "created_at": int(time.time())
        })

        save_data()

        return jsonify({
            "success": True,
            "message": "تم حفظ الرابط بالسيرفر",
            "url": url,
            "count": len(current_data["links"])
        })


@app.route("/links", methods=["GET"])
def get_links():

    with lock:

        links = current_data.get(
            "links",
            []
        )

        return jsonify({
            "success": True,
            "count": len(links),
            "links": links
        })


@app.route("/clear-links", methods=["GET", "POST"])
def clear_links():

    with lock:

        current_data["links"] = []

        save_data()

    return jsonify({
        "success": True,
        "message": "تم حذف جميع الروابط"
    })


@app.route("/status", methods=["GET"])
def server_status():

    with lock:

        return jsonify({
            "success": True,
            "service": "Ahmed Khaled Server",
            "online": True,
            "linked": current_data["linked"],
            "links_count": len(
                current_data["links"]
            ),
            "time": int(time.time())
        })


# =========================================================
# تحميل فيديو من رابط عام
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
            "message": "لم يتم إرسال الرابط"
        }), 400

    allowed_hosts = [
        "tiktok.com",
        "www.tiktok.com",
        "vm.tiktok.com",
        "vt.tiktok.com",
        "instagram.com",
        "www.instagram.com"
    ]

    try:

        from urllib.parse import urlparse

        parsed = urlparse(video_url)

        hostname = parsed.netloc.lower()

        valid = False

        for host in allowed_hosts:

            if hostname == host or hostname.endswith("." + host):
                valid = True
                break

        if not valid:

            return jsonify({
                "success": False,
                "message": "الرابط ليس TikTok أو Instagram"
            }), 400

    except Exception:

        return jsonify({
            "success": False,
            "message": "الرابط غير صالح"
        }), 400

    temp_dir = tempfile.mkdtemp(
        prefix="ahmed_video_"
    )

    output_template = os.path.join(
        temp_dir,
        "%(id)s.%(ext)s"
    )

    try:

        options = {
            "outtmpl": output_template,
            "format": "best[ext=mp4]/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "restrictfilenames": True,
            "socket_timeout": 30,
        }

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                video_url,
                download=True
            )

            downloaded = ydl.prepare_filename(info)

        if not os.path.exists(downloaded):

            files = os.listdir(temp_dir)

            if not files:

                return jsonify({
                    "success": False,
                    "message": "لم يتم العثور على الفيديو"
                }), 500

            downloaded = os.path.join(
                temp_dir,
                files[0]
            )

        filename = os.path.basename(
            downloaded
        )

        return send_file(
            downloaded,
            as_attachment=False,
            download_name=filename,
            mimetype="video/mp4"
        )

    except Exception as e:

        print(
            "Video download error:",
            str(e)
        )

        return jsonify({
            "success": False,
            "message": "تعذر تحميل الفيديو",
            "error": str(e)
        }), 500


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
