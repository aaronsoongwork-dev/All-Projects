package com.fit2081.aaron_34076832.nutritrack.viewmodels

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.data.AuthManager
import com.fit2081.aaron_34076832.nutritrack.data.patient.Patient
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientRepository
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientViewModel
import com.fit2081.aaron_34076832.nutritrack.data.questionnaire.QuestionnaireRepository
import com.fit2081.aaron_34076832.nutritrack.data.questionnaire.QuestionnaireViewModel
import kotlinx.coroutines.launch

class LoginRegisterViewModel(application: Application, private val patientViewModel: PatientViewModel, private val questionnaireViewModel: QuestionnaireViewModel) : AndroidViewModel(application) {

    private val _isLoginScreen = MutableLiveData(true)
    val isLoginScreen: LiveData<Boolean> get() = _isLoginScreen

    fun toggleLoginRegisterScreen() {
        _isLoginScreen.value = !_isLoginScreen.value!!
    }

    private val _loginSelectedUserId = MutableLiveData("")
    val loginSelectedUserId: LiveData<String> get() = _loginSelectedUserId

    private val _loginPassword = MutableLiveData("")
    val loginPassword: LiveData<String> get() = _loginPassword

    private val _loginPasswordVisible = MutableLiveData(false)
    val loginPasswordVisible: LiveData<Boolean> get() = _loginPasswordVisible

    private val _showLoginErrorDialog = MutableLiveData(false)
    val showLoginErrorDialog: LiveData<Boolean> get() = _showLoginErrorDialog

    private val _loginDialogMessage = MutableLiveData("")
    val loginDialogMessage: LiveData<String> get() = _loginDialogMessage

    private val _loginAttemptSuccess = MutableLiveData<Boolean?>(null)
    val loginAttemptSuccess: LiveData<Boolean?> get() = _loginAttemptSuccess

    private val _navigateToQuestionnaire = MutableLiveData<String?>(null)
    val navigateToQuestionnaire: LiveData<String?> get() = _navigateToQuestionnaire

    private val _navigateToHome = MutableLiveData<String?>(null)
    val navigateToHome: LiveData<String?> get() = _navigateToHome

    private val _showForgotPasswordVerifyDialog = MutableLiveData(false)
    val showForgotPasswordVerifyDialog: LiveData<Boolean> get() = _showForgotPasswordVerifyDialog

    private val _showForgotPasswordResetDialog = MutableLiveData(false)
    val showForgotPasswordResetDialog: LiveData<Boolean> get() = _showForgotPasswordResetDialog

    private val _forgotPasswordSelectedUserId = MutableLiveData("")
    val forgotPasswordSelectedUserId: LiveData<String> get() = _forgotPasswordSelectedUserId

    private val _forgotPasswordPhoneNumber = MutableLiveData("")
    val forgotPasswordPhoneNumber: LiveData<String> get() = _forgotPasswordPhoneNumber

    private val _forgotPasswordNewPassword = MutableLiveData("")
    val forgotPasswordNewPassword: LiveData<String> get() = _forgotPasswordNewPassword

    private val _forgotPasswordConfirmNewPassword = MutableLiveData("")
    val forgotPasswordConfirmNewPassword: LiveData<String> get() = _forgotPasswordConfirmNewPassword

    private val _forgotPasswordNewPasswordVisible = MutableLiveData(false)
    val forgotPasswordNewPasswordVisible: LiveData<Boolean> get() = _forgotPasswordNewPasswordVisible

    private val _forgotPasswordConfirmNewPasswordVisible = MutableLiveData(false)
    val forgotPasswordConfirmNewPasswordVisible: LiveData<Boolean> get() = _forgotPasswordConfirmNewPasswordVisible

    private val _forgotPasswordPasswordValid = MutableLiveData(false)
    val forgotPasswordPasswordValid: LiveData<Boolean> get() = _forgotPasswordPasswordValid

    private val _forgotPasswordConfirmPasswordValid = MutableLiveData(false)
    val forgotPasswordConfirmPasswordValid: LiveData<Boolean> get() = _forgotPasswordConfirmPasswordValid

    private val _forgotPasswordPasswordErrorMessage = MutableLiveData("")
    val forgotPasswordPasswordErrorMessage: LiveData<String> get() = _forgotPasswordPasswordErrorMessage

    private val _showForgotPasswordPasswordCriteriaDialog = MutableLiveData(false)
    val showForgotPasswordPasswordCriteriaDialog: LiveData<Boolean> get() = _showForgotPasswordPasswordCriteriaDialog

