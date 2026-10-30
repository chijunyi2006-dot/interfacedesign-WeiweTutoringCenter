"""
建議的資料模型（給後端同學參考，可直接貼到 Django App 的 models.py）
欄位名稱已和前端模板對齊；若要改名，模板中的 {{ 變數 }} 也要一起改。
"""
from django.conf import settings
from django.db import models

CATEGORY_CHOICES = [
    ("研究所", "研究所"),
    ("轉學考", "轉學考"),
    ("公職/國營", "公職/國營"),
]
DEPARTMENT_CHOICES = [
    ("資訊工程類", "資訊工程類"),
    ("電機電子類", "電機電子類"),
    ("機械類", "機械類"),
    ("商管類", "商管類"),
    ("材料化工類", "材料化工類"),
]


class News(models.Model):
    """首頁 Hot News（最新消息 / 研究所考試資訊）"""
    NEWS_CATEGORY_CHOICES = [("最新消息", "最新消息"), ("研究所考試資訊", "研究所考試資訊")]

    category = models.CharField("分類", max_length=20, choices=NEWS_CATEGORY_CHOICES)
    title = models.CharField("標題", max_length=200)
    date = models.DateField("日期")
    content = models.TextField("內容", blank=True)

    class Meta:
        ordering = ["-date"]
        verbose_name = verbose_name_plural = "消息公告"

    def __str__(self):
        return self.title


class Course(models.Model):
    """課程方案（課程列表、課程詳情）"""
    year = models.PositiveIntegerField("學年度", default=115)
    category = models.CharField("類別", max_length=20, choices=CATEGORY_CHOICES)
    department = models.CharField("科系", max_length=20, choices=DEPARTMENT_CHOICES)
    title = models.CharField("課程名稱", max_length=100)
    subjects = models.CharField("包含科目", max_length=300)
    teaching_mode = models.CharField("授課方式", max_length=200, help_text="篩選會比對「實體」「直播」「雲端」等字")
    price_note = models.CharField("費用區間說明", max_length=200)
    syllabus = models.TextField("核心課程與考科重點", help_text="一行一個重點，換行會保留")
    handout_url = models.URLField("歷屆試題／講義連結", blank=True)
    is_featured = models.BooleanField("顯示於首頁熱門課程", default=False)
    # 課程詳情的「授課師資」：考科連到對應老師（作業一 Bad UI 問題 3）
    teachers = models.ManyToManyField("Teacher", blank=True, related_name="courses", verbose_name="授課師資")

    class Meta:
        ordering = ["category", "department", "id"]
        verbose_name = verbose_name_plural = "課程方案"

    def __str__(self):
        return f"{self.year} {self.title}"


class CoursePlan(models.Model):
    """課程的上課方式與費用（實體 / 直播 / 雲端）"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="plans", verbose_name="課程")
    name = models.CharField("方案名稱", max_length=50)
    schedule = models.CharField("時段與彈性", max_length=200)
    feature = models.CharField("課程特色", max_length=200)
    price_min = models.PositiveIntegerField("最低價格")
    price_max = models.PositiveIntegerField("最高價格")

    class Meta:
        verbose_name = verbose_name_plural = "費用方案"

    def __str__(self):
        return f"{self.course.title} - {self.name}"


class CourseMilestone(models.Model):
    """考試時程時間軸（作業一 Flow 3／Frame 8：報名時程時間軸）；沒有資料時前台不顯示"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="milestones", verbose_name="課程")
    order = models.PositiveIntegerField("順序", default=1)
    label = models.CharField("項目", max_length=30, help_text="例如：報名起訖、筆試日期")
    date_text = models.CharField("日期", max_length=30, help_text="例如：06/01–06/20")

    class Meta:
        ordering = ["course", "order"]
        verbose_name = verbose_name_plural = "考試時程"

    def __str__(self):
        return f"{self.course.title} {self.label}"


