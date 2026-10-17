package com.fit2081.aaron_34076832.nutritrack.screens

import android.annotation.SuppressLint
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Face
import androidx.compose.material.icons.filled.Favorite
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.ThumbUp
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.BottomAppBar
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CenterAlignedTopAppBar
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fit2081.aaron_34076832.nutritrack.R
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.ui.theme.A1HealthAppTheme
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomBrown
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomGreen
import com.fit2081.aaron_34076832.nutritrack.viewmodels.EditProfileViewModel
import com.fit2081.aaron_34076832.nutritrack.viewmodels.EditProfileViewModelFactory


class EditProfile : ComponentActivity() {
    @SuppressLint("UnusedMaterial3ScaffoldPaddingParameter")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val userId = intent.getStringExtra("user_id") ?: "Unknown ID"

        enableEdgeToEdge()
        setContent {
            A1HealthAppTheme {
                val context = LocalContext.current

                val userPreferencesManager = remember { UserPreferencesManager(context.applicationContext) }
                LaunchedEffect(Unit) {
                    userPreferencesManager.setLastScreenRoute("edit_profile")
                }

                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    bottomBar = {
                        MyBottomBarEdit(context,userId,"Settings")
                    },
                    topBar = { TopAppBarEdit(context, userId) }
                ) {
                    EditDetails(userId, userPreferencesManager)
                }
            }
        }
    }
}


@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TopAppBarEdit(context: Context, userId: String) {

    CenterAlignedTopAppBar(
        colors = TopAppBarDefaults.centerAlignedTopAppBarColors(
            containerColor = CustomBrown,
            titleContentColor = Color.White

        ),
        title = {
            Text(
                "Edit Profile",
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
                fontWeight = FontWeight.Bold
            )
        },
        navigationIcon = {
            IconButton(onClick = {
                val intent = Intent(context, Settings::class.java)
                intent.putExtra("user_id", userId)
                intent.flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
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
fun MyBottomBarEdit(context: Context, userID: String?, currentScreen: String) {
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
                    IconButton(onClick = {
                        val intent = Intent(context, HomeScreen::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Home, contentDescription = "Go Home",
                            tint = if (currentScreen == "Home") CustomBrown else
                                LocalContentColor.current)
                    }
                    Text("Home",
                        fontSize = 11.sp,
                        color = if (currentScreen == "Home") CustomBrown else
                            LocalContentColor.current)
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Top
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, Insights::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Favorite, contentDescription = "Insights",
                            tint = if (currentScreen == "Insights") CustomBrown else
                                LocalContentColor.current)
                    }
                    Text("Insights",
                        fontSize = 11.sp,
                        color = if (currentScreen == "Insights") CustomBrown else
                            LocalContentColor.current)
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Top
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, NutriCoach::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Face, contentDescription = "NutriCoach",
                            tint = if (currentScreen == "NutriCoach") CustomBrown else
                                LocalContentColor.current)
                    }
                    Text("NutriCoach",
                        fontSize = 11.sp,
                        color = if (currentScreen == "NutriCoach") CustomBrown else
                            LocalContentColor.current)
                }

                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Top
                ) {
                    IconButton(onClick = {
                        val intent = Intent(context, Settings::class.java)
                        intent.putExtra("user_id", userID)
                        context.startActivity(intent)
                    }) {
                        Icon(Icons.Filled.Settings, contentDescription = "Settings",
                            tint = if (currentScreen == "Settings") CustomBrown else
                                LocalContentColor.current
                        )
                    }
                    Text(
                        "Settings",
                        fontSize = 11.sp,
                        color = if (currentScreen == "Settings") CustomBrown else
                            LocalContentColor.current
                    )
                }
            }
        }
    )
}

