import cv2
import numpy as np
import base64
from django.core.files.base import ContentFile
from .models import User , LoginLog, Activity
import insightface
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserForm, ActivityForm
from django.contrib import messages
import subprocess
from scapy.all import ARP, Ether, srp

# Charger le modèle InsightFace
model = insightface.app.FaceAnalysis(name="buffalo_l")
model.prepare(ctx_id=-1, det_size=(640,640))

# Registere
def sign_in_views(request):

    user_id = request.session.get('user_id')

    if user_id:  
        return redirect("dashboard")



    message = ""
    if request.method == "POST":
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password1"]

            if User.objects.filter(username=username).exists():
                messages.error(request, "❌ Ce nom d'utilisateur existe déjà.")
                message = "❌ Ce nom d'utilisateur existe déjà."
                return render(request, "login/sign_in.html", {"form": form, 'message': message})

            user = User(username=username, email=email)
            user.set_password(password)

            # Image upload ou scan
            img_file = None
            if form.cleaned_data.get("image_upload"):
                img_file = form.cleaned_data["image_upload"]
            elif form.cleaned_data.get("image_scan"):
                image_data = form.cleaned_data["image_scan"]
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                img_file = ContentFile(base64.b64decode(imgstr), name=f"{username}.{ext}")

            
            if img_file:
                # user.image = img_file
                # # Calculer l'embedding
                # img_path = user.image.path if hasattr(user.image, 'path') else None
                # if not img_path:  # temporaire pour base64
                #     temp_path = f"temp_{username}.png"
                #     with open(temp_path, "wb") as f:
                #         f.write(img_file.read())
                #     img_path = temp_path

                # img_cv = cv2.imread(img_path)

                user.image = img_file  # on attache le fichier
                # Lire l'image pour calculer l'embedding
                img_file.seek(0)  # revenir au début du fichier
                file_bytes = np.frombuffer(img_file.read(), np.uint8)
                img_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                faces = model.get(img_cv)
                if faces:
                    user.embedding = faces[0].embedding.tolist()
                else:
                    messages.error(request, "❌ Aucun visage détecté sur l'image.")
                    message = "❌ Aucun visage détecté sur l'image."
                    return render(request, "login/sign_in.html", {"form": form, 'message': message})

            
            user.save()
            messages.success(request, "✅ Inscription réussie !")
            return redirect("login")
        else:
            messages.error(request, "❌ Veuillez replir bien le formulaire.")
            message = "❌ Veuillez replir bien le formulaire."
            return render(request, "login/sign_in.html", {"form": form, 'message': message})

    else:
        form = UserForm()
        

    return render(request, "login/sign_in.html", {"form": form, 'message': message})

# Get the mac of the host
def get_mac(ip):
    try:
        pkt = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip)
        ans, _ = srp(pkt, timeout=2, verbose=0)
        for _, rcv in ans:
            return rcv[Ether].src
    except Exception:
        return None
    return None

