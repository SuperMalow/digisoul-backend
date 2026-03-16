from django.db.models.signals import pre_delete
from django.dispatch import receiver
from web.models.Friends import Message
from web.utils.delete_old_audio import delete_old_audio
from web.models.Character import Character
from web.utils.delete_old_photo import delete_old_photo


@receiver(pre_delete, sender=Message)
def cleanup_message_audio(sender, instance, **kwargs):
    delete_old_audio(instance.audio_message)


@receiver(pre_delete, sender=Character)
def cleanup_character_photo(sender, instance, **kwargs):
    delete_old_photo(instance.photo)

@receiver(pre_delete, sender=Character)
def cleanup_character_background_photo(sender, instance, **kwargs):
    delete_old_photo(instance.background_photo)
