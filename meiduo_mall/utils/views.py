from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.http import JsonResponse

# 方式1
# class LoginRequiredMixin(AccessMixin):
#     """Verify that the current user is authenticated."""
#
#     def dispatch(self, request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return JsonResponse({'code': 400, 'errmsg': '没有登录'})
#         return super().dispatch(request, *args, **kwargs)


# 方式2
class LoginRequiredJSONMixin(LoginRequiredMixin):

    def handle_no_permission(self):
        return JsonResponse({'code': 400, 'errmsg': '没有登录'})

