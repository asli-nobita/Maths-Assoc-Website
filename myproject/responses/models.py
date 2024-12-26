from django.db import models

class UserResponse(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    puzzle_id = models.IntegerField()
    response = models.IntegerField()
    is_correct = models.BooleanField()
    attempts = models.IntegerField(default=0)
    solved = models.BooleanField(default=False)
    puzzles_solved = models.IntegerField(default=0)

    def __str__(self):
        return self.name
