from django.contrib import admin
from django.db.models import Count, Q, QuerySet, Sum
from django.utils.html import format_html
from django.contrib.auth.models import User as DjangoUser, Group as DjangoGroup
from django.template.defaultfilters import truncatewords
from django.utils import timezone
from preferences.admin import PreferencesAdmin

from bot import models, types

admin.site.site_header = admin.site.site_title = 'Администрирование бота'
admin.site.site_url = ''

admin.site.unregister(DjangoUser)
admin.site.unregister(DjangoGroup)
admin.site.enable_nav_sidebar = False


class StatsAdmin(admin.ModelAdmin):
    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


class UserAdmin(admin.ModelAdmin):
    list_display = ['created', 'user_id', 'username_custom', 'first_name', 'last_name', 'type', 'phone_custom',
                    'categories_custom', 'portfolio', 'city', 'location_custom', 'balance', 'is_active_master', 'is_banned']
    list_editable = ['is_banned', 'balance']
    list_filter = ['is_banned', 'type', 'is_active_master', 'categories__category', 'city', 'city__country']
    search_fields = ['user_id', 'username', 'first_name', 'last_name']
    date_hierarchy = 'created'
    list_display_links = None
    list_per_page = 25

    def username_custom(self, obj):
        if obj.username:
            return format_html(f'<a href="tg://resolve?domain={obj.username}">@{obj.username}</a>')
        else:
            return '-'
    username_custom.short_description = '@username'

    def location_custom(self, obj):
        if obj.location.x:
            return format_html(f'<a href="https://maps.google.com/maps?q={obj.location.x},{obj.location.y}">{obj.location.x} {obj.location.y}</a>')
        else:
            return '-'
    location_custom.short_description = 'Местоположение'

    def categories_custom(self, obj):
        return truncatewords(', '.join(x.title for x in obj.categories.all()), 5) or '-'
    categories_custom.short_description = 'Категории'

    def phone_custom(self, obj):
        if obj.phone:
            return format_html(f'<a href="tel:{obj.phone}">{obj.phone}</a>')
        else:
            return '-'
    phone_custom.short_description = 'Телефон'

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return True

    def has_delete_permission(self, *args, **kwargs):
        return False


class LogAdmin(admin.ModelAdmin):
    list_display = ['created', 'user_id_custom', 'type', 'content']
    list_display_links = None
    list_per_page = 25

    date_hierarchy = 'created'
    search_fields = ['user__user_id']
    list_filter = ['type']

    def user_id_custom(self, obj):
        if obj.user:
            return format_html(f'<a href="/bot/user/?q={obj.user.user_id}">{obj.user.user_id}</a>')
        else:
            return '-'
    user_id_custom.short_description = 'ID пользователя'

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['text_custom', 'photo_custom', 'video_custom', 'preview']
    list_per_page = 25

    search_fields = ['text']

    def text_custom(self, obj):
        if obj.text:
            return truncatewords(obj.text, 10)
        else:
            return '-'
    text_custom.short_description = 'Текст'

    def photo_custom(self, obj):
        return models.Media.objects.filter(portfolio=obj, type=types.Media.PHOTO).count()
    photo_custom.short_description = 'Количество фото'

    def video_custom(self, obj):
        return models.Media.objects.filter(portfolio=obj, type=types.Media.VIDEO).count()
    video_custom.short_description = 'Количество видео'

    def preview(self, obj):
        return format_html(f'<a href="/portfolio/{obj.id}" target="_blank" class="viewlink">Просмотреть</a>')
    preview.short_description = 'Превью'

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return True

    def has_delete_permission(self, *args, **kwargs):
        return False


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'subcategories_custom', 'subcategories_custom_num', 'radius']

    fieldsets = [
        ('Параметры', {'fields': ['title', 'radius']}),
    ]

    search_fields = ['title']

    def subcategories_custom(self, obj):
        return ', '.join(x.title for x in obj.subcategories) or '-'
    subcategories_custom.short_description = 'Суб-категории'

    def subcategories_custom_num(self, obj):
        return obj.subcategories.count()
    subcategories_custom_num.short_description = 'Количество суб-категорий'

    def has_add_permission(self, *args, **kwargs):
        return True

    def has_change_permission(self, *args, **kwargs):
        return True

    def has_delete_permission(self, *args, **kwargs):
        return True


