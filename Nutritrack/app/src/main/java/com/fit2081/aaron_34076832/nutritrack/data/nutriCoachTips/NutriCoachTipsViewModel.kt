package com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.fit2081.aaron_34076832.nutritrack.BuildConfig
import com.fit2081.aaron_34076832.nutritrack.data.AppDatabase
import com.google.ai.client.generativeai.GenerativeModel
import com.google.ai.client.generativeai.type.content
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.launch
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import kotlinx.coroutines.ExperimentalCoroutinesApi

// Define a UiState for the motivational message generation
sealed class MotivationalUiState {
    object Initial : MotivationalUiState()
    object Loading : MotivationalUiState()
    data class Error(val errorMessage: String) : MotivationalUiState()
    data class Success(val message: String) : MotivationalUiState()
}

class NutriCoachTipsViewModel(application: Application) : AndroidViewModel(application) {

    private var repository: NutriCoachTipsRepository = NutriCoachTipsRepository(AppDatabase.getDatabase(application))

    // MutableStateFlow to hold the current user's ID
    private val _currentUserId = MutableStateFlow<String?>(null)

    @OptIn(ExperimentalCoroutinesApi::class)
    val allTips: StateFlow<List<NutriCoachTips>> = _currentUserId.flatMapLatest { userId ->
        if (userId != null) {
            repository.getAllTipsForUser(userId)
        } else {
            MutableStateFlow(emptyList()) // Return an empty list if no user ID is set
        }
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000), // Keep collecting for 5 seconds after last subscriber
        initialValue = emptyList() // Initial value before any data is loaded
    )

    private val _motivationalUiState: MutableStateFlow<MotivationalUiState> = MutableStateFlow(
        MotivationalUiState.Initial
    )
    val motivationalUiState: StateFlow<MotivationalUiState> = _motivationalUiState.asStateFlow()

    private val generativeModel = GenerativeModel(
        modelName = "gemini-1.5-flash",
        apiKey = BuildConfig.apiKeySafe
    )

    init {
        val database = AppDatabase.getDatabase(application)
        repository = NutriCoachTipsRepository(database)
        // No need to manually collect allTips here, as it's now derived from _currentUserId
    }

    // Function to set the current user ID. This should be called from the UI.
    fun setCurrentUserId(userId: String) {
        _currentUserId.value = userId
    }

    fun resetMotivationalUiState() {
        _motivationalUiState.value = MotivationalUiState.Initial
    }

    fun generateMotivationalMessage(
        motivationType: String, // e.g., "working out", "sleep", "diet", "wellbeing"
        energyLevel: Int?,      // 1-5 scale
        additionalNotes: String // optional notes
    ) {
        _motivationalUiState.value = MotivationalUiState.Loading

        viewModelScope.launch(Dispatchers.IO) {
            _currentUserId.value?.let { userId -> // Ensure userId is available before generating and saving
                try {
                    val promptBuilder = StringBuilder()
                    promptBuilder.append("Generate a short encouraging message to help someone improve their fruit intake. ")
                    promptBuilder.append("Focus on ")
                    promptBuilder.append(motivationType)
                    promptBuilder.append(".")

                    energyLevel?.let {
                        promptBuilder.append(" The person's energy level is currently at a scale of $it out of 5, where 1 is very low and 5 is very high.")
                    }

                    if (additionalNotes.isNotBlank()) {
                        promptBuilder.append(" Also consider this additional information: \"$additionalNotes\"")
                    }

                    val response = generativeModel.generateContent(
                        content {
                            text(promptBuilder.toString())
                        }
                    )
                    response.text?.let { message ->
                        // Create NutriCoachTips with the current userId
                        val newTip = NutriCoachTips(
                            userId = userId,
                            message = message,
                            timestamp = System.currentTimeMillis()
                        )
                        insertTip(newTip)
                        _motivationalUiState.value = MotivationalUiState.Success(message)
                    } ?: run {
                        _motivationalUiState.value =
                            MotivationalUiState.Error("Failed to generate message: AI returned no text.")
                    }
                } catch (e: Exception) {
                    _motivationalUiState.value = MotivationalUiState.Error(
                        e.localizedMessage ?: "Unknown error occurred during message generation."
                    )
                }
            } ?: run {
                _motivationalUiState.value = MotivationalUiState.Error("User ID not available to generate tip.")
            }
        }
    }

    fun insertTip(tip: NutriCoachTips) = viewModelScope.launch(Dispatchers.IO) {
        repository.insertTip(tip)
    }

    // Function to delete all tips for the currently set user
    fun deleteAllTipsForCurrentUser() = viewModelScope.launch(Dispatchers.IO) {
        _currentUserId.value?.let { userId ->
            repository.deleteAllTipsForUser(userId)
        }
    }

    fun deleteTipById(tipId: Long) = viewModelScope.launch(Dispatchers.IO) {
        repository.deleteTipById(tipId)
    }

    // LiveData for UI state related to dialogs and inputs
    private val _showDeleteTipDialog = MutableLiveData(false)
    val showDeleteTipDialog: LiveData<Boolean> = _showDeleteTipDialog

    private val _tipToDeleteId = MutableLiveData(-1L)
    val tipToDeleteId: LiveData<Long> = _tipToDeleteId

    private val _showDeleteAllTipsDialog = MutableLiveData(false)
    val showDeleteAllTipsDialog: LiveData<Boolean> = _showDeleteAllTipsDialog

    private val _showAllTipsModal = MutableLiveData(false)
    val showAllTipsModal: LiveData<Boolean> = _showAllTipsModal

    private val _showMotivationPromptDialog = MutableLiveData(false)
    val showMotivationPromptDialog: LiveData<Boolean> = _showMotivationPromptDialog

    private val _showMotivationQuestion1Dialog = MutableLiveData(false)
    val showMotivationQuestion1Dialog: LiveData<Boolean> = _showMotivationQuestion1Dialog

    private val _showMotivationQuestion2Dialog = MutableLiveData(false)
    val showMotivationQuestion2Dialog: LiveData<Boolean> = _showMotivationQuestion2Dialog

    private val _showMotivationQuestion3Dialog = MutableLiveData(false)
    val showMotivationQuestion3Dialog: LiveData<Boolean> = _showMotivationQuestion3Dialog

    private val _selectedMotivationType = MutableLiveData("")
    val selectedMotivationType: LiveData<String> = _selectedMotivationType

    private val _energyLevel = MutableLiveData(3f)
    val energyLevel: LiveData<Float> = _energyLevel

    private val _additionalNotes = MutableLiveData("")
    val additionalNotes: LiveData<String> = _additionalNotes

    fun setShowDeleteTipDialog(show: Boolean, tipId: Long = -1L) {
        _showDeleteTipDialog.value = show
        _tipToDeleteId.value = tipId
    }

    fun setShowDeleteAllTipsDialog(show: Boolean) {
        _showDeleteAllTipsDialog.value = show
    }

    fun setShowAllTipsModal(show: Boolean) {
        _showAllTipsModal.value = show
    }

    fun setShowMotivationPromptDialog(show: Boolean) {
        _showMotivationPromptDialog.value = show
    }

    fun setShowMotivationQuestion1Dialog(show: Boolean) {
        _showMotivationQuestion1Dialog.value = show
    }

    fun setShowMotivationQuestion2Dialog(show: Boolean) {
        _showMotivationQuestion2Dialog.value = show
    }

    fun setShowMotivationQuestion3Dialog(show: Boolean) {
        _showMotivationQuestion3Dialog.value = show
    }

    fun setSelectedMotivationType(type: String) {
        _selectedMotivationType.value = type
    }

    fun setEnergyLevel(level: Float) {
        _energyLevel.value = level
    }

    fun setAdditionalNotes(notes: String) {
        _additionalNotes.value = notes
    }

    fun resetMotivationInputs() {
        _selectedMotivationType.value = ""
        _energyLevel.value = 3f
        _additionalNotes.value = ""
    }

    // Factory for ViewModel
    class NutriCoachTipsViewModelFactory(private val application: Application) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(NutriCoachTipsViewModel::class.java)) {
                @Suppress("UNCHECKED_CAST")
                return NutriCoachTipsViewModel(application) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}