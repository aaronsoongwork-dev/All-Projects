package com.fit2081.aaron_34076832.nutritrack.screens

import android.annotation.SuppressLint
import android.app.Application
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.Badge
import androidx.compose.material.icons.filled.Cake
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material.icons.filled.Transgender
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientViewModel
import com.fit2081.aaron_34076832.nutritrack.ui.theme.A1HealthAppTheme
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomBrown
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomGreen
import com.fit2081.aaron_34076832.nutritrack.viewmodels.SettingsViewModel

@Composable
fun SettingItem(
    icon: ImageVector,
    label: String,
    value: String?,
    onClick: (() -> Unit)? = null
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = onClick != null) { onClick?.invoke() }
            .padding(vertical = 12.dp, horizontal = 16.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Icon(
                imageVector = icon,
                contentDescription = label,
                modifier = Modifier.size(26.dp),
                tint = Color.Black
            )
            Spacer(modifier = Modifier.width(16.dp))
            Column {
                Text(
                    text = label,
                    fontSize = 16.sp,
                    color = Color.Black
                )
                Text(
                    text = value ?: " ",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Normal,
                    color = Color.Black
                )
            }
        }
    }
}


@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TopAppBarSettings() {

    CenterAlignedTopAppBar(
        colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
            containerColor = CustomBrown,
            titleContentColor = Color.White

        ),
        title = {
            Text(
                text = "Settings",
                fontWeight = FontWeight.Bold,
                textAlign = TextAlign.Center,
                fontSize = 24.sp,
                modifier = Modifier
                    .padding(bottom = 2.dp)
                    .fillMaxWidth()
            )
        }
    )
}


class Settings : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val userId = intent.getStringExtra("user_id")

        enableEdgeToEdge()
        setContent {
            A1HealthAppTheme {
                val context = LocalContext.current

                val userPreferencesManager = remember { UserPreferencesManager(context.applicationContext) }
                LaunchedEffect(Unit) {
                    userPreferencesManager.setLastScreenRoute("settings")
                }

                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    SettingsScreen(Modifier.padding(innerPadding), userId = userId, context)
                }
            }
        }
    }
}

