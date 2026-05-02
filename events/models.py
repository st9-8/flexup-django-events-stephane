from django_enum import EnumField
from django_enum.choices import TextChoices
from django.db import models
from django.forms import ValidationError
from django.utils.encoding import force_str
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from nanoid import generate
from django.utils import timezone
import datetime

def generate_token_16():
    return generate(size=16)

def generate_token_10():
    return generate(size=10)

def get_today():
    return timezone.now().date()

class Event(models.Model):
    name = models.CharField(max_length=200, verbose_name='Event name')
    description = models.TextField(verbose_name='Description', blank=True, null=True)
    location = models.CharField(max_length=200, verbose_name='Location', blank=True, null=True)
    start_date = models.DateField(verbose_name="Start date", default=get_today)
    start_time = models.TimeField(verbose_name="Start time", blank=True, null=True)
    end_date = models.DateField(verbose_name="End date", blank=True, null=True, default=get_today)
    end_time = models.TimeField(verbose_name="End time", blank=True, null=True)
    is_all_day = models.BooleanField(default=False, verbose_name="All-day event")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    max_attendees = models.PositiveIntegerField(verbose_name="Maximum attendees", blank=True, null=True)
    min_attendees = models.PositiveIntegerField(verbose_name="Minimum attendees", blank=True, null=True)
    organizer_token = models.CharField(max_length=16, unique=True, editable=False, default=generate_token_16)
    event_slug = models.CharField(max_length=50, unique=True, editable=False)
    waiting_list = models.BooleanField(default=False, verbose_name="Place all new guests on the waiting list by default", help_text=_("When this box is checked, all guests who confirm their presence will be put on the waiting list. The organizer will have to approve them before they can attend the event."))


    @property
    def has_time(self):
        return self.start_time is not None

    @property
    def duration_in_days(self):
        if not self.end_date:
            return 1
        return (self.end_date - self.start_date).days + 1
        
    @property
    def confirmed_count(self):
        """Return the count of confirmed attendees (not on waiting list)"""
        return self.responses.filter(status=Status.CONFIRMED, is_waiting_list=False).count()
        
    @property
    def waiting_list_count(self):
        """Return the count of attendees on the waiting list"""
        return self.responses.filter(is_waiting_list=True).count()
        
    @property
    def is_at_capacity(self):
        """Check if event is at capacity (if max_attendees is set)"""
        if self.max_attendees is None:
            return False
        return self.confirmed_count >= self.max_attendees
        
    @property
    def available_spots(self):
        """Return the number of available spots (or None if no max set)"""
        if self.max_attendees is None:
            return None
        return max(0, self.max_attendees - self.confirmed_count)

    @property
    def guest_choices(self):
        """Return only the statuses that guests can choose from"""
        return [status for status in Status if status.guest_choice]
        
    @property
    def organizer_choices(self):
        """Return all status options available to organizers"""
        return list(Status)

    def clean(self):
        super().clean()
        # Validate dates and times
        if self.end_date and self.start_date > self.end_date:
            raise ValidationError({'end_date': _('End date must be after start date')})
        if self.end_date == self.start_date and self.end_time and self.start_time and self.start_time > self.end_time:
            raise ValidationError({'end_time': _('End time must be after start time')})
        if self.is_all_day:
            self.start_time = None
            self.end_time = None
            
        # Validate attendee limits - NULL means "no constraint"
        if self.min_attendees is not None:
            # Only validate min_attendees if it's set
            if self.min_attendees < 0:
                raise ValidationError({'min_attendees': _('Minimum attendees cannot be negative')})
            if self.min_attendees == 0:
                raise ValidationError({'min_attendees': _('Minimum attendees cannot be zero')})
                
        if self.max_attendees is not None:
            # Only validate max_attendees if it's set
            if self.max_attendees < 0:
                raise ValidationError({'max_attendees': _('Maximum attendees cannot be negative')})
            if self.max_attendees == 0:
                raise ValidationError({'max_attendees': _('Maximum attendees cannot be zero')})
            
        # Cross-validate only if both are set
        if self.max_attendees is not None and self.min_attendees is not None:
            if self.max_attendees < self.min_attendees:
                raise ValidationError({
                    'max_attendees': _('Maximum attendees cannot be less than minimum attendees')
                })

    def save(self, *args, **kwargs):
        if not self.organizer_token:
            self.organizer_token = generate_token_16()
        if not self.event_slug:
           # slugify the date and name to create a unique URL
            from datetime import datetime
            date_str = self.start_date.strftime('%Y-%m-%d')
            
            # Create base slug from date and name (truncate if necessary)
            base_slug = slugify(f"{date_str}-{self.name}")
            if len(base_slug) > 40:  # Leave room for the random suffix
                base_slug = base_slug[:40]
                
            self.event_slug = base_slug
            
            # Keep generating a unique slug until we find one that doesn't exist
            attempt = 0
            while Event.objects.filter(event_slug=self.event_slug).exists():
                attempt += 1
                # Generate a new random suffix for each attempt
                random_suffix = generate(size=4)
                self.event_slug = f"{base_slug}-{random_suffix}"
                # Safety check to prevent infinite loops (very unlikely)
                if attempt > 10:
                    # If we can't find a unique slug after 10 attempts, use timestamp
                    import time
                    self.event_slug = f"{base_slug}-{int(time.time())}"
                    break
                
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Status(TextChoices):
    symbol: str
    guest_choice: bool    # True if the guest can choose this status
    description: str

    # name =       value,  label,                 symbol,  guest_choice,  description
    NOT_INVITED =  'N',   _('Not invited 🆕'),   '🆕',    False,         _("The guest has not yet been invited to this event")
    INVITED =      'I',   _('Invited 💌'),       '💌',    False,         _("The organizer sent an invitation to this guest, but the guest has not yet responded")
    CONFIRMED =    'C',   _('Confirmed ✅'),     '✅',    True,          _("The guest presence is confirmed")
    MAYBE =        'M',   _('Maybe ❓'),         '❓',    True,          _("The guest is undecided about the invitation")
    DECLINED =     'D',   _("Declined ❌"),      '❌',    True,          _("The guest declined the invitation")
    REJECTED =     'R',   _('Rejected ⛔'),      '⛔',    False,         _("The organizer rejected the guest's request to attend")

    def __str__(self):
        return force_str(self.label)

