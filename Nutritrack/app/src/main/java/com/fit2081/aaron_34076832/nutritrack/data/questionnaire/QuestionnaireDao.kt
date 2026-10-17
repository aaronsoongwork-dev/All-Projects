package com.fit2081.aaron_34076832.nutritrack.data.questionnaire

import androidx.lifecycle.LiveData // Import LiveData
import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update

@Dao
interface QuestionnaireDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertQuestionnaire(questionnaire: Questionnaire)

    @Update
    suspend fun updateQuestionnaire(questionnaire: Questionnaire)

    @Query("SELECT * FROM questionnaire WHERE patientId = :patientId LIMIT 1")
    fun getQuestionnaireForPatient(patientId: String): LiveData<Questionnaire?>

    @Query("SELECT * FROM questionnaire WHERE patientId = :patientId")
    suspend fun getQuestionnaireByPatientId(patientId: String): Questionnaire?

    @Query("DELETE FROM questionnaire")
    suspend fun deleteAllQuestionnaires()

    @Query("UPDATE questionnaire SET isCompleted = :isCompleted WHERE patientId = :patientId")
    suspend fun updateCompletionStatus(patientId: String, isCompleted: Boolean)
}