    private val _showVerificationError = MutableLiveData(false)
    val showVerificationError: LiveData<Boolean> get() = _showVerificationError

    private val _verificationErrorMessage = MutableLiveData("")
    val verificationErrorMessage: LiveData<String> get() = _verificationErrorMessage

    private val _showResetError = MutableLiveData(false)
    val showResetError: LiveData<Boolean> get() = _showResetError

    private val _resetErrorMessage = MutableLiveData("")
    val resetErrorMessage: LiveData<String> get() = _resetErrorMessage


    private val _registerSelectedUserId = MutableLiveData("")
    val registerSelectedUserId: LiveData<String> get() = _registerSelectedUserId

    private val _registerPhone = MutableLiveData("")
    val registerPhone: LiveData<String> get() = _registerPhone

    private val _registerName = MutableLiveData("")
    val registerName: LiveData<String> get() = _registerName

    private val _registerAge = MutableLiveData("")
    val registerAge: LiveData<String> get() = _registerAge

    private val _registerPassword = MutableLiveData("")
    val registerPassword: LiveData<String> get() = _registerPassword

    private val _registerConfirmPassword = MutableLiveData("")
    val registerConfirmPassword: LiveData<String> get() = _registerConfirmPassword

    private val _registerPasswordVisible = MutableLiveData(false)
    val registerPasswordVisible: LiveData<Boolean> get() = _registerPasswordVisible

    private val _registerConfirmPasswordVisible = MutableLiveData(false)
    val registerConfirmPasswordVisible: LiveData<Boolean> get() = _registerConfirmPasswordVisible

    private val _isPhoneVerified = MutableLiveData(false)
    val isPhoneVerified: LiveData<Boolean> get() = _isPhoneVerified

    private val _nameValid = MutableLiveData(false)
    val nameValid: LiveData<Boolean> get() = _nameValid

    private val _passwordValid = MutableLiveData(false)
    val passwordValid: LiveData<Boolean> get() = _passwordValid

    private val _confirmPasswordValid = MutableLiveData(false)
    val confirmPasswordValid: LiveData<Boolean> get() = _confirmPasswordValid

    private val _confirmPasswordChecked = MutableLiveData(false)
    val confirmPasswordChecked: LiveData<Boolean> get() = _confirmPasswordChecked

    private val _registerPasswordErrorMessage = MutableLiveData("")
    val registerPasswordErrorMessage: LiveData<String> get() = _registerPasswordErrorMessage

    private val _confirmPasswordErrorMessage = MutableLiveData("")
    val confirmPasswordErrorMessage: LiveData<String> get() = _confirmPasswordErrorMessage


    private val _showPhoneMismatchDialog = MutableLiveData(false)
    val showPhoneMismatchDialog: LiveData<Boolean> get() = _showPhoneMismatchDialog

    private val _showNameErrorDialog = MutableLiveData(false)
    val showNameErrorDialog: LiveData<Boolean> get() = _showNameErrorDialog

    private val _showPasswordCriteriaDialog = MutableLiveData(false)
    val showPasswordCriteriaDialog: LiveData<Boolean> get() = _showPasswordCriteriaDialog

    private val _showRegisterPasswordErrorDialog = MutableLiveData(false)
    val showRegisterPasswordErrorDialog: LiveData<Boolean> get() = _showRegisterPasswordErrorDialog

    private val _showConfirmPasswordErrorDialog = MutableLiveData(false)
    val showConfirmPasswordErrorDialog: LiveData<Boolean> get() = _showConfirmPasswordErrorDialog

    private val _showConfirmPasswordDependencyDialog = MutableLiveData(false)
    val showConfirmPasswordDependencyDialog: LiveData<Boolean> get() = _showConfirmPasswordDependencyDialog

    private val _showAgeErrorDialog = MutableLiveData(false)
    val showAgeErrorDialog: LiveData<Boolean> get() = _showAgeErrorDialog

    private val _showInvalidDetailsDialog = MutableLiveData(false)
    val showInvalidDetailsDialog: LiveData<Boolean> get() = _showInvalidDetailsDialog

    private val _showGoBackToLoginDialog = MutableLiveData(false)
    val showGoBackToLoginDialog: LiveData<Boolean> get() = _showGoBackToLoginDialog

    private val userPreferencesManager = UserPreferencesManager(application.applicationContext)


    val allPatients: LiveData<List<Patient>> = patientViewModel.allPatients
    val unregisteredUserIds: LiveData<List<String>> = patientViewModel.unregisteredUserIds


