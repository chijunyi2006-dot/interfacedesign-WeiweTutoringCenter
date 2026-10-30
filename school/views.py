"""
建議的 Views（給後端同學參考）。context 變數名稱必須與這裡相同，模板才會顯示資料。
假設 App 名稱為 school；若用別的名稱，請改 from .models import 那行即可。
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import ContactForm
from .models import (CATEGORY_CHOICES, DEPARTMENT_CHOICES, Course, Enrollment,
                     Favorite, News, Ranking, Teacher)

CATEGORIES = [value for value, _ in CATEGORY_CHOICES]
DEPARTMENTS = [value for value, _ in DEPARTMENT_CHOICES]


def home(request):
    return render(request, "index.html", {
        "latest_news": News.objects.filter(category="最新消息")[:5],
        "exam_news": News.objects.filter(category="研究所考試資訊")[:5],
        "featured_courses": Course.objects.filter(is_featured=True)[:3],
    })


def course_list(request):
    return render(request, "courses.html", {
        "courses": Course.objects.all(),
        "categories": CATEGORIES,
        "departments": DEPARTMENTS,
    })


def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.prefetch_related("plans", "testimonials", "teachers", "milestones"), pk=pk
    )
    is_favorited = (
        request.user.is_authenticated
        and Favorite.objects.filter(user=request.user, course=course).exists()
    )
    return render(request, "course_detail.html", {"course": course, "is_favorited": is_favorited})


@login_required
@require_POST
def toggle_favorite(request, pk):
    course = get_object_or_404(Course, pk=pk)
    favorite, created = Favorite.objects.get_or_create(user=request.user, course=course)
    if created:
        messages.success(request, "已加入收藏，可到會員中心查看")
    else:
        favorite.delete()
        messages.info(request, "已取消收藏")

    # 回到原本的頁面（課程詳情或會員中心）
    back = request.META.get("HTTP_REFERER")
    if back and url_has_allowed_host_and_scheme(back, allowed_hosts={request.get_host()}):
        return redirect(back)
    return redirect("course_detail", pk=pk)


def teacher_list(request):
    return render(request, "teachers.html", {
        "teachers": Teacher.objects.prefetch_related("reviews"),
        "categories": CATEGORIES,
        "departments": DEPARTMENTS,
    })


def ranking_list(request):
    rankings = Ranking.objects.all()
    years = Ranking.objects.order_by("-year").values_list("year", flat=True).distinct()
    return render(request, "rankings.html", {
        "rankings": rankings,
        "years": years,
        "categories": CATEGORIES,
    })


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "已收到您的諮詢，我們會在 1–2 個工作天內與您聯絡")
            return redirect("contact")
    else:
        form = ContactForm(initial=contact_initial(request.GET))
    return render(request, "contact.html", {"form": form})


def contact_initial(params):
    """從課程頁「詢問此課程／報名此方案」、師資「立即報名」進來時，自動帶入類別與留言"""
    initial = {"category": params.get("category", "")}
    course, plan = params.get("course"), params.get("plan")
    if course and plan:
        initial["message"] = f"我想報名「{course}」的「{plan}」，請協助安排報名與上課方式。"
    elif course:
        initial["message"] = f"我想詢問「{course}」的上課方式與費用。"
    return initial


@login_required
def member(request):
    enrollments = (
        Enrollment.objects.filter(user=request.user)
        .select_related("course", "last_unit")
        .prefetch_related("course__units")
    )
    favorites = Course.objects.filter(favorited_by__user=request.user)
    return render(request, "member.html", {"enrollments": enrollments, "favorites": favorites})
