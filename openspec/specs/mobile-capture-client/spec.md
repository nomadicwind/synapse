# Capability: Mobile Capture Client

## Purpose
The React Native application exposes the user-facing capture workflow. It guides users from the home screen into the capture form, lets them pick source types, performs client-side validation, and provides immediate feedback while the backend request is simulated locally.

## Requirements
### Requirement: Navigate users into capture flows
Primary entry points MUST route users from marketing screens into the capture experience.

#### Scenario: Home screen launches capture screen
- **GIVEN** the app loads `HomeScreen`
- **WHEN** the user presses “Start Capturing Content”
- **THEN** the navigation stack pushes the `Capture` screen

#### Scenario: Explore screen links to capture
- **GIVEN** the user is on `ExploreScreen`
- **WHEN** they press “📸 Capture Content”
- **THEN** navigation pushes the `Capture` screen

### Requirement: Let users choose capture source types
The capture form MUST expose each supported source type and reflect the active selection visually.

#### Scenario: Source type buttons update selected state
- **GIVEN** the capture screen is visible
- **WHEN** the user presses “Video”, “Audio”, or “Voicememo”
- **THEN** the component updates `sourceType` accordingly and applies the selected styling to the pressed button

### Requirement: Validate URL input before submission
Client-side validation MUST prevent obviously bad submissions and surface helpful inline guidance.

#### Scenario: Empty URL produces inline error
- **GIVEN** `sourceType` is `webpage`, `video`, or `audio`
- **WHEN** the user presses “Capture” with an empty text field
- **THEN** the screen shows “Please enter a URL” and keeps the request from running

#### Scenario: Malformed URL shows correction hint
- **GIVEN** the user enters `invalid-url` and presses “Capture”
- **WHEN** URL parsing fails
- **THEN** the screen displays “Please enter a valid URL (e.g., https://example.com)” and prevents submission

### Requirement: Support voice memo captures without URLs
Voice memo mode SHALL hide URL inputs and SHALL NOT require link validation.

#### Scenario: Voicememo mode omits URL field
- **GIVEN** the user selects the “Voicememo” source type
- **WHEN** the screen re-renders
- **THEN** the URL TextInput disappears and pressing “Capture” skips URL validation

### Requirement: Provide immediate capture feedback
Submitting the form MUST give the user success or failure messaging while the backend call is simulated.

#### Scenario: Successful capture shows alert
- **GIVEN** the user submits a valid capture
- **WHEN** the simulated two-second API delay finishes
- **THEN** the app shows a success `Alert`, clears the URL field, and re-enables the “Capture” button

#### Scenario: Capture failures surface an error alert
- **GIVEN** the simulated request throws an error
- **WHEN** the handler catches it
- **THEN** the screen sets the error message, raises an error `Alert`, and keeps the user on the capture form for correction

### Requirement: Integrate with Android Share Sheet
The app MUST register as a share target so users can send URLs directly into the capture flow.

#### Scenario: Shared URL launches capture screen
- **GIVEN** the Synapse app is registered with the Android Share Sheet
- **WHEN** a user shares a URL from another app and selects Synapse
- **THEN** Synapse opens the capture screen with the URL pre-populated and focuses the source type selector

### Requirement: Record voice memos in-app
The app MUST allow users to capture voice memos directly without leaving the capture experience.

#### Scenario: Voice memo recording completes capture
- **GIVEN** the user selects the “Voicememo” source type
- **WHEN** they press “Record” and stop the recording
- **THEN** the app stores the audio clip locally, shows confirmation that it will be sent on submission, and includes the clip in the subsequent capture request payload
