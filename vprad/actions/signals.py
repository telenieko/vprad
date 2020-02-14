from django.dispatch import Signal

# Signals, the sender is always the Action.
action_pre = Signal(providing_args=['instance'])
action_post = Signal(providing_args=['instance'])
transition_pre = Signal(providing_args=['instance',
                                        'current_value',
                                        'new_value'])
transition_post = Signal(providing_args=['instance',
                                         'old_value',
                                         'new_value'])