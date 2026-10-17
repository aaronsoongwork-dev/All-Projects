package com.fit2081.aaron_34076832.nutritrack

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.ClickableText
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import com.fit2081.aaron_34076832.nutritrack.data.ReadDataViewModel
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntakeRepository
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientRepository
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientViewModel
import com.fit2081.aaron_34076832.nutritrack.screens.ClinicianDashboard
import com.fit2081.aaron_34076832.nutritrack.screens.ClinicianLogIn
import com.fit2081.aaron_34076832.nutritrack.screens.EditProfile
import com.fit2081.aaron_34076832.nutritrack.screens.LogInPage
import com.fit2081.aaron_34076832.nutritrack.screens.NutriCoach
import com.fit2081.aaron_34076832.nutritrack.screens.Settings
import com.fit2081.aaron_34076832.nutritrack.ui.theme.A1HealthAppTheme
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomBrown
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomGreen
import com.fit2081.aaron_34076832.nutritrack.data.ReadDataViewModelFactory
import com.fit2081.aaron_34076832.nutritrack.data.AppDatabase
import com.fit2081.aaron_34076832.nutritrack.screens.HomeScreen
import com.fit2081.aaron_34076832.nutritrack.screens.Insights
import com.fit2081.aaron_34076832.nutritrack.screens.Questionaire
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    private lateinit var userPreferencesManager: UserPreferencesManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        userPreferencesManager = UserPreferencesManager(applicationContext)

        val database = AppDatabase.getDatabase(applicationContext)
        val patientRepository = PatientRepository(applicationContext)
        val foodIntakeRepository = FoodIntakeRepository(applicationContext)

        val viewModelFactory = ReadDataViewModelFactory(patientRepository, foodIntakeRepository)
        val readDataViewModel = ViewModelProvider(this, viewModelFactory)[ReadDataViewModel::class.java]
        readDataViewModel.readAndSaveCsvFromAssets(applicationContext, "dataset.csv")

        val patientViewModelFactory = PatientViewModel.PatientsViewModelFactory(this)
        val patientViewModel = ViewModelProvider(this, patientViewModelFactory)[PatientViewModel::class.java]

        // This ensures the decision happens immediately on app launch
        lifecycleScope.launch {
            val isLoggedIn = userPreferencesManager.isLoggedIn.first()
            if (isLoggedIn) {
                // If logged in, go to the last saved screen
                val lastScreenRoute = userPreferencesManager.lastScreenRoute.first()
                val intent: Intent

                if (!lastScreenRoute.isNullOrEmpty()) {
                    when (lastScreenRoute) {
                        "home_screen" -> intent = Intent(this@MainActivity, HomeScreen::class.java)
                        "questionnaire" -> intent = Intent(this@MainActivity, Questionaire::class.java)
                        "insights" -> intent = Intent(this@MainActivity, Insights::class.java)
                        "nutricoach" -> intent = Intent(this@MainActivity, NutriCoach::class.java)
                        "settings" -> intent = Intent(this@MainActivity, Settings::class.java)
                        "edit_profile" -> intent = Intent(this@MainActivity, EditProfile::class.java)
                        "clinician_login" -> intent = Intent(this@MainActivity, ClinicianLogIn::class.java)
                        "clinician_dashboard" -> intent = Intent(this@MainActivity, ClinicianDashboard::class.java)
                        else -> intent = Intent(this@MainActivity, HomeScreen::class.java)
                    }
                } else {
                    intent = Intent(this@MainActivity, HomeScreen::class.java)
                }

                val currentUserId = userPreferencesManager.currentUserId.first()
                currentUserId?.let {
                    intent.putExtra("user_id", it)
                }

                startActivity(intent)
                finish() // Finish MainActivity so it's not on the back stack
            } else {
                // If logged out, display the LoginScreen (as the initial content)
                setContent {
                    A1HealthAppTheme {
                        Scaffold(
                            modifier = Modifier.fillMaxSize(),
                            bottomBar = { MyBottomBar() }
                        ) { innerPadding ->
                            // When logged out, the user will always see this screen
                            LoginScreen(modifier = Modifier.padding(innerPadding), patientViewModel)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun MyBottomBar() {
    BottomAppBar(
        containerColor = CustomBrown,
        contentColor = Color.White,
        contentPadding = PaddingValues(2.dp)
    ) {
        Text(
            text = "Designed with a lot of ❤️ by \nAaron Soong Yujien (34076832)",
            modifier = Modifier.fillMaxWidth(),
            textAlign = TextAlign.Center,
            fontSize = 16.sp,
            lineHeight = 18.sp,
            color = Color.White
        )
    }
}

@Composable
fun LoginScreen(modifier: Modifier = Modifier, patientViewModel: PatientViewModel) {
    val context = LocalContext.current

    LaunchedEffect(Unit) {
        patientViewModel.getPatientID()
    }

    Surface(
        modifier = modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Image(
                painter = painterResource(id = R.drawable.logo),
                contentDescription = "Logo of Leaf for the App",
                modifier = Modifier.size(300.dp).fillMaxWidth(0.5f)
            )

            Text(
                text = "This app provides general health and nutrition information for " +
                        "educational purposes only. It is not intended as medical advice, " +
                        "diagnosis, or treatment. Always consult a qualified healthcare " +
                        "professional before making any changes to your diet, exercise, or health "
                        + "regimen. Use this app at your own risk. If you’d like to an Accredited" +
                        " Practicing Dietitian (APD), please " + "visit the Monash " +
                        "Nutrition/Dietetics Clinic (discounted rates for students): ",

                fontSize = 14.sp,
                modifier = Modifier
                    .padding(bottom = 2.dp)
                    .fillMaxWidth(0.85f),
                fontStyle = FontStyle.Italic,
                textAlign = TextAlign.Center,
                lineHeight = 20.sp
            )

            val linkText = buildAnnotatedString {
                withStyle(style = SpanStyle(color = MaterialTheme.colorScheme.primary, fontSize = 14.sp)) {
                    append("https://www.monash.edu/medicine/acs/nutrition/clinic/nutrition")
                }
            }

            val uriHandler = LocalUriHandler.current
            ClickableText(
                text = linkText,
                onClick = { uriHandler.openUri(linkText.toString()) },
                modifier = Modifier.padding(horizontal = 16.dp),
                style = MaterialTheme.typography.bodySmall.copy(textAlign = TextAlign.Center)
            )

            Spacer(modifier = Modifier.height(16.dp))

            Button(
                onClick = {
                    context.startActivity(Intent(context, LogInPage::class.java))
                    (context as? ComponentActivity)?.finish()
                },
                colors = ButtonDefaults.buttonColors(containerColor = CustomGreen),
                modifier = Modifier.fillMaxWidth(0.85f),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text("Continue!")
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}