package com.fit2081.aaron_34076832.nutritrack.viewmodels

import android.app.Application
import android.content.Context
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.fit2081.a1healthapp.data.Gender.Gender
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import com.fit2081.aaron_34076832.nutritrack.data.AuthManager
import com.fit2081.aaron_34076832.nutritrack.data.patient.Patient
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientRepository
import com.fit2081.aaron_34076832.nutritrack.data.patient.PatientViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class EditProfileViewModel(application: Application) : AndroidViewModel(application) {

    private val patientRepository: PatientRepository = PatientRepository(application)
    private val authManager: AuthManager = AuthManager(patientRepository)

    private val patientViewModel: PatientViewModel = PatientViewModel(patientRepository, authManager)

    private val _selectedUserId = MutableStateFlow("")
    val selectedUserId: StateFlow<String> = _selectedUserId.asStateFlow()

    val selectedUserName: LiveData<String> = patientViewModel.selectedUserName
    val selectedUserAge: LiveData<Int?> = patientViewModel.selectedUserAge
    val selectedUserSex: LiveData<Gender?> = patientViewModel.selectedUserSex
    val selectedUserPhoneNum: LiveData<String?> = patientViewModel.selectedUserPhoneNum
    val selectedUserPassword: LiveData<String> = patientViewModel.selectedUserPassword

    val allPatients: LiveData<List<Patient>> = patientViewModel.allPatients

    private val _phoneInput = MutableStateFlow("")
    val phoneInput: StateFlow<String> = _phoneInput.asStateFlow()

    private val _nameInput = MutableStateFlow("")
    val nameInput: StateFlow<String> = _nameInput.asStateFlow()

    private val _ageInput = MutableStateFlow("")
    val ageInput: StateFlow<String> = _ageInput.asStateFlow()

    private val _showOldPasswordDialog = MutableStateFlow(false)
    val showOldPasswordDialog: StateFlow<Boolean> = _showOldPasswordDialog.asStateFlow()

    private val _showNewPasswordDialog = MutableStateFlow(false)
    val showNewPasswordDialog: StateFlow<Boolean> = _showNewPasswordDialog.asStateFlow()

    private val _oldPasswordInput = MutableStateFlow("")
    val oldPasswordInput: StateFlow<String> = _oldPasswordInput.asStateFlow()

    private val _newPasswordInput = MutableStateFlow("")
    val newPasswordInput: StateFlow<String> = _newPasswordInput.asStateFlow()

    private val _confirmNewPasswordInput = MutableStateFlow("")
    val confirmNewPasswordInput: StateFlow<String> = _confirmNewPasswordInput.asStateFlow()

    private val _oldPasswordVisible = MutableStateFlow(false)
    val oldPasswordVisible: StateFlow<Boolean> = _oldPasswordVisible.asStateFlow()

    private val _newPasswordVisible = MutableStateFlow(false)
    val newPasswordVisible: StateFlow<Boolean> = _newPasswordVisible.asStateFlow()

    private val _confirmNewPasswordVisible = MutableStateFlow(false)
    val confirmNewPasswordVisible: StateFlow<Boolean> = _confirmNewPasswordVisible.asStateFlow()

    private val _passwordTriesRemaining = MutableStateFlow(3)
    val passwordTriesRemaining: StateFlow<Int> = _passwordTriesRemaining.asStateFlow()

    private val _newPasswordValid = MutableStateFlow(false)
    val newPasswordValid: StateFlow<Boolean> = _newPasswordValid.asStateFlow()

    private val _confirmNewPasswordValid = MutableStateFlow(false)
    val confirmNewPasswordValid: StateFlow<Boolean> = _confirmNewPasswordValid.asStateFlow()

    private val _newPasswordErrorMessage = MutableStateFlow("")
    val newPasswordErrorMessage: StateFlow<String> = _newPasswordErrorMessage.asStateFlow()

    private val _confirmNewPasswordErrorMessage = MutableStateFlow("")
    val confirmNewPasswordErrorMessage: StateFlow<String> = _confirmNewPasswordErrorMessage.asStateFlow()

    private val _expandedDropdown = MutableStateFlow(false)
    val expandedDropdown: StateFlow<Boolean> = _expandedDropdown.asStateFlow()

    private val _isPhoneValid = MutableStateFlow(false)
    val isPhoneValid: StateFlow<Boolean> = _isPhoneValid.asStateFlow()

    private val _showPhoneMismatchDialog = MutableStateFlow(false)
    val showPhoneMismatchDialog: StateFlow<Boolean> = _showPhoneMismatchDialog.asStateFlow()

    private val _nameValid = MutableStateFlow(false)
    val nameValid: StateFlow<Boolean> = _nameValid.asStateFlow()

    private val _showNameErrorDialog = MutableStateFlow(false)
    val showNameErrorDialog: StateFlow<Boolean> = _showNameErrorDialog.asStateFlow()

    private val _showAgeErrorDialog = MutableStateFlow(false)
    val showAgeErrorDialog: StateFlow<Boolean> = _showAgeErrorDialog.asStateFlow()

    private val _showInvalidDetails = MutableStateFlow(false)
    val showInvalidDetails: StateFlow<Boolean> = _showInvalidDetails.asStateFlow()

    private val _showUpdateSuccessDialog = MutableStateFlow(false)
    val showUpdateSuccessDialog: StateFlow<Boolean> = _showUpdateSuccessDialog.asStateFlow()

    private val _showPasswordResetLockedDialog = MutableStateFlow(false)
    val showPasswordResetLockedDialog: StateFlow<Boolean> = _showPasswordResetLockedDialog.asStateFlow()

    val isFormValid: StateFlow<Boolean> = MutableStateFlow(false).apply {
        viewModelScope.launch {
            _selectedUserId.collect { userId ->
                val currentNameValid = _nameValid.value || (_nameInput.value == selectedUserName.value && selectedUserName.value != "Loading...")
                val currentPhoneValid = _isPhoneValid.value || (_phoneInput.value == selectedUserPhoneNum.value && selectedUserPhoneNum.value != "Loading...")

                val currentAgeValid = if (_ageInput.value.isNotBlank()) {
                    _ageInput.value.toIntOrNull() != null && _ageInput.value.toIntOrNull()!! >= 0
                } else {
                    true
                }
                value = userId.isNotBlank() && currentNameValid && currentPhoneValid && currentAgeValid
            }
        }
    }


    init {
        viewModelScope.launch {
            _selectedUserId.collect { userId ->
                if (userId.isNotBlank()) {
                    patientViewModel.setSelectedUserId(userId)
                }
            }
        }

        patientViewModel.selectedUserName.observeForever { name ->
            if (name != "Loading...") {
                _nameInput.value = name
                _nameValid.value = true
            }
        }
        patientViewModel.selectedUserAge.observeForever { age ->
            _ageInput.value = age?.toString() ?: ""
        }
        patientViewModel.selectedUserPhoneNum.observeForever { phone ->
            if (phone != "Loading...") {
                _phoneInput.value = phone ?: ""
                _isPhoneValid.value = true
            }
        }
    }

    fun setInitialUserId(userId: String) {
        _selectedUserId.value = userId
        patientViewModel.setSelectedUserId(userId)
    }

    fun onUserIdSelected(userId: String) {
        _selectedUserId.value = userId
        _expandedDropdown.value = false
        patientViewModel.setSelectedUserId(userId)
        _nameValid.value = false
        _isPhoneValid.value = false
        _oldPasswordInput.value = ""
        _newPasswordInput.value = ""
        _confirmNewPasswordInput.value = ""
        _passwordTriesRemaining.value = 3
        _newPasswordValid.value = false
        _confirmNewPasswordValid.value = false
    }

    fun onPhoneInputChange(newValue: String) {
        _phoneInput.value = newValue
        _isPhoneValid.value = false
    }

    fun validatePhoneNumber(context: Context) {
        val phoneRegex = Regex("^\\d{8,15}\$")
        if (_phoneInput.value.matches(phoneRegex)) {
            _isPhoneValid.value = true
        } else {
            _isPhoneValid.value = false
            _showPhoneMismatchDialog.value = true
        }
    }

    fun dismissPhoneMismatchDialog() {
        _showPhoneMismatchDialog.value = false
    }

    fun onNameInputChange(newValue: String) {
        _nameInput.value = newValue
        _nameValid.value = false
    }

    fun validateName() {
        if (_nameInput.value.matches(Regex("^[a-zA-Z\\s]+\$"))) {
            _nameValid.value = true
        } else {
            _nameValid.value = false
            _showNameErrorDialog.value = true
        }
    }

    fun dismissNameErrorDialog() {
        _showNameErrorDialog.value = false
    }

    fun onAgeInputChange(newValue: String) {
        if (newValue.all { it.isDigit() }) {
            _ageInput.value = newValue
        }
    }

    fun showOldPasswordDialog() {
        if (_selectedUserId.value.isNotBlank()) {
            if (_passwordTriesRemaining.value > 0) {
                _showOldPasswordDialog.value = true
            } else {
                _showPasswordResetLockedDialog.value = true
            }
        }
    }

    fun dismissOldPasswordDialog() {
        _showOldPasswordDialog.value = false
        _oldPasswordInput.value = ""
        _passwordTriesRemaining.value = 3
    }

    fun onOldPasswordInputChange(newValue: String) {
        _oldPasswordInput.value = newValue
    }

    fun toggleOldPasswordVisibility() {
        _oldPasswordVisible.value = !_oldPasswordVisible.value
    }

    fun verifyOldPassword(context: Context) {
        viewModelScope.launch {
            val currentPassword = selectedUserPassword.value
            if (currentPassword != null && _oldPasswordInput.value == currentPassword) {
                _showOldPasswordDialog.value = false
                _showNewPasswordDialog.value = true
                _passwordTriesRemaining.value = 3
                _oldPasswordInput.value = ""
                _newPasswordInput.value = ""
                _confirmNewPasswordInput.value = ""
                _newPasswordValid.value = false
                _confirmNewPasswordValid.value = false
            } else {
                _passwordTriesRemaining.value--
                if (_passwordTriesRemaining.value <= 0) {
                    _showOldPasswordDialog.value = false
                    _showPasswordResetLockedDialog.value = true
                } else {
                    Toast.makeText(context, "Incorrect password. Tries remaining: ${_passwordTriesRemaining.value}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    fun dismissNewPasswordDialog() {
        _showNewPasswordDialog.value = false
        _newPasswordInput.value = ""
        _confirmNewPasswordInput.value = ""
        _newPasswordValid.value = false
        _confirmNewPasswordValid.value = false
    }

    fun onNewPasswordInputChange(newValue: String) {
        _newPasswordInput.value = newValue
        _newPasswordValid.value = false
    }

    fun toggleNewPasswordVisibility() {
        _newPasswordVisible.value = !_newPasswordVisible.value
    }

    fun validateNewPassword() {
        val lengthValid = _newPasswordInput.value.length >= 5
        val containsNumber = _newPasswordInput.value.any { it.isDigit() }
        when {
            !lengthValid -> {
                _newPasswordValid.value = false
                _newPasswordErrorMessage.value = "Password is weak.\nEnsure password is more than 5 characters."
            }
            !containsNumber -> {
                _newPasswordValid.value = false
                _newPasswordErrorMessage.value = "Password must contain a number."
            }
            else -> {
                _newPasswordValid.value = true
            }
        }
    }

    fun onConfirmNewPasswordInputChange(newValue: String) {
        _confirmNewPasswordInput.value = newValue
        _confirmNewPasswordValid.value = false
    }

    fun toggleConfirmNewPasswordVisibility() {
        _confirmNewPasswordVisible.value = !_confirmNewPasswordVisible.value
    }

    fun validateConfirmNewPassword() {
        _confirmNewPasswordValid.value = _newPasswordInput.value == _confirmNewPasswordInput.value && _confirmNewPasswordInput.value.isNotBlank()
        _confirmNewPasswordErrorMessage.value = if (!_confirmNewPasswordValid.value) "Passwords do not match." else ""
    }

    fun saveNewPassword(userPreferencesManager: UserPreferencesManager) {
        viewModelScope.launch {
            if (_newPasswordValid.value && _confirmNewPasswordValid.value && _newPasswordInput.value.isNotBlank()) {
                val intAge = _ageInput.value.toIntOrNull()
                val longPhoneNum = _phoneInput.value.toLongOrNull()

                val success = patientViewModel.registerUser(
                    userId = _selectedUserId.value,
                    name = _nameInput.value,
                    age = intAge,
                    password = _newPasswordInput.value,
                    userPhoneNum = longPhoneNum
                )
                if (success) {
                    _showNewPasswordDialog.value = false
                    _showUpdateSuccessDialog.value = true
                    _newPasswordInput.value = ""
                    _confirmNewPasswordInput.value = ""
                    _newPasswordValid.value = false
                    _confirmNewPasswordValid.value = false
                } else {
                    _showInvalidDetails.value = true
                }
            } else {
                if (!_newPasswordValid.value) {
                    _newPasswordErrorMessage.value = "Please verify your new password."
                }
                if (!_confirmNewPasswordValid.value) {
                    _confirmNewPasswordErrorMessage.value = "Please confirm your new password."
                }
                _showInvalidDetails.value = true
            }
        }
    }

    fun dismissPasswordResetLockedDialog(context: Context, userPreferencesManager: UserPreferencesManager, activity: ComponentActivity) {
        viewModelScope.launch {
            _showPasswordResetLockedDialog.value = false
            userPreferencesManager.setLoggedIn(false)
            userPreferencesManager.setCurrentUserId("")
            userPreferencesManager.setLastScreenRoute("")
        }
    }

    fun updateProfile(userPreferencesManager: UserPreferencesManager) {
        viewModelScope.launch {
            when {
                _selectedUserId.value.isBlank() -> {
                    _showInvalidDetails.value = true
                }
                _ageInput.value.isNotBlank() && (_ageInput.value.toIntOrNull() == null || _ageInput.value.toIntOrNull()!! < 0) -> {
                    _showAgeErrorDialog.value = true
                }
                !(_nameValid.value && _isPhoneValid.value) -> {
                    _showInvalidDetails.value = true
                }
                else -> {
                    val intAge = _ageInput.value.toIntOrNull()
                    val longPhoneNum = _phoneInput.value.toLongOrNull()
                    val finalPassword = selectedUserPassword.value

                    if (finalPassword == null) {
                        _showInvalidDetails.value = true
                        return@launch
                    }

                    val success = patientViewModel.registerUser(
                        userId = _selectedUserId.value,
                        name = _nameInput.value,
                        age = intAge,
                        password = finalPassword,
                        userPhoneNum = longPhoneNum
                    )
                    if (success) {
                        _showUpdateSuccessDialog.value = true
                    } else {
                        _showInvalidDetails.value = true
                    }
                }
            }
        }
    }

    fun dismissInvalidDetailsDialog() {
        _showInvalidDetails.value = false
    }

    fun dismissUpdateSuccessDialog() {
        _showUpdateSuccessDialog.value = false
    }

    fun dismissAgeErrorDialog() {
        _showAgeErrorDialog.value = false
    }

    fun toggleDropdown(isExpanded: Boolean) {
        _expandedDropdown.value = isExpanded
    }
}

class EditProfileViewModelFactory(private val application: Application) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(EditProfileViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return EditProfileViewModel(application) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}