class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'category']

    fieldsets = [
        ('Параметры', {'fields': ['title', 'category']}),
    ]

    search_fields = ['title']
    list_filter = ['category']

    def has_add_permission(self, *args, **kwargs):
        return True

    def has_change_permission(self, *args, **kwargs):
        return True

    def has_delete_permission(self, *args, **kwargs):
        return True


class OrderAdmin(admin.ModelAdmin):
    list_display = ['created', 'client_custom', 'master_custom', 'status', 'subcategory', 'city', 'location_custom', 'date', 'times']
    list_per_page = 25
    date_hierarchy = 'created'

    list_filter = ['status', 'subcategory__category', 'subcategory', 'city']
    search_fields = ['client__user_id', 'master__user_id']

    def client_custom(self, obj):
        if obj.client:
            return format_html(f'<a href="/bot/user/?q={obj.client.user_id}">{obj.client.user_id}</a>')
        else:
            return '-'
    client_custom.short_description = 'Клиент'

    def master_custom(self, obj):
        if obj.master:
            return format_html(f'<a href="/bot/user/?q={obj.master.user_id}">{obj.master.user_id}</a>')
        else:
            return '-'
    master_custom.short_description = 'Мастер'

    def location_custom(self, obj):
        if obj.location.x:
            return format_html(f'<a href="https://maps.google.com/maps?q={obj.location.x},{obj.location.y}">{obj.location.x} {obj.location.y}</a>')
        else:
            return '-'
    location_custom.short_description = 'Местоположение'

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


class RequestAdmin(admin.ModelAdmin):
    list_display = ['created', 'order_custom', 'master']
    list_per_page = 25
    date_hierarchy = 'created'
    list_filter = ['master__categories__category']
    search_fields = ['order__client__user_id', 'master__user_id']

    def order_custom(self, obj):
        if obj.order:
            return format_html(f'<a href="/bot/order/{obj.order.id}">{obj.order.id}</a>')
        else:
            return '-'
    order_custom.short_description = 'Заказ'

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['created', 'user_id_custom', 'amount', 'currency']
    list_per_page = 25

    search_fields = ['user__user_id']
    list_filter = ['currency']

    def user_id_custom(self, obj):
        if obj.user:
            return format_html(f'<a href="/bot/user/?q={obj.user.user_id}">{obj.user.user_id}</a>')
        else:
            return '-'
    user_id_custom.short_description = 'ID пользователя'

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, *args, **kwargs):
        return False


class PriceAdmin(admin.ModelAdmin):
    list_display = ['amount', 'price']

    def has_add_permission(self, *args, **kwargs):
        return True

    def has_change_permission(self, *args, **kwargs):
        return True

    def has_delete_permission(self, *args, **kwargs):
        return True


class SettingsAdmin(PreferencesAdmin):
    fieldsets = [
        ('Параметры', {'fields': ['media_chat_link', 'portfolio_chat_link', 'media_chat_id', 'portfolio_chat_id']}),
    ]

    def has_add_permission(self, *args, **kwargs):
        return False

    def has_change_permission(self, *args, **kwargs):
        return True

    def has_delete_permission(self, request, obj=None):
        return False


