package com.fit2081.aaron_34076832.nutritrack.ui.questionnaire

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.fit2081.a1healthapp.data.Gender.Gender
import com.fit2081.aaron_34076832.nutritrack.data.questionnaire.Questionnaire
import com.fit2081.aaron_34076832.nutritrack.data.questionnaire.QuestionnaireRepository
import com.fit2081.aaron_34076832.nutritrack.data.questionnaire.QuestionnaireViewModel
import com.fit2081.aaron_34076832.nutritrack.data.persona.Persona
import kotlinx.coroutines.launch

class QuestionnaireScreenViewModel(
    application: Application,
    private val questionnaireViewModel: QuestionnaireViewModel
) : AndroidViewModel(application) {

    private val _userId = MutableLiveData<String>()
    val userId: LiveData<String> = _userId

    private val _saveMealTime = MutableLiveData("")
    val saveMealTime: LiveData<String> = _saveMealTime

    private val _saveSleepTime = MutableLiveData("")
    val saveSleepTime: LiveData<String> = _saveSleepTime

    private val _saveWakeTime = MutableLiveData("")
    val saveWakeTime: LiveData<String> = _saveWakeTime

    private val _fruits = MutableLiveData(false)
    val fruits: LiveData<Boolean> = _fruits

    private val _vege = MutableLiveData(false)
    val vege: LiveData<Boolean> = _vege

    private val _grains = MutableLiveData(false)
    val grains: LiveData<Boolean> = _grains

    private val _redMeat = MutableLiveData(false)
    val redMeat: LiveData<Boolean> = _redMeat

    private val _seafood = MutableLiveData(false)
    val seafood: LiveData<Boolean> = _seafood

    private val _poultry = MutableLiveData(false)
    val poultry: LiveData<Boolean> = _poultry

    private val _fish = MutableLiveData(false)
    val fish: LiveData<Boolean> = _fish

    private val _eggs = MutableLiveData(false)
    val eggs: LiveData<Boolean> = _eggs

    private val _nutsSeeds = MutableLiveData(false)
    val nutsSeeds: LiveData<Boolean> = _nutsSeeds

    private val _selectedPersona = MutableLiveData<Persona?>(null)
    val selectedPersona: LiveData<Persona?> = _selectedPersona

    private val _showValidationDialog = MutableLiveData(false)
    val showValidationDialog: LiveData<Boolean> = _showValidationDialog

    private val _validationMessage = MutableLiveData("")
    val validationMessage: LiveData<String> = _validationMessage

    private val _saveSuccess = MutableLiveData<Boolean?>(null)
    val saveSuccess: LiveData<Boolean?> = _saveSuccess

    val existingQuestionnaire: LiveData<Questionnaire?>
        get() = questionnaireViewModel.getQuestionnaireForPatient(_userId.value ?: "")


    init {
        _userId.value = ""
    }

    fun setUserId(id: String) {
        _userId.value = id
        loadQuestionnaireData(id)
    }

    private fun loadQuestionnaireData(patientId: String) {
        viewModelScope.launch {
            val questionnaire = questionnaireViewModel.getQuestionnaireByPatientIdBlocking(patientId)
            questionnaire?.let {
                _saveMealTime.value = it.timeMeal ?: ""
                _saveSleepTime.value = it.timeSleep ?: ""
                _saveWakeTime.value = it.timeWakeUp ?: ""
                _fruits.value = it.fruits
                _vege.value = it.vegetables
                _grains.value = it.grains
                _redMeat.value = it.redMeat
                _seafood.value = it.seafood
                _poultry.value = it.poultry
                _fish.value = it.fish
                _eggs.value = it.eggs
                _nutsSeeds.value = it.nutsSeeds
                _selectedPersona.value = it.persona
            }
        }
    }

    fun onMealTimeSelected(time: String) {
        _saveMealTime.value = time
    }

    fun onSleepTimeSelected(time: String) {
        _saveSleepTime.value = time
    }

    fun onWakeTimeSelected(time: String) {
        _saveWakeTime.value = time
    }

    fun toggleFruits(checked: Boolean) { _fruits.value = checked }
    fun toggleVege(checked: Boolean) { _vege.value = checked }
    fun toggleGrains(checked: Boolean) { _grains.value = checked }
    fun toggleRedMeat(checked: Boolean) { _redMeat.value = checked }
    fun toggleSeafood(checked: Boolean) { _seafood.value = checked }
    fun togglePoultry(checked: Boolean) { _poultry.value = checked }
    fun toggleFish(checked: Boolean) { _fish.value = checked }
    fun toggleEggs(checked: Boolean) { _eggs.value = checked }
    fun toggleNutsSeeds(checked: Boolean) { _nutsSeeds.value = checked }

    fun onPersonaSelected(persona: Persona) {
        _selectedPersona.value = persona
    }

    fun dismissValidationDialog() {
        _showValidationDialog.value = false
        _validationMessage.value = ""
    }

    fun resetSaveSuccessState() {
        _saveSuccess.value = null
    }

    fun saveQuestionnaire() {
        val currentUserId = _userId.value ?: run {
            _validationMessage.value = "User ID not set. Cannot save questionnaire."
            _showValidationDialog.value = true
            _saveSuccess.value = false
            return
        }

        val atLeastOneFoodSelected = _fruits.value!! || _vege.value!! || _grains.value!! ||
                _redMeat.value!! || _seafood.value!! || _poultry.value!! ||
                _fish.value!! || _eggs.value!! || _nutsSeeds.value!!

        if (!atLeastOneFoodSelected) {
            _validationMessage.value = "Please select at least one food category."
            _showValidationDialog.value = true
            _saveSuccess.value = false
            return
        }

        if (_selectedPersona.value == null) {
            _validationMessage.value = "Please select your persona."
            _showValidationDialog.value = true
            _saveSuccess.value = false
            return
        }

        if (_saveMealTime.value.isNullOrBlank() || _saveSleepTime.value.isNullOrBlank() || _saveWakeTime.value.isNullOrBlank()) {
            _validationMessage.value = "Please provide all timing information."
            _showValidationDialog.value = true
            _saveSuccess.value = false
            return
        }

        val newQuestionnaire = Questionnaire(
            patientId = currentUserId,
            fruits = _fruits.value!!,
            vegetables = _vege.value!!,
            grains = _grains.value!!,
            redMeat = _redMeat.value!!,
            seafood = _seafood.value!!,
            poultry = _poultry.value!!,
            fish = _fish.value!!,
            eggs = _eggs.value!!,
            nutsSeeds = _nutsSeeds.value!!,
            persona = _selectedPersona.value,
            timeMeal = _saveMealTime.value,
            timeSleep = _saveSleepTime.value,
            timeWakeUp = _saveWakeTime.value,
            isCompleted = true
        )

        viewModelScope.launch {
            questionnaireViewModel.saveQuestionnaire(newQuestionnaire)
            _saveSuccess.value = true
        }
    }


    class QuestionnaireScreenViewModelFactory(
        private val application: Application,
        private val questionnaireRepository: QuestionnaireRepository
    ) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(QuestionnaireScreenViewModel::class.java)) {
                val questionnaireViewModel = QuestionnaireViewModel(application)
                @Suppress("UNCHECKED_CAST")
                return QuestionnaireScreenViewModel(application, questionnaireViewModel) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}