package com.fit2081.aaron_34076832.nutritrack.data.questionnaire

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class QuestionnaireViewModel(application: Application) : AndroidViewModel(application) {

    private val repository: QuestionnaireRepository = QuestionnaireRepository(application)

    fun getQuestionnaireForPatient(patientId: String): LiveData<Questionnaire?> {
        return repository.getQuestionnaireForPatient(patientId)
    }

    suspend fun getQuestionnaireByPatientIdBlocking(patientId: String): Questionnaire? {
        return repository.getQuestionnaireByPatientId(patientId)
    }

    fun saveQuestionnaire(questionnaire: Questionnaire) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.insertQuestionnaire(questionnaire)
        }
    }

    fun deleteAllQuestionnaires() {
        viewModelScope.launch(Dispatchers.IO) {
            repository.deleteAllQuestionnaires()
        }
    }

    fun markQuestionnaireCompleted(patientId: String, isCompleted: Boolean) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.updateQuestionnaireCompletionStatus(patientId, isCompleted)
        }
    }

    class QuestionnaireViewModelFactory(private val application: Application) : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            if (modelClass.isAssignableFrom(QuestionnaireViewModel::class.java)) {
                @Suppress("UNCHECKED_CAST")
                return QuestionnaireViewModel(application) as T
            }
            throw IllegalArgumentException("Unknown ViewModel class")
        }
    }
}
