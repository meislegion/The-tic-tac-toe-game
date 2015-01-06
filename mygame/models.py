from django.db import models
from django.contrib.auth.models import User
from mygame.exeptions import InviteGameIsExists, GameWrongWay, GameOnlyOne, GameWinnerNotExists
from test_task.settings import WIN_COMBINATION
import json
# Create your models here.


class UserOnline(models.Model):
    user = models.ForeignKey(User, unique=True)
    online = models.BooleanField(default=False)
    online_game = models.BooleanField(default=False)  # True if user play game
    game = models.ForeignKey('GameXO', null=True, blank=True)
    dt = models.DateTimeField(auto_now=True, editable=False, blank=False)


class InviteToGame(models.Model):

    users = models.CharField(max_length=512)  # [id_user_from, id_user_to]
    game_started = models.BooleanField(default=False)
    game_ended = models.BooleanField(default=False)
    user_not_confirm_id = models.IntegerField(default=0)  # id of user end game

    def get_user_from(self):
        return User.objects.get(id=json.loads(self.users)[0])

    def get_user_to(self):
        return User.objects.get(id=json.loads(self.users)[1])

    def get_user_not_confirm(self):
        return User.objects.get(id=self.user_not_confirm_id)

    def get_users_list(self):
        return json.loads(self.users)

    def save(self, *args, **kwargs):
        for e in InviteToGame.objects.filter(game_ended=False):
            if (self.get_users_list() == e.get_users_list() or self.get_users_list()[::-1] == e.get_users_list())\
                    and (self.pk != e.id):
                raise InviteGameIsExists
        super(InviteToGame, self).save(*args, **kwargs)


class GameXO(models.Model):

    state = models.CharField(max_length=150)
    invite = models.ForeignKey(InviteToGame)
    active = models.BooleanField(default=True)
    last_move_id = models.IntegerField(default=0)
    winner_id = models.IntegerField(default=0)  # !=0 the game over
    users_state = models.CharField(default=json.dumps(['', '']), max_length=100)

    def new_move(self, row, col, value):
        new_state = self.get_state()
        if new_state[row][col] == 0 and value != 0:
            new_state[row][col] = value
            self.state = json.dumps(new_state)
            self.last_move_id = self.get_user_from().id if value == 1 else self.get_user_to().id
            self.save()
            return None
        raise GameWrongWay()

    def set_win(self, value):
        if (self.winner_id == 0) and (lambda lst: False if True in [0 in e for e in lst] else True)(self.get_state()):
            win_id = -1
        elif WIN_COMBINATION(self.get_state(), value) and (self.winner_id == 0):
            win_id = self.get_user_from().id if value == 1 else self.get_user_to().id
        else:
            return False
        self.winner_id = win_id
        self.save()
        return True

    def get_state(self):
        return json.loads(self.state)

    def get_users_sate(self):
        return json.loads(self.users_state)

    def get_user_from(self):
        return self.invite.get_user_from()

    def get_user_to(self):
        return self.invite.get_user_to()

    def get_opponent(self, user_id):
        if self.get_user_from().id == user_id:
            return self.get_user_to()
        return self.get_user_from()

    def get_users_list(self):
        return self.invite.get_users_list()

    def get_user_state(self, user_id):
        if self.get_user_from().id == user_id:
            i = self.get_users_list().index(user_id)
        else:
            i = self.get_users_list().index(user_id)
        return json.loads(self.users_state)[i]

    def set_user_state_go(self, user_id):
        if self.winner_id != 0:
            if self.get_user_from().id == user_id:
                i = self.get_users_list().index(user_id)
            else:
                i = self.get_users_list().index(user_id)
            tmp_lst = self.get_users_sate()
            tmp_lst[i] = 'go'
            self.users_state = json.dumps(tmp_lst)
            self.save()
        else:
            raise GameWinnerNotExists()

    def set_user_state_end(self, user_id):
        if self.winner_id != 0:
            if self.get_user_from().id == user_id:
                i = self.get_users_list().index(user_id)
            else:
                i = self.get_users_list().index(user_id)
            tmp_lst = self.get_users_sate()
            tmp_lst[i] = 'end'
            self.users_state = json.dumps(tmp_lst)
            self.save()
        else:
            raise GameWinnerNotExists

    def get_users_state_list(self):
        return json.loads(self.users_state)

    def check_users_online(self):
        for user_id in self.get_users_list():
            if not UserOnline.objects.get(user_id=user_id).online_game:
                self.winner_id = user_id
                self.active = False
                self.save()
                self.invite.game_started = False
                self.invite.game_ended = True
                self.invite.save()
                self.set_user_state_end(user_id)

    def save(self, *args, **kwargs):
        for e in GameXO.objects.filter(active=True):
            for user_id in e.get_users_list():
                if (e.id != self.pk) and (user_id in self.get_users_list()):
                    raise GameOnlyOne

        super(GameXO, self).save(*args, **kwargs)