    fun onLoginSelectedUserIdChange(userId: String) {
        _loginSelectedUserId.value = userId
        patientViewModel.setSelectedUserId(userId)
    }

    fun onLoginPasswordChange(password: String) {
        _loginPassword.value = password
    }

    fun toggleLoginPasswordVisibility() {
        _loginPasswordVisible.value = !_loginPasswordVisible.value!!
    }

    fun dismissLoginErrorDialog() {
        _showLoginErrorDialog.value = false
        _loginDialogMessage.value = ""
    }

    fun resetLoginNavigationStates() {
        _navigateToQuestionnaire.value = null
        _navigateToHome.value = null
        _loginAttemptSuccess.value = null
    }

    fun performLogin() {
        viewModelScope.launch {
            val userId = _loginSelectedUserId.value.orEmpty()
            val password = _loginPassword.value.orEmpty()

            when {
                userId.isNotBlank() && patientViewModel.isPasswordEmpty(userId) -> {
                    _loginDialogMessage.value = "Password has not been set.\nPlease Register!"
                    _showLoginErrorDialog.value = true
                    _loginAttemptSuccess.value = false
                }
                userId.isBlank() || password.isBlank() -> {
                    _loginDialogMessage.value = "Please fill in User ID and Password!"
                    _showLoginErrorDialog.value = true
                    _loginAttemptSuccess.value = false
                }
                else -> {
                    val success = patientViewModel.loginUser(userId, password)
                    if (success) {
                        _loginAttemptSuccess.value = true
                        userPreferencesManager.setLoggedIn(true)
                        userPreferencesManager.setCurrentUserId(userId)

                        val questionnaire = questionnaireViewModel.getQuestionnaireByPatientIdBlocking(userId)
                        if (questionnaire?.isCompleted == true) {
                            _navigateToHome.value = userId
                        } else {
                            _navigateToQuestionnaire.value = userId
                        }
                    } else {
                        _loginDialogMessage.value = "Invalid login credentials"
                        _showLoginErrorDialog.value = true
                        _loginAttemptSuccess.value = false
                    }
                }
            }
        }
    }


    fun showForgotPasswordVerifyDialog() {
        _showForgotPasswordVerifyDialog.value = true
        _forgotPasswordSelectedUserId.value = ""
        _forgotPasswordPhoneNumber.value = ""
        _showVerificationError.value = false
        _verificationErrorMessage.value = ""
    }

    fun dismissForgotPasswordVerifyDialog() {
        _showForgotPasswordVerifyDialog.value = false
    }

    fun onForgotPasswordSelectedUserIdChange(userId: String) {
        _forgotPasswordSelectedUserId.value = userId
        _forgotPasswordPhoneNumber.value = ""
        _showVerificationError.value = false
    }

    fun onForgotPasswordPhoneNumberChange(phoneNumber: String) {
        _forgotPasswordPhoneNumber.value = phoneNumber
        _showVerificationError.value = false
    }

    fun verifyForgotPasswordIdentity(allPatients: List<Patient>) {
        viewModelScope.launch {
            val patient = allPatients.find { it.userID == _forgotPasswordSelectedUserId.value }
            if (patient != null && patient.userPhoneNum.toString() == _forgotPasswordPhoneNumber.value) {
                _showForgotPasswordVerifyDialog.value = false
                _showForgotPasswordResetDialog.value = true
                _forgotPasswordNewPassword.value = ""
                _forgotPasswordConfirmNewPassword.value = ""
                _forgotPasswordPasswordValid.value = false
                _forgotPasswordConfirmPasswordValid.value = false
                _forgotPasswordNewPasswordVisible.value = false
                _forgotPasswordConfirmNewPasswordVisible.value = false
                _showResetError.value = false
                _resetErrorMessage.value = ""
            } else {
                _verificationErrorMessage.value = "User ID or Phone Number incorrect."
                _showVerificationError.value = true
            }
        }
    }

    fun dismissForgotPasswordResetDialog() {
        _showForgotPasswordResetDialog.value = false
        _forgotPasswordNewPassword.value = ""
        _forgotPasswordConfirmNewPassword.value = ""
        _forgotPasswordPasswordValid.value = false
        _forgotPasswordConfirmPasswordValid.value = false
    }

    fun onForgotPasswordNewPasswordChange(password: String) {
        _forgotPasswordNewPassword.value = password
        _forgotPasswordPasswordValid.value = false
        _showResetError.value = false
    }

