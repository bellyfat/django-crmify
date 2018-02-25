from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from crmify.settings import crmify_settings
from crmify.models import Lead
import logging
import pdb

logger = logging.getLogger(__name__)


field_mapper = crmify_settings.BACKEND_FIELDMAPPER()


def get_possible_senders():
    """ the possible senders include the LEAD_MODEL itself, along with all many-to-one and one-to-one relations to the
    LEAD_MODEL (recursively)
    :return: `list` of `cls`
    """
    def rec_helper(cls, seen=None):
        seen = seen or []
        related_objects = [f for f in cls._meta.get_fields() if f.is_relation]

        all_possibles = [cls]
        frame_possibles = [o for o in related_objects if (o.many_to_one or o.one_to_one) and o.related_model is not Lead and o.related_model not in seen]
        for p in frame_possibles:
            all_possibles = all_possibles + rec_helper(p.related_model, seen=all_possibles)

        return list(set(all_possibles))

    return rec_helper(crmify_settings.LEAD_MODEL)

crm_senders = get_possible_senders()


def get_lead_model_instance_from_sender_instance(sender_instance):
    """ given a sender model instance, traverse the object graph to find the LEAD_MODEL instance associated with it.

    For instance, imagine we have objects like UserProfile -> User and then imagine that the UserProfile is the LEAD_MODEL
    and a User instance is saved. Therefore, the sender_instance will be a User, and the goal is to find the UserProfile(s)
    it is associated with to trigger a save on each

    :param sender:
    :return: `object` settings.LEAD_MODEL instance associated with the sender
    """
    for field in sender_instance._meta.get_fields():
        #TODO KNOWN LIMITATION: this will only work one layer deep.
        if field.is_relation and field.related_model is crmify_settings.LEAD_MODEL:
            return getattr(sender_instance, field.name)


@receiver(post_save)
def update_crm_lead(sender=None, instance=None, created=None, **kwargs):
    if sender in crm_senders and sender is not crmify_settings.LEAD_MODEL:
        logger.debug('triggering save on lead model for related instance {}'.format(instance))
        lead_model_instance = get_lead_model_instance_from_sender_instance(instance)
        lead_model_instance.save()
    elif sender == crmify_settings.LEAD_MODEL:
        if created:
            logger.debug('creating new lead for instance {}'.format(instance))
            lead = field_mapper.create_lead(instance)
        else:
            logger.debug('updating lead for instance {}'.format(instance))
            lead = Lead.objects.get(anchor=instance)
            lead = field_mapper.update_lead(lead, instance)

        logger.debug('lead is {}'.format(lead))


@receiver(post_delete, sender=crmify_settings.LEAD_MODEL)
def delete_crm_lead(sender=None, instance=None, **kwargs):
    logger.debug('deleting leads for instance {}'.format(instance))
    Lead.objects.filter(anchor=instance).delete()