class Response(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='responses')
    name = models.CharField(max_length=200, verbose_name='Name')
    email = models.EmailField(null=True, blank=True, verbose_name='Email')
    message = models.TextField(null=True, blank=True, verbose_name='Message')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    response_token = models.CharField(max_length=16, unique=True, editable=False, default=generate_token_16)
    is_organizer = models.BooleanField(default=False, verbose_name='Is organizer')
    status = EnumField(Status, verbose_name='Status', default=Status.NOT_INVITED, choices=Status.choices)
    is_waiting_list = models.BooleanField(default=False, verbose_name='Waiting list')
    
    def get_status_choices(self):
        """
        Return appropriate status choices based on whether user is organizer
        """
        if self.is_organizer:
            return [(status.value, status.label) for status in Status]
        else:
            return [(status.value, status.label) for status in Status if status.guest_choice]
            
    @property
    def is_confirmed(self):
        """Helper to check if response is confirmed"""
        return self.status == Status.CONFIRMED and not self.is_waiting_list
        
    @property
    def is_pending_approval(self):
        """Helper to check if response is waiting for organizer approval"""
        return self.status == Status.REQUESTED or self.is_waiting_list
    
    def clean(self):
        # Validate status
        if self.status and self.status not in dict(Status.choices).keys():
            raise ValidationError({'status': _('Invalid status')})
            
        # Print debug info
        print(f"Clean method called - pk: {self.pk}, event: {hasattr(self, 'event')}, status: {self.status}")
            
        # New responses - check waiting list and capacity
        if not self.pk:
            # If event requires approval, automatically put response on waiting list
            if hasattr(self, 'event') and self.event and self.event.waiting_list:
                print(f"Setting to waiting list: {self.event.waiting_list}")
                self.is_waiting_list = True
            # If this is a confirmed response, check if we've reached max attendees
            elif hasattr(self, 'event') and self.event and self.status == Status.CONFIRMED and not self.is_waiting_list:
                # Use the event's confirmed_count property for cleaner code
                if self.event.max_attendees is not None and self.event.is_at_capacity:
                    self.is_waiting_list = True
			
    def save(self, *args, **kwargs):
        if not self.response_token:
            self.response_token = generate_token_16()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
