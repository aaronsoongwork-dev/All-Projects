package com.fit2081.aaron_34076832.nutritrack.viewmodels

import android.app.Application
import android.content.Context
import android.widget.Toast
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.fit2081.aaron_34076832.nutritrack.data.UserPreferencesManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ClinicianLoginViewModel(application: Application) : AndroidViewModel(application) {

    private val CORRECT_PASSWORD = "dollar-entry-apples"

    private val _passwordInput = MutableStateFlow("")
    val passwordInput: StateFlow<String> = _passwordInput.asStateFlow()

    private val _remainingAttempts = MutableStateFlow(3)
    val remainingAttempts: StateFlow<Int> = _remainingAttempts.asStateFlow()

    private val _showAlertDialog = MutableStateFlow(false)
    val showAlertDialog: StateFlow<Boolean> = _showAlertDialog.asStateFlow()

    private val _dialogMessage = MutableStateFlow("")
    val dialogMessage: StateFlow<String> = _dialogMessage.asStateFlow()

    private val _dialogTitle = MutableStateFlow("")
    val dialogTitle: StateFlow<String> = _dialogTitle.asStateFlow()

    private val _navigateToDashboard = MutableStateFlow<String?>(null)
    val navigateToDashboard: StateFlow<String?> = _navigateToDashboard.asStateFlow()

    private val _navigateToSettings = MutableStateFlow<String?>(null)
    val navigateToSettings: StateFlow<String?> = _navigateToSettings.asStateFlow()

    fun onPasswordInputChanged(newInput: String) {
        _passwordInput.value = newInput
    }


    fun onLoginClicked(context: Context, userId: String?, userPreferencesManager: UserPreferencesManager) {
        viewModelScope.launch {
            if (_passwordInput.value == CORRECT_PASSWORD) {
                Toast.makeText(context, "Login Successful!", Toast.LENGTH_SHORT).show()
                _navigateToDashboard.value = userId // Set the value to trigger navigation
                // Do NOT set it to null here. It will be set to null in navigationToDashboardHandled()
            } else {
                _remainingAttempts.value--
                if (_remainingAttempts.value > 0) {
                    _dialogTitle.value = "Incorrect Password"
                    _dialogMessage.value = "Remaining attempts: ${_remainingAttempts.value}"
                } else {
                    _dialogTitle.value = "Too Many Failed Attempts"
                    _dialogMessage.value = "Returning to Settings page."
                }
                _showAlertDialog.value = true
            }
        }
    }

    fun onAlertDialogDismissed(context: Context, userId: String?, userPreferencesManager: UserPreferencesManager) {
        _showAlertDialog.value = false
        if (_remainingAttempts.value == 0) {
            _navigateToSettings.value = userId
            _navigateToSettings.value = null
        }
    }

    fun resetState() {
        _passwordInput.value = ""
        _remainingAttempts.value = 3
        _showAlertDialog.value = false
        _dialogMessage.value = ""
        _dialogTitle.value = ""
        _navigateToDashboard.value = null
        _navigateToSettings.value = null
    }

    fun navigationToDashboardHandled() {
        _navigateToDashboard.value = null
    }

    fun navigationToSettingsHandled() {
        _navigateToSettings.value = null
    }
}

class ClinicianLoginViewModelFactory(private val application: Application) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ClinicianLoginViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return ClinicianLoginViewModel(application) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}