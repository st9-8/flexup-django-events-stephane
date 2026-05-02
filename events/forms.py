from django import forms
from django.urls import reverse
from .models import Event, Response, Status
from django.utils.translation import gettext_lazy as _


class EventForm(forms.ModelForm):
    organizerLink = forms.CharField(
        label="Copy organizer link",
        required=False,
        widget=forms.TextInput(attrs={
            'title': 'This field is auto-generated to create a unique private URL for organizers, allowing them to manage the event. Click on it to copy it to the clipboard. Save it and share it with other co-organizer if needed, but don\'t share it with guests.',
            'readonly': 'readonly',
            'class': 'bg-blue-50 mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 cursor-pointer',
        })
    )

    registrationLink = forms.CharField(
        label="Copy registration link",
        required=False,
        widget=forms.TextInput(attrs={
            'title': 'This field is auto-generated to create a unique URL for the event. Click on it to copy it to the clipboard. Save it and share it with the guests.',
            'readonly': 'readonly',
            'class': 'bg-blue-50 mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 cursor-pointer',
        })
    )

    class Meta:
        model = Event
        fields = ['name', 'description', 'location', 'start_date', 'start_time',
                  'end_date', 'end_time', 'is_all_day', 'max_attendees', 'min_attendees', 'waiting_list']
        widgets = {
            'name': forms.TextInput(attrs={
                'autocomplete': 'off',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'location': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'start_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'end_time': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'min_attendees': forms.NumberInput(attrs={
                'min': '0',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'max_attendees': forms.NumberInput(attrs={
                'min': '1',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'
            }),
            'is_all_day': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
            'waiting_list': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500'
            }),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        lock_fields = kwargs.pop('lock_fields', False)

        super().__init__(*args, **kwargs)

        # Set initial values for links if the instance exists
        if self.instance and self.instance.pk:
            event_slug = self.instance.event_slug
            organizer_token = self.instance.organizer_token

            # Generate full URLs for organizerLink and registrationLink
            if request:
                domain = request.build_absolute_uri('/')[:-1]  # Get the full domain name
                if 'organizerLink' in self.fields:
                    self.fields[
                        'organizerLink'].initial = f"{domain}{reverse('event_manage', kwargs={'event_slug': event_slug, 'organizer_token': organizer_token})}"

                if 'registrationLink' in self.fields:
                    self.fields[
                        'registrationLink'].initial = f"{domain}{reverse('event_register', kwargs={'event_slug': event_slug})}"

            if lock_fields:
                for field in self.fields:
                    if 'class' in self.fields[field].widget.attrs:
                        self.fields[field].widget.attrs['class'] += " bg-blue-50"
                        self.fields[field].widget.attrs['disabled'] = True


class ResponseForm(forms.ModelForm):
    response_link = forms.CharField(
        label="Response Link",
        required=False,
        widget=forms.TextInput(attrs={
            'title': 'This field is auto-generated to create a unique private URL for users, allowing them to manage their response. Click on it to copy it to the clipboard.',
            'readonly': 'readonly',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 cursor-pointer',
        })
    )

    registrationLink = forms.CharField(
        label="Registration Link",
        required=False,
        widget=forms.TextInput(attrs={
            'title': 'This field is auto-generated to create a unique URL for the event. Click on it to copy it to the clipboard. Save it and share it with the guests.',
            'readonly': 'readonly',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 cursor-pointer',
        })
    )

    class Meta:
        model = Response
        fields = ['name', 'email', 'message', 'status', 'is_waiting_list']
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'response-name'
            }),
            'email': forms.EmailInput(attrs={
                'id': 'response-email'
            }),
            'status': forms.Select(attrs={
                'id': 'response-status'
            }),
            'is_waiting_list': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500',
                'id': 'response-waiting-list'
            }),
            'message': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 border',
                'id': 'response-message'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop('event', None)
        self.request = kwargs.pop('request', None)
        self.is_organizer = kwargs.pop('is_organizer', False)

        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})

        # Set initial data
        if not instance and not initial:
            # For new responses from non-organizers, don't set a default status
            # This forces them to make a selection
            if not self.is_organizer:
                initial['status'] = None

        # Let's set the is_waiting_list default based on the value of event.waiting_list
        if self.event and self.event.waiting_list:
            initial['is_waiting_list'] = True

        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

        # Status choices depend on whether user is organizer
        if self.is_organizer:
            # Organizers can set any status
            self.fields['status'].choices = [(status.value, status.label) for status in Status]
        else:
            # Guests can only choose from guest-allowed statuses
            self.fields['status'].choices = [(status.value, status.label) for status in Status if status.guest_choice]
            # Make status required for guests
            self.fields['status'].required = True
            self.fields['status'].empty_label = None

        # Generate response link for existing responses
        if self.instance and self.instance.pk and self.instance.response_token:
            response_token = self.instance.response_token
            if self.event and self.request:
                event_slug = self.event.event_slug
                domain = self.request.build_absolute_uri('/')[:-1]  # Get the full domain name
                if 'response_link' in self.fields:
                    self.fields[
                        'response_link'].initial = f"{domain}{reverse('response_manage', kwargs={'event_slug': event_slug, 'response_token': response_token})}"
                else:
                    if 'response_link' in self.fields:
                        self.fields['response_link'].initial = ''
        else:
            # For new responses, don't show the link field yet
            self.fields.pop('response_link', None)

    def clean_is_waiting_list(self):
        """Convert checkbox 'on' value to boolean"""
        return self.data.get('is_waiting_list', 'on').lower() == 'on'

    def clean(self):
        cleaned_data = super().clean()

        # Ensure the event is set correctly
        if hasattr(self.instance, 'event') and self.instance.event:
            # Use the event set in __init__
            cleaned_data['event'] = self.instance.event

        return cleaned_data