@SuppressLint("ContextCastToActivity")
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditDetails(userId: String, userPreferencesManager: UserPreferencesManager) {
    val context = LocalContext.current
    val activity = LocalContext.current as ComponentActivity
    val application = context.applicationContext as Application

    val viewModel: EditProfileViewModel = viewModel(
        factory = EditProfileViewModelFactory(application)
    )

    val selectedUserId by viewModel.selectedUserId.collectAsState()
    val selectedUserSex by viewModel.selectedUserSex.observeAsState(null)


    val allPatients by viewModel.allPatients.observeAsState(emptyList())

    val phoneInput by viewModel.phoneInput.collectAsState()
    val nameInput by viewModel.nameInput.collectAsState()
    val showOldPasswordDialog by viewModel.showOldPasswordDialog.collectAsState()
    val showNewPasswordDialog by viewModel.showNewPasswordDialog.collectAsState()
    val oldPasswordInput by viewModel.oldPasswordInput.collectAsState()
    val newPasswordInput by viewModel.newPasswordInput.collectAsState()
    val confirmNewPasswordInput by viewModel.confirmNewPasswordInput.collectAsState()
    val oldPasswordVisible by viewModel.oldPasswordVisible.collectAsState()
    val newPasswordVisible by viewModel.newPasswordVisible.collectAsState()
    val confirmNewPasswordVisible by viewModel.confirmNewPasswordVisible.collectAsState()
    val passwordTriesRemaining by viewModel.passwordTriesRemaining.collectAsState()
    val newPasswordValid by viewModel.newPasswordValid.collectAsState()
    val confirmNewPasswordValid by viewModel.confirmNewPasswordValid.collectAsState()
    val newPasswordErrorMessage by viewModel.newPasswordErrorMessage.collectAsState()
    val confirmNewPasswordErrorMessage by viewModel.confirmNewPasswordErrorMessage.collectAsState()
    val expanded by viewModel.expandedDropdown.collectAsState()
    val isPhoneValid by viewModel.isPhoneValid.collectAsState()
    val showPhoneMismatchDialog by viewModel.showPhoneMismatchDialog.collectAsState()
    val nameValid by viewModel.nameValid.collectAsState()
    val showNameErrorDialog by viewModel.showNameErrorDialog.collectAsState()
    val showInvalidDetails by viewModel.showInvalidDetails.collectAsState()
    val showUpdateSuccessDialog by viewModel.showUpdateSuccessDialog.collectAsState()
    val showPasswordResetLockedDialog by viewModel.showPasswordResetLockedDialog.collectAsState()
    val isFormValid by viewModel.isFormValid.collectAsState()

    val scrollState = rememberScrollState()

    LaunchedEffect(userId) {
        viewModel.setInitialUserId(userId)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Top
    ) {

        Spacer(modifier = Modifier.height(100.dp))

        Image(
            painter = painterResource(id = R.drawable.edit),
            contentDescription = "Edit Profile Image",
            modifier = Modifier
                .size(300.dp)
                .fillMaxWidth(0.5f)
                .align(Alignment.CenterHorizontally)
        )

        Text(
            text = "Edit details",
            fontSize = 32.sp,
            fontWeight = FontWeight.Bold,
            style = MaterialTheme.typography.titleLarge,
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 8.dp),
        )

        HorizontalDivider(
            thickness = 1.dp,
            color = Color.LightGray,
            modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
        )
        ExposedDropdownMenuBox(
            expanded = expanded,
            onExpandedChange = { viewModel.toggleDropdown(!expanded) },
            modifier = Modifier.fillMaxWidth()
        ) {
            OutlinedTextField(
                value = selectedUserId,
                onValueChange = {},
                label = { Text("User ID*") },
                readOnly = true,
                trailingIcon = {
                    ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded)
                },
                modifier = Modifier.menuAnchor()
            )

            ExposedDropdownMenu(
                expanded = expanded,
                onDismissRequest = { viewModel.toggleDropdown(false) }
            ) {
                allPatients.filter { it.isRegistered }.map { it.userID }
                    .forEach { registeredUserId ->
                        DropdownMenuItem(
                            text = { Text(registeredUserId) },
                            onClick = {
                                viewModel.onUserIdSelected(registeredUserId)
                            }
                        )
                    }
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = phoneInput,
            onValueChange = { viewModel.onPhoneInputChange(it) },
            label = { Text("Phone*") },
            trailingIcon = {
                IconButton(onClick = { viewModel.validatePhoneNumber(context) }) {
                    Icon(
                        imageVector = if (isPhoneValid) Icons.Default.ThumbUp else Icons.Default.Check,
                        contentDescription = "Verify Phone"
                    )
                }
            },
            modifier = Modifier.fillMaxWidth(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone)
        )

        if (showPhoneMismatchDialog) {
            AlertDialog(
                onDismissRequest = { viewModel.dismissPhoneMismatchDialog() },
                title = { Text("Validation Failed") },
                text = { Text("Please enter a valid phone number (8-15 digits).") },
                confirmButton = {
                    Button(onClick = { viewModel.dismissPhoneMismatchDialog() }) {
                        Text("OK")
                    }
                }
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = nameInput,
            onValueChange = { viewModel.onNameInputChange(it) },
            label = { Text("Name*") },
            trailingIcon = {
                IconButton(onClick = { viewModel.validateName() }) {
                    Icon(
                        imageVector = if (nameValid) Icons.Default.ThumbUp else Icons.Default.Check,
                        contentDescription = "Validate name"
                    )
                }
            },
            modifier = Modifier.fillMaxWidth()
        )

        if (showNameErrorDialog) {
            AlertDialog(
                onDismissRequest = { viewModel.dismissNameErrorDialog() },
                title = { Text("Error: Invalid Name") },
                text = { Text("Only letters and spaces for name.") },
                confirmButton = {
                    Button(onClick = { viewModel.dismissNameErrorDialog() }) {
                        Text("OK")
                    }
                }
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        GenderDisplayBox(gender = selectedUserSex)

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            value = "",
            onValueChange = {},
            label = { Text("Password") },
            readOnly = true,
            visualTransformation = PasswordVisualTransformation(),
            trailingIcon = {
                IconButton(onClick = { viewModel.showOldPasswordDialog() }) {
                    Icon(
                        imageVector = Icons.Default.Edit,
                        contentDescription = "Edit Password"
                    )
                }
            },
            modifier = Modifier.fillMaxWidth()
        )

        if (showOldPasswordDialog) {
            AlertDialog(
                onDismissRequest = { viewModel.dismissOldPasswordDialog() },
                title = { Text("Verify Old Password") },
                text = {
                    Column {
                        OutlinedTextField(
                            value = oldPasswordInput,
                            onValueChange = { viewModel.onOldPasswordInputChange(it) },
                            label = { Text("Old Password") },
                            visualTransformation = if (oldPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                            trailingIcon = {
                                IconButton(onClick = { viewModel.toggleOldPasswordVisibility() }) {
                                    Icon(
                                        imageVector = if (oldPasswordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                                        contentDescription = "Toggle old password visibility"
                                    )
                                }
                            },
                            modifier = Modifier.fillMaxWidth()
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Tries remaining: $passwordTriesRemaining", color = Color.Red)
                    }
                },
                confirmButton = {
                    Button(onClick = { viewModel.verifyOldPassword(context) }) {
                        Text("Continue")
                    }
                },
                dismissButton = {
                    Button(onClick = { viewModel.dismissOldPasswordDialog() }) {
                        Text("Back")
                    }
                }
            )
        }

        if (showNewPasswordDialog) {
            AlertDialog(
                onDismissRequest = { viewModel.dismissNewPasswordDialog() },
                title = { Text("Enter New Password") },
                text = {
                    Column {
                        OutlinedTextField(
                            value = newPasswordInput,
                            onValueChange = { viewModel.onNewPasswordInputChange(it) },
                            label = { Text("New Password*") },
                            visualTransformation = if (newPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                            trailingIcon = {
                                Row {
                                    IconButton(onClick = { viewModel.toggleNewPasswordVisibility() }) {
                                        Icon(
                                            imageVector = if (newPasswordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                                            contentDescription = "Toggle new password visibility"
                                        )
                                    }
                                    IconButton(onClick = { viewModel.validateNewPassword() }) {
                                        Icon(
                                            imageVector = if (newPasswordValid) Icons.Default.ThumbUp else Icons.Default.Check,
                                            contentDescription = "Validate new password"
                                        )
                                    }
                                }
                            },
                            modifier = Modifier.fillMaxWidth()
                        )
                        if (!newPasswordValid && newPasswordInput.isNotBlank()) {
                            Text(newPasswordErrorMessage, color = Color.Red, fontSize = 12.sp)
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        OutlinedTextField(
                            value = confirmNewPasswordInput,
                            onValueChange = { viewModel.onConfirmNewPasswordInputChange(it) },
                            label = { Text("Confirm New Password*") },
                            visualTransformation = if (confirmNewPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                            trailingIcon = {
                                Row {
                                    IconButton(onClick = { viewModel.toggleConfirmNewPasswordVisibility() }) {
                                        Icon(
                                            imageVector = if (confirmNewPasswordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                                            contentDescription = "Toggle confirm new password visibility"
                                        )
                                    }
                                    IconButton(onClick = { viewModel.validateConfirmNewPassword() }) {
                                        Icon(
                                            imageVector = if (confirmNewPasswordValid) Icons.Default.ThumbUp else Icons.Default.Check,
                                            contentDescription = "Validate confirm new password"
                                        )
                                    }
                                }
                            },
                            modifier = Modifier.fillMaxWidth()
                        )
                        if (!confirmNewPasswordValid && confirmNewPasswordInput.isNotBlank()) {
                            Text(confirmNewPasswordErrorMessage, color = Color.Red, fontSize = 12.sp)
                        }
                    }
                },
                confirmButton = {
                    Button(
                        onClick = { viewModel.saveNewPassword(userPreferencesManager) },
                        enabled = newPasswordValid && confirmNewPasswordValid && newPasswordInput.isNotBlank()
                    ) {
                        Text("Save New Password")
                    }
                },
                dismissButton = {
                    Button(onClick = { viewModel.dismissNewPasswordDialog() }) {
                        Text("Close")
                    }
                }
            )
        }

        if (showPasswordResetLockedDialog) {
            AlertDialog(
                onDismissRequest = { },
                title = { Text("Error: Invalid Password") },
                text = { Text("You have been logged out. Please click on Forgot Password if you wish to reset your password.") },
                confirmButton = {
                    Button(onClick = {
                        viewModel.dismissPasswordResetLockedDialog(context, userPreferencesManager, activity)
                        val intent = Intent(context, LogInPage::class.java)
                        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                        context.startActivity(intent)
                        activity.finish()
                    }) {
                        Text("OK")
                    }
                }
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        Button(
            colors = ButtonDefaults.buttonColors(containerColor = CustomGreen),
            onClick = { viewModel.updateProfile(userPreferencesManager) },
            modifier = Modifier.fillMaxWidth(),
            enabled = selectedUserId.isNotBlank() && isFormValid
        ) {
            Text("Update Profile")
        }

        Spacer(modifier = Modifier.height(150.dp))

        if (showInvalidDetails) {
            AlertDialog(
                onDismissRequest = { viewModel.dismissInvalidDetailsDialog() },
                title = { Text("Error: Invalid Details.") },
                text = { Text("Please ensure all required fields are valid and verified.") },
                confirmButton = {
                    Button(onClick = { viewModel.dismissInvalidDetailsDialog() }) {
                        Text("OK")
                    }
                }
            )
        }

        if (showUpdateSuccessDialog) {
            AlertDialog(
                onDismissRequest = { },
                title = { Text("Profile Updated!") },
                text = { Text("Your details have been successfully updated.") },
                confirmButton = {
                    Button(onClick = {
                        viewModel.dismissUpdateSuccessDialog()
                        val intent = Intent(context, Settings::class.java)
                        intent.putExtra("user_id", selectedUserId)
                        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                        context.startActivity(intent)
                        activity.finish()

                    }) {
                        Text("OK")
                    }
                }
            )
        }
    }
}