# -*- coding: utf-8 -*-
from mygame.models import GameXO
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from mygame.exeptions import GameWrongWay, GameWinnerNotExists
import json


def check_active_game(user_id):
    result = False
    for game in GameXO.objects.filter(active=True):
        if user_id in game.invite.get_users_list():
            result = True
    return result


def check_user_lock(user_id, game_id):
    try:
        game = GameXO.objects.get(id=game_id)
    except ObjectDoesNotExist:
        raise Http404

    if (game.last_move_id == user_id) and (game.winner_id == 0):
        return True
    else:
        return False


# api_game functions

def game_get_status(request, game_id):

    result_dict = dict()
    def_state = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    try:
        game = GameXO.objects.get(id=game_id)

    except ObjectDoesNotExist:
        result_dict['status'] = 'end_game'
        result_dict['game_state'] = def_state
        return HttpResponse(json.dumps(result_dict), content_type="application/javascript")

    state = game.get_state()

    result_dict['status'] = 'lock' if game.last_move_id == request.user.id else 'unlock'

    if game.winner_id == request.user.id:
        result_dict['status'] = 'win'
    elif game.winner_id == game.get_opponent(request.user.id).id:
        result_dict['status'] = 'lose'

    if game.winner_id == -1:
        result_dict['status'] = 'dead_heat'

    if game.get_user_state(request.user.id) == 'go':
        result_dict['status'] = 'wait_response'

    if ('end' in game.get_users_state_list()) or not game.active:
        result_dict['status'] = 'end_game'

    result_dict['game_state'] = state

    return HttpResponse(json.dumps(result_dict), content_type="application/javascript")


def game_new_move(request, game_id):
    if not check_user_lock(request.user.id, game_id):
        try:
            game = GameXO.objects.get(id=game_id)
        except ObjectDoesNotExist:
            raise 404

        value = 1 if game.get_user_from().id == request.user.id else 2

        import re
        re_pattern = re.compile(r'id(\d)(\d)')
        row, col = re_pattern.match(request.POST['cell']).groups()

        try:
            with transaction.atomic():
                game.new_move(int(row), int(col), value)
                game.set_win(value)
        except GameWrongWay:
            pass
    return HttpResponse('', content_type="text/plain")


def game_repeat(request, game_id):
    try:
        game = GameXO.objects.get(id=game_id)
    except ObjectDoesNotExist:
        raise Http404

    try:
        with transaction.atomic():
            game.set_user_state_go(request.user.id)

            if game.get_users_sate() == ['go', 'go']:
                game.last_move_id = game.get_user_to().id
                game.winner_id = 0
                game.state = json.dumps([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
                game.users_state = json.dumps(['', ''])
                game.save()
                return HttpResponseRedirect('/game/')
    except GameWinnerNotExists:
        pass

    return HttpResponse('', content_type="text/plain")


def game_end(request, game_id):
    try:
        game = GameXO.objects.get(id=game_id)
    except ObjectDoesNotExist:
        raise Http404
    try:
        with transaction.atomic():
            game.set_user_state_end(request.user.id)
            game.active = False
            game.save()
            game.invite.game_started = False
            game.invite.game_ended = True
            game.invite.save()
    except GameWinnerNotExists:
        pass
    return HttpResponse('', content_type="text/plain")