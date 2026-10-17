package com.fit2081.aaron_34076832.nutritrack.data.patient

import android.content.Context
import android.util.Log
import androidx.lifecycle.*
import com.fit2081.a1healthapp.data.Gender.Gender
import com.fit2081.aaron_34076832.nutritrack.data.AuthManager
import com.fit2081.aaron_34076832.nutritrack.data.AppDatabase
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class PatientViewModel(
    private val repository: PatientRepository,
    private val authManager: AuthManager
) : ViewModel() {

    val allPatients: LiveData<List<Patient>> = repository.getAllPatients().asLiveData()

    val unregisteredUserIds: LiveData<List<String>> = allPatients.map { patients ->
        patients.filter { !it.isRegistered }.map { it.userID }
    }

    private val _selectedPatientGender = MutableLiveData<Gender?>(null)

    suspend fun loginUser(userId: String, password: String): Boolean {
        Log.d("PatientViewModel", "Attempting login for userId: $userId")
        return authManager.login(userId, password)
    }

    fun logoutUser() {
        authManager.logout()
        Log.d("PatientViewModel", "User logged out.")
    }

    suspend fun isPasswordEmpty(userId: String): Boolean {
        return try {
            val storedPassword = repository.getPatientById(userId).userPassword
            Log.d("PatientViewModel", "Password for $userId is '$storedPassword'")
            storedPassword == ""
        } catch (e: Exception) {
            Log.e("PatientViewModel", "Error checking if password is empty for $userId", e)
            false
        }
    }

    suspend fun registerUser(
        userId: String,
        name: String,
        age: Int?,
        password: String,
        userPhoneNum: Long?
    ): Boolean {
        return try {
            val existing = repository.getPatientById(userId)
            val updatedPatient = existing.copy(
                userName = name,
                userAge = age,
                userPassword = password,
                isRegistered = true,
                userPhoneNum = userPhoneNum
            )
            repository.updatePatient(updatedPatient)
            true
        } catch (e: Exception) {
            Log.e("PatientViewModel", "Error registering user: $userId", e)
            false
        }
    }

    private val _patientID = MutableLiveData<String>()

    fun getPatientID() {
        viewModelScope.launch {
            val id = repository.getPatientID() ?: "No Patient ID"
            _patientID.value = id
        }
    }

    private val _selectedUserId = MutableLiveData("")

    val selectedUserPassword: LiveData<String> = _selectedUserId.switchMap { userId ->
        liveData {
            if (userId.isBlank()) {
                emit("")
            } else {
                try {
                    val patient = repository.getPatientById(userId)
                    emit(patient.userPassword)
                } catch (e: Exception) {
                    Log.e("PatientViewModel", "Error fetching password for userId: $userId", e)
                    emit("User not found")
                }
            }
        }
    }

    private suspend fun fetchUserName(userId: String): String {
        return if (userId.isBlank()) {
            "Guest"
        } else {
            try {
                val userName = repository.getUserNameByUserId(userId)
                userName ?: "Unknown User"
            } catch (e: Exception) {
                Log.e("PatientViewModel", "Failed to get user name for userId: $userId", e)
                "Error User"
            }
        }
    }

    val selectedUserName: LiveData<String> = _selectedUserId.switchMap { userId ->
        liveData {
            emit(fetchUserName(userId))
        }
    }

    private suspend fun fetchUserAge(userId: String): Int? {
        return if (userId.isBlank()) {
            null
        } else {
            try {
                repository.getPatientById(userId).userAge
            } catch (e: Exception) {
                Log.e("PatientViewModel", "Failed to get user age for userId: $userId", e)
                null
            }
        }
    }

    val selectedUserAge: LiveData<Int?> = _selectedUserId.switchMap { userId ->
        liveData {
            emit(fetchUserAge(userId))
        }
    }

    suspend fun updatePassword(userId: String, newPassword: String): Boolean {
        return try {
            val existingPatient = repository.getPatientById(userId)
            val updatedPatient = existingPatient.copy(userPassword = newPassword)
            repository.updatePatient(updatedPatient)
            Log.d("PatientViewModel", "Password updated successfully for userId: $userId")
            true
        } catch (e: Exception) {
            Log.e("PatientViewModel", "Error updating password for userId: $userId", e)
            false
        }
    }

    private suspend fun fetchUserSex(userId: String): Gender? {
        return if (userId.isBlank()) {
            null
        } else {
            try {
                repository.getPatientById(userId).userSex
            } catch (e: Exception) {
                Log.e("PatientViewModel", "Failed to get user sex for userId: $userId", e)
                null
            }
        }
    }

    val selectedUserSex: LiveData<Gender?> = _selectedUserId.switchMap { userId ->
        liveData {
            emit(fetchUserSex(userId))
        }
    }

    private suspend fun fetchUserPhoneNum(userId: String): Long? {
        return if (userId.isBlank()) {
            null
        } else {
            try {
                repository.getPatientById(userId).userPhoneNum
            } catch (e: Exception) {
                Log.e("PatientViewModel", "Failed to get user phone number for userId: $userId", e)
                null
            }
        }
    }

    val selectedUserPhoneNum: LiveData<String?> = _selectedUserId.switchMap { userId ->
        liveData {
            emit(fetchUserPhoneNum(userId).toString())
        }
    }

    private suspend fun getPatientPassword(userId: String): String? {
        return try {
            repository.getPatientPassword(userId)
        } catch (e: Exception) {
            Log.e("PatientViewModel", "Failed to get password for userId: $userId", e)
            null
        }
    }

    fun setSelectedUserId(userId: String) {
        _selectedUserId.value = userId
        viewModelScope.launch(Dispatchers.IO) {
            if (userId.isNotBlank()) {
                try {
                    val patient = repository.getPatientById(userId)
                    _selectedPatientGender.postValue(patient.userSex)
                } catch (e: Exception) {
                    Log.e("PatientViewModel", "Error fetching patient for gender update: $userId", e)
                    _selectedPatientGender.postValue(null)
                }
            } else {
                _selectedPatientGender.postValue(null)
            }
        }
    }

    class PatientsViewModelFactory(private val context: Context) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(PatientViewModel::class.java)) {
                val database = AppDatabase.getDatabase(context)
                val patientDao = database.patientDao()
                val repository = PatientRepository(context)
                val authManager = AuthManager(repository)
                @Suppress("UNCHECKED_CAST")
                return PatientViewModel(repository, authManager) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}
