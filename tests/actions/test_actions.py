from unittest.mock import MagicMock, create_autospec

import pytest
from django.contrib.auth import get_user_model

from vprad.actions import actions_registry, ActionDoesNotExist
from vprad.actions.signals import action_pre, action_post
from vprad.actions.decorators import register_action, register_model_action
from vprad.helpers import clear_url_caches


def test_register_action(actions, mocker):
    User = get_user_model()
    dumb_action = mocker.stub()
    register_model_action(model=User,
                          name='dumb',
                          verbose_name='A dumb action',
                          icon='dumb',
                          takes_self=False)(dumb_action)
    action = actions_registry.find_cls_action(User, 'dumb')
    assert action.full_name == 'users_user_dumb'

    with pytest.raises(ValueError, match=r'The registry already.*'):
        register_model_action(model=User,
                              name='dumb',
                              verbose_name='A dumb action',
                              icon='dumb',
                              takes_self=False)(dumb_action)

    with pytest.raises(ActionDoesNotExist):
        actions_registry.find_action('made_up')

    with pytest.raises(ActionDoesNotExist):
        actions_registry.find_cls_action(User, 'made_up')


def test_cls_action(actions):
    User = get_user_model()

    def create_action(cls, username):
        return

    m = create_autospec(create_action)
    register_model_action(model=User,
                          name='create',
                          takes_self=False)(m)
    action = actions_registry.find_cls_action(User, 'create')
    assert action.full_name == 'users_user_create'
    action.call(username='abc', email='notused')
    m.assert_called_once_with(User, 'abc')

    avail = list(actions_registry.get_all_actions_for(cls=User))
    assert action in avail
    avail = list(actions_registry.get_available_actions_for(cls=User))
    assert action in avail


def test_instance_action(actions):
    User = get_user_model()

    def change_username(instance, new_username):
        return

    user = User(username='marc')
    m = create_autospec(change_username)
    register_model_action(model=User,
                          name='change_username',
                          takes_self=True)(m)
    action = actions_registry.find_cls_action(user.__class__, 'change_username')
    assert action.full_name == 'users_user_change_username'
    action.call(instance=user, new_username='john')
    m.assert_called_once_with(user, 'john')

    avail = list(actions_registry.get_all_actions_for(instance=User()))
    assert action in avail
    avail = list(actions_registry.get_available_actions_for(instance=User()))
    assert action in avail


def test_rogue_action(actions):
    """ An action with no class and no instance. """

    def destroy_world(world, weapon):
        return

    register_action()(destroy_world)
    action = actions_registry.find_action('test_actions_destroy_world')
    assert action.function == destroy_world

    register_action(name='destroy_world',
                    full_name='test_destroy_world'
                    )(destroy_world)
    action = actions_registry.find_action('test_destroy_world')
    assert action.function == destroy_world

    m = create_autospec(destroy_world)
    register_action(name='destroy_world')(m)
    action = actions_registry.find_action('__nomodule_destroy_world')
    action.call(world='Mars', weapon='Rocinante')
    m.assert_called_once_with('Mars', 'Rocinante')


def test_conditions(actions):
    def destroy_world(world, weapon, user):
        return

    def method(user):
        pass

    world = MagicMock()
    user = MagicMock()
    has_weapons = create_autospec(method)
    can_destroy = create_autospec(method)
    action_mock = create_autospec(destroy_world)

    register_action(conditions=[can_destroy, has_weapons],
                    full_name='test_conditions')(action_mock)
    action = actions_registry.find_action('test_conditions')
    assert action.function == action_mock
    assert has_weapons in action.conditions

    can_destroy.return_value = True
    has_weapons.return_value = True
    can = action.check_conditions(user=user)
    can_destroy.assert_called_once_with(user)
    has_weapons.assert_called_once_with(user)
    assert can

    has_weapons.reset_mock()
    can_destroy.reset_mock()
    can_destroy.return_value = False
    can = action.check_conditions(user=user)
    can_destroy.assert_called_once_with(user)
    has_weapons.assert_not_called()
    assert not can


def test_call(actions):
    def destroy_world(world, weapon, request_user):
        return

    pre = MagicMock()
    post = MagicMock()
    action_pre.connect(pre)
    action_post.connect(post)

    action_mock = create_autospec(destroy_world)
    register_action(full_name='test_conditions')(action_mock)
    action = actions_registry.find_action('test_conditions')
    assert action.function == action_mock

    action_mock.return_value = 1234
    assert 1234 == action.call(world='Earth', request_user='Smith', weapon='Asteroid')
    action_mock.assert_called_once_with('Earth', 'Asteroid', 'Smith')

    signal_args = dict(sender=action,
                       signal=action_pre,
                       request_user='Smith',
                       weapon='Asteroid',
                       world='Earth')
    pre.assert_called_once_with(**signal_args)
    signal_args['signal'] = action_post
    post.assert_called_once_with(**signal_args)


def test_url(actions):
    def destroy_world(world, weapon, user):
        return

    action_mock = create_autospec(destroy_world)

    register_action(full_name='test_urls')(action_mock)
    clear_url_caches()
    action = actions_registry.find_action('test_urls')
    assert action.function == action_mock
    assert action.get_absolute_url() == '/action/test_urls'

    instance_mock = MagicMock()
    instance_mock.pk = 1

    register_action(full_name='test_urls2', needs_instance=True)(action_mock)
    clear_url_caches()
    action = actions_registry.find_action('test_urls2')
    assert action.function == action_mock
    assert action.get_absolute_url(instance=instance_mock) == '/action/test_urls2/1'

    with pytest.raises(ValueError, match=r'Action .* needs an instance'):
        action.get_absolute_url()
