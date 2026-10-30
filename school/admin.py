"""建議的 admin.py：讓 Django 後台可以管理前台需要的所有資料"""
from django.contrib import admin

from .models import (ContactMessage, Course, CourseMilestone, CoursePlan, CourseUnit,
                     Enrollment, Favorite, News, Ranking, Teacher)


class CoursePlanInline(admin.TabularInline):
    model = CoursePlan
    extra = 1


class CourseUnitInline(admin.TabularInline):
    model = CourseUnit
    extra = 1


class CourseMilestoneInline(admin.TabularInline):
    model = CourseMilestone
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "year", "category", "department", "is_featured")
    list_filter = ("category", "department", "is_featured")
    search_fields = ("title", "subjects")
    filter_horizontal = ("teachers",)
    inlines = [CourseMilestoneInline, CoursePlanInline, CourseUnitInline]


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "date")
    list_filter = ("category",)
    search_fields = ("title",)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name", "subject", "category", "department", "rating", "success_count")
    list_filter = ("category", "department")
    search_fields = ("name", "subject")


@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ("year", "student_name", "school", "department", "honor", "is_top", "course", "teacher")
    list_filter = ("year", "category", "is_top")
    search_fields = ("student_name", "school", "department")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "plan_name", "progress")
    list_filter = ("course",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "identity", "campus", "category", "contact_time", "created_at", "is_handled")
    list_filter = ("is_handled", "campus", "category", "identity", "contact_time")
    list_editable = ("is_handled",)
    search_fields = ("name", "phone", "message")
    readonly_fields = ("created_at",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "created_at")
