# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.utils.translation import ugettext as _
from django.db import transaction
from django.utils import timezone

from datetime import timedelta
import json

from mygame.forms import RegForm
from mygame.models import UserOnline, InviteToGame, GameXO
from mygame.additional import game_end, game_get_status, game_new_move, game_repeat, check_active_game
from mygame.exeptions import InviteGameIsExists, GameOnlyOne

from django.forms import ValidationError
from django.core.exceptions import ObjectDoesNotExist

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# Create your views here.


# pages

@login_required(redirect_field_name=None)
def home_page(request):
    return render(request, 'home.html')


def login_page(request):
    if request.method == 'POST':
        form = RegForm(request.POST)
        try:
            form.user_login()
            login(request, authenticate(username=request.POST['name'], password=request.POST['password']))
            return redirect('/')
        except ValidationError, e:
            msg = e.message
    else:
        form = RegForm()
        msg = ''
    return render(request, 'login.html', {'form': form, 'msg': msg})


@login_required(redirect_field_name=None)
def logout_user(request):
    logout(request)
    return redirect('/login/')


def register(request):
    if request.method == 'POST':
        form = RegForm(request.POST)
        try:
            form.user_registration()
            return render(request, 'reg_ok.html')
        except ValidationError, e:
            msg = e.message
    else:
        form = RegForm()
        msg = ''

    return render(request, 'register.html', {'form': form, 'msg': msg})


# api

@csrf_exempt
@transaction.atomic
@require_POST
@login_required
def set_user_online(request):

    try:
        user = UserOnline.objects.get(user_id=request.user.id)
        user.online = True
        if 'game' in request.POST:
            user.online_game = True
        user.save()
    except ObjectDoesNotExist:
        new_state = UserOnline(online=True)
        new_state.user_id = request.user.id
        if 'game' in request.POST:
            user.online_game = True
        new_state.save()
    return HttpResponse('OK', content_type='text/plain')


@csrf_exempt
def check_user_online(request):
    dt_now = timezone.now()
    dt_10sec = timedelta(seconds=10)
    for user in UserOnline.objects.filter(online=True):
        if dt_now - user.dt > dt_10sec:
            user.online_game = False
            user.online = False
            user.save()
    for game in GameXO.objects.filter(active=True):
        game.check_users_online()
    return HttpResponse('OK', content_type='text/plain')


@csrf_exempt
@login_required
def get_user_online(request):

    result_lst = list()

    for user in UserOnline.objects.filter(online=True):
        if user.user.username != request.user.username:
            result_lst.append([user.user.username, user.id])

    return HttpResponse(json.dumps(result_lst), content_type='application/javascript')


@csrf_exempt
@login_required
def check_state(request):
    result_dict = dict()

    if check_active_game(request.user.id):
        result_dict['state'] = 'new_game'
    else:
        result_dict['state'] = 'wait'

    if request.method == 'POST':
        result_lst = list()

        for invite in InviteToGame.objects.filter(game_ended=False, game_started=False):

            if (invite.get_users_list()[0] == request.user.id) and (invite.user_not_confirm_id !=0):
                result_dict['state'] = 'not_confirm'
                result_lst.append([invite.id, invite.get_user_not_confirm().username])
            result_dict['user_array'] = result_lst

    return HttpResponse(json.dumps(result_dict), content_type='application/javascript')


@csrf_exempt
@require_POST
@login_required
def invite_to_game(request):
    result_lst = ['', '']
    if request.POST['action'] == 'confirm':
        game_state = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        invite = InviteToGame.objects.get(id=int(request.POST['id']))
        try:
            with transaction.atomic():
                new_game = GameXO(state=json.dumps(game_state), invite_id=int(request.POST['id']),
                                  last_move_id=invite.get_users_list()[1])
                new_game.save()
                new_game.invite.game_started = True
                new_game.invite.save()

                for user_id in new_game.get_users_list():
                    uo = UserOnline.objects.get(id=user_id)
                    uo.online_game = True
                    uo.save()

        except GameOnlyOne:
            result_lst = ['warn', _(u'Пользователь уже играет попробуйте позже')]

    elif request.POST['action'] == 'deny':
        InviteToGame.objects.filter(id=request.POST['id']).update(user_not_confirm_id=request.user.id)

    elif request.POST['action'] == 'add':
        if request.user.id != int(request.POST['id']):
            try:
                with transaction.atomic():
                    new_invite = InviteToGame(users=json.dumps([request.user.id, int(request.POST['id'])]))
                    new_invite.save()
                result_lst = ['info', _(u'Приглашение отправленно')]
            except InviteGameIsExists:
                result_lst = ['warn', _(u'Невозможно отправить приглашение')]

    elif request.POST['action'] == 'close':
        InviteToGame.objects.filter(id=request.POST['id']).update(game_ended=True, user_not_confirm_id=0)

    return HttpResponse(json.dumps(result_lst), content_type='application/javascript')


@csrf_exempt
@login_required
def get_invite(request):

    result_lst = list()

    for invite in InviteToGame.objects.filter(game_ended=False, game_started=False):
        if (invite.get_users_list()[1] == request.user.id) and (invite.user_not_confirm_id != request.user.id):
            result_lst.append([invite.get_user_from().username, invite.id])

    return HttpResponse(json.dumps(result_lst), content_type='application/javascript')


@login_required
def game_page(request):

    for game in GameXO.objects.filter(active=True):

        if request.user.id in game.get_users_list():
            tmp_lst = game.get_users_list()
            tmp_lst.remove(request.user.id)
            return render(request, 'game.html', {'game_id': game.id, 'opponent': game.get_opponent(request.user.id)})
    return redirect('/')


@csrf_exempt
@require_POST
@login_required
def api_game(request, game_id):

    if 'action' in request.POST:
        func_dict = {
            'new_move': game_new_move,
            'get_status': game_get_status,
            'repeat_game': game_repeat,
            'end_game': game_end,
        }

        if request.POST['action'] in func_dict.iterkeys():
            return func_dict[request.POST['action']](request, game_id)
