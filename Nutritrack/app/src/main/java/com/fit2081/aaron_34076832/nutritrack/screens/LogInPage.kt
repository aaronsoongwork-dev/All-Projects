package com.fit2081.aaron_34076832.nutritrack.screens

import android.app.Application
import android.content.Intent
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.ThumbUp
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.livedata.observeAsState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.*
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.fit2081.a1healthapp.data.Gender.Gender
import com.fit2081.aaron_34076832.nutritrack.ui.theme.A1HealthAppTheme
import com.fit2081.aaron_34076832.nutritrack.ui.theme.CustomGreen
import androidx.lifecycle.viewmodel.compose.viewModel
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientRepository
import com.fit2081.aaron_34076832.nutritrack.data.questionnaire.QuestionnaireRepository
import com.fit2081.aaron_34076832.nutritrack.data.AuthManager
import androidx.compose.material.icons.filled.Info
import androidx.compose.foundation.background
import com.fit2081.aaron_34076832.nutritrack.R
import com.fit2081.aaron_34076832.nutritrack.viewmodels.LoginRegisterViewModel


class LogInPage : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            A1HealthAppTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize()
                ) { innerPadding ->
                    val application = LocalContext.current.applicationContext as Application
                    val patientRepository = PatientRepository(application)
                    val questionnaireRepository = QuestionnaireRepository(application)
                    val authManager = AuthManager(patientRepository)

                    val loginRegisterViewModel: LoginRegisterViewModel = viewModel(
                        factory = LoginRegisterViewModel.LoginRegisterViewModelFactory(application, patientRepository, questionnaireRepository, authManager)
                    )
                    MainActivity(Modifier.padding(innerPadding), loginRegisterViewModel)
                }
            }
        }
    }

    @Composable
    fun MainActivity(modifier: Modifier = Modifier, viewModel: LoginRegisterViewModel) {
        val isLoginScreen by viewModel.isLoginScreen.observeAsState(true)

        Column(
            modifier = modifier
                .fillMaxSize()
                .padding(10.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Row(modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = { if (!isLoginScreen) viewModel.toggleLoginRegisterScreen() },
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isLoginScreen) Color(0xFF795548) else Color.LightGray,
                        contentColor = Color.White
                    )
                ) {
                    Text("Login")
                }
                Spacer(modifier = Modifier.width(8.dp))
                Button(
                    onClick = { if (isLoginScreen) viewModel.toggleLoginRegisterScreen() },
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (!isLoginScreen) Color(0xFF795548) else Color.LightGray,
                        contentColor = Color.White
                    )
                ) {
                    Text("Register")
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            HorizontalDivider(
                thickness = 3.dp,
                color = Color.LightGray,
                modifier = Modifier.fillMaxWidth()
            )

            if (isLoginScreen) {
                LogInContent(viewModel = viewModel)
            } else {
                RegisterForm(viewModel = viewModel) {
                    viewModel.toggleLoginRegisterScreen()
                }
            }
        }
    }

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun LogInContent(viewModel: LoginRegisterViewModel) {
        val context = LocalContext.current

        val selectedUserId by viewModel.loginSelectedUserId.observeAsState("")
        val password by viewModel.loginPassword.observeAsState("")
        val passwordVisible by viewModel.loginPasswordVisible.observeAsState(false)
        val showLoginErrorDialog by viewModel.showLoginErrorDialog.observeAsState(false)
        val loginDialogMessage by viewModel.loginDialogMessage.observeAsState("")
        val loginAttemptSuccess by viewModel.loginAttemptSuccess.observeAsState(null)

        val allPatients by viewModel.allPatients.observeAsState(emptyList())
        val userIds = remember(allPatients) { allPatients.map { it.userID } }
        var expanded by remember { mutableStateOf(false) }

        val navigateToQuestionnaire by viewModel.navigateToQuestionnaire.observeAsState(null)
        val navigateToHome by viewModel.navigateToHome.observeAsState(null)

        val showForgotPasswordVerifyDialog by viewModel.showForgotPasswordVerifyDialog.observeAsState(false)
        val showForgotPasswordResetDialog by viewModel.showForgotPasswordResetDialog.observeAsState(false)
        val forgotPasswordSelectedUserId by viewModel.forgotPasswordSelectedUserId.observeAsState("")
        val forgotPasswordPhoneNumber by viewModel.forgotPasswordPhoneNumber.observeAsState("")
        val forgotPasswordNewPassword by viewModel.forgotPasswordNewPassword.observeAsState("")
        val forgotPasswordConfirmNewPassword by viewModel.forgotPasswordConfirmNewPassword.observeAsState("")
        val forgotPasswordNewPasswordVisible by viewModel.forgotPasswordNewPasswordVisible.observeAsState(false)
        val forgotPasswordConfirmNewPasswordVisible by viewModel.forgotPasswordConfirmNewPasswordVisible.observeAsState(false)
        val forgotPasswordPasswordValid by viewModel.forgotPasswordPasswordValid.observeAsState(false)
        val forgotPasswordConfirmPasswordValid by viewModel.forgotPasswordConfirmPasswordValid.observeAsState(false)
        val showForgotPasswordPasswordCriteriaDialog by viewModel.showForgotPasswordPasswordCriteriaDialog.observeAsState(false)
        val showVerificationError by viewModel.showVerificationError.observeAsState(false)
        val verificationErrorMessage by viewModel.verificationErrorMessage.observeAsState("")
        val showResetError by viewModel.showResetError.observeAsState(false)
        val resetErrorMessage by viewModel.resetErrorMessage.observeAsState("")


        LaunchedEffect(loginAttemptSuccess) {
            if (loginAttemptSuccess == true) {
                Toast.makeText(context, "Successful Log in", Toast.LENGTH_SHORT).show()
                viewModel.resetLoginNavigationStates()
            } else if (loginAttemptSuccess == false) {
                viewModel.resetLoginNavigationStates()
            }
        }

        LaunchedEffect(navigateToQuestionnaire) {
            navigateToQuestionnaire?.let { userId ->
                val intent = Intent(context, Questionaire::class.java)
                intent.putExtra("user_id", userId)
                context.startActivity(intent)
                viewModel.resetLoginNavigationStates()
            }
        }

        LaunchedEffect(navigateToHome) {
            navigateToHome?.let { userId ->
                val intent = Intent(context, HomeScreen::class.java)
                intent.putExtra("user_id", userId)
                context.startActivity(intent)
                viewModel.resetLoginNavigationStates()
            }
        }


        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            verticalArrangement = Arrangement.Top,
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Image(
                painter = painterResource(id = R.drawable.welcomeback),
                contentDescription = "Welcome image of Aaron",
                modifier = Modifier
                    .size(300.dp)
                    .fillMaxWidth(0.5f)
                    .align(Alignment.CenterHorizontally)
            )

            Text(
                text = "Enter Details",
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
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "User ID",
                    modifier = Modifier.width(120.dp),
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium
                )
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = !expanded },
                    modifier = Modifier
                        .weight(1f)
                        .height(65.dp)
                ) {
                    OutlinedTextField(
                        value = selectedUserId,
                        onValueChange = { },
                        readOnly = true,
                        label = { Text("Select User ID", fontSize = 16.sp) },
                        trailingIcon = {
                            ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded)
                        },
                        modifier = Modifier
                            .menuAnchor()
                            .fillMaxWidth(),
                        textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                    )

                    ExposedDropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        userIds.forEach { userId ->
                            DropdownMenuItem(
                                text = { Text(userId, fontSize = 18.sp) },
                                onClick = {
                                    viewModel.onLoginSelectedUserIdChange(userId)
                                    expanded = false
                                }
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Password",
                    modifier = Modifier.width(120.dp),
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium
                )
                OutlinedTextField(
                    value = password,
                    onValueChange = { viewModel.onLoginPasswordChange(it) },
                    label = { Text("Enter Password", fontSize = 16.sp) },
                    modifier = Modifier
                        .weight(1f)
                        .height(65.dp),
                    singleLine = true,
                    visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                    trailingIcon = {
                        val icon =
                            if (passwordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff
                        IconButton(
                            onClick = { viewModel.toggleLoginPasswordVisibility() },
                            modifier = Modifier.size(32.dp)
                        ) {
                            Icon(imageVector = icon, contentDescription = null)
                        }
                    },
                    textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                )
            }


            Spacer(modifier = Modifier.height(24.dp))


            Button(
                onClick = { viewModel.performLogin() },
                colors = ButtonDefaults.buttonColors(containerColor = CustomGreen),
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Login")
            }

            Spacer(modifier = Modifier.height(12.dp))

            TextButton(onClick = { viewModel.showForgotPasswordVerifyDialog() }) {
                Text("Forgot Password?", color = MaterialTheme.colorScheme.primary)
            }


            if (showLoginErrorDialog) {
                AlertDialog(
                    onDismissRequest = { viewModel.dismissLoginErrorDialog() },
                    title = { Text("Error: Login Failure.") },
                    text = { Text(loginDialogMessage) },
                    confirmButton = {
                        Button(onClick = { viewModel.dismissLoginErrorDialog() }) {
                            Text("OK")
                        }
                    }
                )
            }

            if (showForgotPasswordVerifyDialog) {
                var localExpanded by remember { mutableStateOf(false) }

                AlertDialog(
                    onDismissRequest = { viewModel.dismissForgotPasswordVerifyDialog() },
                    title = { Text("Verify Identity") },
                    text = {
                        Column {
                            ExposedDropdownMenuBox(
                                expanded = localExpanded,
                                onExpandedChange = { localExpanded = !localExpanded },
                                modifier = Modifier.fillMaxWidth().height(65.dp)
                            ) {
                                OutlinedTextField(
                                    value = forgotPasswordSelectedUserId,
                                    onValueChange = { },
                                    readOnly = true,
                                    label = { Text("Select User ID", fontSize = 16.sp) },
                                    trailingIcon = {
                                        ExposedDropdownMenuDefaults.TrailingIcon(expanded = localExpanded)
                                    },
                                    modifier = Modifier
                                        .menuAnchor()
                                        .fillMaxWidth(),
                                    textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                                )
                                ExposedDropdownMenu(
                                    expanded = localExpanded,
                                    onDismissRequest = { localExpanded = false }
                                ) {
                                    userIds.forEach { userId ->
                                        DropdownMenuItem(
                                            text = { Text(userId, fontSize = 18.sp) },
                                            onClick = {
                                                viewModel.onForgotPasswordSelectedUserIdChange(userId)
                                                localExpanded = false
                                            }
                                        )
                                    }
                                }
                            }
                            Spacer(modifier = Modifier.height(16.dp))
                            OutlinedTextField(
                                value = forgotPasswordPhoneNumber,
                                onValueChange = { viewModel.onForgotPasswordPhoneNumberChange(it) },
                                label = { Text("Enter Phone Number", fontSize = 16.sp) },
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                                modifier = Modifier.fillMaxWidth().height(65.dp),
                                textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                            )
                            if (showVerificationError) {
                                Text(verificationErrorMessage, color = Color.Red, style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    },
                    confirmButton = {
                        Button(onClick = { viewModel.verifyForgotPasswordIdentity(allPatients) }) {
                            Text("Verify")
                        }
                    },
                    dismissButton = {
                        TextButton(onClick = { viewModel.dismissForgotPasswordVerifyDialog() }) {
                            Text("Cancel")
                        }
                    }
                )
            }

            if (showForgotPasswordResetDialog) {
                AlertDialog(
                    onDismissRequest = { viewModel.dismissForgotPasswordResetDialog() },
                    title = { Text("Reset Password - User $forgotPasswordSelectedUserId") },
                    text = {
                        Column {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                OutlinedTextField(
                                    value = forgotPasswordNewPassword,
                                    onValueChange = { viewModel.onForgotPasswordNewPasswordChange(it) },
                                    label = { Text("New Password", fontSize = 16.sp) },
                                    visualTransformation = if (forgotPasswordNewPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                                    trailingIcon = {
                                        Row {
                                            IconButton(
                                                onClick = { viewModel.toggleForgotPasswordNewPasswordVisibility() }
                                            ) {
                                                Icon(
                                                    imageVector = if (forgotPasswordNewPasswordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                                                    contentDescription = "Toggle password visibility"
                                                )
                                            }
                                            IconButton(
                                                onClick = { viewModel.validateForgotPasswordNewPassword() }
                                            ) {
                                                Icon(
                                                    imageVector = if (forgotPasswordPasswordValid) Icons.Default.ThumbUp else Icons.Default.Check,
                                                    contentDescription = "Validate password"
                                                )
                                            }
                                        }
                                    },
                                    modifier = Modifier.fillMaxWidth().height(65.dp),
                                    textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                                )
                            }
                            Spacer(modifier = Modifier.height(16.dp))
                            OutlinedTextField(
                                value = forgotPasswordConfirmNewPassword,
                                onValueChange = { viewModel.onForgotPasswordConfirmNewPasswordChange(it) },
                                label = { Text("Confirm New Password", fontSize = 16.sp) },
                                visualTransformation = if (forgotPasswordConfirmNewPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                                trailingIcon = {
                                    Row {
                                        IconButton(
                                            onClick = { viewModel.toggleForgotPasswordConfirmNewPasswordVisibility() }
                                        ) {
                                            Icon(
                                                imageVector = if (forgotPasswordConfirmNewPasswordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                                                contentDescription = "Toggle confirm password visibility"
                                            )
                                        }
                                        IconButton(
                                            onClick = { viewModel.validateForgotPasswordConfirmPassword() }
                                        ) {
                                            Icon(
                                                imageVector = if (forgotPasswordConfirmPasswordValid) Icons.Default.ThumbUp else Icons.Default.Check,
                                                contentDescription = "Validate confirm password"
                                            )
                                        }
                                    }
                                },
                                modifier = Modifier.fillMaxWidth().height(65.dp),
                                textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                            )
                            if (showResetError) {
                                Text(resetErrorMessage, color = Color.Red, style = MaterialTheme.typography.bodySmall)
                            }

                            if (showForgotPasswordPasswordCriteriaDialog) {
                                AlertDialog(
                                    onDismissRequest = { viewModel.dismissForgotPasswordPasswordCriteriaDialog() },
                                    title = { Text("Password Requirements") },
                                    text = {
                                        Column {
                                            Text("- At least 5 characters long")
                                            Text("- Must contain at least 1 number")
                                        }
                                    },
                                    confirmButton = {
                                        Button(onClick = { viewModel.dismissForgotPasswordPasswordCriteriaDialog() }) {
                                            Text("Got It")
                                        }
                                    }
                                )
                            }
                        }
                    },
                    confirmButton = {
                        Button(onClick = { viewModel.resetPassword() }) {
                            Text("Reset Password")
                        }
                    },
                    dismissButton = {
                        TextButton(onClick = { viewModel.dismissForgotPasswordResetDialog() }) {
                            Text("Cancel")
                        }
                    }
                )
            }
        }
    }

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun RegisterForm(
        viewModel: LoginRegisterViewModel,
        onRegistrationComplete: () -> Unit
    ) {
        val allPatients by viewModel.allPatients.observeAsState(emptyList())
        val unregisteredUserIds by viewModel.unregisteredUserIds.observeAsState(emptyList())

        val selectedUserId by viewModel.registerSelectedUserId.observeAsState("")
        val phone by viewModel.registerPhone.observeAsState("")
        val name by viewModel.registerName.observeAsState("")
        val age by viewModel.registerAge.observeAsState("")
        val password by viewModel.registerPassword.observeAsState("")
        val confirmPassword by viewModel.registerConfirmPassword.observeAsState("")
        val passwordVisible by viewModel.registerPasswordVisible.observeAsState(false)
        val confirmPasswordVisible by viewModel.registerConfirmPasswordVisible.observeAsState(false)
        var expanded by remember { mutableStateOf(false) }

        val isPhoneVerified by viewModel.isPhoneVerified.observeAsState(false)
        val nameValid by viewModel.nameValid.observeAsState(false)
        val passwordValid by viewModel.passwordValid.observeAsState(false)
        val confirmPasswordValid by viewModel.confirmPasswordValid.observeAsState(false)
        val confirmPasswordChecked by viewModel.confirmPasswordChecked.observeAsState(false)

        val showPhoneMismatchDialog by viewModel.showPhoneMismatchDialog.observeAsState(false)
        val showNameErrorDialog by viewModel.showNameErrorDialog.observeAsState(false)
        val showPasswordCriteriaDialog by viewModel.showPasswordCriteriaDialog.observeAsState(false)
        val showRegisterPasswordErrorDialog by viewModel.showRegisterPasswordErrorDialog.observeAsState(false)
        val registerPasswordErrorMessage by viewModel.registerPasswordErrorMessage.observeAsState("")
        val showConfirmPasswordErrorDialog by viewModel.showConfirmPasswordErrorDialog.observeAsState(false)
        val confirmPasswordErrorMessage by viewModel.confirmPasswordErrorMessage.observeAsState("")
        val showConfirmPasswordDependencyDialog by viewModel.showConfirmPasswordDependencyDialog.observeAsState(false)
        val showAgeErrorDialog by viewModel.showAgeErrorDialog.observeAsState(false)
        val showInvalidDetails by viewModel.showInvalidDetailsDialog.observeAsState(false)
        val showGoBackToLogIn by viewModel.showGoBackToLoginDialog.observeAsState(false)


        val scrollState = rememberScrollState()

        val selectedPatient = allPatients.find { it.userID == selectedUserId }

        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState)
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Top
        ) {
            Image(
                painter = painterResource(id = R.drawable.register),
                contentDescription = "Register image of Aaron",
                modifier = Modifier
                    .size(300.dp)
                    .fillMaxWidth(0.5f)
                    .align(Alignment.CenterHorizontally)
            )


            Text(
                text = "Enter Details",
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
                modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp),
            )

            Text(
                text = "Note: Please press ✔ to verify input.",
                modifier = Modifier.fillMaxWidth(),
                fontSize = 16.sp,
                lineHeight = 18.sp,
            )

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "User ID",
                    modifier = Modifier.width(120.dp),
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium
                )
                ExposedDropdownMenuBox(
                    expanded = expanded,
                    onExpandedChange = { expanded = !expanded },
                    modifier = Modifier
                        .weight(1f)
                        .height(65.dp)
                ) {
                    OutlinedTextField(
                        value = selectedUserId,
                        onValueChange = { },
                        readOnly = true,
                        label = { Text("Select User ID", fontSize = 16.sp) },
                        trailingIcon = {
                            ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded)
                        },
                        modifier = Modifier
                            .menuAnchor()
                            .fillMaxWidth(),
                        textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                    )

                    ExposedDropdownMenu(
                        expanded = expanded,
                        onDismissRequest = { expanded = false }
                    ) {
                        unregisteredUserIds.forEach { unregisteredUserId ->
                            DropdownMenuItem(
                                text = { Text(unregisteredUserId, fontSize = 18.sp) },
                                onClick = {
                                    viewModel.onRegisterSelectedUserIdChange(unregisteredUserId)
                                    expanded = false
                                }
                            )
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Phone number",
                    modifier = Modifier.width(120.dp),
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium
                )
                OutlinedTextField(
                    value = phone,
                    onValueChange = { viewModel.onRegisterPhoneChange(it) },
                    label = { Text("Enter Phone Number", fontSize = 16.sp) },
                    placeholder = { Text("Must match pre-registered number.", fontSize = 16.sp) },
                    trailingIcon = {
                        IconButton(
                            onClick = { viewModel.verifyPhoneNumber(selectedPatient) },
                            modifier = Modifier.size(32.dp)
                        ) {
                            Icon(
                                imageVector = if (isPhoneVerified) Icons.Default.ThumbUp else Icons.Default.Check,
                                contentDescription = "Verify Phone"
                            )
                        }
                    },
                    modifier = Modifier
                        .weight(1f)
                        .height(65.dp),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                    textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Name",
                    modifier = Modifier.width(120.dp),
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium
                )
                OutlinedTextField(
                    value = name,
                    onValueChange = { viewModel.onRegisterNameChange(it) },
                    label = { Text("Enter Name", fontSize = 16.sp) },
                    placeholder = { Text("Only letters!", fontSize = 16.sp) },
                    trailingIcon = {
                        IconButton(
                            onClick = { viewModel.validateName() },
                            modifier = Modifier.size(32.dp)
                        ) {
                            Icon(
                                imageVector = if (nameValid) Icons.Default.ThumbUp else Icons.Default.Check,
                                contentDescription = "Validate name"
                            )
                        }
                    },
                    modifier = Modifier
                        .weight(1f)
                        .height(65.dp),
                    textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                )
            }

            if (showNameErrorDialog) {
                AlertDialog(
                    onDismissRequest = { viewModel.dismissNameErrorDialog() },
                    title = { Text("Error: Invalid Name") },
                    text = { Text("Only letters for name.") },
                    confirmButton = {
                        Button(onClick = { viewModel.dismissNameErrorDialog() }) {
                            Text("OK")
                        }
                    }
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Age",
                    modifier = Modifier.width(120.dp),
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium
                )
                OutlinedTextField(
                    value = age,
                    onValueChange = { viewModel.onRegisterAgeChange(it) },
                    label = { Text("Enter Age (optional)", fontSize = 16.sp) },
                    placeholder = { Text("Only numbers!", fontSize = 16.sp) },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier
                        .weight(1f)
                        .height(65.dp),
                    textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                )
            }


            Spacer(modifier = Modifier.height(16.dp))

            val currentSelectedPatientGender by remember(selectedUserId, allPatients) {
                val patient = allPatients.find { it.userID == selectedUserId }
                mutableStateOf(patient?.userSex)
            }

            GenderDisplayBox(gender = currentSelectedPatientGender)

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Password",
                    modifier = Modifier.width(90.dp),
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium
                )
                Spacer(modifier = Modifier.width(4.dp))

                OutlinedTextField(
                    value = password,
                    onValueChange = { viewModel.onRegisterPasswordChange(it) },
                    label = { Text("Enter Password", fontSize = 16.sp) },
                    visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                    trailingIcon = {
                        Row {
                            IconButton(
                                onClick = { viewModel.toggleRegisterPasswordVisibility() },
                                modifier = Modifier.size(32.dp)
                            ) {
                                Icon(
                                    imageVector = if (passwordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                                    contentDescription = "Toggle password visibility"
                                )
                            }
                            IconButton(
                                onClick = { viewModel.validateRegisterPassword() },
                                modifier = Modifier.size(32.dp)
                            ) {
                                Icon(
                                    imageVector = if (passwordValid) Icons.Default.ThumbUp else Icons.Default.Check,
                                    contentDescription = "Validate password"
                                )
                            }
                        }
                    },
                    modifier = Modifier
                        .weight(1f)
                        .height(65.dp),
                    textStyle = LocalTextStyle.current.copy(fontSize = 18.sp)
                )
            }


            if (showRegisterPasswordErrorDialog) {
                AlertDialog(
                    onDismissRequest = { viewModel.dismissRegisterPasswordErrorDialog() },
                    title = { Text("Error: Invalid Password") },
                    text = { Text(registerPasswordErrorMessage) },
                    confirmButton = {
                        Button(onClick = { viewModel.dismissRegisterPasswordErrorDialog() }) {
                            Text("OK")
                        }
                    }
                )
            }

            if (showPasswordCriteriaDialog) {
                AlertDialog(
                    onDismissRequest = { viewModel.dismissPasswordCriteriaDialog() },
                    title = { Text("Password Requirements") },
                    text = {
                        Column {
                            Text("- At least 5 characters long")
                            Text("- Must contain at least 1 number")
                        }
                    },
                    confirmButton = {
                        Button(onClick = { viewModel.dismissPasswordCriteriaDialog() }) {
                            Text("Got It")
                        }
                    }
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Confirm Password",
                    modifier = Modifier.width(120.dp),
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Medium
                )
                OutlinedTextField(
                    value = confirmPassword,
                    onValueChange = { viewModel.onRegisterConfirmPasswordChange(it) },
                    label = { Text("Re-enter", fontSize = 16.sp) }, // Increased label font size
                    visualTransformation = if (confirmPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                    trailingIcon = {
                        Row {
                            IconButton(
                                onClick = { viewModel.toggleRegisterConfirmPasswordVisibility() },
                                modifier = Modifier.size(32.dp)
                            ) {
                                Icon(
                                    imageVector = if (confirmPasswordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                                    contentDescription = "Toggle confirm password visibility"
                                )
                            }
                            IconButton(
                                onClick = { viewModel.validateRegisterConfirmPassword() },
                                modifier = Modifier.size(32.dp)
                            ) {
                                Icon(
                                    imageVector = if (confirmPasswordChecked && confirmPasswordValid)
                                        Icons.Default.ThumbUp else Icons.Default.Check,
                                    contentDescription = "Confirm password check"
                                )
                            }
                        }
                    },
                    modifier = Modifier
                        .weight(1f)
                        .height(65.dp), // Increased height
                    textStyle = LocalTextStyle.current.copy(fontSize = 18.sp) // Increased text inside box
                )
            }


            if (showConfirmPasswordErrorDialog) {
                AlertDialog(
                    onDismissRequest = { viewModel.dismissConfirmPasswordErrorDialog() },
                    title = { Text("Error") },
                    text = { Text(confirmPasswordErrorMessage) },
                    confirmButton = {
                        Button(onClick = { viewModel.dismissConfirmPasswordErrorDialog() }) {
                            Text("OK")
                        }
                    }
                )
            }

            if (showConfirmPasswordDependencyDialog) {
                AlertDialog(
                    onDismissRequest = { viewModel.dismissConfirmPasswordDependencyDialog() },
                    title = { Text("Warning") },
                    text = { Text("Ensure password is verified.") },
                    confirmButton = {
                        Button(onClick = { viewModel.dismissConfirmPasswordDependencyDialog() }) {
                            Text("OK")
                        }
                    }
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            Button(
                colors = ButtonDefaults.buttonColors(containerColor = CustomGreen),
                onClick = { viewModel.performRegistration(onRegistrationComplete) },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Register")
            }

            Spacer(modifier = Modifier.height(10.dp))

            if (showPhoneMismatchDialog) {
                AlertDialog(
                    onDismissRequest = { viewModel.dismissPhoneMismatchDialog() },
                    title = { Text("Verification Failed") },
                    text = { Text("Not matching phone number!") },
                    confirmButton = {
                        Button(onClick = { viewModel.dismissPhoneMismatchDialog() }) {
                            Text("OK")
                        }
                    }
                )
            }

            if (showAgeErrorDialog) {
                AlertDialog(
                    onDismissRequest = { viewModel.dismissAgeErrorDialog() },
                    title = { Text("Error") },
                    text = { Text("Age must be a number only above age 0.") },
                    confirmButton = {
                        Button(onClick = { viewModel.dismissAgeErrorDialog() }) {
                            Text("OK")
                        }
                    }
                )
            }

            if (showInvalidDetails){
                AlertDialog(
                    onDismissRequest = { viewModel.dismissInvalidDetailsDialog() },
                    title = { Text("Error: Invalid Details.") },
                    text = { Text("Please ensure all details are filled and verified.") },
                    confirmButton = {
                        Button(onClick = { viewModel.dismissInvalidDetailsDialog() }) {
                            Text("OK")
                        }
                    }
                )
            }

            if (showGoBackToLogIn) {
                AlertDialog(
                    onDismissRequest = { viewModel.dismissGoBackToLoginDialog() },
                    title = { Text("Registration Complete!") },
                    text = { Text("Your details have been updated.") },
                    confirmButton = {
                        Button(onClick = {
                            viewModel.dismissGoBackToLoginDialog()
                            onRegistrationComplete()
                        }) {
                            Text("Log In")
                        }
                    }
                )
            }
        }
    }
}

@Composable
fun GenderDisplayBox(gender: Gender?) {
    val (displayText, backgroundColor) = when (gender) {
        Gender.MALE -> "Male" to Color(0xFFADD8E6)
        Gender.FEMALE -> "Female" to Color(0xFFFFC0CB)
        null -> "Gender" to Color.LightGray
    }

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(60.dp)
            .padding(vertical = 8.dp)
            .background(color = backgroundColor, shape = RoundedCornerShape(8.dp)),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = displayText,
            color = Color.Black,
            fontSize = 18.sp,
            fontWeight = FontWeight.Bold
        )
    }
}