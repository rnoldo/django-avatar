import os

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat

from avatar.settings import (AVATAR_MAX_SIZE,
                             AVATAR_ALLOWED_FILE_EXTS)


def avatar_img(avatar, size):
    if not avatar.thumbnail_exists(size):
        avatar.create_thumbnail(size)
    return mark_safe("""<img src="%s" alt="%s" width="%s" height="%s" />""" %
        (avatar.avatar_url(size), unicode(avatar), size, size))


class UploadAvatarForm(forms.Form):

    avatar = forms.ImageField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UploadAvatarForm, self).__init__(*args, **kwargs)

    def clean_avatar(self):
        data = self.cleaned_data['avatar']
        if AVATAR_ALLOWED_FILE_EXTS:
            (root, ext) = os.path.splitext(data.name.lower())
            if ext not in AVATAR_ALLOWED_FILE_EXTS:
                raise forms.ValidationError(
                _(u"%(ext)s is an invalid file extension. Authorized extensions are : %(valid_exts_list)s") %
                {'ext': ext, 'valid_exts_list': ", ".join(AVATAR_ALLOWED_FILE_EXTS)})
        if data.size > AVATAR_MAX_SIZE:
            raise forms.ValidationError(
                _(u"Your file is too big (%(size)s), the maximum allowed size is %(max_valid_size)s") %
                {'size': filesizeformat(data.size), 'max_valid_size': filesizeformat(AVATAR_MAX_SIZE)})
        return
