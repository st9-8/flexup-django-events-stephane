from core.utils.print_context import _print_context
from .models import Event, Response, Status
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import ListView
from events.forms import EventForm, ResponseForm
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.template.loader import render_to_string
from django.middleware.csrf import get_token
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden
from django.db.models import Q

def home(request):
    return render(request, 'home.html')

def dashboard(request):
    """
    Display the user's dashboard with their events and responses.
    This view doesn't fetch data from the server - all data is stored in the browser.
    """
    return render(request, 'dashboard.html')

def events(request):
    columns = [
        {"name": "name", "title": "Title"},
        {"name": "start_date", "title": "Start date"},
        {"name": "location", "title": "Location"},
        {"name": "description", "title": "Description"},
    ]

    data = list(Event.objects.all())
    for row in data:
        row.link = reverse('event_register', args=[row.event_slug])
        row.actions = [
            {"url": reverse('event_register', args=[row.event_slug]), "class":"", "icon": "bi bi-eye", "onclick": None},
            {"url": "#", "class":"ms-3", "icon": "bi bi-trash", "onclick": f"deleteEvent(event,'{row.event_slug}')"}
        ]
    context = {"title": "Events", "columns": columns, "data": data}
    return render(request, "events.html", context)

def event_create(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save()
            messages.success(request, "The event has been successfully created!")
            return redirect('event_manage', event_slug=event.event_slug, organizer_token=event.organizer_token)
    else:
        form = EventForm(request=request)
    return render(request, 'event_form.html', {'form': form, 'editable': False, 'view_mode_only': False})

def event_view(request, event_slug):
    event = get_object_or_404(Event, event_slug=event_slug)
    form = EventForm(instance=event, request=request, lock_fields=True)
    return render(request, 'event_view.html', {
        'event': event,
        'form': form,
        'editable': False,
        'view_mode_only': True,
    })

def event_edit(request, event_slug, organizer_token):
    event = get_object_or_404(Event, event_slug=event_slug, organizer_token=organizer_token)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event, request=request)
        if form.is_valid():
            form.save()
            messages.success(request, "The event has been successfully updated!")
            return redirect('event_manage', event_slug=event.event_slug, organizer_token=event.organizer_token)
        
    return render(request, 'event_form.html', {
        'form': EventForm(request=request, instance=event),
        'editable': True,
        'view_mode_only': False
    })

def event_register(request, event_slug):
    event = get_object_or_404(Event, event_slug=event_slug)
   
   
    # Check if the request is coming from an organizer
    organizer_token = request.GET.get('organizer_token')
    response_token = request.GET.get('response_token')
    is_organizer = False
    response = None

    if organizer_token:
        # Verify the organizer token matches the event
        is_organizer = (organizer_token == event.organizer_token)
        
        # Add to session if valid
        if is_organizer:
            if 'organizer_tokens' not in request.session:
                request.session['organizer_tokens'] = []
            if event.organizer_token not in request.session['organizer_tokens']:
                organizer_tokens = request.session['organizer_tokens']
                organizer_tokens.append(event.organizer_token)
                request.session['organizer_tokens'] = organizer_tokens
    
    # Check if there's a response_token to edit an existing response
    if response_token:
        try:
            response = Response.objects.get(event=event, response_token=response_token)
        except Response.DoesNotExist:
            response = None
    
    # Get responses that are not on waiting list
    responses = Response.objects.filter(event=event, is_waiting_list=False)
    
    if request.method == 'POST':
        is_organizer = is_organizer or request.POST.get('is_organizer', False) in ('True', True)
        # If we have a response, we're updating an existing one
        if response:
            response_form = ResponseForm(request.POST, instance=response, event=event, request=request, is_organizer=is_organizer)
        else:
            response_form = ResponseForm(request.POST, event=event, request=request, is_organizer=is_organizer)
        
        print(f"Form is bound: {response_form.is_bound}")
        print(f"Form data: {response_form.data}")
        
        if response_form.is_valid():
            print(f"Form is valid. Cleaned data: {response_form.cleaned_data}")
            
            if response:
                # Updating existing response
                response_form.save()
                return redirect('response_manage', event_slug=event_slug, response_token=response.response_token)
            else:
                # Creating new response
                response = Response(
                    name=response_form.cleaned_data['name'],
                    email=response_form.cleaned_data['email'],
                    message=response_form.cleaned_data.get('message', ''),
                    status=response_form.cleaned_data['status'],
                    event=event,
                    is_organizer=is_organizer,
                    is_waiting_list=False  # Default to not on waiting list
                )
                
                if is_organizer and not event.is_at_capacity:
                    response.is_waiting_list = response_form.cleaned_data['is_waiting_list']
                # Auto-apply waiting list in two cases:
                # 1. Event requires approval for all guests
                # 2. Event is at capacity and the guest confirmed attendance
                elif not is_organizer and (event.waiting_list or (response.status == Status.CONFIRMED and event.is_at_capacity)):
                    response.is_waiting_list = True
                
                try:
                    print(f"Saving response: {response.name}, event: {response.event}, status: {response.status}")
                    response.save()
                    print(f"Response saved successfully with ID: {response.id}")
                    
                    # Redirect back to event management page if organizer
                    if is_organizer:
                        return redirect('event_manage', event_slug=event_slug, organizer_token=event.organizer_token)
                    else:
                        return redirect('response_manage', event_slug=event_slug, response_token=response.response_token)
                except Exception as e:
                    print(f"Error saving response: {str(e)}")
                    raise
        else:
            print(f"Form is invalid. Errors: {response_form.errors}")
    else:
        if response:
            response_form = ResponseForm(instance=response, event=event, request=request, is_organizer=is_organizer)
        else:
            response_form = ResponseForm(event=event, request=request, is_organizer=is_organizer)

    confirmed_responses = event.responses.filter(status="CONFIRMED", is_waiting_list=False)
    form = EventForm(instance=event, request=request, lock_fields=True)
    
   
    context = {
        'event': event,
        'form': form,
        'response_form': response_form,
        'responses': responses,
        'response': response,
        'is_organizer': is_organizer,
        'confirmed_responses': confirmed_responses,
        'editable': False,
        'view_mode_only': True,
    }
    return render(request, 'event_register.html', context)

