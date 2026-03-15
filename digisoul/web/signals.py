from django.db.models.signals import pre_delete
from django.dispatch import receiver
from web.models.Friends import Message
from web.utils.delete_old_audio import delete_old_audio


@receiver(pre_delete, sender=Message)
def cleanup_message_audio(sender, instance, **kwargs):
    delete_old_audio(instance.audio_message)