@SuppressLint("ContextCastToActivity")
@Composable
fun SettingsScreen(modifier: Modifier = Modifier, userId: String?, context: Context) {
    val patientViewModel: PatientViewModel = viewModel(
        factory = PatientViewModel.PatientsViewModelFactory(context.applicationContext as Application)
    )

    val settingsViewModel: SettingsViewModel = viewModel(
        factory = SettingsViewModel.SettingsViewModelFactory(context.applicationContext as Application)
    )

    var showLogoutDialog by remember { mutableStateOf(false) }
    var showClinicianDialog by remember { mutableStateOf(false) }

    val userName by patientViewModel.selectedUserName.observeAsState("Loading...")
    val userAge by patientViewModel.selectedUserAge.observeAsState(null)
    val userSex by patientViewModel.selectedUserSex.observeAsState(null)
    val userPhoneNum by patientViewModel.selectedUserPhoneNum.observeAsState("Loading...")

    LaunchedEffect(userId) {
        if (!userId.isNullOrBlank()) {
            patientViewModel.setSelectedUserId(userId)
        }
    }

    Scaffold(modifier = Modifier.fillMaxSize(),
        bottomBar = {
            MyBottomBarHome(context, userId, "Settings")
        },
        topBar = { TopAppBarSettings() }

    ) { innerPadding ->
        Column(
            modifier = Modifier
                .padding(innerPadding)
                .fillMaxHeight()
                .padding(horizontal = 24.dp),
            verticalArrangement = Arrangement.Top,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {

            Spacer(modifier = Modifier.height(24.dp))

            Spacer(modifier = Modifier.height(24.dp))

            Column(
                modifier = Modifier.padding(start = 16.dp, bottom = 8.dp),
                horizontalAlignment = Alignment.Start
            ) {
                Text(
                    text = "ACCOUNT",
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Left,
                    fontSize = 18.sp,
                    color = Color.Gray,
                )

                Spacer(modifier = Modifier.height(10.dp))

                val patientDetails = listOf(
                    Triple(Icons.Default.Person, "Name", userName),
                    Triple(Icons.Default.Phone, "Phone", userPhoneNum),
                    Triple(Icons.Default.Badge, "User ID", userId),
                    Triple(Icons.Default.Cake, "Age", userAge?.toString()),
                    Triple(Icons.Default.Transgender, "Gender", userSex?.name)
                )

                Column(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    patientDetails.forEachIndexed { index, (icon, label, value) ->
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(
                                horizontalAlignment = Alignment.Start,
                                modifier = Modifier.width(36.dp)
                            ) {
                                Icon(
                                    imageVector = icon,
                                    contentDescription = "$label Icon",
                                    modifier = Modifier.size(26.dp),
                                    tint = Color.DarkGray
                                )
                            }

                            Column(
                                horizontalAlignment = Alignment.Start,
                                modifier = Modifier.width(100.dp)
                            ) {
                                Text(
                                    text = label,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 16.sp,
                                    color = Color.DarkGray
                                )
                            }

                            Column(
                                horizontalAlignment = Alignment.Start,
                                modifier = Modifier.weight(1f)
                            ) {
                                Text(
                                    text = value ?: "N/A",
                                    fontSize = 16.sp,
                                    color = Color.Black,
                                )
                            }

                            if (label == "Gender") {
                                Button(
                                    shape = RoundedCornerShape(12.dp),
                                    onClick = {
                                        if (!userId.isNullOrBlank()) {
                                            val intent = Intent(context, EditProfile::class.java)
                                            intent.putExtra("user_id", userId)
                                            Toast.makeText(
                                                context,
                                                "Navigating to Edit Profile!",
                                                Toast.LENGTH_SHORT
                                            ).show()
                                            context.startActivity(intent)
                                            (context as? ComponentActivity)?.finish()
                                        } else {
                                            Toast.makeText(
                                                context,
                                                "No user selected to edit.",
                                                Toast.LENGTH_SHORT
                                            ).show()
                                        }
                                    },
                                    colors = ButtonDefaults.buttonColors(containerColor = CustomGreen),
                                    modifier = Modifier.padding(start = 16.dp)
                                ) {
                                    Text(text = "✏  Edit")
                                }
                            }
                        }
                        Spacer(modifier = Modifier.height(10.dp))
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                HorizontalDivider(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 16.dp),
                    thickness = 1.dp,
                    color = Color.LightGray
                )

            }

            Column(
                modifier = Modifier.fillMaxWidth(),
                horizontalAlignment = Alignment.Start
            ) {
                Text(
                    text = "OTHER SETTINGS",
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Left,
                    fontSize = 18.sp,
                    color = Color.Gray,
                    modifier = Modifier.padding(start = 18.dp, bottom = 8.dp)
                )

                SettingItem(
                    icon = Icons.AutoMirrored.Filled.KeyboardArrowRight,
                    label = "Logout",
                    value = "Press to Log out of the account",
                    onClick = {
                        showLogoutDialog = true
                    }
                )

                SettingItem(
                    icon = Icons.AutoMirrored.Filled.KeyboardArrowRight,
                    label = "Clinician Login",
                    value = "Press for Clinicians screen.",
                    onClick = {
                        showClinicianDialog = true
                    }
                )
            }
        }

        if (showLogoutDialog) {
            AlertDialog(
                onDismissRequest = {
                    showLogoutDialog = false
                },
                title = { Text("Confirm Logout") },
                text = { Text("Do you confirm you want to log out?") },
                confirmButton = {
                    Button(onClick = {
                        settingsViewModel.logoutUser()

                        Toast.makeText(context, "Logged out!", Toast.LENGTH_SHORT).show()

                        val intent = Intent(context, LogInPage::class.java)
                        intent.flags =
                            Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                        context.startActivity(intent)
                        (context as? ComponentActivity)?.finish()

                        showLogoutDialog = false
                    }) {
                        Text("Yes, Log Out")
                    }
                },
                dismissButton = {
                    Button(onClick = {
                        showLogoutDialog = false
                    }) {
                        Text("Cancel")
                    }
                }
            )
        }

        if (showClinicianDialog) {
            AlertDialog(
                onDismissRequest = {
                    showClinicianDialog = false
                },
                title = { Text("Confirm Proceed?") },
                text = { Text("Are you a Professional Clinician?") },
                confirmButton = {
                    Button(onClick = {
                        Toast.makeText(context, "Logging in!", Toast.LENGTH_SHORT).show()

                        val intent = Intent(context, ClinicianLogIn::class.java)
                        intent.putExtra("user_id", userId)
                        context.startActivity(intent)

                        showClinicianDialog = false
                    }) {
                        Text("Yes, I am")
                    }
                },
                dismissButton = {
                    Button(onClick = {
                        showClinicianDialog = false
                    }) {
                        Text("Cancel")
                    }
                }
            )
        }
    }
}