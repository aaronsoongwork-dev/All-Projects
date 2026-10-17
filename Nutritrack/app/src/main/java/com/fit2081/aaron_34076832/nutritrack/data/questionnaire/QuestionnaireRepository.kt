package com.fit2081.aaron_34076832.nutritrack.data.questionnaire

import android.content.Context
import com.fit2081.aaron_34076832.nutritrack.data.AppDatabase // Ensure this import path is correct for your AppDatabase

class QuestionnaireRepository(context: Context) {
    private val questionnaireDao: QuestionnaireDao

    init {
        val database = AppDatabase.getDatabase(context)
        questionnaireDao = database.questionnaireDao()
    }

    suspend fun insertQuestionnaire(questionnaire: Questionnaire) {
        questionnaireDao.insertQuestionnaire(questionnaire)
    }

    suspend fun updateQuestionnaireCompletionStatus(patientId: String, isCompleted: Boolean) {
        questionnaireDao.updateCompletionStatus(patientId, isCompleted)
    }

    fun getQuestionnaireForPatient(patientId: String) =
        questionnaireDao.getQuestionnaireForPatient(patientId)

    suspend fun getQuestionnaireByPatientId(patientId: String): Questionnaire? {
        return questionnaireDao.getQuestionnaireByPatientId(patientId)
    }

    suspend fun deleteAllQuestionnaires() {
        questionnaireDao.deleteAllQuestionnaires()
    }
}