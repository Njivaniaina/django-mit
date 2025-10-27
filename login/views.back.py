from django.shortcuts import render, redirect
from .forms import UserForm
from .models import User
from django.contrib import messages
import base64
from django.core.files.base import ContentFile

def login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password1")
        face_scan = request.POST.get("face_scan")

        # --- Vérification si username existe ---
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "❌ Utilisateur introuvable.")
            return render(request, "login/login.html")

        # --- Cas 1 : Login avec mot de passe ---
        if password:
            if user.check_password(password):
                login(request, user)  # Connecte l’utilisateur
                return redirect("home")  # page après connexion
            else:
                messages.error(request, "❌ Mot de passe incorrect.")

        # --- Cas 2 : Login avec Face Scan ---
        elif face_scan:
            if not user.image:
                messages.error(request, "❌ Aucun visage enregistré pour cet utilisateur.")
                return render(request, "login/login.html")

            # Convertir l'image base64 en fichier temporaire
            format, imgstr = face_scan.split(';base64,')
            img_data = base64.b64decode(imgstr)
            temp_file = ContentFile(img_data, name=f"{username}_login.png")

            # ⚠️ Ici il faut comparer `temp_file` avec `user.image`
            # Tu peux utiliser une lib comme `DeepFace` ou `face_recognition`
            # Pour l'instant, on simule une réussite si l'image existe
            if user.image:  
                login(request, user)
                return redirect("home")
            else:
                messages.error(request, "❌ Échec de la reconnaissance faciale.")

        else:
            messages.error(request, "❌ Veuillez entrer un mot de passe ou utiliser Face Scan.")

    return render(request, "login/login.html")


def sign_in(request):
    if request.method == "POST":
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password1"]

            # Vérifier si username existe déjà
            if User.objects.filter(username=username).exists():
                messages.error(request, "❌ Ce nom d'utilisateur existe déjà.")
                return render(request, "login/sign_in.html", {"form": form})

            # Créer un nouvel utilisateur
            user = User(
                username=username,
                email=email
            )
            user.set_password(password)

            # Gestion de l’image (upload ou scan)
            if form.cleaned_data.get("image_upload"):
                user.image = form.cleaned_data["image_upload"]

            elif form.cleaned_data.get("image_scan"):
                image_data = form.cleaned_data["image_scan"]
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]  # png/jpg
                file = ContentFile(base64.b64decode(imgstr), name=f"{username}.{ext}")
                user.image = file

            user.save()
            messages.success(request, "✅ Inscription réussie, vous pouvez maintenant vous connecter.")
            return redirect("login")  # à remplacer par ton URL de login

        else:
            messages.error(request, "❌ Le formulaire contient des erreurs.")
            return render(request, "login/sign_in.html", {"form": form})

    else:
        form = UserForm()
    return render(request, "login/sign_in.html", {"form": form})
