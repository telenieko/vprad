from unittest.mock import MagicMock
from src.partners.models import Partner
from src.partners.tests.factories import PartnerFactory
from src.users.tests.factories import UserFactory
from vprad.actions import actions_registry
from vprad.actions.signals import transition_pre, transition_post


def test_constraints():
    partner = PartnerFactory.build(status=Partner.PartnerStatus.NEW)
    assert sorted(['approve_partner',
                   'reject_partner',
                   'disable_partner']) == sorted([a.name for a in actions_registry.get_available_actions_for(instance=partner)])

    partner.status = Partner.PartnerStatus.APPROVED
    assert sorted(['reject_partner',
                   'disable_partner']) == sorted([a.name for a in actions_registry.get_available_actions_for(instance=partner)])

    partner.status = Partner.PartnerStatus.REJECTED
    assert sorted(['approve_partner',
                   'disable_partner']) == sorted([a.name for a in actions_registry.get_available_actions_for(instance=partner)])

    partner.status = Partner.PartnerStatus.DISABLED
    assert sorted(['approve_partner']) == sorted([a.name for a in actions_registry.get_available_actions_for(instance=partner)])


def test_transition(db):
    user = UserFactory.create()
    partner = PartnerFactory.create(status=Partner.PartnerStatus.NEW)

    pre = MagicMock()
    post = MagicMock()
    transition_pre.connect(pre)
    transition_post.connect(post)

    action = actions_registry.find_cls_action(Partner, 'approve_partner')
    assert action.check_conditions(instance=partner)
    action.call(instance=partner, request_user=user)
    assert partner.status == Partner.PartnerStatus.APPROVED

    signal_args = dict(current_value=Partner.PartnerStatus.NEW,
                       new_value=Partner.PartnerStatus.APPROVED,
                       signal=transition_pre,
                       sender=action,
                       instance=partner)
    pre.assert_called_once_with(**signal_args)
    signal_args['signal'] = transition_post
    signal_args['old_value'] = signal_args.pop('current_value')
    post.assert_called_once_with(**signal_args)

    transition_pre.disconnect(pre)
    transition_post.disconnect(post)