class CourseUnit(models.Model):
    """課程單元（會員中心：繼續觀看、講義下載）"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="units", verbose_name="課程")
    order = models.PositiveIntegerField("章節序號")
    title = models.CharField("單元名稱", max_length=100)
    video_url = models.URLField("影片嵌入網址", blank=True, help_text="YouTube 請用 https://www.youtube.com/embed/影片ID")
    handout_url = models.URLField("講義連結", blank=True)

    class Meta:
        ordering = ["course", "order"]
        verbose_name = verbose_name_plural = "課程單元"

    def __str__(self):
        return f"{self.course.title} 第{self.order}章 {self.title}"


class Teacher(models.Model):
    """師資介紹與線上試聽"""
    name = models.CharField("姓名", max_length=20)
    subject = models.CharField("授課科目", max_length=50)
    category = models.CharField("類別", max_length=20, choices=CATEGORY_CHOICES)
    department = models.CharField("科系", max_length=20, choices=DEPARTMENT_CHOICES)
    rating = models.DecimalField("學生評價", max_digits=2, decimal_places=1, default=5.0)
    success_count = models.PositiveIntegerField("上榜學生數", default=0)
    tagline = models.CharField("一句話特色", max_length=50)
    education = models.CharField("學經歷", max_length=200)
    highlights = models.TextField("詳細授課重點", help_text="一行一個重點")
    video_url = models.URLField("試聽影片嵌入網址", blank=True)
    handout_url = models.URLField("歷屆試題連結（會員可下載）", blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "師資"

    def __str__(self):
        return f"{self.name}（{self.subject}）"


class Ranking(models.Model):
    """榜單榮譽；有填 course 與心得的資料，會顯示在該課程詳情頁"""
    year = models.PositiveIntegerField("年度")
    student_name = models.CharField("學員稱呼", max_length=20, help_text="請用「陳學長」等稱呼，勿放全名")
    school = models.CharField("錄取學校", max_length=50)
    department = models.CharField("系所", max_length=50)
    category = models.CharField("類別", max_length=20, choices=CATEGORY_CHOICES)
    honor = models.CharField("榮譽", max_length=20, help_text="例如：榜首、前三名、正取")
    is_top = models.BooleanField("是否為榜首／前三名", default=False)
    scores = models.CharField("成績表現", max_length=100, blank=True)
    testimonial = models.TextField("心得", blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="testimonials", verbose_name="就讀課程")
    # 有填老師的心得，會顯示在該老師的介紹下（作業一 Bad UI 問題 5）
    teacher = models.ForeignKey("Teacher", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="reviews", verbose_name="指導老師")

    class Meta:
        ordering = ["-year", "-is_top", "id"]
        verbose_name = verbose_name_plural = "榜單"

    def __str__(self):
        return f"{self.year} {self.student_name} {self.school}"


class Favorite(models.Model):
    """會員收藏的課程"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "course")
        verbose_name = verbose_name_plural = "會員收藏"


class ContactMessage(models.Model):
    """聯絡我們：線上諮詢表單（後台可查看與標記已處理）"""
    IDENTITY_CHOICES = [("家長", "家長"), ("學生", "學生"), ("社會人士", "社會人士")]
    CAMPUS_CHOICES = [("雲科據點", "雲科據點"), ("虎科據點", "虎科據點"), ("其他區域", "其他區域")]
    CONTACT_CATEGORY_CHOICES = CATEGORY_CHOICES + [("其他", "其他")]
    CONTACT_TIME_CHOICES = [("平日白天", "平日白天 10:00–18:00"), ("平日晚上", "平日晚上 18:00–21:30"), ("週末", "週末")]

    name = models.CharField("姓名", max_length=30)
    phone = models.CharField("電話", max_length=20)
    identity = models.CharField("身分", max_length=10, choices=IDENTITY_CHOICES)
    campus = models.CharField("諮詢據點", max_length=10, choices=CAMPUS_CHOICES)
    category = models.CharField("詢問類別", max_length=20, choices=CONTACT_CATEGORY_CHOICES)
    contact_time = models.CharField("希望聯絡時段", max_length=10, choices=CONTACT_TIME_CHOICES)
    school_info = models.CharField("學校／科系／年級", max_length=100, blank=True)
    message = models.TextField("想了解的資訊", max_length=1000)
    line_id = models.CharField("LINE ID", max_length=50, blank=True)
    created_at = models.DateTimeField("送出時間", auto_now_add=True)
    is_handled = models.BooleanField("已處理", default=False)

    class Meta:
        ordering = ["is_handled", "-created_at"]
        verbose_name = verbose_name_plural = "線上諮詢"

    def __str__(self):
        return f"{self.name}（{self.category}）"


class Enrollment(models.Model):
    """會員已選購的課程（由後台指派）"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="課程")
    plan_name = models.CharField("選購方案", max_length=50, help_text="例如：雲端隨選班")
    progress = models.PositiveSmallIntegerField("學習進度 %", default=0)
    last_unit = models.ForeignKey(CourseUnit, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="上次觀看單元")

    class Meta:
        verbose_name = verbose_name_plural = "會員選課"

    def __str__(self):
        return f"{self.user} - {self.course.title}"
