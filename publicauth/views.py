from django.conf import settings as global_settings
from django.utils.translation import ugettext as _
from django.shortcuts import redirect
from django.contrib import messages
from django.http import Http404
from django.contrib import auth 

from annoying.decorators import render_to

from publicauth.utils import str_to_class, get_backend
from publicauth import settings
from publicauth import lang


def logout(request):
    auth.logout(request)
    messages.success(request, lang.SUCCESS_LOGOUT)
    return redirect(global_settings.LOGOUT_URL)


def begin(request, provider):
    """
    Display authentication form. This is also the first step
    in registration. The actual login is in social_complete 
    function below.
    """
    # merge data from POST and GET methods
    data = request.GET.copy()
    data.update(request.POST)

    # store url to where user will be redirected 
    # after successfull authentication.
    request.session['next_url'] = request.GET.get("next") or \
                                    global_settings.LOGIN_REDIRECT_URL
        
    # start the authentication process 
    backend = get_backend(provider)
    return backend.begin(request, data)


def complete(request, provider):
    """
    After first step of public authentication, we must validate the response. 
    If everything is ok, we must do the following:
    1. If user is already authenticated:
        a. Try to login him again (strange variation but we must take it to account).
        b. Create new PublicID record in database.
        c. Merge authenticated account with newly created PublicID record.
        d. Redirect user to 'next' url stored in session.
    2. If user is anonymouse:
        a. Try to log him by identity and redirect to 'next' url.
        b. Create new  PublicID record in database.
        c. Try to automaticaly fill all extra fields with information returned form 
           server. If successfull, login the user and redirect to 'next' url.
        d. Redirect user to extra page where he can fill all extra fields by hand.
    """
    # merge data from POST and GET methods
    data = request.GET.copy()
    data.update(request.POST)

    backend = get_backend(provider)
    response = backend.validate(request, data)

    if request.user.is_authenticated():
        backend.login_user(request)
        backend.merge_accounts(request)
    else:
        backend.login_user(request)
        if not settings.REGISTRATION_ALLOWED:
            messages.warning(request, lang.REGISTRATION_DISABLED)
            return redirect(settings.REGISTRATION_DISABLED_REDIRECT)

    return backend.complete(request, response)


@render_to('publicauth/extra.html')
def extra(request, provider):
    """                                                
    Handle registration of new user with extra data for profile
    """                                                          
    try:
        identity = request.session['identity']
    except KeyError:
        raise Http404

    if request.method == "POST":
        form = str_to_class(settings.EXTRA_FORM)(request.POST)
        if form.is_valid():
            user = form.save(request, identity, provider)
            del request.session['identity']
            if not settings.PUBLICAUTH_ACTIVATION_REQUIRED:
                user = auth.authenticate(identity=identity, provider=provider)
                if user:
                    auth.login(request, user)
                    next_url = request.session['next_url']
                    del request.session['next_url']
                    return redirect(next_url)
            else:
                messages.warning(request, lang.ACTIVATION_REQUIRED_TEXT)
                return redirect(settings.ACTIVATION_REDIRECT_URL)
    else:
        initial = request.session['extra']
        form = str_to_class(settings.EXTRA_FORM)(initial=initial)

    return {'form': form}

