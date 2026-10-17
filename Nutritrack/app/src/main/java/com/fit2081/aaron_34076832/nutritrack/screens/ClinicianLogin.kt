package com.fit2081.aaron_34076832.nutritrack.screens

import android.app.Application
import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Face
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.BottomAppBar
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fit2081.aaron_34076832.nutritrack.R
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.ui.theme.A1HealthAppTheme
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomBrown
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomGreen
import com.fit2081.aaron_34076832.nutritrack.viewmodels.ClinicianLoginViewModel
import com.fit2081.aaron_34076832.nutritrack.viewmodels.ClinicianLoginViewModelFactory

class ClinicianLogIn : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            A1HealthAppTheme {
                val userId = intent.getStringExtra("user_id")
                val context = LocalContext.current

                val userPreferencesManager = remember { UserPreferencesManager(context.applicationContext) }
                LaunchedEffect(Unit) {
                    userPreferencesManager.setLastScreenRoute("clinician_login")
                }

                ClinicianLoginScreen(context, userId = userId, userPreferencesManager = userPreferencesManager)
            }
        }
    }

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun TopAppBarClinicianLogin(userID: String?) {
        val context = LocalContext.current
        CenterAlignedTopAppBar(
            colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
                containerColor = CustomBrown,
                titleContentColor = Color.White
            ),
            title = {
                Text(
                    "Clinician Login",
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    fontWeight = FontWeight.Bold
                )
            },
            navigationIcon = {
                IconButton(onClick = {
                    val intent = Intent(context, Settings::class.java)
                    intent.putExtra("user_id", userID)
                    intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_NEW_TASK)
                    context.startActivity(intent)
                    (context as? ComponentActivity)?.finish()
                }) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "Back to Settings",
                        tint = Color.White
                    )
                }
            }
        )
    }

    @Composable
    fun ClinicianLoginScreen(context: Context, modifier: Modifier = Modifier, userId: String?, userPreferencesManager: UserPreferencesManager) {
        val application = context.applicationContext as Application
        val viewModel: ClinicianLoginViewModel = viewModel(
            factory = ClinicianLoginViewModelFactory(application)
        )

        val passwordInput by viewModel.passwordInput.collectAsState()
        val remainingAttempts by viewModel.remainingAttempts.collectAsState()
        val showAlertDialog by viewModel.showAlertDialog.collectAsState()
        val dialogMessage by viewModel.dialogMessage.collectAsState()
        val dialogTitle by viewModel.dialogTitle.collectAsState()
        val navigateToDashboard by viewModel.navigateToDashboard.collectAsState()
        val navigateToSettings by viewModel.navigateToSettings.collectAsState()

        LaunchedEffect(navigateToDashboard) {
            navigateToDashboard?.let { id ->
                val intent = Intent(context, ClinicianDashboard::class.java)
                intent.putExtra("user_id", id)
                context.startActivity(intent)
                (context as? ComponentActivity)?.finish()
                viewModel.navigationToDashboardHandled()
            }
        }

        LaunchedEffect(navigateToSettings) {
            navigateToSettings?.let { id ->
                val intent = Intent(context, Settings::class.java)
                intent.putExtra("user_id", id)
                context.startActivity(intent)
                (context as? ComponentActivity)?.finish()
                viewModel.navigationToSettingsHandled()
            }
        }

        Scaffold(
            modifier = Modifier.fillMaxSize(),
            topBar = { TopAppBarClinicianLogin(userId) },
            bottomBar = { MyBottomBarClinicianLogin(context, userId, "Settings") }
        ) { innerPadding ->
            Column(
                modifier = modifier
                    .padding(innerPadding)
                    .fillMaxSize()
                    .padding(horizontal = 24.dp),
                verticalArrangement = Arrangement.Top,
                horizontalAlignment = Alignment.CenterHorizontally
            ) {

                Spacer(modifier = Modifier.height(30.dp))

                Image(
                    painter = painterResource(id = R.drawable.clinician),
                    contentDescription = "Clinician Log In image of Aaron",
                    modifier = Modifier.size(300.dp).fillMaxWidth(0.5f)
                        .align(Alignment.CenterHorizontally)
                )

                Spacer(modifier = Modifier.height(30.dp))

                Text(
                    text = "Enter Clinician Password",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(bottom = 16.dp)
                )

                TextField(
                    value = passwordInput,
                    onValueChange = { viewModel.onPasswordInputChanged(it) },
                    label = { Text("Password") },
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(16.dp))

                Button(
                    onClick = {
                        viewModel.onLoginClicked(context, userId, userPreferencesManager)
                    },
                    enabled = remainingAttempts > 0,
                    colors = ButtonDefaults.buttonColors(containerColor = CustomGreen),
                    shape = RoundedCornerShape(12.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(text = "Log In")
                }

                if (showAlertDialog) {
                    AlertDialog(
                        onDismissRequest = {
                            if (remainingAttempts > 0) {
                                viewModel.onAlertDialogDismissed(context, userId, userPreferencesManager)
                            }
                        },
                        title = { Text(dialogTitle) },
                        text = { Text(dialogMessage) },
                        confirmButton = {
                            Button(onClick = {
                                viewModel.onAlertDialogDismissed(context, userId, userPreferencesManager)
                            }) {
                                Text("Understood")
                            }
                        }
                    )
                }
            }
        }
    }


    @Composable
    fun MyBottomBarClinicianLogin(context: Context, userID: String?, currentScreen: String) {
        BottomAppBar(
            modifier = Modifier.height(100.dp),
            content = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Top
                    ) {
                        val isActive = currentScreen == "Home"
                        IconButton(
                            onClick = {
                                if (!isActive) {
                                    val intent = Intent(context, HomeScreen::class.java)
                                    intent.putExtra("user_id", userID)
                                    intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                    context.startActivity(intent)
                                }
                            },
                            enabled = !isActive
                        ) {
                            Icon(
                                Icons.Filled.Home, contentDescription = "Go Home",
                                tint = if (isActive) CustomBrown else LocalContentColor.current
                            )
                        }
                        Text(
                            "Home",
                            fontSize = 11.sp,
                            color = if (isActive) CustomBrown else LocalContentColor.current
                        )
                    }

                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Top
                    ) {
                        val isActive = currentScreen == "Insights"
                        IconButton(
                            onClick = {
                                if (!isActive) {
                                    val intent = Intent(context, Insights::class.java)
                                    intent.putExtra("user_id", userID)
                                    intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                    context.startActivity(intent)
                                }
                            },
                            enabled = !isActive
                        ) {
                            Icon(
                                Icons.Filled.Favorite, contentDescription = "Insights",
                                tint = if (isActive) CustomBrown else LocalContentColor.current
                            )
                        }
                        Text(
                            "Insights",
                            fontSize = 11.sp,
                            color = if (isActive) CustomBrown else LocalContentColor.current
                        )
                    }

                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Top
                    ) {
                        val isActive = currentScreen == "NutriCoach"
                        IconButton(
                            onClick = {
                                if (!isActive) {
                                    val intent = Intent(context, NutriCoach::class.java)
                                    intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                    context.startActivity(intent)
                                }
                            },
                            enabled = !isActive
                        ) {
                            Icon(
                                Icons.Filled.Face, contentDescription = "NutriCoach",
                                tint = if (isActive) CustomBrown else LocalContentColor.current
                            )
                        }
                        Text(
                            "NutriCoach",
                            fontSize = 11.sp,
                            color = if (isActive) CustomBrown else LocalContentColor.current
                        )
                    }

                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Top
                    ) {
                        val isActive = currentScreen == "Settings"
                        IconButton(
                            onClick = {
                                if (!isActive) {
                                    val intent = Intent(context, Settings::class.java)
                                    intent.putExtra("user_id", userID)
                                    intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                                    context.startActivity(intent)
                                }
                            },
                            enabled = !isActive
                        ) {
                            Icon(
                                Icons.Filled.Settings, contentDescription = "Settings",
                                tint = if (isActive) CustomBrown else LocalContentColor.current
                            )
                        }
                        Text(
                            "Settings",
                            fontSize = 11.sp,
                            color = if (isActive) CustomBrown else LocalContentColor.current
                        )
                    }
                }
            }
        )
    }
}