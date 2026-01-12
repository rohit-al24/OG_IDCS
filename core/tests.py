from .models import *

if __name__ == '__main__':
    avg = 0.0

    ratings = IndividualStaffRating.objects.all()
    print(ratings)