# Login 
def login_views(request):

    user_id = request.session.get('user_id')

    if user_id:  
        return redirect("dashboard")


    form = UserForm()
    user = None
    if 'user_id' in request.session:
        try:
            user = User.objects.get(id=request.session['user_id'])
        except User.DoesNotExist:
            user = None
    message = ""


    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password1")
        face_scan = request.POST.get("face_scan")
        ip_address = request.META.get("REMOTE_ADDR")
        mac_address = get_mac(ip_address)

        
        if username and password:
            
            try:
                user = User.objects.get(username=username)
                if not user.is_active:
                    message = "L'utilisateur n'est pas encore actif."
                    return render(request, "login/login.html", {"form": form, "user": None, "message": message})


                if user.check_password(password):
                    # Si le scan de visage est fourni, on vérifie également l'embedding
                    if face_scan:
                        if user.embedding is None:
                            messages.error(request, "❌ Aucun visage enregistré pour cet utilisateur.")
                            message = "❌ Aucun visage enregistré pour cet utilisateur."
                        else:
                            nparr = np.frombuffer(base64.b64decode(face_scan.split(';base64,')[1]), np.uint8)
                            img_scan = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                            faces_scan = model.get(img_scan)
                            if not faces_scan:
                                messages.error(request, "❌ Aucun visage détecté sur le scan.")
                                message = "❌ Aucun visage détecté sur le scan."
                            else:
                                emb_scan = faces_scan[0].embedding
                                emb_user = np.array(user.embedding)
                                similarity = np.dot(emb_scan, emb_user) / (np.linalg.norm(emb_scan) * np.linalg.norm(emb_user))
                                if similarity < 0.4:
                                    messages.error(request, "❌ Visage non reconnu pour cet utilisateur.")
                                    message = "❌ Visage non reconnu pour cet utilisateur."
                                else:
                                    # Connexion réussie
                                    request.session['user_id'] = user.id
                                    request.session['username'] = user.username

                                    LoginLog.objects.create(
                                        user=user,
                                        username=username,
                                        ip_address=ip_address,
                                        mac_address=mac_address,
                                        status="success"
                                    )

                                    return redirect("login")  # redirige vers la page souhaitée
                    else:
                        # Pas de scan fourni, connexion par mot de passe uniquement
                        # request.session['user_id'] = user.id
                        # request.session['username'] = user.username
                        message = "Pas de Image fournie"
                        LoginLog.objects.create(
                            user=user,
                            username=username,
                            ip_address=ip_address,
                            mac_address=mac_address,
                            status="failed"
                        )
                        return render(request, "login/login.html", {"form": form, "user": user, "message": message})

                else:
                    messages.error(request, "❌ Mot de passe incorrect.")
                    message = "❌ Mot de passe incorrect."
                    LoginLog.objects.create(
                        user=user,
                        username=username,
                        ip_address=ip_address,
                        mac_address=mac_address,
                        status="failed"
                    )
            except User.DoesNotExist:
                messages.error(request, "❌ Utilisateur introuvable.")
                message = "❌ Utilisateur introuvable."
                LoginLog.objects.create(
                    user=user,
                    username=username,
                    ip_address=ip_address,
                    mac_address=mac_address,
                    status="failed"
                )

    
    return render(request, "login/login.html", {"form": form, "user": user, "message": message})

def user_list(request):
    user_id = request.session.get('user_id')


    if request.session.get("username") != "admin":
        return redirect("dashboard")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("login")


    list = User.objects.all()
    return render(request, 'login/user_list.html', {'list': list, 'user': user})

def user_delete(request, id):

    user_id = request.session.get('user_id')


    if request.session.get("username") != "admin":
        return redirect("dashboard")

    user = get_object_or_404(User, id=id)
    if request.method == "POST":
        user.delete()
        return redirect('user_list')
    
    return render(request, 'login/user_delete.html', {'user': user})

def user_active(request, id):
    user_id = request.session.get('user_id')

    if request.session.get("username") != "admin":
        return redirect("dashboard")

    user = get_object_or_404(User, id=id)
    
    if request.method == "POST":
        user.is_active = not user.is_active
        user.save()

        return redirect('user_list')
    
    return redirect('user_list')

# Acceil du site 
def home(request):
    user_id = request.session.get('user_id')

    if user_id:
        return redirect("dashboard")
    return render(request, 'login/home.html')



# Logout 
def logout(request):
    user_id = request.session.get('user_id')
    ip_address = request.META.get("REMOTE_ADDR")
    mac_address = get_mac(ip_address)

    if user_id:
        user = User.objects.get(id=user_id)
        LoginLog.objects.create(
            user=user,
            username=user.username,
            ip_address=ip_address,
            mac_address=mac_address,
            status="logout"
        )


    request.session.flush() 
    return redirect("login")



def dashboard(request):
    all_user = User.objects.all()
    # activities = Activity.objects.all()
    activities = Activity.objects.order_by("-created_at")[:2]
    user_id = request.session.get('user_id')
    users = User.objects.all()
    active_users = users.filter(is_active=True)
    inactive_users = users.filter(is_active=False)

    if not user_id:  # pas connecté
        return redirect("login")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("login")

    return render(request, "login/dashboard.html", {
        "user": user, 
        "users": users,
        "active_count": active_users.count(),
        "inactive_count": inactive_users.count(),
        "total_count": users.count(),
        "activities": activities, 
    })


