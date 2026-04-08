from cycle.models import User
from django.db.transaction import atomic


def get(user_id: int) -> User:
    return User.objects.get(pk=user_id)


@atomic
def update_kalman(user_id: int, estimate: float, error: float) -> None:
    user = User.objects.select_for_update().get(pk=user_id)
    user.kalman_estimate = estimate
    user.kalman_error = error
    user.save(update_fields=['kalman_estimate', 'kalman_error'])
