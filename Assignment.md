# Assignment Details - Ticket

This file containts the coding assignment, written in the same format as a "ticket" in a project management tool.

## Event creation form
[x] Change checkbox text from "Require approval for all guests" to "Place all new guests on the waiting list by default"
[x] Change the related tooltip to "If this is enabled, all new guests will be placed on the waiting list first, and only the organiser can approve them later and move them to the confirmed guest list".
[x] Add 5px padding for all multi-line text boxes (in the CSS file)

## Event management form
[x] Add extra space between the header and the form
[x] Reformat the organizer and registration links with the secondary button style, and:
  [x] Change button text to "Copy organizer link" and "Copy registration link" respectively.
  [x] Change the button tooltips to:
    [x] "Copy the secret organizer link to the clipboard. Keep this link private, as it allows full access to the event. Only share it with other organizers."
    [x] "Copy the public registration link to the clipboard. This link can be shared with anyone who wants to register for the event."

## Add new response form (by organizer)
[x] Fix the "On waiting list" checkbox
  [x] Change the label to "Waiting list"
  [x] If the event checkbox "Place all new guests on the waiting list by default" is checked, then this checkbox should be checked by default when the form is opened. Else it should be unchecked by default.
  [x] Add a tooltip to the checkbox: "If this is checked, the guest will be placed on the waiting list. If unchecked, the guest will be confirmed directly."
  
## Responses table
[ ] Always show all 4 groups of responses, with the corresponding toolips:
  [ ] "Confirmed" - "These guests have confirmed their attendance, and they are not on the waiting list."
  [ ] "Waiting list" - "These guests have confirmed their attendance, but they are currently on the waiting list."
  [ ] "Pending" - "These guests have not yet responded or confirmed their attendance."
  [ ] "Not coming" - "These guests have declined the invitation or their request to join has been rejected by the organizer."
[ ] If a group has no records, show a message "No records in this group"
[ ] Every time the status of a guest is changed or the waiting list checkbox is toggled:
  [  ] the record should be updated accordingly using HTMX or via a page reload (whichever is the easiest to code)
  [  ] if this change results in the record being moved to a different group ("Confirmed", "Waiting list", "Pending" or "Not coming"), the record should be moved to the correct group in the table.
[ ] Change the button to toggle the waiting status to a checkbox in a "Waiting list" column, with a tooltip "If checked, the guest is on the waiting list. If unchecked, the guest is confirmed directly."