def user_modify(request):
    message = ""
    message_error = ""
    user = None

    if 'user_id' in request.session:
        try:
            user = User.objects.get(id=request.session['user_id'])
            form = UserForm(instance=user)
        except User.DoesNotExist:
            messages.error(request, "Utilisateur non trouvé.")
            return redirect("login")


    if request.method == "POST":
        form_type = request.POST.get("form_type")

        # -------------------------------
        # Modification informations
        # -------------------------------
        if form_type == "update_info":
            form = UserForm(request.POST, request.FILES, instance=user)

            if form.is_valid():
                user.username = form.cleaned_data["username"]
                user.email = form.cleaned_data["email"]

                # Image upload ou scan
                img_file = None
                if form.cleaned_data.get("image_upload"):
                    img_file = form.cleaned_data["image_upload"]
                elif form.cleaned_data.get("image_scan"):
                    image_data = form.cleaned_data["image_scan"]
                    format, imgstr = image_data.split(';base64,')
                    ext = format.split('/')[-1]
                    img_file = ContentFile(base64.b64decode(imgstr), name=f"{user.username}.{ext}")

                if img_file:
                    user.image = img_file
                    img_file.seek(0)
                    file_bytes = np.frombuffer(img_file.read(), np.uint8)
                    img_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                    faces = model.get(img_cv)
                    if faces:
                        user.embedding = faces[0].embedding.tolist()
                    else:
                        message_error = "❌ Aucun visage détecté sur l'image/scan."
                        messages.error(request, "❌ Aucun visage détecté sur l'image/scan.")
                        return render(request, "login/modify.html", {"form": form, "user": user, "message": message, 'message_error': message_error})

                user.save()
                message = "✅ Informations mises à jour avec succès !"
                messages.success(request, "✅ Informations mises à jour avec succès !")

                return render(request, "login/modify.html", {"form": form, "user": user, "message": message, 'message_error': message_error})
            else:
                message_error = "❌ Formulaire invalide."
                messages.error(request, "❌ Formulaire invalide.")
        
        # -------------------------------
        # Changement mot de passe
        # -------------------------------
        elif form_type == "change_password":
            current = request.POST.get("current_password")
            new1 = request.POST.get("new_password1")
            new2 = request.POST.get("new_password2")

            if not user.check_password(current):
                message_error = "❌ Mot de passe actuel incorrect."
                messages.error(request, "❌ Mot de passe actuel incorrect.")
            elif new1 != new2:
                message_error = "❌ Les nouveaux mots de passe ne correspondent pas."
                messages.error(request, "❌ Les nouveaux mots de passe ne correspondent pas.")
            else:
                user.set_password(new1)
                user.save()
                message = "✅ Mot de passe mis à jour avec succès !"
                messages.success(request, "✅ Mot de passe mis à jour avec succès !")
                 
                return render(request, "login/modify.html", {"form": form, "user": user, "message": message, 'message_error': message_error})


    else:
        form = UserForm(instance=user)

    return render(request, "login/modify.html", {"form": form, "user": user, "message": message, 'message_error': message_error})
    
# Log list
def user_log(request):
    user_id = request.session.get('user_id')

    if request.session.get("username") != "admin":
        return redirect("dashboard")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("login")


    logs = LoginLog.objects.all()
    return render(request, 'login/log.html', {'logs': logs, 'user': user})

def create_activity(request):
    user_id = request.session.get('user_id')

    if request.session.get("username") != "admin":
        return redirect("dashboard")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("login")


    if request.method == "POST":
        form = ActivityForm(request.POST, request.FILES)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.author = get_object_or_404(User, id=user_id)
            activity.save()
            return redirect("activity_list")  # à définir
    else:
        form = ActivityForm()


    return render(request, "login/create_activity.html", {"form": form, 'user': user})


def activity_list(request):
    user_id = request.session.get('user_id')


    if request.session.get("username") != "admin":
        return redirect("dashboard")
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("login")


    list = Activity.objects.all()
    return render(request, 'login/activity_list.html', {'list': list, 'user': user})

def activity_delete(request, id):
    user_id = request.session.get('user_id')


    if request.session.get("username") != "admin":
        return redirect("dashboard")

    activity = get_object_or_404(Activity, id=id)
    if request.method == "POST":
        activity.delete()
        return redirect('activity_list')
    
    return render(request, 'login/activity_delete.html', {'activity': activity})

def activity_list_all(request):
    user_id = request.session.get('user_id')
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("login")


    activities = Activity.objects.all()
    return render(request, 'login/activity_list_all.html', {'activities': activities, 'user': user})

