from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from django.contrib.auth.decorators import login_required

from avatar.forms import  UploadAvatarForm
from avatar.models import Avatar
from avatar.signals import avatar_updated


def _get_next(request):
    """
    The part that's the least straightforward about views in this module is how they
    determine their redirects after they have finished computation.

    In short, they will try and determine the next place to go in the following order:

    1. If there is a variable named ``next`` in the *POST* parameters, the view will
    redirect to that variable's value.
    2. If there is a variable named ``next`` in the *GET* parameters, the view will
    redirect to that variable's value.
    3. If Django can determine the previous page from the HTTP headers, the view will
    redirect to that previous page.
    """
    next = request.POST.get('next', request.GET.get('next',
        request.META.get('HTTP_REFERER', None)))
    if not next:
        next = request.path
    return next


@login_required
def add(request, extra_context=None, next_override=None,
        upload_form=UploadAvatarForm, *args, **kwargs):
    if extra_context is None:
        extra_context = {}
    avatar = Avatar.objects.get(user=request.user)
    upload_avatar_form = upload_form(request.POST or None,
        request.FILES or None, user=request.user)
    if request.method == "POST" and 'avatar' in request.FILES:
        if upload_avatar_form.is_valid():
            image_file = request.FILES['avatar']
            avatar.avatar.save(image_file.name, image_file)
            avatar.save()
            request.user.message_set.create(
                message=_("Successfully uploaded a new avatar."))
            avatar_updated.send(sender=Avatar, user=request.user, avatar=avatar)
            return HttpResponseRedirect(next_override or _get_next(request))
    return render_to_response(
            'avatar/add.html',
            extra_context,
            context_instance=RequestContext(
                request,
                {'avatar': avatar,
                 'upload_avatar_form': upload_avatar_form,
                 'next': next_override or _get_next(request), }
            )
        )

