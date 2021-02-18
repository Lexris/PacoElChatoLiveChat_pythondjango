from django.shortcuts import render


# def home_screen_view(request, *args, **kwardgs):
#     context = {}
#     return render(request, "personal/home.html", context)


def lobby_select(request):
    """
    Contextul este gol deoarece aceast este pagina de home si nu avem nevoie de date pentru frontend
    """
    return render(request, "personal/home.html", {})


def room(request, room_name):
    """
    Trimitem in context username-ul(pentru afisarea numelui in chat) si room-name-ul(pentru crearea/accesarea chatului ales)
    """
    return render(request, 'personal/room.html', {
        'username': request.user.username,
        'room_name': room_name
    })
