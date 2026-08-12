# =========================================================
# تحميل الفيديو
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

    if not video_url:

        return jsonify({
            "success": False,
            "message": "لم يتم إرسال الرابط"
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
            "message": "الرابط ليس TikTok أو Instagram"
        }), 400

    # محاولة حل الرابط المختصر
    resolved_url = resolve_short_url(
        video_url
    )

    # بعد التحويل نتحقق مرة ثانية
    if not is_allowed_video_url(
        resolved_url
    ):
        resolved_url = video_url

    print("================================")
    print("Download request:")
    print("Original URL:", video_url)
    print("Resolved URL:", resolved_url)
    print("================================")

    # إنشاء مجلد مؤقت
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
                False,

            "no_warnings":
                False,

            "restrictfilenames":
                True,

            "socket_timeout":
                60,

            "retries":
                5,

            "fragment_retries":
                5,

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

        print("Starting yt-dlp...")

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

        print(
            "Prepared filename:",
            downloaded
        )

        # =================================================
        # البحث عن الملف إذا تغير الامتداد
        # =================================================

        if not os.path.exists(
            downloaded
        ):

            files = os.listdir(
                temp_dir
            )

            print(
                "Files in temp directory:",
                files
            )

            if not files:

                return jsonify({

                    "success": False,

                    "message":
                        "yt-dlp لم ينتج ملف فيديو"

                }), 500

            # البحث عن أول ملف فعلي
            downloaded = os.path.join(
                temp_dir,
                files[0]
            )

        # =================================================
        # التأكد من وجود الملف
        # =================================================

        if not os.path.exists(
            downloaded
        ):

            return jsonify({

                "success": False,

                "message":
                    "لم يتم العثور على الفيديو"

            }), 500

        # =================================================
        # حجم الملف
        # =================================================

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

        print("================================")
        print("Video downloaded successfully")
        print("Filename:", filename)
        print("Size:", file_size)
        print("================================")

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
        # تنظيف الملفات بعد الإرسال
        # =================================================

        @response.call_on_close
        def cleanup():

            try:

                shutil.rmtree(
                    temp_dir,
                    ignore_errors=True
                )

                print(
                    "Temporary folder deleted"
                )

            except Exception as e:

                print(
                    "Cleanup error:",
                    str(e)
                )

        return response

    # =====================================================
    # معالجة الأخطاء
    # =====================================================

    except Exception as e:

        error_text = str(e)

        print("================================")
        print("VIDEO DOWNLOAD ERROR")
        print(error_text)
        print("================================")

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