def event_manage(request, event_slug, organizer_token):
    event = get_object_or_404(Event, event_slug=event_slug, organizer_token=organizer_token)
    responses = Response.objects.filter(event=event)
    confirmed_responses = event.responses.filter(status=Status.CONFIRMED, is_waiting_list=False)
    declined_responses = event.responses.filter(Q(status=Status.DECLINED) | Q(status=Status.REJECTED))
    pending_responses = event.responses.exclude(
        Q(id__in=confirmed_responses.values_list('id', flat=True))|
        Q(id__in=declined_responses.values_list('id', flat=True))
    )
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event, request=request)
        if form.is_valid():
            form.save()
            return redirect('event_manage', event_slug=event_slug, organizer_token=organizer_token)
    else:
        form = EventForm(instance=event, request=request, lock_fields=True)
    
    response_form = ResponseForm(request=request, is_organizer=True, event=event)
    return render(request, 'event_manage.html', {
        'event': event,
        'form': form,
        'response_form': response_form,
        'responses': responses,
        'confirmed_responses': confirmed_responses,
        'pending_responses': pending_responses,
        'declined_responses': declined_responses,
        'organizer_token': organizer_token,
        'is_organizer': True,
    })

@require_POST
def event_delete(request, event_slug, organizer_token):
    event = get_object_or_404(Event, event_slug=event_slug, organizer_token=organizer_token)
    event.delete()
    return redirect('home')

def response_manage(request, event_slug, response_token):
    response = get_object_or_404(Response, response_token=response_token, event__event_slug=event_slug)
    event = response.event
    is_organizer = (event.organizer_token in request.session.get('organizer_tokens', []))
    
    if request.method == 'POST':
        is_organizer = is_organizer or request.POST.get('is_organizer', False)
        response_form = ResponseForm(
            request.POST, 
            instance=response, 
            event=event,
            request=request,
            is_organizer=is_organizer
        )
        if response_form.is_valid():
            response_form.save()
            return redirect('response_manage', event_slug=event_slug, response_token=response_token)
    else:
        response_form = ResponseForm(
            instance=response, 
            event=event,
            request=request,
            is_organizer=is_organizer
        )
    
    form = EventForm(instance=event, request=request, lock_fields=True)
    return render(request, 'response_manage.html', {
        'event': event,
        'response': response,
        'form': form,
        'response_form': response_form,
        'is_organizer': is_organizer,
        'editable': False,
        'view_mode_only': True,
    })

@require_POST
def response_delete(request, event_slug, response_token):
    response = get_object_or_404(Response, response_token=response_token, event__event_slug=event_slug)
    event = response.event
    response.delete()
    return redirect('event_manage', event_slug=event_slug, organizer_token=event.organizer_token)

@require_POST
def update_response_status(request, event_slug, response_token, organizer_token):
    """
    HTMX endpoint to update a response's status
    """
    response = get_object_or_404(Response, response_token=response_token, event__event_slug=event_slug)
    event = response.event
    
    # Check if the user is an organizer for this event
    is_organizer = (event.organizer_token == organizer_token)
    
    if not is_organizer:
        return HttpResponseForbidden("You don't have permission to update this response")
    
    new_status = request.POST.get('status')
    print(f"🔍 Nouveau statut reçu : {new_status}") 
    if new_status and new_status in [status.value for status in Status]:
        response.status = new_status
        response.save()
        
    # Return the updated response row
    context = {
        'response': response,
        'event': event,
        'is_organizer': is_organizer,
        'organizer_token': organizer_token
    }
    return render(request, 'partials/response_row.html', context)

@require_POST
def toggle_waiting_list(request, event_slug, response_token, organizer_token):
    """
    HTMX endpoint to toggle waiting list status for a response
    """
    response = get_object_or_404(Response, response_token=response_token, event__event_slug=event_slug)
    event = response.event
    
    # Check if the user is an organizer for this event
    is_organizer = (event.organizer_token == organizer_token)
    
    if not is_organizer:
        return HttpResponseForbidden("You don't have permission to update this response")
    
    # Toggle waiting list status
    response.is_waiting_list = not response.is_waiting_list
    response.save()
    
    # Return the updated response row
    context = {
        'response': response,
        'event': event,
        'organizer_token': organizer_token,
        'is_organizer': is_organizer
    }
    return render(request, 'partials/response_row.html', context)
