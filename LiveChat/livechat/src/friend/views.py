from django.shortcuts import render, redirect
from django.http import HttpResponse
import json
from account.models import Account
from friend.models import FriendRequest, FriendList


def get_friend_requests(request, *args, **kwargs):
    """
    facem query-ul la db pentru friend-requesturi si trimitem datele la front end pentru afisarea in UI
    """
    context = {}
    user = request.user
    if user.is_authenticated:
        user_id = kwargs.get("user_id")
        account = Account.objects.get(pk=user_id)
        if account == user:
            friend_requests = FriendRequest.objects.filter(receiver=account, is_active=True)
            context["friend_requests"] = friend_requests
        else:
            return HttpResponse(
                "You can't view other people's friend requests, go to your own profile in order to see yours.")
    else:
        redirect("login")
    return render(request, "friend/friend_requests.html", context)


def send_friend_request(request):
    """
    luam toate friend-requesturile existente intre cei doi useri din baza de date
    folosind instructiunea filter si daca nu exsita deja un friend request activ atunci trimitem unul nou.
    mapam response-ul in context pentru abilitatea de a modifica dinamic ui-ul in cadrul scripturilor de javascript
    """
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
                # get all friends requests between user and receiver
                friend_requests = FriendRequest.objects.filter(sender=user, receiver=receiver)
                try:
                    for friend_request in friend_requests:
                        if friend_request.is_active:
                            raise Exception("You already sent them a friend request")
                    friend_request = FriendRequest(sender=user, receiver=receiver)
                    friend_request.save()
                    payload['response'] = "Friend request sent."
                except Exception as e:
                    payload['response'] = str(e)
            except FriendRequest.DoesNotExist:
                friend_request = FriendRequest(sender=user, receiver=receiver)
                friend_request.save()
                payload['response'] = "Friend request sent"

                if payload['response'] is None:
                    payload['response'] = "Something went wrong"
        else:
            payload['response'] = "Unable to send the friend request"
    else:
        payload['response'] = "You must be authenticated to send a friend request"
    return HttpResponse(json.dumps(payload), content_type="application/json")


def accept_friend_request(request, *args, **kwargs):
    """
    luam toate friend requesturile dintre cei doi useri, iar daca exista una activa atunci o acceptam
    """
    user = request.user
    payload = {}
    if request.method == "GET" and user.is_authenticated:
        # get friend request id from link
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            if friend_request.receiver == user: #daca primim noi firend requestul doar atunci il putem accepta
                if friend_request:
                    friend_request.accept()
                    payload['response'] = "Friend request accepted."
                else:
                    payload['response'] = "Something went wrong, please try again later."
            else:
                payload['response'] = "You can't except requests for other people."
        else:
            payload['response'] = "Unable to accept that friend request."
    else:
        payload['response'] = "You must be authenticated to accept a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def remove_friend(request, *args, **kwargs):
    """
    Facem query dupa userul care trebuie eliminat si dupa prietenii userului care vrea sa elimine prietenul, si apelam
    functia din models de eliminarea a prietenului din lista de prieteni
    """
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            try:
                removee = Account.objects.get(pk=user_id)
                friend_list = FriendList.objects.get(user=user)
                friend_list.unfriend(removee)
                payload['response'] = "Friend has been removed."
            except Exception as e:
                payload['response'] = f"Something went wrong: {e}."
        else:
            payload['response'] = "There was an error, please try again later."
    else:
        payload['response'] = "You must be authenticated in order to perform this operation."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def decline_friend_request(request, *args, **kwargs):
    """
    Facem query dupa frined requesturile dintre cei doi useri(sender, receiver), iar apoi, folosind functia de decline() din models refuzam
    friend-requestul
    """
    user = request.user
    payload = {}
    if request.method == "GET" and user.is_authenticated:
        friend_request_id = kwargs.get("friend_request_id")
        if friend_request_id:
            friend_request = FriendRequest.objects.get(pk=friend_request_id)
            if friend_request.receiver == user:
                if friend_request:
                    friend_request.decline()
                    payload['response'] = "Friend request declined."
                else:
                    payload['response'] = "Something went wrong."
            else:
                payload['response'] = "That is not your frined request to decline."
        else:
            payload['response'] = "Unable to decline that friend request."
    else:
        payload['response'] = "You must be authenticated in order to perform this action."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def cancel_friend_request(request, *args, **kwargs):
    """
    Facem query dupa frined requesturile dintre cei doi useri(sender, receiver), iar apoi, folosind functia de cancel() din models refuzam
    friend-requestul
    """
    user = request.user
    payload = {}
    if request.method == "POST" and user.is_authenticated:
        user_id = request.POST.get("receiver_user_id")
        if user_id:
            receiver = Account.objects.get(pk=user_id)
            try:
                friend_requests = FriendRequest.objects.filter(sender=user, receiver=receiver, is_active=True)
                if len(friend_requests) > 1:
                    for request in friend_requests:
                        request.cancel()
                else:
                    friend_requests.first().cancel()
                payload['response'] = "Friend request cancelled."
            except Exception as e:
                payload['response'] = "Friend request does not exist."
        else:
            payload['response'] = "Could not perform the operation."
    else:
        payload['response'] = "You must be authenticated to cancel a friend request."
    return HttpResponse(json.dumps(payload), content_type="application/json")


def friend_list_view(request, *args, **kwargs):
    """
    Facem query dupa toti prietenii userukui care face requestul si error handling pentru cazurile in care userul care
    face requsetul nu este logat, sau nu are dreptul de a vedea prietenii altcuiva(care nu ii este prieten) si mapam
    in context lista de prieteni pentru a o afisa in partea de front end pe ui
    """
    context = {}
    user = request.user
    # if we are authenticated
    if user.is_authenticated:
        user_id = kwargs.get("user_id")
        if user_id:
            try:
                this_user = Account.objects.get(pk=user_id)  # the account we are viewing
                context['this_user'] = this_user
            except Account.DoesNotExist:
                return HttpResponse("That user does not exist")
            try:
                friend_list = FriendList.objects.get(user=this_user)
            except FriendList.DoesNotExist:
                return HttpResponse(f"Could not find a friend list for {this_user.username}")

            # if we try to view someone else's friends and we are not their friends we cannot do that
            if user != this_user:
                if user not in friend_list.friends.all():
                    return HttpResponse("You must be friends in order to be someone else's friend list")
            friends = []  # [(account, IS_FRIEND)...]
            auth_user_friend_list = FriendList.objects.get(user=user)
            for friend in friend_list.friends.all():
                friends.append((friend, auth_user_friend_list.is_mutual_friend(friend)))
            context['friends'] = friends
    else:
        return HttpResponse("You must be friends to view their friends list")
    return render(request, "friend/friend_list.html", context)
