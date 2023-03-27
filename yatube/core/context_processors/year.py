from datetime import datetime


def year(request):
    today: int = datetime.now().year
    return {
        'year': today
    }