class PostAdmin(admin.ModelAdmin):
    change_form_template = 'admin/text_change_form.html'

    list_display = ['created', 'status', 'receivers_custom', 'media_custom', 'text_custom', 'keyboard_custom', 'filters_custom']

    fieldsets = [
        ('Медиа', {'fields': ['photo_id', 'gif_id', 'video_id']}),
        ('Текст', {'fields': ['message', 'preview']}),
        ('Клавиатура', {'fields': ['button', 'link']}),
        ('Фильтры', {'fields': ['user_type']}),
    ]

    date_hierarchy = 'created'
    search_fields = ['photo_id', 'gif_id', 'video_id', 'message', 'button', 'link']
    list_filter = ['status', 'user_type']
    list_per_page = 10

    def filters_custom(self, obj):
        USER_TYPES = {types.User.CLIENT: 'Клиенты', types.User.MASTER: 'Мастера'}
        result = []
        if obj.user_type: result.append(USER_TYPES[obj.user_type])
        return ' | '.join(result) or '-'
    filters_custom.short_description = 'Фильтры'

    def receivers_custom(self, obj):
        if obj.receivers is not None:
            return format_html(f'<b>{obj.receivers}</b>')
        else:
            return '-'
    receivers_custom.short_description = 'Получатели'

    def media_custom(self, obj):
        file_id = obj.photo_id or obj.gif_id
        return file_id or '-'
    media_custom.short_description = 'Медиа'

    def text_custom(self, obj):
        text = obj.message.replace('\n', '<br>')
        if obj.preview:
            text += '<br><br>(превью)'
        return format_html(text)
    text_custom.short_description = 'Текст'

    def keyboard_custom(self, obj):
        if obj.button and obj.link:
            return format_html(f'<a href="{obj.link}" target="_blank">{obj.button}</a>')
        else:
            return '-'
    keyboard_custom.short_description = 'Кнопка'

    def change_view(self, *args, **kwargs):
        if not kwargs.get('extra_context'):
            kwargs['extra_context'] = {}
        kwargs['extra_context']['show_save_and_continue'] = False
        return super().change_view(*args, **kwargs)

    def has_change_permission(self, *args, **kwargs):
        return False

    def has_delete_permission(self, request, obj=None):
        return (obj is None) or (obj.status == types.Post.DONE)


class UserStatsAdmin(StatsAdmin):
    change_list_template = 'admin/user_stats.html'
    date_hierarchy = 'created'

    list_filter = ['categories__category', 'city', 'city__country']

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs: QuerySet = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        metrics = {
            'total': Count('user_id'),
            'clients': Count('user_id', Q(type=types.User.CLIENT)),
            'masters': Count('user_id', Q(type=types.User.MASTER)),
            'active': Count('user_id', Q(type=types.User.MASTER, is_active_master=True)),
            'inactive': Count('user_id', Q(type=types.User.MASTER, is_active_master=False)),
            'balance': Sum('balance'),
        }
        response.context_data['summary_total'] = dict(
            qs.aggregate(**metrics)
        )
        return response


class CategoryStatsAdmin(StatsAdmin):
    change_list_template = 'admin/category_stats.html'

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)

        summary = []
        masters = models.User.objects.filter(type=types.User.MASTER)
        for cat in models.Category.objects.all():
            users = masters.filter(categories__category=cat).distinct()
            summary.append({'title': cat.title,
                            'total': users.count(),
                            'active': users.filter(is_active_master=True).count(),
                            'inactive': users.filter(is_active_master=False).count()})
        response.context_data['summary'] = summary
        return response


class OrderStatsAdmin(StatsAdmin):
    change_list_template = 'admin/order_stats.html'
    date_hierarchy = 'created'

    list_filter = ['city']

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs: QuerySet = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        metrics = {
            'total': Count('id'),
            'closed': Count('id', Q(master__isnull=False)),
        }
        response.context_data['summary_total'] = dict(
            qs.aggregate(**metrics)
        )
        orders = models.Order.objects.filter(created__month=timezone.now().month).values('client')
        # orders = models.Order.objects.all().values('client')
        response.context_data['repeated'] = orders.count() - orders.distinct().count()
        response.context_data['month'] = timezone.now().strftime('%m.%Y')
        return response


class RequestStatsAdmin(StatsAdmin):
    change_list_template = 'admin/request_stats.html'
    date_hierarchy = 'created'
    list_filter = ['order__city']

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs: QuerySet = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
        metrics = []
        for cat in models.Category.objects.all():
            metrics.append({'title': cat.title,
                            **qs.aggregate(total=Count('id', Q(order__subcategory__category=cat)))})
        response.context_data['summary'] = metrics
        return response


admin.site.register(models.User, UserAdmin)
admin.site.register(models.Log, LogAdmin)
admin.site.register(models.Portfolio, PortfolioAdmin)
admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.Subcategory, SubcategoryAdmin)
admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.Request, RequestAdmin)
admin.site.register(models.Transaction, TransactionAdmin)
admin.site.register(models.Price, PriceAdmin)
admin.site.register(models.Settings, SettingsAdmin)
admin.site.register(models.Post, PostAdmin)
admin.site.register(models.UserStats, UserStatsAdmin)
admin.site.register(models.CategoryStats, CategoryStatsAdmin)
admin.site.register(models.OrderStats, OrderStatsAdmin)
admin.site.register(models.RequestStats, RequestStatsAdmin)