    fun onForgotPasswordConfirmNewPasswordChange(password: String) {
        _forgotPasswordConfirmNewPassword.value = password
        _forgotPasswordConfirmPasswordValid.value = false
        _showResetError.value = false
    }

    fun toggleForgotPasswordNewPasswordVisibility() {
        _forgotPasswordNewPasswordVisible.value = !_forgotPasswordNewPasswordVisible.value!!
    }

    fun toggleForgotPasswordConfirmNewPasswordVisibility() {
        _forgotPasswordConfirmNewPasswordVisible.value = !_forgotPasswordConfirmNewPasswordVisible.value!!
    }

    fun validateForgotPasswordNewPassword() {
        val password = _forgotPasswordNewPassword.value.orEmpty()
        val lengthValid = password.length >= 5
        val containsNumber = password.any { it.isDigit() }
        when {
            !lengthValid -> {
                _forgotPasswordPasswordValid.value = false
                _forgotPasswordPasswordErrorMessage.value = "Password is weak.\nEnsure password is more than 5 characters."
                _showForgotPasswordPasswordCriteriaDialog.value = true
            }
            !containsNumber -> {
                _forgotPasswordPasswordValid.value = false
                _forgotPasswordPasswordErrorMessage.value = "Password must contain a number."
                _showForgotPasswordPasswordCriteriaDialog.value = true
            }
            else -> {
                _forgotPasswordPasswordValid.value = true
                _showForgotPasswordPasswordCriteriaDialog.value = false
            }
        }
    }

    fun validateForgotPasswordConfirmPassword() {
        if (!_forgotPasswordPasswordValid.value!!) {
            _resetErrorMessage.value = "Please set and validate the new password first."
            _showResetError.value = true
            return
        }
        _forgotPasswordConfirmPasswordValid.value = _forgotPasswordConfirmNewPassword.value == _forgotPasswordNewPassword.value
        if (!_forgotPasswordConfirmPasswordValid.value!!) {
            _resetErrorMessage.value = "Passwords do not match."
            _showResetError.value = true
        } else {
            _showResetError.value = false
        }
    }

    fun showForgotPasswordPasswordCriteriaDialogClick() {
        _showForgotPasswordPasswordCriteriaDialog.value = true
    }

    fun dismissForgotPasswordPasswordCriteriaDialog() {
        _showForgotPasswordPasswordCriteriaDialog.value = false
    }

    fun dismissVerificationErrorDialog() {
        _showVerificationError.value = false
    }

    fun dismissResetErrorDialog() {
        _showResetError.value = false
    }

    fun resetPassword() {
        viewModelScope.launch {
            if (_forgotPasswordPasswordValid.value!! && _forgotPasswordConfirmPasswordValid.value!! && _forgotPasswordNewPassword.value == _forgotPasswordConfirmNewPassword.value) {
                patientViewModel.updatePassword(_forgotPasswordSelectedUserId.value.orEmpty(), _forgotPasswordNewPassword.value.orEmpty())
                _showForgotPasswordResetDialog.value = false
                _loginPassword.value = ""
            } else {
                _resetErrorMessage.value = "Please ensure both passwords match and meet the criteria."
                _showResetError.value = true
            }
        }
    }


    fun onRegisterSelectedUserIdChange(userId: String) {
        _registerSelectedUserId.value = userId
        _registerPhone.value = ""
        _isPhoneVerified.value = false
    }

    fun onRegisterPhoneChange(phone: String) {
        _registerPhone.value = phone
        _isPhoneVerified.value = false
    }

    fun onRegisterNameChange(name: String) {
        _registerName.value = name
        _nameValid.value = false
    }

    fun onRegisterAgeChange(age: String) {
        if (age.all { it.isDigit() }) {
            _registerAge.value = age
        }
    }

    fun onRegisterPasswordChange(password: String) {
        _registerPassword.value = password
        _passwordValid.value = false
        _confirmPasswordChecked.value = false
    }

    fun onRegisterConfirmPasswordChange(confirmPassword: String) {
        _registerConfirmPassword.value = confirmPassword
        _confirmPasswordChecked.value = false
    }

    fun toggleRegisterPasswordVisibility() {
        _registerPasswordVisible.value = !_registerPasswordVisible.value!!
    }

    fun toggleRegisterConfirmPasswordVisibility() {
        _registerConfirmPasswordVisible.value = !_registerConfirmPasswordVisible.value!!
    }

