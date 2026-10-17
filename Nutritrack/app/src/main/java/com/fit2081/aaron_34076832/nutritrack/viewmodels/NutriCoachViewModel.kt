package com.fit2081.aaron_34076832.nutritrack.data.nutricoach

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntake
import com.fit2081.aaron_34076832.nutritrack.data.foodIntake.FoodIntakeRepository
import com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips.MotivationalUiState
import com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips.NutriCoachTips
import com.fit2081.aaron_34076832.nutritrack.data.nutriCoachTips.NutriCoachTipsRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch
import androidx.lifecycle.asLiveData
import com.fit2081.aaron_34076832.nutritrack.data.AppDatabase
import com.fit2081.aaron_34076832.nutritrack.genAI.GenAIViewModel
import com.fit2081.aaron_34076832.nutritrack.genAI.GenAIViewModelFactory
import kotlinx.coroutines.ExperimentalCoroutinesApi

class NutriCoachViewModel(application: Application) : AndroidViewModel(application) {

    private val database: AppDatabase = AppDatabase.getDatabase(application)

    private val nutriCoachTipsRepository: NutriCoachTipsRepository = NutriCoachTipsRepository(database)
    private val foodIntakeRepository: FoodIntakeRepository = FoodIntakeRepository(application)

    private val genAIViewModel: GenAIViewModel = GenAIViewModelFactory(application).create(GenAIViewModel::class.java)

    // A MutableStateFlow to hold the current user's ID
    private val _currentUserId = MutableStateFlow<String?>(null)

    // Modify allTips to depend on _currentUserId, fetching tips specific to that user
    @OptIn(ExperimentalCoroutinesApi::class)
    val allTips: Flow<List<NutriCoachTips>> = _currentUserId.flatMapLatest { userId ->
        if (userId != null) {
            nutriCoachTipsRepository.getAllTipsForUser(userId)
        } else {
            MutableStateFlow(emptyList()) // Return an empty list if no user ID is set
        }
    }

    private val _motivationalUiState = MutableStateFlow<MotivationalUiState>(MotivationalUiState.Initial)
    val motivationalUiState: StateFlow<MotivationalUiState> = _motivationalUiState.asStateFlow()

    // Function to set the current user ID
    fun setCurrentUserId(userId: String) {
        _currentUserId.value = userId
    }

    fun insertTip(tip: NutriCoachTips) = viewModelScope.launch {
        nutriCoachTipsRepository.insertTip(tip)
    }

    fun deleteTipById(id: Long) = viewModelScope.launch {
        nutriCoachTipsRepository.deleteTipById(id)
    }

    // This function will now delete all tips for the currently set user ID
    fun deleteAllTipsForCurrentUser() = viewModelScope.launch {
        _currentUserId.value?.let { userId ->
            nutriCoachTipsRepository.deleteAllTipsForUser(userId)
        }
    }

    fun generateMotivationalMessage(
        motivationType: String,
        energyLevel: Int?,
        additionalNotes: String
    ) {
        _motivationalUiState.value = MotivationalUiState.Loading

        viewModelScope.launch {
            _currentUserId.value?.let { userId -> // Ensure userId is available
                try {
                    val generatedMessage = genAIViewModel.generateMotivationalContent(
                        motivationType,
                        energyLevel,
                        additionalNotes
                    )

                    val newTip = NutriCoachTips(
                        userId = userId, // Pass the current userId to the new tip
                        message = generatedMessage,
                        timestamp = System.currentTimeMillis()
                    )
                    insertTip(newTip)
                    _motivationalUiState.value = MotivationalUiState.Success(generatedMessage)

                } catch (e: Exception) {
                    _motivationalUiState.value = MotivationalUiState.Error("Error generating message: ${e.localizedMessage}")
                    e.printStackTrace()
                }
            } ?: run {
                _motivationalUiState.value = MotivationalUiState.Error("User ID not available to generate tip.")
            }
        }
    }

    fun resetMotivationalUiState() {
        _motivationalUiState.value = MotivationalUiState.Initial
    }

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

    private val _patientIdForFoodIntake = MutableStateFlow<String?>(null)

    @OptIn(ExperimentalCoroutinesApi::class)
    val latestFoodIntakeByPatientId: Flow<FoodIntake?> = _patientIdForFoodIntake.flatMapLatest { patientId ->
        if (patientId != null) {
            foodIntakeRepository.getLatestFoodIntakeByPatientId(patientId)
        } else {
            MutableStateFlow(null)
        }
    }

    fun setPatientIdForFoodIntake(patientId: String) {
        _patientIdForFoodIntake.value = patientId
        // Assuming patientId for food intake is the same as userId for tips
        setCurrentUserId(patientId)
    }

    val isFruitScoreOptimal: LiveData<Boolean> = latestFoodIntakeByPatientId.map { latestFoodIntake ->
        (latestFoodIntake?.fruitservesize ?: 0.0) >= 2.0 &&
                (latestFoodIntake?.fruitvariationsscore ?: 0) >= 5
    }.asLiveData()

    class NutriCoachViewModelFactory(private val application: Application) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(NutriCoachViewModel::class.java)) {
                @Suppress("UNCHECKED_CAST")
                return NutriCoachViewModel(application) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}