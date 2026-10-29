# Nutritrack

A nutrition tracking Android app built with Kotlin and Jetpack Compose. Nutritrack gives users a **Food Quality Score** based on their dietary intake, breaks that score down by food group, and offers AI-generated motivational tips to help them eat better. A separate clinician view summarises patient data and generates AI insights.

Built for **FIT2081 (Mobile Application Development)** at Monash University.

## Features

**Accounts and login**
- Log in by selecting a pre-registered User ID and entering a password
- Register by claiming a pre-registered ID (verified against the phone number in the dataset), then setting a name and password
- Forgot password flow: verify identity with phone number, then reset (at least 5 characters and at least 1 number)
- Login state and last visited screen are remembered, so the app reopens where you left off

**Questionnaire**
- Select the food categories you eat (fruits, vegetables, grains, red meat, seafood, poultry, fish, eggs, nuts/seeds)
- Choose one of six personas: Health Devotee, Mindful Eater, Wellness Striver, Balance Seeker, Health Procrastinator, Food Carefree
- Set usual meal, sleep and wake times with time pickers

**Home**
- Shows your overall Food Quality Score out of 100
- Quick link to edit your details, plus an explanation of what the score means

**Insights**
- Per-category scores (vegetables, fruit, grains and cereals, whole grains, meat and alternatives, dairy, water, saturated and unsaturated fats, sodium, sugar and more)
- Share your score with others through the Android share sheet

**NutriCoach**
- Look up fruit nutrition details from the [FruityVice API](https://www.fruityvice.com/)
- Generate short motivational tips with Google Gemini, optionally personalised by motivation type, energy level and extra notes
- View all past tips and delete individual tips or all tips

**Profile and settings**
- Edit name and phone number with input validation
- Change password (verifies the old password first)
- Log out with confirmation

**Clinician mode**
- Password-protected clinician login, reachable from Settings
- Dashboard with average HEIFA scores for male and female patients
- Generate and delete AI-written data insights (gender differences, food group patterns and more) from the patient dataset

## Tech Stack

| Area | Technology |
|------|------------|
| Language | Kotlin 2.0.0 |
| UI | Jetpack Compose, Material 3 |
| Architecture | MVVM with repositories |
| Local database | Room (with KSP) |
| Preferences | Jetpack DataStore |
| Networking | Retrofit with Gson |
| Images | Coil |
| AI | Google Generative AI SDK (`gemini-2.5-flash`) |
| Build | Gradle (Kotlin DSL), AGP 8.8.2 |

**Requirements:** compileSdk 35, minSdk 35 (Android 15 or newer), Java 11.

## Project Structure

```
Nutritrack/
├── app/src/main/
│   ├── AndroidManifest.xml
│   ├── assets/
│   │   └── dataset.csv               # Patient nutrition data, imported into Room on first launch
│   ├── res/                          # Drawables, layouts, values, XML config
│   └── java/com/fit2081/aaron_34076832/nutritrack/
│       ├── MainActivity.kt           # Entry point: restores session or shows welcome screen
│       ├── screens/                  # Compose screens (login, questionnaire, home, insights,
│       │                             #   NutriCoach, settings, edit profile, clinician)
│       ├── viewmodels/               # Screen-level ViewModels
│       ├── data/                     # Room database, DAOs, repositories, entities
│       │   ├── patient/
│       │   ├── foodIntake/
│       │   ├── questionnaire/
│       │   ├── nutriCoachTips/
│       │   ├── persona/ and gender/  # Enums and Room type converters
│       │   └── userPreferences.kt    # DataStore session storage
│       ├── network/                  # Retrofit service for the FruityVice API
│       ├── genAI/                    # Gemini ViewModel for insights and tips
│       └── ui/theme/                 # Colours, typography, theme
├── gradle/libs.versions.toml
└── build.gradle.kts
```

## Getting Started

### Prerequisites

- [Android Studio](https://developer.android.com/studio) (latest stable)
- Android SDK 35 installed via the SDK Manager
- An emulator or device running **Android 15 (API 35) or newer**
- A [Google Gemini API key](https://aistudio.google.com/app/apikey) for the AI features

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/aaronsoongwork-dev/All-Projects.git
   ```
2. Open Android Studio, choose **File → Open**, and select the `Nutritrack` folder.
3. Add your API key to `local.properties` in the `Nutritrack` folder (Android Studio creates this file automatically; this file is git-ignored, so your key stays private):
   ```
   apiKey=YOUR_GEMINI_API_KEY
   ```
4. Let Gradle sync, then run the app on an emulator or device.

> The AI features (NutriCoach tips and clinician insights) need the API key and an internet connection. The rest of the app works offline except the fruit lookup, which also needs internet.

## Dataset

`app/src/main/assets/dataset.csv` contains pre-registered patient records: phone number, user ID, sex, and HEIFA (Healthy Eating Index for Australian Adults) scores for each food group, for both male and female scoring. On first launch (and whenever the database version changes) the app imports it into the Room database so users can register against those IDs.

## Screenshots

*[TODO: add screenshots, e.g. `![Home screen](screenshots/home.png)`]*

## Author

**Aaron Soong Yujien**
GitHub: [@aaronsoongwork-dev](https://github.com/aaronsoongwork-dev)

## License

*[TODO: add a license, or remove this section if not applicable.]*