    fun verifyPhoneNumber(selectedPatient: Patient?) {
        val phoneLong = _registerPhone.value.toLongOrNull()
        val isMatch = (selectedPatient?.userPhoneNum == phoneLong && selectedPatient != null)
        _isPhoneVerified.value = isMatch
        if (!isMatch) {
            _showPhoneMismatchDialog.value = true
        }
    }

    fun validateName() {
        if (_registerName.value.orEmpty().matches(Regex("^[a-zA-Z\\s]+\$"))) {
            _nameValid.value = true
        } else {
            _nameValid.value = false
            _showNameErrorDialog.value = true
        }
    }

    fun validateRegisterPassword() {
        val password = _registerPassword.value.orEmpty()
        val lengthValid = password.length >= 5
        val containsNumber = password.any { it.isDigit() }
        when {
            !lengthValid -> {
                _passwordValid.value = false
                _registerPasswordErrorMessage.value = "Password is weak.\nEnsure password is more than 5 characters."
                _showRegisterPasswordErrorDialog.value = true
            }
            !containsNumber -> {
                _passwordValid.value = false
                _registerPasswordErrorMessage.value = "Password must contain a number."
                _showRegisterPasswordErrorDialog.value = true
            }
            else -> {
                _passwordValid.value = true
            }
        }
    }

    fun validateRegisterConfirmPassword() {
        if (!_passwordValid.value!!) {
            _showConfirmPasswordDependencyDialog.value = true
            return
        }
        _confirmPasswordChecked.value = true
        _confirmPasswordValid.value = _registerConfirmPassword.value == _registerPassword.value && _registerConfirmPassword.value.orEmpty().isNotEmpty()
        _confirmPasswordErrorMessage.value = if (!_confirmPasswordValid.value!!) "Please ensure the same password is used." else ""
        _showConfirmPasswordErrorDialog.value = !_confirmPasswordValid.value!!
    }

    fun dismissPhoneMismatchDialog() { _showPhoneMismatchDialog.value = false }
    fun dismissNameErrorDialog() { _showNameErrorDialog.value = false }
    fun dismissRegisterPasswordErrorDialog() { _showRegisterPasswordErrorDialog.value = false }
    fun dismissPasswordCriteriaDialog() { _showPasswordCriteriaDialog.value = false }
    fun dismissConfirmPasswordErrorDialog() { _showConfirmPasswordErrorDialog.value = false }
    fun dismissConfirmPasswordDependencyDialog() { _showConfirmPasswordDependencyDialog.value = false }
    fun dismissAgeErrorDialog() { _showAgeErrorDialog.value = false }
    fun dismissInvalidDetailsDialog() { _showInvalidDetailsDialog.value = false }
    fun dismissGoBackToLoginDialog() { _showGoBackToLoginDialog.value = false }


    fun performRegistration(onRegistrationComplete: () -> Unit) {
        val isFormValid = _nameValid.value!! && _isPhoneVerified.value!! && _passwordValid.value!! && _confirmPasswordValid.value!!
        val selectedUserId = _registerSelectedUserId.value.orEmpty()
        val password = _registerPassword.value.orEmpty()
        val confirmPassword = _registerConfirmPassword.value.orEmpty()
        val age = _registerAge.value.orEmpty()
        val name = _registerName.value.orEmpty()
        val phone = _registerPhone.value.orEmpty()

        when {
            !isFormValid || selectedUserId.isBlank() || password.isBlank() || confirmPassword.isBlank() -> {
                _showInvalidDetailsDialog.value = true
            }
            (age.isNotBlank() && (age.toIntOrNull() == null || age.toIntOrNull()!! < 1)) -> {
                _showAgeErrorDialog.value = true
            }
            else -> {
                val intAge = age.toIntOrNull()
                viewModelScope.launch {
                    patientViewModel.registerUser(
                        userId = selectedUserId,
                        name = name,
                        age = intAge,
                        password = password,
                        userPhoneNum = phone.toLongOrNull()
                    )
                    _showGoBackToLoginDialog.value = true
                    onRegistrationComplete()
                }
            }
        }
    }

    class LoginRegisterViewModelFactory(
        private val application: Application,
        private val patientRepository: PatientRepository,
        private val questionnaireRepository: QuestionnaireRepository,
        private val authManager: AuthManager
    ) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(LoginRegisterViewModel::class.java)) {
                val patientViewModel = PatientViewModel(patientRepository, authManager)
                val questionnaireViewModel = QuestionnaireViewModel(application)
                @Suppress("UNCHECKED_CAST")
                return LoginRegisterViewModel(application, patientViewModel, questionnaireViewModel) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}