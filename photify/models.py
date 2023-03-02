from django.conf.global_settings import MEDIA_ROOT
from django.db import models
from django.contrib.auth.models import User
import uuid
from pathlib import Path

from django.dispatch import receiver
from django.utils.deconstruct import deconstructible
import os


@deconstructible
class PathAndRename(object):
    def __init__(self, dir_path):
        self.path = dir_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        # set filename as random string
        filename = '{}.{}'.format(uuid.uuid4().hex, ext)
        # return the whole path to the file
        return str(Path(self.path, filename))


path_and_rename_post = PathAndRename(Path(MEDIA_ROOT, 'post_images'))


class Post(models.Model):
    caption = models.CharField(max_length=1024)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField('Post Image', upload_to=path_and_rename_post)
    published_date = models.DateTimeField('Date Published')
    private = models.BooleanField("Private Post")

    @property
    def filename(self):
        return os.path.basename(self.image.name)

    def __str__(self):
        return f'Post {self.id}, author={self.author}, private={self.private}'


class PostLikes(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user} likes post {self.post.id}'


class Followers(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed')
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    date_from = models.DateTimeField('Friends Since')

    def __str__(self):
        return f'{self.follower} follows {self.user}'


class FollowRequest(models.Model):
    user_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests_from')
    user_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests_to')
    sent_date = models.DateTimeField('Date Sent')
    # Do not allow request less than month after rejection, (after 1 month delete rejected entry from db to unblock)
    rejected_date = models.DateTimeField('Date Rejected', blank=True, null=True)

    def __str__(self):
        return f'Request from={self.user_from}, to={self.user_to}'


# These two auto-delete image files from filesystem when they are unneeded:
@receiver(models.signals.post_delete, sender=Post)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes image file from filesystem
    when corresponding `Post` object is deleted.
    """
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


@receiver(models.signals.pre_save, sender=Post)
def auto_delete_file_on_change(sender, instance, **kwargs):
    """
    Deletes old image file from filesystem
    when corresponding `Post` object is updated
    with new file.
    """
    if not instance.pk:
        return False

    try:
        old_file = Post.objects.get(pk=instance.pk).image
    except Post.DoesNotExist:
        return False

    new_file = instance.image
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
